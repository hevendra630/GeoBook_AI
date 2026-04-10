from __future__ import annotations

from dataclasses import dataclass

from typing import Any, Literal

import httpx

from app.core.config import settings

from app.core.logging import logger

GooglePlaceType = Literal["restaurant", "school", "hospital", "police", "bus_station", "bus_stop"]

@dataclass(frozen=True)

class GoogleGeocodeContext:

    latitude: float

    longitude: float

    overpass_area_id: int | None = None

@dataclass(frozen=True)

class GooglePlace:

    place_id: str

    name: str

    address: str | None

    rating: float | None

    latitude: float

    longitude: float

    maps_url: str | None = None

    phone: str | None = None

class GoogleMapsClient:

    def __init__(self, api_key: str | None = None) -> None:

        self.api_key = api_key or settings.google_maps_api_key

    def _require_key(self) -> str:

        if not self.api_key:

            raise RuntimeError("GOOGLE_MAPS_API_KEY is not configured")

        return self.api_key

    async def geocode(self, address: str) -> tuple[float, float] | None:

        key = self._require_key()

        url = "https://maps.googleapis.com/maps/api/geocode/json"

        async with httpx.AsyncClient(timeout=15) as client:

            resp = await client.get(url, params={"address": address, "key": key})

            resp.raise_for_status()

            data = resp.json()

        

        status = data.get("status")

        if status != "OK":

            logger.warning("google_maps.geocode_failed", status=status, address=address, error_message=data.get("error_message"))

            return None

            

        loc = data["results"][0]["geometry"]["location"]

        return float(loc["lat"]), float(loc["lng"])

    async def geocode_context(self, address: str) -> GoogleGeocodeContext | None:

        coords = await self.geocode(address)

        if coords:

            return GoogleGeocodeContext(latitude=coords[0], longitude=coords[1])

        return None

    async def nearby_search(

        self,

        latitude: float,

        longitude: float,

        keyword: str,

        place_type: str | None = None,

        radius_meters: int = 5000,

        limit: int = 10,

        overpass_area_id: int | None = None,

    ) -> list[GooglePlace]:

        key = self._require_key()

        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

        params: dict[str, Any] = {

            "location": f"{latitude},{longitude}",

            "radius": radius_meters,

            "keyword": keyword,

            "key": key,

        }

        if place_type:

            params["type"] = place_type

        async with httpx.AsyncClient(timeout=20) as client:

            resp = await client.get(url, params=params)

            resp.raise_for_status()

            data = resp.json()

        status = data.get("status")

        if status not in ("OK", "ZERO_RESULTS"):

            logger.warning("google_maps.nearby_search_failed", status=status, keyword=keyword, error_message=data.get("error_message"))

            return []

        places: list[GooglePlace] = []

        for r in data.get("results", [])[:limit]:

            loc = r.get("geometry", {}).get("location") or {}

            place_id = r.get("place_id")

            if not place_id or "lat" not in loc or "lng" not in loc:

                continue

            places.append(

                GooglePlace(

                    place_id=place_id,

                    name=r.get("name") or "Unknown",

                    address=r.get("vicinity") or r.get("formatted_address"),

                    rating=float(r["rating"]) if "rating" in r else None,

                    latitude=float(loc["lat"]),

                    longitude=float(loc["lng"]),

                    maps_url=f"https://www.google.com/maps/place/?q=place_id:{place_id}",

                )

            )

        return places

    async def place_details(self, place_id: str) -> dict[str, Any] | None:

        key = self._require_key()

        url = "https://maps.googleapis.com/maps/api/place/details/json"

        async with httpx.AsyncClient(timeout=20) as client:

            resp = await client.get(

                url,

                params={

                    "place_id": place_id,

                    "fields": "formatted_phone_number,international_phone_number,url",

                    "key": key,

                },

            )

            resp.raise_for_status()

            data = resp.json()

        

        status = data.get("status")

        if status != "OK":

            logger.warning("google_maps.place_details_failed", status=status, place_id=place_id, error_message=data.get("error_message"))

            return None

            

        return data.get("result")

    async def photon_geocode(self, address: str) -> tuple[float, float] | None:

        """
        Fallback geocoder using Photon (OpenStreetMap).
        Requires a User-Agent identifying the application.
        """

        url = f"{settings.osm_photon_base_url.rstrip('/')}/api/"

        headers = {"User-Agent": settings.osm_user_agent}

        try:

            async with httpx.AsyncClient(timeout=10) as client:

                resp = await client.get(url, params={"q": address, "limit": 1}, headers=headers)

                resp.raise_for_status()

                data = resp.json()

            

            features = data.get("features", [])

            if not features:

                return None

            

            

            coords = features[0]["geometry"]["coordinates"]

            return float(coords[1]), float(coords[0])

        except Exception as e:

            logger.warning("photon_geocode.failed", error=str(e), address=address)

            return None

    async def nominatim_geocode(self, address: str) -> tuple[float, float] | None:

        """
        Tertiary fallback geocoder using Nominatim (OpenStreetMap).
        Requires a User-Agent identifying the application.
        """

        url = f"{settings.osm_nominatim_base_url.rstrip('/')}/search"

        params = {

            "q": address,

            "format": "json",

            "limit": 1,

            "accept-language": "en",

        }

        if settings.osm_nominatim_email:

            params["email"] = settings.osm_nominatim_email

        headers = {"User-Agent": settings.osm_user_agent}

        try:

            async with httpx.AsyncClient(timeout=10) as client:

                resp = await client.get(url, params=params, headers=headers)

                resp.raise_for_status()

                data = resp.json()

            

            if not data:

                return None

            

            

            return float(data[0]["lat"]), float(data[0]["lon"])

        except Exception as e:

            logger.warning("nominatim_geocode.failed", error=str(e), address=address)

            return None

