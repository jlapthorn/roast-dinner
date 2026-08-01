from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from roast_dinner import db
from roast_dinner.models import Food
from roast_dinner.planner import build_plan, format_minutes

bp = Blueprint("main", __name__)

CATEGORIES = ("meat", "vegetable", "other")
MEAT_TYPES = ("chicken", "beef", "pork", "lamb")


@bp.app_template_filter("hm")
def datetime_hm(value: datetime | str) -> str:
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.strftime("%H:%M")


@bp.app_template_filter("mins")
def mins_filter(value: float) -> str:
    return format_minutes(float(value or 0))


@bp.route("/")
def index():
    foods = Food.query.order_by(Food.category, Food.name).all()
    grouped = {cat: [f for f in foods if f.category == cat] for cat in CATEGORIES}
    return render_template("index.html", grouped=grouped, categories=CATEGORIES)


@bp.route("/plan", methods=["POST"])
def plan():
    serve_raw = request.form.get("serve_at", "").strip()
    if not serve_raw:
        flash("Choose when you want to eat.", "error")
        return redirect(url_for("main.index"))

    try:
        serve_at = datetime.fromisoformat(serve_raw)
    except ValueError:
        flash("That date and time looks invalid.", "error")
        return redirect(url_for("main.index"))

    food_ids = request.form.getlist("food_id")
    if not food_ids:
        flash("Pick at least one food for the roast.", "error")
        return redirect(url_for("main.index"))

    selections = []
    for food_id in food_ids:
        food = db.session.get(Food, int(food_id))
        if food is None:
            continue
        weight = None
        if food.category == "meat":
            weight_raw = request.form.get(f"weight_{food.id}", "").strip()
            try:
                weight = float(weight_raw)
            except ValueError:
                flash(f"Enter a weight in kg for {food.name}.", "error")
                return redirect(url_for("main.index"))
            if weight <= 0:
                flash(f"Weight for {food.name} must be greater than zero.", "error")
                return redirect(url_for("main.index"))
        selections.append({"food": food, "weight_kg": weight})

    if not selections:
        flash("None of the selected foods could be found.", "error")
        return redirect(url_for("main.index"))

    steps = build_plan(serve_at, selections)
    earliest = min(step.start_at for step in steps)
    return render_template(
        "plan.html",
        steps=steps,
        serve_at=serve_at,
        earliest=earliest,
    )


@bp.route("/foods")
def foods():
    items = Food.query.order_by(Food.category, Food.name).all()
    return render_template("foods.html", foods=items, categories=CATEGORIES)


@bp.route("/foods/new", methods=["GET", "POST"])
def food_new():
    if request.method == "POST":
        food, error = _food_from_form()
        if error:
            flash(error, "error")
            return render_template(
                "food_form.html",
                food=None,
                form=request.form,
                categories=CATEGORIES,
                meat_types=MEAT_TYPES,
            )
        db.session.add(food)
        db.session.commit()
        flash(f"Added {food.name}.", "success")
        return redirect(url_for("main.foods"))

    return render_template(
        "food_form.html",
        food=None,
        form={},
        categories=CATEGORIES,
        meat_types=MEAT_TYPES,
    )


@bp.route("/foods/<int:food_id>/edit", methods=["GET", "POST"])
def food_edit(food_id: int):
    food = db.session.get(Food, food_id)
    if food is None:
        flash("Food not found.", "error")
        return redirect(url_for("main.foods"))

    if request.method == "POST":
        updated, error = _food_from_form(existing=food)
        if error:
            flash(error, "error")
            return render_template(
                "food_form.html",
                food=food,
                form=request.form,
                categories=CATEGORIES,
                meat_types=MEAT_TYPES,
            )
        db.session.commit()
        flash(f"Updated {updated.name}.", "success")
        return redirect(url_for("main.foods"))

    return render_template(
        "food_form.html",
        food=food,
        form=food.to_dict(),
        categories=CATEGORIES,
        meat_types=MEAT_TYPES,
    )


@bp.route("/foods/<int:food_id>/delete", methods=["POST"])
def food_delete(food_id: int):
    food = db.session.get(Food, food_id)
    if food is None:
        flash("Food not found.", "error")
        return redirect(url_for("main.foods"))
    name = food.name
    db.session.delete(food)
    db.session.commit()
    flash(f"Deleted {name}.", "success")
    return redirect(url_for("main.foods"))


def _float_or_none(raw: str | None) -> float | None:
    if raw is None:
        return None
    value = raw.strip()
    if value == "":
        return None
    return float(value)


def _food_from_form(existing: Food | None = None) -> tuple[Food | None, str | None]:
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    meat_type = request.form.get("meat_type", "").strip() or None
    notes = request.form.get("notes", "").strip()

    if not name:
        return None, "Name is required."
    if category not in CATEGORIES:
        return None, "Choose a valid category."

    try:
        temperature_c = int(request.form.get("temperature_c", "").strip())
        minutes_per_kg = _float_or_none(request.form.get("minutes_per_kg"))
        base_minutes = _float_or_none(request.form.get("base_minutes")) or 0
        fixed_minutes = _float_or_none(request.form.get("fixed_minutes"))
        rest_minutes = _float_or_none(request.form.get("rest_minutes")) or 0
    except ValueError:
        return None, "Check the number fields — temperatures and times must be numbers."

    if category == "meat":
        if meat_type not in MEAT_TYPES:
            return None, "Choose a meat type."
        if minutes_per_kg is None:
            return None, "Meats need minutes per kg."
        fixed_minutes = None
    else:
        meat_type = None
        minutes_per_kg = None
        base_minutes = 0
        if fixed_minutes is None:
            return None, "Vegetables and other items need a fixed cook time."

    duplicate = Food.query.filter(Food.name == name).first()
    if duplicate and (existing is None or duplicate.id != existing.id):
        return None, "A food with that name already exists."

    food = existing or Food()
    food.name = name
    food.category = category
    food.meat_type = meat_type
    food.temperature_c = temperature_c
    food.minutes_per_kg = minutes_per_kg
    food.base_minutes = base_minutes
    food.fixed_minutes = fixed_minutes
    food.rest_minutes = rest_minutes
    food.notes = notes
    return food, None
