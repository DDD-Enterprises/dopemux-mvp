---
id: pm-plane-runtime-recovery
title: PM Plane Runtime Recovery
type: tutorial
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-11'
last_review: '2026-03-11'
next_review: '2026-06-11'
status: active
prelude: Concrete runbook for detecting and clearing rogue runtimes, interpreting readiness endpoints, and dealing with pending reconciliation.
---
# PM Plane Runtime Recovery

This runbook provides actionable steps for recovering from PM-plane drift, rogue runtime containers, and dealing with pending reconciliation states. It addresses the `PM-TO-004` rogue container remediation requirement.

## 1. Symptoms

You are likely experiencing a PM-plane runtime or synchronization issue if:
- A PM-plane readiness endpoint (`/health`) returns `degraded` or `fail`.
- A canonical write succeeded but the mirror write failed.
- The `pm_reconciliation_pending_total` metric is consistently growing without resolving.
- The wrong runtime version or port is responding to `task-orchestrator` requests.
- Duplicate or rogue service instances are actively serving traffic, resulting in race conditions.

## 2. Detection Steps

### Check Readiness Endpoints
Both `task-orchestrator` and `dopecon-bridge` expose a standard `/health` endpoint:
```bash
# Check Task Orchestrator (Canonical Port: 8000)
curl -s http://localhost:8000/health | jq .
# Expect: { "status": "ok", "service": "task-orchestrator", "dependencies": {...} }

# Check Dopecon-Bridge
curl -s http://localhost:3016/health | jq .
# Expect: { "status": "healthy", ... }
```

### Confirm Runtime Identity and Port
To ensure you are not hitting a stale runtime answering on the canonical port:
```bash
curl -s http://localhost:8000/info | jq .version
```

### Inspect Rogue Containers
If a rogue/stale `task-orchestrator` container from an old `docker compose` or direct execution is blocking the port or executing stray sync workflows:
```bash
docker ps | grep task-orchestrator
lsof -i :8000
lsof -i :3014 # Check the legacy port as well
```

### Distinguish Canonical vs Mirror Failure
If metrics show failures, check the structured application logs to see exactly what failed:
```bash
# Identify if it was a Canonical Failure or a Mirror Failure
grep -E "PM Write | Mirror Failure" logs/task-orchestrator.log
```
- If `canonical_success=False`, the primary system failed to accept the write. This is a critical workflow block.
- If `Mirror Failure (Reconciliation Pending)`, the primary state is saved but the mirror system missed the update.

## 3. Cleanup / Recovery

### Stop Rogue Runtimes
If you found stray containers or loose process IDs:
```bash
# Kill old docker containers aggressively
docker rm -f $(docker ps -aq --filter "name=task-orchestrator")

# Kill processes holding the port
kill -9 $(lsof -t -i :8000)
kill -9 $(lsof -t -i :3014)
```

### Restart Canonical Runtime
Use the provided shell scripts or docker compose command:
```bash
# Recommended
scripts/start.sh task-orchestrator

# Or Compose
docker compose -f compose.yml up -d task-orchestrator
```

### Verify Sanctioned Runtime
Wait a few seconds, then verify the canonical instance is up and is the *only* one running:
```bash
curl -s http://localhost:8000/health | jq .status
```

## 4. Reconciliation Follow-Up

### Identify Pending Items
When a mirror fails, the task or workflow item enters a `PARTIAL` reconciliation state. Currently, this relies on finding the mirror failures in the structured logs, or reading the Prometheus metrics:
```bash
curl -s http://localhost:8000/metrics | grep pm_reconciliation_pending_total
```
Find the exact `canonical_id` that failed by querying logs for `Mirror Failure (Reconciliation Pending)`.

### Retry / Replay
Depending on the specific subsystem, retry the operation or manually apply the state in the mirror system.
If `dope-memory` was the failed mirror, you can re-submit the chronicle append manually or via a script using the `canonical_id`.

### Confirm Degraded Became Healthy
Once manual updates have been synced to the mirror system, the system should operate cleanly on the next PM-plane operations. (Ensure `pm_reconciliation_pending_total` stabilizes).

## 5. Escalation / Rollback

### When to Halt Writes
If `task-orchestrator` canonical writes consistently fail (e.g., `Leantime` or `ConPort` as the primary authority is unreachable), halt operations dependent on PM-plane modifications. Do not attempt to construct "shadow" authority tables.

### When to Preserve Canonical-Only Behavior
If the mirror system is down (e.g., `dope-memory` is unavailable) but canonical writes are succeeding, you may elect to continue operations in a degraded state. The workflow authority will progress normally, but historical logs will require back-filling from the workflow engine once the mirror system returns.
