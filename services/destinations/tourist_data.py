"""Curated tourist destinations for the destinations microservice."""
from pathlib import Path
import sys

# Re-use the monolith list if available when running from repo root;
# otherwise this file can be extended independently.
try:
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "app"))
    from tourist_destinations import TOP_TOURIST_DESTINATIONS  # type: ignore
except Exception:
    TOP_TOURIST_DESTINATIONS = [
        {"name": "Kribi", "country": "Cameroon", "continent": "Africa",
         "description": "Cameroon's top beach destination.",
         "tags": ["beach", "nature", "food"], "avg_cost_per_day": 45,
         "image": "https://images.unsplash.com/photo-1519046904884-53103b34b206?w=800&h=600&fit=crop"},
        {"name": "Limbe", "country": "Cameroon", "continent": "Africa",
         "description": "Black-sand beaches near Mount Cameroon.",
         "tags": ["beach", "nature", "adventure"], "avg_cost_per_day": 40,
         "image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&h=600&fit=crop"},
        {"name": "Paris", "country": "France", "continent": "Europe",
         "description": "City of Light.",
         "tags": ["culture", "food", "romance"], "avg_cost_per_day": 120,
         "image": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&h=600&fit=crop"},
    ]
