import asyncio, os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

async def run():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("No DATABASE_URL")
        return
    db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://')
    db_url = db_url.replace('postgres://', 'postgresql+asyncpg://')
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        res = await conn.execute(text('SELECT COUNT(*) FROM businesses'))
        print('COUNT:', res.scalar())
        
        # Let's also check how many have NULL embeddings
        res2 = await conn.execute(text('SELECT COUNT(*) FROM businesses WHERE embedding IS NULL'))
        print('NULL EMBEDDINGS COUNT:', res2.scalar())

if __name__ == "__main__":
    asyncio.run(run())
