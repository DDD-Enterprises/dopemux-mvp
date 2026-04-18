# dopeCode Phase 2 Contract

## 1. Scope
Phase 2 upgrades the dopeCode transform layer from preview-only scaffolding into bounded, deterministic mutation flows on top of the existing AST/navigation foundation.

## 2. Authoritative Surfaces
- `services/serena/mcp_server.py` registers the operator tools and wires them into the dopeCode layers.
- `services/serena/dopecode/transform/write_layer.py` is the canonical bounded mutation writer.
- `services/serena/dopecode/transform/refactor_layer.py` is the canonical symbol refactor mutation layer.
- `services/serena/dopecode/navigation/ast_engine.py` remains the read/navigation authority for symbol and reference discovery.

## 3. Current Phase 2 Behavior

### Apply Patch
- Supports supported unified diff inputs for one workspace file.
- Rejects malformed hunks, multi-file patch payloads, and any path that resolves outside the workspace root.
- Applies mutations in pure Python without shell execution.
- Emits deterministic audit logs for success and no-op outcomes.

### Batch Apply Patch
- Sorts operations deterministically by path and original index.
- Returns preview receipts without mutating in preview mode.
- Executes operations in sorted order when `preview=False`.
- Continues after failures and reports partial failure explicitly.

### Rename Symbol
- Uses reference discovery plus deterministic file ordering.
- Preview returns affected-file inventory before apply.
- Apply performs workspace-bounded text replacement on word boundaries.
- Execution is deterministic and auditable.

### Replace Symbol Body
- Currently supports Python symbols only.
- Preview returns the affected file and the target line span.
- Apply preserves the symbol signature and replaces only the body block.
- Execution is workspace-bounded and auditable.

## 4. Hard Constraints
- No write may escape `DOPEMUX_WORKSPACE_ROOT`.
- No shell-based editing is used for these flows.
- dopeCode does not become PM truth, memory truth, retrieval truth, or project authority.
- Existing Dopemux/ADHD features must remain registered and operational.

## 5. Known Limits
- `replace_symbol_body` is implemented for Python symbols only.
- Patch application supports the unified diff shapes exercised by the regression tests, and rejects unsupported patch structures instead of guessing.
- Broader Serena test surfaces still include unrelated drift outside the dopeCode slice.

