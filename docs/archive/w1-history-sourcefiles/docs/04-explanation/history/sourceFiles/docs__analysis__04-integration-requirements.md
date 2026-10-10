# Integration Requirements - Cross-Client Support & Concurrency

## Overview

This document specifies integration requirements for supporting multiple client interfaces, Docker networking, and safe multi-agent concurrency patterns in the Dopemux orchestration system.

## Cross-Client Integration Matrix

### Supported Clients

| Client | Connection Type | Protocol | Use Case | Session Management |
|--------|-----------------|----------|----------|-------------------|
| **Claude Code** | Native MCP | stdio/http | Interactive development | Built-in session persistence |
| **Codex CLI** | MetaMCP | stdio/http | Command-line automation | tmux session attachment |
| **Dopemux CLI** | MetaMCP | stdio/http | Agentic workflows | Process-based state |
| **tmux Interface** | Multiple shells | Mixed | Long-running agents | Named session management |
| **Zed (ACP)** | Agent Client Protocol | ACP→MCP bridge | Chat-triggered workflows | Hot agent swapping |

### Client-Specific Integration Patterns

#### Claude Code (Primary Development Interface)
```yaml
integration_pattern: "Native MCP Client"
configuration:
  mcp_servers:
    - metamcp:
        command: "docker"
        args: ["exec", "metamcp", "mcp-server"]
        env:
          WORKSPACE: "engineer"
    - claude-context:
        command: "npx"
        args: ["@zilliz/claude-context"]
connection_type: "stdio"
session_management: "Built-in Claude Code persistence"
advantages:
  - Direct MCP protocol support
  - Rich UI for tool interactions
  - Integrated code context
  - Desktop Extension support
```

#### Codex CLI (Command-Line Automation)
```yaml
integration_pattern: "MetaMCP Stdio Client"
configuration:
  connection:
    endpoint: "stdio"
    command: "docker exec metamcp mcp-server --workspace=engineer"
  session_file: "$HOME/.codex/session.json"
session_management: "File-based state persistence"
advantages:
  - Scriptable automation
  - CI/CD integration
  - Batch processing
  - Shell environment integration
```

#### Dopemux CLI (Agentic Workflows)
```yaml
integration_pattern: "Autonomous Agent Client"
configuration:
  metamcp_endpoint: "http://localhost:3000"
  workspace: "dynamic"  # Changes based on role
  auth: "bearer_token"
session_management: "Process-based with checkpoints"
advantages:
  - Long-running autonomous workflows
  - Role-based context switching
  - Multi-step task execution
  - Failure recovery
```

#### tmux Interface (Session Multiplexing)
```yaml
integration_pattern: "Multi-pane Agent Farm"
configuration:
  session_name: "dopemux-agents"
  panes:
    - name: "researcher"
      command: "dopemux-cli --role=researcher --attach"
    - name: "architect"
      command: "dopemux-cli --role=architect --attach"
    - name: "implementer"
      command: "dopemux-cli --role=implementer --attach"
session_management: "Named tmux sessions with restoration"
advantages:
  - Visual multi-agent monitoring
  - Individual pane control
  - Session persistence across disconnects
  - Resource isolation per role
```

#### Zed Editor (Agent Client Protocol)
```yaml
integration_pattern: "ACP Bridge to MCP"
configuration:
  acp_adapter:
    bridge: "claude-code-acp-adapter"
    mcp_endpoint: "metamcp"
  chat_triggers:
    - "/research <topic>": "researcher agent"
    - "/implement <feature>": "engineer agent"
    - "/review <pr>": "validator agent"
session_management: "Editor-based with agent hot-swap"
advantages:
  - In-editor chat interface
  - Context-aware triggers
  - Agent switching without losing MCP access
  - Rich text and code display
```

## Docker Network Architecture

### Network Topology
```yaml
# docker-compose.yml networking
networks:
  dopemux-net:
    driver: bridge
    internal: false  # Allow external access for webhooks
    ipam:
      config:
        - subnet: 172.20.0.0/16

# Service connectivity matrix
services:
  metamcp:
    networks:
      dopemux-net:
        aliases: ["mcp.dopemux.local"]

  leantime:
    networks:
      dopemux-net:
        aliases: ["leantime.dopemux.local"]

  milvus:
    networks:
      dopemux-net:
        aliases: ["milvus.dopemux.local"]

  redis:
    networks:
      dopemux-net:
        aliases: ["redis.dopemux.local"]

  neo4j:
    networks:
      dopemux-net:
        aliases: ["neo4j.dopemux.local"]
```

### Service Discovery
```bash
# Internal DNS resolution examples
ping metamcp                    # ✅ Resolves to container
ping mcp.dopemux.local         # ✅ Resolves with alias
curl http://leantime/api/tasks  # ✅ Direct service-to-service

# External access patterns
localhost:3001 → metamcp:3000   # MetaMCP aggregator
localhost:3002 → leantime:80    # Leantime web UI
localhost:3003 → neo4j:7474     # Neo4j browser
```

### Port Allocation Strategy
```yaml
port_allocation:
  external_access:
    metamcp: "3001:3000"
    leantime: "3002:80"
    neo4j_browser: "3003:7474"
    neo4j_bolt: "3004:7687"
    milvus: "3005:19530"
    redis: "3006:6379"

  internal_only:
    opensearch: "9200"
    mysql: "3306"
    task_orchestrator: "8080"
    doc_context: "8081"

  dynamic_allocation:
    # Git worktree isolation
    base_port: 4000
    per_worktree: 100  # e.g., worktree 'feature-x' uses ports 4100-4199
```

## Multi-Agent Concurrency Patterns

### Git Worktree Isolation

#### Worktree Creation and Namespacing
```bash
#!/bin/bash
# create-agent-workspace.sh

WORKTREE_ID=$1
BRANCH_NAME=${2:-"agent-workspace-$WORKTREE_ID"}
BASE_PORT=$((4000 + $(echo $WORKTREE_ID | md5sum | head -c 4 | printf "%d\n" 0x$(cat))))

# Create isolated git worktree
git worktree add .worktrees/$WORKTREE_ID $BRANCH_NAME

# Namespace configuration
export DOPEMUX_WORKTREE_ID=$WORKTREE_ID
export DOPEMUX_BASE_PORT=$BASE_PORT

# Environment isolation
cat > .worktrees/$WORKTREE_ID/.env <<EOF
WORKTREE_ID=$WORKTREE_ID
MILVUS_COLLECTION_PREFIX=${WORKTREE_ID}_
NEO4J_DATABASE=${WORKTREE_ID}_graph
REDIS_KEY_PREFIX=cache:${WORKTREE_ID}:
METAMCP_PORT=$BASE_PORT
EOF
```

#### Datastore Namespacing Implementation
```python
# Milvus collection namespacing
class WorktreeIsolatedMilvus:
    def __init__(self, worktree_id: str):
        self.worktree_id = worktree_id
        self.collection_prefix = f"{worktree_id}_"

    def search(self, collection_name: str, query: str):
        isolated_collection = f"{self.collection_prefix}{collection_name}"
        return self.client.search(isolated_collection, query)

# Neo4j label isolation
class WorktreeIsolatedNeo4j:
    def execute_query(self, query: str, worktree_id: str):
        # Automatically add worktree labels
        modified_query = query.replace(
            "CREATE (n:",
            f"CREATE (n:Worktree_{worktree_id}:"
        )
        return self.session.run(modified_query)

# Redis key prefixing
class WorktreeIsolatedRedis:
    def __init__(self, worktree_id: str):
        self.key_prefix = f"cache:{worktree_id}:"

    def get(self, key: str):
        return self.client.get(f"{self.key_prefix}{key}")
```

### Idempotency and Consistency Patterns

#### Idempotency Key Management
```python
from dataclasses import dataclass
from typing import Optional
import hashlib
import json

@dataclass
class IdempotentOperation:
    operation_type: str
    resource_id: str
    payload: dict
    worktree_id: str
    timestamp: str

    @property
    def idempotency_key(self) -> str:
        content = f"{self.operation_type}:{self.resource_id}:{self.worktree_id}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

class IdempotencyManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1 hour

    async def execute_once(self, operation: IdempotentOperation, func):
        key = f"idempotency:{operation.idempotency_key}"

        # Check if already executed
        existing_result = await self.redis.get(key)
        if existing_result:
            return json.loads(existing_result)

        # Execute operation
        result = await func(operation.payload)

        # Store result
        await self.redis.setex(key, self.ttl, json.dumps(result))
        return result
```

#### Transactional Outbox Pattern
```python
class OutboxEvent:
    def __init__(self, event_type: str, source_system: str,
                 target_systems: list, payload: dict, worktree_id: str):
        self.id = str(uuid.uuid4())
        self.event_type = event_type
        self.source_system = source_system
        self.target_systems = target_systems
        self.payload = payload
        self.worktree_id = worktree_id
        self.status = "pending"
        self.created_at = datetime.utcnow()

class OutboxProcessor:
    async def publish_event(self, event: OutboxEvent):
        # Store in outbox table within same transaction
        async with self.db.transaction():
            # Primary business operation
            await self.execute_primary_operation(event.payload)

            # Store outbox event
            await self.store_outbox_event(event)

        # Process outbox asynchronously
        await self.process_outbox_events()

    async def process_outbox_events(self):
        pending_events = await self.get_pending_outbox_events()
        for event in pending_events:
            for target_system in event.target_systems:
                try:
                    await self.deliver_to_target(event, target_system)
                    await self.mark_delivered(event.id, target_system)
                except Exception as e:
                    await self.mark_failed(event.id, target_system, str(e))
```

### Resource Contention Management

#### Lock-Free Operations Where Possible
```python
# Optimistic concurrency for Leantime sync
class OptimisticLeanTimeSync:
    async def update_task(self, task_id: str, updates: dict, expected_version: int):
        current_task = await self.leantime_api.get_task(task_id)

        if current_task.version != expected_version:
            raise ConcurrencyError(
                f"Task {task_id} was modified. Expected version {expected_version}, "
                f"got {current_task.version}"
            )

        # Apply updates with version increment
        updates['version'] = current_task.version + 1
        return await self.leantime_api.update_task(task_id, updates)
```

#### Circuit Breaker Pattern for External Services
```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    async def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half_open"
            else:
                raise CircuitOpenError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"

            raise e
```

## Client Configuration Templates

### Claude Code MCP Configuration
```json
{
  "mcpServers": {
    "dopemux-metamcp": {
      "command": "docker",
      "args": [
        "exec", "dopemux-metamcp",
        "mcp-server", "--workspace", "engineer"
      ],
      "env": {
        "WORKTREE_ID": "${DOPEMUX_WORKTREE_ID:-main}",
        "USER_ROLE": "engineer"
      }
    }
  }
}
```

### Dopemux CLI Configuration
```yaml
# ~/.config/dopemux/config.yaml
metamcp:
  endpoint: "http://localhost:3001"
  auth: "bearer"
  token: "${DOPEMUX_API_TOKEN}"

worktree:
  auto_create: true
  cleanup_on_exit: false
  base_path: "./.worktrees"

roles:
  default: "engineer"
  available:
    - researcher
    - product_architect
    - engineering_architect
    - planner
    - engineer
    - validator
    - docs_writer
    - qa

sessions:
  persist: true
  directory: "~/.config/dopemux/sessions"
  auto_save_interval: 30  # seconds
```

### tmux Session Script
```bash
#!/bin/bash
# start-dopemux-agents.sh

SESSION="dopemux-agents"

# Create session if it doesn't exist
tmux has-session -t $SESSION 2>/dev/null || tmux new-session -d -s $SESSION

# Set up panes for different roles
tmux split-window -h -t $SESSION:0
tmux split-window -v -t $SESSION:0.0
tmux split-window -v -t $SESSION:0.2

# Start agents in each pane
tmux send-keys -t $SESSION:0.0 "dopemux-cli --role=researcher --attach" Enter
tmux send-keys -t $SESSION:0.1 "dopemux-cli --role=architect --attach" Enter
tmux send-keys -t $SESSION:0.2 "dopemux-cli --role=engineer --attach" Enter
tmux send-keys -t $SESSION:0.3 "dopemux-cli --role=validator --attach" Enter

# Set pane titles
tmux select-pane -t $SESSION:0.0 -T "Researcher"
tmux select-pane -t $SESSION:0.1 -T "Architect"
tmux select-pane -t $SESSION:0.2 -T "Engineer"
tmux select-pane -t $SESSION:0.3 -T "Validator"

echo "Dopemux agents started in tmux session: $SESSION"
echo "Attach with: tmux attach-session -t $SESSION"
```

---

Generated: 2025-09-24
Status: Integration patterns specified
Next: Final synthesis and architectural decisions