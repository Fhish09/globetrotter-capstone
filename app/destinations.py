"""
app/destinations.py

Destination search endpoint + HTML page for browser navigation.

GET /destinations
  - Browser (Accept: text/html) → destinations.html
  - fetch() / API clients → JSON list
"""
from flask import Blueprint, request, jsonify, render_template

from app.models import get_all_destinations
from app.external_api import get_combined_destinations

destinations_bp = Blueprint("destinations", __name__)


def _wants_html() -> bool:
    accept = request.headers.get("Accept", "")
    # fetch() often sends */* — treat explicit HTML or no JSON preference as page only when navigating
    if "application/json" in accept:
        return False
    if "text/html" in accept:
        return True
    # Default for plain fetch() from our templates: JSON
    return False


@destinations_bp.route("/destinations", methods=["GET"])
def search_destinations():
    """HTML page for browsers, JSON for API/fetch."""
    if _wants_html():
        return render_template("destinations.html")

    q = request.args.get("q", "").strip().lower()
    tag = request.args.get("tag", "").strip().lower()
    continent = request.args.get("continent", "").strip().lower()
    max_cost_str = request.args.get("max_cost", "").strip()
    source = request.args.get("source", "all").strip().lower()

    max_cost = None
    if max_cost_str:
        try:
            max_cost = int(max_cost_str)
        except ValueError:
            return jsonify({"error": "max_cost must be an integer"}), 400

    try:
        local = get_all_destinations()
    except Exception as exc:
        return jsonify({"error": f"failed to load destinations: {exc}"}), 500

    if source == "local":
        destinations = local
    else:
        try:
            destinations = get_combined_destinations(local)
        except Exception:
            destinations = local

    results = []

    for dest in destinations:
        if q:
            searchable = " ".join([
                dest.get("name", ""),
                dest.get("country", ""),
                dest.get("description", ""),
            ]).lower()
            if q not in searchable:
                continue

        if tag and tag not in [t.lower() for t in dest.get("tags", [])]:
            continue

        if continent and continent != dest.get("continent", "").lower():
            continue

        if max_cost is not None:
            cost = dest.get("avg_cost_per_day")
            if cost is None or cost > max_cost:
                continue

        results.append(dest)

    return jsonify(results), 200
