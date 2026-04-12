from sqlmodel import SQLModel, Field


class PlantBase(SQLModel):
    name: str = Field(index=True)
    species: str
    location: str = "Unknown"
    light_need: str = "medium"
    water_frequency_days: int = 7
    last_watered: str | None = None
    health_status: str = "healthy"
    image_url: str = ""
    notes: str = ""


class Plant(PlantBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class PlantCreate(PlantBase):
    pass


class PlantRead(PlantBase):
    id: int


class PlantUpdate(SQLModel):
    name: str | None = None
    species: str | None = None
    location: str | None = None
    light_need: str | None = None
    water_frequency_days: int | None = None
    last_watered: str | None = None
    health_status: str | None = None
    image_url: str | None = None
    notes: str | None = None
