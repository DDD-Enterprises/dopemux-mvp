# ConPort Path C → Path A: Execution Plan

**Strategy**: Start simple (Event Bridge), validate value, then build unified system  
**Timeline**: 3 days (Path C) + 6 weeks (Path A) = ~7 weeks total  
**Status**: Ready to execute  
**Date**: 2025-10-28

---

## PHASE 1: Path C - Event Bridge (3 days)

### Goal
Prove agent integration value with minimal investment (200 lines of code)

### Success Criteria
- ✅ ConPort MCP SQLite changes → Redis Streams events
- ✅ Serena shows decisions in LSP hover tooltips
- ✅ < 100ms event latency
- ✅ Zero risk to existing systems

---

## DAY 1: Event Bridge Core (8 hours)

### Hour 1-2: Project Setup

**Create directory structure**:
```bash
mkdir -p docker/mcp-servers/conport-bridge
cd docker/mcp-servers/conport-bridge
```

**Files to create**:
```
docker/mcp-servers/conport-bridge/
├── main.py              # Event bridge core
├── watcher.py          # SQLite file watcher
├── publisher.py        # Redis Streams publisher
├── event_schemas.py    # Event type definitions
├── requirements.txt    # Dependencies
├── Dockerfile          # Container definition
└── .env.example        # Configuration template
```

**requirements.txt**:
```txt
watchdog==3.0.0
redis==5.0.1
pydantic==2.5.0
python-dotenv==1.0.0
```

**Deliverable**: Project skeleton ready

---

### Hour 3-4: SQLite File Watcher

**watcher.py** (~100 lines):
```python
#!/usr/bin/env python3
"""
SQLite File Watcher
Monitors ConPort MCP context.db for changes using watchdog
"""

import os
import sqlite3
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ConPortDBWatcher(FileSystemEventHandler):
    """Watch ConPort MCP SQLite database for changes"""
    
    def __init__(self, db_path: str, callback):
        self.db_path = Path(db_path)
        self.callback = callback
        self.last_row_id = self._get_max_row_id()
        logger.info(f"Watching {self.db_path}, starting at row {self.last_row_id}")
    
    def _get_max_row_id(self, table: str = "decisions") -> int:
        """Get max row ID from decisions table"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute(f"SELECT MAX(id) FROM {table}")
            result = cursor.fetchone()
            conn.close()
            return result[0] or 0
        except Exception as e:
            logger.error(f"Error getting max row ID: {e}")
            return 0
    
    def on_modified(self, event):
        """Called when database file is modified"""
        if event.src_path != str(self.db_path):
            return
        
        # Check for new rows in decisions table
        self._check_new_decisions()
        
        # Could also check progress, system_patterns, etc.
    
    def _check_new_decisions(self):
        """Check for new decision rows and publish events"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get new rows since last check
            cursor.execute("""
                SELECT id, summary, rationale, implementation_details,
                       tags, created_at
                FROM decisions
                WHERE id > ?
                ORDER BY id
            """, (self.last_row_id,))
            
            rows = cursor.fetchall()
            
            for row in rows:
                # Convert row to dict
                decision = dict(row)
                
                # Publish event
                self.callback({
                    "event_type": "decision.logged",
                    "data": decision,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "conport-mcp"
                })
                
                self.last_row_id = decision["id"]
            
            conn.close()
            
            if rows:
                logger.info(f"Published {len(rows)} new decision(s)")
                
        except Exception as e:
            logger.error(f"Error checking new decisions: {e}")
    
    def start_watching(self):
        """Start watching the database directory"""
        observer = Observer()
        observer.schedule(self, str(self.db_path.parent), recursive=False)
        observer.start()
        return observer


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    def test_callback(event):
        print(f"Event: {event['event_type']}")
        print(f"Data: {event['data']['summary']}")
    
    # Find ConPort MCP database
    db_path = Path.home() / "code/dopemux-mvp/context_portal/context.db"
    
    if db_path.exists():
        watcher = ConPortDBWatcher(str(db_path), test_callback)
        observer = watcher.start_watching()
        
        try:
            import time
            print("Watching for changes... (Ctrl+C to stop)")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    else:
        print(f"Database not found: {db_path}")
```

**Test**:
```bash
python watcher.py
# In another terminal, create a decision in ConPort MCP
# Should see event logged
```

**Deliverable**: File watching works

---

### Hour 5-6: Event Publisher

**event_schemas.py** (~50 lines):
```python
"""Event type definitions"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DecisionLoggedEvent(BaseModel):
    """Event schema for decision.logged"""
    event_type: str = "decision.logged"
    timestamp: str
    source: str
    data: dict  # Contains: id, summary, rationale, tags, etc.


class DecisionUpdatedEvent(BaseModel):
    """Event schema for decision.updated"""
    event_type: str = "decision.updated"
    timestamp: str
    source: str
    data: dict


class ProgressUpdatedEvent(BaseModel):
    """Event schema for progress.updated"""
    event_type: str = "progress.updated"
    timestamp: str
    source: str
    data: dict


# Event type registry
EVENT_TYPES = {
    "decision.logged": DecisionLoggedEvent,
    "decision.updated": DecisionUpdatedEvent,
    "progress.updated": ProgressUpdatedEvent,
}
```

**publisher.py** (~50 lines):
```python
"""Redis Streams Event Publisher"""
import redis
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publish events to Redis Streams"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        self.stream_name = "conport:events"
        logger.info(f"Connected to Redis, stream: {self.stream_name}")
    
    def publish(self, event: Dict[str, Any]) -> str:
        """
        Publish event to Redis Stream
        
        Returns: Event ID (timestamp-sequence)
        """
        try:
            # Add to stream
            event_id = self.redis.xadd(
                self.stream_name,
                {
                    "type": event["event_type"],
                    "source": event["source"],
                    "timestamp": event["timestamp"],
                    "data": json.dumps(event["data"])
                }
            )
            
            logger.info(f"Published {event['event_type']} -> {event_id}")
            return event_id.decode() if isinstance(event_id, bytes) else event_id
            
        except Exception as e:
            logger.error(f"Error publishing event: {e}")
            raise
    
    def close(self):
        """Close Redis connection"""
        self.redis.close()


# Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    pub = EventPublisher()
    
    # Test event
    event = {
        "event_type": "decision.logged",
        "source": "test",
        "timestamp": "2025-10-28T12:00:00Z",
        "data": {
            "id": 1,
            "summary": "Test decision"
        }
    }
    
    event_id = pub.publish(event)
    print(f"Published: {event_id}")
    
    pub.close()
```

**Test**:
```bash
python publisher.py
# Check Redis:
redis-cli
> XRANGE conport:events - +
# Should see test event
```

**Deliverable**: Event publishing works

---

### Hour 7-8: Integration & Main

**main.py** (~100 lines):
```python
#!/usr/bin/env python3
"""
ConPort Event Bridge
Watches ConPort MCP SQLite and publishes events to Redis Streams
"""

import os
import sys
import logging
import signal
from pathlib import Path
from dotenv import load_dotenv

from watcher import ConPortDBWatcher
from publisher import EventPublisher

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EventBridge:
    """Main event bridge coordinator"""
    
    def __init__(self):
        # Configuration
        self.db_path = os.getenv(
            'CONPORT_DB_PATH',
            str(Path.home() / 'code/dopemux-mvp/context_portal/context.db')
        )
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        # Components
        self.publisher = EventPublisher(self.redis_url)
        self.watcher = None
        self.observer = None
        
        # Shutdown flag
        self.running = True
    
    def event_callback(self, event):
        """Called when file system event detected"""
        try:
            self.publisher.publish(event)
        except Exception as e:
            logger.error(f"Error in event callback: {e}")
    
    def start(self):
        """Start the event bridge"""
        logger.info("=" * 60)
        logger.info("ConPort Event Bridge Starting")
        logger.info("=" * 60)
        logger.info(f"Database: {self.db_path}")
        logger.info(f"Redis: {self.redis_url}")
        
        # Check database exists
        if not Path(self.db_path).exists():
            logger.error(f"Database not found: {self.db_path}")
            sys.exit(1)
        
        # Start watcher
        self.watcher = ConPortDBWatcher(self.db_path, self.event_callback)
        self.observer = self.watcher.start_watching()
        
        logger.info("✅ Event Bridge Running")
        logger.info("Watching for ConPort MCP changes...")
        logger.info("Press Ctrl+C to stop")
        
        # Keep running
        try:
            while self.running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
            self.stop()
    
    def stop(self):
        """Stop the event bridge"""
        logger.info("Stopping Event Bridge...")
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        if self.publisher:
            self.publisher.close()
        
        logger.info("✅ Event Bridge Stopped")
        self.running = False


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start bridge
    bridge = EventBridge()
    bridge.start()
```

**Test end-to-end**:
```bash
# Terminal 1: Start bridge
python main.py

# Terminal 2: Monitor Redis
redis-cli MONITOR

# Terminal 3: Create decision in ConPort MCP (via Claude Code)
# Should see event flow through
```

**Deliverable**: Complete event bridge working

---

### End of Day 1 Checklist

- [ ] Project structure created
- [ ] SQLite watcher detects changes
- [ ] Events publish to Redis Streams
- [ ] End-to-end test successful
- [ ] ~200 lines of code written

**Output**: Event Bridge publishing decision events from ConPort MCP

---

## DAY 2: Serena Integration (8 hours)

### Hour 1-3: EventBus Consumer in Serena

**Location**: `services/serena/eventbus_consumer.py`

**Code** (~150 lines):
```python
"""
EventBus Consumer for Serena
Subscribes to ConPort decision events and caches decisions
"""

import asyncio
import redis.asyncio as redis
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DecisionCache:
    """In-memory cache of recent decisions"""
    
    def __init__(self, max_size: int = 100):
        self.decisions: Dict[int, dict] = {}
        self.max_size = max_size
        self.by_summary: Dict[str, List[int]] = {}  # For search
    
    def add(self, decision: dict):
        """Add decision to cache"""
        decision_id = decision["id"]
        self.decisions[decision_id] = decision
        
        # Index by summary words for search
        words = decision["summary"].lower().split()
        for word in words:
            if word not in self.by_summary:
                self.by_summary[word] = []
            if decision_id not in self.by_summary[word]:
                self.by_summary[word].append(decision_id)
        
        # Evict old decisions if over max_size
        if len(self.decisions) > self.max_size:
            oldest_id = min(self.decisions.keys())
            del self.decisions[oldest_id]
        
        logger.debug(f"Cached decision {decision_id}: {decision['summary'][:50]}")
    
    def search(self, query: str, limit: int = 3) -> List[dict]:
        """Search decisions by query string"""
        words = query.lower().split()
        decision_ids = set()
        
        for word in words:
            if word in self.by_summary:
                decision_ids.update(self.by_summary[word])
        
        # Get decisions and sort by ID (newest first)
        results = [
            self.decisions[did]
            for did in sorted(decision_ids, reverse=True)
            if did in self.decisions
        ]
        
        return results[:limit]


class EventBusConsumer:
    """
    EventBus consumer for Serena
    Subscribes to decision events and maintains cache
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        stream_name: str = "conport:events",
        consumer_group: str = "serena",
        consumer_name: str = "serena-1"
    ):
        self.redis_url = redis_url
        self.stream_name = stream_name
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        
        self.redis = None
        self.cache = DecisionCache()
        self.running = False
    
    async def connect(self):
        """Connect to Redis and create consumer group"""
        self.redis = await redis.from_url(self.redis_url)
        
        # Create consumer group if doesn't exist
        try:
            await self.redis.xgroup_create(
                self.stream_name,
                self.consumer_group,
                id='0',
                mkstream=True
            )
            logger.info(f"Created consumer group: {self.consumer_group}")
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
            logger.info(f"Consumer group exists: {self.consumer_group}")
    
    async def start(self):
        """Start consuming events"""
        await self.connect()
        self.running = True
        
        logger.info(f"Consuming from {self.stream_name} as {self.consumer_name}")
        
        while self.running:
            try:
                # Read events (block for 1 second)
                messages = await self.redis.xreadgroup(
                    self.consumer_group,
                    self.consumer_name,
                    {self.stream_name: '>'},
                    count=10,
                    block=1000
                )
                
                for stream, events in messages:
                    for event_id, event_data in events:
                        await self._process_event(event_id, event_data)
                        
            except asyncio.CancelledError:
                logger.info("Consumer cancelled")
                break
            except Exception as e:
                logger.error(f"Error consuming events: {e}")
                await asyncio.sleep(1)
    
    async def _process_event(self, event_id: bytes, event_data: dict):
        """Process a single event"""
        try:
            event_type = event_data[b'type'].decode()
            
            if event_type == "decision.logged":
                data = json.loads(event_data[b'data'].decode())
                self.cache.add(data)
                logger.info(f"Cached decision: {data['summary'][:50]}")
            
            # ACK the message
            await self.redis.xack(
                self.stream_name,
                self.consumer_group,
                event_id
            )
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
    
    async def stop(self):
        """Stop consuming"""
        self.running = False
        if self.redis:
            await self.redis.close()
    
    def search_decisions(self, query: str, limit: int = 3) -> List[dict]:
        """Search cached decisions"""
        return self.cache.search(query, limit)


# Global instance (initialized by LSP server)
consumer: Optional[EventBusConsumer] = None


async def init_consumer():
    """Initialize the global consumer"""
    global consumer
    consumer = EventBusConsumer()
    asyncio.create_task(consumer.start())
    logger.info("EventBus consumer initialized")


def get_consumer() -> Optional[EventBusConsumer]:
    """Get the global consumer instance"""
    return consumer
```

**Test**:
```bash
cd services/serena
python -c "
import asyncio
from eventbus_consumer import EventBusConsumer

async def test():
    consumer = EventBusConsumer()
    await consumer.connect()
    await consumer.start()

asyncio.run(test())
"
```

**Deliverable**: Serena can consume events from Redis

---

### Hour 4-6: LSP Hover Enhancement

**Location**: `services/serena/kg_integration.py`

**Code** (~150 lines):
```python
"""
ConPort-KG Integration for Serena LSP
Shows decision context in hover tooltips
"""

import logging
from typing import Optional, List
from eventbus_consumer import get_consumer

logger = logging.getLogger(__name__)


def get_decisions_for_symbol(symbol: str, limit: int = 3) -> List[dict]:
    """
    Get decisions related to a code symbol
    
    Uses EventBus consumer cache (fast, local)
    """
    consumer = get_consumer()
    
    if not consumer:
        logger.warning("EventBus consumer not initialized")
        return []
    
    try:
        # Search cache for symbol mentions
        decisions = consumer.search_decisions(symbol, limit)
        return decisions
        
    except Exception as e:
        logger.error(f"Error fetching decisions for {symbol}: {e}")
        return []


def format_hover_markdown(symbol: str, decisions: List[dict]) -> str:
    """
    Format decisions for LSP hover tooltip (Markdown)
    
    ADHD-friendly:
    - Top-3 pattern
    - Emoji visual cues
    - Concise summaries
    """
    if not decisions:
        return None  # No enhancement
    
    lines = [
        "---",
        "",
        "### 📝 Related Decisions",
        ""
    ]
    
    for i, decision in enumerate(decisions[:3], 1):
        # Truncate long summaries
        summary = decision["summary"]
        if len(summary) > 60:
            summary = summary[:57] + "..."
        
        lines.append(f"**{i}.** {summary}")
        
        # Add rationale if present (truncated)
        if decision.get("rationale"):
            rationale = decision["rationale"]
            if len(rationale) > 80:
                rationale = rationale[:77] + "..."
            lines.append(f"   _{rationale}_")
        
        # Add tags if present
        if decision.get("tags"):
            try:
                import json
                tags = json.loads(decision["tags"])
                if tags:
                    tag_str = " ".join(f"`{tag}`" for tag in tags[:3])
                    lines.append(f"   {tag_str}")
            except:
                pass
        
        lines.append("")
    
    if len(decisions) > 3:
        lines.append(f"_...and {len(decisions) - 3} more_")
    
    return "\n".join(lines)


def enrich_hover(symbol: str, original_hover: str) -> str:
    """
    Enrich existing hover tooltip with decision context
    
    Appends decision context to existing LSP hover text
    """
    decisions = get_decisions_for_symbol(symbol)
    
    if not decisions:
        return original_hover
    
    decision_markdown = format_hover_markdown(symbol, decisions)
    
    if not decision_markdown:
        return original_hover
    
    # Combine original hover + decision context
    return f"{original_hover}\n\n{decision_markdown}"


# Integration with Serena LSP server
# This gets called from the hover handler
def get_enhanced_hover(params, original_hover: str) -> str:
    """
    Called by LSP hover handler
    
    params: LSP HoverParams
    original_hover: Original hover text (type info, docs, etc)
    
    Returns: Enhanced hover with decision context
    """
    # Extract symbol at cursor position
    # (This depends on your LSP implementation)
    # For now, simplified:
    
    try:
        # Get symbol from params (implementation-specific)
        symbol = extract_symbol_from_params(params)
        
        if not symbol:
            return original_hover
        
        # Enrich with decisions
        return enrich_hover(symbol, original_hover)
        
    except Exception as e:
        logger.error(f"Error enhancing hover: {e}")
        return original_hover


def extract_symbol_from_params(params) -> Optional[str]:
    """
    Extract symbol name from LSP hover params
    
    Implementation depends on your LSP server
    This is a placeholder
    """
    # TODO: Implement based on your LSP server
    # For now, return None
    return None
```

**Deliverable**: Decision enrichment logic ready

---

### Hour 7-8: Wire Up & Test

**Update Serena main LSP file**:

Find your LSP hover handler and add:
```python
from eventbus_consumer import init_consumer
from kg_integration import get_enhanced_hover

# In your server initialization:
async def on_initialize(params):
    # ... existing init code ...
    
    # Initialize EventBus consumer
    await init_consumer()
    
    # ... rest of init ...

# In your hover handler:
@server.feature(HOVER)
async def handle_hover(params: HoverParams):
    # Get original hover (your existing logic)
    original_hover = await get_original_hover(params)
    
    # Enhance with decisions
    enhanced_hover = get_enhanced_hover(params, original_hover)
    
    return Hover(contents=MarkupContent(
        kind=MarkupKind.Markdown,
        value=enhanced_hover
    ))
```

**Test**:
```bash
# Terminal 1: Event Bridge running
cd docker/mcp-servers/conport-bridge
python main.py

# Terminal 2: Start Serena LSP
cd services/serena
# Start your LSP server

# Terminal 3: Open IDE, hover over function
# Should see decision context if any decisions mention that symbol
```

**Deliverable**: Serena shows decisions in hover tooltips

---

### End of Day 2 Checklist

- [ ] EventBus consumer working in Serena
- [ ] Decision cache functional
- [ ] Hover enrichment implemented
- [ ] End-to-end test: decision logged → appears in hover
- [ ] ~300 lines of code added to Serena

**Output**: Serena showing decision context in IDE hovers

---

## DAY 3: Docker Deployment & Polish (8 hours)

### Hour 1-2: Dockerfile & Docker Compose

**Dockerfile** (`docker/mcp-servers/conport-bridge/Dockerfile`):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY *.py ./

# Environment variables
ENV CONPORT_DB_PATH=/workspace/context_portal/context.db
ENV REDIS_URL=redis://dopemux-redis-events:6379

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import redis; r=redis.from_url('${REDIS_URL}'); r.ping()"

# Run
CMD ["python", "main.py"]
```

**Add to docker-compose.yml**:
```yaml
# docker-compose.yml or appropriate compose file

services:
  conport-event-bridge:
    build: ./docker/mcp-servers/conport-bridge
    container_name: conport-event-bridge
    restart: unless-stopped
    environment:
      CONPORT_DB_PATH: /workspace/context_portal/context.db
      REDIS_URL: redis://dopemux-redis-events:6379
    volumes:
      - ${PWD}:/workspace:ro  # Read-only access to workspace
    depends_on:
      - dopemux-redis-events
    networks:
      - dopemux-network
    healthcheck:
      test: ["CMD", "python", "-c", "import redis; r=redis.from_url('redis://dopemux-redis-events:6379'); r.ping()"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Deploy**:
```bash
docker-compose up -d conport-event-bridge

# Check logs
docker logs -f conport-event-bridge
```

**Deliverable**: Event Bridge running in Docker

---

### Hour 3-4: Error Handling & Resilience

**Add to main.py**:
```python
# Retry logic for Redis connection
from tenacity import retry, stop_after_attempt, wait_exponential

class EventBridge:
    # ...
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _connect_redis(self):
        """Connect to Redis with retry"""
        logger.info(f"Connecting to Redis: {self.redis_url}")
        self.publisher = EventPublisher(self.redis_url)
        logger.info("✅ Redis connected")
    
    def start(self):
        # ... existing code ...
        
        # Connect with retry
        self._connect_redis()
        
        # ... rest of start ...
```

**Add graceful degradation**:
```python
def event_callback(self, event):
    """Called when file system event detected"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            self.publisher.publish(event)
            return  # Success
        except Exception as e:
            logger.error(f"Error publishing (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
    
    logger.error(f"Failed to publish event after {max_retries} attempts")
```

**Deliverable**: Robust error handling

---

### Hour 5-6: Documentation

**README.md** (`docker/mcp-servers/conport-bridge/README.md`):
```markdown
# ConPort Event Bridge

Watches ConPort MCP SQLite database and publishes change events to Redis Streams.

## Architecture

```
ConPort MCP (SQLite) → Event Bridge → Redis Streams → Agents (Serena, etc)
```

## Events Published

- `decision.logged` - New decision created
- `decision.updated` - Decision modified
- `progress.updated` - Progress updated

## Configuration

Environment variables:

- `CONPORT_DB_PATH` - Path to context.db (default: /workspace/context_portal/context.db)
- `REDIS_URL` - Redis connection URL (default: redis://localhost:6379)

## Usage

### Local Development

```bash
cd docker/mcp-servers/conport-bridge
pip install -r requirements.txt
python main.py
```

### Docker

```bash
docker-compose up -d conport-event-bridge
```

### Check Status

```bash
# Logs
docker logs -f conport-event-bridge

# Redis events
redis-cli XRANGE conport:events - + COUNT 10
```

## Event Schema

```json
{
  "event_type": "decision.logged",
  "timestamp": "2025-10-28T12:00:00Z",
  "source": "conport-mcp",
  "data": {
    "id": 123,
    "summary": "Decision summary",
    "rationale": "Why we made this decision",
    "tags": "[\"architecture\", \"database\"]",
    "created_at": "2025-10-28T12:00:00Z"
  }
}
```

## Adding More Agents

To consume events in another agent:

1. Connect to Redis
2. Create consumer group
3. Read from stream `conport:events`
4. Process events
5. ACK messages

See `services/serena/eventbus_consumer.py` for example.

## Troubleshooting

**Events not publishing**:
- Check ConPort MCP database path is correct
- Verify watchdog is detecting file changes
- Check Redis connectivity

**Serena not showing decisions**:
- Verify EventBus consumer is running
- Check Redis for events: `redis-cli XRANGE conport:events - +`
- Check Serena logs for errors
```

**Deliverable**: Complete documentation

---

### Hour 7-8: Integration Testing & Validation

**Create test script** (`docker/mcp-servers/conport-bridge/test_integration.sh`):
```bash
#!/bin/bash
set -e

echo "ConPort Event Bridge - Integration Test"
echo "======================================="
echo ""

# 1. Check Event Bridge is running
echo "1. Checking Event Bridge..."
docker ps | grep conport-event-bridge || {
    echo "❌ Event Bridge not running"
    exit 1
}
echo "✅ Event Bridge running"
echo ""

# 2. Check Redis is accessible
echo "2. Checking Redis..."
docker exec conport-event-bridge python -c "
import redis
r = redis.from_url('redis://dopemux-redis-events:6379')
r.ping()
print('✅ Redis connected')
" || {
    echo "❌ Redis not accessible"
    exit 1
}
echo ""

# 3. Monitor Redis stream
echo "3. Monitoring Redis stream for 10 seconds..."
echo "   (Create a decision in ConPort MCP now)"
timeout 10 redis-cli -h localhost -p 6379 XREAD BLOCK 10000 STREAMS conport:events 0 || true
echo ""

# 4. Check recent events
echo "4. Recent events in Redis:"
redis-cli -h localhost -p 6379 XRANGE conport:events - + COUNT 5
echo ""

echo "✅ Integration test complete"
echo ""
echo "Next: Test Serena hover in IDE"
```

**Run test**:
```bash
chmod +x test_integration.sh
./test_integration.sh
```

**Manual IDE test**:
1. Open IDE with Serena LSP
2. Create decision in ConPort MCP
3. Wait 1-2 seconds
4. Hover over function/class name mentioned in decision
5. Should see decision in hover tooltip

**Deliverable**: End-to-end validation complete

---

### End of Day 3 Checklist

- [ ] Event Bridge deployed to Docker
- [ ] Error handling robust
- [ ] Documentation complete
- [ ] Integration tests passing
- [ ] Manual IDE test successful

**Output**: Production-ready Event Bridge + Serena integration

---

## PATH C COMPLETION CRITERIA

✅ **Technical**:
- Event Bridge publishes to Redis Streams
- Serena consumes events and shows decisions
- < 100ms latency from decision logged to cache updated
- Graceful error handling (retries, fallbacks)
- Docker deployment working

✅ **Functional**:
- Create decision in ConPort MCP → Appears in Serena hover (within seconds)
- Multiple decisions with same keyword → Top-3 shown
- Decision tags/rationale visible in hover

✅ **Operational**:
- Health checks passing
- Logs clean (no errors)
- Documentation complete
- Zero impact on existing systems (MCP still works normally)

---

## DECISION POINT: Validate Value

**After Path C completion, ask**:

1. **Is decision context in hovers useful?**
   - Do you actually look at the decisions when hovering?
   - Does it help understand code better?

2. **Do other agents need this?**
   - Would Task-Orchestrator benefit from decision context?
   - Would Zen use decisions for consensus?

3. **Is the pattern working?**
   - Is EventBus clean and simple?
   - Is the architecture scalable?

**If YES to most questions** → Proceed to Path A (Unified ConPort v3)

**If NO** → Stop here, keep MCP as-is, skip complex integration

---

## PHASE 2: Path A - Unified ConPort v3 (6 weeks)

### Goal
Build single unified system with all features from MCP, Enhanced, and KG

### Success Criteria
- ✅ One codebase (vs three)
- ✅ Multiple deployment modes (STDIO, HTTP, EventBus)
- ✅ All features preserved (auth, ADHD, graph queries)
- ✅ 6 agents integrated
- ✅ Dashboard deployed
- ✅ < 100ms latency (all modes)
- ✅ 90%+ test coverage

---

## WEEK 1: Core Architecture (40 hours)

### Overview
Build unified core engine with PostgreSQL AGE + SQLite cache

### Daily Breakdown

**Day 1: Project Setup & Data Model** (8 hours)
```bash
# Create project
mkdir -p services/conport_v3/{core,storage,queries,api,deployment}

# Define unified data model
# - Decisions (core entity)
# - Workspace (multi-tenant)
# - Users (auth, optional)
# - Relationships (graph)
```

**Files to create**:
```
services/conport_v3/
├── core/
│   ├── __init__.py
│   ├── models.py          # Unified data models
│   ├── config.py          # Configuration management
│   └── events.py          # Event system
├── storage/
│   ├── __init__.py
│   ├── interface.py       # Abstract storage interface
│   ├── postgres_age.py    # PostgreSQL AGE implementation
│   └── sqlite_cache.py    # SQLite cache layer
├── requirements.txt
└── README.md
```

**Deliverable**: Unified data model defined

---

**Day 2: Storage Layer** (8 hours)

**Implement dual storage**:

1. **PostgreSQL AGE** (from ConPort-KG):
   - Copy `age_client.py` from services/conport_kg/
   - Adapt to unified model
   - Graph queries (Cypher)

2. **SQLite cache** (from ConPort MCP):
   - Copy SQLite logic from services/conport/
   - Adapt to unified model
   - Local fast access

3. **Abstract interface**:
```python
# storage/interface.py
class StorageInterface:
    async def create_decision(self, decision: Decision) -> int
    async def get_decision(self, id: int) -> Decision
    async def search_decisions(self, query: str) -> List[Decision]
    async def get_graph_neighborhood(self, id: int) -> Graph
```

**Deliverable**: Storage layer working (both PostgreSQL and SQLite)

---

**Day 3: Query Layer** (8 hours)

**Implement unified queries**:

1. Copy from services/conport_kg/queries/:
   - overview.py (Top-3 ADHD)
   - exploration.py (Progressive)
   - deep_context.py (Complete)

2. Add from services/conport/:
   - FTS search
   - Semantic search

3. Unified query router:
```python
class QueryRouter:
    def route_query(self, query_type, params):
        # Use SQLite cache if available and sufficient
        # Otherwise use PostgreSQL for complex queries
```

**Deliverable**: All query types working

---

**Day 4: Auth Layer (Optional)** (8 hours)

**Copy from ConPort-KG**:
```bash
cp -r services/conport_kg/auth services/conport_v3/
cp -r services/conport_kg/middleware services/conport_v3/
```

**Make auth optional**:
```python
# core/config.py
class Config:
    auth_enabled: bool = False  # Can be disabled for STDIO mode
    
    @classmethod
    def from_deployment_mode(cls, mode: str):
        if mode == "stdio":
            return cls(auth_enabled=False)  # Trust OS-level
        else:
            return cls(auth_enabled=True)   # Require JWT
```

**Deliverable**: Optional auth working

---

**Day 5: Event System** (8 hours)

**Build EventBus integration**:

1. Publisher (from Path C Event Bridge)
2. Consumer (from services/serena/eventbus_consumer.py)
3. Event schemas (from Path C)

```python
# core/events.py
class EventSystem:
    def __init__(self, redis_url: str):
        self.publisher = EventPublisher(redis_url)
        self.consumers = []
    
    async def publish(self, event_type: str, data: dict):
        # Publish to Redis Streams
        
    async def subscribe(self, event_type: str, callback):
        # Subscribe to events
```

**Deliverable**: EventBus working in core

---

### End of Week 1

**Code written**: ~3,500 lines
**Status**: Core engine complete
- ✅ Storage (PostgreSQL + SQLite)
- ✅ Queries (all types)
- ✅ Auth (optional)
- ✅ Events (pub/sub)

---

## WEEK 2: Deployment Modes (40 hours)

### Overview
Add STDIO, HTTP, REST API, EventBus deployment modes

### Daily Breakdown

**Day 6: STDIO Mode** (8 hours)

**Copy from ConPort MCP**:
```bash
# Copy MCP protocol handler
cp services/conport/src/context_portal_mcp/server.py services/conport_v3/deployment/stdio_server.py
```

**Adapt to unified core**:
```python
# deployment/stdio_server.py
from core.models import Decision
from storage.sqlite_cache import SQLiteStorage

class StdioServer:
    def __init__(self):
        # Use SQLite for fast local access
        self.storage = SQLiteStorage("~/.conport_v3/cache.db")
        
    async def handle_log_decision(self, params):
        decision = Decision(**params)
        await self.storage.create_decision(decision)
        return {"success": True}
```

**Test**:
```bash
# Run in STDIO mode
python -m conport_v3.deployment.stdio_server

# Test with Claude Code
```

**Deliverable**: STDIO mode working (MCP protocol)

---

**Day 7: HTTP Mode** (8 hours)

**Copy from Enhanced Server**:
```bash
cp docker/mcp-servers/conport/enhanced_server.py services/conport_v3/deployment/http_server.py
```

**Adapt to unified core**:
```python
# deployment/http_server.py
from fastapi import FastAPI
from core import EventSystem

app = FastAPI()

@app.post("/decisions")
async def create_decision(decision: Decision):
    # Create in PostgreSQL
    decision_id = await storage.create_decision(decision)
    
    # Publish event
    await events.publish("decision.logged", decision.dict())
    
    return {"id": decision_id}
```

**Deliverable**: HTTP/SSE mode working

---

**Day 8: REST API** (8 hours)

**Copy from ConPort-KG**:
```bash
cp services/conport_kg/api/auth_routes.py services/conport_v3/api/
# Create api/query_routes.py (from our quickstart guide)
```

**Wire up queries**:
```python
# api/query_routes.py
from queries.overview import OverviewQueries

@router.get("/decisions/recent")
async def get_recent_decisions(limit: int = 3):
    return await overview.get_recent_decisions(limit)
```

**Deliverable**: REST API complete

---

**Day 9: EventBus API** (8 hours)

**Event consumers and publishers**:
```python
# deployment/eventbus_server.py
class EventBusServer:
    async def start(self):
        # Subscribe to all event types
        await events.subscribe("decision.*", self.handle_decision_event)
        
    async def handle_decision_event(self, event):
        # Process event, update storage
```

**Deliverable**: EventBus mode working

---

**Day 10: Configuration System** (8 hours)

**Deployment profiles**:
```python
# core/config.py
class DeploymentProfile:
    MINIMAL = {
        "storage": "sqlite",
        "auth": False,
        "api_modes": ["stdio"]
    }
    
    STANDARD = {
        "storage": "postgres",
        "auth": False,
        "api_modes": ["http", "eventbus"]
    }
    
    FULL = {
        "storage": "postgres",
        "auth": True,
        "api_modes": ["stdio", "http", "rest", "eventbus"]
    }
```

**CLI for deployment**:
```bash
# Minimal (like current MCP)
conport-v3 --mode minimal

# Standard (HTTP + EventBus)
conport-v3 --mode standard

# Full (all features)
conport-v3 --mode full --auth-enabled
```

**Deliverable**: Configuration system complete

---

### End of Week 2

**Code written**: ~1,800 lines
**Total**: ~5,300 lines
**Status**: All deployment modes working

---

## WEEKS 3-6: Integration, Dashboard, Testing

**Week 3**: Migration & Testing
- Export from MCP/Enhanced/KG
- Import to v3
- Unit + integration tests
- Performance benchmarks

**Week 4**: Agent Integration
- Serena (already done via EventBus)
- Task-Orchestrator
- Zen, Dope-Context, ADHD Engine, Desktop Commander

**Week 5**: ADHD Dashboard
- React + TypeScript
- Decision timeline
- Cognitive load heatmap
- Real-time WebSocket

**Week 6**: Polish & Deploy
- Documentation
- Performance tuning
- Production deployment
- User acceptance testing

---

## PATH A COMPLETION CRITERIA

✅ **Architecture**:
- One unified codebase
- Multiple deployment modes
- All features from 3 systems

✅ **Features**:
- Auth (optional, JWT + RBAC)
- Queries (3-tier + FTS + graph)
- ADHD optimizations
- EventBus integration
- Dashboard UI

✅ **Integration**:
- 6 agents connected
- All using EventBus
- < 100ms latency

✅ **Quality**:
- 90%+ test coverage
- Production deployment
- Complete documentation

---

## FILES TO CREATE - COMPLETE CHECKLIST

### Path C (3 days)

**Event Bridge**:
- [ ] docker/mcp-servers/conport-bridge/main.py
- [ ] docker/mcp-servers/conport-bridge/watcher.py
- [ ] docker/mcp-servers/conport-bridge/publisher.py
- [ ] docker/mcp-servers/conport-bridge/event_schemas.py
- [ ] docker/mcp-servers/conport-bridge/requirements.txt
- [ ] docker/mcp-servers/conport-bridge/Dockerfile
- [ ] docker/mcp-servers/conport-bridge/README.md

**Serena Integration**:
- [ ] services/serena/eventbus_consumer.py
- [ ] services/serena/kg_integration.py
- [ ] Update services/serena/main.py (add consumer init + hover enhancement)

**Documentation**:
- [ ] docker/mcp-servers/conport-bridge/test_integration.sh
- [ ] Update docker-compose.yml (add conport-event-bridge service)

### Path A (6 weeks)

**Core** (~50 files, ~7,500 lines):
- services/conport_v3/ (complete structure)
- See detailed breakdown in Week 1-6 sections above

---

## SUMMARY

**Path C** (3 days, 500 lines):
- Event Bridge: ConPort MCP → Redis Streams
- Serena integration: Decisions in hover tooltips
- Validates agent coordination value
- Zero risk to existing systems

**Path A** (6 weeks, 7,500 lines):
- Unified ConPort v3
- Best of all three systems
- Multiple deployment modes
- Production-ready architecture

**Total timeline**: 3 days + 6 weeks = ~7 weeks
**Total code**: 500 + 7,500 = ~8,000 lines

**Result**: One excellent system instead of three incomplete ones

---

**Ready to execute**: YES  
**Start with**: Path C Day 1 (Event Bridge)  
**Decision point**: After Path C completion (validate value)  
**Long-term**: Path A (if Path C validates value)

---

Let's build it! 🚀
