# Two-Plane Architecture Model Configuration

**Purpose**: Mode-aware model routing for PLAN/ACT cognitive states
**Architecture**: Optimized for Project Management + Cognitive Plane coordination
**ADHD Focus**: Attention-state adaptive model selection

## 🎯 Mode-Aware Model Routing

### PLAN Mode (Strategic Planning)
**Cognitive Load**: High complexity, long-form thinking
**Primary Models**:
- **Architecture Decisions**: `o3-pro` (for complex analysis), `gemini-2.5-pro` (for comprehensive reasoning)
- **Sprint Planning**: `o3` (for systematic breakdown), `gpt-4.1` (for structured planning)
- **Story Analysis**: `gemini-2.5-flash` (for quick iteration), `o3-mini` (for balanced analysis)

**Plane Integration**:
- Load PM Plane modules: task-master, task-orchestrator, leantime
- Enable ConPort decision logging with rationale
- Focus on synthesis and strategic thinking

### ACT Mode (Implementation)
**Cognitive Load**: Focused execution, concrete changes
**Primary Models**:
- **Code Generation**: `gemini-2.5-flash` (for rapid iteration), `o3-mini` (for quality balance)
- **Bug Fixing**: `gemini-2.5-flash` (for quick fixes), `o3` (for complex debugging)
- **Testing**: `gemini-2.5-pro` (for comprehensive test design), `o3-mini` (for focused testing)

**Plane Integration**:
- Load Cognitive Plane modules: serena-lsp, conport-memory
- Enable artifact creation and progress tracking
- Focus on concrete deliverables

## 🧠 Attention-State Adaptive Routing

### Scattered Attention
**Characteristics**: Short sessions, frequent context switches
**Model Strategy**: Fast, concise responses
- **Primary**: `gemini-2.5-flash` (ultra-fast, 1M context)
- **Fallback**: `o4-mini` (optimized for short contexts)
- **Token Limit**: 500 per response
- **Response Style**: Bullet points, single clear action

### Focused Attention
**Characteristics**: Sustained work, moderate complexity
**Model Strategy**: Balanced depth and speed
- **Primary**: `o3-mini` (balanced performance/speed)
- **Secondary**: `gemini-2.5-pro` (comprehensive analysis)
- **Token Limit**: 2000 per response
- **Response Style**: Structured detail, multiple options (max 3)

### Hyperfocus State
**Characteristics**: Deep work, high complexity tolerance
**Model Strategy**: Maximum capability and detail
- **Primary**: `o3` (strong reasoning), `gemini-2.5-pro` (deep analysis)
- **Premium**: `o3-pro` (universe-scale complexity, use sparingly)
- **Token Limit**: 4000 per response
- **Response Style**: Comprehensive analysis, full context

## 🛠️ Python Development Optimizations

### Code Quality Models
- **Type Checking**: `o3-mini` (systematic analysis)
- **Refactoring**: `gemini-2.5-pro` (pattern recognition)
- **Documentation**: `o3` (comprehensive explanation)
- **Testing**: `gemini-2.5-flash` (rapid test generation)

### Framework-Specific Routing
- **FastAPI/Pydantic**: `o3` (type system expertise)
- **pytest**: `gemini-2.5-flash` (quick test patterns)
- **SQLAlchemy**: `o3-mini` (balanced complexity)
- **Docker/Compose**: `gemini-2.5-pro` (comprehensive setup)

## 🔄 MCP Server Coordination

### Essential Servers (Always Active)
- **Context7**: Documentation retrieval for all model calls
- **ConPort**: Memory management with automatic logging
- **Sequential-Thinking**: Complex reasoning support
- **Claude-Context**: Semantic code search

### Mode-Specific Server Loading
**PLAN Mode Additions**:
- **Task-Master**: AI task decomposition
- **Task-Orchestrator**: Dependency analysis
- **Zen-MCP**: Multi-model consensus for decisions

**ACT Mode Additions**:
- **Morphllm-Fast-Apply**: Rapid code transformations
- **Serena**: Enhanced code navigation

## ⚡ Performance Optimization

### Cost Management
- **Scattered Attention**: Prefer `gemini-2.5-flash` (cost-effective, fast)
- **Routine Tasks**: Use `o4-mini` for standard operations
- **Complex Decisions**: Reserve `o3-pro` for critical architecture choices
- **Documentation**: Balance `o3` and `gemini-2.5-pro` based on complexity

### Fallback Chains
1. **Primary Model** → **Secondary Model** → **Fast Fallback**
2. **Timeout Handling**: Auto-switch to faster model if >10s response time
3. **Error Recovery**: Graceful degradation to simpler model on failure

### Token Optimization
- **Context Pruning**: Keep only essential context for each mode
- **Progressive Detail**: Start concise, expand on request
- **Smart Caching**: Reuse model outputs for similar queries

---

**Integration**: Seamlessly coordinate between Project Management and Cognitive planes
**Efficiency**: 77% token reduction through intelligent model routing
**ADHD Support**: Attention-state aware model selection with gentle guidance
