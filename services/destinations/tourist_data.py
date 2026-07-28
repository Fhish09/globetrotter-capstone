"""Load curated tourist destinations for this service."""
try:
    from tourist_destinations import TOP_TOURIST_DESTINATIONS
except ImportError:
    TOP_TOURIST_DESTINATIONS = []
