"""
app/external_api.py

Fetch additional travel destinations from the free REST Countries API
(https://restcountries.com) and normalise them into our destination schema.

No API key required. Results are cached in memory for the lifetime of the
process so we don't hit the external API on every request.
"""
from __future__ import annotations

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# In-memory cache so we only call the external API once per process lifetime
_cache: Optional[list] = None

# Capitals / popular cities we prefer when a country has multiple options
REGION_TO_CONTINENT = {
    "Africa": "Africa",
    "Americas": "North America",  # refined below using subregion
    "Asia": "Asia",
    "Europe": "Europe",
    "Oceania": "Oceania",
    "Antarctic": "Antarctica",
}

SUBREGION_OVERRIDES = {
    "South America": "South America",
    "Caribbean": "North America",
    "Central America": "North America",
    "Northern America": "North America",
}

# Rough daily-budget estimates by region (USD) – used only for API-sourced entries
REGION_COST = {
    "Africa": 55,
    "Asia": 60,
    "Europe": 110,
    "North America": 140,
    "South America": 70,
    "Oceania": 120,
    "Antarctica": 200,
}

# Default interest tags by region
REGION_TAGS = {
    "Africa": ["nature", "adventure", "culture"],
    "Asia": ["culture", "food", "city"],
    "Europe": ["culture", "history", "food"],
    "North America": ["city", "culture", "food"],
    "South America": ["nature", "adventure", "culture"],
    "Oceania": ["nature", "beach", "adventure"],
    "Antarctica": ["nature", "adventure", "unique"],
}


def _resolve_continent(region: str, subregion: str) -> str:
    if subregion in SUBREGION_OVERRIDES:
        return SUBREGION_OVERRIDES[subregion]
    return REGION_TO_CONTINENT.get(region, region or "Unknown")


def _fetch_from_restcountries() -> list:
    """Call REST Countries and return a list of normalised destination dicts."""
    url = (
        "https://restcountries.com/v3.1/all"
        "?fields=name,capital,region,subregion,flags,cca2,population"
    )
    try:
        resp = requests.get(url, timeout=12)
        resp.raise_for_status()
        countries = resp.json()
    except Exception as exc:
        logger.warning("REST Countries API unavailable: %s", exc)
        return []

    destinations = []
    next_id = 1000  # start high so we don't collide with seed ids 1-12

    for country in countries:
        capitals = country.get("capital") or []
        if not capitals:
            continue

        capital = capitals[0]
        country_name = country.get("name", {}).get("common", "")
        region = country.get("region", "")
        subregion = country.get("subregion", "")
        continent = _resolve_continent(region, subregion)
        flag = (country.get("flags") or {}).get("png") or ""
        population = country.get("population") or 0

        # Skip tiny / non-tourist entries
        if population < 100_000 and continent != "Oceania":
            continue

        cost = REGION_COST.get(continent, 80)
        tags = list(REGION_TAGS.get(continent, ["culture"]))

        # Light tag enrichment from name/region keywords
        lower = f"{capital} {country_name} {subregion}".lower()
        if any(w in lower for w in ("island", "beach", "coast", "caribbean")):
            if "beach" not in tags:
                tags.append("beach")
        if any(w in lower for w in ("mountain", "alpine", "himalaya")):
            if "nature" not in tags:
                tags.append("nature")

        destinations.append({
            "id": next_id,
            "name": capital,
            "country": country_name,
            "continent": continent,
            "description": (
                f"{capital} is the capital of {country_name}. "
                f"Located in {subregion or region}, it offers a mix of local culture and travel experiences."
            ),
            "tags": tags,
            "avg_cost_per_day": cost,
            "image": flag,  # country flag as a reliable free image
            "source": "restcountries",
        })
        next_id += 1

    # Prefer larger / more interesting destinations first
    destinations.sort(key=lambda d: d.get("country", ""))
    return destinations


def get_external_destinations() -> list:
    """Return cached external destinations (fetched once)."""
    global _cache
    if _cache is not None:
        return _cache

    _cache = _fetch_from_restcountries()
    logger.info("Loaded %d destinations from REST Countries API", len(_cache))
    return _cache


def get_combined_destinations(local: list) -> list:
    """Merge curated local destinations with external API results.

    Local (seed) entries always win on name conflict so our rich descriptions
    and photos are preferred.
    """
    local_names = {d.get("name", "").lower() for d in local}
    external = get_external_destinations()

    merged = list(local)
    for dest in external:
        if dest.get("name", "").lower() not in local_names:
            merged.append(dest)

    return merged
