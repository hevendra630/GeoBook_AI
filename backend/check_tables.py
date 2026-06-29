import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run():
    url = os.getenv('DATABASE_URL').replace('postgresql+asyncpg', 'postgresql')
    conn = await asyncpg.connect(url, ssl='require')
    rows = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    for row in rows:
        print(row['table_name'])
    await conn.close()

if __name__ == "__main__":
    asyncio.run(run())
