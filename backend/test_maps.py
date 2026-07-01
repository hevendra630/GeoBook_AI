import asyncio
from app.services.osm import OSMClient

async def main():
    c = OSMClient()
    loc = await c.geocode_context('guntur')
    print("Geocode:", loc)
    res = await c.nearby_search(
        latitude=loc.latitude,
        longitude=loc.longitude,
        place_type='salon',
        overpass_area_id=loc.overpass_area_id
    )
    print('Found:', len(res))
    for r in res:
        print(r.name, r.address)

asyncio.run(main())
