"""
Destinations microservice – search catalogue (seed + tourist + REST Countries).
Port: 5002
"""
import json
import logging
import os
from typing import Optional

import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
logger = logging.getLogger(__name__)

DESTINATIONS_FILE = os.path.join(os.path.dirname(__file__), "data", "destinations.json")
_cache: Optional[list] = None

# --- Tourist curated (Cameroon + world) – subset imported inline for independence ---
from tourist_data import TOP_TOURIST_DESTINATIONS  # noqa: E402


def _load_seed() -> list:
    if not os.path.exists(DESTINATIONS_FILE):
        return []
    with open(DESTINATIONS_FILE, encoding="utf-8") as f:
        content = f.read().strip()
        return json.loads(content) if content else []


def _fetch_restcountries() -> list:
    url = "https://restcountries.com/v3.1/all?fields=name,capital,region,subregion,flags"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        countries = resp.json()
    except Exception as exc:
        logger.warning("REST Countries unavailable: %s", exc)
        return []

    region_map = {
        "Africa": "Africa", "Asia": "Asia", "Europe": "Europe",
        "Oceania": "Oceania", "Antarctic": "Antarctica",
    }
    sub_map = {
        "South America": "South America", "Caribbean": "North America",
        "Central America": "North America", "Northern America": "North America",
    }
    costs = {"Africa": 55, "Asia": 60, "Europe": 110, "North America": 140,
             "South America": 70, "Oceania": 120, "Antarctica": 200}
    tags_map = {
        "Africa": ["nature", "adventure", "culture"],
        "Asia": ["culture", "food", "city"],
        "Europe": ["culture", "history", "food"],
        "North America": ["city", "culture", "food"],
        "South America": ["nature", "adventure", "culture"],
        "Oceania": ["nature", "beach", "adventure"],
    }

    out = []
    nid = 1000
    for c in countries:
        caps = c.get("capital") or []
        if not caps:
            continue
        region = c.get("region", "")
        sub = c.get("subregion", "")
        continent = sub_map.get(sub) or region_map.get(region, region or "Unknown")
        if region == "Americas" and continent == "North America" and sub == "South America":
            continent = "South America"
        out.append({
            "id": nid,
            "name": caps[0],
            "country": c.get("name", {}).get("common", ""),
            "continent": continent,
            "description": f"{caps[0]} is the capital of {c.get('name', {}).get('common', '')}.",
            "tags": list(tags_map.get(continent, ["culture"])),
            "avg_cost_per_day": costs.get(continent, 80),
            "image": (c.get("flags") or {}).get("png", ""),
            "source": "restcountries",
        })
        nid += 1
    return out


def get_all_destinations(source: str = "all") -> list:
    global _cache
    seed = _load_seed()
    if source == "local":
        return seed

    if _cache is None:
        tourist = []
        for i, d in enumerate(TOP_TOURIST_DESTINATIONS, start=2000):
            entry = dict(d)
            entry["id"] = i
            entry["source"] = "tourist_curated"
            tourist.append(entry)

        seen = {d["name"].lower() for d in seed}
        merged = list(seed)
        for d in tourist:
            if d["name"].lower() not in seen:
                merged.append(d)
                seen.add(d["name"].lower())
        for d in _fetch_restcountries():
            if d["name"].lower() not in seen:
                merged.append(d)
                seen.add(d["name"].lower())
        _cache = merged

    return _cache


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "destinations"}), 200


@app.get("/destinations")
def search():
    q = request.args.get("q", "").strip().lower()
    tag = request.args.get("tag", "").strip().lower()
    continent = request.args.get("continent", "").strip().lower()
    source = request.args.get("source", "all").strip().lower()
    max_cost_str = request.args.get("max_cost", "").strip()

    max_cost = None
    if max_cost_str:
        try:
            max_cost = int(max_cost_str)
        except ValueError:
            return jsonify({"error": "max_cost must be an integer"}), 400

    results = []
    for dest in get_all_destinations(source):
        if q:
            blob = f"{dest.get('name','')} {dest.get('country','')} {dest.get('description','')}".lower()
            if q not in blob:
                continue
        if tag and tag not in [t.lower() for t in dest.get("tags", [])]:
            continue
        if continent and continent != dest.get("continent", "").lower():
            continue
        if max_cost is not None:
            cost = dest.get("avg_cost_per_day")
            if cost is None or cost > max_cost:
                continue
        results.append(dest)

    return jsonify(results), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5002)), debug=True)
