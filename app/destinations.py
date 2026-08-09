"""Douala tourist sites — curated JSON + optional live OSM places."""
from flask import Blueprint, request, jsonify, render_template

from app.models import get_all_destinations
from app.places_api import fetch_douala_live_places, merge_curated_and_live

destinations_bp = Blueprint("destinations", __name__)


def _wants_html() -> bool:
    accept = (request.headers.get("Accept") or "").lower()
    if "application/json" in accept:
        return False
    if "text/html" in accept:
        return True
    return False


def _filter_douala(destinations: list) -> list:
    return [
        d
        for d in destinations
        if (d.get("city") or "").lower() == "douala"
        or (d.get("country") or "").lower() in ("cameroon", "cameroun")
    ]


def _apply_filters(destinations: list) -> tuple[list, str | None]:
    q = request.args.get("q", "").strip().lower()
    tag = request.args.get("tag", "").strip().lower()
    district = request.args.get("district", "").strip().lower()
    max_cost_str = request.args.get("max_cost", "").strip()
    source = request.args.get("source", "").strip().lower()  # curated | live | all

    max_cost = None
    if max_cost_str:
        try:
            max_cost = int(max_cost_str)
        except ValueError:
            return [], "max_cost must be an integer"

    results = []
    for dest in destinations:
        if source == "curated" and dest.get("source") == "openstreetmap":
            continue
        if source == "live" and dest.get("source") != "openstreetmap":
            continue
        if q:
            searchable = " ".join(
                [
                    dest.get("name", ""),
                    dest.get("district", ""),
                    dest.get("city", ""),
                    dest.get("description", ""),
                ]
            ).lower()
            if q not in searchable:
                continue
        if tag and tag not in [t.lower() for t in dest.get("tags", [])]:
            continue
        if district and district != (dest.get("district") or "").lower():
            continue
        if max_cost is not None:
            cost = dest.get("avg_cost_per_day")
            if cost is None or cost > max_cost:
                continue
        results.append(dest)
    return results, None


@destinations_bp.route("/destinations", methods=["GET"])
def search_destinations():
    if _wants_html():
        return render_template("destinations.html")

    include_live = request.args.get("live", "1").strip() not in ("0", "false", "no")

    try:
        curated = _filter_douala(get_all_destinations())
        if include_live:
            live = fetch_douala_live_places()
            destinations = merge_curated_and_live(curated, live)
        else:
            destinations = curated
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    results, err = _apply_filters(destinations)
    if err:
        return jsonify({"error": err}), 400
    return jsonify(results), 200


@destinations_bp.route("/destinations/live", methods=["GET"])
def live_destinations():
    """Force-refresh or return cached OSM tourism POIs in Douala only."""
    force = request.args.get("refresh", "").strip() in ("1", "true", "yes")
    try:
        places = fetch_douala_live_places(force=force)
        return jsonify(
            {
                "city": "Douala",
                "source": "openstreetmap_overpass",
                "count": len(places),
                "places": places,
            }
        ), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
