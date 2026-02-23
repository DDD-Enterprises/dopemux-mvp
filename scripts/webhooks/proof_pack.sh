#!/usr/bin/env bash
set -eo pipefail

echo "==========================================="
echo "   DPMX Webhook Operator Proof Pack        "
echo "==========================================="
echo "Generated at: $(date)"
echo ""

# 1. Connectivity Checks
echo "[1/4] Connectivity Checks"
echo -n "  Local health:  "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8790/healthz | grep 200 >/dev/null && echo "✓ OK (200)" || echo "✗ FAILED"

echo -n "  Public health: "
curl -s -o /dev/null -w "%{http_code}" https://webhooks.krohman.org/healthz | grep 200 >/dev/null && echo "✓ OK (200)" || echo "✗ FAILED"
echo ""

# 2. Security Rejection Logic
echo "[2/4] Security Rejection Checks"
echo -n "  Rejects missing webhook-id:  "
curl -s -o /dev/null -X POST -w "%{http_code}" https://webhooks.krohman.org/webhook/openai | grep 400 >/dev/null && echo "✓ OK (400)" || echo "✗ FAILED"

echo -n "  Rejects invalid signature:   "
curl -s -o /dev/null -X POST -H "webhook-id: test-id" -w "%{http_code}" https://webhooks.krohman.org/webhook/openai | grep 401 >/dev/null && echo "✓ OK (401)" || echo "✗ FAILED"
echo ""

# 3. Infrastructure Checks
echo "[3/4] Infrastructure Checks"
echo -n "  LaunchAgent status: "
launchctl list com.cloudflare.dopemux-webhooks >/dev/null 2>&1 && echo "✓ OK (Running)" || echo "✗ FAILED (Not Loaded)"

# 4. Database Ledger Stats
echo "[4/4] Database Ledger Stats"
# Use admin.py from the service directory
docker exec dopemux-webhook-receiver python3 /app/services/webhook_receiver/admin.py db stats 2>/dev/null || (echo "  (Service down, checking local sqlite if configured...)" && ls -l services/webhook_receiver/webhook_ledger.db 2>/dev/null || echo "  (Local DB not found)")
echo ""

echo "==========================================="
echo "   Verification Complete                   "
echo "==========================================="
