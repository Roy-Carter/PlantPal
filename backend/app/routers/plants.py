from fastapi import APIRouter

from app.db import SessionDep
from app.models import PlantCreate, PlantRead, PlantUpdate
from app.services import plants as service

router = APIRouter(prefix="/plants", tags=["plants"])


@router.post("/", response_model=PlantRead)
def create_plant(payload: PlantCreate, session: SessionDep) -> PlantRead:
    return service.create_plant(session, payload)


@router.get("/", response_model=list[PlantRead])
def list_plants(session: SessionDep, skip: int = 0, limit: int = 100) -> list[PlantRead]:
    return service.list_plants(session, skip=skip, limit=limit)


@router.get("/{plant_id}", response_model=PlantRead)
def get_plant(plant_id: int, session: SessionDep) -> PlantRead:
    return service.get_plant(session, plant_id)


@router.put("/{plant_id}", response_model=PlantRead)
def update_plant(plant_id: int, payload: PlantCreate, session: SessionDep) -> PlantRead:
    return service.update_plant(session, plant_id, payload)


@router.patch("/{plant_id}", response_model=PlantRead)
def patch_plant(plant_id: int, payload: PlantUpdate, session: SessionDep) -> PlantRead:
    return service.patch_plant(session, plant_id, payload)


@router.delete("/{plant_id}")
def delete_plant(plant_id: int, session: SessionDep) -> dict:
    service.delete_plant(session, plant_id)
    return {"detail": "Plant deleted successfully"}
