# Runbook: Zero-Touch Sync Operations

**Version:** 1.0
**Last Updated:** 2025-09-25
**Maintainer:** Dopemux Platform Team

## Quick Reference

### Service Status
```bash
# Check sync service health
curl -f http://localhost:8080/health

# View current sync status
dopemux sync status

# Check all system connectivity
dopemux sync connectivity-test
```

### Emergency Commands
```bash
# Stop sync immediately
dopemux sync stop

# Emergency rollback of last sync
dopemux sync rollback --last

# Force manual review queue processing
dopemux sync process-queue --manual
```

## Service Overview

The Zero-Touch Sync service maintains data consistency between Leantime, Task-Master, and ConPort through a polling-based synchronization loop with conflict resolution.

### Core Components
- **Sync Loop**: Polls systems every 300s by default
- **Conflict Resolver**: Handles data inconsistencies using precedence rules
- **Review Queue**: Manual intervention for complex conflicts
- **ADHD Features**: Top-3 Today, Daily Digest, Batch Logging

## Installation & Setup

### Prerequisites
```bash
# Required tools
uvx --version  # For Task-Master and ConPort
curl --version # For health checks
docker --version # For containerized deployment

# API access
export LEANTIME_URL="https://your-leantime.com"
export LEANTIME_TOKEN="your_pat_token"
```

### Environment Configuration
```bash
# Core sync settings
export SYNC_INTERVAL_SEC=300
export LEANTIME_URL="https://leantime.dopemux.com"
export LEANTIME_TOKEN="lt_pat_xxx"
export TASKMASTER_CMD="uvx task-master-ai"
export CONPORT_CMD="uvx --from context-portal-mcp conport-mcp --mode stdio"

# ADHD optimizations
export TOP3_TODAY_ENABLED=true
export DAILY_DIGEST_TIME="09:00"
export BATCH_LOG_ENABLED=true

# Reliability settings
export MAX_RETRIES=3
export BACKOFF_MULTIPLIER=1.5
export HEALTH_CHECK_INTERVAL=60
```

### Quick Start
```bash
# 1. Inventory only (dry run)
dopemux sync inventory \
  --leantime $LEANTIME_URL --lt-token $LEANTIME_TOKEN \
  --taskmaster "$TASKMASTER_CMD" \
  --conport "$CONPORT_CMD" \
  --inflight-only

# 2. Start minimal sync (status only)
dopemux sync loop --interval 300 --mode minimal \
  --status-owner leantime --merge lww --batch-conport

# 3. Enable full sync with ADHD features
dopemux sync prefs --top3-today on --daily-digest 09:00 --batch-log on
dopemux sync loop --interval 300 --mode full
```

## Daily Operations

### Morning Checklist
```bash
# 1. Check service health
curl -s http://localhost:8080/health | jq '.status'

# 2. Review overnight sync activity
dopemux sync logs --since yesterday --summary

# 3. Check review queue length
dopemux sync queue status

# 4. Verify Top-3 Today generation
dopemux sync top3 --verify-today
```

### Monitoring Commands
```bash
# Real-time sync status
watch -n 30 'dopemux sync status'

# View recent conflicts
dopemux sync conflicts --last 24h

# System connectivity check
dopemux sync health-check --all-systems

# Performance metrics
dopemux sync metrics --last 1h
```

## Troubleshooting

### Common Issues

#### 1. Sync Service Not Running
```bash
# Symptoms
curl: (7) Failed to connect to localhost port 8080: Connection refused

# Diagnosis
ps aux | grep "dopemux sync"
docker ps | grep zero-touch-sync

# Resolution
# If Docker deployment:
docker-compose up -d sync-service

# If local deployment:
dopemux sync start --daemon
```

#### 2. High Conflict Rate
```bash
# Symptoms
dopemux sync queue status
# Output: "Queue length: 25 items (WARNING: >10)"

# Diagnosis
dopemux sync conflicts --analyze --last 4h
# Look for patterns in conflict types

# Resolution
# Review and resolve conflicts:
dopemux sync queue process --interactive

# Adjust conflict thresholds if needed:
dopemux sync config set simultaneous_edit_threshold 120  # 2 minutes
```

#### 3. System Connectivity Issues
```bash
# Symptoms
ERROR: Failed to connect to Leantime: Connection timeout
ERROR: Task-Master MCP unavailable

# Diagnosis
dopemux sync connectivity-test --verbose

# Resolution for Leantime:
curl -v "$LEANTIME_URL/api/v1/health"
# Check token validity:
curl -H "Authorization: Bearer $LEANTIME_TOKEN" "$LEANTIME_URL/api/v1/user/me"

# Resolution for Task-Master:
uvx task-master-ai --version
uvx task-master-ai list-tasks  # Test basic functionality

# Resolution for ConPort:
uvx --from context-portal-mcp conport-mcp --help
```

#### 4. Slow Sync Performance
```bash
# Symptoms
Sync pass taking >60 seconds consistently

# Diagnosis
dopemux sync metrics --performance --last 1h
dopemux sync logs --grep "sync_pass_duration" --last 1h

# Resolution
# Increase polling interval:
dopemux sync config set interval 600  # 10 minutes

# Enable parallel processing:
dopemux sync config set parallel_systems true

# Check system response times:
dopemux sync benchmark --all-systems
```

### Error Code Reference

| Code | Meaning | Action |
|------|---------|--------|
| SYNC_001 | Leantime API unavailable | Check network, token, service status |
| SYNC_002 | Task-Master MCP error | Verify uvx installation, permissions |
| SYNC_003 | ConPort connection failed | Check MCP stdio connectivity |
| SYNC_004 | Conflict resolution timeout | Increase timeout, check queue |
| SYNC_005 | Data integrity violation | Run consistency check, manual review |

## Maintenance Procedures

### Weekly Maintenance
```bash
# 1. Archive old audit logs
dopemux sync archive --older-than 30d

# 2. Review conflict patterns
dopemux sync analyze --conflicts --last 7d

# 3. Update performance baselines
dopemux sync benchmark --update-baselines

# 4. Backup sync configuration
dopemux sync config export > sync-config-backup.json
```

### Monthly Maintenance
```bash
# 1. Full system consistency check
dopemux sync verify --full-consistency --fix-minor

# 2. Review and tune sync intervals
dopemux sync analyze --performance --last 30d
# Adjust intervals based on activity patterns

# 3. Update conflict resolution rules if needed
dopemux sync config review-rules

# 4. Rotate API tokens
# (Manual process - update environment variables)
```

### Configuration Updates
```bash
# View current config
dopemux sync config show

# Update specific settings
dopemux sync config set sync_interval 450  # 7.5 minutes
dopemux sync config set top3_enabled false
dopemux sync config set max_retries 5

# Validate configuration
dopemux sync config validate

# Restart with new config
dopemux sync restart
```

## ADHD Feature Management

### Top-3 Today Configuration
```bash
# Enable/disable Top-3 generation
dopemux sync feature top3-today enable
dopemux sync feature top3-today disable

# Customize Top-3 criteria
dopemux sync config set top3_criteria "priority,deadline,blockers"
dopemux sync config set top3_max_items 3

# Force regenerate today's Top-3
dopemux sync top3 --regenerate --post-to-leantime
```

### Daily Digest Settings
```bash
# Configure digest timing
dopemux sync config set daily_digest_time "09:00"
dopemux sync config set digest_timezone "America/Vancouver"

# Customize digest content
dopemux sync config set digest_include "completed,blocked,new"

# Send test digest
dopemux sync digest --test --send-to-email admin@dopemux.com
```

### Batch Logging Control
```bash
# Enable batch logging to reduce noise
dopemux sync config set batch_log_enabled true
dopemux sync config set batch_size 10
dopemux sync config set batch_timeout 300  # 5 minutes

# Force flush pending batch
dopemux sync batch-log --flush-now
```

## Performance Tuning

### Optimize for Different Scenarios

#### High Activity Environment
```bash
# Shorter intervals, parallel processing
dopemux sync config set sync_interval 180  # 3 minutes
dopemux sync config set parallel_systems true
dopemux sync config set batch_size 20
```

#### Low Activity Environment
```bash
# Longer intervals, conservative settings
dopemux sync config set sync_interval 900  # 15 minutes
dopemux sync config set parallel_systems false
dopemux sync config set batch_size 5
```

#### ADHD-Optimized Settings
```bash
# Focus on reducing cognitive load
dopemux sync config set top3_enabled true
dopemux sync config set batch_log_enabled true
dopemux sync config set conflict_auto_resolve true
dopemux sync config set digest_format "simple"
```

## Backup & Recovery

### Backup Procedures
```bash
# Backup sync configuration
dopemux sync config export > backup/sync-config-$(date +%Y%m%d).json

# Backup audit logs
tar -czf backup/sync-audit-logs-$(date +%Y%m%d).tar.gz logs/

# Backup review queue data
dopemux sync queue export > backup/review-queue-$(date +%Y%m%d).json
```

### Recovery Procedures
```bash
# Restore configuration
dopemux sync config import backup/sync-config-20250925.json

# Restore review queue
dopemux sync queue import backup/review-queue-20250925.json

# Verify system consistency after restore
dopemux sync verify --full-check --report-only
```

## Monitoring & Alerting

### Key Metrics to Monitor
```bash
# Service availability
curl -f http://localhost:8080/health

# Sync performance
dopemux sync metrics sync_pass_duration_seconds

# Conflict rate
dopemux sync metrics sync_conflicts_total

# Queue length
dopemux sync metrics review_queue_length
```

### Alert Conditions
- Sync service down for >2 minutes
- Review queue length >10 items
- Sync duration >60 seconds consistently
- Error rate >5% over 5 minutes
- Any system unreachable for >5 minutes

## Emergency Procedures

### Complete System Outage
1. **Stop sync service** to prevent further conflicts
2. **Document current state** of all systems
3. **Identify root cause** (network, auth, system failure)
4. **Restore connectivity** to each system individually
5. **Run consistency check** before resuming sync
6. **Resume sync** with increased monitoring

### Data Corruption Detection
1. **Immediately stop sync**
2. **Export current state** from all systems
3. **Run data integrity checks**
4. **Restore from last known good backup** if needed
5. **Perform manual reconciliation**
6. **Resume with enhanced validation**

## Contact & Escalation

### Primary Contacts
- **Platform Team**: platform@dopemux.com
- **On-Call Engineer**: +1-555-DOPEMUX
- **Escalation Manager**: ops-manager@dopemux.com

### Support Channels
- **Urgent Issues**: #dopemux-urgent (Slack)
- **General Support**: #dopemux-platform (Slack)
- **Bug Reports**: GitHub Issues

## References

- [RFC: Zero-Touch Sync](../01-decisions/RFC-zero-touch-sync.md)
- [Architecture: Zero-Touch Sync](../94-architecture/zero-touch-sync-architecture.md)
- [ADR-040: Sync Mechanism](../90-adr/040-sync-mechanism-polling-mcp.md)
- [ADR-041: Conflict Resolution](../90-adr/041-conflict-resolution-lww-precedence.md)

---

*This runbook is maintained by the Dopemux Platform Team. For updates or corrections, please submit a PR or contact the team directly.*