# dopeCode Phase 5 Implementation Summary

## 1. What Changed
- Extended `services/serena/dopecode/navigation/ast_engine.py` with a shared script parser cache for JavaScript, TypeScript, and TSX grammars.
- Added bounded TypeScript symbol extraction for top-level functions, exported functions, classes, and function-valued lexical declarations.
- Added bounded TypeScript callee resolution for local symbols and workspace-local relative value imports.
- Added TypeScript import graph resolution for `.ts`, `.tsx`, `.js`, `.jsx`, and index file candidates.
- Ignored TypeScript `import type` statements for value import and callee resolution.
- Extended `services/serena/dopecode/transform/refactor_layer.py` so `replace_symbol_body` supports block-bodied TypeScript functions, classes, and function-valued declarations.
- Added `approval_receipt()` to `services/serena/dopecode/policy/mutation_policy.py`.
- Surfaced `approval_receipt` in write and refactor mutation responses.
- Removed stale analyzer locals/imports flagged in review and made empty JavaScript/TypeScript body replacement fail closed.

## 2. Mutation Model
- Single-file patch application remains directly executable when workspace-bounded.
- Batch patch operations expose preview-required and approval-required execution modes through both `policy` and `approval_receipt`.
- Symbol refactors expose preview-required and approval-required execution modes through both `policy` and `approval_receipt`.
- TypeScript body replacement uses the same preview/apply separation as Python and JavaScript.
- No shell mutation paths were introduced.

## 3. TypeScript Fail-Closed Behavior
- Inline TypeScript arrow bodies are not rewritten by `replace_symbol_body`.
- Type-only imports are not treated as callable value imports.
- Unsupported TypeScript-only declaration forms are not promoted into mutation targets.
- Parser initialization failure returns empty language-specific results instead of guessing.

## 4. Test Coverage Added
- TypeScript symbol discovery for `.tsx` files.
- TypeScript callee resolution for local symbols and workspace-local relative value imports.
- TypeScript import graph resolution to `.ts` files.
- Type-only import exclusion from value import graph results.
- TypeScript block-body replacement preview/apply behavior.
- TypeScript inline arrow-expression replacement failure.
- Approval receipt assertions for direct, preview-required, and approval-required mutation modes.

## 5. Validation Results
- Passed:
  - `pytest -q services/serena/tests/test_dopecode_ast_engine.py services/serena/tests/test_dopecode_write_layer.py services/serena/tests/test_dopecode_refactor_layer.py services/serena/tests/test_dopecode_policy.py`
  - `pre-commit run --files services/serena/dopecode/navigation/ast_engine.py services/serena/dopecode/policy/mutation_policy.py services/serena/dopecode/transform/refactor_layer.py services/serena/dopecode/transform/write_layer.py services/serena/tests/test_dopecode_ast_engine.py services/serena/tests/test_dopecode_policy.py services/serena/tests/test_dopecode_refactor_layer.py services/serena/tests/test_dopecode_write_layer.py proof/dopecode_phase5_contract.md proof/dopecode_phase5_implementation.md proof/dopecode_phase5.proof.json`
  - `python -m json.tool proof/dopecode_phase5.proof.json`
- Manual diff review found and fixed one material TypeScript issue: `import type` was initially treated as a value import. Type-only imports are now ignored by value import and callee resolution.

## 6. Remaining Limits
- Broader TypeScript semantics remain out of scope.
- Runtime wiring and MCP registration did not require changes because existing dopeCode tools return the updated layer responses.
- Broader repository drift outside the dopeCode slice remains unverified in this pass.
