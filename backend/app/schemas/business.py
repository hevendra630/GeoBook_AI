from __future__ import annotations

from uuid import UUID

from pydantic import EmailStr, Field

from app.db.models import BusinessCategory

from app.schemas.common import APIModel

class AvailabilityRuleCreate(APIModel):

    weekday: int = Field(ge=0, le=6)

    start_time: str  

    end_time: str  

    slot_minutes: int = Field(default=30, ge=10, le=240)

class BusinessCreate(APIModel):

    name: str = Field(min_length=2, max_length=200)

    category: BusinessCategory

    address: str = Field(min_length=5, max_length=300)

    latitude: float

    longitude: float

    phone: str | None = Field(default=None, max_length=50)

    email: EmailStr | None = None

    description: str | None = None

    availability: list[AvailabilityRuleCreate] = Field(default_factory=list)

class BusinessOut(APIModel):

    id: UUID

    name: str

    category: BusinessCategory

    address: str

    latitude: float

    longitude: float

    phone: str | None = None

    email: EmailStr | None = None

    description: str | None = None

