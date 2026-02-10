#!/bin/bash
# G30 Runtime Fixes Verification Script

echo "=== G30 Smoke Stack Runtime Verification ==="
echo

echo "1. Container Status:"
docker compose -p smoke-g30 -f docker-compose.smoke.yml ps | grep -E "(conport|task-orchestrator|dopecon-bridge)"
echo

echo "2. Health Endpoints:"
echo "  conport (8005):"
curl -s http://localhost:8005/health | jq -c '{status, service, ts}'
echo "  task-orchestrator (3014):"
curl -s http://localhost:3014/health | jq -c '{status, service, ts}'
echo "  dopecon-bridge (3016):"
curl -s http://localhost:3016/health | jq -c '{status, service, ts}'
echo

echo "3. Health Audit:"
python tools/ports_health_audit.py --mode runtime --services conport,task-orchestrator,dopecon-bridge 2>&1 | grep -A 10 "Runtime Summary"
echo

echo "=== Verification Complete ==="
