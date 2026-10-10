# ADR-011: ADHD Accommodation Technical Decisions

## Status
**Accepted** - Comprehensive ADHD support through terminal-optimized accommodations

## Context

Dopemux is designed as an ADHD-accommodated development platform. Academic research shows:

- **Large magnitude deficits (d = 1.62-2.03)** in working memory for ADHD individuals
- **75-81% experience significant executive function impairments**
- **25-40% consistent time underestimation** with temporal processing difficulties
- **87-93% accuracy** achieved by AI-powered support systems for ADHD

The technical implementation must address core ADHD challenges while maintaining high performance and professional development capabilities.

## Decision

**Multi-layered ADHD Support System** integrated throughout Dopemux architecture:
1. **Automatic Detection and Adaptation** using AI-powered pattern recognition
2. **Terminal-Optimized Interfaces** designed for ADHD cognitive patterns
3. **Executive Function Scaffolding** through intelligent automation
4. **Working Memory Augmentation** via external memory systems
5. **Attention Management** through visual and temporal accommodations

## Core ADHD Challenges and Technical Solutions

### 1. Working Memory Deficits
**Problem**: Difficulty maintaining context across files, commands, and tasks

**Technical Implementation**:
```python
class WorkingMemorySupport:
    def __init__(self):
        self.context_buffer = deque(maxlen=20)  # External memory scaffold
        self.command_aliases = {}  # Reduce cognitive load

    def auto_context_preservation(self, terminal_state):
        """Automatically save context during task switches"""
        context = {
            'working_directory': os.getcwd(),
            'active_files': self.get_open_files(),
            'recent_commands': self.get_command_history(-10),
            'git_status': self.capture_git_state(),
            'timestamp': datetime.now()
        }
        self.context_buffer.append(context)
        return self.generate_context_summary(context)

    def smart_command_completion(self, partial_command):
        """Context-aware command completion"""
        recent_patterns = self.analyze_command_patterns()
        return self.suggest_commands(partial_command, recent_patterns)
```

### 2. Time Blindness and Temporal Processing
**Problem**: 25-40% time underestimation, delayed circadian rhythms, temporal distortion

**Technical Implementation**:
```go
type ADHDTimeDisplay struct {
    analogClock   *AnalogClockWidget  // Superior to digital for ADHD
    timeRemaining *VisualCountdown    // Concrete time representation
    sessionTimer  *PomodoroTracker    // 25-minute focus chunks
}

func (t *ADHDTimeDisplay) Render() string {
    remaining := t.timeRemaining.Minutes()
    var color string
    switch {
    case remaining < 5:
        color = "\033[1;31m"  // Bold red - urgent
    case remaining < 15:
        color = "\033[1;33m"  // Yellow - warning
    default:
        color = "\033[0;32m"  // Green - comfortable
    }
    return fmt.Sprintf("%s⏰ %d minutes remaining\033[0m", color, remaining)
}

func (t *ADHDTimeDisplay) ProvideTimeAnchors() {
    // Provide multiple time references for temporal grounding
    t.ShowSystemTime()
    t.ShowSessionElapsed()
    t.ShowNextDeadline()
    t.ShowFocusSessionRemaining()
}
```

### 3. Executive Function Impairments
**Problem**: Difficulty with planning, task initiation, and organization

**Technical Implementation**:
```yaml
executive_function_scaffolding:
  automated_planning:
    task_decomposition: AI breaks large tasks into 25-minute chunks
    dependency_mapping: Automatic prerequisite identification
    progress_tracking: Visual progress indicators

  decision_support:
    option_reduction: Limit choices to 3-5 options maximum
    default_suggestions: Intelligent defaults based on context
    undo_capability: Safe exploration with easy reversal

  initiation_support:
    gentle_prompts: Non-intrusive task initiation reminders
    momentum_preservation: Maintain flow state through automation
    friction_reduction: Minimize steps between intention and action
```

### 4. Attention and Hyperfocus Management
**Problem**: Difficulty regulating attention, alternating between distraction and hyperfocus

**Technical Implementation**:
```rust
pub struct AttentionManager {
    focus_state: FocusState,
    distraction_filters: Vec<DistractionFilter>,
    hyperfocus_detection: HyperfocusDetector,
}

impl AttentionManager {
    pub fn adaptive_interface(&mut self, user_input: &UserInput) -> InterfaceConfig {
        match self.detect_attention_state(user_input) {
            AttentionState::Distracted => {
                // Reduce visual noise, increase contrast
                InterfaceConfig {
                    color_scheme: HighContrast,
                    animation_level: Minimal,
                    notification_mode: Quiet,
                    layout_complexity: Simplified,
                }
            },
            AttentionState::Focused => {
                // Normal interface, preserve flow
                InterfaceConfig::default()
            },
            AttentionState::Hyperfocused => {
                // Gentle break reminders, hydration prompts
                self.schedule_gentle_interruption();
                InterfaceConfig::focused_with_breaks()
            }
        }
    }

    fn schedule_gentle_interruption(&self) {
        // Non-disruptive break reminders during hyperfocus
        tokio::spawn(async {
            tokio::time::sleep(Duration::from_secs(1800)).await; // 30 minutes
            self.gentle_break_suggestion().await;
        });
    }
}
```

## ADHD-Optimized UI/UX Design

### Visual Design Principles
```yaml
visual_accommodations:
  color_and_contrast:
    high_contrast_mode: Optional high contrast themes
    color_coding: Consistent color meanings across interface
    customizable_themes: User-defined color preferences

  information_hierarchy:
    progressive_disclosure: Show information in layers
    visual_chunking: Group related information clearly
    importance_highlighting: Emphasize critical information

  animation_and_motion:
    reduced_motion_option: Disable animations for sensory sensitivity
    purposeful_animation: Use motion to guide attention
    loading_indicators: Clear feedback on system state
```

### Terminal-Specific Accommodations
```typescript
class ADHDTerminalInterface {
    private statusBar: ADHDStatusBar;
    private commandPalette: SmartCommandPalette;
    private contextPanel: ContextPreservationPanel;

    public configureForADHD(userProfile: ADHDProfile): void {
        // Configure based on user's specific ADHD profile
        this.statusBar.setUpdateFrequency(userProfile.attentionSpan);
        this.commandPalette.setMaxSuggestions(userProfile.cognitiveLoad);
        this.contextPanel.setAutoSaveInterval(userProfile.memorySupport);
    }

    public adaptivePrompt(context: WorkContext): string {
        // Dynamic prompt that provides context without clutter
        const essentials = this.extractEssentials(context);
        return this.buildContextualPrompt(essentials);
    }

    private extractEssentials(context: WorkContext): Essentials {
        return {
            currentProject: context.projectName,
            activeFiles: context.openFiles.slice(0, 3), // Limit cognitive load
            gitStatus: context.gitStatus,
            nextDeadline: context.upcomingDeadlines[0]
        };
    }
}
```

## Intelligent Automation for ADHD

### Context-Aware Assistance
```python
class ADHDAssistanceEngine:
    def __init__(self):
        self.user_patterns = UserPatternAnalyzer()
        self.context_predictor = ContextPredictor()
        self.energy_tracker = EnergyLevelTracker()

    async def provide_proactive_support(self, user_state: UserState):
        """Provide support before user realizes they need it"""

        if self.energy_tracker.is_low_energy():
            # Simplify interface, provide more guidance
            await self.enable_simplified_mode()

        if self.context_predictor.predicts_context_switch():
            # Prepare context bridge
            await self.prepare_context_preservation()

        if self.user_patterns.detects_procrastination():
            # Gentle task initiation support
            await self.offer_task_breakdown()

    async def smart_task_chunking(self, task: ComplexTask) -> List[FocusTask]:
        """Break tasks into ADHD-friendly chunks"""
        chunks = []
        for subtask in task.decompose():
            if subtask.estimated_duration > 25:  # Pomodoro limit
                chunks.extend(await self.further_decompose(subtask))
            else:
                chunks.append(self.create_focus_task(subtask))
        return chunks
```

### Adaptive Workflow Management
```yaml
workflow_adaptations:
  focus_session_management:
    pomodoro_integration: Built-in 25-minute focus blocks
    break_reminders: Intelligent break suggestions
    momentum_preservation: Save state between breaks

  energy_aware_scheduling:
    peak_hours_detection: Learn user's optimal work times
    task_energy_matching: Match task complexity to energy levels
    rest_period_suggestions: Recommend breaks based on activity

  hyperfocus_protection:
    gentle_interruptions: Non-disruptive break reminders
    hydration_prompts: Health-focused notifications
    session_extension: Option to extend focus sessions safely
```

## Memory Augmentation Systems

### External Memory Architecture
```yaml
memory_scaffolding:
  automatic_capture:
    decision_logging: Record all significant decisions
    context_snapshots: Regular state preservation
    pattern_recognition: Learn user's work patterns

  intelligent_recall:
    semantic_search: Find information by meaning, not keywords
    temporal_queries: "What was I working on yesterday?"
    pattern_based_suggestions: "You usually do X after Y"

  cross_session_continuity:
    warm_startup: Restore previous session context
    project_memory: Remember project-specific preferences
    learning_retention: Preserve user adaptations
```

### Context Preservation Implementation
```rust
pub struct ContextPreservationSystem {
    auto_save_interval: Duration,
    context_snapshots: VecDeque<ContextSnapshot>,
    semantic_indexer: SemanticIndexer,
}

impl ContextPreservationSystem {
    pub async fn auto_preserve_context(&mut self) {
        loop {
            tokio::time::sleep(self.auto_save_interval).await;

            let current_context = self.capture_current_context().await;
            let context_snapshot = ContextSnapshot {
                timestamp: Utc::now(),
                working_directory: current_context.cwd,
                open_files: current_context.files,
                git_state: current_context.git,
                mental_model: current_context.ai_inferred_intent,
                energy_level: current_context.user_energy,
            };

            self.context_snapshots.push_back(context_snapshot.clone());

            // Index semantically for intelligent recall
            self.semantic_indexer.index_context(context_snapshot).await;
        }
    }

    pub async fn restore_context(&self, query: &str) -> Option<ContextSnapshot> {
        // Use semantic search to find relevant context
        self.semantic_indexer.search_context(query).await
    }
}
```

## Performance Optimization for ADHD

### Latency Requirements
```yaml
adhd_critical_latencies:
  attention_preservation: < 50ms  # Prevent attention loss
  context_switching: < 100ms      # Seamless transitions
  memory_recall: < 200ms          # External memory access
  visual_feedback: < 16ms         # 60fps for smooth experience

optimization_strategies:
  precomputation: Anticipate user needs and prepare responses
  caching: Aggressive caching of frequently accessed information
  progressive_loading: Show important information first
  background_processing: Perform heavy operations in background
```

### Resource Management
```yaml
resource_allocation:
  memory_priority: ADHD features get highest memory priority
  cpu_scheduling: Attention-critical tasks get priority
  network_optimization: Cache documentation and patterns locally
  battery_awareness: Adjust features based on power state
```

## User Customization and Adaptation

### ADHD Profile System
```typescript
interface ADHDProfile {
    // Attention characteristics
    attentionSpan: number;           // Minutes of sustained focus
    distractibilityLevel: 'low' | 'medium' | 'high';
    hyperfocusTendency: boolean;

    // Executive function support needs
    planningSupport: 'minimal' | 'moderate' | 'extensive';
    taskInitiationHelp: boolean;
    organizationAssistance: 'low' | 'medium' | 'high';

    // Sensory preferences
    colorSensitivity: boolean;
    motionSensitivity: boolean;
    soundSensitivity: boolean;

    // Time management
    timeBlindnessLevel: 'mild' | 'moderate' | 'severe';
    preferredFocusBlocks: number;    // Minutes
    breakFrequency: number;          // Minutes between breaks

    // Memory support
    workingMemorySupport: 'low' | 'medium' | 'high';
    contextPreservationNeeds: boolean;
    externalMemoryReliance: number;  // 0-10 scale
}

class ADHDAdaptationEngine {
    public adaptInterface(profile: ADHDProfile): InterfaceConfig {
        return {
            statusUpdateFrequency: this.calculateUpdateFrequency(profile),
            maxSimultaneousOptions: this.calculateCognitiveLoad(profile),
            autoSaveInterval: this.calculateSaveFrequency(profile),
            visualComplexity: this.calculateVisualComplexity(profile),
            automationLevel: this.calculateAutomationNeeds(profile)
        };
    }
}
```

### Learning and Adaptation
```python
class ADHDLearningSystem:
    def __init__(self):
        self.pattern_recognizer = PatternRecognizer()
        self.effectiveness_tracker = EffectivenessTracker()
        self.adaptation_engine = AdaptationEngine()

    async def continuous_learning(self, user_interactions: List[Interaction]):
        """Learn from user behavior to improve accommodations"""

        # Analyze interaction patterns
        patterns = self.pattern_recognizer.analyze(user_interactions)

        # Track effectiveness of accommodations
        effectiveness = self.effectiveness_tracker.measure(patterns)

        # Adapt accommodations based on effectiveness
        if effectiveness.attention_support < 0.8:
            await self.adaptation_engine.enhance_attention_support()

        if effectiveness.memory_support < 0.8:
            await self.adaptation_engine.enhance_memory_support()

        if effectiveness.executive_support < 0.8:
            await self.adaptation_engine.enhance_executive_support()
```

## Integration with Core Dopemux Systems

### MCP Server ADHD Enhancements
```yaml
mcp_adhd_integration:
  zen-mcp:
    consensus_simplification: Reduce decision paralysis
    model_routing: Route to ADHD-aware models

  context7:
    documentation_chunking: Break docs into digestible pieces
    pattern_highlighting: Emphasize relevant patterns

  serena:
    memory_augmentation: Enhanced session persistence
    context_restoration: Seamless work resumption

  task-master-ai:
    adhd_task_decomposition: ADHD-aware task breakdown
    energy_matching: Match tasks to energy levels
```

### Agent Coordination for ADHD
```python
class ADHDAgentCoordinator:
    async def coordinate_for_adhd(self, user_state: ADHDUserState):
        """Coordinate agents to minimize cognitive load"""

        if user_state.attention_level == 'low':
            # Reduce agent chatter, increase automation
            await self.enable_quiet_mode()

        if user_state.executive_function == 'impaired':
            # Provide more guidance, reduce choices
            await self.enable_guidance_mode()

        if user_state.hyperfocus_detected:
            # Protect flow state, minimize interruptions
            await self.enable_flow_protection()

    async def intelligent_task_routing(self, task: Task, user_state: ADHDUserState):
        """Route tasks based on ADHD state"""
        if user_state.energy_level == 'high':
            # Route complex tasks to user
            return await self.route_to_user_with_support(task)
        else:
            # Route to AI agents for automation
            return await self.route_to_agents(task)
```

## Validation and Effectiveness Measurement

### ADHD Accommodation Metrics
```yaml
effectiveness_metrics:
  cognitive_load_reduction:
    measurement: "30-50% reduction vs. traditional terminals"
    method: "Cognitive load assessment tools"

  task_completion_improvement:
    measurement: "20-40% improvement in completion rates"
    method: "Before/after user studies"

  attention_management:
    measurement: "25% longer focus sessions"
    method: "Attention tracking and user feedback"

  context_switching_efficiency:
    measurement: "89% reduction in context loss"
    method: "Context restoration success rates"
```

### Continuous Validation
```python
class ADHDEffectivenessValidator:
    async def validate_accommodations(self, user_data: ADHDUserData):
        """Continuously validate ADHD accommodation effectiveness"""

        metrics = {
            'focus_duration': self.measure_focus_duration(user_data),
            'task_completion': self.measure_completion_rates(user_data),
            'context_preservation': self.measure_context_success(user_data),
            'cognitive_load': self.measure_cognitive_load(user_data),
            'user_satisfaction': self.measure_satisfaction(user_data)
        }

        if any(metric < 0.8 for metric in metrics.values()):
            await self.trigger_accommodation_adjustment(metrics)
```

## Consequences

### Positive
- **Comprehensive ADHD Support**: Addresses all major ADHD challenges
- **Terminal-Optimized**: Purpose-built for command-line development
- **AI-Enhanced**: Intelligent adaptation and automation
- **Evidence-Based**: Grounded in academic research and proven patterns
- **Continuous Learning**: Improves through usage and feedback

### Negative
- **Implementation Complexity**: Sophisticated accommodation system
- **Resource Overhead**: Additional processing for ADHD features
- **Personalization Requirements**: Extensive user profiling needed
- **Validation Complexity**: Measuring accommodation effectiveness

### Risks and Mitigations
- **Over-Accommodation**: Risk of reducing user agency through excessive automation
  - *Mitigation*: User control over automation levels
- **Stigmatization**: Risk of marking users as "different"
  - *Mitigation*: Universal design principles, optional features
- **Privacy Concerns**: Extensive behavioral tracking
  - *Mitigation*: Local processing, user control over data

## Related Decisions
- **ADR-009**: Session persistence supports ADHD context preservation
- **ADR-010**: Custom agents implement ADHD-aware coordination
- **ADR-008**: Task management integration provides executive function support
- **ADR-005**: Letta Framework enables external memory augmentation

## References
- ADHD Features Research: `/research/findings/comprehensive-adhd-features.md`
- ADHD Support Patterns: `/research/findings/adhd-support.md`
- Context Management: `/research/findings/context-management-frameworks.md`
- Terminal Frameworks: `/research/findings/modern-terminal-frameworks.md`