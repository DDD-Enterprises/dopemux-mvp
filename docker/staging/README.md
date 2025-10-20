# Staging Deployment Configuration

**Purpose**: Docker Compose configuration for Architecture 3.0 staging environment

## Quick Start

```bash
# Start all core services
cd docker/staging
docker-compose -f docker-compose.staging.yml up -d

# Start with monitoring (Prometheus + Grafana)
docker-compose -f docker-compose.staging.yml --profile monitoring up -d

# Check service health
docker-compose -f docker-compose.staging.yml ps

# View logs
docker-compose -f docker-compose.staging.yml logs -f

# Stop all services
docker-compose -f docker-compose.staging.yml down
```

## Services

### Core Infrastructure
- **Redis** (PORT 6379): Event bus and caching
- **PostgreSQL** (PORT 5455): ConPort knowledge graph

### Application Services
- **Integration Bridge** (PORT 3016): Cross-plane coordination
- **Task-Orchestrator** (PORT 3017): Query server + ADHD engine

### Monitoring (Optional)
- **Prometheus** (PORT 9090): Metrics collection
- **Grafana** (PORT 3030): Visualization dashboards

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Integration Bridge (PORT 3016)                         │
│  • HTTP Proxy to Orchestrator                           │
│  • Event routing from PM Plane                          │
│  • Authority enforcement                                │
└────────────┬────────────────────────────────────────────┘
             │
             │ ← HTTP Queries (Component 5)
             │
┌────────────▼────────────────────────────────────────────┐
│  Task-Orchestrator (PORT 3017)                          │
│  • Query endpoints: tasks, ADHD state, recommendations  │
│  • ConPort MCP client integration                       │
│  • ADHD-aware task routing                              │
└────────────┬────────────────────────────────────────────┘
             │
             │ → ConPort MCP calls
             │
┌────────────▼────────────────────────────────────────────┐
│  PostgreSQL AGE (PORT 5455)                             │
│  • ConPort knowledge graph                              │
│  • Decisions, progress, patterns                        │
└─────────────────────────────────────────────────────────┘
```

## Environment Variables

Create `.env` file:

```bash
# PostgreSQL
POSTGRES_PASSWORD=your_secure_password_here

# Grafana (optional, monitoring profile only)
GRAFANA_PASSWORD=your_grafana_password_here

# Application
PORT_BASE=3000
LOG_LEVEL=INFO
USE_MOCK_FALLBACK=false
```

## Health Checks

All services have health checks:

```bash
# Check individual service health
curl http://localhost:3016/health  # Integration Bridge
curl http://localhost:3017/health  # Task-Orchestrator

# Check Redis
docker exec dopemux-staging-redis redis-cli ping

# Check PostgreSQL
docker exec dopemux-staging-postgres pg_isready -U dopemux_staging
```

## Performance Validation

Run integration tests against staging:

```bash
# From project root
pytest tests/integration/test_architecture_3_0_e2e.py -v -s

# Run specific test class
pytest tests/integration/test_architecture_3_0_e2e.py::TestComponent5HTTPQueries -v

# Run with performance summary
pytest tests/integration/test_architecture_3_0_e2e.py::test_performance_summary -v -s
```

## ADHD Performance Targets

- **Single Query**: < 70ms average (Component 5)
- **P95 Latency**: < 200ms (attention-safe)
- **End-to-End**: < 400ms (full PM ↔ Cognitive cycle)
- **Event Propagation**: < 100ms (async Redis Streams)

## Monitoring

### Prometheus Metrics

Access metrics at: `http://localhost:9090`

**Key Metrics**:
- `component5_query_latency_ms`: HTTP query latencies
- `component5_cache_hit_rate`: Redis cache effectiveness
- `component5_error_count`: Error tracking
- `component5_concurrent_requests`: Load monitoring

### Grafana Dashboards

Access dashboards at: `http://localhost:3030` (default: admin/admin)

**Pre-configured Dashboards**:
- Architecture 3.0 Performance Overview
- ADHD Latency Validation
- Component-by-Component Analysis
- Error and Alert Dashboard

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.staging.yml logs <service_name>

# Restart individual service
docker-compose -f docker-compose.staging.yml restart <service_name>

# Rebuild service
docker-compose -f docker-compose.staging.yml build <service_name>
docker-compose -f docker-compose.staging.yml up -d <service_name>
```

### Connection Issues

```bash
# Verify network
docker network inspect dopemux-staging-network

# Test service-to-service connectivity
docker exec dopemux-staging-integration-bridge ping task-orchestrator
docker exec dopemux-staging-task-orchestrator ping postgres
```

### Performance Issues

```bash
# Check container resource usage
docker stats

# Increase Docker resources if needed (Docker Desktop > Settings > Resources)

# Check for slow queries
docker-compose -f docker-compose.staging.yml logs task-orchestrator | grep "slow"
```

## Security Notes

⚠️ **Staging Environment Only** - Not production-ready:
- Default passwords in `.env` (change for production)
- No SSL/TLS termination
- No authentication on Integration Bridge
- No rate limiting
- No API keys required

For production deployment, see `docs/PRODUCTION_DEPLOYMENT.md`

## Next Steps

After successful staging deployment:

1. ✅ Run integration test suite
2. ✅ Validate ADHD performance targets
3. ✅ Monitor for 24 hours
4. ⏳ Load testing (100+ concurrent users)
5. ⏳ Security audit
6. ⏳ Production deployment preparation

---

**Status**: Architecture 3.0 Production Ready
**Last Updated**: 2025-10-20
**Documentation**: `docs/ARCHITECTURE_3.0_IMPLEMENTATION.md`
