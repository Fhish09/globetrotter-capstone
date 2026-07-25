"""
app/destinations.py

Destination search endpoint.

Routes
------
GET /destinations?q=paris&tag=food&continent=Europe
    Returns destinations that match any of the provided query parameters.
    All parameters are optional; omitting them returns the full catalogue.

Data sources
------------
1. Curated seed data in data/destinations.json (rich descriptions + photos)
2. REST Countries API – expands the catalogue with world capitals (no API key)
"""
from flask import Blueprint, request, jsonify

from app.models import get_all_destinations
from app.external_api import get_combined_destinations

destinations_bp = Blueprint("destinations", __name__)


@destinations_bp.route("/destinations", methods=["GET"])
def search_destinations():
    """Search destinations by name keyword, tag, and/or continent.

    Query parameters (all optional):
        q          – free-text search against name, country, and description
        tag        – filter by a single interest tag (e.g. "beach")
        continent  – filter by continent name (e.g. "Europe")
        max_cost   – filter by maximum average daily cost (integer)
        source     – "local" to only return seed data, "all" (default) for combined

    Returns a JSON list of matching destination objects.
    """
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

    local = get_all_destinations()

    if source == "local":
        destinations = local
    else:
        # Merge curated seed data with REST Countries capitals
        destinations = get_combined_destinations(local)

    results = []

    for dest in destinations:
        # Free-text filter
        if q:
            searchable = " ".join([
                dest.get("name", ""),
                dest.get("country", ""),
                dest.get("description", ""),
            ]).lower()
            if q not in searchable:
                continue

        # Tag filter
        if tag and tag not in [t.lower() for t in dest.get("tags", [])]:
            continue

        # Continent filter
        if continent and continent != dest.get("continent", "").lower():
            continue

        # Cost filter
        if max_cost is not None:
            cost = dest.get("avg_cost_per_day")
            if cost is None or cost > max_cost:
                continue

        results.append(dest)

    return jsonify(results), 200
