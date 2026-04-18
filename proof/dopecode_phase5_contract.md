# dopeCode Phase 5 Contract

## 1. Scope
Phase 5 extends the Phase 4 Python and JavaScript dopeCode behavior with a bounded TypeScript path and operator-visible approval receipts in mutation responses.

## 2. Authoritative Surfaces
- `services/serena/dopecode/navigation/ast_engine.py` is the navigation authority for Python, JavaScript, and the bounded TypeScript subset.
- `services/serena/dopecode/transform/refactor_layer.py` remains the bounded refactor authority.
- `services/serena/dopecode/transform/write_layer.py` remains the workspace-bounded mutation authority.
- `services/serena/dopecode/policy/mutation_policy.py` is the explicit mutation policy and approval receipt source.
- `services/serena/dopecode/runtime.py` continues to bundle policy, navigation, and transform layers.
- `services/serena/mcp_server.py` remains the operator-facing MCP registration surface.

## 3. TypeScript Subset
- `.ts` files use the installed `tree_sitter_typescript.language_typescript()` grammar.
- `.tsx` files use the installed `tree_sitter_typescript.language_tsx()` grammar.
- TypeScript symbol discovery is bounded to top-level functions, exported functions, classes, and function-valued lexical declarations with parser-visible bodies.
- TypeScript callee resolution is bounded to local symbols and workspace-local relative value imports.
- TypeScript import graph support is bounded to value imports with workspace-local relative resolution for `.ts`, `.tsx`, `.js`, `.jsx`, and index files.
- Type-only imports are ignored for value import and callee resolution.
- `replace_symbol_body` supports TypeScript block-bodied functions, classes, and block-bodied function-valued declarations where the parser exposes a `statement_block` or `class_body`.

## 4. Approval Receipts
- Mutation responses expose `approval_receipt` alongside existing `policy` evidence.
- `approval_receipt` includes operation, operation class, execution mode, approval requirement, preview requirement, approval level, blast radius, and affected files.
- Single-file bounded patches remain `direct`.
- Batch patches preview as `preview_required` and apply as `approval_required`.
- Symbol refactors preview as `preview_required` and apply as `approval_required`.
- dopeCode reports approval state but does not become approval authority or the operator control plane.

## 5. Hard Constraints
- dopeCode remains workspace-scoped for all mutation.
- No write may escape `DOPEMUX_WORKSPACE_ROOT`.
- No shell-based editing or arbitrary subprocess mutation is used by dopeCode.
- dopemux remains the operator/control plane.
- dopeCode remains separate from PM truth, memory truth, retrieval truth, and project authority.
- Phase 2 bounded mutation behavior must not regress.
- Phase 3 preview/apply separation and policy evidence must not regress.
- Phase 4 JavaScript support must not regress.
- Unsupported TypeScript cases fail closed rather than guess.

## 6. Known Limits
- TypeScript support is not general semantic TypeScript analysis.
- Type-only imports are intentionally ignored by value import and callee resolution.
- Interface, type alias, enum, namespace, decorator, overload, generic constraint, and ambient declaration semantics are not represented as supported mutation targets.
- Inline arrow-expression bodies remain fail-closed for `replace_symbol_body`.
- Import resolution remains workspace-local and relative to the source file's directory.
