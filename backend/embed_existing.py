import asyncio, os
import google.generativeai as genai
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text, select
from dotenv import load_dotenv
from app.db.models import Business

load_dotenv()

async def run():
    db_url = os.getenv('DATABASE_URL')
    if not db_url: return
    db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://')
    db_url = db_url.replace('postgres://', 'postgresql+asyncpg://')
    
    engine = create_async_engine(db_url)
    Session = async_sessionmaker(engine)
    
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    
    async with Session() as db:
        res = await db.execute(select(Business).where(Business.embedding.is_(None)))
        businesses = list(res.scalars().all())
        print(f"Found {len(businesses)} businesses needing embeddings.")
        
        batch_size = 50
        for i in range(0, len(businesses), batch_size):
            batch = businesses[i:i+batch_size]
            texts = [f"{b.name} - {b.category.value} - {b.description}" for b in batch]
            
            success = False
            retries = 3
            while not success and retries > 0:
                try:
                    result = genai.embed_content(
                        model="models/gemini-embedding-2",
                        content=texts,
                        task_type="retrieval_document"
                    )
                    for b, emb in zip(batch, result['embedding']):
                        b.embedding = emb
                    await db.commit()
                    print(f"Batch {i//batch_size} done.")
                    success = True
                    await asyncio.sleep(5)
                except Exception as e:
                    print(f"Error on batch {i}: {e}")
                    if "429" in str(e):
                        print("Rate limit hit, sleeping for 30s...")
                        await asyncio.sleep(30)
                    retries -= 1

if __name__ == "__main__":
    asyncio.run(run())
