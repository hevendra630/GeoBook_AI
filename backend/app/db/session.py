from __future__ import annotations

import uuid

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Strip PgBouncer parameter — asyncpg does not support it
clean_url = settings.database_url.replace("?pgbouncer=true", "").replace("&pgbouncer=true", "")


engine: AsyncEngine = create_async_engine(
    clean_url,
    # NullPool lets PgBouncer handle connection pooling and avoids double-pooling.
    poolclass=NullPool,
    connect_args={
        # Disable prepared statement cache — required for PgBouncer transaction mode.
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "server_settings": {"jit": "off"},
    },
)


@event.listens_for(engine.sync_engine, "connect")
def _register_uuid_codec(dbapi_conn, connection_record):
    """
    Register a text-mode UUID codec on every new asyncpg connection.

    asyncpg sends Python uuid.UUID objects as native binary UUIDs by default,
    but Supabase PgBouncer (transaction-mode pooling) breaks that binary
    type-negotiation, causing:
        DatatypeMismatchError: column "id" is of type uuid but expression
        is of type character varying

    Using SQLAlchemy's sync 'connect' event with run_async() lets us call
    the async set_type_codec without needing the unsupported 'init' kwarg.
    """
    dbapi_conn.run_async(
        lambda conn: conn.set_type_codec(
            "uuid",
            encoder=str,
            decoder=uuid.UUID,
            format="text",
            schema="pg_catalog",
        )
    )


AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncSession:

    async with AsyncSessionLocal() as session:

        yield session
