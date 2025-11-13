#!/bin/bash
# Test ConPort → DopeconBridge EventBus integration

echo "🧪 Testing ConPort → EventBus Integration"
echo "=========================================="
echo ""

# Clear existing events for clean test
echo "🧹 Clearing dopemux:events stream..."
docker exec dopemux-redis-primary redis-cli DEL "dopemux:events"
echo ""

# Test 1: log_decision via HTTP API
echo "1️⃣ Testing log_decision → decision_logged event..."
curl -s -X POST http://localhost:3004/api/decisions \
  -H "Content-Type: application/json" \
  -d '{"workspace_id":"/Users/hue/code/dopemux-mvp","summary":"Test decision via HTTP","rationale":"Testing EventBus integration","tags":["test"]}' | jq .
echo ""

sleep 1

# Check if event was published
echo "📊 Checking Redis Stream for decision_logged event..."
EVENTS=$(docker exec dopemux-redis-primary redis-cli XLEN "dopemux:events")
echo "Events in stream: $EVENTS"

if [ "$EVENTS" -gt "0" ]; then
    echo "✅ Event published!"
    docker exec dopemux-redis-primary redis-cli XREAD COUNT 1 STREAMS "dopemux:events" 0-0
else
    echo "❌ No event published"
fi
echo ""

# Test 2: log_progress via HTTP API
echo "2️⃣ Testing log_progress → progress_updated event..."
curl -s -X POST http://localhost:3004/api/progress \
  -H "Content-Type: application/json" \
  -d '{"workspace_id":"/Users/hue/code/dopemux-mvp","status":"IN_PROGRESS","description":"Test progress entry","percentage":50}' | jq .
echo ""

sleep 1

# Check stream length again
echo "📊 Checking stream after log_progress..."
EVENTS2=$(docker exec dopemux-redis-primary redis-cli XLEN "dopemux:events")
echo "Events in stream: $EVENTS2"

if [ "$EVENTS2" -gt "$EVENTS" ]; then
    echo "✅ Progress event published!"
    docker exec dopemux-redis-primary redis-cli XRANGE "dopemux:events" - + COUNT 2
else
    echo "❌ No new event"
fi
echo ""

echo "=========================================="
echo "✅ ConPort → EventBus integration test complete"
echo "=========================================="
