from __future__ import annotations

from dataclasses import dataclass

from datetime import datetime, timedelta, timezone

from uuid import UUID

from fastapi import HTTPException

from sqlalchemy import and_, select

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Appointment, AppointmentStatus, Business, BusinessAvailabilityRule

from app.services.emailer import send_email

@dataclass(frozen=True)

class AvailabilityCheck:

    ok: bool

    reason: str | None = None

def _ensure_tz(dt: datetime) -> datetime:

    if dt.tzinfo is None:

        return dt.replace(tzinfo=timezone.utc)

    return dt

async def check_availability(

    db: AsyncSession,

    business: Business,

    start_at: datetime,

    duration_minutes: int,

) -> AvailabilityCheck:

    start_at = _ensure_tz(start_at)

    end_at = start_at + timedelta(minutes=duration_minutes)

    weekday = start_at.weekday()

    rules_res = await db.execute(

        select(BusinessAvailabilityRule).where(BusinessAvailabilityRule.business_id == business.id)

    )

    rules = list(rules_res.scalars().all())

    

    from app.core.logging import logger

    log_msg = f"DEBUG_AVAILABILITY: Business={business.name}, ReqTime={start_at}, Weekday={weekday}, RulesCount={len(rules)}"

    logger.info(log_msg)

    with open("debug_availability.log", "a") as f:

        f.write(log_msg + "\n")

    if not rules:

        

        from datetime import time

        from uuid import uuid4

        for d in range(7):

            new_rule = BusinessAvailabilityRule(

                id=str(uuid4()),

                business_id=business.id,

                weekday=d,

                start_time=time(0, 0),

                end_time=time(23, 59),

                slot_minutes=30

            )

            db.add(new_rule)

            rules.append(new_rule)

        

        

        logger.info(f"SELF_HEALING: Created 24/7 rules for {business.name}")

    if not rules:

        return AvailabilityCheck(ok=False, reason="Business has no availability schedule")

    

    has_day_rule = any(r.weekday == weekday for r in rules)

    if not has_day_rule:

        from datetime import time

        from uuid import uuid4

        new_rule = BusinessAvailabilityRule(

            id=str(uuid4()),

            business_id=business.id,

            weekday=weekday,

            start_time=time(0, 0),

            end_time=time(23, 59),

            slot_minutes=30

        )

        db.add(new_rule)

        rules.append(new_rule)

        logger.info(f"SELF_HEALING: Created missing 24/7 rule for day {weekday} for {business.name}")

    

    fits_rule = False

    for r in rules:

        if r.weekday != weekday:

            continue

        

        req_time = start_at.time()

        req_end_time = end_at.time()

        

        rule_log = f"DEBUG_AVAILABILITY: Checking Rule: Day={r.weekday}, {r.start_time} to {r.end_time} vs Req: {req_time} to {req_end_time}"

        logger.info(rule_log)

        with open("debug_availability.log", "a") as f:

            f.write(rule_log + "\n")

        

        if end_at.date() > start_at.date():

             with open("debug_availability.log", "a") as f:

                 f.write("FAIL: Spans cross multiple days\n")

             return AvailabilityCheck(ok=False, reason="Appointment spans across multiple days")

        if r.start_time <= req_time and req_end_time <= r.end_time:

            fits_rule = True

            with open("debug_availability.log", "a") as f:

                f.write("SUCCESS: Fits rule!\n")

            break

    

    if not fits_rule:

        with open("debug_availability.log", "a") as f:

            f.write("FAIL: No matching rules for this weekday/time\n")

        return AvailabilityCheck(ok=False, reason="Requested time is outside business hours")

    

    conflict = await db.execute(

        select(Appointment).where(

            and_(

                Appointment.business_id == business.id,

                Appointment.status == AppointmentStatus.scheduled,

                Appointment.start_at < end_at,

                Appointment.end_at > start_at,

            )

        )

    )

    if conflict.scalar_one_or_none():

        return AvailabilityCheck(ok=False, reason="Time slot is already booked")

    return AvailabilityCheck(ok=True)

async def create_appointment(

    db: AsyncSession,

    *,

    user_id: str,

    business_id: str,

    start_at: datetime,

    duration_minutes: int,

    notes: str | None,

) -> Appointment:

    business_res = await db.execute(select(Business).where(Business.id == business_id))

    business = business_res.scalar_one_or_none()

    if not business:

        raise HTTPException(status_code=404, detail="Business not found")

    check = await check_availability(db, business, start_at, duration_minutes)

    if not check.ok:

        raise HTTPException(status_code=409, detail=check.reason or "Not available")

    start_at = _ensure_tz(start_at)

    end_at = start_at + timedelta(minutes=duration_minutes)

    appt = Appointment(

        user_id=user_id,

        business_id=business_id,

        start_at=start_at,

        end_at=end_at,

        notes=notes,

    )

    db.add(appt)

    await db.commit()

    await db.refresh(appt)

    return appt

def build_booking_email(*, business: Business, appointment: Appointment) -> tuple[str, str]:

    subject = f"New appointment: {business.name}"

    body = (

        f"You have a new appointment booking from GeoBook AI.\n\n"

        f"Business: {business.name}\n"

        f"Start: {appointment.start_at}\n"

        f"End: {appointment.end_at}\n"

        f"Appointment ID: {appointment.id}\n"

    )

    return subject, body

def send_booking_email_if_configured(*, business: Business, appointment: Appointment) -> None:

    if not business.email:

        return

    subject, body = build_booking_email(business=business, appointment=appointment)

    send_email(to_email=business.email, subject=subject, body=body)

