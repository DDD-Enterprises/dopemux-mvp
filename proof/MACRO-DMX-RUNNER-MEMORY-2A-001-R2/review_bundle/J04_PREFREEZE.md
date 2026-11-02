# MACRO-DMX-RUNNER-MEMORY-2A-001-R2 — J04 pre-freeze record

**Recorded:** 2026-11-01 (UTC), by the team lead (Control Tower supervisor session). Authority: NONE.

## Operator rulings (verbatim)

| Answer | In answer to |
|---|---|
| "Yes, merge main first (Recommended)" | "Update feat/runner-memory-2a from main (6fb9d8179, trial merge is clean) before freezing it for the audit?" |
| "Grok + AGY (Recommended)" | "Which independent route should run 2A's single final L3 audit (it must be a different model family from the Claude implementers)?" |

## Merge

| Item | Value |
|---|---|
| Merged | `origin/main` at `6fb9d8179` (includes #1482, Route Ledger) into `feat/runner-memory-2a` |
| Merge commit | `3e1c4aa58` |
| Parents | `c7604ec1c` (2A) and `6fb9d8179` (main) |
| Result | trial merge and real merge both clean, no conflicts; 216 files came in from main |
| Pushed | no, local only |

## Tests on the merge head

Whole 2A set, services venv:

| Included | Result |
|---|---|
| all W suites, guard, ConPort wiring, hooks, MCP config, catalog tests, all of `tests/arch`, repair, capture, ledgers, dope-memory endpoint, MCP lifecycle, caller suites, `tests/pr_steward`, `tests/dcp` | **2,127 passed**, 1 deselected |

The deselected test is the pre-existing `tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified`. It diffs `.github/workflows/` from an old packet base, and it fails on main too.

## Still before freeze (doctrine: CI and reviews settle before the substantive freeze)

1. **CI has not run.** The branch has never been pushed, and pushing it (a draft PR) is not yet authorized.
2. **Freeze.** The head after CI settles becomes the audit subject.
3. **Audit packet.** Grok (grok-4.5, tool-less) and AGY (gemini-4-argon-high, sandboxed), following #1482's R6 recipe, with operator gate lines.
   - The 2A diff is much larger than R6's, so the audit input needs a scoping plan: a delta summary, the key files in full, and the return records.
4. **After the audit:** signing, the ADR-MCPINT-002 amendment's acceptance, and merge. All remain operator gates.
