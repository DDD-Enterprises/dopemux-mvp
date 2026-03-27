# RAG System Operations Runbook

## Overview

This runbook provides operational procedures, monitoring guidelines, and troubleshooting steps for the Dopemux RAG system in production. It covers health checks, performance monitoring, incident response, and maintenance tasks.

## System Components

- **Milvus**: Vector database for hybrid search
- **ConPort**: Project memory graph
- **Voyage AI**: Embedding and reranking services
- **RAG Pipeline**: Retrieval and processing services

## Health Monitoring

### Automated Health Checks

#### System Status Script
```bash
#!/bin/bash
# scripts/check_rag_health.sh

set -e

echo "🔍 RAG System Health Check - $(date)"

# Check Milvus
echo "📊 Checking Milvus..."
if curl -f http://localhost:9091/health >/dev/null 2>&1; then
    echo "✅ Milvus: Healthy"
else
    echo "❌ Milvus: Unhealthy"
    exit 1
fi

# Check ConPort
echo "🧠 Checking ConPort..."
if curl -f http://localhost:8080/health >/dev/null 2>&1; then
    echo "✅ ConPort: Healthy"
else
    echo "⚠️ ConPort: Unavailable (degraded mode)"
fi

# Check Voyage AI
echo "🚢 Checking Voyage AI..."
python -c "
import os
import voyageai
try:
    client = voyageai.Client(api_key=os.getenv('VOYAGE_API_KEY'))
    client.embed(texts=['health check'], model='voyage-context-3')
    print('✅ Voyage AI: Healthy')
except Exception as e:
    print(f'❌ Voyage AI: Error - {e}')
    exit(1)
"

echo "🎉 Health check complete!"
```

#### Python Health Monitor
```python
# scripts/health_monitor.py
import time
import requests
import logging
from typing import Dict, Any, List
import voyageai
from pymilvus import connections, utility

class RAGHealthMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize clients
        self.voyage_client = voyageai.Client(api_key=config["voyage_api_key"])

    def check_milvus_health(self) -> Dict[str, Any]:
        """Check Milvus database health."""
        try:
            # Check HTTP health endpoint
            response = requests.get(f"http://{self.config['milvus_host']}:9091/health", timeout=5)
            http_healthy = response.status_code == 200

            # Check gRPC connection
            connections.connect("health_check",
                              host=self.config['milvus_host'],
                              port=self.config['milvus_port'])

            # Check collections
            collections = utility.list_collections()
            expected_collections = ["ProjectDocs", "ProjectCode"]
            collections_healthy = all(col in collections for col in expected_collections)

            # Check collection entity counts
            entity_counts = {}
            for collection_name in expected_collections:
                try:
                    from pymilvus import Collection
                    collection = Collection(collection_name)
                    entity_counts[collection_name] = collection.num_entities
                except Exception as e:
                    entity_counts[collection_name] = f"Error: {e}"

            return {
                "status": "healthy" if http_healthy and collections_healthy else "unhealthy",
                "http_endpoint": http_healthy,
                "grpc_connection": True,
                "collections": collections_healthy,
                "entity_counts": entity_counts,
                "timestamp": int(time.time())
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": int(time.time())
            }

    def check_conport_health(self) -> Dict[str, Any]:
        """Check ConPort memory system health."""
        try:
            response = requests.get(f"{self.config['conport_url']}/health", timeout=5)

            if response.status_code == 200:
                # Get memory stats
                stats_response = requests.get(f"{self.config['conport_url']}/api/memory/stats", timeout=5)
                stats = stats_response.json() if stats_response.status_code == 200 else {}

                return {
                    "status": "healthy",
                    "api_responsive": True,
                    "memory_stats": stats,
                    "timestamp": int(time.time())
                }
            else:
                return {
                    "status": "unhealthy",
                    "api_responsive": False,
                    "http_status": response.status_code,
                    "timestamp": int(time.time())
                }

        except Exception as e:
            return {
                "status": "unavailable",
                "error": str(e),
                "timestamp": int(time.time())
            }

    def check_voyage_health(self) -> Dict[str, Any]:
        """Check Voyage AI service health."""
        try:
            # Test embedding
            start_time = time.time()
            response = self.voyage_client.embed(
                texts=["health check test"],
                model="voyage-context-3"
            )
            embedding_latency = (time.time() - start_time) * 1000

            # Test reranking
            start_time = time.time()
            rerank_response = self.voyage_client.rerank(
                query="test query",
                documents=["test document"],
                model="rerank-2.5-lite"
            )
            rerank_latency = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "embedding_service": True,
                "reranking_service": True,
                "embedding_latency_ms": embedding_latency,
                "rerank_latency_ms": rerank_latency,
                "timestamp": int(time.time())
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": int(time.time())
            }

    def check_overall_system(self) -> Dict[str, Any]:
        """Check overall system health."""
        milvus_health = self.check_milvus_health()
        conport_health = self.check_conport_health()
        voyage_health = self.check_voyage_health()

        # Determine overall status
        critical_services = [milvus_health["status"], voyage_health["status"]]
        overall_status = "healthy" if all(s == "healthy" for s in critical_services) else "degraded"

        if conport_health["status"] != "healthy":
            overall_status = "degraded" if overall_status == "healthy" else "unhealthy"

        return {
            "overall_status": overall_status,
            "services": {
                "milvus": milvus_health,
                "conport": conport_health,
                "voyage": voyage_health
            },
            "timestamp": int(time.time())
        }

# Usage example
if __name__ == "__main__":
    config = {
        "voyage_api_key": os.getenv("VOYAGE_API_KEY"),
        "milvus_host": "localhost",
        "milvus_port": 19530,
        "conport_url": "http://localhost:8080"
    }

    monitor = RAGHealthMonitor(config)
    health = monitor.check_overall_system()
    print(json.dumps(health, indent=2))
```

### Key Performance Indicators (KPIs)

#### Critical Metrics
- **Query Latency**: p50 < 500ms, p95 < 2000ms
- **Success Rate**: > 95% for valid queries
- **Milvus Response Time**: < 100ms for vector searches
- **Memory Usage**: < 80% of allocated resources
- **Error Rate**: < 1% of total requests

#### Monitoring Queries
```sql
-- Milvus collection health
SELECT collection_name, num_entities, num_partitions
FROM collections_info;

-- ConPort memory usage
SELECT workspace_id, COUNT(*) as node_count,
       AVG(timestamp) as avg_age
FROM memory_nodes
GROUP BY workspace_id;
```

## Performance Monitoring

### Latency Tracking

```python
# Performance monitoring implementation
import time
from functools import wraps
from collections import defaultdict
import statistics

class PerformanceTracker:
    def __init__(self):
        self.metrics = defaultdict(list)

    def track_latency(self, operation_name):
        """Decorator to track operation latency."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    success = True
                except Exception as e:
                    success = False
                    raise
                finally:
                    latency_ms = (time.time() - start_time) * 1000
                    self.record_metric(operation_name, latency_ms, success)
                return result
            return wrapper
        return decorator

    def record_metric(self, operation: str, latency_ms: float, success: bool):
        """Record performance metric."""
        self.metrics[operation].append({
            "latency_ms": latency_ms,
            "success": success,
            "timestamp": time.time()
        })

        # Keep only last 1000 measurements
        if len(self.metrics[operation]) > 1000:
            self.metrics[operation] = self.metrics[operation][-1000:]

    def get_stats(self, operation: str) -> dict:
        """Get performance statistics for an operation."""
        if operation not in self.metrics:
            return {}

        measurements = self.metrics[operation]
        latencies = [m["latency_ms"] for m in measurements]
        successes = [m["success"] for m in measurements]

        return {
            "count": len(measurements),
            "success_rate": sum(successes) / len(successes) if successes else 0,
            "latency_p50": statistics.median(latencies) if latencies else 0,
            "latency_p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else 0,
            "latency_mean": statistics.mean(latencies) if latencies else 0
        }

# Global tracker instance
perf_tracker = PerformanceTracker()

# Usage in retrieval code
class InstrumentedRetriever(HybridRetriever):
    @perf_tracker.track_latency("hybrid_search")
    def hybrid_search(self, *args, **kwargs):
        return super().hybrid_search(*args, **kwargs)

    @perf_tracker.track_latency("rerank_candidates")
    def rerank_candidates(self, *args, **kwargs):
        return super().rerank_candidates(*args, **kwargs)
```

### Resource Monitoring

```bash
#!/bin/bash
# scripts/monitor_resources.sh

echo "📊 RAG System Resource Usage - $(date)"

# Milvus container resources
echo "🗄️ Milvus Resources:"
docker stats milvus-standalone --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# ConPort container resources
echo "🧠 ConPort Resources:"
docker stats conport-server --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>/dev/null || echo "ConPort not containerized"

# Disk usage
echo "💾 Disk Usage:"
df -h | grep -E "(milvus|conport)"

# Network connections
echo "🌐 Network Connections:"
netstat -an | grep -E "(19530|8080)" | wc -l
```

## Incident Response

### Alert Conditions

#### Critical Alerts (Page Immediately)
- Milvus service down
- Voyage API quota exceeded or service unavailable
- Query success rate < 50%
- Query latency p95 > 10 seconds

#### Warning Alerts (Monitor Closely)
- ConPort memory service unavailable
- Query latency p95 > 5 seconds
- Memory usage > 90%
- High error rate (> 5%)

### Troubleshooting Guide

#### Issue: High Query Latency

**Symptoms**: Query response times > 2 seconds consistently

**Investigation Steps**:
1. Check Milvus query performance:
   ```python
   # Check index status
   from pymilvus import Collection
   collection = Collection("ProjectDocs")
   print(collection.index())
   ```

2. Monitor reranker performance:
   ```bash
   # Check Voyage API latency
   time curl -X POST https://api.voyageai.com/v1/rerank \
     -H "Content-Type: application/json" \
     -d '{"model": "rerank-2.5-lite", "query": "test", "documents": ["test"]}'
   ```

3. Check system resources:
   ```bash
   docker stats --no-stream
   htop
   ```

**Remediation**:
- Reduce `ef` parameter in HNSW search
- Switch to `rerank-2.5-lite` model
- Scale horizontally if needed
- Check for resource contention

#### Issue: Empty Search Results

**Symptoms**: Queries returning no results when they should

**Investigation Steps**:
1. Verify collection entity counts:
   ```python
   from pymilvus import Collection
   docs_collection = Collection("ProjectDocs")
   print(f"Docs entities: {docs_collection.num_entities}")

   code_collection = Collection("ProjectCode")
   print(f"Code entities: {code_collection.num_entities}")
   ```

2. Check workspace isolation:
   ```python
   # Verify workspace filtering
   results = collection.query(
       expr="workspace_id == 'your_workspace'",
       output_fields=["id", "workspace_id"],
       limit=10
   )
   print(f"Workspace results: {len(results)}")
   ```

3. Test embedding similarity:
   ```python
   # Test query embedding
   query_embedding = voyage_client.embed(
       texts=["your test query"],
       model="voyage-context-3"
   ).embeddings[0]

   # Manual similarity search
   results = collection.search(
       data=[query_embedding],
       anns_field="embedding",
       param={"metric_type": "COSINE", "params": {"ef": 256}},
       limit=10
   )
   ```

**Remediation**:
- Re-ingest content if entities are missing
- Check workspace ID consistency
- Verify embedding model consistency
- Lower similarity thresholds temporarily

#### Issue: ConPort Memory Unavailable

**Symptoms**: Memory logging failing, buffered operations growing

**Investigation Steps**:
1. Check ConPort service:
   ```bash
   curl http://localhost:8080/health
   docker logs conport-server
   ```

2. Check database integrity:
   ```bash
   sqlite3 /data/conport/rag-memory.db ".schema"
   sqlite3 /data/conport/rag-memory.db "SELECT COUNT(*) FROM nodes;"
   ```

3. Monitor buffer status:
   ```python
   status = memory_logger.get_buffer_status()
   print(f"Buffered operations: {status['buffered_count']}")
   ```

**Remediation**:
- Restart ConPort service
- Clear corrupted database if needed
- Retry buffered operations
- Continue in degraded mode if necessary

### Incident Response Procedures

#### Step 1: Assess Impact
- Determine affected services and users
- Check if system can operate in degraded mode
- Estimate user impact and urgency

#### Step 2: Immediate Actions
- Switch to degraded mode if needed
- Scale down non-critical operations
- Implement circuit breakers
- Notify stakeholders

#### Step 3: Root Cause Analysis
- Collect relevant logs and metrics
- Identify timeline of events
- Determine contributing factors
- Document findings

#### Step 4: Resolution
- Apply immediate fixes
- Test resolution thoroughly
- Restore full service gradually
- Monitor for stability

#### Step 5: Post-Incident
- Write incident report
- Update runbooks and monitoring
- Implement preventive measures
- Conduct team retrospective

## Maintenance Tasks

### Daily Operations

#### Health Check Routine
```bash
#!/bin/bash
# Daily health check script

echo "🌅 Daily RAG Health Check - $(date)"

# Run comprehensive health check
python scripts/health_monitor.py

# Check performance metrics
python -c "
from scripts.performance_tracker import perf_tracker
print('Performance Summary:')
for op in ['hybrid_search', 'rerank_candidates']:
    stats = perf_tracker.get_stats(op)
    print(f'{op}: {stats}')
"

# Check resource usage
./scripts/monitor_resources.sh

# Check error logs
echo "🔍 Recent Errors:"
docker logs milvus-standalone --since=24h | grep -i error | tail -10
```

#### Buffer Management
```python
# Daily buffer cleanup
def daily_buffer_maintenance():
    """Perform daily buffer maintenance."""

    # Retry buffered operations
    memory_logger.retry_buffered_operations(max_retries=500)

    # Clear old buffer entries (> 24 hours)
    cutoff_time = time.time() - 86400
    memory_logger.operation_buffer = [
        op for op in memory_logger.operation_buffer
        if op["timestamp"] > cutoff_time
    ]

    # Log buffer status
    status = memory_logger.get_buffer_status()
    logger.info(f"Buffer maintenance: {status['buffered_count']} operations remaining")
```

### Weekly Operations

#### Index Optimization
```python
# Weekly index maintenance
def weekly_index_maintenance():
    """Optimize Milvus indices weekly."""

    from pymilvus import Collection

    collections = ["ProjectDocs", "ProjectCode"]

    for collection_name in collections:
        collection = Collection(collection_name)

        # Compact collection
        collection.compact()

        # Check index efficiency
        stats = collection.get_compaction_state()
        logger.info(f"{collection_name} compaction state: {stats}")

        # Rebuild index if needed (based on growth)
        if collection.num_entities > 100000:  # Threshold for rebuild
            logger.info(f"Considering index rebuild for {collection_name}")
```

#### Performance Review
```bash
#!/bin/bash
# Weekly performance review

echo "📊 Weekly RAG Performance Review - $(date)"

# Generate performance report
python -c "
import json
from scripts.performance_tracker import perf_tracker

report = {}
for operation in ['hybrid_search', 'rerank_candidates', 'memory_logging']:
    report[operation] = perf_tracker.get_stats(operation)

print(json.dumps(report, indent=2))
" > weekly_performance_$(date +%Y%m%d).json

# Check for performance degradation
python scripts/performance_analysis.py weekly_performance_*.json
```

### Monthly Operations

#### Capacity Planning
```python
# Monthly capacity analysis
def monthly_capacity_review():
    """Review system capacity monthly."""

    # Analyze growth trends
    collections = ["ProjectDocs", "ProjectCode"]

    for collection_name in collections:
        collection = Collection(collection_name)
        entity_count = collection.num_entities

        # Estimate storage usage
        estimated_size_gb = entity_count * 1.2 / 1000  # Rough estimate

        print(f"{collection_name}:")
        print(f"  Entities: {entity_count:,}")
        print(f"  Estimated size: {estimated_size_gb:.1f} GB")

        # Project growth
        monthly_growth = entity_count * 0.1  # Assume 10% monthly growth
        projected_6_months = entity_count + (monthly_growth * 6)

        print(f"  Projected 6-month entities: {projected_6_months:,.0f}")
```

#### Data Cleanup
```bash
#!/bin/bash
# Monthly data cleanup

echo "🧹 Monthly RAG Data Cleanup - $(date)"

# Clean old logs
find /var/log/rag -name "*.log" -mtime +30 -delete

# Clean temporary files
find /tmp -name "rag_temp_*" -mtime +7 -delete

# Archive old performance data
tar -czf "rag_metrics_$(date +%Y%m).tar.gz" weekly_performance_*.json
rm weekly_performance_*.json

# ConPort database maintenance
sqlite3 /data/conport/rag-memory.db "VACUUM;"
```

## Configuration Management

### Environment Configuration

```bash
# Production environment variables
export VOYAGE_API_KEY="prod_voyage_key"
export MILVUS_HOST="milvus-prod.internal"
export MILVUS_PORT="19530"
export CONPORT_URL="https://conport-prod.internal"

# Performance tuning
export RAG_QUERY_TIMEOUT="30"
export RAG_BATCH_SIZE="100"
export RAG_MAX_CONCURRENT="20"

# Resource limits
export RAG_MEMORY_LIMIT="16GB"
export RAG_CPU_LIMIT="8"
```

### Feature Flags

```python
# Feature flag configuration
FEATURE_FLAGS = {
    "enable_memory_logging": True,
    "enable_query_caching": True,
    "enable_performance_tracking": True,
    "use_rerank_lite_under_load": True,
    "enable_circuit_breakers": True
}

# Usage in code
if FEATURE_FLAGS.get("enable_memory_logging", False):
    memory_logger.log_query_async(query, role, task, session_id, workspace_id)
```

## Emergency Procedures

### System Recovery

#### Milvus Recovery
```bash
#!/bin/bash
# Emergency Milvus recovery

echo "🚨 Emergency Milvus Recovery"

# Stop Milvus
docker-compose down milvus

# Backup current data
cp -r ./data/milvus ./data/milvus_backup_$(date +%Y%m%d_%H%M)

# Start with clean state if corrupted
# docker-compose up milvus

# Restore from backup if needed
# cp -r ./data/milvus_backup_latest/* ./data/milvus/

# Start Milvus
docker-compose up -d milvus

# Verify recovery
python scripts/validate_rag_system.py
```

#### ConPort Recovery
```bash
#!/bin/bash
# Emergency ConPort recovery

echo "🚨 Emergency ConPort Recovery"

# Backup database
cp /data/conport/rag-memory.db /data/conport/rag-memory.db.backup.$(date +%Y%m%d_%H%M)

# Check database integrity
sqlite3 /data/conport/rag-memory.db "PRAGMA integrity_check;"

# Restart service
docker restart conport-server

# If database is corrupted, restore from backup
# cp /data/conport/rag-memory.db.backup.latest /data/conport/rag-memory.db
```

### Degraded Mode Operation

```python
# Degraded mode configuration
class DegradedModeManager:
    def __init__(self):
        self.degraded_mode = False
        self.available_services = set()

    def enable_degraded_mode(self, unavailable_services: List[str]):
        """Enable degraded mode when services are unavailable."""
        self.degraded_mode = True
        self.available_services = {"milvus", "voyage"} - set(unavailable_services)

        if "milvus" not in self.available_services:
            # Critical failure - system cannot operate
            raise SystemError("Milvus unavailable - system cannot operate")

        if "voyage" not in self.available_services:
            # Use cached embeddings or simpler ranking
            logger.warning("Voyage unavailable - using fallback ranking")

        if "conport" not in self.available_services:
            # Disable memory logging, use local buffer only
            logger.warning("ConPort unavailable - memory features disabled")
```

## Related Documentation

- **[RAG System Overview](../../94-architecture/rag/rag-system-overview.md)** - System architecture
- **[Setup Guide](../../02-how-to/rag/setup-rag-pipeline.md)** - Implementation instructions
- **[Milvus Configuration](../../03-reference/rag/milvus-configuration-reference.md)** - Database configuration
- **[ConPort Integration](../../02-how-to/rag/integrate-conport-memory.md)** - Memory system setup

---

**Status**: Runbook Complete
**Last Updated**: 2025-09-23
**Version**: 1.0
**Next Review**: Monthly operational review