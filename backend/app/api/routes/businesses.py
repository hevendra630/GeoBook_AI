from __future__ import annotations

from datetime import time

from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user

from app.db.models import Business, BusinessAvailabilityRule, User

from app.db.session import get_db

from app.schemas.business import BusinessCreate, BusinessOut

router = APIRouter()

def _parse_hhmm(s: str) -> time:

    parts = s.strip().split(":")

    if len(parts) != 2:

        raise ValueError("Invalid time format")

    h, m = int(parts[0]), int(parts[1])

    if not (0 <= h <= 23 and 0 <= m <= 59):

        raise ValueError("Invalid time value")

    return time(hour=h, minute=m)

@router.post("", response_model=BusinessOut, status_code=201)

async def create_business(

    payload: BusinessCreate,

    db: AsyncSession = Depends(get_db),

    _: User = Depends(get_current_user),

) -> BusinessOut:

    business = Business(

        name=payload.name,

        category=payload.category,

        address=payload.address,

        latitude=payload.latitude,

        longitude=payload.longitude,

        phone=payload.phone,

        email=str(payload.email) if payload.email else None,

        description=payload.description,

    )

    for rule in payload.availability:

        try:

            start_t = _parse_hhmm(rule.start_time)

            end_t = _parse_hhmm(rule.end_time)

        except ValueError:

            raise HTTPException(status_code=422, detail="Invalid availability time (use HH:MM)")

        business.availability_rules.append(

            BusinessAvailabilityRule(

                weekday=rule.weekday,

                start_time=start_t,

                end_time=end_t,

                slot_minutes=rule.slot_minutes,

            )

        )

    db.add(business)

    await db.commit()

    await db.refresh(business)

    return BusinessOut.model_validate(business)

@router.get("", response_model=list[BusinessOut])

async def list_businesses(db: AsyncSession = Depends(get_db)) -> list[BusinessOut]:

    res = await db.execute(select(Business).order_by(Business.created_at.desc()).limit(200))

    return [BusinessOut.model_validate(b) for b in res.scalars().all()]

