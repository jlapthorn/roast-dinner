"""Build a reverse cooking schedule from a target serve time."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta

from roast_dinner.models import Food


@dataclass
class PlanStep:
    food_id: int
    name: str
    category: str
    temperature_c: int
    weight_kg: float | None
    cook_minutes: float
    rest_minutes: float
    start_at: datetime
    oven_out_at: datetime
    ready_at: datetime
    notes: str

    def to_dict(self) -> dict:
        data = asdict(self)
        for key in ("start_at", "oven_out_at", "ready_at"):
            data[key] = data[key].isoformat(timespec="minutes")
            data[f"{key}_display"] = data[key]  # kept for templates via formatter
        return data


def build_plan(
    serve_at: datetime,
    selections: list[dict],
) -> list[PlanStep]:
    """
    selections: [{food: Food, weight_kg: float | None}, ...]
    Everything finishes at serve_at (after any resting).
    """
    steps: list[PlanStep] = []

    for selection in selections:
        food: Food = selection["food"]
        weight = selection.get("weight_kg")
        cook = food.cook_minutes(weight)
        rest = float(food.rest_minutes or 0)
        ready_at = serve_at
        oven_out_at = ready_at - timedelta(minutes=rest)
        start_at = oven_out_at - timedelta(minutes=cook)

        steps.append(
            PlanStep(
                food_id=food.id,
                name=food.name,
                category=food.category,
                temperature_c=int(food.temperature_c),
                weight_kg=float(weight) if weight is not None else None,
                cook_minutes=cook,
                rest_minutes=rest,
                start_at=start_at,
                oven_out_at=oven_out_at,
                ready_at=ready_at,
                notes=food.notes or "",
            )
        )

    steps.sort(key=lambda step: (step.start_at, step.name.lower()))
    return steps


def format_minutes(value: float) -> str:
    total = int(round(value))
    hours, minutes = divmod(total, 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"
