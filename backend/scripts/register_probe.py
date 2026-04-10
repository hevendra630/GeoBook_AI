import os

import sys

import asyncio

import traceback

from dotenv import load_dotenv

from sqlalchemy import select

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import hash_password

from app.db.models import User

from app.db.session import AsyncSessionLocal

async def main() -> None:

    load_dotenv(".env")

    email = "probe@example.com"

    try:

        async with AsyncSessionLocal() as db:

            existing = await db.execute(select(User).where(User.email == email))

            if existing.scalar_one_or_none():

                print("user already exists")

                return

            user = User(email=email, hashed_password=hash_password("password123"))

            db.add(user)

            await db.commit()

            await db.refresh(user)

            print("created user id:", user.id)

    except Exception:

        traceback.print_exc()

if __name__ == "__main__":

    asyncio.run(main())

