# Complete Implementation Plan: zen-mcp + Role-Based MCP Orchestration with Automated Session Management

## Overview
Implement a sophisticated MCP orchestration system for Dopemux that:
- Reduces token usage from 100k+ to <10k through role-based tool loading
- Provides automated session lifecycle management
- Enables workflow-driven development with natural role transitions
- Includes comprehensive telemetry for optimization

## Phase 1: zen-mcp Integration (2-3 hours)

### 1.1 Install Script Updates
**File: `scripts/install-mcp-servers.sh`**
- Add zen-mcp installation with proper error handling
- Configure environment variable checks for multi-model support

### 1.2 Configuration Setup
**File: `src/dopemux/config/manager.py`**
- Add zen-mcp to default MCP servers with disabled tools list:
  - Disabled: analyze, refactor, testgen, secaudit, docgen, tracer
  - Enabled: chat, debug, precommit, planner, codereview, consensus, challenge
- Set conservative thinking mode defaults (low = 4k tokens)

### 1.3 Environment Template
**File: `.env.example`**
```bash
# Multi-model API keys for zen-mcp
GEMINI_API_KEY=your-key
OPENAI_API_KEY=your-key
OPENROUTER_API_KEY=your-key
XAI_API_KEY=your-key

# zen-mcp configuration
ZEN_DISABLED_TOOLS=analyze,refactor,testgen,secaudit,docgen,tracer
ZEN_DEFAULT_THINKING_MODE=low
```

## Phase 2: Role-Based Orchestration Core (4-5 hours)

### 2.1 Role Manager
**File: `src/dopemux/mcp/roles.py`**

#### Core Roles Definition:
```python
ROLES = {
    'researcher': {
        'servers': {
            'mas-sequential-thinking': ['sequentialthinking'],
            'exa': ['exa_search'],
            'web-search': ['search'],
        },
        'context_window': 'large',  # 100k+
        'token_budget': 15000,
        'primary_focus': 'information gathering'
    },

    'implementer': {
        'servers': {
            'context7': ['get_docs', 'search'],
            'claude-context': ['search_code'],
            'morphllm-fast-apply': ['edit_file'],
            'zen': ['precommit'],
        },
        'context_window': 'medium',  # 50k
        'token_budget': 10000,
        'primary_focus': 'code generation'
    },

    'reviewer': {
        'servers': {
            'context7': ['get_docs'],
            'zen': ['codereview', 'precommit'],
            'claude-context': ['search_code'],
        },
        'context_window': 'medium',
        'token_budget': 12000,
        'primary_focus': 'quality assurance'
    },

    'architect': {
        'servers': {
            'mas-sequential-thinking': ['sequentialthinking'],
            'zen': ['consensus', 'challenge'],
        },
        'context_window': 'large',
        'token_budget': 15000,
        'primary_focus': 'system design'
    },

    'product_manager': {
        'servers': {
            'zen': ['planner'],
            'task-master-ai': ['parse_prd', 'create_tasks'],
            'leantime': ['create_story', 'update_sprint'],
        },
        'context_window': 'small',  # 25k
        'token_budget': 8000,
        'primary_focus': 'planning'
    },

    'scrum_master': {
        'servers': {
            'leantime': ['sprint_tools', 'burndown'],
            'task-master-ai': ['status', 'blockers'],
        },
        'context_window': 'small',
        'token_budget': 6000,
        'primary_focus': 'process management'
    },

    'debugger': {
        'servers': {
            'zen': ['debug'],
            'claude-context': ['search_code'],
            'mas-sequential-thinking': ['sequentialthinking'],
        },
        'context_window': 'large',
        'token_budget': 15000,
        'primary_focus': 'problem solving'
    },

    'refactorer': {
        'servers': {
            'zen': ['refactor', 'analyze'],
            'claude-context': ['search_code', 'index_codebase'],
            'morphllm-fast-apply': ['edit_file'],
        },
        'context_window': 'medium',
        'token_budget': 12000,
        'primary_focus': 'code improvement'
    },

    'documenter': {
        'servers': {
            'morphllm-fast-apply': ['edit_file'],
            'claude-context': ['search_code'],
        },
        'context_window': 'small',
        'token_budget': 6000,
        'primary_focus': 'documentation'
    },

    'session_orchestrator': {
        'servers': {
            'claude-context': ['index_codebase', 'clear_index', 'get_indexing_status'],
            'task-master-ai': ['get_tasks', 'update_status', 'parse_prd'],
            'conport': ['store_decision', 'get_context', 'list_decisions'],
            'leantime': ['get_current_sprint', 'update_story'],
        },
        'context_window': 'small',
        'token_budget': 5000,
        'primary_focus': 'session management',
        'automation': {
            'triggers': ['session_start', 'session_end', 'context_switch', 'milestone'],
            'run_mode': 'background'
        }
    },

    'knowledge_curator': {
        'servers': {
            'conport': ['store_decision', 'get_decisions', 'update_knowledge_graph'],
            'claude-context': ['get_indexing_status'],
        },
        'context_window': 'small',
        'token_budget': 4000,
        'primary_focus': 'knowledge management',
        'automation': {
            'triggers': ['decision_made', 'milestone_reached', 'session_end'],
            'run_mode': 'background'
        }
    }
}
```

### 2.2 Tool Manager
**File: `src/dopemux/mcp/tool_manager.py`**
- Fine-grained tool loading/unloading
- Token budget calculation per role
- Ad-hoc composition support
- Tool cost estimation

### 2.3 Token Budget Manager
**File: `src/dopemux/mcp/token_manager.py`**
```python
# Token allocation strategy:
MAX_TOKENS = 10000
CORE_RESERVE = 2000  # Always available
ROLE_BUDGET = 8000   # Dynamically allocated

# zen-mcp tool token costs (estimated):
ZEN_TOOL_COSTS = {
    'chat': 2000,
    'thinkdeep': 16000,  # Disabled by default
    'consensus': 10000,
    'debug': 8000,
    'codereview': 15000,
    'planner': 5000,
    'precommit': 3000,
    'analyze': 20000,    # Disabled by default
    'refactor': 10000,   # Disabled by default
    'challenge': 3000,
}
```

## Phase 3: Session Orchestration & Automation (4-5 hours)

### 3.1 Session Manager
**File: `src/dopemux/mcp/session_manager.py`**

Key responsibilities:
- Automated session lifecycle (start/milestone/end)
- Codebase indexing management
- Task synchronization with task-master-ai and leantime
- Context preservation via conport
- Knowledge extraction and storage

```python
class SessionManager:
    async def on_session_start(self, context):
        # 1. Load current tasks from task-master/leantime
        # 2. Check if codebase needs indexing
        # 3. Restore previous context from conport
        # 4. Set up initial role based on task type

    async def on_milestone(self, milestone_type, data):
        # Handle: task_complete, context_switch, focus_break

    async def on_session_end(self):
        # 1. Final task status update
        # 2. Store session knowledge
        # 3. Update sprint/project status
```

### 3.2 Hook System
**File: `src/dopemux/mcp/hooks.py`**

```python
HOOK_POINTS = {
    'session_start': {
        'roles': ['session_orchestrator'],
        'actions': ['index', 'load_tasks', 'restore_context']
    },
    'file_save': {
        'condition': lambda ctx: ctx.files_modified > 10,
        'roles': ['session_orchestrator'],
        'actions': ['incremental_index']
    },
    'focus_break': {  # ADHD support - every 25 min
        'roles': ['session_orchestrator'],
        'actions': ['checkpoint_progress', 'update_task_status']
    },
    'task_complete': {
        'roles': ['knowledge_curator', 'session_orchestrator'],
        'actions': ['store_decisions', 'update_task', 'load_next_task']
    },
    'role_transition': {
        'roles': ['session_orchestrator'],
        'actions': ['save_role_context', 'load_new_role_context']
    },
    'session_end': {
        'roles': ['session_orchestrator', 'knowledge_curator'],
        'actions': ['final_sync', 'knowledge_export', 'clear_index']
    }
}
```

### 3.3 Workflow Engine
**File: `src/dopemux/mcp/workflows.py`**

```python
WORKFLOWS = {
    'feature_development': [
        ('researcher', 'gather requirements'),
        ('architect', 'design solution'),
        ('implementer', 'build with TDD'),
        ('reviewer', 'validate implementation'),
    ],

    'bug_fix': [
        ('debugger', 'identify root cause'),
        ('implementer', 'fix issue'),
        ('reviewer', 'verify fix'),
    ],

    'planning_session': [
        ('product_manager', 'create roadmap'),
        ('architect', 'technical feasibility'),
        ('scrum_master', 'sprint planning'),
    ],

    'refactoring': [
        ('reviewer', 'identify issues'),
        ('refactorer', 'improve code'),
        ('reviewer', 'validate changes'),
    ]
}
```

## Phase 4: Configuration & CLI (2-3 hours)

### 4.1 YAML Configuration Files

**File: `config/roles.yaml`**
```yaml
roles:
  researcher:
    description: "Information gathering and analysis"
    servers:
      mas-sequential-thinking:
        tools: [sequentialthinking]
        priority: high
      exa:
        tools: [exa_search]
        priority: medium
    context_window: large
    token_budget: 15000

  implementer:
    description: "Code generation and implementation"
    servers:
      context7:
        tools: [get_docs, search]
        priority: high
      claude-context:
        tools: [search_code]
        priority: high
      morphllm-fast-apply:
        tools: [edit_file]
        priority: medium
      zen:
        tools: [precommit]
        priority: low
    context_window: medium
    token_budget: 10000
```

**File: `config/workflows.yaml`**
```yaml
workflows:
  feature_development:
    pre_hooks:
      - role: session_orchestrator
        actions: [index_codebase, load_tasks, restore_context]

    steps:
      - role: researcher
        duration: 5-10min
      - role: architect
        duration: 10-15min

      - milestone: design_complete
        hooks:
          - role: knowledge_curator
            actions: [store_design_decisions]

      - role: implementer
        duration: 25-45min

      - milestone: implementation_checkpoint  # Every 25 min for ADHD
        hooks:
          - role: session_orchestrator
            actions: [save_progress, update_task_status]

      - role: reviewer
        duration: 10-15min

    post_hooks:
      - role: session_orchestrator
        actions: [update_all_tasks, store_session_knowledge, clear_temp_index]
```

**File: `config/orchestration.yaml`**
```yaml
orchestration:
  mode: conservative  # Start conservative

  core_servers:
    # Always loaded (<2k tokens)
    - context7: {tools: [search, get_docs]}

  task_detection:
    patterns:
      implementation: 'implement|create|build|add feature'
      debugging: 'debug|fix|error|not working'
      review: 'review|check|validate|precommit'
      planning: 'plan|design|architecture|roadmap'

  zen_config:
    # Initially disabled tools
    disabled_tools:
      - analyze      # 20k tokens
      - refactor     # 10k tokens (enable for refactorer role)
      - testgen      # Variable
      - secaudit     # 15k tokens
      - docgen       # 5k tokens
      - tracer       # Variable
      - thinkdeep    # 16k tokens (manual enable only)

    # Conservative defaults
    default_thinking_mode: low  # 4k tokens vs 16k

  token_budgets:
    strict_mode: true
    max_total: 10000
    warning_threshold: 8000
    core_reserve: 2000
```

### 4.2 CLI Commands
**File: `src/dopemux/cli.py`** (additions)

```bash
# Role management
dopemux role <name>              # Switch to role
dopemux role compose <tools>     # Ad-hoc composition
dopemux role list                # Show available roles
dopemux role current             # Show current role and tools

# Workflow commands
dopemux workflow start <name>    # Start workflow
dopemux workflow next            # Next step
dopemux workflow status          # Current position
dopemux workflow list            # Available workflows

# MCP management
dopemux mcp status               # Show active servers/tools
dopemux mcp budget               # Token budget usage
dopemux mcp servers              # List all servers

# Telemetry
dopemux telemetry report         # Usage patterns
dopemux telemetry optimize       # Suggestions
dopemux telemetry export         # Export data
```

## Phase 5: Telemetry & Monitoring (2-3 hours)

### 5.1 Telemetry Collector
**File: `src/dopemux/mcp/telemetry.py`**

```python
class TelemetryCollector:
    def __init__(self):
        self.db = sqlite3.connect('~/.dopemux/telemetry.db')
        self._init_tables()

    def track_tool_load(self, role, server, tool, tokens):
        # Record when tools are loaded

    def track_tool_use(self, role, server, tool, tokens_used, duration):
        # Record actual tool usage

    def track_role_transition(self, from_role, to_role, context_preserved):
        # Track workflow transitions

    def analyze_patterns(self) -> Dict:
        return {
            'most_used_tools': self._get_most_used(),
            'token_efficiency': self._calculate_efficiency(),
            'role_transitions': self._analyze_transitions(),
            'unused_tools': self._find_unused(),
            'optimization_suggestions': self._suggest_optimizations()
        }
```

### 5.2 Analytics Dashboard
**File: `src/dopemux/mcp/analytics.py`**
- Usage reports
- Optimization suggestions
- Unused tool detection
- Token efficiency metrics
- Role effectiveness analysis

## Phase 6: Docker Infrastructure (2-3 hours)

### 6.1 MetaMCP Docker Setup
**File: `docker/metamcp/docker-compose.yml`**

```yaml
version: '3.8'
services:
  metamcp-gateway:
    image: metatool/metamcp:latest
    ports:
      - "8080:8080"
    environment:
      LAZY_LOAD_ENABLED: "true"
      MAX_INITIAL_TOKENS: "5000"
      COMPRESSION_LEVEL: "aggressive"
    volumes:
      - ./mcp-configs:/configs
      - ./cache:/cache
    deploy:
      resources:
        limits:
          memory: 2G

  redis-cache:
    image: redis:7-alpine
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data

volumes:
  redis-data:
    driver: local
```

## Phase 7: Documentation & Testing (3-4 hours)

### 7.1 Documentation

**File: `docs/MCP_ORCHESTRATION.md`**
- Complete orchestration guide
- Architecture overview
- Configuration examples

**File: `docs/ROLE_REFERENCE.md`**
- All roles with tools
- Token budgets
- Use cases and examples

**File: `docs/ZEN_MCP_GUIDE.md`**
- zen-mcp tool reference
- Model selection guide
- Best practices

**File: `docs/WORKFLOW_GUIDE.md`**
- Pre-defined workflows
- Creating custom workflows
- Hook system usage

### 7.2 Testing
**Directory: `tests/mcp/`**
- Unit tests for all components
- Integration tests for workflows
- Performance tests for token limits
- Telemetry validation tests

## Implementation Order & Timeline

### Day 1 Morning (4 hours)
1. ✅ Install zen-mcp (30 min)
2. ✅ Update configuration manager (30 min)
3. ✅ Create role definitions (1 hour)
4. ✅ Implement tool manager (2 hours)

### Day 1 Afternoon (4 hours)
1. ✅ Build session manager (1.5 hours)
2. ✅ Implement hook system (1 hour)
3. ✅ Create workflow engine (1 hour)
4. ✅ Initial testing (30 min)

### Day 2 Morning (4 hours)
1. ✅ Set up telemetry (1.5 hours)
2. ✅ Docker infrastructure (1 hour)
3. ✅ CLI commands (1 hour)
4. ✅ Configuration files (30 min)

### Day 2 Afternoon (3 hours)
1. ✅ Documentation (1.5 hours)
2. ✅ Integration tests (1 hour)
3. ✅ Final validation (30 min)

## Files to Create/Modify

### New Files (25 files):

```
src/dopemux/mcp/
├── __init__.py
├── roles.py              # Role definitions
├── tool_manager.py       # Tool loading/unloading
├── token_manager.py      # Token budget management
├── session_manager.py    # Session lifecycle
├── hooks.py             # Hook system
├── workflows.py         # Workflow engine
├── telemetry.py        # Usage tracking
├── analytics.py        # Analytics dashboard
└── orchestrator.py     # Main orchestration

config/
├── roles.yaml          # Role configurations
├── workflows.yaml      # Workflow definitions
├── orchestration.yaml  # Orchestration settings
└── zen_models.json    # zen-mcp model config

docker/metamcp/
├── docker-compose.yml  # Docker services
└── orchestrator.env   # Environment config

docs/
├── MCP_ORCHESTRATION.md
├── ROLE_REFERENCE.md
├── ZEN_MCP_GUIDE.md
└── WORKFLOW_GUIDE.md

tests/mcp/
├── test_roles.py
├── test_workflows.py
├── test_session_manager.py
└── test_telemetry.py

.env.example           # Environment template
```

### Modified Files (5 files):
- `scripts/install-mcp-servers.sh` - Add zen-mcp
- `src/dopemux/config/manager.py` - Add orchestration config
- `src/dopemux/cli.py` - Add role/workflow commands
- `pyproject.toml` - Add dependencies (redis, sqlite-utils)
- `.claude/CLAUDE.md` - Update with orchestration info

## Success Metrics
- ✅ Token usage <10k per session (90% reduction)
- ✅ Role switching <200ms
- ✅ Automated session management
- ✅ Zero manual indexing required
- ✅ Complete task synchronization
- ✅ Knowledge preservation across sessions
- ✅ ADHD-friendly automated checkpoints

## Key Benefits
1. **Token Efficiency**: Only loads tools needed for current role
2. **Automation**: Session management happens transparently
3. **Flexibility**: Easy role customization via YAML
4. **Data-Driven**: Telemetry guides optimization
5. **Workflow Support**: Natural development progression
6. **ADHD-Optimized**: Automatic context preservation and checkpoints

## Token Optimization Strategy

### zen-mcp Tool Management
- Most zen tools disabled by default (analyze, refactor, testgen, secaudit, docgen, tracer, thinkdeep)
- Only enable specific tools for specific roles
- Use conservative thinking mode (low = 4k tokens vs high = 16k tokens)
- Manual activation for expensive tools like consensus and thinkdeep

### Role-Based Loading
- Maximum 10k tokens allocated per session
- Core servers (context7 search) always loaded (2k tokens)
- Role-specific tools loaded on demand (8k token budget)
- Automatic unloading when switching roles

### Context Window Management
- Small roles (PM, scrum): 25k context window, 6-8k token budget
- Medium roles (implementer, reviewer): 50k context window, 10-12k token budget
- Large roles (researcher, architect, debugger): 100k+ context window, 15k token budget

Ready to begin implementation when you give the go-ahead!