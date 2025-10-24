# Unified Complexity Coordinator

**Status**: Implemented (Synergy A)
**Version**: 1.0.0

## Overview

Combines complexity signals from multiple systems into a single unified score:
- **dope-context**: AST structural complexity (50% weight)
- **Serena v2**: LSP usage patterns (30% weight)
- **ADHD Engine**: User-specific adjustments (20% weight)

## Algorithm

```
unified_score = (
    ast_complexity * 0.50 +      # Structural complexity
    usage_complexity * 0.30      # How widely used
) * (1.0 + (user_multiplier - 1.0) * 0.20)  # ADHD personalization
```

## Usage

```python
from services.shared.complexity_coordinator import ComplexityCoordinator

coordinator = ComplexityCoordinator(
    dope_context_client=dope_client,
    serena_client=serena_client,
    adhd_engine_client=adhd_client
)

result = await coordinator.get_unified_complexity(
    file_path="src/auth/middleware.py",
    symbol="authenticate_request",
    user_id="user123"
)

print(f"Unified: {result.unified_score}")
print(f"AST: {result.ast_complexity}")
print(f"Usage: {result.usage_complexity}")
print(f"ADHD: {result.user_multiplier}")
```

## Benefits

- Single source of truth for complexity
- Better accuracy (hybrid approach)
- Reduced computation (cache once, use everywhere)
- Personalized to ADHD patterns

## Integration

**Next Steps** (requires MCP tool additions):
1. Add `get_chunk_complexity()` to dope-context
2. Add `get_symbol_metadata()` to Serena
3. Add `get_complexity_adjustment()` to ADHD Engine
4. Integrate into search/navigation workflows
