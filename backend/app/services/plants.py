from datetime import datetime, timezone

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import Plant, PlantCreate, PlantUpdate
from app.services.care_events import log_event

FIELD_LABELS = {
    "name": "name",
    "species": "species",
    "location": "location",
    "light_need": "light need",
    "water_frequency_hours": "water frequency",
    "health_status": "health status",
    "notes": "notes",
}

_SEVERITY = {"healthy": 0, "needs_attention": 1, "critical": 2}


def _hours_since_watered(plant: Plant) -> float | None:
    """Parse ``last_watered`` ISO string and return hours elapsed, or None
    if the field is empty / unparseable.  Naive datetimes are assumed UTC."""
    if not plant.last_watered:
        return None
    try:
        watered = datetime.fromisoformat(plant.last_watered)
        if watered.tzinfo is None:
            watered = watered.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - watered).total_seconds() / 3600
    except ValueError:
        return None


def _refresh_health(session: Session, plant: Plant) -> Plant:
    """Degrade health when overdue; never auto-heal (only watering heals).

    Thresholds (relative to ``water_frequency_hours``):
      * overdue by 0–50% of frequency  ->  ``needs_attention``
      * overdue by >50% of frequency   ->  ``critical``

    Health only worsens — if the plant is already at the computed severity
    or worse, no change is made.  A ``health_changed`` care event is logged
    whenever the status actually transitions.
    """
    hours = _hours_since_watered(plant)
    if hours is None:
        return plant

    freq = plant.water_frequency_hours
    overdue = hours - freq

    if overdue <= 0:
        return plant

    new_status = "critical" if overdue > freq * 0.5 else "needs_attention"

    if _SEVERITY.get(new_status, 0) <= _SEVERITY.get(plant.health_status, 0):
        return plant

    old_status = plant.health_status
    plant.health_status = new_status
    session.add(plant)
    log_event(
        session,
        plant_id=plant.id,
        event_type="health_changed",
        detail=f"{old_status} -> {new_status}",
    )
    session.commit()
    session.refresh(plant)
    return plant


def _log_field_changes(session: Session, plant: Plant, old: dict, new: dict) -> None:
    """Compare old and new field values; log each changed field as an 'edited' event."""
    for field, label in FIELD_LABELS.items():
        old_val = old.get(field)
        new_val = new.get(field)
        if old_val != new_val:
            log_event(
                session,
                plant_id=plant.id,
                event_type="edited",
                detail=f"{label}: {old_val} -> {new_val}",
            )


def create_plant(session: Session, payload: PlantCreate) -> Plant:
    """Persist a new plant.  Fills in sensible defaults when the caller
    omits ``last_watered`` (set to *now*) or ``image_url`` (generated
    as a DiceBear identicon derived from the plant name)."""
    if not payload.last_watered:
        payload.last_watered = datetime.now(timezone.utc).isoformat()

    if not payload.image_url:
        safe = payload.name.replace(" ", "+")
        payload.image_url = (
            f"https://api.dicebear.com/7.x/identicon/svg?seed={safe}"
        )

    db_plant = Plant.model_validate(payload)
    session.add(db_plant)
    session.commit()
    session.refresh(db_plant)
    return db_plant


def list_plants(session: Session, *, skip: int = 0, limit: int = 100) -> list[Plant]:
    plants = list(session.exec(select(Plant).offset(skip).limit(limit)).all())
    return [_refresh_health(session, p) for p in plants]


def get_plant(session: Session, plant_id: int) -> Plant:
    plant = session.get(Plant, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return _refresh_health(session, plant)


def update_plant(session: Session, plant_id: int, payload: PlantCreate) -> Plant:
    db_plant = session.get(Plant, plant_id)
    if not db_plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    old_values = {f: getattr(db_plant, f) for f in FIELD_LABELS}
    new_values = payload.model_dump()

    for key, value in new_values.items():
        setattr(db_plant, key, value)

    session.add(db_plant)
    _log_field_changes(session, db_plant, old_values, new_values)
    session.commit()
    session.refresh(db_plant)
    return db_plant


def patch_plant(session: Session, plant_id: int, payload: PlantUpdate) -> Plant:
    """Apply a partial update.  Special watering behaviour: when
    ``last_watered`` is included in the patch and the plant is currently
    unhealthy, health is automatically reset to ``"healthy"`` unless the
    caller explicitly provides a different ``health_status``.  A
    ``"watered"`` care event is logged, and any changed fields produce
    ``"edited"`` events."""
    db_plant = session.get(Plant, plant_id)
    if not db_plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    updates = payload.model_dump(exclude_unset=True)
    watering = "last_watered" in updates

    if watering and db_plant.health_status in ("needs_attention", "critical"):
        if "health_status" not in updates:
            updates["health_status"] = "healthy"

    old_values = {f: getattr(db_plant, f) for f in FIELD_LABELS if f in updates}

    for key, value in updates.items():
        setattr(db_plant, key, value)

    session.add(db_plant)

    if watering:
        log_event(session, plant_id=db_plant.id, event_type="watered")

    new_values = {f: updates[f] for f in FIELD_LABELS if f in updates}
    _log_field_changes(session, db_plant, old_values, new_values)

    session.commit()
    session.refresh(db_plant)
    return db_plant


def delete_plant(session: Session, plant_id: int) -> None:
    db_plant = session.get(Plant, plant_id)
    if not db_plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    session.delete(db_plant)
    session.commit()
