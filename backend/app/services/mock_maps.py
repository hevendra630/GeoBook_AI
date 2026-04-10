from __future__ import annotations

from dataclasses import dataclass

from typing import Any, Literal

from app.core.config import settings

MockPlaceType = Literal["restaurant", "school", "hospital", "police", "bus_stop"]

@dataclass(frozen=True)

class MockPlace:

    osm_type: str

    osm_id: int

    name: str

    address: str | None

    latitude: float

    longitude: float

    phone: str | None = None

    maps_url: str | None = None

@dataclass(frozen=True)

class MockGeocodeContext:

    latitude: float

    longitude: float

    overpass_area_id: int | None = None

class MockClient:

    """Mock client that returns dummy data for testing when OSM services are unavailable."""

    def __init__(self) -> None:

        pass

    def _headers(self) -> dict[str, str]:

        return {"User-Agent": settings.osm_user_agent}

    async def geocode(self, query: str) -> tuple[float, float] | None:

        """Mock geocoding - returns dummy coordinates for common cities."""

        query_lower = query.lower().strip()

        

        mock_locations = {

            "new york": (40.7128, -74.0060),

            "london": (51.5074, -0.1278),

            "paris": (48.8566, 2.3522),

            "tokyo": (35.6762, 139.6503),

            "sydney": (-33.8688, 151.2093),

            "mumbai": (19.0760, 72.8777),

            "delhi": (28.7041, 77.1025),

            "bangalore": (12.9716, 77.5946),

            "chennai": (13.0827, 80.2707),

            "hyderabad": (17.3850, 78.4867),

            "guntur": (16.3067, 80.4365),

        }

        for city, coords in mock_locations.items():

            if city in query_lower:

                return coords

        

        return (40.7128, -74.0060)  

    async def geocode_context(self, query: str) -> MockGeocodeContext | None:

        """Mock geocode context."""

        coords = await self.geocode(query)

        if coords:

            return MockGeocodeContext(latitude=coords[0], longitude=coords[1])

        return None

    async def nearby_search(

        self,

        latitude: float,

        longitude: float,

        place_type: MockPlaceType,

        radius_meters: int = 5000,

        limit: int = 10,

        overpass_area_id: int | None = None,

    ) -> list[MockPlace]:

        """Mock nearby search - returns dummy places."""

        

        mock_data = {

            "restaurant": [

                ("Joe's Pizza", "123 Main St", 0.5, 0.5),

                ("Mama's Italian", "456 Oak Ave", -0.3, 0.7),

                ("Burger King", "789 Pine St", 0.8, -0.2),

                ("Starbucks", "321 Elm St", -0.6, 0.4),

                ("Subway", "654 Maple Ave", 0.2, -0.8),

            ],

            "school": [

                ("Central High School", "100 Education Blvd", 1.0, 0.0),

                ("Lincoln Elementary", "200 Learning St", -0.5, 1.2),

                ("Washington Middle School", "300 Knowledge Ave", 0.7, -0.6),

            ],

            "hospital": [

                ("City General Hospital", "500 Health Way", 0.3, 0.9),

                ("Mercy Medical Center", "600 Care St", -0.8, 0.1),

                ("St. Mary's Hospital", "700 Healing Blvd", 1.1, -0.3),

            ],

            "police": [

                ("Central Police Station", "800 Safety Rd", 0.4, -0.7),

                ("North Precinct", "900 Protection Ave", -0.2, 1.0),

            ],

            "bus_stop": [

                ("Main St & 1st Ave", "Main St & 1st Ave", 0.1, 0.1),

                ("Oak St & 2nd Ave", "Oak St & 2nd Ave", -0.1, 0.2),

                ("Pine St & 3rd Ave", "Pine St & 3rd Ave", 0.2, -0.1),

                ("Elm St & 4th Ave", "Elm St & 4th Ave", -0.3, 0.0),

            ],

        }

        places = mock_data.get(place_type, [])

        results = []

        for i, (name, address, lat_offset, lon_offset) in enumerate(places[:limit]):

            results.append(MockPlace(

                osm_type="node",

                osm_id=1000000 + i,

                name=name,

                address=address,

                latitude=latitude + lat_offset * 0.01,  

                longitude=longitude + lon_offset * 0.01,

                phone="+1-555-0123" if place_type in ["restaurant", "hospital"] else None,

                maps_url=f"https://www.openstreetmap.org/?mlat={latitude + lat_offset * 0.01}&mlon={longitude + lon_offset * 0.01}#map=18/{latitude + lat_offset * 0.01}/{longitude + lon_offset * 0.01}",

            ))

        return results
