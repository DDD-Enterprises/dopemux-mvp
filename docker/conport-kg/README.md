# Dope Decision Graph (formerly ConPort KG)

**Status**: READY TO USE - Implementation DEFERRED (Option A chosen)
**Reason**: Development mode is production-quality

---

## Quick Start (When Ready to Deploy)

### 1. Configure Environment

```bash
cd docker/conport-kg
cp .env.example .env.production

# Edit .env.production with secure passwords
nano .env.production
```

### 2. Deploy

```bash
cd /Users/hue/code/dopemux-mvp
./scripts/deploy-conport-kg.sh  # legacy script name
```

### 3. Verify

```bash
# Health check
curl http://localhost:3016/kg/health

# Test API
curl http://localhost:3016/kg/decisions/recent

# Launch Terminal UI
cd services/conport_kg_ui && npm run dev
```

---

## Services

**PostgreSQL AGE (Decision Graph DB)**:
- Port: 5455
- Database: dopemux_knowledge_graph
- Graph: conport_knowledge
- Health: `docker exec dope-decision-graph-postgres pg_isready`

**DopeconBridge**:
- Port: 3016 (PORT_BASE + 16)
- API: http://localhost:3016/kg
- Health: GET /kg/health

**Redis (Decision Graph cache)**:
- Port: 6379
- Purpose: Event bus and caching
- Health: `docker exec dope-decision-graph-redis redis-cli ping`

---

## Management Commands

### Start Services

```bash
docker-compose -f docker/conport-kg/docker-compose.yml up -d
```

### Stop Services

```bash
docker-compose -f docker/conport-kg/docker-compose.yml down
```

### View Logs

```bash
# All services
docker-compose -f docker/conport-kg/docker-compose.yml logs -f

# Specific service
docker-compose -f docker/conport-kg/docker-compose.yml logs -f dopecon-bridge
```

### Restart Service

```bash
docker-compose -f docker/conport-kg/docker-compose.yml restart dopecon-bridge
```

---

## Backup & Restore

### Manual Backup

```bash
./scripts/backup-conport-kg.sh
```

### Automated Backups (Cron)

```bash
# Add to crontab
crontab -e

# Add this line (daily at 2 AM)
0 2 * * * /Users/hue/code/dopemux-mvp/scripts/backup-conport-kg.sh >> /var/log/dope-decision-graph-backup.log 2>&1
```

### Restore from Backup

```bash
# List available backups
ls -lh /var/backups/dope-decision-graph/

# Restore
./scripts/restore-conport-kg.sh /var/backups/dope-decision-graph/dope-decision-graph-20251002_020000.sql.gz
```

---

## Health Monitoring

### Manual Health Check

```bash
./scripts/health-check-kg.sh
```

### Automated Monitoring (Cron)

```bash
# Add to crontab (every 5 minutes)
*/5 * * * * /Users/hue/code/dopemux-mvp/scripts/health-check-kg.sh >> /var/log/dope-decision-graph-health.log 2>&1
```

### Configure Alerts

```bash
# Set webhook in .env.production
ALERT_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Or in environment
export ALERT_WEBHOOK=https://discord.com/api/webhooks/YOUR/WEBHOOK
./scripts/health-check-kg.sh
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose -f docker/conport-kg/docker-compose.yml logs dopecon-bridge

# Check health
docker ps --filter "name=dope-decision-graph"

# Restart
docker-compose -f docker/conport-kg/docker-compose.yml restart
```

### Database Connection Issues

```bash
# Test connection from DopeconBridge
docker-compose -f docker/conport-kg/docker-compose.yml exec dopecon-bridge \
  python -c "from services.conport_kg.age_client import AGEClient; AGEClient()"
```

### Performance Issues

```bash
# Check connection pool
docker-compose -f docker/conport-kg/docker-compose.yml logs dopecon-bridge | grep "Pool stats"

# Check query times
curl -w "Time: %{time_total}s\n" http://localhost:3016/kg/decisions/recent
```

---

## File Inventory

**Configuration**:
- docker-compose.yml (Docker orchestration)
- .env.example (environment template)

**Scripts** (in /scripts):
- deploy-conport-kg.sh (one-command deployment)
- backup-conport-kg.sh (automated backups)
- restore-conport-kg.sh (database restoration)
- health-check-kg.sh (health monitoring)

**Documentation**:
- docs/PHASE-11-PRODUCTION-DEPLOYMENT-PLAN.md (complete plan)
- This README.md (quick reference)

---

## When to Deploy

**Deploy to Production When**:
- Multiple concurrent users expected
- Need automated backup/restore
- Want single-command startup: `docker-compose up`
- Preparing for external access
- Team scaling beyond solo developer

**Current Status**: Development mode works perfectly, no urgent need to deploy

---

**Status**: READY BUT NOT DEPLOYED (Option A - defer until needed)
