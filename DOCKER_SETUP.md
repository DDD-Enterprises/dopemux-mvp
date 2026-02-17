---
id: DOCKER_SETUP
title: Docker Setup
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-17'
last_review: '2026-02-17'
next_review: '2026-05-18'
prelude: Docker Setup (explanation) for dopemux documentation and developer workflows.
---
# Docker Setup for Dopemux

This directory contains optimized Dockerfiles and docker-compose configurations for containerizing Dopemux.

## Files

- **Dockerfile** — Multi-stage Python backend (optimized for production)
- **Dockerfile.frontend** — Multi-stage Next.js frontend (minimal runtime image)
- **docker-compose.dev.yml** — Development environment with hot reload
- **docker-compose.prod.yml** — Production environment with security hardening
- **.dockerignore** — Excludes unnecessary files from build context
- **.env.example** — Configuration template (copy to .env)

## Quick Start (Development)

### 1. Setup environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 2. Build images
```bash
docker buildx build -f Dockerfile -t dopemux-backend:latest --load .
docker buildx build -f Dockerfile.frontend -t dopemux-frontend:latest --load .
```

### 3. Start services
```bash
docker compose -f docker-compose.dev.yml up -d --pull always
```

### 4. View logs
```bash
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f frontend
```

### 5. Stop services
```bash
docker compose -f docker-compose.dev.yml down
```

## Development Workflow

### Hot Reload for Backend (Python)
The dev compose mounts source code with live reload:
```bash
docker compose -f docker-compose.dev.yml logs -f backend
# Edit src/ or config/ — changes auto-reload
```

### Hot Reload for Frontend (Next.js)
The dev compose mounts Next.js source:
```bash
docker compose -f docker-compose.dev.yml logs -f frontend
# Edit pages/, components/, or styles/ — fast refresh enabled
```

### Database Access
- **PostgreSQL**: `localhost:5432`
  - User: `dopemux_age`
  - Password: from `.env` (AGE_PASSWORD)
  - Database: `dopemux_knowledge_graph`

- **Redis**: `localhost:6379`
  - Password: from `.env` (REDIS_PASSWORD)

- **Qdrant**: `localhost:6333` (API), `localhost:6334` (gRPC)

- **Redis UI**: `http://localhost:8001`

## Production Deployment

### 1. Build for production
```bash
docker buildx build -f Dockerfile -t dopemux-backend:1.0.0 .
docker buildx build -f Dockerfile.frontend -t dopemux-frontend:1.0.0 .
```

### 2. Configure environment
```bash
cp .env.example .env.production
# Set secure values in .env.production
export $(cat .env.production | grep -v '^#' | xargs)
```

### 3. Deploy
```bash
docker compose -f docker-compose.prod.yml up -d
```

### 4. Monitor
```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f
```

## Best Practices Implemented

### Multi-Stage Builds
- **Backend**: Separate build and runtime stages reduce final image size
- **Frontend**: Three-stage build optimizes Next.js bundle and dependencies

### Security
- Non-root user (UID 1000) in both images
- Read-only root filesystem in production
- No-new-privileges security option
- Environment variables for secrets (never baked into image)

### Caching
- Layer caching optimized by copying `requirements.txt` before source code
- Dependencies cached separately from application code

### Health Checks
- All services include health endpoints
- Docker Compose waits for service readiness before starting dependents

### Resource Management (Production)
- CPU and memory limits to prevent runaway processes
- Reservations ensure guaranteed resources

### Environment Separation
- Development: hot reload, verbose logging, all tools
- Production: minimal footprint, strict security, resource limits

## Troubleshooting

### "Port already in use"
```bash
# Change ports in docker-compose file or use:
docker compose -f docker-compose.dev.yml down
# Then restart
```

### Database connection errors
```bash
# Check PostgreSQL health
docker compose -f docker-compose.dev.yml exec postgres pg_isready -U dopemux_age

# View postgres logs
docker compose -f docker-compose.dev.yml logs postgres
```

### Build fails with rate limiting
```bash
# Retry with specific base image versions
docker buildx build -f Dockerfile --build-arg BASE_IMAGE=python:3.11-slim-bookworm -t dopemux-backend --load .
```

### Memory issues in containers
```bash
# Check resource usage
docker stats

# Increase in docker-compose.yml deploy section or Docker Desktop settings
```

## Commands Reference

```bash
# Build only
docker compose -f docker-compose.dev.yml build

# Build with no cache
docker compose -f docker-compose.dev.yml build --no-cache

# Pull latest base images
docker compose -f docker-compose.dev.yml pull

# Start in background
docker compose -f docker-compose.dev.yml up -d

# Start and watch logs
docker compose -f docker-compose.dev.yml up

# Stop services
docker compose -f docker-compose.dev.yml down

# Stop and remove volumes (WARNING: deletes data)
docker compose -f docker-compose.dev.yml down -v

# View real-time resource usage
docker stats

# Clean up unused images/containers/networks
docker system prune
docker system prune -a

# Remove specific image
docker rmi dopemux-backend:latest

# View image size
docker images dopemux-*

# Exec shell in running container
docker compose -f docker-compose.dev.yml exec backend bash
```

## Image Sizes

- **dopemux-backend**: ~1.5 GB (Python + all dependencies)
- **dopemux-frontend**: ~400 MB (Node.js + Next.js optimized)

(Sizes will vary based on dependencies and base image tags)
