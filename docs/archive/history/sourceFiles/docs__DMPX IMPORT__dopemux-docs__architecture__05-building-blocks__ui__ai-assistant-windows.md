# AI Assistant Windows Architecture

## Overview

AI Assistant Windows provide first-class integration for AI coding assistants (Claude Code, Codex, etc.) within the Dopemux terminal environment, enabling seamless AI-assisted development workflows.

## Window Types

### 1. Chat Window

Primary interface for conversational AI interactions with persistent context.

```rust
struct ChatWindow {
    conversation: ConversationHistory,
    context_files: Vec<FileReference>,
    model_selector: ModelSelector,
    token_usage: TokenTracker,
    streaming_buffer: StreamingRenderer,
}

enum MessageType {
    User(UserMessage),
    AI(AIResponse),
    System(SystemNotification),
    Error(ErrorMessage),
}

struct UserMessage {
    content: String,
    attachments: Vec<Attachment>,
    context: ConversationContext,
    timestamp: DateTime<Utc>,
}

struct AIResponse {
    content: String,
    code_blocks: Vec<CodeBlock>,
    suggestions: Vec<ActionSuggestion>,
    confidence: f32,
    token_count: u32,
}
```

#### Visual Layout

```
┌─────────────── AI Chat ───────────────┐
│ Model: Claude-4 | Tokens: 1.2k/200k  │
├───────────────────────────────────────┤
│ 👤 User: Refactor this function       │
│ 🤖 Claude: I'll help you refactor... │
│                                       │
│ ```rust                               │
│ fn improved_function() {              │
│     // Better implementation          │
│ }                                     │
│ ```                                   │
│                                       │
│ Would you like me to apply this?      │
│ [Apply] [Modify] [Explain]           │
├───────────────────────────────────────┤
│ Context: 📄 main.rs, lib.rs          │
│ > Your message here...                │
└───────────────────────────────────────┘
```

### 2. Diff Window

Specialized interface for reviewing and applying AI-generated code changes.

```rust
struct DiffWindow {
    original: CodeBuffer,
    proposed: CodeBuffer,
    diff_engine: DiffRenderer,
    hunk_selector: HunkSelector,
    comments: Vec<InlineComment>,
}

enum DiffMode {
    SideBySide,
    Unified,
    Inline,
}

struct HunkSelector {
    hunks: Vec<DiffHunk>,
    selected: HashSet<usize>,
    actions: HunkActions,
}

enum HunkAction {
    Accept,
    Reject,
    Modify,
    Comment,
}
```

#### Visual Layout

```
┌─────────────── Code Diff ─────────────────┐
│ 📁 src/main.rs | +12 -8 | Modified      │
├──────────────┬────────────────────────────┤
│   Original   │       AI Proposed          │
├──────────────┼────────────────────────────┤
│  1 fn calc() │  1 fn calculate_total() {  │
│  2   let x   │  2   let amount = get_amt();│
│  3   ...     │  3   let tax = calc_tax(); │
│              │  4   amount + tax          │
│  4 }         │  5 }                       │
├──────────────┴────────────────────────────┤
│ 🟢 Hunk 1/3: Function rename & logic     │
│ [✓ Accept] [✗ Reject] [📝 Modify]        │
│                                           │
│ 💬 AI: Renamed for clarity and added... │
└───────────────────────────────────────────┘
```

### 3. Generation Window

Real-time streaming interface for AI code generation with progress tracking.

```rust
struct GenerationWindow {
    prompt: GenerationPrompt,
    stream: ResponseStream,
    progress: ProgressIndicator,
    controls: GenerationControls,
    output_buffer: StreamingCodeBuffer,
}

struct GenerationPrompt {
    instruction: String,
    context: CodeContext,
    template: Option<Template>,
    constraints: GenerationConstraints,
}

enum GenerationStatus {
    Thinking,
    Generating,
    Complete,
    Error(String),
    Cancelled,
}
```

#### Visual Layout

```
┌─────────── AI Code Generation ────────────┐
│ Task: Implement user authentication      │
├───────────────────────────────────────────┤
│ Status: 🤖 Generating... | 45% complete  │
│ ████████████████████░░░░░░░░░░░░░░░░░░░   │
│                                           │
│ ```rust                                   │
│ use bcrypt::{hash, verify, DEFAULT_COST}; │
│                                           │
│ pub struct AuthService {                  │
│     db: DatabasePool,                     │
│ }                                         │
│                                           │
│ impl AuthService {                        │
│     pub fn new(db: DatabasePool) -> Self {│
│         Self { db }                       │ ▓
│     }                                     │
│                                           │
│ ```                                       │
│                                           │
│ [⏸️ Pause] [⏹️ Cancel] [⚙️ Settings]      │
└───────────────────────────────────────────┘
```

### 4. Context Window

Context management interface showing relevant files, symbols, and documentation.

```rust
struct ContextWindow {
    file_tree: SelectableFileTree,
    symbol_browser: SymbolBrowser,
    memory_results: RAGResults,
    documentation: DocViewer,
    context_builder: ContextBuilder,
}

struct ContextBuilder {
    selected_files: Vec<FilePath>,
    selected_symbols: Vec<Symbol>,
    context_size: usize,
    auto_selection: bool,
}
```

#### Visual Layout

```
┌─────────── Context Manager ───────────────┐
│ Auto-select: ✅ | Size: 8.2k/200k tokens │
├───────────────────────────────────────────┤
│ 📁 Selected Files                        │
│ ✅ src/auth.rs           2.1k tokens     │
│ ✅ src/models/user.rs    1.8k tokens     │
│ ⬜ src/handlers.rs       3.2k tokens     │
│                                           │
│ 🔍 Relevant Symbols                      │
│ ✅ User::authenticate()                   │
│ ✅ hash_password()                        │
│ ⬜ Session::create()                      │
│                                           │
│ 📚 Documentation                         │
│ • Bcrypt crate docs                      │
│ • JWT authentication                     │
│ • Database session mgmt                  │
│                                           │
│ [🔄 Refresh] [➕ Add] [✂️ Optimize]     │
└───────────────────────────────────────────┘
```

## AI Integration Patterns

### Command Interface

```rust
enum AICommand {
    // Inline operations
    Complete { cursor: Position },
    Refactor { range: Range, instruction: String },
    Explain { symbol: Symbol },
    Fix { diagnostic: Diagnostic },

    // Multi-file operations
    Implement { spec: String, files: Vec<Path> },
    Review { changes: Vec<Diff> },
    Test { module: Module },

    // Chat operations
    Ask { question: String, context: Context },
    Continue { session: SessionId },
}

struct AICommandProcessor {
    active_models: Vec<ModelConnection>,
    context_manager: ContextManager,
    command_history: CommandHistory,
    response_cache: ResponseCache,
}
```

### Interaction Flows

#### Selection → AI Flow

```yaml
interaction_pattern:
  trigger: "Select code + AI hotkey"
  steps:
    1. capture_selection:
        - text: selected_code
        - context: surrounding_code + imports
        - cursor_position: exact_location

    2. open_ai_panel:
        - window: chat_window
        - prepopulate: selection_context
        - suggest_actions: [explain, refactor, fix, test]

    3. ai_processing:
        - analyze: code_semantics
        - generate: contextual_suggestions
        - stream: real_time_response

    4. user_interaction:
        - review: suggestions_in_diff_window
        - modify: adjust_before_applying
        - apply: integrate_changes
```

#### AI → Editor Flow

```yaml
integration_pattern:
  ai_generates_code:
    1. preview_in_diff: side_by_side_comparison
    2. validate_syntax: real_time_checking
    3. user_approval: accept/modify/reject_hunks
    4. apply_changes: atomic_file_updates
    5. auto_format: consistent_style
    6. trigger_tests: validation_workflow

  continuous_assistance:
    1. watch_for_errors: syntax + semantic
    2. proactive_suggestions: background_analysis
    3. context_awareness: maintain_conversation
    4. learning_adaptation: user_preference_tracking
```

### Multi-Model Support

```rust
enum ModelProvider {
    Anthropic { model: AnthropicModel },
    OpenAI { model: OpenAIModel },
    Local { model: LocalModel },
    Custom { endpoint: Url, auth: Auth },
}

struct ModelSelector {
    available_models: Vec<ModelProvider>,
    routing_rules: RoutingRules,
    fallback_chain: Vec<ModelProvider>,
    performance_metrics: ModelMetrics,
}

struct RoutingRules {
    by_task_type: HashMap<TaskType, ModelProvider>,
    by_context_size: Vec<(Range<usize>, ModelProvider)>,
    by_performance_req: HashMap<PerformanceClass, ModelProvider>,
    by_cost_limit: HashMap<CostTier, ModelProvider>,
}
```

## Window Orchestration

### State Management

```rust
struct AIWindowManager {
    active_windows: HashMap<WindowId, AIWindow>,
    focus_stack: Vec<WindowId>,
    layout_manager: LayoutManager,
    event_bus: EventBus,
}

enum AIWindowEvent {
    MessageReceived(WindowId, Message),
    GenerationComplete(WindowId, Result<String>),
    ContextChanged(WindowId, Context),
    UserAction(WindowId, UserAction),
    WindowClosed(WindowId),
}

impl AIWindowManager {
    fn handle_event(&mut self, event: AIWindowEvent) {
        match event {
            AIWindowEvent::MessageReceived(id, msg) => {
                self.route_to_window(id, msg);
                self.update_context_windows();
            }
            AIWindowEvent::GenerationComplete(id, result) => {
                self.show_diff_window(result);
                self.notify_completion();
            }
            // ... other events
        }
    }
}
```

### Inter-Window Communication

```rust
struct WindowCommunication {
    message_bus: MessageBus,
    shared_state: SharedState,
    synchronization: SyncManager,
}

enum WindowMessage {
    ContextUpdate(Context),
    CodeChange(CodeDiff),
    SelectionChanged(Selection),
    ModelSwitched(ModelProvider),
    ErrorOccurred(Error),
}

trait AIWindow {
    fn handle_message(&mut self, message: WindowMessage);
    fn get_state(&self) -> WindowState;
    fn subscribe_to(&self) -> Vec<MessageType>;
}
```

## Performance Optimization

### Streaming and Caching

```rust
struct StreamingOptimizer {
    chunk_buffer: ChunkBuffer,
    render_scheduler: RenderScheduler,
    background_processing: BackgroundProcessor,
}

struct ResponseCache {
    prompt_cache: LRUCache<PromptHash, Response>,
    context_cache: LRUCache<ContextHash, ProcessedContext>,
    model_cache: HashMap<ModelId, ModelConnection>,
    ttl_manager: TTLManager,
}
```

### Resource Management

```yaml
resource_limits:
  memory_per_window: 50MB
  max_concurrent_requests: 3
  context_cache_size: 100MB
  response_history: 1000_messages

performance_targets:
  response_start: <2s
  streaming_latency: <200ms
  window_switching: <100ms
  memory_cleanup: automatic
```

## ADHD Accommodations

### Attention Management

```rust
struct ADHDSupport {
    attention_tracking: AttentionTracker,
    distraction_shield: DistractionShield,
    progress_indicators: ProgressManager,
    break_suggestions: BreakManager,
}

enum AttentionSignal {
    LowFocus,
    ContextSwitching,
    OverStimulation,
    FlowState,
}
```

### Cognitive Load Reduction

```yaml
adhd_optimizations:
  visual_simplification:
    - reduce_visual_clutter: true
    - highlight_active_areas: true
    - minimize_simultaneous_windows: 2

  interaction_support:
    - clear_action_buttons: true
    - progress_visibility: prominent
    - completion_confirmation: gentle

  memory_assistance:
    - context_preservation: automatic
    - conversation_history: persistent
    - recent_actions: visible
```

## Quality Assurance

### Testing Strategy

1. **Window Rendering**: Cross-terminal compatibility
2. **AI Integration**: Response handling and error recovery
3. **Performance**: Memory usage and response times
4. **Accessibility**: Keyboard navigation and screen readers
5. **ADHD Testing**: Cognitive load assessment

### Monitoring

```rust
struct WindowMetrics {
    response_times: Histogram,
    memory_usage: Gauge,
    user_interactions: Counter,
    error_rates: Counter,
    satisfaction_scores: Histogram,
}
```