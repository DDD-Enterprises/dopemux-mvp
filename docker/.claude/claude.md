# Docker and Deployment Context

**Scope**: Container configuration, deployment automation, and infrastructure
**Inherits**: Two-Plane Architecture from project root
**Focus**: Reliable containerization with ADHD-friendly deployment patterns

## 🐳 Container Philosophy

### ADHD-Optimized Deployment
- **Clear Build Process**: Verbose output with progress indicators
- **Fast Iteration**: Quick container rebuilds for development workflow
- **Error Visibility**: Clear error messages and debugging information
- **Consistent Environments**: Identical development, staging, and production setups

### Container Strategy
- **Multi-Stage Builds**: Optimized images with clear separation of concerns
- **Development vs Production**: Different configurations for different environments
- **Service Isolation**: Each service in its own container with clear boundaries
- **Health Checks**: Reliable service health monitoring and recovery

## 🎯 Docker Standards

### Dockerfile Patterns
```dockerfile
# Multi-stage build for Python services
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1000 app && \
    useradd --uid 1000 --gid app --shell /bin/bash --create-home app

# Set working directory
WORKDIR /app

# Development stage
FROM base as development

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY --chown=app:app . .

# Switch to non-root user
USER app

# Development command with auto-reload
CMD ["uvicorn", "dopemux.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Install only production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY --chown=app:app . .

# Switch to non-root user
USER app

# Health check for container monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["uvicorn", "dopemux.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose Patterns
```yaml
# docker-compose.yml - Development environment
version: '3.8'

services:
  # Main application service
  dopemux-api:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - /app/__pycache__
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/dopemux
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # Database service
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: dopemux
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d dopemux"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Cache service
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:

networks:
  default:
    name: dopemux-network
```

## 🚀 Agent Coordination

### Developer Agent (Primary)
**For Container Development**:
- Create optimized Dockerfiles with clear build stages
- Implement proper health checks and monitoring
- Ensure containers follow security best practices
- Debug container issues and optimize build times

### Architect Agent (Consultation)
**For Infrastructure Design**:
- Design service communication patterns
- Plan container orchestration and scaling strategies
- Review security implications of container configurations
- Guide infrastructure architecture decisions

### Deployment Standards
- **Security**: Non-root users, minimal attack surface, secure communication
- **Performance**: Optimized images, efficient resource usage, fast startup times
- **Reliability**: Health checks, graceful shutdowns, restart policies
- **Observability**: Comprehensive logging, metrics, and monitoring

## 🔧 Service-Specific Configurations

### MCP Server Containers
```dockerfile
# Dockerfile for MCP servers
FROM python:3.11-slim

# Install MCP server dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP server code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash mcp
USER mcp

# Health check for MCP server
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('localhost', 8080))" || exit 1

# Start MCP server
CMD ["python", "server.py", "--port", "8080"]
```

### Database Migration Container
```dockerfile
# Dockerfile for database migrations
FROM python:3.11-slim

# Install migration tools
RUN pip install alembic psycopg2-binary

# Copy migration scripts
COPY migrations/ /migrations/
COPY alembic.ini /alembic.ini

WORKDIR /

# Migration command
ENTRYPOINT ["alembic"]
CMD ["upgrade", "head"]
```

## 📁 Container Organization

### Directory Structure
```
docker/
├── services/              # Service-specific container configs
│   ├── dopemux-api/      # Main application container
│   ├── mcp-servers/      # MCP server containers
│   └── workers/          # Background worker containers
├── infrastructure/        # Infrastructure containers
│   ├── postgres/         # Database configuration
│   ├── redis/           # Cache configuration
│   └── nginx/           # Reverse proxy configuration
├── compose/              # Docker Compose configurations
│   ├── development.yml   # Development environment
│   ├── staging.yml      # Staging environment
│   └── production.yml   # Production environment
└── scripts/              # Container management scripts
    ├── build.sh         # Build all containers
    ├── deploy.sh        # Deployment automation
    └── health-check.sh  # Health monitoring
```

### Environment-Specific Configurations
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  dopemux-api:
    build:
      target: production
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
    environment:
      - LOG_LEVEL=INFO
      - WORKERS=4

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - dopemux-api
```

## 🎯 ADHD-Friendly Container Patterns

### Build Progress Feedback
```bash
# docker/scripts/build.sh
#!/bin/bash

set -euo pipefail

# Color codes for visual feedback
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

services=("dopemux-api" "mcp-conport" "mcp-task-master")
total=${#services[@]}

echo "🐳 Building Docker containers..."

for i in "${!services[@]}"; do
    service=${services[i]}
    current=$((i+1))

    echo -e "${BLUE}[${current}/${total}]${NC} Building ${service}..."

    if docker build -t "dopemux/${service}" "docker/services/${service}"; then
        echo -e "${GREEN}✅${NC} ${service} built successfully"
    else
        echo -e "${RED}❌${NC} Failed to build ${service}"
        exit 1
    fi
done

echo -e "${GREEN}🎉 All containers built successfully!${NC}"
```

### Health Monitoring
```bash
# docker/scripts/health-check.sh
#!/bin/bash

check_service_health() {
    local service=$1
    local url=$2

    echo -n "Checking ${service}... "

    if curl -sf "${url}" > /dev/null; then
        echo "✅ Healthy"
        return 0
    else
        echo "❌ Unhealthy"
        return 1
    fi
}

echo "🏥 Checking service health..."

check_service_health "API" "http://localhost:8000/health"
check_service_health "ConPort" "http://localhost:8001/health"
check_service_health "Task-Master" "http://localhost:8002/health"

echo "🎯 Health check completed"
```

### Container Debugging
```bash
# docker/scripts/debug.sh
#!/bin/bash

debug_container() {
    local container=$1

    echo "🔍 Debugging container: ${container}"
    echo "📊 Container stats:"
    docker stats "${container}" --no-stream

    echo "📝 Recent logs:"
    docker logs "${container}" --tail 20

    echo "🐚 Entering container shell:"
    docker exec -it "${container}" /bin/bash
}

# Usage: ./debug.sh dopemux-api
debug_container "$1"
```

## 🔍 Container Security

### Security Best Practices
- **Non-root Users**: All containers run with non-privileged users
- **Minimal Images**: Use slim/alpine base images to reduce attack surface
- **Secret Management**: Use Docker secrets or environment files for sensitive data
- **Network Isolation**: Services communicate through defined networks only

### Security Scanning
```bash
# docker/scripts/security-scan.sh
#!/bin/bash

scan_image() {
    local image=$1

    echo "🔐 Scanning ${image} for vulnerabilities..."

    if command -v trivy >/dev/null; then
        trivy image "${image}"
    else
        echo "⚠️ Trivy not installed. Install for security scanning."
    fi
}

# Scan all project images
for image in $(docker images --format "table {{.Repository}}:{{.Tag}}" | grep dopemux); do
    scan_image "${image}"
done
```

---

**Container Excellence**: Optimized, secure containers with clear build and deployment processes
**ADHD Integration**: Visual feedback and streamlined workflows for container management
**Production Ready**: Reliable deployment patterns with comprehensive monitoring and debugging tools