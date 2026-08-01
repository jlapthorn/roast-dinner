from pathlib import Path

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parent.parent / "templates"),
        static_folder=str(Path(__file__).resolve().parent.parent / "static"),
    )
    app.config["SECRET_KEY"] = "roast-dinner-dev-key"
    instance_path = Path(__file__).resolve().parent.parent / "instance"
    instance_path.mkdir(exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{instance_path / 'roast_dinner.db'}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from roast_dinner import routes  # noqa: WPS433
    from roast_dinner.seed import seed_foods

    app.register_blueprint(routes.bp)

    with app.app_context():
        db.create_all()
        seed_foods()

    return app
