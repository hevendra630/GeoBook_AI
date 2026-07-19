from __future__ import annotations

import re

from dataclasses import dataclass

from datetime import datetime, time

from uuid import UUID, uuid4

from fastapi import HTTPException

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.chatbot.nlu import ParsedMessage, parse_message

from app.core.logging import logger

from app.db.models import Business, BusinessAvailabilityRule, BusinessCategory, User

from app.schemas.chat import (
    BookingConfirmation,
    ChatRequest,
    ChatResponse,
    ClientLocation,
    PlaceResult,
)

from app.services.appointments import create_appointment

from app.services.chat_sessions import get_or_create_session, update_last_results

from app.services.embeddings import generate_embedding

from app.services.business_search import search_businesses

from app.services.geo import haversine_distance_meters

from app.services.google_maps import GoogleMapsClient

from app.services.osm import OSMClient, OSMPlaceType

from rapidfuzz import fuzz

@dataclass(frozen=True)

class ChatResult:

    intent: str

    normalized_location: ClientLocation | None

    results: list[PlaceResult]

    booking: BookingConfirmation | None

    assistant_message: str

    session_id: str | None = None

def _extract_duration_minutes(text: str) -> int:

    t = text.lower()

    m = re.search(r"\bfor\s+(\d+)\s*(minutes|minute|mins|min)\b", t)

    if m:

        return max(10, min(240, int(m.group(1))))

    h = re.search(r"\bfor\s+(\d+)\s*(hours|hour|hrs|hr)\b", t)

    if h:

        return max(10, min(240, int(h.group(1)) * 60))

    return 30

async def _resolve_location(

    db: AsyncSession,

    parsed: ParsedMessage,

    client_location: ClientLocation | None,

    maps: GoogleMapsClient,

) -> ClientLocation:

    if parsed.location_text:

        

        ctx = None

        try:

            ctx = await maps.geocode_context(parsed.location_text)

        except Exception as e:

            logger.warning("google_geocode.failed", error=str(e), location=parsed.location_text)

        if not ctx:

            

            logger.info("geocoding_fallback.photon", address=parsed.location_text)

            fallback_coords = await maps.photon_geocode(parsed.location_text)

            

            if not fallback_coords:

                

                logger.info("geocoding_fallback.nominatim", address=parsed.location_text)

                fallback_coords = await maps.nominatim_geocode(parsed.location_text)

            if fallback_coords:

                return ClientLocation(latitude=fallback_coords[0], longitude=fallback_coords[1])

        if ctx:

            

            try:

                setattr(parsed, "_overpass_area_id", ctx.overpass_area_id)

            except Exception:

                pass

            return ClientLocation(latitude=ctx.latitude, longitude=ctx.longitude)

        

        if client_location:

            logger.info("geocode.fallback_to_gps", reason="geocode_failed", location=parsed.location_text)

            return client_location

        

        loc_q = parsed.location_text.strip().lower()

        res = await db.execute(select(Business).order_by(Business.created_at.desc()).limit(500))

        businesses = list(res.scalars().all())

        best: tuple[int, Business] | None = None

        for b in businesses:

            addr = (b.address or "").lower()

            score = fuzz.partial_ratio(loc_q, addr) if addr else 0

            if best is None or score > best[0]:

                best = (score, b)

        

        if best and best[0] >= 80:

            b = best[1]

            return ClientLocation(latitude=float(b.latitude), longitude=float(b.longitude))

        raise HTTPException(

            status_code=422,

            detail="Could not resolve the provided location. Try a more specific place name or enable geolocation.",

        )

    if client_location:

        return client_location

    raise HTTPException(status_code=422, detail="Missing location. Provide a location or enable geolocation.")

async def handle_chat(

    db: AsyncSession,

    user: User,

    message: str,

    client_location: ClientLocation | None,

    *,

    session: object | None = None,

    on_db_booking_email: object | None = None,

) -> ChatResult:

    parsed = await parse_message(message)

    

    import dataclasses
    if session is not None and getattr(session, "messages", None):
        messages = getattr(session, "messages")
        if messages:
            last_msg = messages[-1]
            if last_msg.get("role") == "assistant" and "Which business would you like to book?" in last_msg.get("text", ""):
                parsed = dataclasses.replace(parsed, intent="book", target_text=message)
                
    logger.info(f"ENGINE_DEBUG: Message='{message}', Intent='{parsed.intent}', Category='{parsed.category}', Loc='{parsed.location_text}'")

    try:
        with open("engine_debug.log", "a") as f:
            f.write(f"Message='{message}', Intent='{parsed.intent}', Category='{parsed.category}', Loc='{parsed.location_text}'\n")
    except Exception:
        pass

    maps = GoogleMapsClient()

    loc: ClientLocation | None = None

    if parsed.intent in ("search", "book") or parsed.location_text or client_location:

        loc = await _resolve_location(db, parsed, client_location, maps)

    if parsed.intent == "search":

        assert loc is not None

        results: list[PlaceResult] = []

        

        

        

        

        

        

        dist_ref = loc
        search_vector = await generate_embedding(parsed.raw)
        
        db_hits = await search_businesses(
            db,
            latitude=dist_ref.latitude,
            longitude=dist_ref.longitude,
            category=parsed.category,
            query=parsed.raw,
            limit=15,
            search_vector=search_vector,
        )

        if not db_hits and parsed.category is None:
            broad_hits = await search_businesses(
                db,
                latitude=loc.latitude,
                longitude=loc.longitude,
                category=None,
                query=parsed.raw,
                limit=25,
                search_vector=search_vector,
            )

            

            

            loc_text = (parsed.location_text or "").strip().lower()

            filtered = []

            for h in broad_hits:

                addr = (h.business.address or "").lower()

                addr_match = fuzz.partial_ratio(loc_text, addr) if loc_text and addr else 0

                if h.relevance >= 70 or addr_match >= 80:

                    filtered.append(h)

            db_hits = filtered[:15]

        seen_business_ids: set[str] = set()

        for h in db_hits:

            b = h.business

            bid = str(b.id)

            if bid in seen_business_ids:

                continue

            seen_business_ids.add(bid)

            

        

        from app.chatbot.nlu import _PLACE_TYPE_BY_CATEGORY

        g_type = _PLACE_TYPE_BY_CATEGORY.get(parsed.category) if parsed.category else None

        keyword = parsed.search_term or (parsed.category.value if parsed.category else None) or parsed.raw

        google_places = []

        if keyword:

            area_id = getattr(parsed, "_overpass_area_id", None)

            google_places = await maps.nearby_search(

                latitude=loc.latitude,

                longitude=loc.longitude,

                keyword=str(keyword),

                place_type=g_type,

                overpass_area_id=area_id,

            )

            

            if parsed.category:

                cat_name = parsed.category.value.lower()

                filtered = []

                

                CATEGORY_SYNONYMS = {

                    BusinessCategory.salon: ["salon", "style", "barber", "spa", "cut", "hair", "beauty", "parlour", "grooming", "trim", "saloon", "saloons"],

                    BusinessCategory.restaurant: ["food", "restaurant", "cafe", "diner", "pizza", "burger", "eat", "bake", "coffee", "hotel", "canteen", "kitchen", "biryani"],

                    BusinessCategory.hospital: ["hospital", "emergency", "medical", "er", "care", "diagnostic"],

                    BusinessCategory.dental: ["dental", "dentist", "teeth", "ortho"],

                    BusinessCategory.clinic: ["clinic", "doctor", "physician", "health center", "medical clinic", "nursing home"],

                }

                synonyms = CATEGORY_SYNONYMS.get(parsed.category, [cat_name])

                for p in google_places:

                    name = p.name.lower()

                    addr = (p.address or "").lower()

                    is_cat_match = any(s in name for s in synonyms)

                    town_match = True

                    if parsed.location_text:

                        town = parsed.location_text.lower()

                        town_match = town in name or town in addr

                    

                    # Relaxed filter: if we have a specific category, Google already filtered by place_type.

                    # We'll just include all of them unless they explicitly fail both checks terribly, but 

                    # actually it's safer to just include all Google places returned for this location.

                    filtered.append(p)

                

                google_places = filtered

        

        results: list[PlaceResult] = []

        

        

        for h in db_hits:

            b = h.business

            

            if parsed.category and b.category != parsed.category:

                continue

            results.append(

                PlaceResult(

                    source="local",

                    name=b.name,

                    address=b.address,

                    rating=None,

                    distance_meters=h.distance_meters,

                    latitude=float(b.latitude),

                    longitude=float(b.longitude),

                    phone=b.phone,

                    maps_url=f"https://www.openstreetmap.org/?mlat={b.latitude}&mlon={b.longitude}#map=18/{b.latitude}/{b.longitude}",

                    business_id=str(b.id),

                )

            )

        

        for p in google_places:

            dist = haversine_distance_meters(dist_ref.latitude, dist_ref.longitude, p.latitude, p.longitude)

            results.append(

                PlaceResult(

                    source="google",

                    name=p.name,

                    address=p.address or "",

                    rating=p.rating,

                    distance_meters=dist,

                    latitude=p.latitude,

                    longitude=p.longitude,

                    phone=p.phone,

                    maps_url=p.maps_url,

                    business_id=None,

                    external_id=p.place_id,

                )

            )

        

        if not google_places and keyword:

            logger.info("place_search_fallback.osm", keyword=keyword)

            osm_type = None

            if parsed.category == BusinessCategory.restaurant: osm_type = "restaurant"

            elif parsed.category == BusinessCategory.school: osm_type = "school"

            elif parsed.category == BusinessCategory.hospital: osm_type = "hospital"

            elif parsed.category == BusinessCategory.police: osm_type = "police"

            elif parsed.category == BusinessCategory.bus_stop: osm_type = "bus_stop"

            elif parsed.category == BusinessCategory.salon: osm_type = "salon"

            elif parsed.category == BusinessCategory.dental: osm_type = "dental"

            elif parsed.category == BusinessCategory.clinic: osm_type = "clinic"

            

            if osm_type:

                try:

                    osm = OSMClient()

                    osm_places = await osm.nearby_search(

                        latitude=loc.latitude,

                        longitude=loc.longitude,

                        place_type=osm_type,

                        overpass_area_id=getattr(parsed, "_overpass_area_id", None)

                    )

                    for p in osm_places:

                        dist = haversine_distance_meters(dist_ref.latitude, dist_ref.longitude, p.latitude, p.longitude)

                        results.append(

                            PlaceResult(

                                source="osm",

                                name=p.name,

                                address=p.address or "",

                                rating=None,

                                distance_meters=dist,

                                latitude=p.latitude,

                                longitude=p.longitude,

                                phone=p.phone,

                                maps_url=p.maps_url,

                                business_id=None,

                                external_id=f"osm_{p.osm_type}_{p.osm_id}",

                            )

                        )

                except Exception as e:

                    logger.warning("osm_fallback.failed", error=str(e))

        results.sort(key=lambda x: (x.distance_meters or 9e18))

        

        

        results = results[:15]
        
        if not results:
            assistant_message = f"I couldn't find any businesses matching your request in that area."
        else:
            assistant_message = "Here are the closest matches I found."
        
        if session is not None and results:

            

            await update_last_results(db, session=session, last_results=[r.model_dump() for r in results])

        return ChatResult(

            intent="search",

            normalized_location=loc,

            results=results[:10],

            booking=None,

            assistant_message=assistant_message,

            session_id=str(getattr(session, "id", "")) if session is not None else None,

        )

    if parsed.intent == "book":

        assert loc is not None

        if not parsed.when:
            # Try to recover 'when' from previous user messages in the session
            recovered_when = None
            if session is not None and getattr(session, "messages", None):
                from app.chatbot.nlu import _extract_when
                for msg in reversed(getattr(session, "messages")):
                    if msg.get("role") == "user":
                        recovered_when = _extract_when(msg.get("text", ""))
                        if recovered_when:
                            parsed = dataclasses.replace(parsed, when=recovered_when)
                            break
            
            if not parsed.when:
                return ChatResult(
                    intent="book",
                    normalized_location=loc,
                    results=[],
                    booking=None,
                    assistant_message="Please include a date and time for your appointment (e.g., 'tomorrow at 4pm').",
                    session_id=str(session.id) if session else None
                )

        duration = _extract_duration_minutes(parsed.raw)

        chosen: Business | None = None

        

        if session is not None and getattr(session, "last_results", None):

            last_results = getattr(session, "last_results", [])

            

            candidates = [r for r in last_results if fuzz.partial_ratio(str(parsed.target_text or "").lower(), str(r.get("name", "")).lower()) >= 75]

            

            

            if not candidates or (parsed.target_text and parsed.target_text.lower() in ("this", "it", "one", "the")):

                

                m = re.search(r"\b(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)\b", message.lower())

                if m:

                    word = m.group(1)

                    idx_map = {

                        "first": 0, "1st": 0,

                        "second": 1, "2nd": 1,

                        "third": 2, "3rd": 2,

                        "fourth": 3, "4th": 3,

                        "fifth": 4, "5th": 4,

                    }

                    idx = idx_map.get(word)

                    if idx is not None and idx < len(last_results):

                        candidates = [last_results[idx]]

            if not candidates:

                current_results = []

                if session is not None and getattr(session, "last_results", None):

                    current_results = [PlaceResult(**r) for r in getattr(session, "last_results")]

                return ChatResult(

                    intent="book",

                    normalized_location=loc,

                    results=current_results,

                    booking=None,

                    assistant_message=f"I couldn't find '{parsed.target_text}' in the recent results. Which place would you like to book?",

                )

            

            ref = candidates[0]

            if ref.get("business_id"):

                bid = str(UUID(str(ref["business_id"])))

                bres = await db.execute(select(Business).where(Business.id == bid))

                chosen = bres.scalar_one_or_none()

            elif ref.get("external_id"):

                new_business = Business(

                    id=str(uuid4()),

                    name=ref.get("name", "Unknown Google Place"),

                    category=BusinessCategory.other,

                    address=ref.get("address", ""),

                    latitude=ref.get("latitude", 0.0),

                    longitude=ref.get("longitude", 0.0),

                    phone=ref.get("phone"),

                )

                db.add(new_business)

                

                

                for day in range(7):

                    rule = BusinessAvailabilityRule(

                        id=str(uuid4()),

                        business_id=new_business.id,

                        weekday=day,

                        start_time=time(0, 0),

                        end_time=time(23, 59),

                        slot_minutes=30

                    )

                    db.add(rule)

                

                await db.flush()

                chosen = new_business

            else:

                raise HTTPException(

                    status_code=422,

                    detail="Could not identify the business to book.",

                )

        

        if chosen is None:

            category = parsed.category

            candidates = await search_businesses(

                db,

                latitude=loc.latitude,

                longitude=loc.longitude,

                category=category,

                query=parsed.raw,

                limit=10,

            )

            if not candidates:

                raise HTTPException(status_code=404, detail="No registered businesses found to book.")

            chosen = candidates[0].business

        try:

            appt = await create_appointment(

                db,

                user_id=str(user.id),

                business_id=str(chosen.id),

                start_at=parsed.when,

                duration_minutes=duration,

                notes=None,

            )

            logger.info("appointment.created", user_id=str(user.id), business_id=str(chosen.id), appointment_id=str(appt.id))

            if on_db_booking_email is not None:

                try:

                    on_db_booking_email(chosen, appt)

                except Exception:

                    

                    logger.exception("email.booking_failed", business_id=str(chosen.id), appointment_id=str(appt.id))

            booking = BookingConfirmation(

                appointment_id=str(appt.id),

                business_id=str(chosen.id),

                start_at=appt.start_at,

                end_at=appt.end_at,

            )

            msg = f"Booking successful! I've scheduled your appointment with {chosen.name} for {appt.start_at.strftime('%Y-%m-%d %H:%M')}."

            

            

            from app.core.config import settings

            has_smtp = bool(settings.smtp_host and settings.smtp_from_email)

            if not chosen.email:

                msg += " (Note: This business hasn't provided an email address, so they won't be notified automatically. You may want to call them.)"

            elif not has_smtp:

                msg += " (Note: Email notifications are currently disabled in the server settings.)"

            else:

                msg += " They should receive an email notification shortly."

            

            current_results = []

            if session is not None and getattr(session, "last_results", None):

                

                current_results = [PlaceResult(**r) for r in getattr(session, "last_results")]

            return ChatResult(

                intent="book",

                normalized_location=loc,

                results=current_results,

                booking=booking,

                assistant_message=msg,

                session_id=str(getattr(session, "id", "")) if session is not None else None,

            )

        except HTTPException as e:

            

            fail_msg = f"I'm sorry, I couldn't complete your booking at {chosen.name}. {e.detail}. Please try a different time or date."

            

            current_results = []

            if session is not None and getattr(session, "last_results", None):

                current_results = [PlaceResult(**r) for r in getattr(session, "last_results")]

            return ChatResult(

                intent="book",

                normalized_location=loc,

                results=current_results,

                booking=None,

                assistant_message=fail_msg,

                session_id=str(getattr(session, "id", "")) if session is not None else None,

            )

    return ChatResult(

        intent="unknown",

        normalized_location=loc,

        results=[],

        booking=None,

        assistant_message="Tell me what you want to do (e.g., 'Find the nearest hospital' or 'Book a dental appointment tomorrow at 4pm').",

    )

