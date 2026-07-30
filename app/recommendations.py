"""Personalised recommendations – HTML page or JSON API."""
from flask import Blueprint, request, jsonify, render_template

from app.auth import get_current_user
from app.models import get_all_destinations, get_user_by_username
from app.external_api import get_combined_destinations

recommendations_bp = Blueprint("recommendations", __name__)


def _wants_html() -> bool:
    accept = request.headers.get("Accept", "")
    if "application/json" in accept:
        return False
    if "text/html" in accept:
        return True
    return False


def _score_destination(dest: dict, preferences: list, last_search: str = "") -> tuple:
    dest_tags = [t.lower() for t in dest.get("tags", [])]
    name = dest.get("name", "").lower()
    description = dest.get("description", "").lower()
    country = dest.get("country", "").lower()
    cost = dest.get("avg_cost_per_day") or 100
    source = dest.get("source", "local")

    score = 0.0
    matched = []

    for pref in preferences:
        if pref in dest_tags:
            score += 3.0
            matched.append(pref)
        elif pref in name or pref in description:
            score += 1.0
            if pref not in matched:
                matched.append(f"{pref} (mentioned)")

    # Boost places related to last search (country or name keyword)
    if last_search:
        ls = last_search.lower()
        if ls in name or ls in country or ls in description:
            score += 4.0
            matched.append(f"related to “{last_search}”")

    if cost <= 60:
        score += 0.8
    elif cost <= 100:
        score += 0.4

    if not dest.get("source") or source in ("local", "tourist_curated"):
        score += 2.0

    return score, matched


@recommendations_bp.route("/recommendations", methods=["GET"])
def get_recommendations():
    if _wants_html():
        return render_template("recommendations.html")

    username = get_current_user(request)
    if not username:
        return jsonify({"error": "authentication required"}), 401

    user = get_user_by_username(username)
    if not user:
        return jsonify({"error": "user not found"}), 404

    preferences = [p.lower().strip() for p in user.get("preferences", []) if p.strip()]
    last_search = (request.args.get("q") or request.args.get("last_search") or "").strip()

    try:
        limit = int(request.args.get("limit", 8))
        limit = max(1, min(limit, 20))
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400

    local = get_all_destinations()
    try:
        destinations = get_combined_destinations(local)
    except Exception:
        destinations = local

    # Country snapshot for UI
    countries = sorted({
        d.get("country") for d in destinations if d.get("country")
    })[:40]

    scored = []
    for dest in destinations:
        score, matched = _score_destination(dest, preferences, last_search)
        if score > 0 or not preferences:
            scored.append((score if preferences or last_search else 1.0, dest, matched or ["popular pick"]))

    scored.sort(key=lambda x: (-x[0], x[1].get("avg_cost_per_day") or 999))

    results = []
    continent_count = {}
    for score, dest, matched in scored:
        continent = dest.get("continent", "Unknown")
        count = continent_count.get(continent, 0)
        if count >= 2 and len(results) >= 3:
            continue
        entry = dict(dest)
        entry["match_score"] = round(score, 1)
        entry["match_reasons"] = matched
        results.append(entry)
        continent_count[continent] = count + 1
        if len(results) >= limit:
            break

    return jsonify({"destinations": results, "countries": countries, "last_search": last_search}), 200
