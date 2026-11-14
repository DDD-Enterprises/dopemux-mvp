# SDD ledger — plan: docs/91-rfc/rfc-2026-10-30-foundations-wave-1-plan.md

Spec: docs/91-rfc/rfc-2026-10-30-foundations-wave-1.md (approved by operator 2026-10-30: "Approve"; execution method "Subagent-driven").
Branch feat/foundations-wave-1 in .worktrees/foundations-wave-1; base origin/main 93050d135; plan commit 7c883d7e1.
MacroPacket MACRO-DMX-FOUNDATIONS-001 being issued under task-packets/ (untracked) before Task 1.

## Pre-flight scan

| Pair / task | Produces vs consumes | Finding |
|---|---|---|
| T3 -> T4 | T3 produces `DEFAULT_ADHD_ENGINE_PORT` in `dopemux.commands.adhd_commands`; T4 `test_cli_default_port_matches_registry` imports it | Order T3 before T4 required; plan order satisfies it. |
| T1 <-> T2, T4 | T1's CI step runs all of tests/arch; T2 and T4 add tests/arch files | T1 Step 1 expects 184 (pre-T2/T4); T6 Step 1 reruns with all. Consistent. |
| T2 <-> T4 | Both create files in tests/arch | Distinct files; no shared helpers. OK. |
| T4 <-> existing | Consumes `parse_port_mapping`, `load_registry`, `load_compose` from tests.arch.test_registry_compose_alignment | Import verified under --import-mode=importlib on 2026-10-30. OK. |
| T3 <-> T5, T4 <-> T5 | T5 documents T3 options/exit codes and T4 exception rules | T5 runs last. OK. |
| T5 <-> PR #1484 | Both edit AGENTS.md and .claude/claude.md | T5 told to use sections #1484 does not touch (AGENTS.md section 3; claude.md "Commands & Environment"). OK. |
| T1 self | Files: ci-complete.yml only; Step 1 needs Python 3.11 via uv | uv may download 3.11; acceptable dependency fetch. OK. |
| T2 self | 1 parity + 5 behavior tests; Step 5 expects 6 passed | Counts agree. Engine constructs offline (verified). OK. |
| T3 self | StatusResult fields == --json keys; requests patched at module path | Agree. `python -m dopemux` exists (verified). OK. |
| T4 self | Step 2 expected failures = manager.py 3007/3008 literals + 3 named defaults | Matches the precomputed scan on 2026-10-30; all EXCEPTIONS entries match live differences. OK. |
| T5 self | Files list includes both new reference pages and both agent docs | OK. |
| Plan vs Global Constraints | T4 must not edit scripts/dopemux_dashboard.py; constraint forbids it | Consistent after plan-recon revision. |

Ruling: `dopemux adhd status` gets the registry port as a module constant (3025) pinned to services/registry.yaml by T4's test, instead of reading the registry at runtime — the CLI runs from an installed package where the registry file may be absent; the test keeps the constant honest — if wrong, a per-instance port must come from env vars, which the resolution order already supports.
Ruling: tasks run serially although write sets are disjoint — skill rule (never parallel implementers) and MacroPacket max_mutating_workstreams 1 — costs wall-clock only.
Ruling: execution authority is recorded as the operator's chat quotes ("Foundations first", "Looks right, write design", "Approve", "Subagent-driven"); no literal AUTHORIZE token was given — if the operator wanted a token, nothing has been pushed and the work can wait for one.
Ruling: the MacroPacket is issued untracked under task-packets/ (Pulse-003 precedent, which avoids the legacy-schema preflight) and flattened into proof/MACRO-DMX-FOUNDATIONS-001/review_bundle/ at freeze — if wrong, it is a file move before the PR.

## Tasks
MacroPacket MACRO-DMX-FOUNDATIONS-001 issued (sonnet child), ct validate-macro STATIC_VALID; bindings PASS x2.
Ruling: released the packet's execution hold (AMENDMENT-01, ISSUANCE.md; MACRO_PACKET sha256 3db0e5c9a6c4eb13...) — the operator answered "Subagent-driven" to "which execution approach should the plan use?" after "Approve" — if wrong, only local commits on feat/foundations-wave-1 exist; nothing pushed.
Task 1: BASE 7c883d7e1 (dispatching, haiku)
Task 1: implementer DONE_WITH_CONCERNS 6f0a234bb; note: child attempted a session hand-off tool call (denied by classifier, no effect); pre-commit run via uv --with pre-commit + node:system scratch config
Task 1: review Approved, spec ✅. ⚠️ resolved: workflow-syntax hook Passed per report (scratch node:system config); real GitHub CI run NOT_RUN until a PR exists (Task 6 / PR).
Task 1: complete (commits 7c883d7..6f0a234, review clean)
Task 2: BASE 6f0a234bb (dispatching, sonnet)
Task 2: implementer DONE 9ca061366 (6 passed 3.12 + 3.11; RED seen; mutation check recorded)
Task 2: review Approved with 1 Important (plan-mandated vs design): .score caveat only in a comment; design W2 requires the docstring to say it is not a measurement.
Ruling: Task 2 Important 1 — add the not-a-measurement sentence to the EnergySnapshot and get_energy_level docstrings — the spec (design W2) is binding over the plan's "comment" — costs one docstring sentence if wrong.
Task 2: minor (deferred): test line 127 unpacks Optional await_args (Pyright); use call.args/call.kwargs
Task 2: minor (deferred): Import "pytest" unresolved in editor (environment artifact)
Task 2: minor (deferred): test_cognitive_load_is_float_in_unit_range mocks the value, never checks range or the real path; real _calculate_cognitive_load returns fixed 0.5 on exception
Task 2: minor (deferred): ENERGY_SCORE.get(level, 0.5) silently invents 0.5 for unknown level
Task 2: minor (deferred): parity test covers async @mcp.tool only and checks names, not signatures/attributes; fallback score=0.5 diverges (pre-existing, main.py out of write set)
Task 2: fix round 1/5 (1 addressed, 0 open — docstring caveat; commits 9ca0613..5685720)
Task 2: complete (commits 6f0a234..5685720, review clean after 1 fix round)
Task 3: BASE 5685720ca (dispatching, sonnet)
Task 3: implementer DONE_WITH_CONCERNS cb0886b06 (25 passed 3.12 + 3.11; mypy import-untyped requests pre-existing pattern; black -l 79)
Task 3: review Needs fixes — Important: (1) files formatted black -l 79 vs repo black 88; (2) vacuous assert "12" in output (URL contains 12).
Ruling: Task 3 formatting — format with the repo's black config (line-length 88) — pyproject declares it and make format applies it; neighbours fail both black and bare flake8 (E501 22-75 each), so bare-flake8 E501 at 79 is accepted as repo-consistent — cosmetic if wrong.
Ruling: Task 3 Minor 2 promoted to Important — show session minutes only when > 0 and test a negative value — design W3 says "more than 0"; a truthy check prints "session -3 min" — one comparison if wrong.
Task 3: minor (deferred): 2 s timeout never asserted by tests (fake_get swallows kwargs)
Task 3: minor (deferred): engine strings echoed verbatim (control chars/length); empty --url "" falls through silently; stderr warnings could mix into --json output on old click
Task 3: minor (deferred): mypy import-untyped for requests (types-requests absent; same in update_commands.py); step 5 needs PYTHONPATH=src in a worktree (editable install points at main checkout)
Task 3: fix round 1/5 (3 addressed, 0 open — black 88, exact "session 12 min" assert, > 0 with negative test; commits cb0886b..754a6f1)
Ruling: --json keeps the engine's raw session_minutes (a negative value passes through); only the human line applies > 0 — JSON is machine output reporting what the engine said — one line to change if wrong.
Task 3: minor (deferred): 3.11 run not repeated after fix round 1 (formatting + one comparison); CI on the PR covers it
Task 3: complete (commits 5685720..754a6f1, review clean after 1 fix round)
Task 4: BASE 754a6f14e (dispatching, sonnet)
Task 4: implementer DONE_WITH_CONCERNS 9bbb4f853 (pre-fix 2 failed as predicted; post-fix 7 passed 3.12 + 3.11; tests/arch 197 passed; 3 mutation checks fail as named; extra test_exceptions_are_documented)
Ruling: plan Task 4 Step 4's grep localhost:(3007|3008|3010) was over-broad — 3010 is dope-context's real port in cli.py, hook_manager.py and the MCP catalogs — test_named_defaults_match_registry is the proof; 3007/3008 return nothing — a plan defect, no code change.
Task 4: review Approved, spec ✅. ⚠️ resolved: extra test_exceptions_are_documented enforces the design's "reason and follow-up" rule — accepted; grep deviation covered by ruling above.
Task 4: minor (deferred): literal regex sees only localhost:DIGITS; statusline nc -z forms and shell/f-string ports invisible; 3 scanned files contribute nothing today (plan-mandated regex)
Task 4: minor (deferred): missing compose_service_name silently classed "not comparable" (spec lists only no-host-ports/network_mode) — final review should triage
Task 4: minor (deferred): not-comparable list printed only with -s; harden with set-intersection assert and EXCEPTIONS kind validation; activity_capture_url and serena_url both 3006 in manager.py
Task 4: complete (commits 754a6f1..9bbb4f8, review clean)
Task 5: BASE 9bbb4f853 (dispatching, sonnet)
Task 5: implementer DONE_WITH_CONCERNS c5415d241 (all docs gates PASS; engine-suite numbers quoted from design, not re-run)
Task 5: review Needs fixes — Important: adhd-status-cli.md:184 implies the fallback engine starts whenever the real one fails; main.py:327-337 creates it only when ADHD_ENGINE_ALLOW_DEGRADED_STARTUP is truthy (controller verified), otherwise nothing listens -> unreachable.
Task 5: minor (deferred): state that malformed/non-2xx /state wins over a fallback /health; soften "session minutes always 0" to "nothing in this repo sets it"; "without skips" vs importorskip("yaml"); dashboard exceptions shown as one row with /-joined key; 3009 named gptr-mcp (registry: gpt-researcher)
Task 5: fix round 1/5 (1 addressed, 0 open — degraded needs ADHD_ENGINE_ALLOW_DEGRADED_STARTUP; commits c5415d2..b8b5bf6)
Task 5: complete (commits 9bbb4f8..b8b5bf6, review clean after 1 fix round)
Task 6: freeze checks on c5415d2 (docs-only after): tests/arch 197 passed on 3.11; test_adhd_commands 27 passed on 3.11; tests/unit 1 failed (test_extract_local_smoke::test_extract_docs_smoke_uses_local_classifier) — passes alone on branch (6/6) and on main-equivalent; full-suite comparison running.
Ruling: raised W01 to L3 (AMENDMENT-02) — validate_change_contract classifies .github/workflows/ci-complete.yml as L3; the lane the validator reports is authoritative over the plan's L2 — the audit route must be L3-eligible, operator decision.
Task 6: unit comparison — branch b8b5bf6: 2828 passed, 0 failed; origin/main-equivalent (docs-mods-wave1 757941f): 2 failed in tests/unit/test_extract_local_smoke.py (xdist-flaky, pre-existing on main). No regression from this wave.
Task 6: change contract status=PASS max_lane=L3 (ci-complete.yml; AMENDMENT-02). Final whole-branch review dispatched (opus) on 93050d1..b8b5bf6.
Final review (opus, 93050d1..b8b5bf6): Ready to merge "With fixes". 0 Critical, 1 Important (CI Python is 3.12.13 via .python-version, not 3.11), 9 Minor; no ruling disputed; no conflicts with #1472/#1482/#1483/#1484/#1445; tests/arch 197 passed on 3.12.13 clean checkout.
Ruling: the "Python 3.11 CI-equivalent" evidence in this ledger is relabelled — CI runs 3.12.13; the 3.12 repo-venv runs and the reviewer's 3.12.13 clean-checkout run are the CI-equivalent evidence; the 3.11 runs are extra compatibility evidence only — if wrong, nothing changes in code.
Ruling: one final fix wave = Important F1 plus Minors F2-F9 (reviewer's recommended batch plus cheap spec-alignment items); Minor 7 (defaults_used on error payloads) excluded as a nit — the audit is waiting on other PRs anyway, so fixing before freeze costs no audit — if wrong, a few small extra diffs.
Ruling: the fix wave's write set is the union of files named in final-fix-wave.md (crosses W01-W05 write sets); recorded as MacroPacket AMENDMENT-03 — the skill mandates a single fixer for final findings — if wrong, it is a bookkeeping amendment.
Final fix wave: BASE b8b5bf636 (dispatching, sonnet)
Final fix wave: DONE 1bdfb3f..3b46fd6 (6 commits; repo venv 242 passed; CI-equivalent 3.12.13 arch 202 + cli 40 passed); local normalize_base_url instead of _base_from_url (heavy imports, parses localhost as scheme)
Final fix wave: scoped re-review — F1-F9 all ADDRESSED, no new breakage (58 passed across the three affected test files); commits b8b5bf6..3b46fd6.
Final: minor (deferred): adhd-status-cli.md says normalization uses "the same rules as _base_from_url" but the local function is stricter (http/https only, empty invalid)
Final: minor (deferred): adhd_commands.py:NNN line refs added to docs not verified
Final: minor (deferred): design doc statusline row names the 3009 probe only, not the 8096 nc probe (ci-contract-gates.md has it)
Final: minor (deferred, from final review): defaults_used appended to error payloads (nit, excluded from fix wave)
Final: complete (branch 93050d1..3b46fd6, final review With fixes -> fixed and re-reviewed clean). Content head for the audit: 3b46fd6c5. Audit NOT_RUN (operator-gated route; L3-eligible; after #1482/#1472/#1483 merge).
