# PlantPal — Indoor Plant Care Tracker

A monorepo for the EASS course (EX1 + EX2). PlantPal helps you manage your houseplant collection, track watering schedules, and monitor plant health — all from a single dashboard.

## Project Structure

```
EASS-HIT/
├── backend/          # EX1 – FastAPI backend
│   ├── app/          # Application code (models, routes, services, DB)
│   ├── tests/        # pytest test suite (15 tests)
│   ├── seed.py       # Sample data loader
│   └── README.md     # Backend-specific docs
├── frontend/          # EX2 – Streamlit dashboard
│   ├── plantpal_ui.py # Main entry point
│   ├── plant_api.py   # HTTP client for the backend
│   ├── cached_api.py  # Cached data layer
│   ├── pages/         # Additional views (Care Log)
│   └── tests/         # Frontend workflow tests
├── .env.example      # Environment variable template
└── .gitignore
```

## Quick Start

### 1. Backend (EX1)

```bash
cd backend
uv sync
mkdir -p data
uv run uvicorn app.main:app --reload
```

API at http://localhost:8000 — Docs at http://localhost:8000/docs

Optionally seed sample data (with the API running):

```bash
uv run python seed.py
```

Run tests:

```bash
uv run pytest -v
```

### 2. Frontend (EX2)

In a second terminal:

```bash
cd frontend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run plantpal_ui.py
```

> **Linux note:** Modern Debian/Ubuntu systems block `pip install` outside a virtual environment (PEP 668). The `python3 -m venv` step above creates a local `.venv` to work around this. On macOS/Windows you may be able to skip the venv, but using one is recommended regardless.

Dashboard at http://localhost:8501

Set `API_URL` if the backend runs on a different host:

```bash
API_URL=http://some-host:8000 streamlit run plantpal_ui.py
```

## Features

### Backend (EX1)

- Full CRUD for plants (`POST`, `GET`, `PUT`, `PATCH`, `DELETE`)
- SQLite persistence via SQLModel
- Health check endpoint (`/health`)
- CORS middleware for frontend integration
- 15 pytest tests (happy-path + error-path + validation)
- Seed script with 6 sample plants

### Frontend (EX2)

- **Dashboard**: List all plants with health badges, light indicators, and watering status
- **Add / Edit / Delete**: Full CRUD through dialog forms
- **Water Now**: One-click watering that updates `last_watered` to today
- **Overdue Alerts**: Plants past their watering schedule are flagged with warnings
- **Care Log**: Dedicated page showing watering schedule table and overdue breakdown
- **Search & Filter**: Filter by name, location, health status, or light need
- **Export to JSON**: Download your plant collection as a JSON file
- Green/nature-themed dark UI

## AI Assistance

This project was built with the assistance of an AI coding agent (Claude / Cursor). The AI was used to:

- Generate the initial project scaffolding and boilerplate
- Implement CRUD service logic and route handlers
- Write pytest test cases
- Build the Streamlit dashboard layout and styling
- Draft documentation

All outputs were reviewed and tested locally. Backend tests (15 passing) and frontend workflow tests (3 passing) verify correctness.
