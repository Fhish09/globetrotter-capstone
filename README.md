# GlobeTrotter – Travel Assistant

GlobeTrotter is a distributed travel recommendation application built as a semester-long capstone project.

Students start with a **monolith** (Phase 1), refactor into **microservices** (Phase 2), deploy to the **cloud** (Phase 3), and add **resilience** patterns (Phase 4).

**Current status: Phase 2 – Microservices ✅ Complete**

---

## Features

- Search travel destinations (seed data + world capitals + curated tourist cities)
- Personalized recommendations based on user preferences
- Create and manage travel itineraries
- JWT authentication (register / login / preferences)
- Modern Tailwind CSS frontend
- Strong coverage of **Cameroon** and African tourist sites
- **Microservices** with API gateway and inter-service HTTP calls
- **Separate databases** per stateful service (auth-db, itineraries-db)
- Retries, timeouts, and health checks between services
- Service-level tests + OpenAPI specs per service
- Monolith API tests with pytest

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
      ┌────▼────┐              calls auth + destinations      ┌────▼────┐
      │ auth-db │                                             │ itin-db │
      └─────────┘                                             └─────────┘
```

| Service | Port | Database | Responsibility |
|---------|------|----------|----------------|
| **gateway** | 5000 | — | Frontend + API proxy |
| **auth** | 5001 | **auth-db** | Register, login, JWT, preferences |
| **destinations** | 5002 | — (JSON + API) | Search catalogue |
| **recommendations** | 5003 | — | Personalized picks (calls auth + destinations) |
| **itineraries** | 5004 | **itineraries-db** | Create / list trips |

Inter-service calls use a shared HTTP client with **timeouts**, **retries**, and **clear error responses**.

---

## Project Structure

```
.
├── app/                              # Phase 1 monolith
├── services/                         # Phase 2 microservices
│   ├── shared/
│   │   ├── requirements.txt
│   │   └── http_client.py
│   ├── auth/
│   │   ├── app.py
│   │   ├── openapi.json
│   │   └── tests/
│   ├── destinations/
│   │   ├── app.py
│   │   ├── openapi.json
│   │   └── tests/
│   ├── recommendations/
│   │   ├── app.py
│   │   └── openapi.json
│   ├── itineraries/
│   │   ├── app.py
│   │   ├── openapi.json
│   │   └── tests/
│   └── gateway/
├── data/destinations.json
├── tests/                            # Monolith tests
├── docker-compose.yml                # Phase 1
├── docker-compose.microservices.yml  # Phase 2
└── README.md
```

---

## REST API

Same public API in both phases (Phase 2 via gateway):

| Method | Endpoint           | Auth | Description |
|--------|--------------------|------|-------------|
| POST   | `/register`        | No   | Register |
| POST   | `/login`           | No   | JWT login |
| GET    | `/me`              | Yes  | Profile + preferences |
| PUT    | `/preferences`     | Yes  | Update preferences |
| GET    | `/destinations`    | No   | Search destinations |
| GET    | `/recommendations` | Yes  | Personalized recommendations |
| POST   | `/itineraries`     | Yes  | Create itinerary |
| GET    | `/itineraries`     | Yes  | List itineraries |
| GET    | `/health`          | No   | Gateway + upstream health |

OpenAPI specs live under each service folder, e.g. `services/auth/openapi.json`.

Protected routes: `Authorization: Bearer <token>`

### Example requests

```bash
curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "s3cr3t", "preferences": ["beach", "food"]}'

curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "s3cr3t"}'

curl "http://localhost:5000/destinations?q=cameroon"

curl http://localhost:5000/recommendations -H "Authorization: Bearer $TOKEN"

curl http://localhost:5000/health
```

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

```bash
docker-compose -f docker-compose.microservices.yml down
```

---

## Running tests

**Monolith:**

```bash
pip install -r requirements.txt
pytest tests/ -v
```

**Microservices (examples):**

```bash
pip install -r services/shared/requirements.txt pytest PyJWT
pytest services/auth/tests/ -v
pytest services/destinations/tests/ -v
pytest services/itineraries/tests/ -v
```

---

## Data storage (Phase 2)

| Data | Storage |
|------|---------|
| Users | **auth-db** (PostgreSQL) |
| Itineraries | **itineraries-db** (PostgreSQL) |
| Destinations | JSON seed + REST Countries + curated list |

---

## Capstone phases

| Phase | Goal | Status |
|-------|------|--------|
| **1. Monolith** | REST API, Docker, PostgreSQL, frontend, tests | ✅ Done |
| **2. Microservices** | Decomposition, gateway, inter-service calls, separate DBs, OpenAPI | ✅ Done |
| **3. Cloud Deployment** | Kubernetes, load balancing, auto-scaling | ⏳ Next |
| **4. Resilience** | Caching, queues, circuit breakers, fault tolerance | ⏳ Planned |

---

## License

See [LICENSE](LICENSE).
