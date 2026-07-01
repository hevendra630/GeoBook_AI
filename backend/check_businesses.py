import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models import Business

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Business))
        for b in res.scalars():
            print(f"Name: {b.name}, Cat: {b.category}, Addr: {b.address}, Lat: {b.latitude}, Lon: {b.longitude}")

asyncio.run(main())
