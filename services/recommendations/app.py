"""
Recommendations microservice.
Calls Auth + Destinations with circuit breakers and optional Redis cache.
Port: 5003
"""
import os
import sys

import jwt
from flask import Flask, request, jsonify

sys.path.insert(0, os.path.dirname(__file__))

try:
    from http_client import call_service, ServiceError, register_breaker
    from circuit_breaker import CircuitBreaker
    from cache import cache_get, cache_set
except ImportError:
    import requests

    class ServiceError(Exception):
        def __init__(self, service, message, status_code=503):
            self.service = service
            self.message = message
            self.status_code = status_code

    def call_service(service_name, method, url, **kwargs):
        r = requests.request(method, url, timeout=kwargs.get("timeout", 5),
                             headers=kwargs.get("headers"))
        if r.status_code >= 400:
            raise ServiceError(service_name, r.reason, r.status_code)
        return r.json()

    def register_breaker(name, breaker): pass
    def cache_get(key): return None
    def cache_set(key, value, ttl_seconds=300): pass
    CircuitBreaker = None

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "globetrotter-secret-change-in-prod")
AUTH_URL = os.environ.get("AUTH_SERVICE_URL", "http://auth:5001").rstrip("/")
DEST_URL = os.environ.get("DESTINATIONS_SERVICE_URL", "http://destinations:5002").rstrip("/")
CACHE_TTL = int(os.environ.get("CACHE_TTL", "60"))

# Circuit breakers for upstreams
if CircuitBreaker is not None:
    _auth_breaker = CircuitBreaker("auth", failure_threshold=5, recovery_timeout=20)
    _dest_breaker = CircuitBreaker("destinations", failure_threshold=5, recovery_timeout=20)
    register_breaker("auth", _auth_breaker)
    register_breaker("destinations", _dest_breaker)
else:
    _auth_breaker = _dest_breaker = None


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
    deps = {}
    for name, url in (("auth", AUTH_URL), ("destinations", DEST_URL)):
        try:
            call_service(name, "GET", f"{url}/health", timeout=2, retries=0)
            deps[name] = "up"
        except ServiceError:
            deps[name] = "down"

    breakers = {}
    if _auth_breaker:
        breakers["auth"] = _auth_breaker.status()
    if _dest_breaker:
        breakers["destinations"] = _dest_breaker.status()

    status = "ok" if all(v == "up" for v in deps.values()) else "degraded"
    return jsonify({
        "status": status,
        "service": "recommendations",
        "dependencies": deps,
        "circuit_breakers": breakers,
    }), 200


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

    cache_key = f"rec:{username}:{limit}"
    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify(cached), 200

    try:
        user = call_service("auth", "GET", f"{AUTH_URL}/internal/users/{username}", timeout=5, retries=2)
        preferences = [p.lower().strip() for p in (user or {}).get("preferences", []) if p]
    except ServiceError as exc:
        code = 404 if exc.status_code == 404 else 503
        return jsonify({"error": f"auth service: {exc.message}", "service": "auth"}), code

    try:
        destinations = call_service("destinations", "GET", f"{DEST_URL}/destinations", timeout=10, retries=2) or []
    except ServiceError as exc:
        return jsonify({"error": f"destinations service: {exc.message}", "service": "destinations"}), 503

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
        cache_set(cache_key, results, CACHE_TTL)
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

    cache_set(cache_key, results, CACHE_TTL)
    return jsonify(results), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5003)), debug=True)
