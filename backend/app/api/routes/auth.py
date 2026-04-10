from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password

from app.db.models import User

from app.db.session import get_db

from app.schemas.auth import Token, UserCreate, UserOut

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=201)

async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserOut:

    existing = await db.execute(select(User).where(User.email == payload.email))

    if existing.scalar_one_or_none():

        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=payload.email, hashed_password=hash_password(payload.password))

    db.add(user)

    await db.commit()

    await db.refresh(user)

    return UserOut(id=str(user.id), email=user.email)

@router.post("/login", response_model=Token)

async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)) -> Token:

    result = await db.execute(select(User).where(User.email == form.username))

    user = result.scalar_one_or_none()

    if not user or not verify_password(form.password, user.hashed_password):

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=str(user.id))

    return Token(access_token=token)

