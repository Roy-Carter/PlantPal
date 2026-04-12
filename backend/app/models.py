"""SQLModel schemas for plants and care events.

The Plant family uses a Base/Table/Create/Read/Update split so that
the DB table definition, incoming payloads, and API responses each
carry only the fields they need while sharing common validation.
"""

from sqlmodel import SQLModel, Field


class PlantBase(SQLModel):
    """Shared fields inherited by the DB table, create, and read schemas."""

    name: str = Field(index=True)
    species: str
    location: str = "Unknown"
    light_need: str = "medium"
    water_frequency_hours: int = 168
    last_watered: str | None = None
    health_status: str = "healthy"
    image_url: str = ""
    notes: str = ""


class Plant(PlantBase, table=True):
    """SQLite table row — adds the auto-generated primary key."""

    id: int | None = Field(default=None, primary_key=True)


class PlantCreate(PlantBase):
    """Incoming POST payload — same fields as base, no id required."""

    pass


class PlantRead(PlantBase):
    """Outgoing response — guarantees ``id`` is always present."""

    id: int


class PlantUpdate(SQLModel):
    """PATCH payload — every field is optional so callers send only
    what changed.  Unset fields are excluded via ``exclude_unset``."""

    name: str | None = None
    species: str | None = None
    location: str | None = None
    light_need: str | None = None
    water_frequency_hours: int | None = None
    last_watered: str | None = None
    health_status: str | None = None
    image_url: str | None = None
    notes: str | None = None


# ---------------------------------------------------------------------------
# Care Events
# ---------------------------------------------------------------------------

class CareEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    plant_id: int = Field(foreign_key="plant.id", index=True)
    event_type: str  # "watered", "health_changed", "note"
    detail: str = ""
    created_at: str = ""


class CareEventCreate(SQLModel):
    plant_id: int
    event_type: str = "note"
    detail: str = ""
    created_at: str | None = None


class CareEventRead(SQLModel):
    id: int
    plant_id: int
    event_type: str
    detail: str
    created_at: str
    plant_name: str | None = None
