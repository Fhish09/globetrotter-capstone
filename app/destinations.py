"""Cameroon destinations search — HTML page or JSON API."""
from flask import Blueprint, request, jsonify, render_template

from app.models import get_all_destinations

destinations_bp = Blueprint("destinations", __name__)


def _wants_html() -> bool:
    accept = (request.headers.get("Accept") or "").lower()
    if "application/json" in accept:
        return False
    if "text/html" in accept:
        return True
    return False


@destinations_bp.route("/destinations", methods=["GET"])
def search_destinations():
    if _wants_html():
        return render_template("destinations.html")

    q = request.args.get("q", "").strip().lower()
    tag = request.args.get("tag", "").strip().lower()
    region = request.args.get("region", "").strip().lower()
    continent = request.args.get("continent", "").strip().lower()
    max_cost_str = request.args.get("max_cost", "").strip()

    max_cost = None
    if max_cost_str:
        try:
            max_cost = int(max_cost_str)
        except ValueError:
            return jsonify({"error": "max_cost must be an integer"}), 400

    try:
        destinations = get_all_destinations()
    except Exception as exc:
        return jsonify({"error": f"failed to load destinations: {exc}"}), 500

    # Only Cameroon catalogue
    destinations = [
        d for d in destinations
        if (d.get("country") or "").lower() in ("cameroon", "cameroun", "")
        or not d.get("country")
    ]

    results = []
    for dest in destinations:
        if q:
            searchable = " ".join([
                dest.get("name", ""),
                dest.get("country", ""),
                dest.get("region", ""),
                dest.get("description", ""),
            ]).lower()
            if q not in searchable:
                continue
        if tag and tag not in [t.lower() for t in dest.get("tags", [])]:
            continue
        if region and region != (dest.get("region") or "").lower():
            continue
        if continent and continent != (dest.get("continent") or "").lower():
            continue
        if max_cost is not None:
            cost = dest.get("avg_cost_per_day")
            if cost is None or cost > max_cost:
                continue
        results.append(dest)

    return jsonify(results), 200
