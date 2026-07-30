"""Flask application factory."""
import os
from flask import Flask

from app.models import db


def create_app(config_overrides: dict | None = None):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "globetrotter-secret-change-in-prod"
    )

    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        # File-based SQLite so users/trips survive Flask restarts (local Windows)
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base, "data", "globetrotter.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        # forward slashes work on Windows for SQLAlchemy
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path.replace("\\", "/")

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    from app.auth import auth_bp
    from app.destinations import destinations_bp
    from app.recommendations import recommendations_bp
    from app.itineraries import itineraries_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(destinations_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(itineraries_bp)

    return app
