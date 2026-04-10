from __future__ import annotations

from datetime import datetime, timedelta, timezone

from typing import Any

from jose import jwt

from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:

    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:

    return pwd_context.verify(password, hashed_password)

def create_access_token(subject: str, expires_minutes: int | None = None, extra: dict[str, Any] | None = None) -> str:

    expire = datetime.now(timezone.utc) + timedelta(

        minutes=expires_minutes if expires_minutes is not None else settings.jwt_access_token_expire_minutes

    )

    to_encode: dict[str, Any] = {"sub": subject, "exp": expire}

    if extra:

        to_encode.update(extra)

    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict[str, Any]:

    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

