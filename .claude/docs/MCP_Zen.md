# Zen MCP - Multi-Model Reasoning Suite

**Provider**: Dopemux
**Purpose**: Advanced multi-model reasoning, planning, debugging, and consensus building
**Servers**: `zen-mcp` (OpenAI, Gemini, xAI Grok, Anthropic Claude, and 50+ models via OpenRouter)

## Overview

Zen MCP provides a comprehensive suite of AI-powered reasoning tools that leverage multiple models for enhanced analysis, planning, and decision-making. Each tool uses specialized prompting strategies and multi-model validation for robust results.

## Available Tools

### 1. `zen/thinkdeep` - Multi-Step Investigation
**Use Case**: Complex problem analysis, root cause investigation, architectural decisions

**Features**:
- Hypothesis-driven investigation with evidence gathering
- Multi-step reasoning with confidence tracking
- File analysis and code inspection
- Expert model validation (optional)

**Parameters**:
- `step`: Current investigation step content
- `step_number`: Current step (1-based)
- `total_steps`: Estimated total steps needed
- `next_step_required`: Boolean for continuation
- `findings`: Key discoveries and evidence
- `confidence`: exploring → low → medium → high → very_high → almost_certain → certain
- `model`: o3-mini (default), gpt-5, gpt-5-mini

**Example**:
```
Use zen/thinkdeep to investigate why authentication fails intermittently
- Step 1: Analyze authentication flow and session management
- Step 2: Check database connection pooling and timeout settings
- Step 3: Review load balancer configuration for session affinity
```

### 2. `zen/planner` - Interactive Planning
**Use Case**: Breaking down complex tasks, project planning, implementation roadmaps

**Features**:
- Incremental plan building with revision support
- Branch exploration for alternative approaches
- Dependency tracking and phase identification
- Step-by-step plan refinement

**Parameters**:
- `step`: Planning content for current step
- `step_number`: Current step in planning sequence
- `total_steps`: Estimated planning steps
- `next_step_required`: Continue planning or finalize
- `is_revision`: Whether revising a previous step
- `is_branch_point`: Exploring alternative approach

**Example**:
```
Use zen/planner to create migration strategy from SQLite to PostgreSQL
- Step 1: Analyze current schema and data dependencies
- Step 2: Design PostgreSQL schema with optimizations
- Step 3: Plan zero-downtime migration approach
```

### 3. `zen/consensus` - Multi-Model Decision Making
**Use Case**: Architecture decisions, technology evaluation, design trade-offs

**Features**:
- Consults 2-5 models with different stances (for/against/neutral)
- Synthesizes perspectives into balanced recommendation
- Identifies points of agreement and disagreement
- Provides confidence scores and key takeaways

**Parameters**:
- `step`: Decision question or proposal to evaluate
- `models`: Array of {model, stance, stance_prompt} configs
- `findings`: Your analysis summary
- `step_number`: Current consultation step
- `total_steps`: Number of models to consult
- `next_step_required`: More models or finalize

**Example**:
```
Use zen/consensus to evaluate: "Should we use microservices or monolith for this project?"
- Consult o3-mini (for microservices)
- Consult gpt-5-mini (against microservices)
- Consult o3-mini (neutral analysis)
- Synthesize recommendation with trade-offs
```

### 4. `zen/debug` - Systematic Debugging
**Use Case**: Bug investigation, mysterious errors, performance issues, race conditions

**Features**:
- Hypothesis-testing debugging workflow
- Code inspection and log analysis
- Root cause identification with validation
- Fix recommendation with confidence scoring

**Parameters**:
- `step`: Investigation step describing bug symptoms or analysis
- `hypothesis`: Current theory about root cause
- `findings`: Evidence discovered (clues, code, logs)
- `confidence`: evolving as evidence accumulates
- `files_checked`: List of examined files
- `relevant_files`: Files directly related to issue

**Example**:
```
Use zen/debug to find why memory usage grows unbounded
- Hypothesis: Memory leak in event listener registration
- Check event subscription patterns in component lifecycle
- Validate cleanup in useEffect/componentWillUnmount
```

### 5. `zen/codereview` - Multi-Model Code Review
**Use Case**: Comprehensive code review covering quality, security, performance, architecture

**Features**:
- Systematic review across multiple dimensions
- Expert model validation for thoroughness
- Issue severity classification (critical/high/medium/low)
- Actionable recommendations with examples

**Parameters**:
- `step`: Review plan and findings for current step
- `relevant_files`: Files to review (absolute paths)
- `review_type`: full, security, performance, quick
- `focus_on`: Specific areas of concern
- `issues_found`: Array of {severity, description}

**Example**:
```
Use zen/codereview for security audit of authentication module
- Review type: security
- Focus on: JWT handling, password hashing, session management
- Check for: SQL injection, XSS, CSRF, timing attacks
```

### 6. `zen/challenge` - Critical Thinking Validation
**Use Case**: Preventing reflexive agreement, forcing deeper analysis of assertions

**Features**:
- Automatically triggers on user challenges or disagreements
- Forces critical evaluation rather than automatic agreement
- Truth-seeking over compliance
- Reasoned analysis with evidence

**Parameters**:
- `prompt`: User's challenging statement or question

**Example**:
```
Automatically activated when user questions a previous recommendation
Forces re-evaluation with critical thinking instead of agreement
```

## Best Practices

### ADHD Optimization
- **Step Chunking**: All tools support incremental processing (step_number, total_steps)
- **Progress Tracking**: Confidence levels show investigation progress
- **Interrupt/Resume**: Use continuation_id to resume previous sessions
- **Cognitive Load**: Tools handle complexity so you can focus on decisions

### Model Selection

**Top-Tier Models** (Intelligence 16-18):
- **Grok Code Fast 1** (18): Code generation, 2M context, FREE on OpenRouter!
- **Gemini 2.5 Pro** (18): Research, analysis, 1M context
- **GPT-5 Codex** (17): Code-specialized, 400K context
- **GPT-5** (16): General reasoning, extended thinking
- **Grok 4 Fast** (16): Reasoning model, 2M context, FREE!

**Mid-Tier Models** (Intelligence 12-15):
- **Claude Sonnet 4.5** (12): Architecture, fast reasoning
- **O3-Mini** (12): Balanced performance
- **Grok 3 Mini** (12): Fast efficient variant
- **O3-Mini High** (13): Complex problems
- **Opus 4.1** (14): Claude flagship
- **O3** (14): Balanced reasoning
- **Grok 3** (14): Vision support
- **DeepSeek R1** (15): Thinking mode
- **O3 Pro** (15): Professional grade
- **Grok 4** (15): Multi-modal

**Quick Guide**:
- **Research**: Gemini 2.5 Pro or Grok 4 Fast (both have massive context)
- **Code**: Grok Code Fast 1 (FREE!) or GPT-5 Codex
- **Architecture**: Claude Sonnet 4.5 or GPT-5
- **Debug**: Gemini 2.5 Pro (analysis strength)
- **Fast**: Flash models (Gemini Flash, Grok 4 Fast)

### When to Use Each Tool

**Use zen/thinkdeep when**:
- You need to investigate a complex problem systematically
- Multiple hypotheses need testing
- Evidence gathering and validation required

**Use zen/planner when**:
- Breaking down large projects into phases
- Need to explore alternative approaches
- Want interactive planning with revision capability

**Use zen/consensus when**:
- Making important architectural decisions
- Evaluating trade-offs between approaches
- Need multiple perspectives on a proposal

**Use zen/debug when**:
- Facing mysterious bugs or errors
- Performance issues with unclear cause
- Need systematic hypothesis testing

**Use zen/codereview when**:
- Comprehensive quality/security/performance review needed
- Pre-deployment validation required
- Want expert-validated analysis

## Integration with SuperClaude Commands

Zen MCP replaces SuperClaude's "Sequential MCP" with enhanced capabilities:

- `/sc:implement` → Uses zen/planner for complex implementation planning
- `/sc:workflow` → Uses zen/planner for PRD decomposition
- `/sc:brainstorm` → Uses zen/consensus for multi-perspective analysis
- `/sc:analyze` → Uses zen/thinkdeep for systematic code analysis
- `/sc:troubleshoot` → Uses zen/debug for bug investigation

## Performance

- **Response Time**: Typically 2-15 seconds depending on model and complexity
- **Context Window**: 200K tokens (o3-mini), 400K tokens (gpt-5)
- **ADHD Target**: All operations complete within attention span windows

## Limitations

- Requires valid API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY, GROQ_API_KEY)
- Model costs apply (especially o3-pro - use sparingly)
- Cannot execute code (read-only analysis)
- Limited to information available in provided context

---

**Status**: ✅ Fully operational in Dopemux
**Replaces**: SuperClaude's sequential MCP
**Enhancement**: Multi-model validation, interactive planning, consensus building
