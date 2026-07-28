# GlobeTrotter – Travel Assistant

GlobeTrotter is a distributed travel recommendation application built as a semester-long capstone project.

Students start with a **monolith** (Phase 1), refactor into **microservices** (Phase 2), deploy to the **cloud** (Phase 3), and add **resilience** patterns (Phase 4).

**Current status: Phase 2 – Microservices**

---

## Features

- Search travel destinations (seed data + world capitals + curated tourist cities)
- Personalized recommendations based on user preferences
- Create and manage travel itineraries
- JWT authentication (register / login / preferences)
- Modern Tailwind CSS frontend
- Strong coverage of **Cameroon** and African tourist sites
- PostgreSQL for users and itineraries
- **Microservices** with API gateway and inter-service HTTP calls
- Retries, timeouts, and health checks between services
- Automated API tests (monolith)

---

## Architecture

### Phase 1 – Monolith

Single Flask app + PostgreSQL (`docker-compose.yml`).

### Phase 2 – Microservices

```
                    ┌─────────────┐
                    │   Gateway   │  :5000  (public entry + frontend)
                    └──────┬──────┘
           ┌───────────────┼───────────────────┐
           │               │                   │
    ┌──────▼─────┐  ┌──────▼──────┐  ┌─────────▼────────┐  ┌──────▼───────┐
    │    Auth    │  │ Destinations│  │ Recommendations  │  │ Itineraries  │
    │   :5001    │  │   :5002     │  │     :5003        │  │   :5004      │
    └──────┬─────┘  └─────────────┘  └────────┬─────────┘  └──────┬───────┘
           │                                  │                    │
           │         calls auth + destinations│                    │
           └─────────────────┬────────────────┴────────────────────┘
                             │
                      ┌──────▼──────┐
                      │  PostgreSQL │
                      └─────────────┘
```

| Service | Port | Responsibility |
|---------|------|----------------|
| **gateway** | 5000 | Frontend + API proxy |
| **auth** | 5001 | Register, login, JWT, preferences |
| **destinations** | 5002 | Search catalogue |
| **recommendations** | 5003 | Personalized picks (calls auth + destinations) |
| **itineraries** | 5004 | Create / list trips |
| **db** | 5432 | PostgreSQL |

Inter-service calls use a shared HTTP client with **timeouts**, **retries**, and **clear error responses**.

---

## Project Structure

```
.
├── app/                         # Phase 1 monolith
│   ├── __init__.py
│   ├── models.py
│   ├── auth.py
│   ├── destinations.py
│   ├── recommendations.py
│   ├── itineraries.py
│   ├── routes.py
│   ├── external_api.py
│   ├── tourist_destinations.py
│   ├── main.py
│   └── templates/
├── services/                    # Phase 2 microservices
│   ├── shared/
│   │   ├── requirements.txt
│   │   └── http_client.py       # Retries, timeouts, ServiceError
│   ├── auth/
│   ├── destinations/
│   ├── recommendations/
│   ├── itineraries/
│   └── gateway/
├── data/
│   └── destinations.json
├── tests/                       # Monolith API tests
├── Dockerfile                   # Monolith image
├── docker-compose.yml           # Phase 1: monolith + Postgres
├── docker-compose.microservices.yml  # Phase 2: full service stack
├── requirements.txt
└── README.md
```

---

## REST API

Same public API in both Phase 1 and Phase 2 (via gateway):

| Method | Endpoint           | Auth | Description |
|--------|--------------------|------|-------------|
| POST   | `/register`        | No   | Register a new user |
| POST   | `/login`           | No   | Authenticate and receive a JWT |
| GET    | `/me`              | Yes  | Current user profile + preferences |
| PUT    | `/preferences`     | Yes  | Update travel preferences |
| GET    | `/destinations`    | No   | Search (`q`, `tag`, `continent`, `max_cost`, `source`) |
| GET    | `/recommendations` | Yes  | Personalised recommendations |
| POST   | `/itineraries`     | Yes  | Create a new itinerary |
| GET    | `/itineraries`     | Yes  | List itineraries for the logged-in user |
| GET    | `/health`          | No   | Gateway + upstream health |

Protected routes expect: `Authorization: Bearer <token>`

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

# Search Cameroon places
curl "http://localhost:5000/destinations?q=cameroon"

# Recommendations
curl http://localhost:5000/recommendations \
  -H "Authorization: Bearer $TOKEN"

# Health (shows each upstream service)
curl http://localhost:5000/health
```

### Frontend pages

| URL | Page |
|-----|------|
| `/` | Home |
| `/destinations` | Browse & filter |
| `/destinations/<id>` | Detail |
| `/recommendations` | Personalized picks |
| `/itineraries` | My trips |

---

## Running Phase 1 (Monolith)

```bash
docker-compose up --build
# → http://localhost:5000
```

---

## Running Phase 2 (Microservices)

```bash
docker-compose -f docker-compose.microservices.yml up --build
# → http://localhost:5000  (gateway)
```

Stop:

```bash
docker-compose -f docker-compose.microservices.yml down
```

---

## Running tests (monolith)

```bash
docker-compose exec globetrotter pytest tests/ -v

# Or locally
pip install -r requirements.txt
pytest tests/ -v
```

---

## Data storage

| Data | Storage |
|------|---------|
| Users | PostgreSQL |
| Itineraries | PostgreSQL |
| Destinations (seed) | `data/destinations.json` |
| Destinations (runtime) | REST Countries API + curated tourist list |

---

## Configuration

| Variable | Used by | Description |
|----------|---------|-------------|
| `SECRET_KEY` | auth, recommendations, itineraries, gateway | JWT signing key |
| `DATABASE_URL` | auth, itineraries | PostgreSQL connection |
| `AUTH_SERVICE_URL` | recommendations, gateway | Auth base URL |
| `DESTINATIONS_SERVICE_URL` | recommendations, gateway | Destinations base URL |
| `RECOMMENDATIONS_SERVICE_URL` | gateway | Recommendations base URL |
| `ITINERARIES_SERVICE_URL` | gateway | Itineraries base URL |
| `PROXY_TIMEOUT` | gateway | Upstream timeout (default 12s) |
| `PROXY_RETRIES` | gateway | Proxy retries (default 1) |

---

## Capstone phases

| Phase | Goal | Status |
|-------|------|--------|
| **1. Monolith** | Working REST API, Docker, PostgreSQL, frontend, tests | ✅ Done |
| **2. Microservices** | Service decomposition, gateway, inter-service calls | ✅ In progress |
| **3. Cloud Deployment** | Kubernetes, load balancing, auto-scaling | ⏳ Planned |
| **4. Resilience** | Caching, queues, circuit breakers, fault tolerance | ⏳ Planned |

---

## License

See [LICENSE](LICENSE).
