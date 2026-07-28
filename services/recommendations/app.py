"""
Recommendations microservice.
Calls Auth (user preferences) and Destinations (catalogue) over HTTP.
Port: 5003
"""
import os

import jwt
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "globetrotter-secret-change-in-prod")
AUTH_URL = os.environ.get("AUTH_SERVICE_URL", "http://auth:5001")
DEST_URL = os.environ.get("DESTINATIONS_SERVICE_URL", "http://destinations:5002")


def get_username_from_token() -> str | None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


def _score(dest: dict, preferences: list[str]) -> tuple[float, list[str]]:
    dest_tags = [t.lower() for t in dest.get("tags", [])]
    name = dest.get("name", "").lower()
    description = dest.get("description", "").lower()
    cost = dest.get("avg_cost_per_day") or 100
    source = dest.get("source") or "local"

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

    if cost <= 60:
        score += 0.8
    elif cost <= 100:
        score += 0.4

    if source in ("local", "tourist_curated") or not dest.get("source"):
        score += 2.5
        if "popular tourist spot" not in matched:
            matched.append("popular tourist spot")

    return score, matched


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "recommendations"}), 200


@app.get("/recommendations")
def recommendations():
    username = get_username_from_token()
    if not username:
        return jsonify({"error": "authentication required"}), 401

    try:
        limit = int(request.args.get("limit", 6))
        limit = max(1, min(limit, 20))
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400

    # Inter-service call: Auth
    try:
        r = requests.get(f"{AUTH_URL}/internal/users/{username}", timeout=5)
        if r.status_code != 200:
            return jsonify({"error": "user not found"}), 404
        preferences = [p.lower().strip() for p in r.json().get("preferences", []) if p]
    except requests.RequestException:
        return jsonify({"error": "auth service unavailable"}), 503

    # Inter-service call: Destinations
    try:
        r = requests.get(f"{DEST_URL}/destinations", timeout=10)
        r.raise_for_status()
        destinations = r.json()
    except requests.RequestException:
        return jsonify({"error": "destinations service unavailable"}), 503

    if not preferences:
        results = []
        seen = set()
        for dest in destinations:
            cont = dest.get("continent", "Unknown")
            src = dest.get("source") or "local"
            if src not in ("local", "tourist_curated") and dest.get("source"):
                continue
            if cont in seen and len(results) >= 3:
                continue
            entry = dict(dest)
            entry["match_score"] = 0
            entry["match_reasons"] = ["popular tourist pick"]
            results.append(entry)
            seen.add(cont)
            if len(results) >= limit:
                break
        return jsonify(results), 200

    scored = []
    for dest in destinations:
        score, matched = _score(dest, preferences)
        if score > 0:
            scored.append((score, dest, matched))
    scored.sort(key=lambda x: (-x[0], x[1].get("avg_cost_per_day") or 999))

    results = []
    continent_count = {}
    for score, dest, matched in scored:
        cont = dest.get("continent", "Unknown")
        if continent_count.get(cont, 0) >= 2 and len(results) >= 3:
            continue
        entry = dict(dest)
        entry["match_score"] = round(score, 1)
        entry["match_reasons"] = matched
        results.append(entry)
        continent_count[cont] = continent_count.get(cont, 0) + 1
        if len(results) >= limit:
            break

    return jsonify(results), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5003)), debug=True)
