# GeoBook AI — Conversational Location Search & Booking (React + FastAPI + PostgreSQL)

A production-oriented monorepo for an AI chatbot that understands natural-language, location-based requests — "find a dentist near me" or "book a haircut tomorrow at 4pm" — and turns them into real nearby-place results and confirmed appointments.

## What it does

- **Conversational chatbot UI** (React) with a ChatGPT-like chat experience, session history, and follow-up handling (e.g., "book the first one").
- **Hybrid NLU**: Gemini-based intent/entity extraction (via `google-generativeai`) for parsing intent, category, location, date/time, and search terms, with rule-based keyword matching as a fallback when no API key is configured.
- **Semantic + geospatial business search (RAG-style retrieval)**: user queries are embedded with Gemini's `text-embedding-004` model and matched against business embeddings stored in PostgreSQL via `pgvector`, using cosine-distance similarity search combined with haversine-distance geo-filtering and fuzzy text matching (`rapidfuzz`).
- **Multi-source place search**: merges registered businesses (Postgres) with live results from the Google Maps Places API and OpenStreetMap (Overpass API for nearby search, Nominatim/Photon for geocoding fallback), so results are accurate even when no business is registered locally.
- **Business registration** and **automated appointment booking** with configurable availability rules, slot durations, and conflict checking.
- **Email notifications** to businesses on new bookings (SMTP-based).
- **JWT authentication**, password hashing (bcrypt), request validation (Pydantic), structured logging (`structlog`), and IP-based rate limiting (`slowapi`).

## Tech stack

**Frontend:** React 19, TypeScript, Vite, Tailwind CSS, React Router, Axios, Framer Motion

**Backend:** FastAPI, SQLAlchemy 2.0 (async), Alembic migrations, PostgreSQL + `pgvector`, `asyncpg`

**AI / NLU:** Google Gemini (`google-generativeai`) for intent parsing and text embeddings, `pgvector` cosine similarity for retrieval, `rapidfuzz` for fuzzy matching, `dateparser` for natural-language date/time parsing

**Geo / Maps:** Google Maps Places API, OpenStreetMap (Overpass API, Nominatim, Photon)

**Infra:** Docker Compose (local Postgres), Alembic for schema migrations, deployable to Render/Vercel

## Folder structure

```
frontend/                React app (Vite + Tailwind)
  src/ui/                 Chat, auth, and layout components
  src/lib/                API client, geolocation, shared types
backend/                  FastAPI app
  app/api/routes/          auth, businesses, appointments, chat endpoints
  app/chatbot/             NLU (Gemini + rule-based) and conversation engine
  app/services/            embeddings, business search, geo, Google Maps, OSM
  app/db/                  SQLAlchemy models and session handling
  alembic/                 DB migrations (incl. pgvector embedding column)
infra/                    Docker compose (Postgres)
```

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker Desktop (recommended for Postgres with `pgvector`)
- API keys: Google Maps API key, Gemini API key (optional but recommended — enables AI-based NLU and semantic search; falls back to rule-based parsing without it)

## Quick start (recommended)

1. Start Postgres:

```bash
cd infra
docker compose up -d
```

2. Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

3. Frontend:

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Open:

- Frontend: `http://localhost:5173`
- Backend docs (Swagger): `http://localhost:8000/docs`

## Environment variables

Backend: see `backend/.env.example` — includes `DATABASE_URL`, `JWT_SECRET_KEY`, `GOOGLE_MAPS_API_KEY`, `GEMINI_API_KEY`, OSM/Nominatim settings, and SMTP settings for booking emails.

Frontend: see `frontend/.env.example`

## OpenStreetMap setup notes

- Nominatim requires a valid **User-Agent** that identifies your application (set `OSM_USER_AGENT` in `backend/.env`).
- Photon is used as an additional geocoding fallback before Nominatim.
- For production reliability/quotas, consider a managed provider or self-hosting Nominatim/Overpass.

## Production notes

- Use a proper reverse proxy (Caddy/Nginx) and HTTPS.
- Store secrets in a secret manager, not `.env`.
- Enable stronger rate limiting (Redis-backed) if needed.
- Ensure the `pgvector` extension is enabled on your production Postgres instance.
