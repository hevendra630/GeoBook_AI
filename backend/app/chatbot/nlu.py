from __future__ import annotations

import re

import json

from dataclasses import dataclass

from datetime import datetime

from typing import Literal

import dateparser

import google.generativeai as genai

from app.db.models import BusinessCategory

from app.core.config import settings

from app.core.logging import logger

if settings.gemini_api_key:

    genai.configure(api_key=settings.gemini_api_key)

Intent = Literal["search", "book", "unknown"]

@dataclass(frozen=True)

class ParsedMessage:

    intent: Intent

    category: BusinessCategory | None

    place_type: str | None

    location_text: str | None

    when: datetime | None

    target_text: str | None

    raw: str

    search_term: str | None

_CATEGORY_KEYWORDS: list[tuple[BusinessCategory, list[str]]] = [

    (BusinessCategory.restaurant, ["restaurant", "food", "eat", "cafe", "diner", "coffee", "breakfast", "lunch", "dinner", "pizza", "burger", "bakery"]),

    (BusinessCategory.school, ["school", "college", "university", "academy", "education"]),

    (BusinessCategory.hospital, ["hospital", "emergency", "er", "medical center"]),

    (BusinessCategory.police, ["police", "cops", "station"]),

    (BusinessCategory.bus_stop, ["bus stop", "transit", "bus station", "depot"]),

    (BusinessCategory.dental, ["dentist", "dental", "orthodontist", "teeth"]),

    (BusinessCategory.clinic, ["clinic", "doctor", "physician", "health center", "medical clinic"]),

    (BusinessCategory.salon, ["salon", "barber", "haircut", "spa", "beauty", "grooming", "parlour", "styling", "saloon", "saloons"]),

]

_PLACE_TYPE_BY_CATEGORY: dict[BusinessCategory, str] = {

    BusinessCategory.restaurant: "restaurant",

    BusinessCategory.school: "school",

    BusinessCategory.hospital: "hospital",

    BusinessCategory.police: "police",

    BusinessCategory.bus_stop: "bus_station",

    BusinessCategory.salon: "beauty_salon",

    BusinessCategory.dental: "dentist",

    BusinessCategory.clinic: "doctor",

}

async def _parse_with_gemini(text: str) -> dict | None:

    if not settings.gemini_api_key:

        return None

    prompt = f"""
    You are an NLU engine for a local service chatbot. 
    Analyze the user message and extract the intent and entities in JSON format.
    
    User Message: "{text}"
    Current Time: {datetime.now().isoformat()}

    Available Categories: {[c.value for c in BusinessCategory]}

    Return JSON with these fields:
    - intent: "search" (finding places), "book" (scheduling an appointment), or "unknown"
    - category: The specific category from the list above, or null
    - location: A city or neighborhood mentioned, or null
    - when: An ISO string if the user mentions a specific time for booking, or null
    - target_text: For booking, the name of the place they want to book, or null
    - search_term: For searching, the specific thing they are looking for (e.g. "orthopedic surgeon"), or null

    Example 1: "Find a hospital in Guntur"
    Output: {{ "intent": "search", "category": "hospital", "location": "Guntur", "when": null, "target_text": null, "search_term": "hospital"}} 

    Example 2: "Book an appointment at Downtown Dental tomorrow at 4pm"
    Output: {{ "intent": "book", "category": "dental", "location": null, "when": "2026-04-02T16:00:00", "target_text": "Downtown Dental", "search_term": null}} 

    Return ONLY the JSON.
    """

    try:

        model = genai.GenerativeModel("gemini-1.5-flash-latest")

        response = await model.generate_content_async(prompt)

        

        raw_json = response.text.strip()

        if raw_json.startswith("```json"):

            raw_json = raw_json[7:-3].strip()

        elif raw_json.startswith("```"):

            raw_json = raw_json[3:-3].strip()

        

        return json.loads(raw_json)

    except Exception as e:

        logger.error("gemini_nlu.failed", error=str(e))

        return None

def _detect_intent(text: str) -> Intent:

    t = text.lower()

    if any(k in t for k in ["book", "schedule", "appointment", "reserve"]):

        return "book"

    if any(k in t for k in ["find", "nearest", "nearby", "search", "show me", "look for"]):

        return "search"

    return "unknown"

def _extract_location(text: str) -> str | None:

    patterns = [

        r"\b(?:in|near|around|at)\s+([a-zA-Z0-9\s,.'-]{3,})$",

        r"\b(?:in|near|around|at)\s+([a-zA-Z0-9\s,.'-]{3,})\b",

    ]

    for p in patterns:

        m = re.search(p, text, flags=re.IGNORECASE)

        if m:

            loc = m.group(1).strip()

            loc = re.sub(r"\b(tomorrow|today|tonight|next week|next monday|next tuesday|next wednesday|next thursday|next friday|next saturday|next sunday)\b.*$", "", loc, flags=re.I).strip()

            return loc if len(loc) >= 3 else None

    return None

def _extract_category(text: str) -> BusinessCategory | None:

    t = text.lower()

    for cat, keywords in _CATEGORY_KEYWORDS:

        if any(k in t for k in keywords):

            return cat

    return None

def _extract_when(text: str) -> datetime | None:

    

    t = text.lower()

    for prefix in ["book an appointment", "book appointment", "schedule an appointment", "schedule appointment", "book", "schedule"]:

        if t.startswith(prefix):

            t = t[len(prefix):].strip()

    

    

    t = re.sub(r"\b(in|for|at)\s+(the\s+)?(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)(\s+one)?\b", "", t, flags=re.I).strip()

    dt = dateparser.parse(

        t,

        settings={

            "PREFER_DATES_FROM": "future",

            "RETURN_AS_TIMEZONE_AWARE": True,

        },

    )

    if dt:

        return dt

    

    

    m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", text, flags=re.I)

    if m:

        

        

        dt_time = dateparser.parse(m.group(0), settings={"PREFER_DATES_FROM": "future", "RETURN_AS_TIMEZONE_AWARE": True})

        if dt_time:

            return dt_time

    return None

def _extract_target(text: str) -> str | None:

    t = text.strip()

    m = re.search(r"\b(?:for|at)\s+([a-zA-Z0-9\s,.'-]{2,}?)\s+\b(?:at|on|tomorrow|today|next)\b", t, flags=re.I)

    if m:

        return m.group(1).strip()

    m2 = re.search(r"\bbook\s+(?:an\s+)?(?:appointment\s+)?(?:for\s+)?([a-zA-Z0-9\s,.'-]{2,})", t, flags=re.I)

    if m2:

        candidate = m2.group(1).strip()

        candidate = re.sub(r"\b(at\s+\d{1,2}(:\d{2})?\s*(am|pm)?)\b.*$", "", candidate, flags=re.I).strip()

        return candidate if candidate else None

    return None

def _extract_search_term(text: str, intent: str, loc_text: str | None) -> str | None:

    if intent != "search":

        return None

    t = text.lower()

    t = re.sub(r"^(can you|could you|would you|please)\s+", "", t).strip()

    prefixes = ["find me", "show me", "search for", "look for", "find", "show", "search", "the nearest", "the nearby", "nearest", "nearby"]

    for _ in range(2):

        for prefix in prefixes:

            if t.startswith(prefix):

                t = t[len(prefix):].strip()

                t = re.sub(r"^(the|a|an)\s+", "", t).strip()

    

    if loc_text:

        t = re.sub(rf"(?i)\b(?:in|near|around|at)\s+{re.escape(loc_text)}\b", "", t).strip()

    

    t = re.sub(r"\b(near me|nearby|nearest|around me)\b", "", t).strip()

    return t if t else None

async def parse_message(message: str) -> ParsedMessage:

    

    ai_data = await _parse_with_gemini(message)

    

    if ai_data:

        try:

            intent = ai_data.get("intent", "unknown")

            category_val = ai_data.get("category")

            category = next((c for c in BusinessCategory if c.value == category_val), None)

            

            when_val = ai_data.get("when")

            when = datetime.fromisoformat(when_val) if when_val else None

            

            return ParsedMessage(

                intent=intent,

                category=category,

                place_type=_PLACE_TYPE_BY_CATEGORY.get(category) if category else None,

                location_text=ai_data.get("location"),

                when=when,

                target_text=ai_data.get("target_text"),

                raw=message,

                search_term=ai_data.get("search_term"),

            )

        except Exception as e:

            logger.warning("ai_parse_conversion.failed", error=str(e))

    

    intent = _detect_intent(message)

    category = _extract_category(message)

    location_text = _extract_location(message)

    

    return ParsedMessage(

        intent=intent,

        category=category,

        place_type=_PLACE_TYPE_BY_CATEGORY.get(category) if category else None,

        location_text=location_text,

        when=_extract_when(message) if intent == "book" else None,

        target_text=_extract_target(message) if intent == "book" else None,

        raw=message,

        search_term=_extract_search_term(message, intent, location_text),

    )

