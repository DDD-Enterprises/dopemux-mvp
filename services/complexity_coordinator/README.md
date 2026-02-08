# Complexity Coordinator

Unified complexity scoring service that combines:

- AST structural complexity (Dope-Context)
- LSP/semantic complexity (Serena)
- Usage/reference complexity (Serena DB)
- ADHD-aware user multiplier (ADHD Engine)

## Primary Module

- `/Users/hue/code/dopemux-mvp/services/complexity_coordinator/unified_complexity.py`

## Public API

- `get_complexity_coordinator()`
- `get_unified_complexity(file_path, symbol=None, user_id=\"default\")`

Returned payload includes:

- `ast_score`
- `lsp_score`
- `usage_score`
- `adhd_multiplier`
- `unified_score`
- `confidence`
- `interpretation`

## Notes

- Scoring output is clamped to `0.0..1.0`.
- When dependencies are unavailable, the coordinator degrades to safe fallback scores.
- Unit tests are in `/Users/hue/code/dopemux-mvp/tests/unit/test_unified_complexity_coordinator.py`.
