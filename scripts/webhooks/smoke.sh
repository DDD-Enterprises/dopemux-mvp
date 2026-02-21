#!/usr/bin/env bash
set -eo pipefail

echo "==========================================="
echo "   Webhook Receiver Smoke Tests            "
echo "==========================================="

echo "1. Checking Local Health..."
LOCAL_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8790/healthz || echo "failed")
if [ "$LOCAL_STATUS" = "200" ]; then
    echo "   [✓] Local health ok (200)"
else
    echo "   [✗] Local health failed: $LOCAL_STATUS"
    exit 1
fi

echo "2. Checking Public Health (Cloudflare Tunnel)..."
PUBLIC_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://webhooks.krohman.org/healthz || echo "failed")
if [ "$PUBLIC_STATUS" = "200" ]; then
    echo "   [✓] Public health ok (200)"
else
    echo "   [✗] Public health failed: $PUBLIC_STATUS"
    exit 1
fi

echo ""
echo "3. Webhook Delivery Test"
echo "   Please use the OpenAI dashboard to send a test event to:"
echo "   https://webhooks.krohman.org/webhook/openai"
echo "   "
echo "   To verify deduplication, resend the EXACT same test event."
echo "   Then check the logs with 'make webhook-logs' to see 'duplicate ignored'."
echo ""

echo "4. Checking Database Rows..."
python3 "$(dirname "$0")/db_query.py" || true

echo ""
echo "==========================================="
echo "   PASS                                    "
echo "==========================================="
