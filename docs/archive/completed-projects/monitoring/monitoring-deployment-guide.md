---
id: MONITORING_DEPLOYMENT_GUIDE
title: Monitoring_Deployment_Guide
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Monitoring_Deployment_Guide (explanation) for dopemux documentation and developer
  workflows.
---
# Monitoring Deployment Guide

**Status**: Code Complete ✅ | Deployment Pending 🔲
**Last Updated**: 2025-11-13

---

## Quick Summary

The monitoring infrastructure and code integration are **100% complete**. All that remains is rebuilding containers to include the new dependencies and monitoring code.

### What's Done

✅ Prometheus, Grafana, AlertManager deployed and running
✅ Monitoring base class created (`shared/monitoring/base.py`)
✅ ADHD Engine code integrated with monitoring
✅ ConPort code integrated with monitoring
✅ All 6 services configured in Prometheus

### What's Needed

🔲 Rebuild containers with `prometheus-client` package
🔲 Copy `shared/monitoring` module into containers
🔲 Restart services
🔲 Verify metrics endpoints work

---

## Step-by-Step Deployment

### 1. ADHD Engine Deployment

**Option A: Update Dockerfile (Recommended)**

Edit `services/adhd_engine/Dockerfile`:

```dockerfile
# Add prometheus-client to requirements
RUN pip install prometheus-client

# Copy shared monitoring module
COPY ../../shared/monitoring /app/shared/monitoring
```

Then rebuild:

```bash
docker-compose build adhd-engine
docker-compose up -d adhd-engine
```

**Option B: Hot Patch (Quick Test)**

```bash
# Install prometheus-client in running container
docker exec adhd-engine-1 pip install prometheus-client

# Copy monitoring module
docker cp shared/monitoring adhd-engine-1:/app/shared/monitoring

# Restart
docker restart adhd-engine-1
```

**Verify:**

```bash
# Test metrics endpoint
curl http://localhost:8001/metrics

# Should see output like:
# dopemux_service_info{service="adhd-engine",workspace_id="default",...} 1.0
# dopemux_requests_total{endpoint="/health",method="GET",status="200",...} 5.0
```

---

### 2. ConPort Deployment

**Already Updated!** The Dockerfile has been modified with:
- `prometheus-client` added to pip install
- Monitoring files copied (`shared_monitoring.py`, `shared_monitoring_init.py`)

Just rebuild:

```bash
docker-compose build conport
docker-compose up -d conport
```

**Verify:**

```bash
curl http://localhost:3004/metrics
```

---

### 3. Verify in Prometheus

1. Open Prometheus UI: http://localhost:9090

1. Check targets: http://localhost:9090/targets
- All services should show "UP" (green)
- Previously showed "down" with connection refused errors

1. Query metrics:
   ```promql
   # See all services
   dopemux_service_info

   # Request rates by service
   rate(dopemux_requests_total[5m])

   # Filter by workspace
   dopemux_requests_total{workspace_id="workspace1"}
   ```

---

### 4. Verify in Grafana

1. Open Grafana: http://localhost:3000
- Username: `admin`
- Password: `dopemux_admin`

1. Go to Explore tab

1. Try queries:
   ```promql
   # Service health
   dopemux_health_status

   # Request duration p95
   histogram_quantile(0.95, rate(dopemux_request_duration_seconds_bucket[5m]))

   # Requests per second by service
   sum(rate(dopemux_requests_total[5m])) by (service)
   ```

---

## Troubleshooting

### Metrics endpoint returns 404

**Cause**: Service hasn't loaded new code
**Fix**:
```bash
docker restart <service-name>
docker logs <service-name> | grep -i monitoring
# Should see "✅ Monitoring initialized"
```

### Metrics endpoint returns 500

**Cause**: Missing `prometheus-client` package
**Fix**:
```bash
docker exec <service> pip install prometheus-client
docker restart <service>
```

### Prometheus shows service as "down"

**Cause**: Metrics endpoint not responding
**Fix**:
```bash
# Check if service is running
docker ps | grep <service>

# Test endpoint from inside Docker network (replace host/port as needed)
docker exec prometheus curl http://localhost:9090/metrics

# Check Prometheus logs
docker logs dopemux-prometheus | grep <service>
```

### No workspace_id labels

**Cause**: Missing environment variable
**Fix**:
```bash
# Add to docker-compose.yml
environment:
- WORKSPACE_ID=workspace1  # or use actual workspace ID
- INSTANCE_ID=1
```

---

## Verification Checklist

After deployment, verify:

- [ ] All services show "UP" in Prometheus targets
- [ ] Metrics endpoints return data: `/metrics` on each service
- [ ] Workspace labels appear in metrics: `workspace_id="..."`
- [ ] Instance labels appear: `instance_id="..."`
- [ ] Request counts increment when APIs are called
- [ ] Health status metrics exist: `dopemux_health_status`
- [ ] Grafana can query metrics successfully
- [ ] No errors in service logs related to monitoring

---

## Files Modified Summary

### Created Files

1. `shared/monitoring/base.py` - Core monitoring class (300+ lines)
1. `shared/monitoring/__init__.py` - Module exports
1. `services/monitoring/prometheus.yml` - Prometheus configuration
1. `services/monitoring/alerting_rules.yml` - Alert rules
1. `services/monitoring/alertmanager.yml` - AlertManager config
1. `services/monitoring/grafana/provisioning/` - Grafana auto-config
1. `docker-compose.monitoring.yml` - Monitoring stack compose
1. `docker/mcp-servers/conport/shared_monitoring.py` - ConPort copy of monitoring
1. `docker/mcp-servers/conport/shared_monitoring_init.py` - ConPort **init**

### Modified Files

1. `services/adhd_engine/main.py` - Added monitoring initialization, middleware, /metrics endpoint
1. `docker/mcp-servers/conport/enhanced_server.py` - Added monitoring integration
1. `docker/mcp-servers/conport/Dockerfile` - Added prometheus-client dependency

---

## Next Steps After Deployment

Once all services are deployed and metrics are flowing:

1. **Create Grafana Dashboards**
- Service overview dashboard
- Workspace comparison dashboard
- ADHD-specific metrics dashboard

1. **Test Alerts**
- Trigger high error rate
- Verify AlertManager notifications
- Test workspace-aware routing

1. **Performance Validation**
- Monitor overhead (should be < 100ms per request)
- Check memory usage
- Validate label cardinality

1. **Integrate Remaining Services**
- Orchestrator
- Serena
- Dopecon Bridge
- Dope Context

---

## Quick Commands Reference

```bash
# Check monitoring stack
docker ps | grep -E "prometheus|grafana|alertmanager"

# View Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job, health, lastError}'

# Test service metrics
curl http://localhost:8001/metrics  # ADHD Engine
curl http://localhost:3004/metrics  # ConPort

# Check service logs for monitoring
docker logs adhd-engine-1 | grep -i monitoring
docker logs conport-1 | grep -i monitoring

# Restart monitoring stack
docker-compose -f docker-compose.monitoring.yml restart

# View Prometheus config
docker exec dopemux-prometheus cat /etc/prometheus/prometheus.yml
```

---

## Success Criteria

✅ All 6 service targets showing "UP" in Prometheus
✅ Metrics data flowing for at least 2 services (ADHD Engine, ConPort)
✅ Workspace labels visible in all metrics
✅ Request tracking working (counters incrementing)
✅ Health status metrics updating
✅ Grafana can query and visualize metrics
✅ No errors in service or monitoring logs

**When all criteria met**: Ready to create dashboards and integrate remaining services.
