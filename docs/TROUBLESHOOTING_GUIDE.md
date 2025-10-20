# Architecture 3.0 Troubleshooting Guide

**Purpose**: Common issues, root causes, and solutions for Architecture 3.0
**Audience**: Developers, DevOps engineers, support engineers
**Status**: Production-Ready Troubleshooting Reference

---

## Quick Diagnostic Commands

```bash
# Health checks
curl -f http://localhost:3016/health  # Integration Bridge
curl -f http://localhost:3017/health  # Task-Orchestrator

# Container status
docker-compose ps

# Logs (last 50 lines)
docker-compose logs --tail=50 integration-bridge
docker-compose logs --tail=50 task-orchestrator

# Resource usage
docker stats --no-stream

# Performance test
curl -o /dev/null -w '%{time_total}s\n' http://localhost:3016/orchestrator/tasks
```

---

## Issue Categories

1. [Service Won't Start](#service-wont-start)
2. [Connection Failures](#connection-failures)
3. [Performance Issues](#performance-issues)
4. [Error Responses](#error-responses)
5. [Data Issues](#data-issues)
6. [Testing Issues](#testing-issues)

---

## Service Won't Start

### Issue: Integration Bridge fails to start

**Symptoms**:
- Container exits immediately
- Health check never passes
- `docker-compose ps` shows "Exited (1)"

**Common Causes**:

1. **Port already in use (PORT 3016)**
   ```bash
   # Check what's using the port
   lsof -i :3016

   # Solution: Kill the process or change PORT_BASE
   kill -9 <PID>
   # OR
   PORT_BASE=4000 docker-compose up -d
   ```

2. **Missing environment variables**
   ```bash
   # Check .env file exists
   cat .env

   # Solution: Create .env file
   cat > .env <<EOF
   PORT_BASE=3000
   LOG_LEVEL=INFO
   USE_MOCK_FALLBACK=false
   REDIS_URL=redis://localhost:6379
   EOF
   ```

3. **Python import errors**
   ```bash
   # Check logs for ImportError
   docker-compose logs integration-bridge | grep ImportError

   # Solution: Rebuild container with updated dependencies
   docker-compose build integration-bridge
   docker-compose up -d integration-bridge
   ```

4. **ORCHESTRATOR_URL misconfigured**
   ```bash
   # Check environment
   docker-compose exec integration-bridge env | grep ORCHESTRATOR_URL

   # Solution: Update docker-compose.yml or .env
   # ORCHESTRATOR_URL should be: http://task-orchestrator:3017
   ```

**Verification**:
```bash
# Service should be healthy within 30 seconds
docker-compose ps integration-bridge
# Expected: STATUS shows "healthy"

curl -f http://localhost:3016/health
# Expected: {"status": "healthy"}
```

---

### Issue: Task-Orchestrator fails to start

**Symptoms**:
- Container exits or restarts repeatedly
- Health check fails
- Integration Bridge shows "503 Service Unavailable"

**Common Causes**:

1. **Port conflict (PORT 3017)**
   ```bash
   lsof -i :3017
   # Solution: Kill process or change PORT_BASE
   ```

2. **PostgreSQL connection failure**
   ```bash
   # Check PostgreSQL is running
   docker-compose ps postgres
   # Expected: "healthy"

   # Test connection
   docker-compose exec task-orchestrator python -c "
   import psycopg2
   conn = psycopg2.connect('host=postgres dbname=dopemux_staging user=dopemux_staging password=changeme')
   print('Connected!')
   "

   # Solution: Verify POSTGRES_* environment variables match
   ```

3. **Redis connection failure**
   ```bash
   # Check Redis is running
   docker-compose ps redis

   # Test connection
   docker-compose exec task-orchestrator redis-cli -h redis ping
   # Expected: PONG

   # Solution: Verify REDIS_URL environment variable
   ```

4. **Missing Python dependencies**
   ```bash
   docker-compose logs task-orchestrator | grep "ModuleNotFoundError"

   # Solution: Rebuild with dependencies
   docker-compose build task-orchestrator
   docker-compose up -d task-orchestrator
   ```

---

## Connection Failures

### Issue: "503 Service Unavailable" from Integration Bridge

**Symptoms**:
- Queries return 503 status code
- Error: "Task-Orchestrator unavailable"

**Root Causes**:

1. **Task-Orchestrator not running**
   ```bash
   docker-compose ps task-orchestrator
   # If not healthy, check logs
   docker-compose logs task-orchestrator

   # Solution: Restart orchestrator
   docker-compose restart task-orchestrator
   ```

2. **Network connectivity issue**
   ```bash
   # Test internal network
   docker-compose exec integration-bridge ping task-orchestrator
   # Expected: ping successful

   # Test HTTP connectivity
   docker-compose exec integration-bridge curl -f http://task-orchestrator:3017/health
   # Expected: {"status": "healthy"}

   # Solution: Recreate network
   docker-compose down
   docker-compose up -d
   ```

3. **Orchestrator URL misconfigured**
   ```bash
   # Check configured URL
   docker-compose exec integration-bridge env | grep ORCHESTRATOR_URL
   # Expected: http://task-orchestrator:3017

   # Solution: Fix environment variable in docker-compose.yml
   ```

4. **Mock fallback enabled (development mode)**
   ```bash
   docker-compose exec integration-bridge env | grep USE_MOCK_FALLBACK
   # If "true", queries use mock data instead of real orchestrator

   # Solution: Set USE_MOCK_FALLBACK=false
   ```

---

### Issue: "Redis connection refused"

**Symptoms**:
- Event propagation fails
- Cache misses with connection errors
- Logs show "ConnectionRefusedError: [Errno 111] Connection refused"

**Root Causes**:

1. **Redis not running**
   ```bash
   docker-compose ps redis
   # Expected: "healthy"

   # Solution: Start Redis
   docker-compose up -d redis
   sleep 10  # Wait for startup
   ```

2. **Redis URL misconfigured**
   ```bash
   docker-compose exec task-orchestrator env | grep REDIS_URL
   # Expected: redis://redis:6379 (Docker network)
   # OR: redis://localhost:6379 (local dev)

   # Solution: Fix REDIS_URL environment variable
   ```

3. **Redis maxmemory exceeded**
   ```bash
   docker-compose exec redis redis-cli INFO memory | grep maxmemory
   docker-compose exec redis redis-cli INFO memory | grep used_memory

   # Solution: Increase maxmemory or clear cache
   docker-compose exec redis redis-cli FLUSHDB
   ```

4. **Network isolation**
   ```bash
   # Test connectivity
   docker-compose exec task-orchestrator redis-cli -h redis ping
   # Expected: PONG

   # Solution: Verify all services on same Docker network
   docker network inspect dopemux-staging-network
   ```

---

## Performance Issues

### Issue: Queries exceed ADHD latency targets (> 200ms)

**Symptoms**:
- Slow response times
- P95 latency > 200ms
- Users report "sluggish" experience

**Diagnostic Steps**:

```bash
# 1. Measure current latency
for i in {1..20}; do
  curl -o /dev/null -sw '%{time_total}s\n' http://localhost:3016/orchestrator/tasks
done

# 2. Check container resource usage
docker stats --no-stream

# 3. Check system resources
free -m  # Memory
top -b -n 1 | head -20  # CPU
df -h  # Disk
```

**Common Causes**:

1. **Insufficient container resources**
   ```yaml
   # Solution: Add resource limits to docker-compose.yml
   services:
     integration-bridge:
       deploy:
         resources:
           limits:
             cpus: '2.0'
             memory: 1G
           reservations:
             cpus: '1.0'
             memory: 512M
   ```

2. **Redis caching disabled**
   ```bash
   # Check if caching enabled
   docker-compose exec task-orchestrator env | grep REDIS_TTL_SECONDS

   # Solution: Enable caching
   # Edit .env: REDIS_TTL_SECONDS=30
   docker-compose up -d
   ```

3. **PostgreSQL slow queries**
   ```bash
   # Enable slow query logging
   docker-compose exec postgres psql -U dopemux_staging -c "
   ALTER SYSTEM SET log_min_duration_statement = 100;
   SELECT pg_reload_conf();
   "

   # Check logs for slow queries
   docker-compose logs postgres | grep "duration:"

   # Solution: Add indexes, optimize queries
   ```

4. **Too many concurrent requests**
   ```bash
   # Check concurrent connections
   docker-compose exec integration-bridge netstat -an | grep :3016 | grep ESTABLISHED | wc -l

   # Solution: Add rate limiting or scale horizontally
   ```

5. **Network latency (Docker on Mac/Windows)**
   ```bash
   # Docker Desktop network overhead on non-Linux systems
   # Solution: Use host networking mode or deploy on Linux
   ```

**Optimization Steps**:

1. **Enable connection pooling**
   ```python
   # Already implemented in aiohttp ClientSession
   # Verify keep-alive connections
   docker-compose logs integration-bridge | grep "Connection: keep-alive"
   ```

2. **Implement response caching**
   ```python
   # Add Redis caching to orchestrator_endpoints.py
   # Cache tasks, ADHD state, recommendations for 30 seconds
   ```

3. **Use parallel queries**
   ```python
   # Already implemented via asyncio.gather() for parallel endpoints
   # Verify parallel execution in logs
   ```

---

### Issue: High memory usage / memory leak

**Symptoms**:
- Container memory usage grows continuously
- OOMKilled errors
- Degrading performance over time

**Diagnostic Steps**:

```bash
# 1. Monitor memory usage over time
watch docker stats

# 2. Check for memory leaks in Python
docker-compose exec integration-bridge python -c "
import gc
print(f'Objects: {len(gc.get_objects())}')
gc.collect()
print(f'After GC: {len(gc.get_objects())}')
"

# 3. Check Redis memory
docker-compose exec redis redis-cli INFO memory
```

**Common Causes**:

1. **Unclosed HTTP connections**
   ```python
   # Solution: Verify async context managers used everywhere
   async with aiohttp.ClientSession() as session:
       async with session.get(url) as resp:
           return await resp.json()
   ```

2. **Redis memory not limited**
   ```bash
   # Solution: Set maxmemory policy
   docker-compose exec redis redis-cli CONFIG SET maxmemory 256mb
   docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
   ```

3. **Large response caching**
   ```bash
   # Check cache sizes
   docker-compose exec redis redis-cli INFO memory

   # Solution: Reduce TTL or implement size limits
   ```

**Solutions**:

```bash
# 1. Restart services to clear memory
docker-compose restart integration-bridge task-orchestrator

# 2. Add memory limits
# Edit docker-compose.yml to add memory limits

# 3. Enable memory profiling
docker-compose exec integration-bridge pip install memory_profiler
# Add @profile decorator to suspect functions
```

---

## Error Responses

### Issue: "404 Not Found" on query endpoints

**Symptoms**:
- `/orchestrator/tasks` returns 404
- `/orchestrator/adhd-state` returns 404

**Root Causes**:

1. **Router not registered**
   ```python
   # Check main.py for router registration
   docker-compose exec integration-bridge cat /app/main.py | grep "include_router"

   # Expected:
   # app.include_router(orchestrator_router)

   # Solution: Verify orchestrator_endpoints.py imported and registered
   ```

2. **Wrong URL path**
   ```bash
   # Correct paths:
   http://localhost:3016/orchestrator/tasks
   http://localhost:3016/orchestrator/adhd-state

   # NOT:
   http://localhost:3016/tasks  # Missing /orchestrator prefix
   ```

3. **FastAPI docs for debugging**
   ```bash
   # Check available endpoints
   open http://localhost:3016/docs
   # Should show all /orchestrator/* endpoints
   ```

---

### Issue: "400 Bad Request" or "422 Unprocessable Entity"

**Symptoms**:
- Query parameters rejected
- Request validation fails

**Root Causes**:

1. **Invalid query parameters**
   ```bash
   # Check Pydantic validation errors
   curl -v http://localhost:3016/orchestrator/tasks?limit=invalid
   # Expected error: "value is not a valid integer"

   # Solution: Use correct types
   curl http://localhost:3016/orchestrator/tasks?limit=10
   ```

2. **Missing required parameters**
   ```bash
   # Some endpoints may require parameters
   # Check API docs: http://localhost:3016/docs
   ```

---

## Data Issues

### Issue: Empty task list returned

**Symptoms**:
- `/orchestrator/tasks` returns `[]`
- No tasks available for selection

**Root Causes**:

1. **Mock data mode enabled**
   ```bash
   docker-compose exec integration-bridge env | grep USE_MOCK_FALLBACK
   # If "true", using mock data

   # Solution: Set USE_MOCK_FALLBACK=false for real data
   ```

2. **No tasks in ConPort database**
   ```bash
   # Check ConPort for progress entries
   docker-compose exec postgres psql -U dopemux_staging -c "
   SELECT COUNT(*) FROM conport.progress_entry;
   "

   # Solution: Create test tasks via ConPort MCP
   ```

3. **Filter parameters too restrictive**
   ```bash
   # Remove filters
   curl http://localhost:3016/orchestrator/tasks?limit=50
   # Instead of:
   curl http://localhost:3016/orchestrator/tasks?status=DONE&limit=10
   ```

---

### Issue: ADHD state shows unrealistic values

**Symptoms**:
- Energy level always "medium"
- Attention level doesn't change
- Time since break incorrect

**Root Causes**:

1. **Mock data in use**
   ```bash
   # Check USE_MOCK_FALLBACK
   # Mock data returns static values
   ```

2. **ADHD state not being updated**
   ```bash
   # Check Task-Orchestrator ADHD engine
   docker-compose logs task-orchestrator | grep "ADHD"

   # Solution: Verify ADHD state tracking implemented
   ```

3. **Session not active**
   ```bash
   # Start a session first
   curl -X POST http://localhost:3017/session/start

   # Then query ADHD state
   curl http://localhost:3016/orchestrator/adhd-state
   ```

---

## Testing Issues

### Issue: Integration tests fail with "Connection refused"

**Symptoms**:
- Tests fail immediately
- Error: `aiohttp.ClientConnectionError`

**Root Causes**:

1. **Services not running**
   ```bash
   # Start services before tests
   cd docker/staging
   docker-compose -f docker-compose.staging.yml up -d

   # Wait for health checks
   sleep 30

   # Run tests
   cd ../..
   pytest tests/integration/test_architecture_3_0_e2e.py -v
   ```

2. **Wrong URLs in tests**
   ```python
   # Check test configuration
   INTEGRATION_BRIDGE_URL = "http://localhost:3016"  # Correct
   ORCHESTRATOR_URL = "http://localhost:3017"  # Correct
   ```

3. **Firewall blocking localhost**
   ```bash
   # Test connectivity
   curl -f http://localhost:3016/health

   # Solution: Allow localhost connections in firewall
   ```

---

### Issue: Performance tests fail ADHD targets

**Symptoms**:
- Average latency > 70ms
- P95 latency > 200ms
- Test assertion fails

**Root Causes**:

1. **System under load**
   ```bash
   # Check system load
   uptime
   top -b -n 1

   # Solution: Run tests on idle system or increase tolerances
   ```

2. **Cold start effects**
   ```bash
   # Services just started, not warmed up
   # Solution: Add warmup requests before test
   for i in {1..5}; do
     curl -s http://localhost:3016/orchestrator/tasks > /dev/null
   done

   # Then run performance tests
   pytest tests/integration/test_architecture_3_0_e2e.py::TestPerformanceValidation -v
   ```

3. **Docker overhead (non-Linux)**
   ```bash
   # Docker Desktop on Mac/Windows adds network latency
   # Solution: Adjust targets or test on Linux
   ```

---

## Common Error Messages

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Connection refused` | Service not running | Start service, verify port |
| `503 Service Unavailable` | Orchestrator down | Restart orchestrator |
| `404 Not Found` | Wrong URL or router not registered | Check URL, verify router |
| `422 Unprocessable Entity` | Invalid parameters | Check API docs, fix params |
| `ModuleNotFoundError` | Missing dependency | Rebuild container |
| `Redis connection timeout` | Redis overloaded | Restart Redis, check maxmemory |
| `pg_isready: no response` | PostgreSQL not ready | Wait 30s, check logs |

---

## Debug Mode

Enable detailed logging for troubleshooting:

```bash
# Edit .env
LOG_LEVEL=DEBUG

# Restart services
docker-compose up -d

# Watch logs in real-time
docker-compose logs -f integration-bridge task-orchestrator
```

---

## Getting Help

If issues persist after troubleshooting:

1. **Collect diagnostic information**:
   ```bash
   # Health checks
   ./health-check.sh > diagnostics.txt

   # Logs
   docker-compose logs > docker-logs.txt

   # Resource usage
   docker stats --no-stream >> diagnostics.txt

   # Environment
   docker-compose config >> diagnostics.txt
   ```

2. **Check documentation**:
   - Architecture 3.0 implementation: `docs/ARCHITECTURE_3.0_IMPLEMENTATION.md`
   - Performance analysis: `docs/COMPONENT_5_PERFORMANCE_ANALYSIS.md`
   - Deployment runbook: `docs/DEPLOYMENT_RUNBOOK.md`

3. **Create GitHub issue** with diagnostics attached

---

**Version**: 1.0.0
**Last Updated**: 2025-10-20
**Review Frequency**: Quarterly
