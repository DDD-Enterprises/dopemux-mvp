# ADR-007: Routing Logic Architecture

## Status
**Accepted** - Provider-agnostic routing layer with adaptive fallback

## Context

Dopemux requires intelligent routing of AI requests across multiple providers to ensure:
- Optimal cost/performance balance
- Resilience against provider outages or rate limits
- Task-specific model selection
- ADHD-optimized response times through smart provider selection

The routing layer must handle Claude subscription (native), API-based providers (OpenRouter), and specialized models while maintaining transparent fallback behavior.

## Decision

**Provider-Agnostic Routing Layer** with four task-specific routes:
- **default**: Interactive coding (cc-default via Claude subscription)
- **background**: Cost-optimized long-running tasks
- **think**: Reasoning-enabled models for complex analysis
- **longContext**: Context-aware routing based on token thresholds

## Architecture

### Core Components

```yaml
Dopemux Router Architecture:
  Control_Plane:
    - Config Store (hot-reloadable YAML)
    - Circuit Breakers (target health monitoring)
    - Budget Management (spend governance)
    - Observability (metrics, logs, traces)

  Data_Plane:
    - Route Classification (task → route mapping)
    - Target Selection (priority-ordered provider list)
    - Adapter Layer (provider API normalization)
    - Retry Logic (jittered backoff with circuit breaking)
```

### Request Lifecycle Flow

```
[Request] → Classify Task → Route Selection → Target List → Provider Attempts → Response

1) Task Classification:
   - longContext: estimated_tokens > threshold
   - think: reasoning trace requested
   - background: non-interactive tasks
   - default: interactive coding/chat

2) Target Priority List:
   - Route-specific provider ordering
   - Circuit breaker status check
   - Budget/rate limit validation

3) Provider Attempts:
   - Transform via adapter
   - Call with retries
   - Handle errors (429/5xx/4xx)
   - Circuit breaker updates
```

## Route Strategies

### 1. Default Route (cc-default)
**Purpose**: Interactive coding with highest UX fidelity
```yaml
primary: Claude_Subscription  # Native Claude via Claude Code UI
fallbacks:
  - DeepSeek_V3.1 (OpenRouter)
  - Qwen3-Coder (OpenRouter)
  - GPT-5 (OpenRouter, if enabled)

triggers_to_fallback:
  - Usage/weekly limit message
  - HTTP 429 rate limiting
  - Repeated 5xx errors
  - Explicit user override (/model command)
```

### 2. Background Route
**Purpose**: Cost/latency-optimized for long-running tasks
```yaml
primary: Grok_Code_Fast_1 (OpenRouter)
fallbacks:
  - DeepSeek_V3.1
  - Default chain

use_cases:
  - Code indexing
  - Scaffold generation
  - Batch processing
```

### 3. Think Route
**Purpose**: Reasoning traces for complex analysis
```yaml
primary: DeepSeek_R1 (reasoning-enabled)
behavior:
  - Capture reasoning_content fields
  - Persist thought traces to artifacts
  - Retention policy for debugging
```

### 4. Long Context Route
**Purpose**: Context-aware routing based on token usage
```yaml
routing_thresholds:
  <= 128k_tokens: DeepSeek_V3.1 (cost-effective)
  128k-400k_tokens: GPT-5 (mid-range quality)
  > 400k_tokens: Gemini_2.5_Pro (1M context)

optional_anthropic:
  > 400k_tokens: Sonnet_4 (if API key supplied)
```

## Error Handling & Resilience

### Circuit Breaker Pattern
```yaml
failure_detection:
  - 429/usage_limit: immediate breaker open
  - 5xx/network: limited retries → breaker if repeated
  - 4xx/invalid_request: no retry, surface error

breaker_states:
  closed: normal operation
  open: temporary "do not use"
  half_open: limited traffic to test recovery

recovery_logic:
  - Exponential backoff intervals
  - Health check requests
  - Gradual traffic restoration
```

### Adapter Normalization
```yaml
adapter_types:
  claude_subscription: Native Claude Code UI integration
  openai_compatible: Standard OpenAI chat format
  anthropic_messages: Anthropic-specific message format
  reasoning_enhanced: DeepSeek reasoning fields

transformation_pipeline:
  request: Dopemux_format → Provider_format
  response: Provider_format → Dopemux_format
  streaming: Chunk-by-chunk normalization
```

## Configuration Schema

### Provider Configuration
```yaml
providers:
  - name: anthropic_native
    type: claude_subscription
    # Uses local Claude Code session, no API key

  - name: openrouter
    type: openai_compatible
    api_base: https://openrouter.ai/api/v1
    api_key: env:OPENROUTER_API_KEY

models:
  - id: cc_sonnet4
    provider: anthropic_native
    meta:
      family: claude-sonnet
      max_context: 200k
      quality: high
      cost_tier: native

  - id: or_deepseek_v31
    provider: openrouter
    meta:
      family: deepseek
      max_context: 256k
      quality: medium
      cost_tier: budget
```

### Route Configuration
```yaml
routes:
  default:
    targets: [cc_sonnet4, or_deepseek_v31, or_qwen3_coder]
    retry_policy: immediate
    circuit_breaker: true

  background:
    targets: [or_grok_code_fast, or_deepseek_v31]
    retry_policy: patient
    cost_optimization: true

  think:
    targets: [or_deepseek_r1, or_deepseek_v31]
    capture_reasoning: true
    persist_traces: true

  longContext:
    targets:
      - threshold: 128k
        models: [or_deepseek_v31]
      - threshold: 400k
        models: [or_gpt5]
      - threshold: 1M
        models: [gcp_gemini_2_5_pro]
```

## ADHD Optimizations

### Response Time Optimization
- **Native Claude First**: Fastest path for interactive coding
- **Circuit Breaker Fast-Fail**: Immediate fallback on provider issues
- **Context-Aware Routing**: Prevent long-context timeouts

### Cognitive Load Reduction
- **Transparent Fallback**: User unaware of provider switching
- **Consistent Interface**: Same API regardless of underlying model
- **Smart Defaults**: Optimal model selection without user decisions

### Attention Management
- **Streaming Responses**: Immediate feedback during processing
- **Error Recovery**: Graceful degradation without user intervention
- **Status Visibility**: Optional routing visibility for debugging

## Implementation Considerations

### Performance Targets
```yaml
latency_requirements:
  route_classification: < 10ms
  provider_selection: < 5ms
  adapter_transformation: < 20ms
  total_overhead: < 50ms (ADHD critical)

reliability_targets:
  availability: 99.9% (considering provider fallbacks)
  error_recovery: < 2 seconds to fallback
  circuit_breaker_reaction: < 100ms
```

### Observability & Monitoring
```yaml
metrics:
  - route_selection_latency
  - provider_success_rate
  - circuit_breaker_state
  - cost_per_request
  - context_window_utilization

logging:
  - structured_json: true
  - request_tracing: true
  - error_classification: detailed
  - budget_tracking: per_route
```

## Consequences

### Positive
- **Provider Independence**: Not locked to single AI provider
- **Cost Optimization**: Automatic routing to cost-effective models
- **Resilience**: Graceful degradation on provider failures
- **Performance**: ADHD-optimized response times
- **Transparency**: User unaware of complex routing logic

### Negative
- **Complexity**: Additional layer increases system complexity
- **Debugging**: Harder to trace issues across multiple providers
- **Configuration**: More configuration surface area
- **Latency**: Routing logic adds minimal overhead

### Risks and Mitigations
- **Provider API Changes**: Adapter layer isolates impact
- **Rate Limit Cascading**: Circuit breakers prevent cascade failures
- **Cost Overruns**: Budget governance and monitoring
- **Routing Logic Bugs**: Comprehensive testing and fallback to defaults

## Related Decisions
- **ADR-006**: MCP server selection complements routing logic
- **ADR-001**: Hub-and-spoke architecture enables centralized routing
- **Future ADR-008**: Task management integration with routing
- **Future ADR-009**: Session persistence across provider switches

## References
- Routing Logic Design: `/research/integrations/dopemux_routing_logic_design_doc_spec_v_0.md`
- Provider Integration: `/research/integrations/multi-instance-claude-code-research.md`
- Circuit Breaker Pattern: Martin Fowler's Circuit Breaker documentation