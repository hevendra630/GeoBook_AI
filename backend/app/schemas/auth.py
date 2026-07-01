from __future__ import annotations

from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.common import APIModel

class UserCreate(APIModel):

    email: EmailStr

    password: str = Field(min_length=8, max_length=128)

class Token(APIModel):

    access_token: str

    token_type: str = "bearer"

class UserOut(APIModel):

    id: UUID

    email: EmailStr

