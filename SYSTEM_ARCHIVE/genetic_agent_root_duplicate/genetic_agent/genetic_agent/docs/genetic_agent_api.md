# Genetic Coding Agent API Documentation

## Overview

The Genetic Coding Agent is a hybrid AI system that combines Large Language Models (LLMs), Genetic Programming (GP), and Multi-Component Processing (MCP) services for automated code repair and optimization. The system implements a research-based approach to code repair, learning from historical patterns and adapting strategies based on bug complexity and context.

## Architecture

### Core Components

- **GeneticAgent**: Main agent implementing hybrid LLM + GP repair
- **VanillaAgent**: Baseline LLM-only repair agent for comparison
- **MCP Integrations**:
  - **Zen MCP**: Multi-model reasoning and planning
  - **DopeContext MCP**: Semantic code search and pattern discovery
  - **Serena MCP**: Code complexity analysis
  - **ConPort MCP**: Knowledge graph and memory management

### Complete Zen-Enhanced Repair Flow

The genetic agent now implements a comprehensive multi-model repair pipeline using all major Zen tools:

#### Phase 0: Zen Thinkdeep - Comprehensive Reasoning
- **Purpose**: Overall repair approach and root cause hypothesis
- **Input**: Bug description, file context
- **Output**: Root cause hypothesis, recommended strategy, expected challenges, success criteria
- **Model**: gpt-5-codex for code-focused reasoning

#### Phase 1: Analysis (Serena + Enhanced DopeContext)
- **Serena**: Code complexity scoring (0.0-1.0)
- **DopeContext**: Multi-query semantic search (fix/bug/error/repair patterns)
- **Output**: Detailed context with complexity and similar patterns (top 10, deduplicated)

#### Phase 1.5: Zen Planner - Strategy Selection
- **Purpose**: Choose selective vs standard GP based on complexity and history
- **Input**: Analysis context, historical patterns from ConPort
- **Output**: Optimal repair strategy
- **Model**: gemini-2.5-pro for planning

#### Phase 2: LLM Generation (Pattern-Enhanced)
- **Input**: Detailed context with patterns from DopeContext
- **Process**: Generate initial repair with confidence based on pattern availability
- **Output**: Code candidate with explanation and confidence score

#### Phase 3: GP Optimization
- **Selective GP**: Small population (3-5) for complex bugs
- **Standard GP**: Full population evolution for routine bugs
- **Fitness Function**: Multi-objective (test success 40%, size 30%, quality 30%)
- **Research-Based**: Chronicle methodology with operator learning

#### Phase 4: Zen Consensus Validation
- **Purpose**: Multi-model validation of generated repair
- **Models**: gpt-5-codex (neutral), gemini-2.5-pro (critical), gpt-5 (optimistic)
- **Output**: Approval recommendation with risks and confidence

#### Phase 5: Zen Codereview - Quality Assessment
- **Focus**: Functional correctness, security, performance, code quality, architecture fit
- **Output**: Approval with issues list and recommendations
- **Model**: gpt-5-codex for code-focused review

#### Phase 6: Zen Precommit - Safety Validation
- **Purpose**: Final validation before committing
- **Checks**: Syntax, breaking changes, performance impact, integration, security
- **Output**: Ready-to-commit recommendation
- **Model**: gpt-5-codex for comprehensive validation

#### Learning Loop (ConPort)
- All Zen decisions and outcomes logged for future improvement
- Failure patterns analyzed for strategy refinement
- Operator performance tracked for evolution

**Full Flow Diagram:**
```
Bug Report → [Zen Thinkdeep: Reasoning] → [Serena + DopeContext: Analysis] → [Zen Planner: Strategy]
                ↓
        [LLM Generation: Pattern-Enhanced] → [GP Optimization: Research-Based]
                ↓
        [Zen Consensus: Validation] → [Zen Codereview: Quality] → [Zen Precommit: Safety] → Success
                ↓
              [ConPort: Log for Learning] ←─────────────────────── [All Phases]
```

## API Endpoints

### Core Repair Endpoints

#### `POST /repair/auto`
Automatically selects the best agent (genetic preferred) for code repair.

**Request Body:**
```json
{
  "bug_description": "string - Description of the bug or issue",
  "file_path": "string - Path to the file containing the bug",
  "line_number": "integer - Line number where bug occurs (optional)"
}
```

**Response:**
```json
{
  "success": "boolean",
  "confidence": "number (0.0-1.0)",
  "repair": "string - Generated code repair",
  "iterations": "integer - Number of repair attempts",
  "explanation": "string - Explanation of the repair",
  "method": "string - Repair method used (validated_llm|gp_reviewed|hybrid_reviewed|gp_precommit)",
  "candidates_evaluated": "integer - Total candidates considered",
  "agent_used": "string - Agent that performed the repair",
  "zen_integration": {
    "planning_used": "boolean",
    "strategy": "string",
    "reasoning_available": "boolean"
  },
  "reasoning": {
    "root_cause": "string",
    "recommended_strategy": "string",
    "expected_challenges": ["array"],
    "integration_points": ["array"],
    "success_criteria": ["array"]
  },
  "review_analysis": {
    "approved": "boolean",
    "quality_score": "number",
    "issues": ["array"],
    "recommendations": ["array"],
    "detailed_review": "string"
  },
  "debug_analysis": {
    "root_causes": ["array"],
    "systemic_issues": ["array"],
    "improvements": ["array"],
    "needed_capabilities": ["array"]
  }
}
```

**Failure Response (when no suitable repair found):**
```json
{
  "success": false,
  "confidence": 0.0,
  "repair": null,
  "iterations": "integer",
  "explanation": "No suitable repair found",
  "candidates_evaluated": "integer",
  "reasoning": "object from Zen thinkdeep",
  "debug_analysis": "object from Zen debug",
  "review_analysis": "object from Zen codereview"
}
```

#### `POST /repair/genetic`
Uses the genetic agent with hybrid LLM + GP optimization.

**Request Body:** Same as `/repair/auto`

**Response:** Same as `/repair/auto` with additional genetic programming metrics

#### `POST /repair/vanilla`
Uses the baseline LLM-only agent for comparison and research.

**Request Body:** Same as `/repair/auto`

**Response:** Same as `/repair/auto`

### Status and Monitoring

#### `GET /status`
Get comprehensive system status including agent health and performance metrics.

**Response:**
```json
{
  "system": "healthy|degraded|error",
  "version": "string",
  "vanilla_agent": {
    "status": "active|inactive",
    "circuit_breaker": "closed|open"
  },
  "genetic_agent": {
    "status": "active|inactive",
    "population_size": "integer",
    "generations_completed": "integer",
    "circuit_breaker": "closed|open"
  }
}
```

#### `GET /health`
Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "string",
  "agents": {
    "vanilla": "boolean",
    "genetic": "boolean"
  }
}
```

#### `GET /dashboard`
Performance dashboard with genetic programming metrics.

**Response:**
```json
{
  "version": "string",
  "timestamp": "string",
  "summary": {
    "total_repairs_attempted": "integer",
    "success_rate": "number",
    "average_confidence": "number"
  },
  "operator_performance": {
    "llm_initial": {
      "avg_fitness": "number",
      "success_rate": "number",
      "usage_count": "integer"
    },
    "selective_gp": {
      "avg_fitness": "number",
      "success_rate": "number",
      "usage_count": "integer"
    }
  },
  "recent_activity": [
    {
      "type": "failure_pattern",
      "signals": ["array of failure signals"],
      "timestamp": "string"
    }
  ]
}
```

#### `GET /dashboard/operators`
Detailed operator performance statistics.

**Response:**
```json
{
  "operators": {
    "operator_name": {
      "avg_fitness": "number",
      "success_rate": "number",
      "usage_count": "integer",
      "last_used": "timestamp"
    }
  },
  "total_operators": "integer",
  "top_performer": "string"
}
```

### Administration

#### `POST /reset/{agent_type}`
Reset an agent (for testing/admin purposes).

**Parameters:**
- `agent_type`: `"vanilla"` or `"genetic"`

**Response:**
```json
{
  "message": "Agent reset successfully"
}
```

## Zen MCP Integration

### Strategy Planning
The genetic agent uses Zen's planner tool for intelligent repair strategy selection:

- **Selective GP**: Used for complex/novel bugs with small populations (3-5 candidates)
- **Standard GP**: Used for routine bugs with full population evolution

**Decision Factors:**
- Bug complexity score (0.0-1.0 from Serena)
- Similar pattern count from DopeContext
- Historical failure patterns from ConPort
- Bug description length and novelty

### Planning Process
```python
# Zen planner analyzes context and recommends strategy
response = await zen_client.planner(
    step=planning_prompt,
    step_number=1,
    total_steps=1,
    next_step_required=False,
    model="gemini-2.5-pro"
)
```

## DopeContext Integration

### Enhanced Pattern Discovery
The genetic agent uses DopeContext for comprehensive bug pattern analysis:

**Multi-Query Search:**
- `"fix {bug_description}"` - Direct repair patterns
- `"bug {bug_description}"` - Bug manifestation patterns
- `"error {bug_description}"` - Error handling patterns
- `"repair {bug_description}"` - Repair implementation patterns

**ADHD-Optimized Results:**
- Deduplication by code similarity
- Relevance-based sorting
- Top 10 results limit to prevent overwhelm
- Complexity score integration

### Pattern-Based Repair Enhancement
```python
# Enhanced LLM generation based on patterns
if similar_patterns:
    confidence = min(0.8, base_confidence + 0.2)  # Boost confidence with patterns
    explanation = f"Pattern-based repair using {len(similar_patterns)} similar fixes"
```

## ConPort Integration

### Research-Based Learning
The genetic agent logs all repair attempts and outcomes to ConPort for continuous learning:

**Logged Data:**
- Attempt metadata (operator, fitness, context)
- Strategy decisions with Zen planner results
- Failure patterns and signals
- Session summaries with aggregate metrics

**Learning Loop:**
```
Repair Attempt → ConPort Logging → Pattern Analysis → Strategy Improvement
```

### Memory Adapter
```python
# Log repair attempts for research learning
await memory_adapter.log_attempt(
    attempt_number=iteration,
    operator=f"zen_planner_{strategy}",
    fitness_score=confidence,
    context=repair_context,
    success=confidence >= threshold
)
```

## Configuration

### Agent Configuration
```python
class AgentConfig(BaseSettings):
    # Quality thresholds
    confidence_threshold: float = 0.7
    max_tokens: int = 24000
    timeout_seconds: int = 300

    # Genetic algorithm parameters
    population_size: int = 10
    max_generations: int = 5
    crossover_rate: float = 0.8
    mutation_rate: float = 0.2
    max_tree_depth: int = 5

    # MCP service URLs
    conport_url: str = "http://localhost:3000"
    serena_url: str = "http://localhost:3001"
    dope_context_url: str = "http://localhost:3002"
    zen_url: str = "http://localhost:3003"
    workspace_id: str = "/app/workspace"

    # Infrastructure
    redis_url: str = "redis://localhost:6379"
```

### MCP Configuration
```python
class MCPConfig(BaseSettings):
    timeout: int = 30
    retry_attempts: int = 3
    health_check_interval: int = 300
```

## Fitness Functions

### Research-Based Multi-Objective Scoring
The genetic agent uses Chronicle methodology with three weighted components:

**Component 1: Test Success (40% weight)**
- Syntax validation as proxy for basic correctness
- Actual test execution when available

**Component 2: Size Penalty (30% weight)**
- Penalizes code over 50 lines (Chronicle research)
- `penalty = max(0, (lines - 50) * 0.1)`

**Component 3: Code Quality (30% weight)**
- AST complexity analysis
- Linting-style penalties for code quality issues

**Final Fitness:**
```python
fitness = (
    0.4 * test_success +
    0.3 * (1.0 - size_penalty) +
    0.3 * (1.0 - lint_penalty)
)
```

## Error Handling

### Circuit Breaker Pattern
- Agents implement circuit breaker pattern for fault tolerance
- Automatic fallback between genetic and vanilla agents
- Service health monitoring with MCP health checks

### Graceful Degradation
- MCP service failures don't break core functionality
- Fallback to mock responses with reduced confidence
- Comprehensive error logging for debugging

## Usage Examples

### Basic Bug Repair
```python
import requests

response = requests.post("http://localhost:8000/repair/auto", json={
    "bug_description": "null pointer exception in user authentication",
    "file_path": "/app/auth.py",
    "line_number": 42
})

if response.json()["success"]:
    repair_code = response.json()["repair"]
    print(f"Repair generated with {response.json()['confidence']:.1f} confidence")
```

### Advanced Configuration
```python
# Custom agent configuration
config = AgentConfig(
    confidence_threshold=0.8,
    population_size=20,
    max_generations=10,
    zen_url="http://custom-zen:3003"
)

agent = GeneticAgent(config)
```

## Performance Characteristics

### Response Times
- **Simple bugs**: 5-15 seconds (LLM-only)
- **Complex bugs**: 30-120 seconds (LLM + GP optimization)
- **Novel bugs**: 60-300 seconds (Research-based selective GP)

### Quality Metrics
- **Success Rate**: 70-85% depending on bug complexity
- **Average Confidence**: 0.75-0.85 for successful repairs
- **Operator Learning**: Continuous improvement through ConPort logging

## Research Integration

### Genetic Programming Operators
- **Mutation**: negate_condition, swap_operator, change_operand
- **Crossover**: subtree_swap, one_point_crossover
- **Selection**: tournament_selection, fitness_proportional

### Learning from History
- **Failure Pattern Analysis**: Identifies recurring failure modes
- **Operator Success Tracking**: Learns which operators work for specific contexts
- **Strategy Optimization**: Adapts repair approach based on historical performance

## Deployment

### Docker Configuration
```yaml
services:
  genetic-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GENETIC_AGENT_CONPORT_URL=http://conport:3000
      - GENETIC_AGENT_SERENA_URL=http://serena:3001
      - GENETIC_AGENT_DOPE_CONTEXT_URL=http://dope-context:3002
      - GENETIC_AGENT_ZEN_URL=http://zen:3003
    depends_on:
      - conport
      - serena
      - dope-context
      - zen
```

### Health Monitoring
```bash
# Health check
curl http://localhost:8000/health

# Status monitoring
curl http://localhost:8000/status

# Performance dashboard
curl http://localhost:8000/dashboard
```

## Troubleshooting

### Common Issues

**MCP Service Unavailable:**
```json
{
  "success": false,
  "error": "MCP service unavailable",
  "fallback": "using mock responses"
}
```

**Low Confidence Repairs:**
- Check DopeContext for similar patterns
- Verify Serena complexity analysis
- Review ConPort historical performance

**Genetic Algorithm Stuck:**
- Increase population size
- Adjust mutation/crossover rates
- Check fitness function implementation

### Debug Endpoints

**Enable Debug Logging:**
```bash
export GENETIC_AGENT_LOG_LEVEL=DEBUG
```

**View Recent Activity:**
```bash
curl http://localhost:8000/dashboard | jq '.recent_activity'
```

**Check Operator Performance:**
```bash
curl http://localhost:8000/dashboard/operators
```

---

## Integration with Dopemux Ultra UI

The Genetic Coding Agent integrates with the Dopemux Ultra UI ADHD accommodation system:

- **Cognitive Load Management**: Uses Serena complexity analysis for ADHD-safe code exploration
- **Energy-Aware Scheduling**: Adapts repair strategies based on user energy patterns
- **Break Integration**: Respects ADHD-optimized 25-minute focus sessions
- **Context Preservation**: Maintains repair state across interruptions
- **Progressive Disclosure**: Limits results to prevent cognitive overwhelm

This creates an ADHD-optimized development workflow where the genetic agent learns from user patterns and adapts its repair strategies accordingly.