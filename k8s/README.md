# GlobeTrotter – Phase 3: Kubernetes Deployment

This folder contains Kubernetes manifests for deploying the microservices stack.

## What you get

| Capability | How |
|------------|-----|
| **Containerization** | Docker images per service |
| **Load balancing** | Kubernetes Service (ClusterIP) + Ingress |
| **Auto-scaling** | HorizontalPodAutoscaler (CPU 70%, min 2 / max 5–6) |
| **Health checks** | readinessProbe + livenessProbe on `/health` |
| **Config** | ConfigMap + Secrets |
| **Persistence** | PVC for auth-db and itineraries-db |

## Prerequisites

- Docker
- kubectl
- A local cluster: **Minikube**, **Kind**, or **Docker Desktop Kubernetes**
- Ingress controller (nginx), e.g. on Minikube:

```bash
minikube addons enable ingress
```

## 1. Build images

From the **repo root**:

```bash
# Build all service images
docker build -f services/auth/Dockerfile -t globetrotter/auth:latest .
docker build -f services/destinations/Dockerfile -t globetrotter/destinations:latest .
docker build -f services/recommendations/Dockerfile -t globetrotter/recommendations:latest .
docker build -f services/itineraries/Dockerfile -t globetrotter/itineraries:latest .
docker build -f services/gateway/Dockerfile -t globetrotter/gateway:latest .
```

### Minikube tip

Use Minikube’s Docker daemon so the cluster can see the images:

```bash
eval $(minikube docker-env)
# then run the docker build commands above
```

### Kind tip

```bash
kind load docker-image globetrotter/auth:latest
kind load docker-image globetrotter/destinations:latest
kind load docker-image globetrotter/recommendations:latest
kind load docker-image globetrotter/itineraries:latest
kind load docker-image globetrotter/gateway:latest
```

## 2. Deploy

```bash
kubectl apply -k k8s/
```

Or apply files individually:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/
```

## 3. Check status

```bash
kubectl get pods -n globetrotter
kubectl get svc -n globetrotter
kubectl get hpa -n globetrotter
kubectl get ingress -n globetrotter
```

## 4. Access the app

### Option A – Port-forward (simplest)

```bash
kubectl port-forward -n globetrotter svc/gateway 5000:80
# → http://localhost:5000
```

### Option B – Ingress (Minikube)

```bash
# Add host entry
echo "$(minikube ip) globetrotter.local" | sudo tee -a /etc/hosts

# Open
open http://globetrotter.local
```

## 5. Tear down

```bash
kubectl delete -k k8s/
```

## Notes for production

- Change `SECRET_KEY` and DB passwords (use real Secrets / sealed-secrets).
- Push images to a registry (GHCR, ECR, GCR) and update image names.
- Use managed Postgres (RDS, Cloud SQL) instead of in-cluster DBs for production.
- Enable metrics-server for HPA to work (`minikube addons enable metrics-server`).
