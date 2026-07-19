from __future__ import annotations

from dataclasses import dataclass

from typing import Any, Literal

import httpx

from app.core.config import settings

OSMPlaceType = Literal["restaurant", "school", "hospital", "police", "bus_stop", "salon", "dental", "clinic"]

@dataclass(frozen=True)

class OSMPlace:

    osm_type: str  

    osm_id: int

    name: str

    address: str | None

    latitude: float

    longitude: float

    phone: str | None = None

    maps_url: str | None = None

@dataclass(frozen=True)

class GeocodeContext:

    latitude: float

    longitude: float

    

    overpass_area_id: int | None = None

class OSMClient:

    def __init__(

        self,

        *,

        user_agent: str | None = None,

        nominatim_base_url: str | None = None,

        overpass_url: str | None = None,

    ) -> None:

        self.user_agent = user_agent or settings.osm_user_agent

        self.nominatim_base_url = nominatim_base_url or settings.osm_nominatim_base_url

        raw_overpass = overpass_url or settings.osm_overpass_url

        self.overpass_urls = [u.strip() for u in raw_overpass.split(",") if u.strip()]

    def _headers(self) -> dict[str, str]:

        return {"User-Agent": self.user_agent, "Accept": "application/json"}

    async def geocode(self, query: str) -> tuple[float, float] | None:

        """
        Address/city geocoding via Nominatim.
        Docs: https://nominatim.org/release-docs/latest/api/Search/
        """

        

        url = f"{self.nominatim_base_url.rstrip('/')}/search"

        async with httpx.AsyncClient(timeout=15, headers=self._headers()) as client:

            params = {"q": query, "format": "json", "limit": 1}

            if settings.osm_nominatim_email:

                params["email"] = settings.osm_nominatim_email

            try:

                resp = await client.get(url, params=params)

                if resp.status_code == 200:

                    data = resp.json()

                    if data:

                        return float(data[0]["lat"]), float(data[0]["lon"])

            except httpx.HTTPError:

                pass

        

        

        photon_url = f"{settings.osm_photon_base_url.rstrip('/')}/api"

        async with httpx.AsyncClient(timeout=15, headers=self._headers()) as client:

            try:

                resp = await client.get(photon_url, params={"q": query, "limit": 1})

                if resp.status_code != 200:

                    return None

                data = resp.json()

            except httpx.HTTPError:

                return None

        features = (data or {}).get("features") or []

        if not features:

            return None

        coords = (features[0].get("geometry") or {}).get("coordinates") or []

        if len(coords) != 2:

            return None

        lon, lat = coords

        return float(lat), float(lon)

    async def geocode_context(self, query: str) -> GeocodeContext | None:

        """
        Returns center point + (when possible) an Overpass area id to improve town precision.
        Photon includes osm_type/osm_id in feature properties for many administrative boundaries.
        """

        

        photon_url = f"{settings.osm_photon_base_url.rstrip('/')}/api"

        async with httpx.AsyncClient(timeout=15, headers=self._headers()) as client:

            try:

                resp = await client.get(photon_url, params={"q": query, "limit": 1})

                if resp.status_code != 200:

                    return None

                data = resp.json()

            except httpx.HTTPError:

                return None

        features = (data or {}).get("features") or []

        if not features:

            return None

        f0 = features[0]

        coords = (f0.get("geometry") or {}).get("coordinates") or []

        if len(coords) != 2:

            return None

        lon, lat = coords

        props = f0.get("properties") or {}

        osm_type = props.get("osm_type")

        osm_id = props.get("osm_id")

        area_id: int | None = None

        try:

            if osm_type == "R" and osm_id is not None:

                area_id = 3600000000 + int(osm_id)

            elif osm_type == "W" and osm_id is not None:

                area_id = 2400000000 + int(osm_id)

        except (TypeError, ValueError):

            area_id = None

        return GeocodeContext(latitude=float(lat), longitude=float(lon), overpass_area_id=area_id)

    def _overpass_filter(self, place_type: OSMPlaceType) -> str:

        if place_type == "restaurant":

            return 'nwr["amenity"="restaurant"]'

        if place_type == "school":

            return 'nwr["amenity"="school"]'

        if place_type == "hospital":

            

            return 'nwr["amenity"="hospital"];nwr["amenity"="clinic"];nwr["healthcare"="hospital"];nwr["healthcare"="clinic"];'

        if place_type == "police":

            return 'nwr["amenity"="police"]'

        if place_type == "bus_stop":

            

            return 'nwr["highway"="bus_stop"];nwr["amenity"="bus_station"];nwr["public_transport"="platform"]["bus"="yes"];'

        if place_type == "salon":

            return 'nwr["shop"="hairdresser"];nwr["shop"="beauty"];'

        if place_type == "dental":

            return 'nwr["healthcare"="dentist"];nwr["amenity"="dentist"];'

        if place_type == "clinic":

            return 'nwr["amenity"="clinic"];nwr["healthcare"="clinic"];nwr["healthcare"="doctor"];'

        raise ValueError("Unsupported type")

    async def nearby_search(

        self,

        *,

        latitude: float,

        longitude: float,

        place_type: OSMPlaceType,

        radius_meters: int = 5000,

        limit: int = 10,

        overpass_area_id: int | None = None,

    ) -> list[OSMPlace]:

        """
        Nearby search via Overpass API around a coordinate.
        Docs: https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL
        """

        filt = self._overpass_filter(place_type)

        around = f"(around:{radius_meters},{latitude},{longitude})"

        

        

        

        

        

        

        inner_lines = []

        for line in [s.strip() for s in filt.split(";") if s.strip()]:

            if overpass_area_id:

                inner_lines.append(f"  {line}(area:{overpass_area_id});")

            else:

                inner_lines.append(f"  {line}{around};")

        inner = "\n".join(inner_lines)

        body = f"""
        [out:json][timeout:90];
        (
{inner}
        );
        out tags center qt;
        """

        async with httpx.AsyncClient(timeout=10, headers=self._headers()) as client:

            data = None

            for url in self.overpass_urls:

                try:

                    resp = await client.post(url, data={"data": body})

                except httpx.HTTPError:

                    continue

                if resp.status_code == 200:

                    try:

                        data = resp.json()

                    except ValueError:

                        data = None

                    if data is not None:

                        break

            if data is None:

                return []

        elements = data.get("elements", [])

        places: list[OSMPlace] = []

        for el in elements:

            tags = el.get("tags") or {}

            name = (tags.get("name") or tags.get("brand") or "").strip()

            

            if not name:

                continue

            lat = el.get("lat") or (el.get("center") or {}).get("lat")

            lon = el.get("lon") or (el.get("center") or {}).get("lon")

            if lat is None or lon is None:

                continue

            phone = tags.get("phone") or tags.get("contact:phone")

            address = _format_osm_address(tags)

            osm_type = el.get("type", "node")

            osm_id = int(el.get("id"))

            maps_url = f"https://www.openstreetmap.org/{osm_type}/{osm_id}"

            places.append(

                OSMPlace(

                    osm_type=osm_type,

                    osm_id=osm_id,

                    name=name,

                    address=address,

                    latitude=float(lat),

                    longitude=float(lon),

                    phone=phone,

                    maps_url=maps_url,

                )

            )

        

        

        return places[:limit]

def _format_osm_address(tags: dict[str, Any]) -> str | None:

    parts = []

    for k in ["addr:housenumber", "addr:street", "addr:suburb", "addr:city", "addr:state", "addr:postcode"]:

        v = tags.get(k)

        if v:

            parts.append(str(v))

    if parts:

        return ", ".join(parts)

    return None

