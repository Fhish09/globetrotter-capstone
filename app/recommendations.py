"""Cameroon-only personalised recommendations."""
from flask import Blueprint, request, jsonify, render_template

from app.auth import get_current_user
from app.models import get_all_destinations, get_user_by_username

recommendations_bp = Blueprint("recommendations", __name__)


def _wants_html() -> bool:
    accept = (request.headers.get("Accept") or "").lower()
    if "application/json" in accept:
        return False
    if "text/html" in accept:
        return True
    return False


def _cameroon_only(destinations: list) -> list:
    return [
        d for d in destinations
        if (d.get("country") or "Cameroon").lower() in ("cameroon", "cameroun")
    ]


def _score_destination(dest: dict, preferences: list, last_search: str = "") -> tuple:
    dest_tags = [t.lower() for t in dest.get("tags", [])]
    name = dest.get("name", "").lower()
    description = dest.get("description", "").lower()
    region = dest.get("region", "").lower()
    cost = dest.get("avg_cost_per_day") or 100

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

    if last_search:
        ls = last_search.lower()
        if ls in name or ls in region or ls in description or ls in " ".join(dest_tags):
            score += 4.0
            matched.append(f"related to “{last_search}”")

    if cost <= 45:
        score += 0.8
    elif cost <= 60:
        score += 0.4

    score += 1.0  # all are curated Cameroon picks
    return score, matched or ["Cameroon highlight"]


@recommendations_bp.route("/recommendations", methods=["GET"])
def get_recommendations():
    if _wants_html():
        return render_template("recommendations.html")

    username = get_current_user(request)
    if not username:
        return jsonify({"error": "authentication required"}), 401

    user = get_user_by_username(username)
    if not user:
        return jsonify({"error": "session expired — please login again"}), 401

    preferences = [p.lower().strip() for p in user.get("preferences", []) if p.strip()]
    last_search = (request.args.get("q") or request.args.get("last_search") or "").strip()

    try:
        limit = int(request.args.get("limit", 8))
        limit = max(1, min(limit, 20))
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400

    destinations = _cameroon_only(get_all_destinations())

    regions = sorted({d.get("region") for d in destinations if d.get("region")})

    scored = []
    for dest in destinations:
        score, matched = _score_destination(dest, preferences, last_search)
        scored.append((score, dest, matched))

    scored.sort(key=lambda x: (-x[0], x[1].get("avg_cost_per_day") or 999))

    results = []
    for score, dest, matched in scored[:limit]:
        entry = dict(dest)
        entry["match_score"] = round(score, 1)
        entry["match_reasons"] = matched
        results.append(entry)

    return jsonify({
        "destinations": results,
        "regions": regions,
        "countries": ["Cameroon"],
        "last_search": last_search,
    }), 200
