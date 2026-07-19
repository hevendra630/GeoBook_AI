import asyncio, os
from dotenv import load_dotenv
from app.db.session import AsyncSessionLocal
from app.chatbot.engine import handle_chat
from app.schemas.chat import ClientLocation
from app.db.models import User

load_dotenv()

async def run():
    async with AsyncSessionLocal() as db:
        user = User(id="00000000-0000-0000-0000-000000000000", email="test@example.com")
        loc = ClientLocation(latitude=17.3850, longitude=78.4867) # Hyderabad
        try:
            res = await handle_chat(db, user, "find schools", loc)
            print("SUCCESS:")
            print(res)
        except Exception as e:
            print("ERROR!")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run())
