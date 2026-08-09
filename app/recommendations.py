"""Douala-only personalised recommendations (costs in FCFA)."""
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


def _score(dest: dict, preferences: list, last_search: str = "") -> tuple:
    dest_tags = [t.lower() for t in dest.get("tags", [])]
    name = dest.get("name", "").lower()
    description = dest.get("description", "").lower()
    district = dest.get("district", "").lower()
    cost = dest.get("avg_cost_per_day") or 50000
    score = 1.0
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
        if ls in name or ls in district or ls in description or ls in " ".join(dest_tags):
            score += 4.0
            matched.append(f"related to “{last_search}”")

    # Prefer cheaper Douala sites slightly (FCFA)
    if cost <= 3000:
        score += 0.8
    elif cost <= 10000:
        score += 0.4

    return score, matched or ["Douala highlight"]


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
        limit = max(1, min(int(request.args.get("limit", 10)), 20))
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400

    destinations = [
        d for d in get_all_destinations()
        if (d.get("city") or "").lower() == "douala"
    ]
    if not destinations:
        destinations = get_all_destinations()

    districts = sorted({d.get("district") for d in destinations if d.get("district")})

    scored = []
    for d in destinations:
        s, m = _score(d, preferences, last_search)
        scored.append((s, d, m))
    scored.sort(key=lambda x: -x[0])

    results = []
    for score, dest, matched in scored[:limit]:
        entry = dict(dest)
        entry["match_score"] = round(score, 1)
        entry["match_reasons"] = matched
        entry["currency"] = "FCFA"
        results.append(entry)

    return jsonify({
        "destinations": results,
        "districts": districts,
        "regions": districts,
        "countries": ["Cameroon"],
        "currency": "FCFA",
        "last_search": last_search,
        "city": "Douala",
    }), 200
