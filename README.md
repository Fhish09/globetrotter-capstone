# GlobeTrotter – Travel Assistant

Distributed travel recommendation application for a semester capstone.

**Current status: All four phases complete ✅**

| Phase | Goal | Status |
|-------|------|--------|
| **1. Monolith** | REST API, Docker, PostgreSQL, frontend, tests | ✅ |
| **2. Microservices** | Decomposition, gateway, inter-service calls, separate DBs | ✅ |
| **3. Cloud Deployment** | Kubernetes, load balancing, auto-scaling | ✅ |
| **4. Resilience** | Caching, circuit breakers, retries, fault tolerance | ✅ |

---

## Phase 4 – Resilience patterns

| Pattern | Implementation |
|---------|----------------|
| **Caching** | Redis for destinations search + recommendations |
| **Circuit breaker** | Per-upstream breaker in recommendations service |
| **Retries + backoff** | Shared HTTP client (`services/shared/http_client.py`) |
| **Timeouts** | Configurable on every inter-service call |
| **Graceful degradation** | App works if Redis is down; clear 503s if upstreams fail |
| **Health + breaker status** | `GET /health` on recommendations shows circuit state |

Circuit breaker states: `closed` → `open` (after 5 failures) → `half_open` (after 20s recovery).

---

## Quick start

### Phase 1 – Monolith

```bash
docker-compose up --build
```

### Phase 2–4 – Microservices + Redis

```bash
docker-compose -f docker-compose.microservices.yml up --build
# → http://localhost:5000
curl http://localhost:5000/health
```

### Phase 3 – Kubernetes

See [k8s/README.md](k8s/README.md).

```bash
kubectl apply -k k8s/
kubectl port-forward -n globetrotter svc/gateway 5000:80
```

---

## Architecture

```
Gateway → Auth | Destinations | Recommendations | Itineraries
                      │                │
                   Redis cache    circuit breakers
                                   + Redis cache
```

- **auth-db** / **itineraries-db**: separate PostgreSQL instances  
- **redis**: shared cache (optional; services degrade if missing)

---

## Project layout

```
app/                 # Phase 1 monolith
services/            # Phase 2–4 microservices
  shared/            # http_client, circuit_breaker, cache
  auth|destinations|recommendations|itineraries|gateway/
k8s/                 # Phase 3 Kubernetes manifests
docker-compose.yml
docker-compose.microservices.yml
tests/
```

---

## REST API

| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/register`, `/login` | No |
| GET | `/me` | Yes |
| PUT | `/preferences` | Yes |
| GET | `/destinations` | No |
| GET | `/recommendations` | Yes |
| GET/POST | `/itineraries` | Yes |
| GET | `/health` | No |

---

## License

See [LICENSE](LICENSE).
