from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, status

from fastapi.security import OAuth2PasswordBearer

from jose import JWTError

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token

from app.db.models import User

from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(

    db: AsyncSession = Depends(get_db),

    token: str = Depends(oauth2_scheme),

) -> User:

    try:

        payload = decode_token(token)

        sub = payload.get("sub")

        if not sub:

            raise ValueError("Missing subject")

        user_id = str(UUID(sub))

    except (JWTError, ValueError) as e:

        from app.core.logging import logger

        logger.warning("auth.token_invalid", error=str(e))

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED, 

            detail=f"Invalid token: {str(e)}"

        )

    result = await db.execute(select(User).where(User.id == user_id))

    user = result.scalar_one_or_none()

    if not user or not user.is_active:

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user

