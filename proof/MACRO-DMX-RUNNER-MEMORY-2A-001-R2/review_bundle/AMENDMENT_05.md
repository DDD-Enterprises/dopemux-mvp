# MACRO-DMX-RUNNER-MEMORY-2A-001-R2 — Amendment 05: `make test` regression repair (W13) and the J04 test gate

**Recorded:** 2026-11-04 (UTC), by the team lead (Control Tower supervisor session), after the freeze of `4550f3ff5` was held.

**Operator words (verbatim):** "Yes, approve it"

**In answer to (verbatim):** "Approve Amendment 05?"

The message put to the operator listed three items:
1. Commit the test fix as W13: 10 test files, no production code, including `tests/mcp/test_conport_surface_contract.py`, which is outside every write surface. The team lead makes it, because the macro's correction rounds are used up.
2. Redefine J04's `make test` gate as "no new failures against main".
3. Leave one known failure in place, `test_live_catalog_files_are_untouched_by_this_packet`, and disclose it to the auditors.

## Why

The operator approved freezing `4550f3ff5` ("Yes, freeze it"). J04-FREEZE requires `make test`, which had not been run, so the team lead ran it before freezing. It failed, and 2A caused the failure. The freeze was held.

CI did not catch this: no workflow runs `tests/mcp`, and CI's unit job runs selected paths. The team lead's 2,127-test set did not catch it either, because it was a curated subset run in the services environment.

| Cause | Origin | Effect under `make test` |
|---|---|---|
| The keychain guard in `tests/conftest.py` patched by dotted string. Four older test modules run `sys.modules.pop("dopemux", None)` at collection, so the walk from the new parent cannot find `auth` | W07 / Amendment 02 | every test errored at setup |
| W05's `conftest.py` and `keychain_guard_plugin.py` used the same string paths | W05 | W05 suites errored at setup |
| `conport_mcp_stdio.py` imports `Context`; the fake `mcp.server.fastmcp` in `tests/mcp/test_conport_surface_contract.py` had only `FastMCP` | W02 | collection aborted, so nothing ran |
| That test passed two arguments to a fake of `_post_json`, which now takes three, and called the tools positionally after W12 reordered their parameters | W02, W12 | 4 tests failed once collection worked |
| That test's fakes stayed in `sys.modules`, so other suites' `pytest.importorskip("mcp.server.fastmcp")` succeeded against them | pre-existing fake, exposed by W02's tests | tests that should skip ran and failed |
| dope-memory and ConPort each ship a top-level `auth_identity.py`. W01 and W12 imported it by bare name, and older tests leave ConPort's directory on `sys.path` | W01, W02, W12 | dope-memory tests got ConPort's module |

The two `auth_identity` modules never share a process in production: each service has its own image. This is a test-process collision, not a server defect.

## Effect

**W13 (test code only; no file under `src/`, `services/` or `docker/` changes):**

| Path | Change |
|---|---|
| `tests/conftest.py` | guard patches the module object |
| `tests/unit/runner_memory_2a_r2_w05/conftest.py`, `keychain_guard_plugin.py` | patch module objects |
| `tests/unit/runner_memory_2a_r2_w01/helpers.py` | `load_dope_memory_auth_identity()` loads by file location; `pin_dope_memory_modules()` for one test |
| `tests/unit/runner_memory_2a_r2_w01/conftest.py` | autouse pin |
| `tests/unit/runner_memory_2a_r2_w01/test_auth_identity.py`, `test_rest_writes.py`, `test_mcp_writes.py` | load through the helper |
| `tests/unit/runner_memory_2a_r2_w12/test_dope_memory_defaults.py` | autouse pin |
| `tests/mcp/test_conport_surface_contract.py` | **outside every write surface, authorized here.** Adds `Context` to the fake, updates the `_post_json` fake and the four call shapes, and leaves no fake, path entry or ConPort module behind. Its assertions are unchanged |

**J04-FREEZE:** the `make test` condition now means "no new failures against main at the merged base". Main itself does not pass: `75dacb43f` gives 28 failed and 5 errors under `pytest tests`.

**One accepted failure on this branch:** `tests/mcp/test_fleet_catalog_v2_runtime.py::test_live_catalog_files_are_untouched_by_this_packet`. It asserts `mcp_catalog.yaml` is absent from `git diff origin/main...HEAD`. W07 changed that file as authorized (`codex: full-sequenced` to `full` for conport and dope-memory). The test is a packet-local check from 2026-09-04, fails on any branch touching that file, and passes once merged. It is left as is and disclosed to the auditors.

**Route:** the team lead made this repair; no child was dispatched. The macro's 4 correction rounds are spent (W04, W07, W10, W12).

## Erratum: W12_RETURN.md

`W12_RETURN.md` says of the reordered stdio tool parameters: "No code imports or calls them positionally". That is false. `tests/mcp/test_conport_surface_contract.py` called four of them positionally. They were the only positional callers in the repository; MCP clients call tools by name, so production is unaffected. The return's bytes are kept.

## Pre-commit validation

Run in a throwaway worktree at `4550f3ff5` plus this patch.

| Check | Result |
|---|---|
| Clean main `75dacb43f`, `pytest tests`, `test` extra | 7,899 passed, 28 failed, 5 errors |
| Same command, 2A with W13 | 8,833 passed, 29 failed, 3 errors |
| New failures against main | 1, the accepted catalog guard |
| Failures gone against main | 2 errors in `tests/security/test_rate_limiting.py` |
| Whole 2A set plus `tests/mcp/test_conport_surface_contract.py`, services venv | 2,131 passed, 1 deselected |

Results at the frozen head are recorded with the audit packet.

## Superseded

`4550f3ff5` is not the audit subject. The freeze moves to the head that carries W13, once CI settles.

## Still not authorized

Marking ready; signing; dispatching the audit (it needs the operator's gate lines); token issuance; migrations against a real database; the enforce switch; the ADR-MCPINT-002 amendment's acceptance; image rebuilds; the live Codex run; merge.
