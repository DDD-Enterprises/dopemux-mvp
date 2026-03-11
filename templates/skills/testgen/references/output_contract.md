# Output Contract

Emit a single JSON-compatible report object with these keys:

- `request`: normalized invocation inputs.
- `requirements`: parsed requirement list with stable IDs.
- `tool_strategy`: chosen deepthinking/planning/analysis and specialist-routing strategy.
- `traceability_matrix`: requirement-to-test mapping.
- `layer_plan`: all five layers with applicability flags.
- `na_layers`: subset of non-applicable layers with rationale and evidence.
- `coverage_gate`: target, measured percent, status, and missing-evidence diagnostics.
- `next_actions`: ordered execution instructions.

Status values:

- `pass`: coverage measured and threshold met.
- `fail`: coverage measured and threshold missed.
- `error`: coverage unresolved or ambiguous (fail closed).
- `pending`: coverage not evaluated yet.
