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
from app.external_api import get_combined_destinations

recommendations_bp = Blueprint("recommendations", __name__)


def _score_destination(dest: dict, preferences: list[str]) -> tuple[float, list[str]]:
    """Calculate a relevance score and list of matching reasons.

    Scoring:
    - +3 per exact preference tag match
    - +1 for keyword match in name/description
    - Budget-friendly bonus
    - Strong boost for curated tourist destinations (famous travel spots)
    """
    dest_tags = [t.lower() for t in dest.get("tags", [])]
    name = dest.get("name", "").lower()
    description = dest.get("description", "").lower()
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

    # Budget preference
    if cost <= 60:
        score += 0.8
    elif cost <= 100:
        score += 0.4

    # Prefer famous tourist spots over generic capitals
    if source in (None, "local") or source == "local":
        # Seed data has no source field → treat as local
        if not dest.get("source"):
            score += 2.5
            if "curated pick" not in matched:
                matched.append("top destination")
    if source == "tourist_curated":
        score += 2.5
        if "popular tourist spot" not in matched:
            matched.append("popular tourist spot")

    return score, matched


@recommendations_bp.route("/recommendations", methods=["GET"])
def get_recommendations():
    """Return personalised destination recommendations for the logged-in user.

    Prefers curated tourist destinations and seed data over plain country capitals.

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
        limit = max(1, min(limit, 20))
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400

    # Use full catalogue: seed + tourist cities + country capitals
    local = get_all_destinations()
    destinations = get_combined_destinations(local)

    # --- No preferences: return diverse top tourist picks ---
    if not preferences:
        # Prefer tourist_curated and local first
        def popularity_key(d):
            source = d.get("source") or "local"
            source_rank = 0 if source in ("local", "tourist_curated") or not d.get("source") else 1
            return (source_rank, d.get("avg_cost_per_day") or 999)

        popular = sorted(destinations, key=popularity_key)
        results = []
        seen_continents = set()
        for dest in popular:
            continent = dest.get("continent", "Unknown")
            if continent not in seen_continents or len(results) < 3:
                entry = dict(dest)
                entry["match_score"] = 0
                entry["match_reasons"] = ["popular tourist pick"]
                results.append(entry)
                seen_continents.add(continent)
            if len(results) >= limit:
                break
        return jsonify(results), 200

    # --- Score every destination ---
    scored = []
    for dest in destinations:
        score, matched = _score_destination(dest, preferences)
        if score > 0:
            scored.append((score, dest, matched))

    scored.sort(key=lambda x: (-x[0], x[1].get("avg_cost_per_day") or 999))

    # Diversity across continents
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
