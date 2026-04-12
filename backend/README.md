# PlantPal Backend (EX1)

FastAPI backend for the PlantPal indoor plant care tracker.

## Quick Start

### 1. Create the environment

```bash
cd backend
uv sync
```

### 2. Run the API

```bash
mkdir -p data
uv run uvicorn app.main:app --reload
```

The API is available at **http://localhost:8000**.  
Interactive docs at **http://localhost:8000/docs**.

### 3. Run tests

```bash
uv run pytest -v
```

Tests use an in-memory SQLite database — no setup required.

### 4. Seed sample data (bonus)

With the API running:

```bash
uv run python seed.py
```

Seeds 8 sample plants and 30 care events covering every location, light level, and health status. Idempotent — skips if data already exists.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/plants/` | Create a plant |
| `GET` | `/plants/` | List all plants (`?skip=0&limit=100`) |
| `GET` | `/plants/{id}` | Get a single plant |
| `PUT` | `/plants/{id}` | Full update |
| `PATCH` | `/plants/{id}` | Partial update (e.g. water a plant — resets health to healthy) |
| `DELETE` | `/plants/{id}` | Delete a plant |
| `GET` | `/care-events/` | List care events (`?plant_id=&event_type=&limit=50`) |
| `POST` | `/care-events/` | Create a care event |

## Project Structure

```
backend/
├── app/
│   ├── main.py                # FastAPI app, lifespan, CORS, health
│   ├── models.py              # SQLModel schemas (Plant + CareEvent)
│   ├── db.py                  # Engine + session
│   ├── routers/
│   │   ├── plants.py          # /plants CRUD endpoints
│   │   └── care_events.py     # /care-events endpoints
│   └── services/
│       ├── plants.py          # Plant business logic + auto-logging
│       └── care_events.py     # Care event queries + creation
├── tests/
│   ├── conftest.py            # In-memory SQLite fixtures
│   ├── test_plants.py         # Plant CRUD + auto-logging (23 tests)
│   ├── test_care_events.py    # Care events API (8 tests)
│   └── test_smoke.py          # Health / docs smoke tests (3 tests)
├── seed.py                    # Sample data loader (8 plants + 30 events)
├── pyproject.toml             # Dependencies
└── Dockerfile
```
