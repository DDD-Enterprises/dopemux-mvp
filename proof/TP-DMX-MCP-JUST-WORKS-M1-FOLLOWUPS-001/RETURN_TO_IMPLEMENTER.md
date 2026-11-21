# Return to implementer: INCOMPLETE

Packet: `TP-DMX-MCP-JUST-WORKS-M1-FOLLOWUPS-001`
Route: implementer Codex (unchanged). Written by the Claude Code supervisor session on owner instruction ("send back").
Responds to: `HANDOFF.md` (author handback `BLOCKED`).

## Verdict

`INCOMPLETE`. The working tree regresses the packet's own five-file gate against the base. Not committable, not auditable as it stands. No commit, push, PR, audit, signing or Steward action was taken by the supervisor.

## Candidate under review

| Item | Value |
|---|---|
| Worktree | `/Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1-followups` |
| Branch | `fix/mcp-just-works-m1-followups` (not pushed, no PR) |
| HEAD | `4029f6fea371df313ededcbd6f37ad0ecd90e08d` (no packet commits) |
| Base | `365f70ce2edc907d14356d82d2843104dbdaa434` (merge commit of PR #1503 on `main`; also the merge-base) |
| Working diff | 9 files, +755 / -75, uncommitted, nothing staged |
| `git diff` SHA-256 | `f3d523e012cda019b2bedb8e46cfefa8560436adef62d38d69aba736822a51ee` |

## Gate results (supervisor-run, 2026-11-15/16)

Command, run from the worktree root with the repo venv:

```
/Users/hue/code/dopemux-mvp/.venv/bin/python -m pytest -q --no-cov -p no:cacheprovider \
  tests/unit/test_mcp_lifecycle.py \
  tests/unit/test_mcp_lifecycle_ports_from_leases.py \
  tests/unit/test_mcp_launcher.py \
  tests/unit/test_mcp_reap.py \
  tests/unit/test_mcp_stdio_proxy.py
```

| Gate | Base `365f70ce` | Candidate working tree |
|---|---|---|
| Five touched test files | PASS: 311 passed | **FAIL: 15 failed, 343 passed** |
| `ruff check` `launcher.py` | 0 findings | **1 finding (new)** |
| `ruff check` `lifecycle.py` | 4 findings (F841) | 4 findings (F841), unchanged count |
| `ruff check` `reap.py`, `stdio_proxy.py`, `port_allocator.py` | clean | clean |
| `make test-fast` | not run | NOT_RUN (five-file gate fails first) |
| Independent audit (S9) | n/a | NOT_RUN (no frozen head) |

The base figure was measured on an export of the base tree for the same five files. Ruff was run with `--no-cache`, which avoids the cache-write denial recorded in `RUFF_DENIAL.txt`.

## The 15 failing tests

All 15 test functions are defined at the base commit and pass there. They are not new packet tests.

### `tests/unit/test_mcp_reap.py` (5)

- `test_a_marked_dir_with_a_live_build_is_not_a_candidate`
- `test_a_dir_only_candidate_is_rechecked_under_the_lock`
- `test_an_idle_container_pair_with_a_live_build_is_not_planned`
- `test_an_idle_state_only_pair_with_a_live_build_is_not_planned`
- `test_a_build_that_started_after_planning_makes_the_candidate_stale`

Observed: a directory or idle pair with a live build is returned as a reap candidate (the candidate list is non-empty where the test expects `[]`).

### `tests/unit/test_mcp_launcher.py` (5)

- `test_ensure_backend_image_missing_spawns_build_and_exits`
- `test_second_launch_during_a_live_build_spawns_nothing`
- `test_a_stale_build_pid_file_is_replaced`
- `test_one_services_build_never_blocks_the_others`
- `test_a_build_only_launch_leaves_the_instance_marker`

Observed: a second launch during a live build spawns a second build (`assert 2 == 1`), which is the stacking item C exists to prevent. The build PID file content changed from a bare PID to a JSON object carrying an `"unverified"` identity, and tests that read the bare PID reject it.

### `tests/unit/test_mcp_lifecycle_ports_from_leases.py` (5 cases, 4 functions)

- `test_start_heals_colliding_lease_instead_of_port_collision[True]`
- `test_start_heals_colliding_lease_instead_of_port_collision[False]`
- `test_two_retained_leases_on_one_port_block`
- `test_a_retained_lease_on_the_reserved_orchestrator_port_blocks`
- `test_a_same_project_container_without_hash_or_scope_and_foreign_workspace_blocks`

Observed: `PLANNED` and `BLOCKED` outcomes are swapped in several cases, and some cases now surface `LEASE_ENVRC_MISMATCH`.

## New ruff finding

```
src/dopemux/mcp/launcher.py:54:5: F401 [*] `.reap._pid_alive` imported but unused
```

The unused import suggests the launcher's liveness check was meant to call `_pid_alive` and does not. Treat that as a lead, not a diagnosis.

## Supervisor hypothesis (unconfirmed)

The reap and launcher groups look like one shared cause: a build PID with no recorded or verifiable identity is no longer counted as live. That reading comes from the assertion messages only. The supervisor did not trace it in the code, and did not diagnose the lifecycle group at all.

### Addendum: what the launcher diff shows (read from the diff, not proven by a run)

In `src/dopemux/mcp/launcher.py`, base `_live_build_pid` read the PID file as a bare integer and returned it when `_pid_alive(pid)` held and the file was inside the build budget. The candidate instead:

- parses the file as JSON and rejects anything that is not a dict with an integer `"pid"`. A base-format file (`"1234\n"`) parses as a JSON integer, so it is rejected;
- requires the record to equal `_build_process_identity(pid)`, which returns an identity only when the process is its own process-group leader (`os.getpgid(pid) == pid`) with a positive create time;
- in `_write_build_pid`, writes `{"pid": pid, "identity": "unverified"}` when no identity is available. That record can never equal a later identity lookup, so a build written this way is never seen as live.

So a build whose process is not a group leader, and any old-format PID file, both read as "no live build". This matches the launcher failures and the now-unused `_pid_alive` import. `reap.py` has its own `_build_process_identity` (line 504); the supervisor did not read how reap uses it, and did not look at the lifecycle group.

## Required before the next handback

1. The five-file command above passes in full on the candidate, with no test deselected.
2. Each of the 15 tests either passes unmodified, or its change is justified individually in `TEST_ASSERTION_MAPPING.json` with the old and new assertion and the packet item that requires it. A base test that guards against reaping or double-building during a live build must not be weakened to pass.
3. Old-format (bare PID) build PID files have a defined, tested behaviour. Reading one must not be treated as "no live build".
4. `ruff check --no-cache` shows no new findings versus base on the five source files (`launcher.py` back to 0; `lifecycle.py` not above 4).
5. `make test-fast` is run and its result recorded, or the exact blocker is recorded.
6. The handback states full-gate numbers. A selected-case count (the 57 "safe cases") is supporting evidence only and does not stand in for the gate.

## Not changed by this note

`HANDOFF.md`, `PROOF.json`, `PROOF_HASHES.json` and every other file in this directory are untouched, so the recorded hashes remain valid. This file is the only addition and is not covered by `PROOF_HASHES.json`.
