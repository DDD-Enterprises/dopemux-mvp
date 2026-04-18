# dopeCode Phase 6 Contract

## 1. Scope
Phase 6 strengthens semantic certainty reporting and operator-facing mutation receipts for the existing Python, JavaScript, and bounded TypeScript dopeCode surface.

## 2. Authoritative Surfaces
- `services/serena/dopecode/navigation/ast_engine.py` is the navigation authority for symbol discovery, bounded callee resolution, and import graph reporting.
- `services/serena/dopecode/policy/mutation_policy.py` is the explicit mutation policy and approval receipt authority.
- `services/serena/dopecode/transform/write_layer.py` remains the bounded single-file and batch mutation authority.
- `services/serena/dopecode/transform/refactor_layer.py` remains the bounded symbol refactor authority and now exposes structured refactor planning receipts.
- `services/serena/dopecode/runtime.py` remains the runtime bundle for policy, navigation, write, and refactor layers.
- `services/serena/mcp_server.py` remains the operator-facing MCP registration surface.

## 3. Semantic Certainty Model
- `find_callees` continues to operate only on supported Python, JavaScript, and bounded TypeScript paths.
- Each callee now exposes explicit `resolution_status`, `certainty`, `reason_code`, and `confidence`.
- `resolution_status` is one of `resolved`, `partial`, or `unresolved`.
- `certainty` is bounded to the supported dopeCode model, including `exact`, `workspace_local`, `approximate`, `external_or_unresolved_import`, and `unresolved`.
- `reason_code` is explicit for supported resolved paths and fail-closed unresolved paths.
- Aggregate semantic reporting is emitted through `semantic_summary` with stable count fields.
- Unsupported dynamic or ambiguous cases remain fail closed; dopeCode does not guess hidden targets.

## 4. Operator Receipt Model
- `approval_receipt` remains operator-visible and does not make dopeCode the approval authority.
- `approval_receipt` now includes stable `execution_status`, `risk_tier`, `reason`, and `affected_file_summary` fields.
- `execution_mode` remains the policy mode indicator; `execution_status` is the operator-facing state summary.
- `refactor_plan` is exposed in preview responses for supported symbol refactors.
- `refactor_plan` includes target symbol, mutation type, confidence, confidence reason, supported targets, affected file summary, file receipts where available, skipped targets, and fail-closed reasons.

## 5. Hard Constraints
- dopeCode remains workspace-scoped for all mutation.
- No write may escape `DOPEMUX_WORKSPACE_ROOT`.
- No shell-based editing or arbitrary subprocess mutation is used by dopeCode.
- dopemux remains the operator/control plane.
- dopeCode remains separate from PM truth, memory truth, retrieval truth, and project authority.
- Phase 2 bounded mutation behavior must not regress.
- Phase 3 policy evidence and preview/apply separation must not regress.
- Phase 4 JavaScript support must not regress.
- Phase 5 TypeScript support and approval receipt behavior must not regress.
- Unsupported semantic cases must fail closed rather than guess.

## 6. Known Limits
- Semantic certainty remains bounded to parser-visible and workspace-local evidence, not full language-server semantics.
- Import resolution remains workspace-local and source-directory-relative.
- Inline JavaScript and TypeScript arrow-expression bodies remain fail-closed for `replace_symbol_body`.
- TypeScript interfaces, enums, namespaces, overloads, decorators, ambient declarations, and related broader semantic forms remain out of scope as mutation targets.
- `find_callees` does not infer hidden dynamic targets beyond explicit unresolved or approximate reporting.
