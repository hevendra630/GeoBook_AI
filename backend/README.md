# Backend (FastAPI)

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## Create tables (Alembic)

Make sure Postgres is running and `DATABASE_URL` is correct in `.env`, then:

```bash
alembic upgrade head
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

## API

- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## OpenStreetMap services

This backend uses:

- **Nominatim** for geocoding (location text → lat/lng)
- **Overpass API** for nearby search (restaurants/schools/hospitals/police/bus stops)

Configure in `.env`:

- `OSM_USER_AGENT`
- `OSM_NOMINATIM_BASE_URL`
- `OSM_OVERPASS_URL`

