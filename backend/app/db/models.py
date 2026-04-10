from __future__ import annotations

import enum

from datetime import datetime, time, timezone

from uuid import uuid4

from sqlalchemy import (

    Boolean,

    DateTime,

    Enum,

    ForeignKey,

    Float,

    Integer,

    JSON,

    String,

    Text,

    Time,

    UniqueConstraint,

)

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):

    pass

class BusinessCategory(str, enum.Enum):

    restaurant = "restaurant"

    school = "school"

    hospital = "hospital"

    police = "police"

    bus_stop = "bus_stop"

    

    dental = "dental"

    clinic = "clinic"

    salon = "salon"

    other = "other"

class User(Base):

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)

    hashed_password: Mapped[str] = mapped_column(String(255))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(

        DateTime(timezone=True),

        default=lambda: datetime.now(timezone.utc),

    )

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="user")

class Business(Base):

    __tablename__ = "businesses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    name: Mapped[str] = mapped_column(String(200), index=True)

    category: Mapped[BusinessCategory] = mapped_column(Enum(BusinessCategory), index=True)

    address: Mapped[str] = mapped_column(String(300))

    latitude: Mapped[float] = mapped_column(Float)

    longitude: Mapped[float] = mapped_column(Float)

    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    email: Mapped[str | None] = mapped_column(String(320), nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(

        DateTime(timezone=True),

        default=lambda: datetime.now(timezone.utc),

    )

    availability_rules: Mapped[list["BusinessAvailabilityRule"]] = relationship(

        back_populates="business", cascade="all, delete-orphan"

    )

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="business")

class BusinessAvailabilityRule(Base):

    """
    Availability rules are intentionally simple:
    - One rule per weekday + start/end time
    - Appointment slots are generated on-demand by checking conflicts
    """

    __tablename__ = "business_availability_rules"

    __table_args__ = (UniqueConstraint("business_id", "weekday", "start_time", "end_time"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    business_id: Mapped[str] = mapped_column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"))

    weekday: Mapped[int] = mapped_column(Integer)  

    start_time: Mapped[time] = mapped_column(Time)

    end_time: Mapped[time] = mapped_column(Time)

    slot_minutes: Mapped[int] = mapped_column(Integer, default=30)

    business: Mapped["Business"] = relationship(back_populates="availability_rules")

class AppointmentStatus(str, enum.Enum):

    scheduled = "scheduled"

    cancelled = "cancelled"

class Appointment(Base):

    __tablename__ = "appointments"

    __table_args__ = (UniqueConstraint("business_id", "start_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))

    business_id: Mapped[str] = mapped_column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"))

    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus), default=AppointmentStatus.scheduled)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(

        DateTime(timezone=True),

        default=lambda: datetime.now(timezone.utc),

    )

    user: Mapped["User"] = relationship(back_populates="appointments")

    business: Mapped["Business"] = relationship(back_populates="appointments")

class ChatSession(Base):

    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    title: Mapped[str] = mapped_column(String(100), default="New Chat")

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)

    

    last_results: Mapped[list[dict]] = mapped_column(JSON, default=list)

    

    messages: Mapped[list[dict]] = mapped_column(JSON, default=list)

    updated_at: Mapped[datetime] = mapped_column(

        DateTime(timezone=True),

        default=lambda: datetime.now(timezone.utc),

    )

