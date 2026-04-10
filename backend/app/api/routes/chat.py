from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user

from app.chatbot.engine import handle_chat

from app.db.models import User

from app.db.session import get_db

from app.schemas.chat import ChatRequest, ChatResponse, ChatSessionMeta, ChatSessionDetail

from app.services.appointments import send_booking_email_if_configured

from app.services.chat_sessions import get_or_create_session, get_user_sessions, get_session, append_message

router = APIRouter()

@router.post("", response_model=ChatResponse)

async def chat(

    payload: ChatRequest,

    background_tasks: BackgroundTasks,

    db: AsyncSession = Depends(get_db),

    user: User = Depends(get_current_user),

) -> ChatResponse:

    session = await get_or_create_session(db, user_id=user.id, session_id=payload.session_id)

    

    await append_message(db, session=session, role="user", text=payload.message)

    def enqueue_email(business, appt):

        background_tasks.add_task(send_booking_email_if_configured, business=business, appointment=appt)

    result = await handle_chat(

        db,

        user,

        payload.message,

        payload.client_location,

        session=session,

        on_db_booking_email=enqueue_email,

    )

    

    

    resp = ChatResponse(

        intent=result.intent,

        normalized_location=result.normalized_location,

        results=result.results,

        booking=result.booking,

        assistant_message=result.assistant_message,

        session_id=result.session_id or str(session.id),

    )

    await append_message(db, session=session, role="assistant", text=result.assistant_message, payload=resp.model_dump(mode="json"))

    return resp

@router.get("/sessions", response_model=list[ChatSessionMeta])

async def list_sessions(

    db: AsyncSession = Depends(get_db),

    user: User = Depends(get_current_user),

):

    sessions = await get_user_sessions(db, user_id=user.id)

    return [

        ChatSessionMeta(

            id=s.id,

            title=s.title,

            updated_at=s.updated_at

        ) for s in sessions

    ]

@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)

async def get_session_detail(

    session_id: str,

    db: AsyncSession = Depends(get_db),

    user: User = Depends(get_current_user),

):

    session = await get_session(db, session_id=session_id, user_id=user.id)

    if not session:

        raise HTTPException(status_code=404, detail="Session not found")

    

    return ChatSessionDetail(

        id=session.id,

        title=session.title,

        updated_at=session.updated_at,

        messages=session.messages

    )

