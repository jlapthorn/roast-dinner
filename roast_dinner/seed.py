"""Seed default roast-dinner foods for a fan-assisted oven."""

from roast_dinner import db
from roast_dinner.models import Food

# Times are typical fan-oven guidance — editable in the app.
DEFAULT_FOODS = [
    {
        "name": "Chicken",
        "category": "meat",
        "meat_type": "chicken",
        "temperature_c": 180,
        "minutes_per_kg": 40,  # ~20 min per 500g
        "base_minutes": 20,
        "fixed_minutes": None,
        "rest_minutes": 15,
        "notes": "Fan oven. Cover breast loosely with foil if browning too fast.",
    },
    {
        "name": "Beef (medium)",
        "category": "meat",
        "meat_type": "beef",
        "temperature_c": 180,
        "minutes_per_kg": 50,
        "base_minutes": 20,
        "fixed_minutes": None,
        "rest_minutes": 20,
        "notes": "For rare use ~40 min/kg; well done ~60 min/kg. Rest under foil.",
    },
    {
        "name": "Pork",
        "category": "meat",
        "meat_type": "pork",
        "temperature_c": 180,
        "minutes_per_kg": 60,
        "base_minutes": 30,
        "fixed_minutes": None,
        "rest_minutes": 15,
        "notes": "Crackling: start hot or finish uncovered. Juices should run clear.",
    },
    {
        "name": "Lamb",
        "category": "meat",
        "meat_type": "lamb",
        "temperature_c": 180,
        "minutes_per_kg": 50,
        "base_minutes": 25,
        "fixed_minutes": None,
        "rest_minutes": 20,
        "notes": "Medium. Shorter for pink; longer for well done.",
    },
    {
        "name": "Carrots",
        "category": "vegetable",
        "meat_type": None,
        "temperature_c": 180,
        "minutes_per_kg": None,
        "base_minutes": 0,
        "fixed_minutes": 35,
        "rest_minutes": 0,
        "notes": "Roast with a little oil until tender and edged with colour.",
    },
    {
        "name": "Peas",
        "category": "vegetable",
        "meat_type": None,
        "temperature_c": 100,
        "minutes_per_kg": None,
        "base_minutes": 0,
        "fixed_minutes": 4,
        "rest_minutes": 0,
        "notes": "Boil or steam just before serving.",
    },
    {
        "name": "Tenderstem broccoli",
        "category": "vegetable",
        "meat_type": None,
        "temperature_c": 100,
        "minutes_per_kg": None,
        "base_minutes": 0,
        "fixed_minutes": 8,
        "rest_minutes": 0,
        "notes": "Steam or boil until just tender.",
    },
    {
        "name": "Broccoli",
        "category": "vegetable",
        "meat_type": None,
        "temperature_c": 100,
        "minutes_per_kg": None,
        "base_minutes": 0,
        "fixed_minutes": 10,
        "rest_minutes": 0,
        "notes": "Steam or boil florets until bright and tender.",
    },
    {
        "name": "Yorkshire puddings",
        "category": "other",
        "meat_type": None,
        "temperature_c": 220,
        "minutes_per_kg": None,
        "base_minutes": 0,
        "fixed_minutes": 22,
        "rest_minutes": 0,
        "notes": "Hot tin and hot fat. Do not open the oven while they rise.",
    },
]


def seed_foods() -> None:
    if Food.query.count() > 0:
        return
    for item in DEFAULT_FOODS:
        db.session.add(Food(**item))
    db.session.commit()
