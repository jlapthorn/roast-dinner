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
    temperature_c: int | None
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
            data[f"{key}_display"] = data[key]
        return data


@dataclass
class PlanEvent:
    """A single timed action on the cooking timeline."""

    at: datetime
    action: str  # start | take_out | serve
    title: str
    detail: str
    category: str | None = None
    temperature_c: int | None = None
    cook_minutes: float | None = None
    weight_kg: float | None = None
    rest_minutes: float | None = None
    notes: str = ""


_ACTION_ORDER = {"start": 0, "take_out": 1, "serve": 2}


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
        temp = int(food.temperature_c) if food.temperature_c is not None else None

        steps.append(
            PlanStep(
                food_id=food.id,
                name=food.name,
                category=food.category,
                temperature_c=temp,
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


def build_timeline(serve_at: datetime, steps: list[PlanStep]) -> list[PlanEvent]:
    """Expand plan steps into start / take-out / serve events in time order."""
    events: list[PlanEvent] = []

    for step in steps:
        start_detail_parts = [f"Cook for {format_minutes(step.cook_minutes)}"]
        if step.weight_kg is not None:
            start_detail_parts.append(f"{step.weight_kg:.1f} kg")
        if step.rest_minutes:
            start_detail_parts.append(
                f"then rest {format_minutes(step.rest_minutes)} after taking out"
            )
        elif step.temperature_c is not None:
            start_detail_parts.append("until serve")

        events.append(
            PlanEvent(
                at=step.start_at,
                action="start",
                title=f"Start {step.name}",
                detail=" · ".join(start_detail_parts),
                category=step.category,
                temperature_c=step.temperature_c,
                cook_minutes=step.cook_minutes,
                weight_kg=step.weight_kg,
                rest_minutes=step.rest_minutes or None,
                notes=step.notes,
            )
        )

        # Meats (and anything with rest) leave the oven before dinner.
        if step.rest_minutes and step.oven_out_at < serve_at:
            events.append(
                PlanEvent(
                    at=step.oven_out_at,
                    action="take_out",
                    title=f"Take {step.name} out of the oven",
                    detail=(
                        f"Rest for {format_minutes(step.rest_minutes)} "
                        f"until dinner at {serve_at.strftime('%H:%M')}"
                    ),
                    category=step.category,
                    temperature_c=step.temperature_c,
                    rest_minutes=step.rest_minutes,
                )
            )

    events.append(
        PlanEvent(
            at=serve_at,
            action="serve",
            title="Dinner is ready",
            detail="Everything should be plated and on the table.",
        )
    )

    events.sort(
        key=lambda event: (
            event.at,
            _ACTION_ORDER.get(event.action, 9),
            event.title.lower(),
        )
    )
    return events


def format_minutes(value: float) -> str:
    total = int(round(value))
    hours, minutes = divmod(total, 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"
