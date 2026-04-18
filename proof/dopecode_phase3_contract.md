# dopeCode Phase 3 Contract

## 1. Scope
Phase 3 decomposes dopeCode into cleaner runtime layers, introduces an explicit mutation policy layer, and strengthens graph/callee intelligence without weakening the verified Phase 2 bounded mutation contract.

## 2. Authoritative Surfaces
- `services/serena/mcp_server.py` remains the operator-facing MCP registration surface.
- `services/serena/dopecode/runtime.py` is the runtime bundle that wires policy, navigation, and transform layers.
- `services/serena/dopecode/policy/mutation_policy.py` is the explicit mutation policy surface.
- `services/serena/dopecode/navigation/ast_engine.py` remains the navigation authority.
- `services/serena/dopecode/transform/write_layer.py` and `services/serena/dopecode/transform/refactor_layer.py` remain the bounded mutation authorities.

## 3. Current Phase 3 Behavior

### Runtime Decomposition
- dopeCode layer construction is bundled through `DopeCodeRuntime`.
- `mcp_server.py` keeps the public tool surface stable while delegating layer setup and dependency hydration.
- Existing Dopemux/ADHD feature registration remains in `mcp_server.py`.

### Mutation Policy
- Single-file patch operations are classified as directly executable bounded mutations.
- Batch patch operations are policy-classified as multi-file operations and expose explicit preview requirements and blast radius.
- Symbol refactors surface policy-visible blast radius and approval level.
- Policy data is returned in mutation responses as structured evidence.

### Navigation / Graph Intelligence
- `find_callees` now returns deterministic callee metadata including `kind`, `resolved_name`, `resolved_file`, and confidence.
- Python import graph output includes resolved local file paths when the import target exists in the workspace.
- Unsupported language cases fail closed instead of guessing cross-file relationships.

## 4. Hard Constraints
- dopeCode remains workspace-scoped for all mutation.
- No write may escape `DOPEMUX_WORKSPACE_ROOT`.
- No shell-based editing or arbitrary subprocess mutation is used.
- dopeCode remains separate from PM truth, memory truth, retrieval truth, and project authority.
- Phase 2 bounded mutation behavior must not regress.
- Deterministic ordering and preview/apply separation remain required.

## 5. Known Limits
- Callee resolution is strengthened for Python but remains language-limited.
- Cross-file certainty is reported only where the workspace-local import target is resolvable.
- `replace_symbol_body` remains Python-only.

