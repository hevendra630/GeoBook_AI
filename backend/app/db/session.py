from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Ensure pgbouncer parameter is stripped from the URL since asyncpg does not support it
clean_url = settings.database_url.replace("?pgbouncer=true", "").replace("&pgbouncer=true", "")

engine: AsyncEngine = create_async_engine(
    clean_url,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db() -> AsyncSession:

    async with AsyncSessionLocal() as session:

        yield session

