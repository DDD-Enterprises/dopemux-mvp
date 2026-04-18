# dopeCode Phase 4 Contract

## 1. Scope
Phase 4 expands dopeCode beyond the verified Python-only graph/refactor path by adding one bounded second-language path for JavaScript and making mutation policy output explicit about direct, preview-required, and approval-required execution modes.

## 2. Authoritative Surfaces
- `services/serena/dopecode/navigation/ast_engine.py` is the navigation authority for Python and JavaScript symbol, callee, and import graph extraction.
- `services/serena/dopecode/transform/refactor_layer.py` remains the bounded refactor authority.
- `services/serena/dopecode/transform/write_layer.py` remains the workspace-bounded mutation authority.
- `services/serena/dopecode/policy/mutation_policy.py` is the explicit mutation policy surface.
- `services/serena/dopecode/runtime.py` continues to bundle policy, navigation, and transform layers.
- `services/serena/mcp_server.py` remains the operator-facing MCP registration surface.

## 3. Current Phase 4 Behavior
- JavaScript is the selected second language for this packet because the installed tree-sitter stack supports it and the repo already exposes `.js` and `.jsx` navigation surfaces.
- `get_file_symbols` now returns bounded JavaScript symbol inventory for top-level functions, exported functions, classes, and block-bodied function-valued declarations.
- `find_callees` now resolves JavaScript callees deterministically for local symbols and workspace-local relative imports.
- `get_import_graph` now reports JavaScript imports and workspace-local resolved paths when the imported file exists under the source file's directory.
- `replace_symbol_body` now supports Python symbols and block-bodied JavaScript function/class bodies while preserving workspace bounds.
- `MutationPolicyDecision` now exposes `execution_mode` and `requires_approval` so mutation responses can distinguish `direct`, `preview_required`, and `approval_required` outcomes.

## 4. Hard Constraints
- dopeCode remains workspace-scoped for all mutation.
- No write may escape `DOPEMUX_WORKSPACE_ROOT`.
- No shell-based editing or arbitrary subprocess mutation is used.
- dopeCode remains separate from PM truth, memory truth, retrieval truth, and project authority.
- Phase 2 bounded mutation behavior must not regress.
- Phase 3 preview/apply separation and policy evidence must not regress.
- Unsupported language cases must fail closed rather than guess.

## 5. Known Limits
- TypeScript remains fail-closed in this phase.
- JavaScript body replacement is bounded to block-bodied functions and classes; inline body forms remain fail-closed.
- JavaScript import resolution is workspace-local and relative to the source file's directory.
