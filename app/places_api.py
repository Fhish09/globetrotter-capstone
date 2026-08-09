"""Free live places for Douala via OpenStreetMap Overpass (no API key)."""
from __future__ import annotations

import json
import os
import time
from typing import Any

import requests

# Douala approximate centre & search radius (metres)
DOUALA_LAT = 4.0511
DOUALA_LNG = 9.7679
RADIUS_M = 14000

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = os.path.join(_BASE_DIR, "data", "live_places_cache.json")
CACHE_TTL_SEC = 6 * 60 * 60  # 6 hours


def _overpass_query() -> str:
    # Tourism + historic + museums + viewpoints around Douala only
    return f"""
    [out:json][timeout:30];
    (
      node["tourism"](around:{RADIUS_M},{DOUALA_LAT},{DOUALA_LNG});
      way["tourism"](around:{RADIUS_M},{DOUALA_LAT},{DOUALA_LNG});
      node["historic"](around:{RADIUS_M},{DOUALA_LAT},{DOUALA_LNG});
      node["tourism"="museum"](around:{RADIUS_M},{DOUALA_LAT},{DOUALA_LNG});
      node["amenity"="place_of_worship"]["name"](around:{RADIUS_M},{DOUALA_LAT},{DOUALA_LNG});
      node["leisure"="park"]["name"](around:{RADIUS_M},{DOUALA_LAT},{DOUALA_LNG});
      node["shop"="marketplace"]["name"](around:{RADIUS_M},{DOUALA_LAT},{DOUALA_LNG});
    );
    out center tags;
    """


def _element_coords(el: dict) -> tuple[float | None, float | None]:
    if "lat" in el and "lon" in el:
        return float(el["lat"]), float(el["lon"])
    c = el.get("center") or {}
    if "lat" in c and "lon" in c:
        return float(c["lat"]), float(c["lon"])
    return None, None


def _tags_to_tags_list(tags: dict) -> list[str]:
    out = []
    for key in ("tourism", "historic", "amenity", "leisure", "shop"):
        if tags.get(key):
            out.append(str(tags[key]).lower())
    if tags.get("religion"):
        out.append("religion")
    out.append("douala")
    out.append("live")
    # unique preserve order
    seen = set()
    clean = []
    for t in out:
        if t not in seen:
            seen.add(t)
            clean.append(t)
    return clean[:8]


def _guess_district(lat: float, lng: float) -> str:
    # rough districts by coords
    if lat < 4.03:
        return "Youpwe / South"
    if lng < 9.69:
        return "Bonanjo"
    if lat > 4.06 and lng > 9.70:
        return "Deido"
    if 9.69 <= lng <= 9.72 and 4.04 <= lat <= 4.06:
        return "Akwa"
    if lng > 9.72:
        return "Mboppi / East"
    return "Douala"


def _normalize_element(el: dict, idx: int) -> dict | None:
    tags = el.get("tags") or {}
    name = (tags.get("name") or tags.get("name:en") or tags.get("name:fr") or "").strip()
    if not name or len(name) < 2:
        return None
    lat, lng = _element_coords(el)
    if lat is None or lng is None:
        return None
    tourism = tags.get("tourism", "")
    desc_bits = [
        f"Live OpenStreetMap place in Douala ({tourism or tags.get('historic') or tags.get('amenity') or 'POI'}).",
        tags.get("description") or "",
    ]
    description = " ".join(b for b in desc_bits if b).strip()
    return {
        "id": 10000 + idx,  # avoid clash with curated 1–99
        "name": name,
        "country": "Cameroon",
        "city": "Douala",
        "district": _guess_district(lat, lng),
        "continent": "Africa",
        "lat": round(lat, 6),
        "lng": round(lng, 6),
        "description": description,
        "tags": _tags_to_tags_list(tags),
        "avg_cost_per_day": 2000,
        "currency": "FCFA",
        "cost_note": "Estimate — confirm locally",
        "image": "https://commons.wikimedia.org/wiki/Special:FilePath/Douala.JPG?width=900",
        "source": "openstreetmap",
        "osm_id": el.get("id"),
        "osm_type": el.get("type"),
        "tips": {
            "hours": tags.get("opening_hours") or "Check locally — hours vary.",
            "transport": "Taxi or moto within Douala; agree price before departure.",
            "timing": "Daytime visits recommended for first-time visitors.",
            "safety": "Standard city caution; keep valuables secure.",
        },
    }


def _read_cache() -> list | None:
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if time.time() - float(payload.get("ts", 0)) > CACHE_TTL_SEC:
            return None
        return payload.get("places") or []
    except Exception:
        return None


def _write_cache(places: list) -> None:
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as fh:
        json.dump({"ts": time.time(), "places": places}, fh, ensure_ascii=False, indent=2)


def fetch_douala_live_places(force: bool = False) -> list[dict[str, Any]]:
    """Return tourism-related POIs in Douala from OSM Overpass (cached)."""
    if not force:
        cached = _read_cache()
        if cached is not None:
            return cached

    query = _overpass_query()
    data = None
    last_err = None
    for url in OVERPASS_URLS:
        try:
            res = requests.post(
                url,
                data={"data": query},
                timeout=35,
                headers={"User-Agent": "GlobeTrotter-Capstone/1.0 (Douala tourism student project)"},
            )
            res.raise_for_status()
            data = res.json()
            break
        except Exception as exc:
            last_err = exc
            continue

    if data is None:
        # fail soft — empty live list
        return []

    places = []
    seen_names: set[str] = set()
    for i, el in enumerate(data.get("elements") or []):
        item = _normalize_element(el, i)
        if not item:
            continue
        key = item["name"].lower()
        if key in seen_names:
            continue
        seen_names.add(key)
        places.append(item)

    places.sort(key=lambda p: p["name"].lower())
    _write_cache(places)
    return places


def merge_curated_and_live(curated: list, live: list) -> list:
    """Curated first; live places whose names are not already in curated."""
    names = {(c.get("name") or "").lower() for c in curated}
    extra = []
    for p in live:
        n = (p.get("name") or "").lower()
        if not n or n in names:
            continue
        # skip very generic
        if n in ("douala", "cameroun", "cameroon"):
            continue
        extra.append(p)
        names.add(n)
    return list(curated) + extra
