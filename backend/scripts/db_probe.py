import asyncio

import os

import sqlalchemy as sa

from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import create_async_engine

async def main() -> None:

    load_dotenv(".env")

    url = os.environ.get("DATABASE_URL")

    print("DATABASE_URL:", url)

    if not url:

        raise SystemExit("DATABASE_URL is not set")

    engine = create_async_engine(url)

    async with engine.begin() as conn:

        r = await conn.execute(sa.text("select 1"))

        print("select1:", r.scalar())

        r = await conn.execute(sa.text("select count(1) from users"))

        print("users rows:", r.scalar())

if __name__ == "__main__":

    asyncio.run(main())

