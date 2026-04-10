from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import APIModel

class ClientLocation(APIModel):

    latitude: float

    longitude: float

class ChatRequest(APIModel):

    message: str = Field(min_length=1, max_length=4000)

    client_location: ClientLocation | None = None

    session_id: str | None = None

class PlaceResult(APIModel):

    source: str  

    name: str

    address: str

    rating: float | None = None

    distance_meters: float | None = None

    latitude: float | None = None

    longitude: float | None = None

    phone: str | None = None

    maps_url: str | None = None

    business_id: str | None = None

    external_id: str | None = None

class BookingConfirmation(APIModel):

    appointment_id: str

    business_id: str

    start_at: datetime

    end_at: datetime

class ChatResponse(APIModel):

    intent: str

    normalized_location: ClientLocation | None = None

    results: list[PlaceResult] = Field(default_factory=list)

    booking: BookingConfirmation | None = None

    assistant_message: str

    session_id: str | None = None

class ChatSessionMeta(APIModel):

    id: str

    title: str

    updated_at: datetime

class ChatSessionDetail(ChatSessionMeta):

    messages: list[dict]

