from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz

from sqlalchemy import Select, select

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Business, BusinessCategory

from app.services.geo import haversine_distance_meters

@dataclass(frozen=True)

class BusinessHit:

    business: Business

    distance_meters: float

    relevance: float

async def search_businesses(
    db: AsyncSession,
    latitude: float,
    longitude: float,
    category: BusinessCategory | None,
    query: str | None,
    limit: int = 20,
    search_vector: list[float] | None = None,
) -> list[BusinessHit]:
    stmt: Select[tuple[Business]] = select(Business)
    if category:
        stmt = stmt.where(Business.category == category)
    
    if search_vector is not None:
        stmt = stmt.order_by(Business.embedding.cosine_distance(search_vector))
        
    res = await db.execute(stmt)
    businesses = list(res.scalars().all())
    hits: list[BusinessHit] = []
    
    for b in businesses:
        dist = haversine_distance_meters(latitude, longitude, float(b.latitude), float(b.longitude))
        rel = 0.0
        if query:
            rel = max(
                fuzz.partial_ratio(query.lower(), (b.name or "").lower()),
                fuzz.partial_ratio(query.lower(), (b.description or "").lower()),
            )
        hits.append(BusinessHit(business=b, distance_meters=dist, relevance=rel))
        
    if search_vector is None:
        hits.sort(key=lambda h: (h.distance_meters, -h.relevance))
    
    return hits[:limit]

