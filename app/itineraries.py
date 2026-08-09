"""Itineraries + Douala day-plan builder."""
import uuid
import datetime

from flask import Blueprint, request, jsonify, render_template

from app.auth import get_current_user
from app.models import get_itineraries_for_user, save_itinerary, get_all_destinations

itineraries_bp = Blueprint("itineraries", __name__)


def _wants_html() -> bool:
    accept = (request.headers.get("Accept") or "").lower()
    if "application/json" in accept:
        return False
    if "text/html" in accept:
        return True
    return False


@itineraries_bp.route("/itineraries", methods=["GET"])
def list_itineraries():
    if _wants_html():
        return render_template("itineraries.html")

    username = get_current_user(request)
    if not username:
        return jsonify({"error": "authentication required"}), 401

    itineraries = get_itineraries_for_user(username)
    return jsonify(itineraries), 200


@itineraries_bp.route("/day-plan", methods=["GET"])
def day_plan_page():
    """Interactive one-day Douala itinerary builder (HTML)."""
    return render_template("day_plan.html")


@itineraries_bp.route("/itineraries", methods=["POST"])
def create_itinerary():
    username = get_current_user(request)
    if not username:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    destinations = data.get("destinations", [])

    if not title:
        return jsonify({"error": "title is required"}), 400

    if not isinstance(destinations, list):
        return jsonify({"error": "destinations must be a list"}), 400

    itinerary = {
        "id": str(uuid.uuid4()),
        "username": username,
        "title": title,
        "destinations": destinations,
        "slots": data.get("slots") or {},
        "total_fcfa": data.get("total_fcfa"),
        "start_date": data.get("start_date", ""),
        "end_date": data.get("end_date", ""),
        "notes": data.get("notes", ""),
        "kind": data.get("kind", "trip"),
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    save_itinerary(itinerary)
    return jsonify(itinerary), 201
