# PlantPal

Indoor plant care tracker built for the EASS course (EX1 + EX2).

Manage your houseplant collection, track watering schedules, and monitor plant health from a single dashboard. Every action is logged so you can look back at your full care history.

## Project Structure

```
EASS-HIT/
├── backend/                        # FastAPI backend (EX1)
│   ├── app/
│   │   ├── main.py                 # FastAPI app, lifespan, CORS, health
│   │   ├── models.py               # Plant + CareEvent data models
│   │   ├── db.py                   # SQLite / SQLModel setup
│   │   ├── routers/
│   │   │   ├── plants.py           # /plants CRUD endpoints
│   │   │   └── care_events.py      # /care-events endpoints
│   │   └── services/
│   │       ├── plants.py           # Business logic + auto-logging
│   │       └── care_events.py      # Care event queries + creation
│   ├── tests/                      # 34 pytest tests
│   │   ├── conftest.py             # In-memory SQLite fixtures
│   │   ├── test_plants.py          # Plant CRUD + auto-logging
│   │   ├── test_care_events.py     # Care events API
│   │   └── test_smoke.py           # Health / docs smoke tests
│   ├── seed.py                     # Sample data loader (8 plants + 30 events)
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                       # Streamlit dashboard (EX2)
│   ├── plantpal_ui.py              # Main entry point (Dashboard + Add/Edit/Delete)
│   ├── plant_api.py                # HTTP client for the backend
│   ├── cached_api.py               # Cached data layer with TTL
│   ├── care_log.py                 # Care Log page (timeline, drilldown, notes)
│   ├── theme.css                   # Custom green & white theme
│   ├── tests/
│   │   └── test_frontend.py        # 8 frontend tests (mocked, no backend needed)
│   └── requirements.txt
├── .env.example
└── .gitignore
```

## Quick Start

### 1. Backend

```bash
cd backend
uv sync
mkdir -p data
uv run uvicorn app.main:app --reload
```

API: http://localhost:8000 | Docs: http://localhost:8000/docs

Seed sample data (with the API running):

```bash
uv run python seed.py
```

Run backend tests:

```bash
uv run pytest -v                            # all 34 tests
uv run pytest tests/test_plants.py -v       # plant CRUD + auto-logging
uv run pytest tests/test_care_events.py -v  # care events API
uv run pytest tests/test_smoke.py -v        # health / docs smoke
```

### 2. Frontend

In a second terminal:

```bash
cd frontend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run plantpal_ui.py
```

> **Linux note:** Modern Debian/Ubuntu block `pip install` outside a venv (PEP 668). The steps above create a local `.venv` to work around this.

Dashboard: http://localhost:8501

Point to a different backend:

```bash
API_URL=http://some-host:8000 streamlit run plantpal_ui.py
```

Run frontend tests (no backend needed, uses mocks):

```bash
cd frontend
python3 -m pytest tests/ -v  # all 8 tests
```

## Features

### Backend (EX1)

- Full CRUD for plants (`POST`, `GET`, `PUT`, `PATCH`, `DELETE`)
- Care Events API (`GET /care-events/`, `POST /care-events/`) with plant and type filters
- Auto-logging: every watering, health change, and field edit is recorded as a timestamped care event
- Automatic health degradation when plants are overdue for watering
- SQLite persistence via SQLModel
- Health check endpoint (`/health`)
- CORS middleware for frontend integration
- 34 pytest tests using in-memory SQLite (no setup required)
- Seed script with 8 plants and 30 care events covering all field combinations

### Frontend (EX2)

- **Dashboard** — view all plants with health badges, light indicators, and watering status
- **Add / Edit / Delete** — full CRUD through dialog forms
- **Water Now** — one-click watering with automatic event logging
- **Overdue Alerts** — plants past their schedule are flagged
- **Care Log** — full history and insights page:
  - Summary stats: weekly/monthly activity, care streak, most pampered plant
  - Activity timeline grouped by day, filterable by plant and event type
  - Per-plant drilldown with watering count, consistency rating, and full history
  - Add free-text care notes to any plant
  - All edits (name, location, frequency, etc.) appear in the timeline
- **Search and Filter** — filter by name, location, health, or light need
- **Export to JSON** — download your plant collection as a JSON file (EX2 small extra)
- 8 frontend tests using mocks (no backend needed)

## AI Assistance

This project was built with the help of an AI coding agent (Claude / Cursor) for:

- Project scaffolding and boilerplate
- CRUD service logic and route handlers
- Test cases
- Dashboard layout and styling
- Documentation

All code was reviewed and tested locally. Backend: 34 tests passing. Frontend: 8 tests passing.
