"""
app/recommendations.py

Personalised destination recommendations.

Routes
------
GET /recommendations
    Returns destinations that best match the authenticated user's preferences.
    Requires a valid JWT in the Authorization header.
"""
from flask import Blueprint, request, jsonify

from app.auth import get_current_user
from app.models import get_all_destinations, get_user_by_username

recommendations_bp = Blueprint("recommendations", __name__)


def _score_destination(dest: dict, preferences: list[str]) -> tuple[float, list[str]]:
    """Calculate a relevance score and list of matching reasons for a destination.

    Scoring rules:
    - +3 for each exact preference tag match
    - +1 for partial / related keyword matches in description or name
    - Small bonus for lower-cost destinations (budget-friendly bias)
    """
    dest_tags = [t.lower() for t in dest.get("tags", [])]
    name = dest.get("name", "").lower()
    description = dest.get("description", "").lower()
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

    # Mild preference for more affordable destinations
    if cost <= 60:
        score += 0.8
    elif cost <= 100:
        score += 0.4

    return score, matched


@recommendations_bp.route("/recommendations", methods=["GET"])
def get_recommendations():
    """Return personalised destination recommendations for the logged-in user.

    Improvements over the original version:
    - Weighted scoring (exact tag matches are stronger)
    - Diversity across continents
    - Light budget preference
    - Match reasons returned for transparency
    - Graceful fallback when the user has no preferences

    Query parameters:
        limit (int, default 6) – maximum number of results

    Requires: Authorization: Bearer <token>
    """
    username = get_current_user(request)
    if not username:
        return jsonify({"error": "authentication required"}), 401

    user = get_user_by_username(username)
    if not user:
        return jsonify({"error": "user not found"}), 404

    preferences = [p.lower().strip() for p in user.get("preferences", []) if p.strip()]

    try:
        limit = int(request.args.get("limit", 6))
        limit = max(1, min(limit, 20))  # safety bounds
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400

    destinations = get_all_destinations()

    # --- No preferences: return a diverse popular set ---
    if not preferences:
        # Prefer a mix of continents and lower-to-mid cost destinations
        popular = sorted(
            destinations,
            key=lambda d: (d.get("avg_cost_per_day") or 999)
        )
        results = []
        seen_continents = set()
        for dest in popular:
            continent = dest.get("continent", "Unknown")
            if continent not in seen_continents or len(results) < 3:
                entry = dict(dest)
                entry["match_score"] = 0
                entry["match_reasons"] = ["popular / diverse pick"]
                results.append(entry)
                seen_continents.add(continent)
            if len(results) >= limit:
                break
        return jsonify(results), 200

    # --- Score every destination ---
    scored = []
    for dest in destinations:
        score, matched = _score_destination(dest, preferences)
        if score > 0:  # only keep destinations with at least some relevance
            scored.append((score, dest, matched))

    # Sort by score descending, then by cost ascending as tie-breaker
    scored.sort(key=lambda x: (-x[0], x[1].get("avg_cost_per_day") or 999))

    # --- Diversity: try not to return too many from the same continent ---
    results = []
    continent_count = {}

    for score, dest, matched in scored:
        continent = dest.get("continent", "Unknown")
        count = continent_count.get(continent, 0)

        # Allow up to 2 from the same continent before skipping
        if count >= 2 and len(results) >= 3:
            continue

        entry = dict(dest)
        entry["match_score"] = round(score, 1)
        entry["match_reasons"] = matched
        results.append(entry)
        continent_count[continent] = count + 1

        if len(results) >= limit:
            break

    # If diversity filter left us short, fill with remaining high-scoring ones
    if len(results) < limit:
        already_ids = {r.get("id") for r in results}
        for score, dest, matched in scored:
            if dest.get("id") not in already_ids:
                entry = dict(dest)
                entry["match_score"] = round(score, 1)
                entry["match_reasons"] = matched
                results.append(entry)
                if len(results) >= limit:
                    break

    return jsonify(results), 200
