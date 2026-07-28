"""
Auth microservice – registration, login, JWT, profile, preferences.
Port: 5001
"""
import os
import sys
import uuid
import datetime

import jwt
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from werkzeug.security import generate_password_hash, check_password_hash

sys.path.insert(0, os.path.dirname(__file__))
try:
    from observability import init_observability
except ImportError:
    def init_observability(app, service_name):
        import logging
        return logging.getLogger(service_name)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "globetrotter-secret-change-in-prod")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///auth.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

logger = init_observability(app, "auth")
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    preferences = db.Column(JSON, default=list, nullable=False)


with app.app_context():
    db.create_all()


def create_token(username: str) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + datetime.timedelta(hours=24),
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")


def get_username_from_token() -> str | None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "auth"}), 200


@app.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    preferences = data.get("preferences") or []

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "username already exists"}), 409

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        preferences=preferences,
    )
    db.session.add(user)
    db.session.commit()
    logger.info("event=user_registered username=%s", username)
    return jsonify({"message": "user registered successfully", "username": username}), 201


@app.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        logger.info("event=login_failed username=%s", username)
        return jsonify({"error": "invalid credentials"}), 401

    logger.info("event=login_success username=%s", username)
    return jsonify({"token": create_token(username), "username": username}), 200


@app.get("/me")
def me():
    username = get_username_from_token()
    if not username:
        return jsonify({"error": "authentication required"}), 401
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404
    return jsonify({"username": user.username, "preferences": user.preferences or []}), 200


@app.put("/preferences")
def update_preferences():
    username = get_username_from_token()
    if not username:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    preferences = data.get("preferences")
    if preferences is None:
        return jsonify({"error": "preferences field is required"}), 400
    if not isinstance(preferences, list):
        return jsonify({"error": "preferences must be a list"}), 400

    cleaned = [p.strip().lower() for p in preferences if isinstance(p, str) and p.strip()]
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    user.preferences = cleaned
    db.session.commit()
    logger.info("event=preferences_updated username=%s count=%s", username, len(cleaned))
    return jsonify({"message": "preferences updated successfully", "preferences": cleaned}), 200


@app.get("/internal/users/<username>")
def internal_user(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404
    return jsonify({"username": user.username, "preferences": user.preferences or []}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)), debug=True)
