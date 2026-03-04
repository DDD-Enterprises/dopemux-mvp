# Dopemux Configuration System

## Overview

Dopemux uses a multi-layered configuration system designed for ADHD developers, with sensible defaults, gentle validation, and flexible customization. The system supports multiple formats (YAML, TOML, JSON) and provides both global and project-specific settings.

## Configuration Hierarchy

Configuration is loaded in order of precedence (highest to lowest):

```
1. Command Line Arguments    (--debug, --config, etc.)
   ↓
2. Environment Variables     (DOPEMUX_*, CLAUDE_*, etc.)
   ↓
3. Project Configuration     (.dopemux/config.yaml)
   ↓
4. User Configuration        (~/.dopemux/config.yaml)
   ↓
5. Global ADHD Principles    (~/.claude/CLAUDE.md)
   ↓
6. Built-in Defaults         (Hardcoded sensible defaults)
```

---

## Configuration Files

### 1. Project Configuration (`.dopemux/config.yaml`)

**Location:** `{project_root}/.dopemux/config.yaml`
**Purpose:** Project-specific ADHD accommodations and settings

#### Example Configuration

```yaml
# .dopemux/config.yaml
# Project-specific ADHD accommodations

# Core ADHD Profile
adhd_profile:
  # Focus and attention settings
  focus_duration: 25              # Average focused work period (minutes)
  break_interval: 5               # Break between focus sessions (minutes)
  notification_style: gentle      # gentle/standard/minimal
  visual_complexity: minimal      # minimal/standard/comprehensive
  attention_adaptation: true      # Enable real-time adaptation
  decision_reduction: true        # Limit choices to reduce overwhelm

  # Context preservation
  auto_save_interval: 30          # Seconds between auto-saves
  context_restoration_timeout: 500 # Max milliseconds for restoration
  session_retention: 50           # Number of sessions to keep

  # Task management
  default_task_duration: 25       # Default task chunk size (minutes)
  max_task_complexity: 4          # Auto-decompose above this level
  progress_visualization: true    # Show visual progress bars
  break_reminders: true          # Gentle break notifications

# Project-specific settings
project:
  name: "My ADHD-Friendly Project"
  template: python                # python/javascript/rust/etc.
  description: "Web API with authentication"

# Claude Code integration
claude:
  # Model preferences based on attention state
  models:
    focused:
      - claude-opus-4-1-20250805
      - o3-pro-reasoning-2024-12-17
    normal:
      - claude-sonnet-4-20250514
      - gpt-4-turbo-2024-04-09
    scattered:
      - gemini-2.5-flash-001
      - gpt-4o-mini-2024-07-18
    hyperfocus:
      - claude-sonnet-4-20250514
      - grok-code-fast-1-2024-11-15

  # Response formatting preferences
  response_format:
    max_options: 3                # Limit choices for ADHD
    use_bullet_points: true       # Clear structure
    include_time_estimates: true   # Help with planning
    gentle_language: true         # Supportive tone

# MCP Server Configuration
mcp_servers:
  claude-context:
    enabled: true
    config:
      provider: milvus            # milvus/chroma/local
      search_type: hybrid         # hybrid/semantic/keyword
      embedding_model: text-embedding-3-large
      max_results: 10
      similarity_threshold: 0.7

  mas-sequential-thinking:
    enabled: true
    config:
      max_reasoning_depth: 5
      timeout: 30000             # 30 seconds
      path: "/Users/hue/code/mcp-server-mas-sequential-thinking"

  context7:
    enabled: true
    config:
      cache_duration: 3600       # 1 hour
      max_doc_size: 100000       # 100KB per doc

  morphllm-fast-apply:
    enabled: true
    config:
      preview_mode: true         # Show changes before applying
      backup_files: true         # Backup before modification

# Database settings
database:
  path: ".dopemux/context.db"
  backup_interval: 300           # 5 minutes
  vacuum_interval: 86400         # 24 hours
  max_size_mb: 100              # Max database size

# Performance settings
performance:
  max_concurrent_operations: 3
  cache_size_mb: 50
  gc_interval: 300               # Garbage collection interval

# Logging and debugging
logging:
  level: INFO                    # DEBUG/INFO/WARNING/ERROR
  file: ".dopemux/dopemux.log"
  max_size_mb: 10
  backup_count: 3
  adhd_metrics: true             # Log attention metrics

# Integration settings
integrations:
  git:
    auto_commit_context: false   # Auto-commit context saves
    commit_message_template: "Context save: {message}"

  vscode:
    sync_settings: true          # Sync with VSCode settings
    theme_adaptation: true       # Adapt theme to attention state

  tmux:
    session_management: true     # Manage tmux sessions
    auto_layout: true           # Restore window layouts
```

#### Configuration Validation

```yaml
# Schema validation rules (internal)
validation:
  adhd_profile:
    focus_duration:
      type: integer
      min: 5
      max: 90
      default: 25

    break_interval:
      type: integer
      min: 1
      max: 30
      default: 5

    notification_style:
      type: enum
      values: [gentle, standard, minimal]
      default: gentle

    visual_complexity:
      type: enum
      values: [minimal, standard, comprehensive]
      default: minimal
```

### 2. User Configuration (`~/.dopemux/config.yaml`)

**Location:** `~/.dopemux/config.yaml`
**Purpose:** User-wide defaults and personal ADHD accommodations

```yaml
# ~/.dopemux/config.yaml
# User-wide ADHD accommodations

# Personal ADHD profile (applies to all projects)
adhd_profile:
  # Personal attention patterns (learned over time)
  optimal_work_hours:
    - "09:00-11:00"              # Morning focus peak
    - "14:00-16:00"              # Afternoon focus window

  # Personal accommodation preferences
  notification_style: gentle     # Never overwhelming
  visual_complexity: minimal     # Keep it simple
  decision_reduction: true       # Always limit choices

  # Personal triggers and patterns
  distraction_triggers:
    - "social_media"
    - "email_notifications"
    - "slack_messages"

  # Effective break activities (personalized)
  preferred_breaks:
    - type: "nature"
      duration: 5
      description: "Look out window at trees"
    - type: "movement"
      duration: 10
      description: "Walk around the block"
    - type: "mindful"
      duration: 3
      description: "Deep breathing exercise"

# Default project settings
project_defaults:
  template: python              # Default project type
  auto_save_interval: 30        # Conservative default
  task_duration: 25            # 25-minute Pomodoro chunks

# Personal model preferences
claude:
  # Preferred models (personal taste)
  primary_models:
    - claude-opus-4-1-20250805   # Best for complex reasoning
    - claude-sonnet-4-20250514   # Good balance

  fallback_models:
    - gemini-2.5-flash-001      # Fast responses when scattered
    - gpt-4o-mini-2024-07-18    # Lightweight tasks

# Personal MCP server preferences
mcp_servers:
  # Preferred server locations
  mas-sequential-thinking:
    path: "/Users/hue/code/mcp-server-mas-sequential-thinking"

  # Personal settings
  claude-context:
    max_results: 5              # Don't overwhelm with results
    similarity_threshold: 0.8   # Higher threshold for relevance

# UI preferences
interface:
  color_scheme: "adhd_friendly" # Calm colors, high contrast
  animation_speed: "slow"       # No jarring transitions
  progress_bars: true          # Visual progress important for ADHD
  sounds: false                # No audio notifications

# Privacy and data
privacy:
  analytics_enabled: false     # No usage tracking
  crash_reporting: true        # Help improve ADHD features
  cloud_sync: false           # Keep everything local
```

### 3. Global ADHD Principles (`~/.claude/CLAUDE.md`)

**Location:** `~/.claude/CLAUDE.md`
**Purpose:** ADHD-first principles applied to all Claude interactions

```markdown
# Dopemux Global Configuration

This file provides global Claude Code configuration optimized for ADHD developers.

## Core Instructions

You are Claude Code working with Dopemux, an ADHD-optimized development platform.
Your primary goal is to provide accommodating, supportive development assistance
that reduces cognitive load and enhances productivity for neurodivergent developers.

### ADHD-First Principles

- **Context Preservation**: Always maintain awareness of where the user left off
- **Gentle Guidance**: Use encouraging, non-judgmental language with clear next steps
- **Decision Reduction**: Present maximum 3 options to reduce cognitive overwhelm
- **Task Chunking**: Break complex work into 25-minute focused segments
- **Progressive Disclosure**: Show essential information first, details on request

### Response Adaptation

**When attention is focused:**
- Provide comprehensive technical details
- Use full explanations with context
- Include implementation options

**When attention is scattered:**
- Use bullet points and concise explanations
- Highlight critical information first
- One clear action item per response

**During context switches:**
- Provide orientation: "You were working on X, now moving to Y"
- Bridge between contexts with brief summaries
- Maintain awareness of previous task state

### Memory Support

- Log important decisions with rationale
- Track progress with visual indicators: `[████░░░░] 4/8 complete ✅`
- Provide time anchors: "Started X at 2:30pm (45 min ago)"
- Celebrate completions: "✅ Awesome! Task complete!"

### Executive Function Support

- Break goals into specific, actionable steps
- Identify dependencies and prerequisites
- Suggest optimal task ordering
- Provide clear first steps to reduce activation energy

### Communication Style

- Use positive, encouraging tone
- Lead with most important information
- Employ visual elements: ✅ ❌ ⚠️ 💡 🎯
- Structure with clear headers and bullet points

## Quality Standards

- Always verify Claude Code is available before attempting launch
- Maintain session state across interruptions
- Provide clear error messages with recovery suggestions
- Log important decisions for future reference
- Use absolute paths for all file operations

---

**Focus**: ADHD accommodation and development productivity
**Style**: Supportive, clear, action-oriented
**Goal**: Reduce cognitive load while maximizing development effectiveness
```

### 4. Claude Project Configuration (`.claude/claude.md`)

**Location:** `{project_root}/.claude/claude.md`
**Purpose:** Project-specific Claude Code instructions with ADHD accommodations

```markdown
# Python Project - Dopemux Configuration

Project-specific Claude Code instructions for python development with ADHD accommodations.

## Project Context

You are working on a **python project** with Dopemux ADHD optimizations enabled.

### ADHD Accommodations Active

- **Focus Duration**: 25 minutes average
- **Break Intervals**: 5 minutes
- **Notification Style**: gentle
- **Visual Complexity**: minimal
- **Attention Adaptation**: Enabled

### Development Principles

- **Context Preservation**: Auto-save every 30 seconds
- **Gentle Guidance**: Use encouraging, supportive language
- **Progressive Disclosure**: Show essential info first, details on request
- **Task Chunking**: Break work into 25-minute segments

### Python Development Guidelines

- Use type hints for better ADHD developer experience
- Follow PEP 8 with Black formatting
- Prefer explicit over implicit (Zen of Python)
- Use dataclasses and Pydantic for clear data structures
- Write docstrings for all public functions

### Testing Strategy

- Use pytest for all testing
- Write tests first for complex logic
- Use descriptive test names
- Mock external dependencies

## ADHD-Optimized Response Patterns

### When User is Focused
- Provide comprehensive technical details
- Include multiple implementation approaches
- Show complete code examples with explanations

### When User is Scattered
- Use bullet points and concise explanations
- Highlight only critical information
- Provide ONE clear next action
- Keep responses under 500 words

### During Context Switches
- Provide brief orientation: "You were working on X, now Y"
- Bridge between tasks with summaries
- Maintain awareness of previous context

## Integration with Dopemux

### Available Commands
- `dopemux save` - Manual context preservation
- `dopemux restore` - Restore previous session
- `dopemux status` - Check attention metrics
- `dopemux task` - ADHD-friendly task management

### Context Sharing
- Session state automatically preserved
- Mental model tracked across interruptions
- Decision history maintained
- Progress visualization available

---

**Focus**: python development with ADHD accommodations
**Goal**: Maintain productivity while respecting neurodivergent needs
**Style**: Supportive, clear, action-oriented
```

---

## Configuration Templates

### Template System

Dopemux includes templates for common project types, each with ADHD-optimized defaults:

#### Python Template
```yaml
# Generated for Python projects
adhd_profile:
  focus_duration: 25
  break_interval: 5
  task_duration: 25

project:
  template: python

claude:
  models:
    focused: [claude-opus-4-1-20250805]
    scattered: [gemini-2.5-flash-001]

mcp_servers:
  claude-context:
    enabled: true
    config:
      file_types: [".py", ".pyi", ".md"]
```

#### JavaScript/TypeScript Template
```yaml
# Generated for JavaScript/TypeScript projects
adhd_profile:
  focus_duration: 20            # Shorter due to rapid context switches
  break_interval: 5

project:
  template: javascript

claude:
  models:
    focused: [claude-sonnet-4-20250514]
    scattered: [gpt-4o-mini-2024-07-18]

mcp_servers:
  claude-context:
    enabled: true
    config:
      file_types: [".js", ".ts", ".jsx", ".tsx", ".md"]
```

#### Rust Template
```yaml
# Generated for Rust projects
adhd_profile:
  focus_duration: 30            # Longer due to compilation cycles
  break_interval: 5

project:
  template: rust

claude:
  models:
    focused: [claude-opus-4-1-20250805]  # Best for complex type reasoning

mcp_servers:
  claude-context:
    enabled: true
    config:
      file_types: [".rs", ".toml", ".md"]
```

### Custom Templates

Create custom templates in `~/.dopemux/templates/`:

```yaml
# ~/.dopemux/templates/web-api.yaml
# Custom template for web API projects

adhd_profile:
  focus_duration: 25
  task_duration: 20             # Shorter tasks for API work

project:
  template: custom
  description: "RESTful API with authentication"

claude:
  response_format:
    include_curl_examples: true  # Always show API usage
    include_test_cases: true     # Essential for API development

mcp_servers:
  context7:
    enabled: true
    config:
      focus_docs: ["fastapi", "flask", "express"]  # API frameworks
```

---

## Environment Variables

### Configuration Override

| Variable | Description | Example |
|----------|-------------|---------|
| `DOPEMUX_CONFIG` | Override config file location | `export DOPEMUX_CONFIG=/custom/config.yaml` |
| `DOPEMUX_DEBUG` | Enable debug mode | `export DOPEMUX_DEBUG=1` |
| `DOPEMUX_PROFILE` | Load specific ADHD profile | `export DOPEMUX_PROFILE=hyperfocus` |

### ADHD Profile Override

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DOPEMUX_FOCUS_DURATION` | Focus session length (minutes) | `25` | `export DOPEMUX_FOCUS_DURATION=30` |
| `DOPEMUX_BREAK_INTERVAL` | Break duration (minutes) | `5` | `export DOPEMUX_BREAK_INTERVAL=10` |
| `DOPEMUX_AUTO_SAVE_INTERVAL` | Auto-save frequency (seconds) | `30` | `export DOPEMUX_AUTO_SAVE_INTERVAL=15` |
| `DOPEMUX_NOTIFICATION_STYLE` | Notification approach | `gentle` | `export DOPEMUX_NOTIFICATION_STYLE=minimal` |
| `DOPEMUX_VISUAL_COMPLEXITY` | UI complexity level | `minimal` | `export DOPEMUX_VISUAL_COMPLEXITY=standard` |

### Claude Integration

| Variable | Description | Example |
|----------|-------------|---------|
| `DOPEMUX_CLAUDE_PATH` | Custom Claude Code path | `export DOPEMUX_CLAUDE_PATH=/usr/local/bin/claude-code` |
| `DOPEMUX_CLAUDE_CONFIG` | Claude configuration directory | `export DOPEMUX_CLAUDE_CONFIG=/custom/.claude` |

### MCP Server Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `DOPEMUX_MCP_CLAUDE_CONTEXT` | claude-context server path | `export DOPEMUX_MCP_CLAUDE_CONTEXT=/path/to/server` |
| `DOPEMUX_MCP_SEQUENTIAL_THINKING` | mas-sequential-thinking path | `export DOPEMUX_MCP_SEQUENTIAL_THINKING=/path/to/server` |
| `DOPEMUX_MCP_TIMEOUT` | MCP operation timeout (ms) | `export DOPEMUX_MCP_TIMEOUT=30000` |

---

## Configuration Management

### Configuration Validation

The ConfigManager validates all settings on load:

```python
class ConfigManager:
    def validate_config(self, config: Dict) -> Tuple[bool, List[str]]:
        """Validate ADHD-focused configuration"""

        errors = []

        # Validate ADHD profile
        adhd = config.get('adhd_profile', {})

        if not (5 <= adhd.get('focus_duration', 25) <= 90):
            errors.append("focus_duration must be between 5-90 minutes")

        if adhd.get('notification_style') not in ['gentle', 'standard', 'minimal']:
            errors.append("notification_style must be gentle/standard/minimal")

        # Validate performance settings
        if adhd.get('auto_save_interval', 30) < 10:
            errors.append("auto_save_interval too low, minimum 10 seconds for performance")

        return len(errors) == 0, errors
```

### Dynamic Configuration Updates

Some settings can be updated during runtime:

```python
# Update ADHD profile during session
config_manager.update_adhd_profile({
    'notification_style': 'minimal',  # User feeling overwhelmed
    'visual_complexity': 'minimal',   # Reduce cognitive load
    'focus_duration': 15              # Shorter focus periods
})

# Update model preferences based on attention state
config_manager.update_claude_models({
    'current_state': 'scattered',
    'preferred_model': 'gemini-2.5-flash-001'  # Faster responses
})
```

### Configuration Migration

When upgrading Dopemux versions:

```python
class ConfigMigrator:
    """Handle ADHD-sensitive configuration migration"""

    def migrate_v1_to_v2(self, old_config: Dict) -> Dict:
        """Migrate with minimal user disruption"""

        new_config = old_config.copy()

        # Preserve ADHD accommodations
        if 'focus_time' in old_config:
            new_config['adhd_profile'] = {
                'focus_duration': old_config['focus_time'],
                'break_interval': old_config.get('break_time', 5)
            }

        return new_config
```

---

## ADHD-Specific Configuration Patterns

### Attention State Profiles

Different configurations for different cognitive states:

```yaml
# Multiple profiles for different ADHD states
adhd_profiles:
  focused:
    visual_complexity: comprehensive
    notification_style: standard
    decision_options: 3

  scattered:
    visual_complexity: minimal
    notification_style: gentle
    decision_options: 1
    auto_save_interval: 15      # Save more frequently

  hyperfocus:
    visual_complexity: minimal
    notification_style: minimal
    break_reminders: true       # Important to prevent burnout
    max_session_duration: 90    # Force breaks

  overwhelmed:
    visual_complexity: minimal
    notification_style: gentle
    decision_options: 1
    task_duration: 10           # Tiny chunks
    encouragement_frequency: high
```

### Personalization Learning

Configuration that adapts based on usage patterns:

```yaml
# Learned personal patterns (auto-generated)
personal_patterns:
  optimal_focus_times:
    - "09:00-11:00"  # Monday-Friday morning peak
    - "14:00-16:00"  # Afternoon focus window

  effective_break_types:
    - type: "nature"
      effectiveness_score: 0.9
      duration: 5
    - type: "movement"
      effectiveness_score: 0.8
      duration: 10

  distraction_triggers:
    - trigger: "slack_notification"
      impact_score: 0.7
      mitigation: "disable_during_focus"
    - trigger: "email_alert"
      impact_score: 0.5
      mitigation: "batch_process"

  productive_task_patterns:
    - pattern: "code_first_test_later"
      success_rate: 0.8
    - pattern: "small_increments"
      success_rate: 0.9
```

### Team ADHD Configuration

For teams with multiple neurodivergent developers:

```yaml
# Team-wide ADHD accommodations
team_adhd:
  shared_profiles:
    - name: "morning_focused"
      description: "For team members who focus best in morning"
      schedule: "09:00-12:00"

    - name: "afternoon_focused"
      description: "For team members who focus best in afternoon"
      schedule: "13:00-17:00"

  collaboration:
    pair_programming:
      session_duration: 45        # Longer for pairs
      role_switching_interval: 15 # Switch driver/navigator

    code_reviews:
      max_files_per_review: 3     # Don't overwhelm reviewers
      review_time_limit: 30       # Force focused reviews

    meetings:
      max_duration: 25            # ADHD-friendly meeting length
      agenda_required: true       # Clear structure essential
      recording_available: true   # For context restoration
```

---

## Configuration Debugging

### Debug Configuration Loading

```bash
# Debug configuration loading process
dopemux --debug config show

# Output shows configuration hierarchy:
```

```
🔧 Configuration Loading Debug

📁 Configuration Sources (in precedence order):
1. ✅ Command line: --debug=true
2. ❌ Environment variables: None found
3. ✅ Project config: /project/.dopemux/config.yaml
   • adhd_profile.focus_duration: 25
   • claude.models.focused: [claude-opus-4-1-20250805]
4. ✅ User config: ~/.dopemux/config.yaml
   • adhd_profile.notification_style: gentle
5. ✅ Global principles: ~/.claude/CLAUDE.md
   • ADHD-first principles active
6. ✅ Built-in defaults: Applied

🎯 Final Configuration:
{
  "adhd_profile": {
    "focus_duration": 25,        // from project config
    "notification_style": "gentle", // from user config
    "visual_complexity": "minimal"  // from built-in defaults
  }
}

⚡ Configuration loaded in 23ms
✅ All validations passed
```

### Validate Configuration

```bash
# Validate current configuration
dopemux config validate

# Output:
```

```
✅ Configuration Validation Results

🧠 ADHD Profile:
✅ focus_duration: 25 (valid range: 5-90)
✅ break_interval: 5 (valid range: 1-30)
✅ notification_style: gentle (valid options: gentle/standard/minimal)
✅ auto_save_interval: 30 (minimum: 10 for performance)

🤖 Claude Integration:
✅ models configured for all attention states
✅ MCP servers: 4 enabled, all accessible
✅ Response format: ADHD-optimized

💾 Database:
✅ SQLite accessible at .dopemux/context.db
✅ Disk space: 2.3GB available
✅ Performance: <500ms restoration target achievable

🔧 Performance:
✅ Memory usage: Normal (45MB allocated)
✅ CPU impact: Minimal (<2% average)

📊 Overall Score: 100% - Optimal ADHD configuration
```

---

## Configuration Best Practices

### For Individual ADHD Developers

#### Start Conservative
```yaml
# Begin with gentle settings, increase as comfortable
adhd_profile:
  focus_duration: 20          # Start shorter
  break_interval: 10          # Longer breaks initially
  notification_style: gentle  # Always gentle
  visual_complexity: minimal  # Reduce overwhelm
```

#### Personalize Over Time
```yaml
# Track what works for you
personal_notes:
  effective_focus_times:
    - "After morning coffee: 09:30-11:00"
    - "Post-lunch focus: 14:00-15:30"

  break_preferences:
    - "Walking outside beats indoor stretching"
    - "3 deep breaths > 5 minute meditation"

  distraction_patterns:
    - "Phone notifications kill focus"
    - "Background music helps during coding"
```

#### Adapt to Daily Variation
```yaml
# Different configs for different days/states
profiles:
  high_energy:
    focus_duration: 30
    break_interval: 5

  low_energy:
    focus_duration: 15
    break_interval: 10
    task_size: "micro"        # Very small tasks

  overwhelmed:
    notification_style: gentle
    visual_complexity: minimal
    decision_options: 1       # One choice only
```

### For Teams with ADHD Developers

#### Accommodate Different Patterns
```yaml
team_settings:
  flexible_schedules: true    # Allow focus time preferences
  meeting_guidelines:
    max_duration: 25          # ADHD-friendly length
    agenda_required: true     # Structure essential
    breaks_every: 90          # For longer sessions

  collaboration:
    async_preferred: true     # Reduce context switching
    documentation: "visual"   # Diagrams over text walls
```

#### Shared Understanding
```yaml
team_education:
  adhd_awareness: true        # Team understands ADHD needs
  accommodation_respect: true # No judgment for different styles
  context_sharing: enabled    # Share session context safely
```

---

## Configuration Schema Reference

### Complete Schema

```yaml
# Complete Dopemux configuration schema
type: object
properties:
  adhd_profile:
    type: object
    properties:
      focus_duration:
        type: integer
        minimum: 5
        maximum: 90
        default: 25
        description: "Average focused work period in minutes"

      break_interval:
        type: integer
        minimum: 1
        maximum: 30
        default: 5
        description: "Break between focus sessions in minutes"

      notification_style:
        type: string
        enum: [gentle, standard, minimal]
        default: gentle
        description: "Notification approach for ADHD sensitivity"

      visual_complexity:
        type: string
        enum: [minimal, standard, comprehensive]
        default: minimal
        description: "UI complexity level"

      attention_adaptation:
        type: boolean
        default: true
        description: "Enable real-time attention state adaptation"

      auto_save_interval:
        type: integer
        minimum: 10
        maximum: 300
        default: 30
        description: "Seconds between automatic context saves"

      session_retention:
        type: integer
        minimum: 10
        maximum: 200
        default: 50
        description: "Number of sessions to retain"

  claude:
    type: object
    properties:
      models:
        type: object
        properties:
          focused:
            type: array
            items:
              type: string
            description: "Models to use when user is focused"
          scattered:
            type: array
            items:
              type: string
            description: "Models to use when user is scattered"

  mcp_servers:
    type: object
    additionalProperties:
      type: object
      properties:
        enabled:
          type: boolean
          default: true
        config:
          type: object
          description: "Server-specific configuration"

required: []  # All settings have sensible defaults
```

---

**🔧 Configuration Summary:**

Dopemux provides a flexible, ADHD-optimized configuration system with:
- ✅ **Multi-layered hierarchy** - Command line → Environment → Project → User → Global → Defaults
- ✅ **ADHD-first design** - Gentle validation, sensible defaults, minimal cognitive load
- ✅ **Multiple formats** - YAML, TOML, JSON support with auto-detection
- ✅ **Template system** - Pre-configured settings for common project types
- ✅ **Runtime adaptation** - Settings adjust based on attention state
- ✅ **Personal learning** - Configuration evolves with usage patterns
- ✅ **Team support** - Shared accommodations for neurodivergent teams

**Built for ADHD developers who need flexible, supportive configuration without overwhelm. 🧠💚**