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

## Push (operator ruling, 2026-11-02)

| Answer | In answer to |
|---|---|
| "Yes, push draft PR" | "Push feat/runner-memory-2a and open a draft PR so CI runs?" |

| Item | Value |
|---|---|
| Covers | pushing `feat/runner-memory-2a` and opening it as a **draft** PR so CI runs |
| Does not cover | marking it ready, merging, signing, the audit dispatch, a second merge from main |
| Secret scan of the diff | only test fixtures with fake passwords |
| `scripts/check_root_hygiene.py --all-files` | exit 1, pre-existing: all 11 flagged files are on `origin/main` (`FINAL_*`, `.antigravitycli/*.json`, three `caveman` rule files); 2A's only root-level changes, `AGENTS.md` and `mcp_catalog.yaml`, are not flagged |
| main since the merge | `origin/main` moved to `75dacb43f` (#1483, Memory Bridge); a trial merge with HEAD is clean; not merged (the earlier ruling named `6fb9d8179`) |

## Second merge from main (operator ruling, 2026-11-04)

| Answer | In answer to |
|---|---|
| "Yes, merge main now" | "Merge the new main (#1483) into 2A now, before the freeze?" |

| Item | Value |
|---|---|
| Merged | `origin/main` at `75dacb43f` (#1483, Memory Bridge), re-checked as still current immediately before merging |
| Merge commit | `2fc49a1c2`; parents `eb601b33a` (2A) and `75dacb43f` (main) |
| Result | no conflicts |
| Whole 2A set on that merge, services venv | **2,127 passed**, 1 deselected (the same `test_16`), exit 0 |

## CI on the draft PR (#1498) at `eb601b33a`

Passed: Unit Tests, all static and governance jobs except the two below, and every image build except adhd-engine, including conport and dope-memory (W10's COPY lines).

| Check | State | Cause | Caused by 2A? |
|---|---|---|---|
| Scout × 9 | fail | Docker Hub login rejects `DOCKER_SCOUT_HUB_USER/PASSWORD`; same error on `fix/mcp-fleet-r1-repair`, 2026-10-19. Clearing it is a credential change, owner-gated | No. Scout runs only on Dockerfile changes; W10 changed two |
| Build adhd-engine | fail (cancelled) | `timeout-minutes: 30` hit about 2 minutes short. `pip install .[services]` took 1,693 s (326 s on 2026-10-19) and finished; the 183 s export got about 75 s. Most of it was `Preparing metadata` and source wheels on Alpine. The exact upstream change is UNKNOWN | No dependency input changed: `pyproject.toml` is unchanged on main since 2026-10-19 and 2A does not touch it. The only 2A change in adhd-engine is `conport_client.py` |
| independent embedded audit | fail | `audit_not_executed`, `audit_provenance_missing` | No, expected until the audit |
| PR Steward / final readiness | fail | chained to the audit run | No, expected until the audit |

Unresolved review threads: 0.

A cancelled build exports no cache, and `COPY src` comes before pip in that Dockerfile, so the merge push repeats the 28-minute step. If it times out again, the fix sits in `.github/workflows/containers.yml` or the Dockerfile, both outside 2A's write surface, and needs an operator ruling.

At `4550f3ff5` Build adhd-engine passed on the re-run, and Unit Tests and every other required check passed except the audit and PR Steward.

## Freeze of `4550f3ff5` held (operator ruling, 2026-11-04)

| Answer | In answer to |
|---|---|
| "Yes, freeze it" | "Freeze `4550f3ff5` and write the audit packet now?" |
| "Yes, approve it" | "Approve Amendment 05?" |

J04-FREEZE's `make test` failed at `4550f3ff5`, and 2A caused it, so that head was not frozen. See `AMENDMENT_05.md`: W13 repairs the test code, the gate now means no new failures against main, and the head that carries W13 becomes the freeze subject.

## Third merge from main (operator ruling, 2026-11-04)

| Answer | In answer to |
|---|---|
| "Yes, merge main" | "Merge the new main (#1486) into 2A before `make test` and the push?" |

| Item | Value |
|---|---|
| Merged | `origin/main` at `4cd889877` (#1486, ui-dashboard), re-checked as still current immediately before merging |
| Merge commit | `1a81686f9`; parents `4ff9ce5c5` (2A with W13) and `4cd889877` (main) |
| Result | no conflicts; no file overlap with 2A |

## Still before freeze (doctrine: CI and reviews settle before the substantive freeze)

1. **CI.** It re-runs on the merge head. Review threads and CI must settle before the freeze.
2. **Freeze.** The head after CI settles becomes the audit subject.
3. **Audit packet.** Grok (grok-4.5, tool-less) and AGY (gemini-4-argon-high, sandboxed), following #1482's R6 recipe, with operator gate lines.
   - The 2A diff is much larger than R6's, so the audit input needs a scoping plan: a delta summary, the key files in full, and the return records.
4. **After the audit:** signing, the ADR-MCPINT-002 amendment's acceptance, and merge. All remain operator gates.
