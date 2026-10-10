# Dopemux System Architecture Specification
**Version 1.0 | Multi-Platform Development Orchestration Architecture**

## Architecture Overview

### System Philosophy
Dopemux implements a **hybrid orchestration architecture** combining hub-and-spoke coordination with mesh networking fallback, designed to maximize both AI agent collaboration efficiency and system resilience. The architecture prioritizes cognitive accessibility through evidence-based ADHD support patterns while maintaining enterprise-grade performance and scalability.

### High-Level System Topology

```
Dopemux Architecture Topology
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              DOPEMUX ORCHESTRATION LAYER                           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                │
│  │   CLAUDE-FLOW   │    │      LETTA      │    │   MCP SERVERS   │                │
│  │   64 AI Agents  │◄──►│ Memory Framework│◄──►│  12+ Specialized│                │
│  │   PBFT Consensus│    │ 3-Tier Memory   │    │   Tool Servers  │                │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘                │
│           │                       │                       │                        │
│           ▼                       ▼                       ▼                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                            TERMINAL INTERFACE LAYER                                │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                │
│  │     TMUX        │    │   ADHD-OPTIMIZED│    │  VOICE/KEYBOARD │                │
│  │  Multiplexing   │◄──►│   UI Components │◄──►│  Input Systems  │                │
│  │   Sessions      │    │ High Contrast UI│    │ Context-Aware   │                │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘                │
│           │                       │                       │                        │
│           ▼                       ▼                       ▼                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                             DATA PERSISTENCE LAYER                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                │
│  │   POSTGRESQL    │    │      REDIS      │    │     QDRANT      │                │
│  │  + pgvector     │◄──►│ Semantic Cache  │◄──►│ Vector Storage  │                │
│  │ Context Storage │    │ Session State   │    │  GraphRAG Neo4j │                │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘                │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Component Architecture

### 1. Claude-flow Agent Orchestration System

**Component Purpose**: Multi-agent AI coordination with Byzantine fault tolerance
**Research Source**: research/architecture/DOPEMUX_COMPLETE_SYSTEM_v3.md

#### Agent Architecture

```
Claude-flow Agent Hierarchy
┌─────────────────────────────────────────────────────────────────┐
│                    COORDINATION LAYER                          │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │  Master Agent   │◄──►│ Consensus Engine│                   │
│  │  (Orchestra)    │    │    (PBFT)       │                   │
│  └─────────────────┘    └─────────────────┘                   │
│           │                       │                            │
│           ▼                       ▼                            │
├─────────────────────────────────────────────────────────────────┤
│                    SPECIALIST AGENT POOLS                     │
│                                                                │
│  Development Pool      Analysis Pool        Quality Pool      │
│  ┌─────────────┐      ┌─────────────┐     ┌─────────────┐     │
│  │   Coder     │      │  Architect  │     │  Reviewer   │     │
│  │   (8 agents)│      │  (4 agents) │     │  (8 agents) │     │
│  └─────────────┘      └─────────────┘     └─────────────┘     │
│                                                                │
│  ┌─────────────┐      ┌─────────────┐     ┌─────────────┐     │
│  │   Tester    │      │  Debugger   │     │  Optimizer  │     │
│  │   (6 agents)│      │  (4 agents) │     │  (4 agents) │     │
│  └─────────────┘      └─────────────┘     └─────────────┘     │
│                                                                │
│  Support Pool         Integration Pool                        │
│  ┌─────────────┐      ┌─────────────┐                        │
│  │Documentation│      │   DevOps    │                        │
│  │   (4 agents)│      │  (4 agents) │                        │
│  └─────────────┘      └─────────────┘                        │
│                                                                │
│  ADHD Support Pool    Research Pool                          │
│  ┌─────────────┐      ┌─────────────┐                        │
│  │  Cognitive  │      │  Knowledge  │                        │
│  │   (8 agents)│      │  (4 agents) │                        │
│  └─────────────┘      └─────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
Total: 64 Specialized Agents
```

#### Byzantine Fault Tolerance Implementation

**Consensus Protocol**: Practical Byzantine Fault Tolerance (PBFT)
- **Fault Tolerance**: Supports up to (n-1)/3 faulty agents
- **Performance Target**: 84.8% SWE-Bench solve rate
- **Latency**: <500ms for consensus on simple decisions

```python
# PBFT Consensus Implementation Pattern
class AgentConsensus:
    def __init__(self, agent_pool_size):
        self.f = (agent_pool_size - 1) // 3  # Max faulty nodes
        self.min_responses = 2 * self.f + 1

    async def reach_consensus(self, proposal):
        # Three-phase PBFT: pre-prepare, prepare, commit
        responses = await self.broadcast_proposal(proposal)
        if len(responses) >= self.min_responses:
            return self.validate_consensus(responses)
```

#### Agent Communication Protocol

**Message Format**: Structured JSON with semantic metadata
**Transport**: WebSocket connections with Redis pub/sub backup
**Routing**: Content-based routing with priority queues

```json
{
  "agent_id": "coder_007",
  "agent_type": "development",
  "message_type": "code_review_request",
  "priority": "high",
  "context_id": "session_12345",
  "payload": {
    "files": ["src/auth.py"],
    "requirements": ["security", "performance"],
    "deadline": "2025-01-20T15:30:00Z"
  },
  "metadata": {
    "user_adhd_preferences": {
      "feedback_style": "constructive",
      "visual_indicators": true,
      "break_reminders": true
    }
  }
}
```

### 2. Letta Memory Framework Integration

**Component Purpose**: Hierarchical context management with unlimited memory capacity
**Research Source**: research/findings/context-management-frameworks.md:5

#### Three-Tier Memory Architecture

```
Letta Memory Hierarchy
┌─────────────────────────────────────────────────────────────────┐
│                        IN-CONTEXT MEMORY                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Active Working Memory                          │ │
│  │  • Current session state (4K-8K tokens)                   │ │
│  │  • Immediate task context                                  │ │
│  │  • Recent conversation history                             │ │
│  │  • ADHD focus state (hyperfocus timer, break alerts)      │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MEMORY BLOCKS                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Task Memory   │  │ Project Memory  │  │ User Memory     │ │
│  │                 │  │                 │  │                 │ │
│  │ • Current tasks │  │ • Architecture  │  │ • ADHD prefs    │ │
│  │ • Dependencies  │  │ • Design docs   │  │ • Work patterns │ │
│  │ • Progress      │  │ • Code patterns │  │ • Energy levels │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUT-OF-CONTEXT MEMORY                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │               Archival Storage                              │ │
│  │  • Historical sessions (PostgreSQL)                        │ │
│  │  • Long-term project knowledge                             │ │
│  │  • User behavior analytics                                 │ │
│  │  • ADHD pattern analysis and insights                      │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### Memory Operations API

```python
class LettaMemoryManager:
    async def store_context(self, context_type, data, importance_score):
        """Store context with automatic tier assignment"""
        if importance_score > 0.8:
            await self.memory_blocks.store(context_type, data)
        else:
            await self.archival.store(context_type, data)

    async def retrieve_relevant(self, query, max_tokens=2000):
        """Retrieve relevant context within token budget"""
        # Hierarchical search: in-context → blocks → archival
        context = await self.search_hierarchy(query, max_tokens)
        return self.compress_context(context, max_tokens)

    async def update_adhd_state(self, user_id, state_data):
        """Update ADHD-specific state tracking"""
        await self.memory_blocks.update(f"adhd_state_{user_id}", {
            "hyperfocus_duration": state_data.focus_time,
            "break_compliance": state_data.break_taken,
            "energy_level": state_data.current_energy,
            "task_switching_frequency": state_data.switches
        })
```

#### Context Compression Implementation

**Target**: 40-60% token reduction while preserving semantic fidelity
**Method**: Query-aware compression with attention-focused pruning

```python
class ContextCompressor:
    def __init__(self):
        self.importance_threshold = 0.7
        self.adhd_priority_boost = 0.2

    async def compress_context(self, context, target_tokens):
        # Prioritize ADHD-relevant information
        for item in context:
            if self.is_adhd_relevant(item):
                item.importance += self.adhd_priority_boost

        # Apply progressive compression
        compressed = self.remove_low_importance(context)
        if self.count_tokens(compressed) > target_tokens:
            compressed = self.semantic_compression(compressed)

        return compressed
```

### 3. MCP Server Integration Architecture

**Component Purpose**: Standardized tool integration through Model Context Protocol
**Research Source**: research/architecture/DOPEMUX_IMPLEMENTATION_BLUEPRINT.md

#### MCP Server Topology

```
MCP Server Integration Map
┌─────────────────────────────────────────────────────────────────┐
│                    MCP ORCHESTRATION HUB                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Intelligent Router                             │ │
│  │  • Task analysis and server selection                      │ │
│  │  • Load balancing across servers                           │ │
│  │  • Fallback and error handling                             │ │
│  │  • ADHD-aware routing preferences                          │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SPECIALIZED MCP SERVERS                    │
│                                                                 │
│  Core Development        Code Operations      UI & Testing     │
│  ┌─────────────────┐    ┌─────────────────┐  ┌─────────────────┐│
│  │   context7      │    │     serena      │  │     magic       ││
│  │ Documentation   │    │ Symbol Ops     │  │ UI Components   ││
│  │ Framework APIs  │    │ Semantic Search│  │ 21st.dev        ││
│  └─────────────────┘    └─────────────────┘  └─────────────────┘│
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐  ┌─────────────────┐│
│  │ sequential-     │    │   morphllm      │  │   playwright    ││
│  │   thinking      │    │ Pattern Edits   │  │ Browser Testing ││
│  │ Complex Analysis│    │ Bulk Changes    │  │ E2E Validation  ││
│  └─────────────────┘    └─────────────────┘  └─────────────────┘│
│                                                                 │
│  Knowledge & Memory     Task Management     System Ops         │
│  ┌─────────────────┐    ┌─────────────────┐  ┌─────────────────┐│
│  │   claude-       │    │  task-master    │  │      cli        ││
│  │   context       │    │ PRD Processing  │  │ System Commands ││
│  │ Semantic Search │    │ Task Generation │  │ File Operations ││
│  └─────────────────┘    └─────────────────┘  └─────────────────┘│
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐  ┌─────────────────┐│
│  │    conport      │    │      exa        │  │      zen        ││
│  │ Project Memory  │    │ Web Research    │  │ Multi-Model     ││
│  │ Decision Log    │    │ Current Info    │  │ Orchestration   ││
│  └─────────────────┘    └─────────────────┘  └─────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

#### Intelligent Tool Routing

**Routing Logic**: Task type analysis with ADHD preference weighting

```python
class MCPRouter:
    def __init__(self):
        self.server_capabilities = {
            'context7': {'documentation', 'apis', 'frameworks'},
            'magic': {'ui_components', 'design_systems', 'frontend'},
            'sequential-thinking': {'complex_analysis', 'debugging', 'architecture'},
            'serena': {'symbol_operations', 'refactoring', 'semantic_search'},
            'morphllm': {'bulk_edits', 'pattern_changes', 'style_enforcement'}
        }

    async def route_request(self, task, user_preferences):
        # Analyze task requirements
        task_type = self.analyze_task_type(task)

        # Apply ADHD preferences
        if user_preferences.adhd_enabled:
            # Prefer visual tools for UI tasks
            if 'visual' in task_type:
                return self.prioritize_server('magic')
            # Prefer structured analysis for complex tasks
            elif 'complex' in task_type:
                return self.prioritize_server('sequential-thinking')

        # Standard routing logic
        return self.select_optimal_server(task_type)
```

#### MCP Health Monitoring

**Availability Target**: 99.5% server availability
**Monitoring**: Real-time health checks with automated failover

```python
class MCPHealthMonitor:
    async def monitor_server_health(self):
        for server in self.mcp_servers:
            health = await self.check_server_status(server)
            if health.status != 'healthy':
                await self.trigger_fallback(server, health.error)
                await self.notify_administrators(server, health)

    async def trigger_fallback(self, failed_server, error):
        fallback_options = self.get_fallback_servers(failed_server)
        for fallback in fallback_options:
            if await self.check_server_status(fallback).is_healthy():
                await self.route_traffic(failed_server, fallback)
                break
```

---

## Terminal Interface Architecture

### ADHD-Optimized UI Framework

**Component Purpose**: Neurodivergent-friendly terminal interface with cognitive accessibility
**Research Source**: research/findings/adhd-support.md

#### Visual Hierarchy System

```
Terminal Interface Layout
┌─────────────────────────────────────────────────────────────────┐
│                        STATUS BAR                              │
│  Focus Timer: 25:14 │ Energy: ███░░ │ Tasks: 3/7 │ Agents: 12  │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                      MAIN WORKSPACE                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   CODE PANEL    │  │   AGENT PANEL   │  │ CONTEXT PANEL   │ │
│  │                 │  │                 │  │                 │ │
│  │ Active editing  │  │ • Coder_007:    │  │ Current Task:   │ │
│  │ file with       │  │   reviewing     │  │ Implement auth  │ │
│  │ syntax          │  │ • Tester_003:   │  │                 │ │
│  │ highlighting    │  │   writing tests │  │ Dependencies:   │ │
│  │                 │  │ • Reviewer_001: │  │ • User model    │ │
│  │ High contrast   │  │   analyzing     │  │ • JWT library   │ │
│  │ colors for      │  │                 │  │                 │ │
│  │ ADHD focus      │  │ Progress: 67%   │  │ Break in: 11min │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                     COMMAND & FEEDBACK                         │
│  > implement-auth --adhd-mode --break-reminders               │
│  ✅ Authentication scaffold created                             │
│  🔄 Tests generation in progress...                            │
│  ⚠️  Break recommended in 11 minutes (hyperfocus detected)     │
└─────────────────────────────────────────────────────────────────┘
```

#### ADHD-Specific UI Components

**1. Hyperfocus Management**
```python
class HyperfocusTimer:
    def __init__(self, user_preferences):
        self.focus_duration = user_preferences.optimal_focus_time
        self.break_interval = user_preferences.break_interval
        self.gentle_alerts = user_preferences.gentle_mode

    async def monitor_focus_session(self):
        start_time = time.now()
        while self.session_active:
            elapsed = time.now() - start_time

            # 99% of ADHD individuals benefit from focus management
            if elapsed > self.focus_duration * 0.8:  # 80% warning
                await self.show_gentle_alert("Consider a break soon")

            if elapsed > self.focus_duration:
                await self.enforce_break_prompt()
```

**2. RSD-Aware Feedback System**
```python
class RSDFeedbackFormatter:
    def format_feedback(self, feedback_data, severity):
        # 98% of ADHD individuals experience RSD
        if severity == 'error':
            return self.format_constructive_error(feedback_data)
        elif severity == 'improvement':
            return self.format_growth_opportunity(feedback_data)

    def format_constructive_error(self, error):
        return {
            'positive_frame': "Great progress! Here's how to enhance it:",
            'specific_issue': error.description,
            'actionable_steps': error.suggested_fixes,
            'encouragement': "This is a common pattern - you're on the right track!"
        }
```

**3. Working Memory Support**
```python
class WorkingMemorySupport:
    def __init__(self):
        # Effect size g = 0.56 improvement with working memory support
        self.persistent_displays = []
        self.context_reminders = []

    async def maintain_context_visibility(self, current_task):
        context_panel = {
            'current_goal': current_task.objective,
            'progress_indicators': current_task.completion_percentage,
            'next_steps': current_task.upcoming_actions[:3],
            'dependencies': current_task.blocking_items,
            'relevant_files': current_task.file_list
        }

        await self.update_context_display(context_panel)
```

### Voice Input Integration

**Component Purpose**: Hands-free interaction for accessibility and efficiency
**Technology**: Faster-Whisper (4x faster than OpenAI Whisper)

```python
class VoiceInputSystem:
    def __init__(self):
        self.whisper_model = WhisperModel("base", device="cpu")
        self.command_parser = NaturalLanguageCommandParser()

    async def process_voice_command(self, audio_buffer):
        # Transcribe with Faster-Whisper
        segments, info = self.whisper_model.transcribe(audio_buffer)
        transcription = " ".join([s.text for s in segments])

        # Parse natural language commands
        command = await self.command_parser.parse(transcription)

        # Execute with ADHD-aware feedback
        result = await self.execute_command(command)
        return self.format_adhd_feedback(result)
```

---

## Data Persistence Architecture

### Multi-Database Strategy

**Component Purpose**: Optimized storage for different data types and access patterns
**Research Source**: research/findings/context-management-frameworks.md:25

#### Database Topology

```
Data Persistence Layer
┌─────────────────────────────────────────────────────────────────┐
│                    PRIMARY STORAGE LAYER                       │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐  ┌─────────────────┐│
│  │   POSTGRESQL    │    │      REDIS      │  │     QDRANT      ││
│  │   + pgvector    │    │                 │  │                 ││
│  │                 │    │ • Session state │  │ • Vector search ││
│  │ • User data     │◄──►│ • Cache layer   │◄─┤ • Embeddings   ││
│  │ • Project info  │    │ • Real-time     │  │ • Similarity    ││
│  │ • ADHD prefs    │    │   data          │  │   search        ││
│  │ • Task history  │    │ • Pub/sub       │  │ • 626 QPS       ││
│  └─────────────────┘    └─────────────────┘  └─────────────────┘│
│           │                       │                    │        │
│           ▼                       ▼                    ▼        │
├─────────────────────────────────────────────────────────────────┤
│                   SECONDARY STORAGE LAYER                      │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐  ┌─────────────────┐│
│  │     NEO4J       │    │   CLICKHOUSE    │  │   FILE SYSTEM   ││
│  │                 │    │                 │  │                 ││
│  │ • Knowledge     │    │ • Analytics     │  │ • Code repos    ││
│  │   graphs        │    │ • Performance   │  │ • Documents     ││
│  │ • Relationships │    │   metrics       │  │ • Logs          ││
│  │ • GraphRAG      │    │ • Usage stats   │  │ • Artifacts     ││
│  └─────────────────┘    └─────────────────┘  └─────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

#### PostgreSQL + pgvector Configuration

**Purpose**: Primary relational data with vector capabilities
**Performance**: Order-of-magnitude higher throughput than specialized databases

```sql
-- Core schema for Dopemux data
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    adhd_preferences JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    repository_url VARCHAR(500),
    architecture_docs JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE adhd_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_start TIMESTAMP NOT NULL,
    focus_duration INTEGER, -- minutes
    break_compliance BOOLEAN,
    energy_level INTEGER CHECK (energy_level >= 1 AND energy_level <= 10),
    task_switches INTEGER DEFAULT 0,
    hyperfocus_detected BOOLEAN DEFAULT FALSE
);

-- Vector storage for semantic search
CREATE TABLE context_embeddings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    context_type VARCHAR(100),
    content_hash VARCHAR(64),
    embedding vector(1536), -- OpenAI ada-002 dimensions
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast vector similarity search
CREATE INDEX ON context_embeddings USING ivfflat (embedding vector_cosine_ops);
```

#### Redis Semantic Cache Configuration

**Purpose**: Session state and semantic caching
**Performance**: 50-80% latency reduction through intelligent caching

```python
class SemanticCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.similarity_threshold = 0.95

    async def get_cached_response(self, query_embedding):
        # Search for semantically similar queries
        cached_queries = await self.redis.ft().search(
            Query("@embedding:[VECTOR_RANGE $radius $vec]")
            .sort_by("vector_score")
            .paging(0, 1)
            .params({
                "radius": 1 - self.similarity_threshold,
                "vec": query_embedding.tobytes()
            })
        )

        if cached_queries.total > 0:
            return cached_queries.docs[0]
        return None

    async def cache_response(self, query, response, embedding):
        cache_key = f"semantic:{hash(query)}"
        await self.redis.hset(cache_key, mapping={
            "query": query,
            "response": response,
            "embedding": embedding.tobytes(),
            "timestamp": time.time(),
            "access_count": 1
        })
        await self.redis.expire(cache_key, 3600)  # 1 hour TTL
```

#### Qdrant Vector Database Integration

**Purpose**: High-performance vector search and GraphRAG
**Performance**: 626 QPS at 99.5% recall on 1M vectors

```python
from qdrant_client import QdrantClient, models

class QdrantIntegration:
    def __init__(self):
        self.client = QdrantClient("localhost", port=6333)
        self.setup_collections()

    def setup_collections(self):
        # Main collection for document embeddings
        self.client.create_collection(
            collection_name="dopemux_context",
            vectors_config={
                "dense": models.VectorParams(
                    size=1536,
                    distance=models.Distance.COSINE
                ),
                "sparse": models.SparseVectorParams()
            },
            optimizers_config=models.OptimizersConfigDiff(
                default_segment_number=0,
                max_segment_size=20000,
                memmap_threshold=20000
            ),
            quantization_config=models.BinaryQuantization(
                binary=models.BinaryQuantizationConfig(always_ram=True)
            )
        )

    async def hybrid_search(self, query_vector, query_text, limit=10):
        # 20-25% accuracy improvement with hybrid approach
        results = await self.client.search(
            collection_name="dopemux_context",
            query_vector=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="text",
                        match=models.MatchText(text=query_text)
                    )
                ]
            ),
            limit=limit,
            with_payload=True
        )
        return results
```

---

## Integration Patterns

### Leantime Project Management Integration

**Component Purpose**: Neurodivergent-friendly project management with JSON-RPC API
**Research Source**: research/findings/leantime-adhd-integration.md

#### API Integration Architecture

```python
class LeantimeIntegration:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.session = aiohttp.ClientSession()

    async def sync_task_with_sentiment(self, task_data, user_mood):
        # Leantime's emoji sentiment system (angry face to elated unicorn)
        sentiment_mapping = {
            'frustrated': '😠',
            'neutral': '😐',
            'engaged': '🙂',
            'excited': '🦄'
        }

        task_payload = {
            "method": "leantime.rpc.tickets.addTicket",
            "jsonrpc": "2.0",
            "id": f"dopemux_{task_data.id}",
            "params": {
                "headline": task_data.title,
                "type": "task",
                "projectId": task_data.project_id,
                "priority": self.calculate_adhd_priority(task_data, user_mood),
                "sentiment": sentiment_mapping.get(user_mood, '😐'),
                "adhdOptimized": True
            }
        }

        response = await self.call_api(task_payload)
        return response

    def calculate_adhd_priority(self, task, mood):
        # ADHD-specific priority calculation
        base_priority = task.priority

        # Boost priority for tasks matching current energy/mood
        if mood == 'excited' and task.type == 'creative':
            base_priority += 2
        elif mood == 'frustrated' and task.type == 'routine':
            base_priority += 1

        return min(base_priority, 5)  # Cap at highest priority
```

### Task-Master AI Integration

**Component Purpose**: Natural language PRD processing and task decomposition
**Research Source**: research/architecture/leantime-taskmaster-integration.md

```python
class TaskMasterIntegration:
    def __init__(self, project_root):
        self.project_root = project_root
        self.mcp_client = MCPClient()

    async def parse_prd_with_adhd_optimization(self, prd_content):
        # Parse PRD using Task-Master AI
        result = await self.mcp_client.call_tool(
            "task-master-ai__parse_prd",
            {
                "projectRoot": self.project_root,
                "input": prd_content,
                "numTasks": "0",  # Let Task-Master determine complexity
                "adhdOptimized": True  # Enable ADHD-friendly task decomposition
            }
        )

        # Post-process tasks for ADHD patterns
        tasks = result.get('tasks', [])
        optimized_tasks = []

        for task in tasks:
            # Break down tasks longer than 25 minutes (ADHD attention span)
            if task.get('estimatedDuration', 0) > 25:
                subtasks = await self.decompose_task_for_adhd(task)
                optimized_tasks.extend(subtasks)
            else:
                optimized_tasks.append(task)

        return optimized_tasks

    async def decompose_task_for_adhd(self, task):
        # Use Task-Master's complexity analysis for decomposition
        complexity_result = await self.mcp_client.call_tool(
            "task-master-ai__analyze_project_complexity",
            {
                "projectRoot": self.project_root,
                "threshold": 3,  # Lower threshold for ADHD users
                "adhdMode": True
            }
        )

        if complexity_result.get('needsDecomposition'):
            return await self.mcp_client.call_tool(
                "task-master-ai__expand_task",
                {
                    "id": task['id'],
                    "projectRoot": self.project_root,
                    "num": "3-5",  # Optimal subtask count for ADHD
                    "adhdOptimized": True
                }
            )

        return [task]
```

---

## Security and Compliance

### Data Privacy for ADHD Users

**Requirement**: HIPAA-compliant handling of cognitive health data
**Implementation**: End-to-end encryption with user-controlled data retention

```python
class ADHDDataPrivacy:
    def __init__(self):
        self.encryption_key = self.generate_user_key()
        self.retention_policy = {
            'session_data': timedelta(days=30),
            'behavioral_patterns': timedelta(days=365),
            'medical_preferences': 'user_controlled'
        }

    async def encrypt_adhd_data(self, user_data):
        sensitive_fields = [
            'focus_duration', 'energy_levels', 'mood_tracking',
            'medication_schedule', 'therapy_notes'
        ]

        encrypted_data = {}
        for field, value in user_data.items():
            if field in sensitive_fields:
                encrypted_data[field] = self.encrypt_field(value)
            else:
                encrypted_data[field] = value

        return encrypted_data

    async def apply_retention_policy(self, user_id):
        # Automatic data cleanup based on retention rules
        for data_type, retention_period in self.retention_policy.items():
            if retention_period != 'user_controlled':
                await self.cleanup_expired_data(user_id, data_type, retention_period)
```

### AI Agent Security

**Requirement**: Prevent malicious agent behavior and ensure secure multi-agent coordination
**Implementation**: Sandboxed execution with role-based access controls

```python
class AgentSecurityManager:
    def __init__(self):
        self.agent_permissions = {
            'coder': ['read_code', 'write_code', 'run_tests'],
            'reviewer': ['read_code', 'create_feedback'],
            'tester': ['read_code', 'write_tests', 'run_tests'],
            'adhd_support': ['read_user_prefs', 'send_reminders', 'track_focus']
        }

    async def validate_agent_action(self, agent_id, action, target):
        agent_role = self.get_agent_role(agent_id)
        required_permission = self.get_required_permission(action)

        if required_permission not in self.agent_permissions[agent_role]:
            await self.log_security_violation(agent_id, action, target)
            raise SecurityViolation(f"Agent {agent_id} lacks permission for {action}")

        # Additional validation for ADHD-sensitive actions
        if action in ['send_reminder', 'track_focus', 'modify_ui']:
            await self.validate_adhd_action(agent_id, action, target)

        return True
```

---

## Performance and Scalability

### System Performance Targets

**Research Source**: research/findings/context-management-frameworks.md:25

| Component | Target Performance | Measurement Method |
|-----------|-------------------|-------------------|
| Claude-flow Agents | 84.8% SWE-Bench solve rate | Automated benchmark testing |
| Letta Memory | 74% LoCoMo benchmark accuracy | Context recall testing |
| Vector Search | 626 QPS at 99.5% recall | Load testing with Qdrant |
| Context Compression | 40-60% token reduction | Semantic fidelity validation |
| ADHD Features | g = 0.56 effect size improvement | User productivity metrics |
| System Latency | Sub-100ms query response | Real-time monitoring |

### Scaling Architecture

```python
class DopemuxScaler:
    def __init__(self):
        self.performance_thresholds = {
            'agent_utilization': 0.8,
            'memory_usage': 0.75,
            'query_latency': 0.1,  # 100ms
            'user_concurrent': 1000
        }

    async def monitor_and_scale(self):
        metrics = await self.collect_system_metrics()

        # Scale agent pools based on demand
        if metrics.agent_utilization > self.performance_thresholds['agent_utilization']:
            await self.scale_agent_pool(metrics.bottleneck_agent_type)

        # Scale database connections
        if metrics.query_latency > self.performance_thresholds['query_latency']:
            await self.scale_database_pool()

        # Scale MCP servers
        if metrics.mcp_server_load > 0.8:
            await self.scale_mcp_servers(metrics.high_load_servers)

    async def scale_agent_pool(self, agent_type):
        current_pool_size = self.get_agent_pool_size(agent_type)
        target_pool_size = min(current_pool_size * 1.5, 16)  # Cap at 16 per type

        await self.adjust_agent_pool(agent_type, target_pool_size)

        # Maintain Byzantine fault tolerance ratios
        f = (target_pool_size - 1) // 3
        if f * 3 + 1 > target_pool_size:
            await self.adjust_agent_pool(agent_type, f * 3 + 1)
```

---

## Monitoring and Observability

### ADHD-Specific Metrics

```python
class ADHDAnalytics:
    def __init__(self):
        self.cognitive_metrics = [
            'focus_duration_average',
            'task_completion_rate',
            'break_compliance',
            'energy_level_correlation',
            'hyperfocus_frequency',
            'context_switching_rate'
        ]

    async def track_cognitive_performance(self, user_id, session_data):
        metrics = {
            'focus_duration': session_data.focus_time,
            'task_switches': session_data.context_switches,
            'energy_level': session_data.energy_rating,
            'break_taken': session_data.break_compliance,
            'mood_rating': session_data.mood_score
        }

        # Calculate ADHD-specific insights
        insights = await self.calculate_adhd_insights(user_id, metrics)

        # Store for pattern analysis
        await self.store_cognitive_metrics(user_id, metrics, insights)

        return insights

    async def calculate_adhd_insights(self, user_id, current_metrics):
        # Analyze patterns for personalized recommendations
        historical_data = await self.get_user_history(user_id, days=30)

        insights = {
            'optimal_focus_time': self.calculate_optimal_focus_duration(historical_data),
            'energy_patterns': self.analyze_energy_patterns(historical_data),
            'task_type_preferences': self.analyze_task_preferences(historical_data),
            'break_effectiveness': self.analyze_break_patterns(historical_data)
        }

        return insights
```

### System Health Monitoring

```python
class SystemHealthMonitor:
    async def comprehensive_health_check(self):
        health_report = {
            'claude_flow_agents': await self.check_agent_health(),
            'letta_memory': await self.check_memory_system(),
            'mcp_servers': await self.check_mcp_health(),
            'databases': await self.check_database_health(),
            'adhd_features': await self.check_adhd_feature_health()
        }

        overall_health = self.calculate_overall_health(health_report)

        if overall_health < 0.9:  # 90% health threshold
            await self.trigger_alerts(health_report)

        return health_report

    async def check_adhd_feature_health(self):
        # Specific health checks for ADHD features
        checks = {
            'focus_timer_accuracy': await self.validate_timer_precision(),
            'break_reminder_delivery': await self.test_notification_system(),
            'feedback_sentiment_analysis': await self.validate_rsd_filtering(),
            'ui_contrast_levels': await self.check_accessibility_standards()
        }

        return checks
```

---

## Conclusion

This architecture specification provides a comprehensive technical blueprint for implementing Dopemux's Phase 1 development platform. The design emphasizes:

1. **Multi-Agent Coordination**: Byzantine fault-tolerant architecture supporting 64 specialized AI agents
2. **Cognitive Accessibility**: Evidence-based ADHD support with measurable effect sizes
3. **Scalable Infrastructure**: Multi-database approach optimized for different access patterns
4. **Integration Flexibility**: MCP-based tool integration with intelligent routing
5. **Performance Excellence**: Sub-100ms latencies with 99.5% availability targets

The architecture supports the full 5-platform vision while maintaining focus on Phase 1 deliverables, ensuring both immediate value and long-term scalability. All design decisions are backed by research findings and provide clear implementation guidance for development teams.
