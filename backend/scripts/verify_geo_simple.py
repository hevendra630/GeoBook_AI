import asyncio

import httpx

from app.services.google_maps import GoogleMapsClient

from app.core.config import settings

async def test_photon():

    print(f"--- Testing Photon Geocoding Fallback ---")

    print(f"Base URL: {settings.osm_photon_base_url}")

    

    maps = GoogleMapsClient(api_key="INVALID_KEY")

    

    

    address = "vijayawada"

    coords = await maps.photon_geocode(address)

    

    if coords:

        print(f"SUCCESS: Resolved '{address}' to {coords}")

    else:

        print(f"FAILURE: Could not resolve '{address}'")

    

    address2 = "London"

    coords2 = await maps.photon_geocode(address2)

    if coords2:

        print(f"SUCCESS: Resolved '{address2}' to {coords2}")

    else:

        print(f"FAILURE: Could not resolve '{address2}'")

if __name__ == "__main__":

    asyncio.run(test_photon())

