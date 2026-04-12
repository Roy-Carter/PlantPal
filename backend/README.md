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

Seeds 6 sample plants (Monstera, Snake Plant, Pothos, etc.). Idempotent — skips if data already exists.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/plants/` | Create a plant |
| `GET` | `/plants/` | List all plants (`?skip=0&limit=100`) |
| `GET` | `/plants/{id}` | Get a single plant |
| `PUT` | `/plants/{id}` | Full update |
| `PATCH` | `/plants/{id}` | Partial update (e.g. water a plant) |
| `DELETE` | `/plants/{id}` | Delete a plant |

## Project Structure

```
backend/
├── app/
│   ├── main.py          # FastAPI app, lifespan, CORS, health
│   ├── models.py         # SQLModel schemas
│   ├── db.py             # Engine + session
│   ├── routers/plants.py # HTTP endpoints
│   └── services/plants.py# Business logic
├── tests/                # pytest suite
├── seed.py               # Sample data loader
├── pyproject.toml        # Dependencies
└── Dockerfile
```
