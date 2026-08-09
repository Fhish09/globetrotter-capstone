"""User registration, login, JWT, profile."""
import uuid
import datetime

import jwt
from flask import Blueprint, request, jsonify, current_app, render_template
from werkzeug.security import generate_password_hash, check_password_hash

from app.models import get_user_by_username, save_user, update_user_preferences

auth_bp = Blueprint("auth", __name__)


def create_token(username: str, secret: str) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + datetime.timedelta(hours=24),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> dict:
    return jwt.decode(token, secret, algorithms=["HS256"])


def get_current_user(request_obj) -> str | None:
    auth_header = request_obj.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    try:
        payload = decode_token(token, current_app.config["SECRET_KEY"])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", mode="login")

    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    user = get_user_by_username(username)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "invalid credentials"}), 401

    token = create_token(username, current_app.config["SECRET_KEY"])
    return jsonify({"token": token, "username": username}), 200


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("login.html", mode="register")

    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    preferences = data.get("preferences", [])

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    if get_user_by_username(username):
        return jsonify({"error": "username already exists"}), 409

    user = {
        "id": str(uuid.uuid4()),
        "username": username,
        "password_hash": generate_password_hash(password),
        "preferences": preferences,
    }
    save_user(user)
    return jsonify({"message": "user registered successfully", "username": username}), 201


@auth_bp.route("/me", methods=["GET"])
def get_me():
    username = get_current_user(request)
    if not username:
        return jsonify({"error": "authentication required"}), 401

    user = get_user_by_username(username)
    if not user:
        return jsonify({"error": "user not found"}), 404

    return jsonify({
        "username": user["username"],
        "preferences": user.get("preferences", []),
    }), 200


@auth_bp.route("/preferences", methods=["PUT"])
def update_preferences():
    username = get_current_user(request)
    if not username:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    preferences = data.get("preferences")

    if preferences is None:
        return jsonify({"error": "preferences field is required"}), 400

    if not isinstance(preferences, list):
        return jsonify({"error": "preferences must be a list"}), 400

    cleaned = [p.strip().lower() for p in preferences if isinstance(p, str) and p.strip()]
    success = update_user_preferences(username, cleaned)
    if not success:
        return jsonify({"error": "user not found"}), 404

    return jsonify({
        "message": "preferences updated successfully",
        "preferences": cleaned,
    }), 200
