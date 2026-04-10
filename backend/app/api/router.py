from fastapi import APIRouter

from app.api.routes import appointments, auth, businesses, chat

api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

api_router.include_router(businesses.router, prefix="/businesses", tags=["businesses"])

api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])

api_router.include_router(chat.router, prefix="/chat", tags=["chat"])

