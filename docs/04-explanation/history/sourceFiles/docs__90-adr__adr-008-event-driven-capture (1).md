# ADR-008: Event-Driven Asynchronous Capture Architecture

**Status**: Proposed
**Date**: 2025-09-22
**Deciders**: Dopemux Team

## Context

The Intelligent Memory Layer must capture development activities from multiple sources (git, shell, conversations, file changes) without interrupting the developer's workflow. ADHD developers are particularly sensitive to flow state interruption, making latency requirements critical.

Key requirements:
- **Zero perceived latency** (<10ms for capture)
- **Multiple event sources** (git, shell, Claude, filesystem)
- **Reliable delivery** (no lost memories)
- **ADHD-friendly** (never blocks workflow)

## Decision

We will implement an **event-driven asynchronous capture architecture** with:

1. **Instant Capture**: Non-blocking event capture to in-memory queue
2. **Async Processing**: Background classification and storage
3. **Universal Event Bus**: Single pipeline for all event sources
4. **Graceful Degradation**: Works even when downstream services are slow/unavailable

## Rationale

### ADHD Workflow Protection
- **Flow state is fragile** for ADHD developers
- Any perceptible delay (>10ms) can break concentration
- Background processing allows instant feedback while preserving accuracy
- Developer sees immediate "captured" indicator, processing happens later

### Source Diversity Challenge
Multiple event sources require different integration approaches:
- **Git hooks**: Shell script integration
- **Shell commands**: Function/alias wrappers
- **Claude messages**: HTTP hook integration
- **File changes**: Filesystem watcher
- **Context switches**: Directory change detection

A unified event bus provides consistent processing regardless of source.

### Reliability Requirements
Development activities are valuable and should never be lost:
- **Persistent queue** survives process restarts
- **Retry logic** for transient failures
- **Dead letter queue** for investigation of persistent failures
- **Monitoring** to ensure pipeline health

## Architecture

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Git Hook    │  │ Shell Cmd   │  │ Claude Msg  │
└─────┬───────┘  └─────┬───────┘  └─────┬───────┘
      │                │                │
      └────────────────┼────────────────┘
                       │
                ┌──────▼──────┐
                │ Event Bus   │  <-- Instant capture (<10ms)
                │ (In-Memory  │
                │  + Redis)   │
                └──────┬──────┘
                       │
                ┌──────▼──────┐
                │ Event       │  <-- Async processing
                │ Processor   │
                │ Pool        │
                └──────┬──────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐  ┌──────▼──────┐  ┌────▼────┐
   │Classify │  │  Enrich     │  │ Store   │
   │Service  │  │ Relations   │  │Service  │
   └─────────┘  └─────────────┘  └─────────┘
```

## Implementation Details

### Event Capture Layer
```python
class EventCapture:
    def __init__(self):
        self.queue = asyncio.Queue(maxsize=10000)  # In-memory for speed
        self.redis = Redis()  # Persistent backup
        self.feedback = VisualFeedback()

    async def capture(self, source: str, event: dict):
        """Instant, non-blocking capture"""
        start_time = time.perf_counter()

        enriched_event = {
            'id': uuid4(),
            'timestamp': datetime.now(),
            'source': source,
            'context': self.get_context(),
            'event': event,
            'status': 'captured'
        }

        # Instant in-memory queue
        try:
            self.queue.put_nowait(enriched_event)
        except asyncio.QueueFull:
            # Fallback to Redis if queue full
            await self.redis.lpush('dopemux:events', json.dumps(enriched_event))

        # Immediate visual feedback
        elapsed = (time.perf_counter() - start_time) * 1000
        self.feedback.show_capture_indicator(source, elapsed)

        # Guarantee: Always <10ms
        assert elapsed < 10
```

### Event Processing Pipeline
```python
class EventProcessor:
    def __init__(self):
        self.classifier = HybridClassifier()
        self.enricher = RelationshipEnricher()
        self.storage = MemoryStorage()

    async def process_events(self):
        """Background event processing loop"""
        while True:
            try:
                # Get batch of events for efficiency
                events = await self.get_event_batch()

                for event in events:
                    await self.process_single_event(event)

            except Exception as e:
                logger.error(f"Event processing error: {e}")
                await asyncio.sleep(1)  # Brief pause on error

    async def process_single_event(self, event):
        """Process individual event through pipeline"""
        try:
            # 1. Classify content
            classification = await self.classifier.classify(
                event['event']['content'],
                event['context']
            )

            # 2. Enrich with relationships
            enrichment = await self.enricher.enrich(
                classification,
                event['context']
            )

            # 3. Store in memory system
            await self.storage.store(classification, enrichment)

            # 4. Update event status
            event['status'] = 'processed'

        except Exception as e:
            # Move to dead letter queue for investigation
            await self.move_to_dlq(event, str(e))
```

### Integration Points

#### Git Hook Integration
```bash
#!/bin/bash
# .git/hooks/post-commit
echo "$GIT_COMMIT_MESSAGE" | dopemux-capture git_commit &
exit 0  # Never block git
```

#### Shell Integration
```bash
# Transparent wrappers
cd() {
    dopemux-capture context_switch "from:$PWD to:$1" &
    builtin cd "$@"
}
```

#### Claude Code Integration
```python
# HTTP webhook handler
async def claude_message_hook(request):
    message = await request.json()
    await event_capture.capture('claude_message', message)
    return web.Response(status=200)  # Immediate response
```

## Benefits

### For ADHD Developers
- **Zero workflow interruption**: Capture never blocks
- **Immediate feedback**: Visual confirmation of capture
- **Reliable memory**: Activities preserved even during hyperfocus
- **Context preservation**: Background processing maintains relationships

### Technical Benefits
- **Scalable**: Async processing handles burst activity
- **Reliable**: Persistent queuing prevents data loss
- **Flexible**: Easy to add new event sources
- **Monitorable**: Clear pipeline visibility

### Performance Benefits
- **Sub-10ms capture**: Meets ADHD latency requirements
- **Batch processing**: Efficient downstream operations
- **Resource optimization**: Processing scales with available resources

## Risks and Mitigations

### Queue Overflow
**Risk**: High-frequency events overwhelm queue
**Mitigation**:
- Redis fallback for queue overflow
- Batch processing to increase throughput
- Monitoring with alerts

### Processing Lag
**Risk**: Events accumulate faster than processing
**Mitigation**:
- Auto-scaling processor pool
- Priority processing for important events
- Degraded mode that skips complex analysis

### Service Dependencies
**Risk**: Downstream services (AI, storage) become unavailable
**Mitigation**:
- Circuit breaker pattern
- Local caching/buffering
- Graceful degradation modes

### Data Loss
**Risk**: Events lost due to crashes or failures
**Mitigation**:
- Persistent Redis backup
- At-least-once delivery semantics
- Regular health checks and monitoring

## Consequences

### Positive
- **ADHD-friendly**: Preserves flow state with instant capture
- **Scalable**: Handles high-frequency development activity
- **Reliable**: Multiple layers prevent data loss
- **Extensible**: Easy to add new event sources

### Negative
- **Complexity**: More moving parts than synchronous approach
- **Resource usage**: Background processing consumes resources
- **Eventual consistency**: Some delay between capture and availability
- **Monitoring overhead**: Need to track pipeline health

## Alternatives Considered

### Synchronous Processing
- **Pros**: Simpler architecture, immediate consistency
- **Cons**: Latency would break ADHD workflow requirements
- **Rejected**: Cannot meet <10ms requirement

### Direct Database Writes
- **Pros**: Simple, immediate consistency
- **Cons**: Database latency varies, could block capture
- **Rejected**: Unreliable latency for ADHD requirements

### File-Based Queuing
- **Pros**: Very persistent, simple
- **Cons**: Slower than in-memory, harder to monitor
- **Considered**: Could be fallback option for extreme reliability

## Success Metrics

- **Capture Latency**: 99% of captures complete in <10ms
- **Processing Throughput**: Can handle 1000+ events/minute
- **Reliability**: <0.1% event loss rate
- **Developer Satisfaction**: No reported workflow interruptions

## Future Enhancements

1. **Smart Batching**: Optimize batch sizes based on processing capacity
2. **Event Deduplication**: Avoid processing duplicate events
3. **Priority Queues**: Process important events first
4. **Distributed Processing**: Scale across multiple machines

This event-driven architecture ensures that memory capture never interferes with the developer's cognitive flow while maintaining the reliability and accuracy needed for comprehensive memory preservation.