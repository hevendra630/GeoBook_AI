from __future__ import annotations

from datetime import datetime

from uuid import UUID

from pydantic import Field

from app.schemas.common import APIModel

class AppointmentCreate(APIModel):

    business_id: str

    start_at: datetime

    notes: str | None = None

    duration_minutes: int = Field(default=30, ge=10, le=240)

class AppointmentOut(APIModel):

    id: UUID

    user_id: UUID

    business_id: UUID

    start_at: datetime

    end_at: datetime

    status: str

    notes: str | None = None

