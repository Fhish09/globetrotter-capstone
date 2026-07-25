"""
Curated list of the world's most popular tourist destinations.

These are merged with seed data and REST Countries capitals so recommendations
and search surface famous travel cities (not only political capitals).
"""

TOP_TOURIST_DESTINATIONS = [
    # Europe
    {"name": "Rome", "country": "Italy", "continent": "Europe",
     "description": "The Eternal City – Colosseum, Vatican, ancient ruins and incredible Italian food.",
     "tags": ["history", "culture", "food", "romance"], "avg_cost_per_day": 100,
     "image": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800&h=600&fit=crop"},
    {"name": "London", "country": "United Kingdom", "continent": "Europe",
     "description": "Iconic landmarks, world-class museums, royal history and vibrant neighbourhoods.",
     "tags": ["city", "culture", "history", "shopping"], "avg_cost_per_day": 150,
     "image": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800&h=600&fit=crop"},
    {"name": "Amsterdam", "country": "Netherlands", "continent": "Europe",
     "description": "Canals, bikes, museums and a uniquely relaxed European vibe.",
     "tags": ["culture", "city", "history", "nature"], "avg_cost_per_day": 130,
     "image": "https://images.unsplash.com/photo-1534351590666-13e3e96b5017?w=800&h=600&fit=crop"},
    {"name": "Prague", "country": "Czechia", "continent": "Europe",
     "description": "Fairytale architecture, historic old town and affordable Central European charm.",
     "tags": ["history", "culture", "romance", "budget"], "avg_cost_per_day": 70,
     "image": "https://images.unsplash.com/photo-1541849546-216549ae216d?w=800&h=600&fit=crop"},
    {"name": "Istanbul", "country": "Turkey", "continent": "Europe",
     "description": "Where East meets West – bazaars, mosques, Bosphorus views and rich cuisine.",
     "tags": ["culture", "history", "food", "city"], "avg_cost_per_day": 65,
     "image": "https://images.unsplash.com/photo-1524231757912-21f4fe64ae86?w=800&h=600&fit=crop"},
    {"name": "Lisbon", "country": "Portugal", "continent": "Europe",
     "description": "Sunny hills, tiled streets, pastel de nata and Atlantic coast vibes.",
     "tags": ["culture", "food", "beach", "budget"], "avg_cost_per_day": 75,
     "image": "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?w=800&h=600&fit=crop"},
    {"name": "Venice", "country": "Italy", "continent": "Europe",
     "description": "Romantic canals, gondolas and timeless Italian architecture.",
     "tags": ["romance", "culture", "history", "unique"], "avg_cost_per_day": 140,
     "image": "https://images.unsplash.com/photo-1523906834658-6e24ef2386f9?w=800&h=600&fit=crop"},
    {"name": "Florence", "country": "Italy", "continent": "Europe",
     "description": "Renaissance art capital – Uffizi, Duomo and Tuscan beauty.",
     "tags": ["culture", "history", "art", "food"], "avg_cost_per_day": 110,
     "image": "https://images.unsplash.com/photo-1543429258-0b43dbe83e0f?w=800&h=600&fit=crop"},
    {"name": "Vienna", "country": "Austria", "continent": "Europe",
     "description": "Imperial palaces, classical music and elegant café culture.",
     "tags": ["culture", "history", "food", "city"], "avg_cost_per_day": 115,
     "image": "https://images.unsplash.com/photo-1516550893923-42d28cc56732?w=800&h=600&fit=crop"},
    {"name": "Budapest", "country": "Hungary", "continent": "Europe",
     "description": "Thermal baths, ruin bars and stunning Danube views.",
     "tags": ["culture", "history", "budget", "unique"], "avg_cost_per_day": 60,
     "image": "https://images.unsplash.com/photo-1541343672885-9be56236302a?w=800&h=600&fit=crop"},

    # Asia
    {"name": "Seoul", "country": "South Korea", "continent": "Asia",
     "description": "K-culture capital – tech, street food, palaces and nightlife.",
     "tags": ["city", "food", "culture", "technology"], "avg_cost_per_day": 85,
     "image": "https://images.unsplash.com/photo-1517154421851-d9d5c2e2c0e8?w=800&h=600&fit=crop"},
    {"name": "Singapore", "country": "Singapore", "continent": "Asia",
     "description": "Futuristic city-state with amazing food, gardens and clean streets.",
     "tags": ["city", "food", "luxury", "culture"], "avg_cost_per_day": 130,
     "image": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=800&h=600&fit=crop"},
    {"name": "Hong Kong", "country": "China", "continent": "Asia",
     "description": "Skyline views, street markets and a unique East-meets-West energy.",
     "tags": ["city", "food", "shopping", "culture"], "avg_cost_per_day": 120,
     "image": "https://images.unsplash.com/photo-1536599018102-9f803c140fc1?w=800&h=600&fit=crop"},
    {"name": "Kyoto", "country": "Japan", "continent": "Asia",
     "description": "Temples, geishas, cherry blossoms and traditional Japanese beauty.",
     "tags": ["culture", "history", "nature", "romance"], "avg_cost_per_day": 100,
     "image": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=800&h=600&fit=crop"},
    {"name": "Phuket", "country": "Thailand", "continent": "Asia",
     "description": "Tropical beaches, clear waters and lively island nightlife.",
     "tags": ["beach", "nature", "food", "budget"], "avg_cost_per_day": 50,
     "image": "https://images.unsplash.com/photo-1589394815804-964ed0be2eb5?w=800&h=600&fit=crop"},
    {"name": "Maldives", "country": "Maldives", "continent": "Asia",
     "description": "Overwater villas, turquoise lagoons and ultimate tropical luxury.",
     "tags": ["beach", "luxury", "romance", "nature"], "avg_cost_per_day": 250,
     "image": "https://images.unsplash.com/photo-1514282401047-d79a71a590e8?w=800&h=600&fit=crop"},
    {"name": "Hanoi", "country": "Vietnam", "continent": "Asia",
     "description": "Old Quarter charm, street food heaven and rich history.",
     "tags": ["food", "culture", "budget", "history"], "avg_cost_per_day": 35,
     "image": "https://images.unsplash.com/photo-1559592413-7eaaaef917c5?w=800&h=600&fit=crop"},
    {"name": "Marrakech", "country": "Morocco", "continent": "Africa",
     "description": "Souks, riads, spices and the magic of the medina.",
     "tags": ["culture", "food", "adventure", "unique"], "avg_cost_per_day": 50,
     "image": "https://images.unsplash.com/photo-1597212618440-806262de4f6b?w=800&h=600&fit=crop"},

    # Americas
    {"name": "Rio de Janeiro", "country": "Brazil", "continent": "South America",
     "description": "Christ the Redeemer, Copacabana beach and carnival energy.",
     "tags": ["beach", "nature", "culture", "adventure"], "avg_cost_per_day": 70,
     "image": "https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=800&h=600&fit=crop"},
    {"name": "Cancun", "country": "Mexico", "continent": "North America",
     "description": "Caribbean beaches, resorts and gateway to Mayan ruins.",
     "tags": ["beach", "luxury", "adventure", "food"], "avg_cost_per_day": 90,
     "image": "https://images.unsplash.com/photo-1510097467424-192d713c1c62?w=800&h=600&fit=crop"},
    {"name": "Los Angeles", "country": "USA", "continent": "North America",
     "description": "Hollywood, beaches, entertainment and endless sunshine.",
     "tags": ["city", "beach", "culture", "shopping"], "avg_cost_per_day": 160,
     "image": "https://images.unsplash.com/photo-1534190760961-74e8c1c5fd10?w=800&h=600&fit=crop"},
    {"name": "Las Vegas", "country": "USA", "continent": "North America",
     "description": "Entertainment capital – shows, casinos and desert spectacle.",
     "tags": ["city", "luxury", "unique", "shopping"], "avg_cost_per_day": 140,
     "image": "https://images.unsplash.com/photo-1605833556294-ea5c7a74f57d?w=800&h=600&fit=crop"},
    {"name": "Cusco", "country": "Peru", "continent": "South America",
     "description": "Gateway to Machu Picchu and heart of the Inca empire.",
     "tags": ["history", "adventure", "culture", "nature"], "avg_cost_per_day": 55,
     "image": "https://images.unsplash.com/photo-1526392060635-9d6019884377?w=800&h=600&fit=crop"},
    {"name": "Buenos Aires", "country": "Argentina", "continent": "South America",
     "description": "Tango, steak, European-style avenues and late-night energy.",
     "tags": ["culture", "food", "city", "romance"], "avg_cost_per_day": 60,
     "image": "https://images.unsplash.com/photo-1589903308904-1010c2294adc?w=800&h=600&fit=crop"},

    # Africa & Middle East
    {"name": "Cairo", "country": "Egypt", "continent": "Africa",
     "description": "Pyramids of Giza, Nile views and thousands of years of history.",
     "tags": ["history", "culture", "adventure", "unique"], "avg_cost_per_day": 45,
     "image": "https://images.unsplash.com/photo-1572252009286-268acec5ca0a?w=800&h=600&fit=crop"},
    {"name": "Zanzibar", "country": "Tanzania", "continent": "Africa",
     "description": "Spice island beaches, Stone Town and Indian Ocean paradise.",
     "tags": ["beach", "culture", "nature", "romance"], "avg_cost_per_day": 70,
     "image": "https://images.unsplash.com/photo-1586861635166-cbfc8a8e0c0d?w=800&h=600&fit=crop"},
    {"name": "Petra", "country": "Jordan", "continent": "Asia",
     "description": "The Rose City – ancient rock-cut architecture and desert wonder.",
     "tags": ["history", "adventure", "unique", "culture"], "avg_cost_per_day": 80,
     "image": "https://images.unsplash.com/photo-1579606032821-4e6161c815ab?w=800&h=600&fit=crop"},

    # Oceania
    {"name": "Sydney", "country": "Australia", "continent": "Oceania",
     "description": "Opera House, Harbour Bridge, beaches and outdoor lifestyle.",
     "tags": ["city", "beach", "nature", "culture"], "avg_cost_per_day": 140,
     "image": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=800&h=600&fit=crop"},
    {"name": "Auckland", "country": "New Zealand", "continent": "Oceania",
     "description": "Harbour city with volcanoes, islands and adventure nearby.",
     "tags": ["nature", "adventure", "city", "outdoor"], "avg_cost_per_day": 110,
     "image": "https://images.unsplash.com/photo-1507699622108-4be3abd695ad?w=800&h=600&fit=crop"},
]


def get_tourist_destinations() -> list:
    """Return top tourist destinations with sequential IDs starting at 2000."""
    results = []
    for i, dest in enumerate(TOP_TOURIST_DESTINATIONS, start=2000):
        entry = dict(dest)
        entry["id"] = i
        entry["source"] = "tourist_curated"
        results.append(entry)
    return results
