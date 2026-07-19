import google.generativeai as genai
from app.core.config import settings
from app.core.logging import logger

if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)

async def generate_embedding(text: str) -> list[float] | None:
    if not settings.gemini_api_key or not text:
        return None
    try:
        # We use a wrapper or synchronous call in async context, but embed_content is fast.
        # Alternatively, genai provides async methods for chat, but embed_content is sync in this SDK version.
        # It's fine to run it directly for now or wrap in an executor.
        result = genai.embed_content(
            model="models/gemini-embedding-2",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        logger.error("embedding_failed", error=str(e))
        return None
