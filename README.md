# GeoBook AI + Location Search + Booking (React + FastAPI + Postgres)

Production-oriented monorepo that provides:

- **Chatbot UI** (React) with a ChatGPT-like chat experience
- **Location detection** (browser geolocation + prompt overrides)
- **OpenStreetMap search** (Overpass nearby search + Nominatim geocoding)
- **Business registration** (stored in Postgres) and merged/ranked with OSM results
- **Automated appointment booking** with availability checks
- **JWT authentication**, validation, logging, and basic rate limiting

## Folder structure

```
frontend/                React app (Vite + Tailwind)
backend/                 FastAPI app (modular services + DB)
infra/                   Docker compose + DB init (optional)
```

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker Desktop (recommended for Postgres)
- (Optional) For best reliability at scale: managed/self-hosted Nominatim/Overpass

## Quick start (recommended)

1) Start Postgres:

```bash
cd infra
docker compose up -d
```

2) Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

3) Frontend:

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

Backend: see `backend/.env.example`  
Frontend: see `frontend/.env.example`

## OpenStreetMap setup notes

- Nominatim requires a valid **User-Agent** that identifies your application (set `OSM_USER_AGENT` in `backend/.env`).
- For production reliability/quotas, consider a managed provider or self-hosting.

## Production notes

- Use a proper reverse proxy (Caddy/Nginx) and HTTPS.
- Store secrets in a secret manager, not `.env`.
- Enable stronger rate limiting (Redis-backed) if needed.

