#!/bin/bash
# EventBus REST API Test Script

echo "🧪 EventBus REST API Test Suite"
echo "================================="
echo ""

# Test 1: Health check
echo "1️⃣ Testing health endpoint..."
curl -s -X GET http://localhost:3016/health | jq .
echo ""

# Test 2: Publish tasks_imported event
echo "2️⃣ Publishing tasks_imported event..."
curl -s -X POST http://localhost:3016/events \
  -H "Content-Type: application/json" \
  -d '{"event_type":"tasks_imported","data":{"task_count":10,"sprint_id":"S-2025.10"}}' | jq .
echo ""

# Test 3: Publish session_started event
echo "3️⃣ Publishing session_started event..."
curl -s -X POST http://localhost:3016/events \
  -H "Content-Type: application/json" \
  -d '{"event_type":"session_started","data":{"task_id":"task-123","duration_minutes":25}}' | jq .
echo ""

# Test 4: Publish progress_updated event
echo "4️⃣ Publishing progress_updated event..."
curl -s -X POST http://localhost:3016/events \
  -H "Content-Type: application/json" \
  -d '{"event_type":"progress_updated","data":{"task_id":"task-123","status":"IN_PROGRESS","progress":0.5}}' | jq .
echo ""

# Test 5: Publish break_reminder event
echo "5️⃣ Publishing break_reminder event..."
curl -s -X POST http://localhost:3016/events \
  -H "Content-Type: application/json" \
  -d '{"event_type":"break_reminder","data":{"duration_minutes":5,"message":"Time for a break!"}}' | jq .
echo ""

# Test 6: Stream info
echo "6️⃣ Getting stream info..."
curl -s -X GET http://localhost:3016/events/dopemux:events | jq .
echo ""

# Test 7: Convenience endpoint - tasks imported
echo "7️⃣ Testing convenience endpoint (tasks-imported)..."
curl -s -X POST "http://localhost:3016/events/tasks-imported?task_count=15&sprint_id=S-2025.10" | jq .
echo ""

# Test 8: Verify in Redis
echo "8️⃣ Verifying events in Redis Stream..."
docker exec dopemux-redis-primary redis-cli XLEN "dopemux:events"
echo ""

echo "================================="
echo "✅ EventBus REST API tests complete!"
echo "================================="
