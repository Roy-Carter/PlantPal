"""Seed the running PlantPal API with sample plants."""

import httpx

API = "http://localhost:8000"

PLANTS = [
    {
        "name": "Monstera",
        "species": "Monstera deliciosa",
        "location": "Living Room",
        "light_need": "medium",
        "water_frequency_hours": 168,
        "health_status": "healthy",
        "notes": "Loves humidity and indirect light",
    },
    {
        "name": "Snake Plant",
        "species": "Dracaena trifasciata",
        "location": "Bedroom",
        "light_need": "low",
        "water_frequency_hours": 336,
        "health_status": "healthy",
        "notes": "Very low maintenance",
    },
    {
        "name": "Pothos",
        "species": "Epipremnum aureum",
        "location": "Kitchen",
        "light_need": "low",
        "water_frequency_hours": 240,
        "health_status": "healthy",
        "notes": "Great trailing plant",
    },
    {
        "name": "Fiddle Leaf Fig",
        "species": "Ficus lyrata",
        "location": "Living Room",
        "light_need": "high",
        "water_frequency_hours": 168,
        "health_status": "needs_attention",
        "notes": "Sensitive to drafts and overwatering",
    },
    {
        "name": "Aloe Vera",
        "species": "Aloe barbadensis",
        "location": "Balcony",
        "light_need": "high",
        "water_frequency_hours": 504,
        "health_status": "healthy",
        "notes": "Medicinal gel inside leaves",
    },
    {
        "name": "Peace Lily",
        "species": "Spathiphyllum wallisii",
        "location": "Bathroom",
        "light_need": "low",
        "water_frequency_hours": 120,
        "health_status": "critical",
        "notes": "Drooping leaves — needs water urgently",
    },
]


def main() -> None:
    existing = httpx.get(f"{API}/plants/").json()
    if existing:
        print(f"Database already has {len(existing)} plants — skipping seed.")
        return

    for plant in PLANTS:
        resp = httpx.post(f"{API}/plants/", json=plant)
        resp.raise_for_status()
        print(f"  + {plant['name']}")

    print(f"\nSeeded {len(PLANTS)} sample plants.")


if __name__ == "__main__":
    main()
