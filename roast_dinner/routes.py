from datetime import datetime

from flask import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from roast_dinner import db
from roast_dinner.models import Food
from roast_dinner.pdf import render_plan_pdf
from roast_dinner.planner import PlanStep, build_plan, build_timeline, format_minutes

bp = Blueprint("main", __name__)

CATEGORIES = ("meat", "vegetable", "other")
MEAT_TYPES = ("chicken", "beef", "pork", "lamb")
SESSION_PLAN_KEY = "current_plan"


@bp.app_context_processor
def inject_plan_nav():
    return {"has_saved_plan": SESSION_PLAN_KEY in session}


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
    draft = _get_saved_plan()
    editing = request.args.get("edit") == "1" and draft is not None
    return render_template(
        "index.html",
        grouped=grouped,
        categories=CATEGORIES,
        editing=editing,
        saved_plan=draft,
        selected_ids=set(draft["food_ids"]) if editing else set(),
        selected_weights=draft["weights"] if editing else {},
        serve_at_value=draft["serve_at"] if editing else "",
    )


@bp.route("/plan", methods=["GET", "POST"])
def plan():
    if request.method == "POST":
        result = _build_plan_from_form()
        if result.error:
            flash(result.error, "error")
            return redirect(url_for("main.index", edit=1) if _get_saved_plan() else url_for("main.index"))
        _save_plan(result)
    else:
        result = _build_plan_from_session()
        if result is None:
            flash("No saved plan yet — choose your foods to get started.", "error")
            return redirect(url_for("main.index"))
        if result.error:
            flash(result.error, "error")
            return redirect(url_for("main.index", edit=1))

    events = build_timeline(result.serve_at, result.steps)
    return render_template(
        "plan.html",
        events=events,
        serve_at=result.serve_at,
        earliest=result.earliest,
        form_food_ids=result.food_ids,
        form_weights=result.weights,
        form_serve_at=result.serve_at.strftime("%Y-%m-%dT%H:%M"),
    )


@bp.route("/plan/edit")
def plan_edit():
    if not _get_saved_plan():
        flash("No saved plan to edit.", "error")
        return redirect(url_for("main.index"))
    return redirect(url_for("main.index", edit=1))


@bp.route("/plan/clear", methods=["POST"])
def plan_clear():
    session.pop(SESSION_PLAN_KEY, None)
    flash("Saved plan cleared.", "success")
    return redirect(url_for("main.index"))


@bp.route("/plan.pdf", methods=["GET", "POST"])
def plan_pdf():
    if request.method == "POST":
        result = _build_plan_from_form()
        if not result.error:
            _save_plan(result)
    else:
        result = _build_plan_from_session()
        if result is None:
            flash("No saved plan to export.", "error")
            return redirect(url_for("main.index"))

    if result is None or result.error:
        flash(result.error if result else "Could not build the PDF.", "error")
        return redirect(url_for("main.index"))

    pdf_bytes = render_plan_pdf(result.serve_at, result.earliest, result.steps)
    filename = f"roast-dinner-{result.serve_at.strftime('%Y%m%d-%H%M')}.pdf"
    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


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


class _PlanFormResult:
    def __init__(
        self,
        *,
        error: str | None = None,
        serve_at: datetime | None = None,
        steps: list[PlanStep] | None = None,
        earliest: datetime | None = None,
        food_ids: list[str] | None = None,
        weights: dict[str, str] | None = None,
    ):
        self.error = error
        self.serve_at = serve_at
        self.steps = steps or []
        self.earliest = earliest
        self.food_ids = food_ids or []
        self.weights = weights or {}


def _get_saved_plan() -> dict | None:
    data = session.get(SESSION_PLAN_KEY)
    if not data or not data.get("serve_at") or not data.get("food_ids"):
        return None
    return data


def _save_plan(result: _PlanFormResult) -> None:
    session.permanent = True
    session[SESSION_PLAN_KEY] = {
        "serve_at": result.serve_at.strftime("%Y-%m-%dT%H:%M"),
        "food_ids": list(result.food_ids),
        "weights": dict(result.weights),
    }
    session.modified = True


def _build_plan_from_session() -> _PlanFormResult | None:
    data = _get_saved_plan()
    if data is None:
        return None
    return _build_plan_from_values(
        data["serve_at"],
        list(data["food_ids"]),
        dict(data.get("weights") or {}),
    )


def _build_plan_from_form() -> _PlanFormResult:
    food_ids = request.form.getlist("food_id")
    weights = {
        str(food_id): request.form.get(f"weight_{food_id}", "").strip()
        for food_id in food_ids
    }
    return _build_plan_from_values(
        request.form.get("serve_at", "").strip(),
        food_ids,
        weights,
    )


def _build_plan_from_values(
    serve_raw: str,
    food_ids: list[str],
    weights: dict[str, str],
) -> _PlanFormResult:
    if not serve_raw:
        return _PlanFormResult(error="Choose when you want to eat.")

    try:
        serve_at = datetime.fromisoformat(serve_raw)
    except ValueError:
        return _PlanFormResult(error="That date and time looks invalid.")

    if not food_ids:
        return _PlanFormResult(error="Pick at least one food for the roast.")

    selections = []
    kept_weights: dict[str, str] = {}
    for food_id in food_ids:
        try:
            food = db.session.get(Food, int(food_id))
        except (TypeError, ValueError):
            continue
        if food is None:
            continue
        weight = None
        if food.category == "meat":
            weight_raw = (weights.get(str(food.id)) or "").strip()
            kept_weights[str(food.id)] = weight_raw
            try:
                weight = float(weight_raw)
            except ValueError:
                return _PlanFormResult(error=f"Enter a weight in kg for {food.name}.")
            if weight <= 0:
                return _PlanFormResult(
                    error=f"Weight for {food.name} must be greater than zero."
                )
        selections.append({"food": food, "weight_kg": weight})

    if not selections:
        return _PlanFormResult(
            error="None of the selected foods could be found. Edit the plan to choose foods again."
        )

    steps = build_plan(serve_at, selections)
    earliest = min(step.start_at for step in steps)
    return _PlanFormResult(
        serve_at=serve_at,
        steps=steps,
        earliest=earliest,
        food_ids=[str(item["food"].id) for item in selections],
        weights=kept_weights,
    )


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
        minutes_per_kg = _float_or_none(request.form.get("minutes_per_kg"))
        base_minutes = _float_or_none(request.form.get("base_minutes")) or 0
        fixed_minutes = _float_or_none(request.form.get("fixed_minutes"))
        rest_minutes = _float_or_none(request.form.get("rest_minutes")) or 0
        temp_raw = request.form.get("temperature_c", "").strip()
        temperature_c = int(temp_raw) if temp_raw else None
    except ValueError:
        return None, "Check the number fields — temperatures and times must be numbers."

    if category == "meat":
        if meat_type not in MEAT_TYPES:
            return None, "Choose a meat type."
        if temperature_c is None:
            return None, "Meats need a fan oven temperature."
        if minutes_per_kg is None:
            return None, "Meats need minutes per kg."
        fixed_minutes = None
    else:
        meat_type = None
        minutes_per_kg = None
        base_minutes = 0
        temperature_c = None
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
