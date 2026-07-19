import asyncio
from sqlalchemy import text
from app.db.session import engine

async def run():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TYPE businesscategory ADD VALUE IF NOT EXISTS 'other'"))
            print("Successfully added 'other' to businesscategory ENUM")
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(run())
