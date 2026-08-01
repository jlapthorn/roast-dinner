from pathlib import Path
import os
from datetime import timedelta

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parent.parent / "templates"),
        static_folder=str(Path(__file__).resolve().parent.parent / "static"),
    )
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "roast-dinner-dev-key")
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=14)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    # Trust OpenShift / reverse-proxy headers for HTTPS cookie decisions.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    data_dir = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parent.parent / "instance"))
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "roast_dinner.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from roast_dinner import routes  # noqa: WPS433
    from roast_dinner.seed import seed_foods

    app.register_blueprint(routes.bp)

    with app.app_context():
        db.create_all()
        _migrate_optional_temperature()
        _migrate_favourites()
        seed_foods()
        _ensure_default_favourites()

    return app


def _migrate_optional_temperature() -> None:
    """Allow NULL temperatures and clear them for vegetables/other."""
    with db.engine.begin() as conn:
        rows = conn.execute(text("PRAGMA table_info(foods)")).fetchall()
        if not rows:
            return
        temp_col = next((row for row in rows if row[1] == "temperature_c"), None)
        if temp_col is None:
            return
        not_null = bool(temp_col[3])
        if not_null:
            conn.execute(
                text(
                    """
                    CREATE TABLE foods_new (
                        id INTEGER NOT NULL PRIMARY KEY,
                        name VARCHAR(120) NOT NULL UNIQUE,
                        category VARCHAR(32) NOT NULL,
                        meat_type VARCHAR(32),
                        temperature_c INTEGER,
                        minutes_per_kg FLOAT,
                        base_minutes FLOAT,
                        fixed_minutes FLOAT,
                        rest_minutes FLOAT,
                        notes TEXT,
                        is_favourite BOOLEAN NOT NULL DEFAULT 0
                    )
                    """
                )
            )
            conn.execute(
                text(
                    """
                    INSERT INTO foods_new (
                        id, name, category, meat_type, temperature_c,
                        minutes_per_kg, base_minutes, fixed_minutes, rest_minutes, notes, is_favourite
                    )
                    SELECT id, name, category, meat_type,
                           CASE WHEN category = 'meat' THEN temperature_c END,
                           minutes_per_kg, base_minutes, fixed_minutes, rest_minutes, notes, 0
                    FROM foods
                    """
                )
            )
            conn.execute(text("DROP TABLE foods"))
            conn.execute(text("ALTER TABLE foods_new RENAME TO foods"))
        else:
            conn.execute(
                text(
                    "UPDATE foods SET temperature_c = NULL WHERE category != 'meat'"
                )
            )
        conn.execute(
            text(
                """
                UPDATE foods
                SET notes = :notes
                WHERE name = 'Yorkshire puddings'
                  AND (notes IS NULL OR notes NOT LIKE '%220%')
                """
            ),
            {
                "notes": (
                    "About 220°C fan. Hot tin and hot fat — "
                    "do not open the oven while they rise."
                )
            },
        )


def _migrate_favourites() -> None:
    """Add is_favourite column for existing SQLite databases."""
    with db.engine.begin() as conn:
        rows = conn.execute(text("PRAGMA table_info(foods)")).fetchall()
        if not rows:
            return
        if any(row[1] == "is_favourite" for row in rows):
            return
        conn.execute(
            text(
                "ALTER TABLE foods ADD COLUMN is_favourite BOOLEAN NOT NULL DEFAULT 0"
            )
        )


def _ensure_default_favourites() -> None:
    """On first favourites rollout, mark a classic Sunday set if none are set."""
    from roast_dinner.models import Food

    if Food.query.filter_by(is_favourite=True).count() > 0:
        return
    defaults = {
        "Chicken",
        "Carrots",
        "Peas",
        "Broccoli",
        "Yorkshire puddings",
    }
    updated = False
    for food in Food.query.filter(Food.name.in_(defaults)):
        food.is_favourite = True
        updated = True
    if updated:
        db.session.commit()
