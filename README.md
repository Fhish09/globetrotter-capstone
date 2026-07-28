# GlobeTrotter – Travel Assistant

GlobeTrotter is a distributed travel recommendation application built as a semester-long capstone project.

Students start with a **monolith** (Phase 1), refactor into **microservices** (Phase 2), deploy to the **cloud** (Phase 3), and add **resilience** patterns (Phase 4).

**Current status: Phase 3 – Cloud Deployment ✅**

---

## Features

- Search travel destinations (seed + tourist curated + REST Countries)
- Personalized recommendations based on user preferences
- Create and manage travel itineraries
- JWT authentication
- Tailwind CSS frontend
- Strong **Cameroon** / Africa coverage
- Microservices + API gateway
- Separate databases per stateful service
- **Kubernetes**: Deployments, Services, Ingress, HPA (auto-scaling)
- Health probes, ConfigMaps, Secrets, PVCs

---

## Capstone phases

| Phase | Goal | Status |
|-------|------|--------|
| **1. Monolith** | REST API, Docker, PostgreSQL, frontend, tests | ✅ Done |
| **2. Microservices** | Decomposition, gateway, inter-service calls, separate DBs | ✅ Done |
| **3. Cloud Deployment** | Kubernetes, load balancing, auto-scaling | ✅ Done |
| **4. Resilience** | Caching, queues, circuit breakers, fault tolerance | ⏳ Next |

---

## Architecture (Phase 2 + 3)

```
                 ┌──────────── Ingress ────────────┐
                 │     (load balancing / TLS)      │
                 └───────────────┬─────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Gateway (HPA 2–6)     │
                    └────────────┬────────────┘
           ┌─────────────────────┼─────────────────────┐
           │                     │                     │
    ┌──────▼─────┐      ┌────────▼────────┐    ┌───────▼──────┐
    │ Auth (HPA) │      │ Destinations    │    │ Itineraries  │
    │ + auth-db  │      │ Recommendations │    │ + itin-db    │
    └────────────┘      └─────────────────┘    └──────────────┘
```

---

## Project structure

```
.
├── app/                              # Phase 1 monolith
├── services/                         # Phase 2 microservices
├── k8s/                              # Phase 3 Kubernetes
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── auth-db.yaml / itineraries-db.yaml
│   ├── auth.yaml / destinations.yaml / ...
│   ├── gateway.yaml
│   ├── ingress.yaml
│   ├── kustomization.yaml
│   └── README.md                     # Detailed K8s guide
├── docker-compose.yml                # Phase 1
├── docker-compose.microservices.yml  # Phase 2
└── README.md
```

---

## Running locally

### Phase 1 – Monolith

```bash
docker-compose up --build
# http://localhost:5000
```

### Phase 2 – Microservices

```bash
docker-compose -f docker-compose.microservices.yml up --build
# http://localhost:5000
```

### Phase 3 – Kubernetes

Full instructions: **[k8s/README.md](k8s/README.md)**

```bash
# 1. Build images (use minikube docker-env if on Minikube)
docker build -f services/auth/Dockerfile -t globetrotter/auth:latest .
docker build -f services/destinations/Dockerfile -t globetrotter/destinations:latest .
docker build -f services/recommendations/Dockerfile -t globetrotter/recommendations:latest .
docker build -f services/itineraries/Dockerfile -t globetrotter/itineraries:latest .
docker build -f services/gateway/Dockerfile -t globetrotter/gateway:latest .

# 2. Deploy
kubectl apply -k k8s/

# 3. Access
kubectl port-forward -n globetrotter svc/gateway 5000:80
# → http://localhost:5000
```

**Phase 3 capabilities:**

| Capability | Implementation |
|------------|----------------|
| Load balancing | Service + Ingress |
| Auto-scaling | HPA (CPU 70%, min 2 replicas) |
| Health checks | readiness + liveness probes |
| Config | ConfigMap + Secrets |
| Persistence | PVC for databases |

---

## REST API

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | No | Register |
| POST | `/login` | No | JWT login |
| GET | `/me` | Yes | Profile |
| PUT | `/preferences` | Yes | Update preferences |
| GET | `/destinations` | No | Search |
| GET | `/recommendations` | Yes | Personalized |
| POST/GET | `/itineraries` | Yes | Trips |
| GET | `/health` | No | Health |

---

## Tests

```bash
# Monolith
pytest tests/ -v

# Services
pytest services/auth/tests/ -v
pytest services/destinations/tests/ -v
pytest services/itineraries/tests/ -v
```

---

## License

See [LICENSE](LICENSE).
