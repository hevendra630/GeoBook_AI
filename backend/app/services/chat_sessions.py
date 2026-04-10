from __future__ import annotations

from datetime import datetime, timezone

from uuid import UUID, uuid4

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatSession

async def get_or_create_session(db: AsyncSession, *, user_id: str, session_id: str | None) -> ChatSession:

    if session_id:

        res = await db.execute(select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id))

        existing = res.scalar_one_or_none()

        if existing:

            return existing

    sess = ChatSession(

        id=str(uuid4()), 

        title="New Chat",

        user_id=user_id, 

        last_results=[], 

        messages=[],

        updated_at=datetime.now(timezone.utc)

    )

    db.add(sess)

    await db.commit()

    await db.refresh(sess)

    return sess

async def get_user_sessions(db: AsyncSession, *, user_id: str) -> list[ChatSession]:

    res = await db.execute(

        select(ChatSession)

        .where(ChatSession.user_id == user_id)

        .order_by(ChatSession.updated_at.desc())

    )

    return res.scalars().all()

async def get_session(db: AsyncSession, *, session_id: str, user_id: str) -> ChatSession | None:

    res = await db.execute(

        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)

    )

    return res.scalar_one_or_none()

async def append_message(db: AsyncSession, *, session: ChatSession, role: str, text: str, payload: dict | None = None) -> None:

    message = {"role": role, "text": text, "ts": int(datetime.now(timezone.utc).timestamp() * 1000)}

    if payload:

        message["payload"] = payload

    

    

    messages = list(session.messages) if session.messages else []

    

    

    if len(messages) == 0 and role == "user":

        session.title = (text[:37] + "...") if len(text) > 40 else text

    messages.append(message)

    session.messages = messages

    session.updated_at = datetime.now(timezone.utc)

    db.add(session)

    await db.commit()

async def update_last_results(db: AsyncSession, *, session: ChatSession, last_results: list[dict]) -> None:

    session.last_results = last_results

    session.updated_at = datetime.now(timezone.utc)

    db.add(session)

    await db.commit()

