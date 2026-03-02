# DOPEMUX ORCHESTRATION
**Project**: Dopemux Dev Platform | **Framework**: SuperClaude + AB-Method

## MCP SERVERS

```yaml
conport: Project memory, context persistence, knowledge graphs
claude-context: Conversation history, decision tracking, past work
exa: Advanced web search, documentation lookup, research
task-master-ai: Task orchestration, workflow mgmt, multi-step coordination
serena: Semantic code understanding, session persistence, symbol ops, LSP
cli: System commands, file operations, terminal access
zen: Planning, architecture design, strategic thinking
sequential-thinking: Multi-step reasoning, hypothesis testing, complex debugging
context7: Official library docs, framework patterns (React/Vue/Angular/Next)
playwright: Browser automation, E2E testing, visual validation, WCAG
morphllm-fast-apply: Pattern-based edits, bulk transformations, style enforcement
magic: UI components from 21st.dev patterns, design systems
```

## TECHNIQUES

### REV THE ENGINE (Multi-Round Planning)
For critical decisions → multiple rounds:
```
Round 1: Initial analysis + ultrathink → solution paths
Round 2: Critique → find gaps, edge cases, alternatives  
Round 3: Optimize → performance, maintainability, validation
Round 4: Final plan → implementation steps, rollback strategies
```

### SPLIT-ROLE SUB-AGENTS
```python
# Deploy parallel perspectives
perspectives = [
    "senior engineer",     # technical implementation
    "security expert",     # vulnerability assessment
    "performance engineer",# optimization opportunities
    "UX specialist",      # user experience impact
    "QA engineer",        # testing strategy
    "DevOps"             # deployment considerations
]
# Each gets independent context → no cross-contamination
```

### TASK/AGENT TOOLS
```python
# Parallel execution pattern (>3 files)
tasks = [
    "Task 1: Analyze codebase",
    "Task 2: Research best practices", 
    "Task 3: Security implications",
    "Task 4: Performance impact",
    "Task 5: Test cases",
    "Task 6: Documentation",
    "Task 7: Deployment plan"
]
# Execute with 7+ sub-agents in parallel
```

### CUSTOM AGENTS
```yaml
# .claude/agents/[name].md
---
name: code-reviewer-cr1
description: PROACTIVE code review. MUST BE USED after changes.
tools: Read, Grep, Bash  # Minimal for token efficiency (<3k)
model: sonnet  # haiku=simple, sonnet=balanced, opus=complex
---
You are CR1, ensuring code quality...
[Review checklist, output format, boundaries]
```

**Token Optimization**:
- Lightweight (<3k tokens): CR1, T1, P1, D1 - frequent ops
- Medium (10-15k): S1, U1, DO1 - specialized domain
- Heavy (25k+): MO1, ST1 - orchestration only

## WORKFLOW PATTERNS

### Standard Feature Flow
```python
# ALWAYS this sequence
async def implement_feature(name):
    # 1. Documentation first
    docs = await context7.search(name)
    
    # 2. Planning
    plan = await zen.create_plan(name)
    
    # 3. Orchestration
    tasks = await task_master_ai.decompose(plan)
    
    # 4. Parallel execution
    results = await parallel_execute(tasks)
    
    # 5. Testing
    tests = await playwright.test(results)
    
    # 6. Memory
    await conport.store(name, results)
```

### When to Use Each MCP
```python
# Documentation (ALWAYS FIRST)
if need_api_info or library_docs:
    use_context7()  # Official docs, not web search
    
# Planning complex features
if complex_architecture:
    use_zen()  # Strategic planning
    use_sequential_thinking()  # Step-by-step breakdown
    
# Workflows
if multi_step_task:
    use_task_master_ai()  # Orchestrate workflow
    
# Memory
if architectural_decision or important_context:
    use_conport()  # Persist to project memory
    
# Past work
if referencing_previous:
    use_claude_context()  # Review history
    
# System ops
if file_operations or terminal:
    use_cli()  # Direct system access
    
# Testing
if ui_testing:
    use_playwright()  # E2E testing
    
# UI Development
if creating_components:
    use_magic()  # React/Vue components
    
# Refactoring
if bulk_changes:
    use_morphllm_fast_apply()  # Pattern transforms
    
# Symbol operations
if rename_function or find_references:
    use_serena()  # Semantic understanding
```

## AB-METHOD INTEGRATION
```yaml
ideation:
  tools: [zen, exa]
  output: requirements, user stories
  
architecture:
  tools: [context7, sequential-thinking]
  output: system design, technical specs
  
implementation:
  story: task-master-ai creates
  develop: cli executes
  test: playwright validates
  review: split-role analysis
  
validation:
  tools: [playwright, task-master-ai]
  output: test results, metrics
```

### BDD Templates
```
GIVEN: [precondition/context]
WHEN: [action/event]
THEN: [expected outcome]
```

## SUPERCLAUDE COMMANDS
```bash
# Core
/sc:analyze      # Deep analysis
/sc:implement    # Feature implementation
/sc:build        # Compilation/packaging
/sc:improve      # Code optimization
/sc:test         # Test generation
/sc:troubleshoot # Debug issues
/sc:document     # Generate docs
/sc:git          # Git operations
/sc:task         # Task management

# Dopemux Extensions
/dmx:orchestrate # Multi-agent workflow
/dmx:rev         # Rev the engine (deep planning)
/dmx:split       # Split role analysis
/dmx:parallel    # Parallel task execution
```

## CRITICAL RULES

1. **context7 first** - ALWAYS check docs before assumptions
2. **conport saves** - Store important decisions for memory
3. **task-master** - Use for multi-step workflows
4. **rev-engine** - Apply for complex architectural decisions
5. **split-role** - Deploy for comprehensive analysis
6. **parallel** - Execute independent ops with Task tool
7. **playwright** - Test any UI changes
8. **claude-context** - Reference for past discussions

## PROJECT INITIALIZATION
```python
# Starting Dopemux work
1. Check conport for existing context
2. Review claude-context for previous discussions
3. Use zen to plan session work
4. Coordinate with task-master-ai
5. Store progress in conport regularly
```

## ERROR RECOVERY
```python
if failure:
    1. sequential_thinking.analyze(failure)
    2. context7.check_correct_api_usage()
    3. claude_context.search_similar_issues()
    4. zen.create_recovery_plan()
    5. conport.document_solution()
```

## PERFORMANCE OPTIMIZATION

- **Lightweight agents** for simple tasks
- **Parallel ops** when independent
- **Cache docs** frequently accessed
- **Batch operations** together
- **Strip comments** when analyzing
- **Use references** not full content

## AGENT DEPLOYMENT

### Auto-Invocation
```python
def deploy_agents(event, context):
    agents = []
    
    # Always after code changes
    if event in ['code_modified', 'pr_created']:
        agents.append('CR1')
    
    # Performance issues
    if 'slow' in context:
        agents.append('P1')
    
    # Missing tests
    if not has_tests(context):
        agents.append('T1')
    
    # Security-sensitive
    if touches_auth(context):
        agents.append('S1')
    
    # UI changes
    if touches_ui(context):
        agents.append('U1')
    
    # Complex coordination
    if len(agents) > 3:
        agents = ['MO1']  # Meta orchestrator
    
    return agents
```

### Manual Invocation
```bash
# Direct
ask CR1 to review changes
ask P1, T1, S1 to analyze payment module

# Batch
ask all tier1 agents to review
```

## SESSION LIFECYCLE
```python
# Start
dopemux init
SuperClaude install --profile developer

# Work session
/sc:load  # Load context
# ... work ...
/sc:save  # Save progress

# MCP test
dopemux mcp test  # Verify connections
```

## Remember

Building Dopemux requires:
- Leverage MCP servers effectively
- Use parallel processing when possible
- Apply multi-perspective analysis for critical decisions
- Store important context for future reference
- Follow AB-Method principles
- Prioritize code quality and maintainability
