import asyncio

from app.services.google_maps import GoogleMapsClient

from app.chatbot.engine import _resolve_location, ClientLocation

from app.chatbot.nlu import parse_message

from app.db.session import engine, AsyncSessionLocal

from app.core.logging import logger

from sqlalchemy.orm import sessionmaker

async def verify_geocoding():

    print("--- Testing Geocoding Fallback ---")

    

    

    

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    

    async with async_session() as db:

        

        maps = GoogleMapsClient(api_key="INVALID_KEY")

        

        

        parsed = await parse_message("find bakeries in vijayawada")

        print(f"Parsed location: {parsed.location_text}")

        

        try:

            loc = await _resolve_location(db, parsed, None, maps)

            print(f"SUCCESS: Resolved 'vijayawada' to Lat: {loc.latitude}, Lon: {loc.longitude}")

        except Exception as e:

            print(f"FAILURE: Could not resolve 'vijayawada': {e}")

        

        parsed_london = await parse_message("hospitals in London")

        try:

            loc_london = await _resolve_location(db, parsed_london, None, maps)

            print(f"SUCCESS: Resolved 'London' to Lat: {loc_london.latitude}, Lon: {loc_london.longitude}")

        except Exception as e:

            print(f"FAILURE: Could not resolve 'London': {e}")

    print("--- Verification Complete ---")

if __name__ == "__main__":

    asyncio.run(verify_geocoding())

