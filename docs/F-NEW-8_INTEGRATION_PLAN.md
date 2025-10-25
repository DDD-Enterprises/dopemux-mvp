# F-NEW-8 + ADHD Notifier Integration Plan

**Goal**: Combine intelligent break detection (F-NEW-8) with effective delivery (ADHD Notifier)

## Current State

**F-NEW-8 (Break Suggester)**:
- ✅ Engine complete (340 lines)
- ✅ EventBus consumer (210 lines)
- ✅ Tests: 5/6 passing (83%)
- ❌ Not wired to notification system

**ADHD Notifier**:
- ✅ Desktop notifications (visual + voice)
- ✅ Polls Activity Capture every 60s
- ✅ Simple time-based detection
- ✅ Production-ready

## Integration Architecture

```
F-NEW-8 Break Suggester (Intelligent Detection)
  ↓ monitors events
Redis Streams: code.complexity.high, cognitive.state.change
  ↓ correlates patterns
BreakSuggestionEngine
  ↓ generates suggestion
    priority: CRITICAL/HIGH/MEDIUM
    message: "MANDATORY BREAK - 65 min of high complexity"
    duration: 10 minutes
  ↓ publishes to
Redis Stream: break.suggestion
  ↓ consumed by
ADHD Notifier (Delivery System)
  ↓ delivers via
Desktop Notification + Voice TTS
```

## Implementation Steps

### Step 1: F-NEW-8 Event Emission (15 minutes)

**File**: `services/break-suggester/engine.py`

Add event emission after suggestion generation:

```python
async def _emit_break_suggestion(self, suggestion: BreakSuggestion):
    """Emit break suggestion to EventBus for ADHD Notifier"""
    try:
        event = Event(
            type="break.suggestion",
            data={
                "priority": suggestion.priority,
                "message": suggestion.message,
                "suggested_duration": suggestion.suggested_duration,
                "reason": suggestion.reason,
                "user_id": self.user_id
            },
            source="break-suggester"
        )

        await self.event_bus.publish("dopemux:events", event)
    except Exception as e:
        logger.error(f"Failed to emit break suggestion: {e}")
```

### Step 2: ADHD Notifier Event Consumption (15 minutes)

**File**: `services/adhd-notifier/monitor.py`

Add break.suggestion event handler:

```python
async def _subscribe_to_break_suggestions(self):
    """Subscribe to break suggestions from F-NEW-8"""
    # Subscribe to Redis Stream
    async for message_id, event_data in event_bus.subscribe(
        stream="dopemux:events",
        consumer_group="adhd-notifier"
    ):
        if event_data.get("type") == "break.suggestion":
            await self._handle_break_suggestion(event_data)

async def _handle_break_suggestion(self, event_data: dict):
    """Handle intelligent break suggestion from F-NEW-8"""
    priority = event_data.get("priority", "medium")
    message = event_data.get("message", "Time for a break")
    duration = event_data.get("suggested_duration", 5)

    # Map priority to urgency
    urgency = "urgent" if priority in ["critical", "high"] else "normal"

    # Send notification + voice
    self.notifier.send_break_reminder(duration, urgency)
    self.notifier.speak_break_reminder(duration, urgency)
```

### Step 3: Start F-NEW-8 Service (5 minutes)

**File**: `scripts/start-all.sh`

Add F-NEW-8 to startup:

```bash
# Step 7: Start Break Suggester (F-NEW-8)
echo "🎯 Step 7/7: Starting Break Suggester..."
cd "$PROJECT_ROOT/services/break-suggester"

pkill -9 -f "break-suggester" 2>/dev/null || true
sleep 1

nohup python start_service.py > /tmp/break_suggester.log 2>&1 &
SUGGESTER_PID=$!

sleep 2

if ps -p $SUGGESTER_PID >/dev/null 2>&1; then
    echo "✅ Break Suggester started (PID: $SUGGESTER_PID)"
else
    echo "⚠️  Break Suggester failed - check /tmp/break_suggester.log"
fi
```

### Step 4: Testing (15 minutes)

**Test Flow**:
1. Start both services
2. Trigger high complexity events (Serena code analysis)
3. Wait 25+ minutes
4. Verify F-NEW-8 detects pattern
5. Verify ADHD Notifier receives suggestion
6. Verify notification + voice delivered

**Files**:
- services/break-suggester/engine.py (add event emission)
- services/adhd-notifier/monitor.py (add event subscription)
- scripts/start-all.sh (add F-NEW-8 startup)

## Benefits of Integration

**Combined System Strengths**:
- ✅ Intelligent detection (F-NEW-8 correlates multiple signals)
- ✅ Effective delivery (ADHD Notifier multi-modal alerts)
- ✅ Event-driven architecture (loose coupling)
- ✅ Best of both worlds

**ADHD Impact**:
- Smarter break timing (knows WHY not just WHEN)
- Context-aware suggestions ("high complexity work" vs "just time")
- Multiple delivery modes (dashboard + notification + voice)
- Proactive prevention vs reactive reminders

## Timeline

**Total Time**: ~50 minutes
- Step 1: 15 min (F-NEW-8 event emission)
- Step 2: 15 min (ADHD Notifier subscription)
- Step 3: 5 min (startup scripts)
- Step 4: 15 min (testing)

**Priority**: MEDIUM (both systems work independently, integration enhances)

## Decision

**Recommendation**: Integrate in next session
- Both systems functional standalone
- Integration adds value but not critical
- Current ADHD Notifier provides base functionality
- F-NEW-8 adds intelligence layer when integrated

**Status**: Integration plan complete, ready to implement
