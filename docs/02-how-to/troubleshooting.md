---
id: troubleshooting-playbook
title: Troubleshooting Playbook
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Troubleshooting Playbook (how-to) for dopemux documentation and developer
  workflows.
---
# Troubleshooting Playbook - Dopemux Ultra UI

Comprehensive troubleshooting guide for the Dopemux Ultra UI services. This playbook covers common issues, diagnostic procedures, and resolution steps for the ADHD Engine ecosystem.

## 🔍 Quick Diagnosis

### Health Check Commands
```bash
# Overall system health
python -m src.dopemux.cli doctor

# Individual service health
curl http://localhost:8080/health    # ADHD Engine Core
curl http://localhost:8097/health    # ADHD Dashboard
curl http://localhost:8095/health    # Legacy ADHD Engine

# Docker service status
docker compose ps -f "services/adhd_engine/compose.yml"

# Service logs
docker compose logs -f adhd-dashboard
docker compose logs -f adhd-engine
docker compose logs -f redis-primary
```

### Key Indicators
- **🟢 Green**: All services healthy, ports responding
- **🟡 Yellow**: Services up but degraded performance
- **🔴 Red**: Services down, critical failures

## 🚨 Critical Issues

### Issue: ADHD Engine Won't Start
**Symptoms**: Port 8080 unresponsive, health check fails

**Diagnosis**:
```bash
# Check if port is in use
lsof -i :8080

# Check Docker containers
docker ps | grep adhd-engine

# Check service logs
docker compose logs adhd-engine | tail -20
```

**Solutions**:

1. **Port Conflict**:
   ```bash
   # Find conflicting process
   lsof -ti:8080 | xargs kill -9

   # Or change port in docker-compose.yml
   sed -i 's/8080/8081/' compose.yml
   docker compose up -d adhd-engine
   ```

1. **Redis Connection Failed**:
   ```bash
   # Verify Redis is running
   docker ps | grep redis

   # Check Redis logs
   docker compose logs redis-primary

   # Restart Redis if needed
   docker compose restart redis-primary
   ```

1. **Missing Environment Variables**:
   ```bash
   # Check required env vars
   echo $REDIS_URL
   echo $ADHD_ENGINE_API_KEY

   # Set defaults if missing
   export REDIS_URL=redis://redis-primary:6379
   export ADHD_ENGINE_API_KEY=dev-key-123
   docker compose up -d adhd-engine
   ```

### Issue: ADHD Dashboard Unresponsive
**Symptoms**: Port 8097 down, UI fails to load

**Diagnosis**:
```bash
# Check dashboard status
curl -f http://localhost:8097/health || echo "Dashboard down"

# Check dependencies
curl -f http://localhost:8080/health || echo "ADHD Engine down"

# Check CORS configuration
curl -H "Origin: http://localhost:3000" \
     -X OPTIONS http://localhost:8097/health \
     -v
```

**Solutions**:

1. **ADHD Engine Dependency Missing**:
   ```bash
   # Ensure ADHD Engine is running first
   docker compose up -d adhd-engine
   sleep 10
   docker compose up -d adhd-dashboard
   ```

1. **CORS Configuration Error**:
   ```bash
   # Check ALLOWED_ORIGINS
   grep ALLOWED_ORIGINS compose.yml

   # Update if needed
   export ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8097
   docker compose up -d adhd-dashboard
   ```

1. **API Key Authentication Failed**:
   ```bash
   # Check dashboard API key
   curl -H "X-API-Key: test-key-456" \
        http://localhost:8097/health

   # Update environment if needed
   export DASHBOARD_API_KEY=test-key-456
   docker compose restart adhd-dashboard
   ```

### Issue: Redis Connection Lost
**Symptoms**: All services show Redis errors, data not persisting

**Diagnosis**:
```bash
# Check Redis connectivity
docker exec -it dopemux-redis-primary redis-cli ping

# Check Redis logs
docker compose logs redis-primary | tail -20

# Test from ADHD Engine container
docker exec -it dopemux-adhd-engine \
  redis-cli -h redis-primary ping
```

**Solutions**:

1. **Redis Container Crashed**:
   ```bash
   # Restart Redis
   docker compose restart redis-primary

   # Check persistence
   docker exec -it dopemux-redis-primary redis-cli save
   ```

1. **Network Connectivity Issues**:
   ```bash
   # Check network
   docker network ls | grep dopemux

   # Recreate network if needed
   docker compose down
   docker compose up -d redis-primary
   sleep 5
   docker compose up -d
   ```

1. **Memory Issues**:
   ```bash
   # Check Redis memory usage
   docker stats dopemux-redis-primary

   # Clear Redis data if corrupted
   docker exec -it dopemux-redis-primary redis-cli FLUSHALL
   ```

## ⚠️ Performance Issues

### Issue: High Response Times
**Symptoms**: API calls taking >2 seconds, UI lag

**Diagnosis**:
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s \
     http://localhost:8080/api/v1/attention-state

# Monitor resource usage
docker stats dopemux-adhd-engine dopemux-adhd-dashboard

# Check Redis performance
docker exec -it dopemux-redis-primary \
  redis-cli --latency
```

**Solutions**:

1. **Redis Performance Tuning**:
   ```bash
   # Enable Redis persistence
   docker exec -it dopemux-redis-primary \
     redis-cli config set save "900 1 300 10 60 10000"

   # Monitor Redis memory
   docker exec -it dopemux-redis-primary \
     redis-cli info memory
   ```

1. **Service Resource Limits**:
   ```bash
   # Update docker-compose.yml with limits
   services:
     adhd-engine:
       deploy:
         resources:
           limits:
             memory: 512M
             cpus: '0.5'
   ```

1. **Background Monitor Optimization**:
   ```bash
   # Adjust monitor intervals in environment
   export ENERGY_MONITOR_INTERVAL=120  # 2 minutes instead of 1
   export ATTENTION_CHECK_INTERVAL=90   # 1.5 minutes instead of 1
   docker compose restart adhd-engine
   ```

### Issue: Memory Leaks
**Symptoms**: Containers restart due to OOM, gradual performance degradation

**Diagnosis**:
```bash
# Monitor memory usage over time
docker stats --no-stream dopemux-adhd-engine

# Check Python memory usage
docker exec -it dopemux-adhd-engine \
  python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"

# Check for memory leaks in logs
docker compose logs adhd-engine | grep -i memory
```

**Solutions**:

1. **Enable Memory Profiling**:
   ```bash
   # Add to ADHD Engine environment
   export PYTHONMALLOC=malloc
   export PYTHONTRACEMALLOC=1
   docker compose restart adhd-engine
   ```

1. **Implement Memory Limits**:
   ```bash
   # Update docker-compose.yml
   services:
     adhd-engine:
       deploy:
         resources:
           limits:
             memory: 1G
           reservations:
             memory: 512M
   ```

1. **Restart Schedule**:
   ```bash
   # Add restart policy
   services:
     adhd-engine:
       restart: unless-stopped
       deploy:
         restart_policy:
           condition: on-failure
           delay: 5s
           max_attempts: 3
           window: 120s
   ```

## 🔗 Data Flow Issues

### Issue: Dashboard Shows No Data
**Symptoms**: UI loads but shows empty metrics, no ADHD state data

**Diagnosis**:
```bash
# Test ADHD Engine API directly
curl http://localhost:8080/api/v1/attention-state

# Check dashboard API calls
curl -H "X-API-Key: test-key-456" \
     http://localhost:8097/api/metrics

# Verify Redis data
docker exec -it dopemux-redis-primary \
  redis-cli KEYS "adhd:*" | head -10
```

**Solutions**:

1. **ADHD Engine Not Providing Data**:
   ```bash
   # Check engine logs for errors
   docker compose logs adhd-engine | grep -i error

   # Restart engine
   docker compose restart adhd-engine
   ```

1. **Dashboard API Key Mismatch**:
   ```bash
   # Verify API keys match
   grep API_KEY compose.yml

   # Update dashboard key
   export DASHBOARD_API_KEY=test-key-456
   docker compose restart adhd-dashboard
   ```

1. **CORS Blocking API Calls**:
   ```bash
   # Check browser console for CORS errors
   # Update ALLOWED_ORIGINS to include frontend URL
   export ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8097
   docker compose restart adhd-dashboard
   ```

### Issue: Background Monitors Not Working
**Symptoms**: Energy levels don't update, no break suggestions

**Diagnosis**:
```bash
# Check monitor logs
docker compose logs adhd-engine | grep -i monitor

# Test monitor endpoints directly
curl http://localhost:8080/api/v1/energy-level
curl http://localhost:8080/api/v1/break-recommendation

# Check Redis for monitor data
docker exec -it dopemux-redis-primary \
  redis-cli KEYS "monitor:*"
```

**Solutions**:

1. **Monitor Threads Crashed**:
   ```bash
   # Restart ADHD Engine
   docker compose restart adhd-engine

   # Check for async errors
   docker compose logs adhd-engine | grep -i async
   ```

1. **Configuration Issues**:
   ```bash
   # Check monitor intervals
   grep MONITOR_INTERVAL compose.yml

   # Reset to defaults if corrupted
   export ENERGY_MONITOR_INTERVAL=60
   export ATTENTION_CHECK_INTERVAL=60
   docker compose restart adhd-engine
   ```

1. **Redis Data Corruption**:
   ```bash
   # Clear monitor data
   docker exec -it dopemux-redis-primary \
     redis-cli DEL monitor:*

   # Restart monitors
   docker compose restart adhd-engine
   ```

## 🛡️ Security Issues

### Issue: Authentication Failures
**Symptoms**: API calls return 401/403, dashboard shows auth errors

**Diagnosis**:
```bash
# Test API key authentication
curl -H "X-API-Key: invalid-key" \
     http://localhost:8080/api/v1/user-profile

# Check JWT token validation
curl -H "Authorization: Bearer invalid.jwt.token" \
     http://localhost:8080/api/v1/assess-task

# Verify API key configuration
grep API_KEY compose.yml
```

**Solutions**:

1. **API Key Mismatch**:
   ```bash
   # Generate new API key
   openssl rand -hex 32

   # Update environment
   export ADHD_ENGINE_API_KEY=new-key-here
   docker compose restart adhd-engine
   ```

1. **JWT Secret Issues**:
   ```bash
   # Check JWT secret
   echo $JWT_SECRET_KEY

   # Generate new secret
   export JWT_SECRET_KEY=$(openssl rand -hex 32)
   docker compose restart adhd-engine
   ```

1. **CORS Origin Issues**:
   ```bash
   # Add frontend origin to allowed list
   export ALLOWED_ORIGINS=http://localhost:3000,https://myapp.com
   docker compose restart adhd-engine adhd-dashboard
   ```

### Issue: Rate Limiting Too Aggressive
**Symptoms**: Legitimate requests blocked as rate limited

**Diagnosis**:
```bash
# Check current rate limit settings
curl -H "X-API-Key: test-key-123" \
     http://localhost:8080/api/v1/user-profile \
     -H "X-Forwarded-For: 192.168.1.100"

# Check rate limit headers in response
curl -I http://localhost:8080/health
```

**Solutions**:

1. **Adjust Rate Limits**:
   ```bash
   # Increase limits in environment
   export RATE_LIMIT_REQUESTS_PER_MINUTE=100
   export RATE_LIMIT_BURST_SIZE=200
   docker compose restart adhd-engine
   ```

1. **IP-Based Whitelisting**:
   ```bash
   # Add trusted IPs to bypass rate limiting
   export TRUSTED_IPS=192.168.1.0/24,10.0.0.0/8
   docker compose restart adhd-engine
   ```

1. **Rate Limit Bypass for Dashboard**:
   ```bash
   # Allow dashboard higher limits
   export DASHBOARD_RATE_LIMIT=500
   docker compose restart adhd-dashboard
   ```

## 🔧 Configuration Issues

### Issue: Environment Variables Not Loading
**Symptoms**: Services start but use wrong configuration

**Diagnosis**:
```bash
# Check environment in containers
docker exec -it dopemux-adhd-engine env | grep REDIS
docker exec -it dopemux-adhd-dashboard env | grep API_KEY

# Check docker-compose environment section
grep -A 10 "environment:" compose.yml

# Verify .env file
cat .env | grep -v "^#"
```

**Solutions**:

1. **Missing .env File**:
   ```bash
   # Create .env file
   cat > .env << EOF
   REDIS_URL=redis://redis-primary:6379
   ADHD_ENGINE_API_KEY=dev-key-123
   DASHBOARD_API_KEY=dashboard-key-456
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8097
   EOF
   ```

1. **Docker Compose Not Reading .env**:
   ```bash
   # Add env_file to docker-compose.yml
   services:
     adhd-engine:
       env_file:
- .env
   ```

1. **Environment Variable Precedence**:
   ```bash
   # Export takes precedence over .env
   unset REDIS_URL  # Let .env value take effect
   docker compose restart adhd-engine
   ```

## 📊 Monitoring & Alerting

### Setting Up Alerts
```bash
# Create alert configuration
cat > monitoring/alerts.yml << EOF
alerts:
- name: adhd_engine_down
    condition: up{job="adhd-engine"} == 0
    severity: critical
    message: "ADHD Engine service is down"

- name: dashboard_high_error_rate
    condition: rate(errors_total{job="adhd-dashboard"}[5m]) > 0.1
    severity: warning
    message: "Dashboard error rate above 10%"

- name: redis_memory_high
    condition: redis_memory_used_bytes / redis_memory_max_bytes > 0.8
    severity: warning
    message: "Redis memory usage above 80%"
EOF

# Start monitoring stack
docker run -d \
  --name dopemux-monitor \
  -v $(pwd)/monitoring:/config \
  -p 9090:9090 \
  prom/prometheus \
  --config.file=/config/prometheus.yml
```

### Log Analysis
```bash
# Search for patterns in logs
docker compose logs --since 1h | grep -i error

# Monitor error rates
docker compose logs --tail 100 adhd-engine | \
  grep -c "ERROR\|CRITICAL" | \
  awk '{print "Error rate:", $1/100 "%"}'

# Check for performance issues
docker compose logs adhd-engine | \
  grep "response time" | \
  tail -10
```

## 🚀 Advanced Troubleshooting

### Network Debugging
```bash
# Test service-to-service communication
docker exec -it dopemux-adhd-engine \
  curl -f http://adhd-dashboard:8097/health

# Check network connectivity
docker network inspect dopemux-network

# DNS resolution test
docker exec -it dopemux-adhd-engine \
  nslookup redis-primary
```

### Performance Profiling
```bash
# Profile Python performance
docker exec -it dopemux-adhd-engine \
  python -m cProfile -s cumtime main.py > profile.txt

# Memory profiling
docker exec -it dopemux-adhd-engine \
  python -c "
import tracemalloc
tracemalloc.start()
# Run some operations
snapshot = tracemalloc.take_snapshot()
for stat in snapshot.statistics('lineno')[:10]:
    print(stat)
"

# Database query profiling
docker exec -it dopemux-redis-primary \
  redis-cli --latency-history
```

### Data Recovery
```bash
# Backup Redis data
docker exec -it dopemux-redis-primary \
  redis-cli save

# Export data
docker exec -it dopemux-redis-primary \
  redis-cli --raw KEYS "*" | \
  xargs -n1 redis-cli --raw DUMP | \
  xxd -r > redis_backup.rdb

# Restore from backup
docker cp redis_backup.rdb dopemux-redis-primary:/data/dump.rdb
docker exec -it dopemux-redis-primary \
  redis-cli shutdown save
docker compose restart redis-primary
```

## 📞 Getting Help

### Quick Diagnostic Script
```bash
#!/bin/bash
# Run this to get comprehensive diagnostic info

echo "=== Dopemux Ultra UI Diagnostics ==="
echo "Timestamp: $(date)"
echo "Working Directory: $(pwd)"
echo ""

echo "=== System Resources ==="
docker system df
echo ""

echo "=== Service Status ==="
docker compose ps
echo ""

echo "=== Health Checks ==="
echo "ADHD Engine: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health || echo 'DOWN')"
echo "ADHD Dashboard: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8097/health || echo 'DOWN')"
echo ""

echo "=== Recent Errors ==="
docker compose logs --since 5m 2>&1 | grep -i error | tail -10
echo ""

echo "=== Configuration Check ==="
echo "REDIS_URL: ${REDIS_URL:-NOT SET}"
echo "ADHD_ENGINE_API_KEY: ${ADHD_ENGINE_API_KEY:+SET}"
echo "DASHBOARD_API_KEY: ${DASHBOARD_API_KEY:+SET}"
echo "ALLOWED_ORIGINS: ${ALLOWED_ORIGINS:-NOT SET}"
```

### Escalation Checklist
- [ ] Run diagnostic script above
- [ ] Check GitHub issues for similar problems
- [ ] Collect complete logs with timestamps
- [ ] Document exact reproduction steps
- [ ] Include system information (Docker version, OS, etc.)
- [ ] Create minimal test case if possible

---

**Remember**: Always start with the health checks and work systematically through the components. Most issues are configuration-related or dependency failures that can be resolved with the steps above.hecks and work systematically through the components. Most issues are configuration-related or dependency failures that can be resolved with the steps above.
