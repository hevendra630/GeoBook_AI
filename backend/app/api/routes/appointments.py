from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user

from app.db.models import User

from app.db.session import get_db

from app.schemas.appointment import AppointmentCreate, AppointmentOut

from app.services.appointments import create_appointment, send_booking_email_if_configured

router = APIRouter()

@router.post("", response_model=AppointmentOut, status_code=201)

async def book_appointment(

    payload: AppointmentCreate,

    background_tasks: BackgroundTasks,

    db: AsyncSession = Depends(get_db),

    user: User = Depends(get_current_user),

) -> AppointmentOut:

    appt = await create_appointment(

        db,

        user_id=user.id,

        business_id=UUID(payload.business_id),

        start_at=payload.start_at,

        duration_minutes=payload.duration_minutes,

        notes=payload.notes,

    )

    

    

    from sqlalchemy import select

    from app.db.models import Business

    bres = await db.execute(select(Business).where(Business.id == UUID(payload.business_id)))

    business = bres.scalar_one_or_none()

    if business and business.email:

        background_tasks.add_task(send_booking_email_if_configured, business=business, appointment=appt)

    return AppointmentOut.model_validate(appt)

