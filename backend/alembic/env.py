from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.db.base import Base

# Alembic Config object, provides access to values within alembic.ini
config = context.config
#uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _load_env_file_if_present() -> None:
    """
    Minimal .env loader for Alembic.
    Alembic runs before the FastAPI app; we avoid importing app Settings here.
    """

    # Expected working directory is backend/, but be defensive.
    candidates = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(__file__), "..", ".env"),
    ]
    for path in candidates:
        path = os.path.abspath(path)
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                for raw in f.readlines():
                    line = raw.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    # Do not override existing process env.
                    os.environ.setdefault(k, v)
        except OSError:
            pass
        break


def _sync_database_url() -> str:
    # Alembic uses a sync engine. Convert async URL if present.
    _load_env_file_if_present()
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Create backend/.env (copy from .env.example) "
            "or set DATABASE_URL in your shell environment."
        )
    return url.replace("postgresql+asyncpg://", "postgresql://").replace("?pgbouncer=true", "").replace("&pgbouncer=true", "").replace(":6543/", ":5432/") + "?sslmode=require"


def run_migrations_offline() -> None:
    url = _sync_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _sync_database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

