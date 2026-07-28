# GlobeTrotter – Travel Assistant

GlobeTrotter is a **monolithic Flask application** that serves as the starting point for a semester-long capstone project.

Students build the monolith first (Phase 1), then refactor it into microservices (Phase 2), deploy to the cloud (Phase 3), and add resilience patterns (Phase 4) using Docker, Kubernetes, and cloud-native tooling.

**Current status: Phase 1 – Monolith (complete foundation)**

---

## Features

- Search travel destinations (seed data + world capitals + curated tourist cities)
- Personalized recommendations based on user preferences
- Create and manage travel itineraries
- JWT authentication (register / login)
- Edit travel preferences after signup
- Modern Tailwind CSS frontend (Home, Destinations, Detail, Recommendations, My Trips)
- Strong coverage of **Cameroon** and African tourist sites
- PostgreSQL for users and itineraries
- Docker Compose (app + database)
- Automated API tests with pytest

---

## Project Structure

```
.
├── app/
│   ├── __init__.py              # Flask app factory + DB init
│   ├── models.py                # SQLAlchemy models (User, Itinerary) + destination JSON helpers
│   ├── auth.py                  # Registration, login, JWT, /me, /preferences
│   ├── destinations.py          # Destination search endpoint
│   ├── recommendations.py       # Personalised recommendations
│   ├── itineraries.py           # Create / list itineraries
│   ├── routes.py                # Frontend page routes
│   ├── external_api.py          # REST Countries API integration
│   ├── tourist_destinations.py  # Curated tourist cities (incl. Cameroon)
│   ├── main.py                  # App entry point
│   └── templates/               # Tailwind frontend
│       ├── base.html
│       ├── index.html
│       ├── destinations.html
│       ├── destination_detail.html
│       ├── recommendations.html
│       └── itineraries.html
├── data/
│   └── destinations.json        # Static seed catalogue
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_destinations.py
│   ├── test_itineraries.py
│   └── test_recommendations.py
├── Dockerfile
├── docker-compose.yml           # App + PostgreSQL
├── requirements.txt
└── README.md
```

---

## REST API

| Method | Endpoint           | Auth | Description                                      |
|--------|--------------------|------|--------------------------------------------------|
| POST   | `/register`        | No   | Register a new user                              |
| POST   | `/login`           | No   | Authenticate and receive a JWT                   |
| GET    | `/me`              | Yes  | Current user profile + preferences               |
| PUT    | `/preferences`     | Yes  | Update travel preferences                        |
| GET    | `/destinations`    | No   | Search destinations (`q`, `tag`, `continent`, `max_cost`, `source`) |
| GET    | `/recommendations` | Yes  | Personalised recommendations                     |
| POST   | `/itineraries`     | Yes  | Create a new itinerary                           |
| GET    | `/itineraries`     | Yes  | List itineraries for the logged-in user          |

Protected routes expect:

```
Authorization: Bearer <token>
```

### Example requests

```bash
# Register
curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "s3cr3t", "preferences": ["beach", "food"]}'

# Login
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "s3cr3t"}'
# TOKEN=<value from .token field>

# Search destinations (local seed only)
curl "http://localhost:5000/destinations?source=local&tag=beach"

# Search Cameroon places
curl "http://localhost:5000/destinations?q=cameroon"

# Recommendations
curl http://localhost:5000/recommendations \
  -H "Authorization: Bearer $TOKEN"

# Create itinerary
curl -X POST http://localhost:5000/itineraries \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title": "Cameroon Coast", "destinations": ["Kribi", "Limbe"], "start_date": "2026-08-01", "end_date": "2026-08-10"}'

# List itineraries
curl http://localhost:5000/itineraries \
  -H "Authorization: Bearer $TOKEN"
```

### Frontend pages

| URL | Page |
|-----|------|
| `/` | Home |
| `/destinations` | Browse & filter destinations |
| `/destinations/<id>` | Destination detail |
| `/recommendations` | Personalized picks |
| `/itineraries` | My trips |

---

## Running with Docker (recommended)

### Prerequisites
- Docker & Docker Compose

```bash
# Build and start app + PostgreSQL
docker-compose up --build

# App:  http://localhost:5000
# DB:   localhost:5432 (user/pass/db: globetrotter)

# Stop
docker-compose down

# Stop and remove DB volume
docker-compose down -v
```

---

## Running tests

```bash
# Inside the running app container
docker-compose exec globetrotter pytest tests/ -v

# Or locally (uses in-memory SQLite automatically)
pip install -r requirements.txt
pytest tests/ -v
```

---

## Data storage

| Data | Storage |
|------|---------|
| Users | **PostgreSQL** (`users` table) |
| Itineraries | **PostgreSQL** (`itineraries` table) |
| Destinations (seed) | `data/destinations.json` |
| Destinations (runtime) | REST Countries API + curated tourist list (in memory) |

---

## Configuration

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `SECRET_KEY` | `globetrotter-secret-change-in-prod` | JWT signing key – **override in production** |
| `DATABASE_URL` | (set in docker-compose) | PostgreSQL connection string |
| `FLASK_DEBUG` | `0` | Set to `1` for development |
| `PORT` | `5000` | App port |

Generate a strong secret:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Capstone phases

| Phase | Goal | Status |
|-------|------|--------|
| **1. Monolith** | Working REST API, Docker, solid foundation | ✅ In progress / foundation complete |
| **2. Microservices** | Service decomposition, inter-service communication | ⏳ Next |
| **3. Cloud Deployment** | Containers, load balancing, auto-scaling | ⏳ Planned |
| **4. Resilience** | Caching, queues, circuit breakers, fault tolerance | ⏳ Planned |

---

## License

See [LICENSE](LICENSE).
