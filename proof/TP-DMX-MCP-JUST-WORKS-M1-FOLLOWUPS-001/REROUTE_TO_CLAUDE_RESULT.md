# Reroute result: gates pass in the working tree, nothing committed

Packet: `TP-DMX-MCP-JUST-WORKS-M1-FOLLOWUPS-001`
Supersedes: `RETURN_TO_IMPLEMENTER.md` (status there was INCOMPLETE, 15 failing tests).
Author of this note and of the changes it describes: the Claude Code supervisor session, on the owner's instruction to take the fix in this worktree instead of sending it back to Codex.

## Status

The candidate now passes the packet's local gates. It is uncommitted, unpushed and unaudited. No PR, signing, merge or Steward action was taken.

| Item | Value |
|---|---|
| Worktree | `/Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1-followups` |
| HEAD | `4029f6fea371df313ededcbd6f37ad0ecd90e08d` (packet commit only) |
| Base | `365f70ce2edc907d14356d82d2843104dbdaa434` |
| Staged files | 0 |
| `git diff <base> -- src tests claudedocs` SHA-256 | `e2f0f183e9d066b6cf941a17c88fe19836cc955f194281a35db45a5653f67045` |
| Codex hand-back snapshot | `WORKING_DIFF_AT_REROUTE_TO_CLAUDE.patch`, SHA-256 `f3d523e012cda019b2bedb8e46cfefa8560436adef62d38d69aba736822a51ee` |

## Gate results

All run from the worktree root with `/Users/hue/code/dopemux-mvp/.venv/bin/python`, after the last edit unless stated.

| Gate | Result |
|---|---|
| Five touched test files (`-q --no-cov -p no:cacheprovider`) | 358 passed, 0 failed |
| Full unit suite, `tests/unit` | 4512 passed, 29 skipped, 0 failed |
| mypy on the five packet source files | 367 errors in 33 files, the same error set as the base |
| ruff on the five source files and five test files | 5 findings, all F841, all present on the base: four in `lifecycle.py`, one in `tests/unit/test_mcp_lifecycle.py` (a file this candidate does not modify) |
| flake8 on the five source files | 652 findings against 659 on the base: a net −7, all E501. No other error code changed. No line this candidate adds is over 79 columns |
| Changes outside the packet allowlist | none |

The flake8 increase reported in the first version of this note (671 against 659) is cleared. The 19 over-length lines the candidate added were wrapped, 16 from the Codex snapshot and 3 from this session. The repo has no flake8 configuration, so the tool runs at its 79-column default. Per file, base to now: `lifecycle.py` 269 to 268, `launcher.py` 89 to 87, `reap.py` 187 to 183, `stdio_proxy.py` 62 to 62, `port_allocator.py` 52 to 52.

Not run: `make test-fast`, the independent audit, and any real `dopemux mcp start` against Docker.

## What this session changed on top of the Codex snapshot

Seven files, 177 insertions and 42 deletions.

### Source

`src/dopemux/mcp/lifecycle.py` (+26 −5). This holds the only behaviour change; the rest of its delta is line wrapping.

- `_resolve_ports` takes a new optional `planned` list. On a dry run that allocates, the in-memory registry (stale leases released, planned leases added) is appended to it.
- `_mutable_facts` passes that list in and checks the lease/envrc consistency against the planned registry when there is one, instead of reloading the file. Before this, a dry run compared its planned ports with the untouched lease file and reported `LEASE_ENVRC_MISMATCH` or swapped `PLANNED` and `BLOCKED`. That accounted for the five lifecycle failures.
- Two `not allocate` branches were removed. They sat after the early `if not allocate: ... return ports` exit and could not run; mypy flagged them as unreachable.

`src/dopemux/mcp/launcher.py` (+15 −9): removed the unused `_pid_alive` import (the ruff F401 from the hand-back), annotated `pid: int`, added the psutil ignore comment, and wrapped long lines.

`src/dopemux/mcp/reap.py` (+6 −4): psutil ignore comment and line wrapping.

`src/dopemux/mcp/stdio_proxy.py` (+25 −12): line wrapping only.

The wrapping is meant to change no behaviour. Three spots are more than a re-flow and are worth a glance in review:

- `_build_process_identity`, in both `launcher.py` and `reap.py`: `if not running or zombie` became two consecutive `if` statements, in the same order.
- `stdio_proxy.py` `forward`: the `CancelledNotificationParams` object is now built on its own line, still inside the same `try` under the shielded scope.
- `lifecycle.py` `_mutable_facts`: the conditional expression that picks the planned registry became an `if`/`else`.

The ignore comments exist because `types-psutil` is not a declared dependency and the repo runs mypy with `warn_unused_ignores`. If the stubs are ever added, both comments will be reported as unused and should be deleted.

### Tests

`tests/unit/test_mcp_launcher.py` (+44 −5) and `tests/unit/test_mcp_reap.py` (+50 −7):

- Tests that used the test process's own PID as "a live build" wrote it in the old bare-PID form. The candidate treats that form as unverifiable, so those tests now write a full identity record. This accounted for the ten launcher and reap failures.
- An autouse `_real_psutil` fixture restores the real module. `tests/unit/test_health.py` leaves a `MagicMock` in `sys.modules["psutil"]`, which made `except psutil.Error` raise `TypeError` in the full suite only.

`tests/unit/test_mcp_lifecycle_ports_from_leases.py` (+11):

- The `_leased_start` helper now makes a real allocation before its dry-run start. A dry run no longer persists leases, so the tests that retarget a lease had nothing in the file to retarget.
- `test_an_envrc_port_another_worktree_leased_is_replaced` gained an assertion that the dry-run plan matches the ports the real allocation then leases.

## One test expectation was replaced, not repaired

`test_a_dead_or_stale_build_pid_does_not_block_a_reap` in `tests/unit/test_mcp_reap.py` had a `past_the_build_budget` case on the base: a live build older than `DOPEMUX_MCP_BUILD_TIMEOUT_SECS` did not block a reap. The packet's fix C reverses that rule (age alone never proves a build stopped; the launcher terminates it), so the case is now `legacy_one_line`. The reversed behaviour is asserted in `test_a_marked_dir_with_a_live_build_is_not_a_candidate`. The auditor should confirm this reversal is what the packet intends.

## Stale records in this directory

`HANDOFF.md`, `PROOF.json`, `PROOF_HASHES.json`, `WORKING_DIFF.patch` and the other Codex-written files are unchanged. They describe the tree as Codex handed it back (status BLOCKED) and their recorded diff hash no longer matches the working tree. They need regenerating, or an explicit supersession, before this candidate goes to audit.

## Authorship

The candidate is now mixed: Codex wrote the bulk (its `HANDOFF.md` records the requested model as `gpt-6.1-sol/high`, provider-attested model unknown), and the Claude supervisor session wrote the delta above. The packet's binding named Codex as the sole implementer, so the supervisor is no longer independent of this diff and should not be counted as its reviewer.

## Addendum, 2026-11-20: committed, merged with main, proof regenerated

Everything above describes the working tree before it was committed. Since then:

- The candidate was committed as `ec3430c6328894b997a5c8b9d2de6ff107d59d89`, with a follow-up `54ec77f76a88b19c7f23de6338338237ff61e1b2` that adds frontmatter to the packet companion, and opened as draft PR #1521.
- `origin/main` (`ba5c3e07b01ad46cae0d55cefdfbb9f9b3b647d7`) was merged in as `29fb004ee174c27ff6358ba9d0052b9667050594`. Main had not touched any of the five source files, so the base lint and type figures still apply.
- On the merged tree: the five touched test files give 358 passed; `make test-fast` gives 4532 passed, 29 skipped; ruff, flake8 and mypy counts on the five source files are no worse than base. The figures are in `PROOF.json`.
- `WORKING_DIFF_AT_REROUTE_TO_CLAUDE.patch` was byte-identical to `WORKING_DIFF.patch` (SHA-256 `f3d523e012cda019b2bedb8e46cfefa8560436adef62d38d69aba736822a51ee`) and was removed as a duplicate. Read references to it above as `WORKING_DIFF.patch`.
- Codex's hand-back records are kept unchanged under new names: `PROOF_CODEX_HANDBACK.json` and `PROOF_HASHES_CODEX_HANDBACK.json`. The second lists hashes for the hand-back file set, including the old `PROOF.json` and this note before the addendum, so those two entries no longer match.
- The independent audit has not run yet. `PROOF.json` records it as pending.
