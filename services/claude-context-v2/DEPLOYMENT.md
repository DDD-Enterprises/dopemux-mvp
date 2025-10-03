# Dope-Context Deployment Guide

Production deployment instructions for Docker, Docker Compose, and Claude Code integration.

---

## Prerequisites

### Required
- Python 3.11+
- Docker & Docker Compose (for Qdrant)
- Voyage AI API key ([get one here](https://www.voyageai.com/))

### Optional
- Anthropic API key (improves context quality by 35-67%)

---

## Quick Start (Local Development)

### 1. Start Qdrant

```bash
# Using Docker
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant

# Or using Docker Compose (recommended)
cd services/claude-context-v2
docker-compose up -d
```

### 2. Install Dependencies

```bash
cd services/claude-context-v2

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Create .env file
cat > .env <<EOF
VOYAGE_API_KEY=pa-your-voyage-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
QDRANT_URL=localhost
QDRANT_PORT=6333
EOF

# Load environment
export $(cat .env | xargs)
```

### 4. Test Server

```bash
# Run server directly
python src/mcp/server.py

# Should see:
# [INFO] Dope-Context MCP server starting...
# [MCP] Server running on stdio transport
```

---

## Claude Code Integration

### Method 1: Using Claude CLI

```bash
claude mcp add dope-context \
  -e VOYAGE_API_KEY=pa-your-key \
  -e ANTHROPIC_API_KEY=sk-ant-your-key \
  -e QDRANT_URL=localhost \
  -e QDRANT_PORT=6333 \
  -- python /Users/hue/code/dopemux-mvp/services/claude-context-v2/src/mcp/server.py
```

### Method 2: Manual Configuration

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dope-context": {
      "command": "python",
      "args": [
        "/Users/hue/code/dopemux-mvp/services/claude-context-v2/src/mcp/server.py"
      ],
      "env": {
        "VOYAGE_API_KEY": "pa-your-voyage-api-key",
        "ANTHROPIC_API_KEY": "sk-ant-your-anthropic-key",
        "QDRANT_URL": "localhost",
        "QDRANT_PORT": "6333"
      }
    }
  }
}
```

### Method 3: Using Virtual Environment

```json
{
  "mcpServers": {
    "dope-context": {
      "command": "/Users/hue/code/dopemux-mvp/services/claude-context-v2/venv/bin/python",
      "args": [
        "/Users/hue/code/dopemux-mvp/services/claude-context-v2/src/mcp/server.py"
      ],
      "env": {
        "VOYAGE_API_KEY": "pa-your-key",
        "ANTHROPIC_API_KEY": "sk-ant-your-key"
      }
    }
  }
}
```

### Restart Claude Code

```bash
# Restart Claude Code to load new MCP server
# Tools should appear in Claude Code's MCP tools list
```

---

## Docker Deployment

### Option 1: Docker Compose (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: dope-qdrant
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__STORAGE__MMAP_THRESHOLD=1000000
    restart: unless-stopped

  dope-context:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: dope-context-mcp
    environment:
      - VOYAGE_API_KEY=${VOYAGE_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - QDRANT_URL=qdrant
      - QDRANT_PORT=6333
    volumes:
      - ${HOME}/.dope-context:/root/.dope-context
      - ${WORKSPACE_PATH}:/workspace:ro
    depends_on:
      - qdrant
    stdin_open: true
    tty: true
```

### Option 2: Standalone Docker Container

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY config/ ./config/

# Set Python path
ENV PYTHONPATH=/app

# Run MCP server
CMD ["python", "src/mcp/server.py"]
```

**Build and Run:**

```bash
# Build image
docker build -t dope-context:latest .

# Run container
docker run -d \
  --name dope-context-mcp \
  -e VOYAGE_API_KEY=your-key \
  -e ANTHROPIC_API_KEY=your-key \
  -e QDRANT_URL=qdrant \
  -e QDRANT_PORT=6333 \
  -v ~/.dope-context:/root/.dope-context \
  --link qdrant:qdrant \
  dope-context:latest
```

---

## Production Deployment

### 1. Qdrant Setup

**Option A: Qdrant Cloud** (managed, recommended for production)

```bash
# Sign up at cloud.qdrant.io
# Get cluster URL and API key

# Configure
export QDRANT_URL=https://your-cluster.qdrant.io
export QDRANT_API_KEY=your-api-key
```

**Option B: Self-Hosted Qdrant Cluster**

```yaml
# qdrant-cluster.yml
version: '3.8'

services:
  qdrant-node-1:
    image: qdrant/qdrant:latest
    environment:
      - QDRANT__CLUSTER__ENABLED=true
      - QDRANT__CLUSTER__NODE_ID=1
    volumes:
      - ./qdrant_storage_1:/qdrant/storage

  qdrant-node-2:
    image: qdrant/qdrant:latest
    environment:
      - QDRANT__CLUSTER__ENABLED=true
      - QDRANT__CLUSTER__NODE_ID=2
      - QDRANT__CLUSTER__BOOTSTRAP__NODE_URL=http://qdrant-node-1:6335
    volumes:
      - ./qdrant_storage_2:/qdrant/storage

  # Add more nodes as needed
```

### 2. Production Environment Variables

```bash
# .env.production
VOYAGE_API_KEY=pa-prod-key
ANTHROPIC_API_KEY=sk-ant-prod-key
QDRANT_URL=https://prod-cluster.qdrant.io
QDRANT_API_KEY=prod-qdrant-key

# Performance tuning
EMBEDDING_BATCH_SIZE=16
CONTEXT_BATCH_SIZE=20
QDRANT_BATCH_SIZE=200

# Caching
EMBEDDING_CACHE_TTL_HOURS=168
CONTEXT_CACHE_TTL_HOURS=2160
```

### 3. Health Checks

```python
# Add to server.py
@mcp.tool()
async def health() -> Dict:
    """Health check for monitoring."""
    try:
        # Check Qdrant
        collections = await client.get_collections()

        # Check Voyage
        test_embedding = await embedder.embed("test", model="voyage-code-3")

        return {
            "status": "healthy",
            "qdrant": "connected",
            "voyage": "connected",
            "collections": len(collections.collections)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

### 4. Monitoring

**Prometheus Metrics** (optional):

```python
from prometheus_client import Counter, Histogram, start_http_server

# Metrics
search_latency = Histogram('dope_context_search_latency_seconds', 'Search latency')
embedding_calls = Counter('dope_context_embedding_calls_total', 'Embedding API calls')
cache_hits = Counter('dope_context_cache_hits_total', 'Cache hits')

# Instrument
@search_latency.time()
async def search_code(...):
    ...
```

---

## Security

### API Key Management

**Never commit keys to git:**
```bash
# Add to .gitignore
.env
.env.*
*.key
```

**Use environment variables:**
```bash
# Load from secure storage
export VOYAGE_API_KEY=$(cat /secure/voyage.key)
```

**Docker secrets** (Docker Swarm/Kubernetes):
```yaml
services:
  dope-context:
    secrets:
      - voyage_api_key
      - anthropic_api_key

secrets:
  voyage_api_key:
    file: ./secrets/voyage.key
  anthropic_api_key:
    file: ./secrets/anthropic.key
```

### Snapshot Directory Permissions

```bash
# Ensure snapshots are user-only
chmod 700 ~/.dope-context/snapshots/

# In Dockerfile
RUN mkdir -p /root/.dope-context/snapshots && \
    chmod 700 /root/.dope-context
```

### Network Security

**Production Qdrant:**
```yaml
qdrant:
  environment:
    - QDRANT__SERVICE__API_KEY=secure-random-key
    - QDRANT__SERVICE__ENABLE_TLS=true
```

**Access Control:**
```python
# Add API key to Qdrant client
client = AsyncQdrantClient(
    url="https://prod.qdrant.io",
    api_key=os.getenv("QDRANT_API_KEY")
)
```

---

## Backup and Recovery

### Backup Qdrant Collections

```bash
# Create snapshot
docker exec qdrant curl -X POST \
  http://localhost:6333/collections/code_3ca12e07/snapshots

# Download snapshot
docker cp qdrant:/qdrant/storage/snapshots/code_3ca12e07-*.snapshot \
  ./backups/
```

### Backup Sync Snapshots

```bash
# Snapshots are in ~/.dope-context/snapshots/
tar -czf dope-context-snapshots-$(date +%Y%m%d).tar.gz \
  ~/.dope-context/snapshots/

# Restore
tar -xzf dope-context-snapshots-20251003.tar.gz -C ~/
```

### Disaster Recovery

```bash
# 1. Restore Qdrant snapshots
# 2. Restore sync snapshots
# 3. Run sync to detect any new changes since backup
sync_workspace("/path/to/workspace")
```

---

## Multi-User Deployment

### Shared Qdrant, Per-User Workspaces

**Architecture:**
```
Qdrant Instance (shared)
├─ user1_code_workspace_a
├─ user1_docs_workspace_a
├─ user2_code_workspace_b
└─ user2_docs_workspace_b
```

**Configuration:**
```python
# Add user ID to collection name
def get_collection_names(workspace_path, user_id):
    hash_val = workspace_to_hash(workspace_path)
    return (
        f"{user_id}_code_{hash_val}",
        f"{user_id}_docs_{hash_val}"
    )
```

### Kubernetes Deployment

**Deployment YAML:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dope-context
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dope-context
  template:
    metadata:
      labels:
        app: dope-context
    spec:
      containers:
      - name: dope-context
        image: dope-context:latest
        env:
        - name: VOYAGE_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: voyage
        - name: QDRANT_URL
          value: "qdrant-service.default.svc.cluster.local"
        volumeMounts:
        - name: snapshots
          mountPath: /root/.dope-context
      volumes:
      - name: snapshots
        persistentVolumeClaim:
          claimName: dope-context-snapshots
```

---

## Upgrade and Migration

### Upgrading Dope-Context

```bash
# 1. Backup snapshots
tar -czf backup-$(date +%Y%m%d).tar.gz ~/.dope-context/

# 2. Pull new version
git pull origin main

# 3. Update dependencies
pip install -r requirements.txt --upgrade

# 4. Restart server
# (Claude Code will automatically reload)
```

### Migrating from Shared Collections

If you have existing data in shared `code_index` collection:

```python
# migration_script.py
async def migrate_to_per_workspace():
    # 1. Get all points from old collection
    old_points = await old_client.scroll(
        collection_name="code_index",
        limit=10000,
        with_payload=True
    )

    # 2. Group by workspace_id
    by_workspace = {}
    for point in old_points:
        workspace_id = point.payload.get("workspace_id")
        if workspace_id not in by_workspace:
            by_workspace[workspace_id] = []
        by_workspace[workspace_id].append(point)

    # 3. Create new collections and insert
    for workspace_id, points in by_workspace.items():
        workspace_hash = workspace_to_hash(Path(workspace_id))
        new_collection = f"code_{workspace_hash}"

        await create_collection(new_collection)
        await insert_points(new_collection, points)

    print(f"Migrated {len(by_workspace)} workspaces")
```

---

## Troubleshooting

### Server Won't Start

**Check logs:**
```bash
# If running via Docker
docker logs dope-context-mcp

# If running directly
python src/mcp/server.py 2>&1 | tee server.log
```

**Common issues:**
1. Missing API keys: Check `VOYAGE_API_KEY`
2. Qdrant not running: `docker ps | grep qdrant`
3. Port conflicts: Change `QDRANT_PORT`
4. Python version: Requires 3.11+

### Can't Connect to Qdrant

```bash
# Test Qdrant connection
curl http://localhost:6333/health

# Should return: {"title":"qdrant - vector search engine","version":"1.x.x"}

# Check Qdrant logs
docker logs qdrant

# Restart Qdrant
docker restart qdrant
```

### Claude Code Doesn't See Tools

```bash
# 1. Check MCP config
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 2. Check server process
ps aux | grep "dope-context"

# 3. Restart Claude Code completely
# (Quit and reopen, not just reload)

# 4. Check Claude Code logs
tail -f ~/Library/Logs/Claude/mcp*.log
```

### High Memory Usage

```bash
# Check Qdrant memory
docker stats qdrant

# Optimize Qdrant
docker exec qdrant curl -X PATCH \
  http://localhost:6333/collections/code_3ca12e07 \
  -H 'Content-Type: application/json' \
  -d '{"quantization_config": {"scalar": {"type": "int8"}}}'

# Clear Python caches
# (Restart server)
```

---

## Performance Monitoring

### Log Analysis

```bash
# Search for slow queries
grep "Search took" ~/.claude/logs/dope-context.log | \
  awk '{print $NF}' | \
  sort -n | \
  tail -10

# Count cache hits
grep "Cache hit" ~/.claude/logs/dope-context.log | wc -l
```

### Qdrant Metrics

```bash
# Collection stats
curl http://localhost:6333/collections/code_3ca12e07

# Cluster info
curl http://localhost:6333/cluster

# Telemetry
curl http://localhost:6333/telemetry
```

---

## Best Practices

### 1. Resource Limits

```yaml
# docker-compose.yml
services:
  qdrant:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
        reservations:
          memory: 2G
          cpus: '1'
```

### 2. Backup Schedule

```bash
# Cron job for daily backups
0 2 * * * /usr/local/bin/backup-dope-context.sh

# backup-dope-context.sh
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf /backups/snapshots-$DATE.tar.gz ~/.dope-context/snapshots/
docker exec qdrant curl -X POST http://localhost:6333/snapshots/all
```

### 3. Log Rotation

```bash
# logrotate config
/var/log/dope-context/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 640 root adm
}
```

### 4. Rate Limiting

```python
# Add rate limiting to MCP tools
from fastmcp.rate_limit import RateLimiter

limiter = RateLimiter(max_calls=100, period=60)  # 100 calls/minute

@mcp.tool()
@limiter.limit
async def search_code(...):
    ...
```

---

## Scaling Guide

### Small Team (1-5 users, 10-50 workspaces)

- **Qdrant**: Single instance, 4GB RAM
- **Dope-Context**: Single server
- **Cost**: ~$20-50/month (Qdrant Cloud + API calls)

### Medium Team (5-20 users, 50-200 workspaces)

- **Qdrant**: Cluster (3 nodes), 8GB RAM each
- **Dope-Context**: Load balanced (2-3 instances)
- **Cost**: ~$100-300/month

### Large Organization (20+ users, 200+ workspaces)

- **Qdrant**: Cluster (5+ nodes), 16GB RAM each
- **Dope-Context**: Auto-scaling (Kubernetes HPA)
- **Cost**: ~$500-2000/month

---

## Next Steps

After deployment:

1. **Index your workspaces**: Run `index_workspace` for each project
2. **Set up sync**: Add to git hooks or cron
3. **Monitor performance**: Track latencies and costs
4. **Tune parameters**: Adjust based on usage patterns

For questions: See [README.md](README.md) and [API_REFERENCE.md](API_REFERENCE.md)
