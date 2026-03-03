# Intelligent Memory Layer - Complete System Architecture

**Version**: 1.0
**Date**: 2025-09-22
**Status**: Design Phase

## Overview

The Intelligent Memory Layer transforms Dopemux from a manual memory system into an intelligent, implicit context preservation platform. This document provides the complete technical architecture for implementing AI-powered memory capture, classification, and retrieval.

## System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEVELOPER ENVIRONMENT                       │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Git Repos     │   Claude Code   │    Shell/Terminal           │
│   File System   │   Conversations │    Editor/IDE               │
└─────────────────┴─────────────────┴─────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              INTELLIGENT MEMORY LAYER                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Capture   │  │  Classify   │  │       Enrich &          │  │
│  │   Events    │  │ & Extract   │  │    Store Memories       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               MEMORY STORAGE LAYER                             │
│         PostgreSQL (Truth) + Milvus (Vectors)                 │
└─────────────────────────────────────────────────────────────────┘
```

## Core Architecture Components

### 1. Event Collection Layer

#### Universal Event Collector
**Purpose**: Capture all development activities with zero latency impact

```python
class UniversalEventCollector:
    """Zero-latency event capture from all sources"""

    def __init__(self):
        self.event_queue = AsyncQueue(maxsize=10000)
        self.redis_backup = RedisQueue("dopemux:events")
        self.sources = self._register_sources()

    async def capture_event(self, source: str, raw_event: dict) -> str:
        """Capture event with <10ms guarantee"""

        event = EnrichedEvent(
            id=uuid4(),
            timestamp=datetime.now(),
            source=source,
            raw_data=raw_event,
            context=await self._get_current_context(),
            status=EventStatus.CAPTURED
        )

        # Non-blocking queue insertion
        try:
            self.event_queue.put_nowait(event)
        except QueueFull:
            await self.redis_backup.push(event)  # Fallback to Redis

        # Immediate visual feedback
        await self._show_capture_indicator(source)

        return event.id
```

#### Context Enrichment
**Purpose**: Add environmental context to all captured events

```python
class ContextEnricher:
    """Enrich events with current development context"""

    async def get_current_context(self) -> DevelopmentContext:
        """Gather current development state"""

        return DevelopmentContext(
            # Git context
            repository=git.get_current_repo(),
            branch=git.get_current_branch(),
            commit_hash=git.get_current_commit(),
            uncommitted_changes=git.has_uncommitted_changes(),

            # File system context
            working_directory=os.getcwd(),
            open_files=self._get_open_files(),
            recent_file_changes=self._get_recent_changes(minutes=30),

            # Session context
            session_id=self.session_tracker.current_session_id,
            session_duration=self.session_tracker.get_duration(),
            last_context_switch=self.session_tracker.last_context_switch,

            # ADHD-specific context
            attention_state=self.attention_monitor.current_state,
            focus_session_length=self.attention_monitor.focus_duration,
            recent_breaks=self.attention_monitor.recent_breaks,

            # Application context
            claude_conversation_id=self._get_active_conversation(),
            editor_context=self._get_editor_state(),
            terminal_context=self._get_terminal_state()
        )
```

### 2. Classification Engine

#### Hybrid Classification Pipeline
**Purpose**: Fast pattern matching with AI fallback for complex cases

```python
class HybridClassificationEngine:
    """Two-tier classification: patterns then AI"""

    def __init__(self):
        self.pattern_classifier = FastPatternClassifier()
        self.ai_classifier = AIClassificationService()
        self.confidence_threshold = 0.7

    async def classify_event(self, event: EnrichedEvent) -> ClassificationResult:
        """Classify with hybrid approach"""

        # Tier 1: Fast pattern matching (<10ms)
        pattern_result = self.pattern_classifier.classify(
            text=event.extract_text(),
            context=event.context,
            source=event.source
        )

        if pattern_result and pattern_result.confidence > self.confidence_threshold:
            return pattern_result

        # Tier 2: AI classification (async)
        ai_result = await self.ai_classifier.classify_with_extraction(
            text=event.extract_text(),
            context=event.context,
            previous_attempts=[pattern_result] if pattern_result else []
        )

        return ai_result or pattern_result or self._create_fallback_classification()
```

#### Fast Pattern Classifier
**Purpose**: Rule-based classification for common development patterns

```python
class FastPatternClassifier:
    """Local pattern-based classification"""

    CLASSIFICATION_RULES = {
        MemoryType.DECISION: [
            # Git commit patterns
            r'^(feat|feature)(\(.+\))?: .+',
            r'^(add|implement|create): .+',

            # Conversation patterns
            r'(?i)\b(decided?|chose|going with|let\'s use|we\'ll use)\b',
            r'(?i)\b(switched to|migrated to|adopted|selected)\b',

            # Architecture decisions
            r'(?i)\b(architecture|design|approach|strategy)\b.*\b(decision|choice)\b'
        ],

        MemoryType.TASK: [
            r'(?i)\b(todo|fixme|hack|bug|issue)\b',
            r'(?i)\b(need to|must|should|have to|will)\b',
            r'^(fix|refactor|improve|optimize|update): .+',
        ],

        MemoryType.PROBLEM: [
            r'(?i)\b(error|fail|broken|issue|bug|problem)\b',
            r'(?i)\b(doesn\'t work|not working|failing)\b',
            r'(?i)\b(confused|stuck|unclear)\b',
        ],

        MemoryType.SOLUTION: [
            r'(?i)\b(fixed|solved|resolved|working)\b',
            r'^(fix|resolve): .+',
            r'(?i)\b(found the issue|figured out)\b',
        ],

        MemoryType.QUESTION: [
            r'(?i)^(why|how|what|when|where|which|who).+\?',
            r'(?i)\b(question|wondering|curious)\b',
        ]
    }

    CONTEXT_BOOSTS = {
        'git_commit': {
            MemoryType.DECISION: 1.3,  # Commits are often decisions
            MemoryType.SOLUTION: 1.2   # Commits often solve problems
        },
        'claude_message': {
            MemoryType.QUESTION: 1.2,  # Conversations contain questions
            MemoryType.DECISION: 1.1   # Discussions lead to decisions
        },
        'test_failure': {
            MemoryType.PROBLEM: 1.5    # Test failures are problems
        }
    }

    def classify(self, text: str, context: DevelopmentContext, source: str) -> Optional[ClassificationResult]:
        """Fast rule-based classification"""

        scores = {}

        # Check all pattern rules
        for memory_type, patterns in self.CLASSIFICATION_RULES.items():
            score = 0.0

            for pattern in patterns:
                if re.search(pattern, text):
                    score += 1.0

            # Apply context boosts
            if source in self.CONTEXT_BOOSTS:
                boost = self.CONTEXT_BOOSTS[source].get(memory_type, 1.0)
                score *= boost

            if score > 0:
                scores[memory_type] = score

        if not scores:
            return None

        # Return highest scoring classification
        best_type = max(scores.keys(), key=lambda k: scores[k])
        confidence = min(scores[best_type] / 3.0, 1.0)  # Normalize to 0-1

        return ClassificationResult(
            memory_type=best_type,
            confidence=confidence,
            method='pattern_matching',
            matched_patterns=[pattern for pattern in self.CLASSIFICATION_RULES[best_type]
                            if re.search(pattern, text)]
        )
```

### 3. AI Classification Service

#### LLM-Powered Classification
**Purpose**: Handle nuanced content that patterns can't classify

```python
class AIClassificationService:
    """LLM-powered intelligent classification"""

    def __init__(self, privacy_config: PrivacyConfig):
        self.privacy_config = privacy_config
        self.llm_client = self._create_llm_client()
        self.content_filter = SensitiveContentFilter()

    async def classify_with_extraction(self, text: str, context: DevelopmentContext) -> ClassificationResult:
        """Classify and extract metadata in one pass"""

        # Apply privacy filtering
        filtered_text = await self._apply_privacy_filtering(text, context)

        # Create classification prompt
        prompt = self._create_classification_prompt(filtered_text, context)

        try:
            # Get structured response from LLM
            response = await self.llm_client.get_structured_response(
                prompt=prompt,
                response_schema=ClassificationResponseSchema
            )

            return ClassificationResult(
                memory_type=MemoryType(response.memory_type),
                confidence=response.confidence,
                method='ai_classification',
                extracted_metadata=response.metadata,
                suggested_relationships=response.relationships,
                summary=response.summary,
                privacy_level=self.privacy_config.get_processing_level()
            )

        except Exception as e:
            logger.warning(f"AI classification failed: {e}")
            return self._create_fallback_result()

    def _create_classification_prompt(self, text: str, context: DevelopmentContext) -> str:
        """Create AI prompt for classification"""

        return f"""
        Analyze this development activity and classify it:

        Context:
        - Source: {context.source}
        - Repository: {context.repository}
        - Branch: {context.branch}
        - Session Duration: {context.session_duration}
        - Recent Files: {context.recent_file_changes[:3]}

        Content: {text}

        Classify as one of: decision, task, problem, solution, observation, question

        Return JSON:
        {{
            "memory_type": "decision|task|problem|solution|observation|question",
            "confidence": 0.0-1.0,
            "summary": "one line summary of the content",
            "metadata": {{
                "priority": "high|medium|low",
                "status": "planned|in_progress|completed|blocked",
                "entities": ["list", "of", "mentioned", "technologies", "files"],
                "tags": ["relevant", "tags"]
            }},
            "relationships": [
                {{
                    "type": "affects|depends_on|implements|solves|discusses",
                    "target": "file.py|previous_decision_id|task_id",
                    "confidence": 0.0-1.0,
                    "reason": "why this relationship exists"
                }}
            ]
        }}
        """
```

### 4. Relationship Intelligence Engine

#### Automatic Relationship Discovery
**Purpose**: Find connections between memories without manual linking

```python
class RelationshipInferenceEngine:
    """Discover relationships between memories"""

    def __init__(self):
        self.recent_memory_cache = RecentMemoryCache(size=1000)
        self.file_tracker = FileChangeTracker()
        self.conversation_tracker = ConversationTracker()

    async def infer_relationships(self, new_memory: ClassifiedMemory, context: DevelopmentContext) -> List[Relationship]:
        """Find relationships for new memory"""

        relationships = []

        # Temporal proximity relationships
        relationships.extend(await self._find_temporal_relationships(new_memory, context))

        # File-based relationships
        relationships.extend(await self._find_file_relationships(new_memory, context))

        # Conversation flow relationships
        relationships.extend(await self._find_conversation_relationships(new_memory, context))

        # Problem-solution relationships
        relationships.extend(await self._find_problem_solution_relationships(new_memory, context))

        # Semantic similarity relationships
        relationships.extend(await self._find_semantic_relationships(new_memory, context))

        return relationships

    async def _find_temporal_relationships(self, memory: ClassifiedMemory, context: DevelopmentContext) -> List[Relationship]:
        """Find relationships based on temporal proximity"""

        relationships = []

        # Find recent memories (last 2 hours)
        recent_memories = self.recent_memory_cache.get_memories_since(
            datetime.now() - timedelta(hours=2)
        )

        for recent_memory in recent_memories:
            # Decision followed by implementation
            if (recent_memory.type == MemoryType.DECISION and
                memory.type in [MemoryType.TASK, MemoryType.SOLUTION] and
                self._contexts_overlap(recent_memory.context, context)):

                relationships.append(Relationship(
                    from_id=recent_memory.id,
                    to_id=memory.id,
                    relation_type="motivates",
                    confidence=0.8,
                    metadata={"temporal_gap": str(memory.timestamp - recent_memory.timestamp)}
                ))

            # Problem followed by solution
            if (recent_memory.type == MemoryType.PROBLEM and
                memory.type == MemoryType.SOLUTION and
                self._similar_context(recent_memory.context, context)):

                relationships.append(Relationship(
                    from_id=memory.id,
                    to_id=recent_memory.id,
                    relation_type="solves",
                    confidence=0.9,
                    metadata={"solution_time": str(memory.timestamp - recent_memory.timestamp)}
                ))

        return relationships

    async def _find_file_relationships(self, memory: ClassifiedMemory, context: DevelopmentContext) -> List[Relationship]:
        """Find relationships based on file interactions"""

        relationships = []

        # Git commit relationships
        if context.source == 'git_commit':
            changed_files = git.get_changed_files(context.commit_hash)

            for file_path in changed_files:
                # Create or find file node
                file_node = await self._get_or_create_file_node(file_path)

                relationships.append(Relationship(
                    from_id=memory.id,
                    to_id=file_node.id,
                    relation_type="modifies",
                    confidence=1.0,
                    metadata={"commit": context.commit_hash, "file_path": file_path}
                ))

        # Editor activity relationships
        if context.open_files:
            for file_path in context.open_files:
                # Find recent decisions about this file
                file_decisions = await self._find_decisions_about_file(file_path)

                for decision in file_decisions:
                    relationships.append(Relationship(
                        from_id=decision.id,
                        to_id=memory.id,
                        relation_type="influences",
                        confidence=0.6,
                        metadata={"file_context": file_path}
                    ))

        return relationships
```

### 5. Storage Router

#### Context-Aware Storage Strategy
**Purpose**: Intelligently route memories to appropriate storage

```python
class ContextAwareStorageRouter:
    """Route memories based on importance and context"""

    def __init__(self):
        self.importance_scorer = MemoryImportanceScorer()
        self.postgres_storage = PostgreSQLMemoryStorage()
        self.milvus_storage = MilvusVectorStorage()

    async def route_and_store(self, classified_memory: ClassifiedMemory, relationships: List[Relationship]) -> StorageResult:
        """Route memory to appropriate storage layers"""

        # Calculate importance score
        importance = self.importance_scorer.calculate_importance(
            classified_memory,
            classified_memory.context
        )

        # Create storage plan
        storage_plan = self._create_storage_plan(classified_memory, importance)

        # Execute storage plan
        results = StorageResult()

        # Always store in PostgreSQL (truth layer)
        results.postgres_result = await self.postgres_storage.store_memory(
            classified_memory,
            relationships
        )

        # Conditionally store in Milvus (vector layer)
        if storage_plan.should_vectorize:
            results.milvus_result = await self.milvus_storage.store_memory(
                classified_memory,
                storage_plan.embedding_options
            )

        # Store relationships
        results.relationships_result = await self.postgres_storage.store_relationships(
            relationships
        )

        return results

    def _create_storage_plan(self, memory: ClassifiedMemory, importance: float) -> StoragePlan:
        """Create storage strategy based on memory characteristics"""

        plan = StoragePlan()

        # High importance: full treatment
        if importance >= 0.7:
            plan.should_vectorize = True
            plan.embedding_quality = "high"
            plan.proactive_surfacing = True

        # Medium importance: selective treatment
        elif importance >= 0.4:
            plan.should_vectorize = self._should_vectorize_medium_importance(memory)
            plan.embedding_quality = "medium"
            plan.proactive_surfacing = False

        # Low importance: minimal treatment
        else:
            plan.should_vectorize = False
            plan.embedding_quality = None
            plan.proactive_surfacing = False

        return plan
```

### 6. Proactive Surfacing Engine

#### Context-Aware Memory Retrieval
**Purpose**: Surface relevant memories when context changes

```python
class ProactiveMemorySurfacing:
    """Intelligently surface memories based on context"""

    def __init__(self):
        self.context_monitor = ContextChangeMonitor()
        self.memory_retriever = MemoryRetriever()
        self.surfacing_policy = SurfacingPolicy()

    async def monitor_and_surface(self):
        """Background monitoring for context changes"""

        async for context_change in self.context_monitor.watch_context_changes():

            if self.surfacing_policy.should_check_for_memories(context_change):
                relevant_memories = await self._find_contextually_relevant_memories(context_change)

                if relevant_memories and self.surfacing_policy.should_surface(context_change, relevant_memories):
                    await self._gentle_surface_memories(relevant_memories, context_change)

    async def _find_contextually_relevant_memories(self, context_change: ContextChange) -> List[Memory]:
        """Find memories relevant to context change"""

        relevant_memories = []

        # File-based relevance
        if context_change.type == ContextChangeType.FILE_OPENED:
            # Find decisions about this file
            file_decisions = await self.memory_retriever.find_memories_about_file(
                context_change.file_path,
                memory_types=[MemoryType.DECISION, MemoryType.PROBLEM],
                max_age=timedelta(days=30)
            )
            relevant_memories.extend(file_decisions)

        # Directory-based relevance
        elif context_change.type == ContextChangeType.DIRECTORY_CHANGED:
            # Find decisions about this area of codebase
            area_memories = await self.memory_retriever.find_memories_in_directory_area(
                context_change.directory,
                memory_types=[MemoryType.DECISION, MemoryType.OBSERVATION],
                max_age=timedelta(days=7)
            )
            relevant_memories.extend(area_memories)

        # Break recovery
        elif context_change.type == ContextChangeType.RETURN_FROM_BREAK:
            # Find recent work context
            recent_work = await self.memory_retriever.find_recent_work_context(
                max_age=timedelta(hours=4),
                min_importance=0.5
            )
            relevant_memories.extend(recent_work)

        return relevant_memories

    async def _gentle_surface_memories(self, memories: List[Memory], context_change: ContextChange):
        """Surface memories in ADHD-friendly way"""

        # Create gentle notification
        notification = GentleMemoryNotification(
            title=f"📝 Context: {context_change.description}",
            memories=memories[:3],  # Limit to avoid overwhelming
            style="minimal",  # ADHD-friendly minimal style
            auto_dismiss=True,
            position="bottom_right"
        )

        # Show notification with escape hatch
        await notification.show_with_dismiss_option()

        # Log for transparency
        self._log_surfacing_event(memories, context_change)
```

## Integration Points

### Git Hook Integration
```bash
#!/bin/bash
# .git/hooks/post-commit (auto-installed by dopemux init)

# Capture commit with zero latency
{
    echo "source: git_commit"
    echo "commit_hash: $(git rev-parse HEAD)"
    echo "message: $GIT_COMMIT_MESSAGE"
    echo "files_changed: $(git diff-tree --no-commit-id --name-only -r HEAD)"
    echo "author: $(git config user.name)"
    echo "timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | dopemux-capture git_commit &

# Never block git operations
exit 0
```

### Shell Command Integration
```bash
# ~/.dopemux/shell_integration.sh (sourced in .bashrc/.zshrc)

# Transparent command wrappers
cd() {
    dopemux-capture context_switch "from:$PWD to:$1" &
    builtin cd "$@"

    # Trigger context-aware memory surfacing
    dopemux-surface-context &
}

# Test failure capture
pytest() {
    local exit_code
    command pytest "$@"
    exit_code=$?

    if [ $exit_code -ne 0 ]; then
        dopemux-capture test_failure "pytest failed in $PWD: $*" &
    fi

    return $exit_code
}

# Git command wrapper
git() {
    command git "$@"
    local exit_code=$?

    # Capture git operations for context
    if [[ "$1" == "checkout" || "$1" == "switch" ]]; then
        dopemux-capture git_branch_switch "switched to: $2" &
    fi

    return $exit_code
}
```

### Claude Code Integration
```python
# ~/.claude/hooks/memory_integration.py

async def on_message_sent(message: Message, context: ConversationContext):
    """Capture substantive Claude Code messages"""

    # Skip trivial messages
    if len(message.content) < 50 or message.is_navigation_only():
        return

    # Capture with context
    await dopemux_capture('claude_message', {
        'content': message.content,
        'role': message.role,
        'conversation_id': context.conversation_id,
        'context_files': context.open_files,
        'tool_calls': message.tool_calls,
        'session_duration': context.session_duration
    })

async def on_tool_call_result(tool_call: ToolCall, result: ToolResult):
    """Capture significant tool call results"""

    if tool_call.tool in ['edit', 'write', 'multiedit']:
        # File modification events
        await dopemux_capture('file_modification', {
            'tool': tool_call.tool,
            'files_modified': result.modified_files,
            'change_summary': result.summary,
            'conversation_context': result.conversation_id
        })
```

## Performance Specifications

### Latency Requirements
- **Event Capture**: <10ms (guaranteed, ADHD-critical)
- **Pattern Classification**: <50ms (local processing)
- **Memory Storage**: <200ms (PostgreSQL + Milvus)
- **Context Surfacing**: <500ms (background, non-blocking)

### Throughput Targets
- **Event Processing**: 1000+ events/minute sustained
- **Concurrent Classifications**: 10+ simultaneous AI calls
- **Memory Queries**: 100+ searches/minute
- **Relationship Inference**: 50+ relationships/minute

### Resource Usage
- **Memory Footprint**: <1GB baseline + 2GB for AI models
- **Storage Growth**: ~100MB/month per active developer
- **CPU Usage**: <5% baseline, burst to 50% during processing
- **Network**: Minimal for local AI, variable for cloud AI

This architecture provides the foundation for truly implicit memory capture while maintaining the performance and reliability requirements for ADHD-optimized development workflows.