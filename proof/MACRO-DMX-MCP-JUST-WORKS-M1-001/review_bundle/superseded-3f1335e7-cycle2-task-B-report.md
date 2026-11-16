# Cycle 2 Task B report: reap / lifecycle / launcher robustness

Status: **DONE_WITH_CONCERNS**. B1, B2 (per the amended ruling (b)), B3, B4 and B5 are
implemented, and each change has a test that failed before it and passes after.
Residuals (below) are known, low-impact and accepted or deferred by the controller's ruling.

Worktree: `/Users/hue/code/dopemux-mvp/.worktrees/mcp-just-works-m1`. HEAD is `e57d2b10c`, the
controller's WIP checkpoint of my B1/B3/B4 edits. Everything after it is in the working tree,
not staged and not committed: B2, formatting of my hunks, one test tidy-up, and the docs.

Files changed by this task, `git diff 0cde3a921 --numstat` (added/removed):

| File | + | - |
|---|---|---|
| `src/dopemux/mcp/reap.py` | 231 | 18 |
| `src/dopemux/mcp/launcher.py` | 80 | 1 |
| `src/dopemux/mcp/lifecycle.py` | 151 | 67 |
| `tests/unit/test_mcp_reap.py` | 369 | 4 |
| `tests/unit/test_mcp_launcher.py` | 123 | 0 |
| `tests/unit/test_mcp_lifecycle.py` | 237 | 0 |
| `docs/02-how-to/mcp-setup-other-repos.md` | 11 | 5 |
| `claudedocs/mcp-just-works-design-2026-11-05.md` | 5 | 0 (appended only) |

The deadlock demo script lives in the gitignored plan workspace:
`.superpowers/sdd/mcp-just-works-m1-plan-2026-11-05/cycle2-task-B-abba_demo.py`. There is no
scratch file in the tracked tree; `git status` shows only the 8 modified files above.

## B1. A failed state save keeps the runtime dir (codex F1): DONE

Change:
- `reap.py:836` `_release_state` now returns `List[str]`, the labelled error strings it appended
  to `report.errors` (`reap.py:870-872`).
- `reap.py:942-960`, `_reap_one`, path where every docker call succeeded: if `_release_state`
  returned any error, it calls `report.skip(cand, "state_error")` and returns. The runtime dir
  stays and nothing is appended to `reaped`. The containers are gone; registry, leases and dir
  stay for a later run, as with `registry_busy`.
- Path where some docker calls failed (`reap.py:918-938`): unchanged. It already returned
  without `rmtree` or `reaped.append`. I added a comment saying so and a test that pins it.
- `state_error` is documented wherever skip reasons are listed: the `ReapReport.skip`
  docstring, the module docstring, the `apply_reap` docstring and the how-to (B5).
  `maybe_reap`'s "not attempted" set (`cap/deadline/locked/stale`) leaves `state_error` out on
  purpose: docker calls were made, so the throttle is consumed, as with `registry_busy`.
  `mcp_commands.py` passes the reason through unchanged.

Tests in `tests/unit/test_mcp_reap.py`:
- `test_a_failed_state_save_keeps_the_runtime_dir_and_is_not_reaped` (line 1412).
  `save_states_locked` is patched to return `["boom"]`. Checks: the dir still exists,
  `reaped == []`, the one skip is `state_error`, "boom" is in `errors`, both containers were
  removed, and the registry and lease files are byte-identical. With the real save restored,
  the next run's state-only candidate finishes the job: entries stopped, dir removed.
- `test_a_failed_state_save_in_separate_registry_dirs_keeps_the_runtime_dir` (1447). Same
  result on the per-file `save_state_locked` path, with the lease file in another directory.
- `test_a_failed_state_save_after_a_partial_docker_failure_is_never_reaped` (1473). A guard on
  the partial-failure path; it passed before the change too.

RED before the change (`-k failed_state_save`):
```
E       AssertionError: assert [ReapCandidat...ope-memory'})] == []
FAILED ...::test_a_failed_state_save_keeps_the_runtime_dir_and_is_not_reaped
FAILED ...::test_a_failed_state_save_in_separate_registry_dirs_keeps_the_runtime_dir
2 failed, 1 passed, 63 deselected
```
GREEN: all 66 reap tests passed after B1.

Locks: none added or moved. `_release_state` still takes the registry lock inside the
instance lock that `_reap_one` holds.

## B2. CLI start/restart vs the reaper (codex F2): DONE per amended ruling (b)

### Finding behind the amendment

As originally ruled, `run_lifecycle` would hold the instance lock around the whole
`start`/`restart`. That deadlocks:
- A CLI start whose selection includes task-orchestrator (the default `.mcp.json` has all
  three services) would take the `:7890` reserved lock at `lifecycle.py:2120` while holding the
  instance lock: instance, then reserved.
- `switch-project` takes the reserved lock (`mcp_commands.py:477`) and then calls
  `run_lifecycle` (`:512`), which would take the instance lock: reserved, then instance.

The two orders cycle (ABBA). A real-flock model of the two lock sequences hung on both sides:
`finished: [] | still blocked: [True, True]`. The script is in the plan workspace (see top).

### What was built

- `lifecycle.py:840`: new keyword-only argument `hold_instance_lock: bool = True` on
  `run_lifecycle`, documented in the docstring.
- `lifecycle.py:1323`: `runtime_dir = runtime_dir_for_paths(...)` is computed once, before the
  op branches. `lifecycle.py:1330`: `lock_instance = hold_instance_lock and not dry_run`, so dry
  runs never lock.
- `stop` (`lifecycle.py:1333-1362`): same behaviour as before, but it now honours the flag and
  reuses `runtime_dir`. All selected services, the orchestrator included, stop under one
  instance lock. Verified that this never takes `:7890`: `_stop_services` and
  `_release_stopped_state` contain no `reserved_port_lock`; the only acquisitions in
  `lifecycle.py` are `_to_start_gate` (`:693`) and `_start_services`' orchestrator branch
  (`:2120`). Before this change `instance_lock` and `reserved_port_lock` were never held
  together anywhere: the stop branch held only the instance lock and no start path held it.
- `start` and `restart` (`lifecycle.py:1364-1465`) split the selection into two parts:
  - The **worktree part** (`worktree_part`, `:1370`) is every selected service except
    task-orchestrator. It runs under ONE `instance_lock(runtime_dir)` acquisition
    (`worktree_lock`, `:1374`).
  - The **orchestrator part** runs outside that lock.
  - When locking is off (launcher callers, dry runs), or the selection is only worktree
    services, or only the orchestrator, there is no split: `_start_services`/`_stop_services`
    is called once, as before. A worktree-only selection runs that one call under the lock;
    an orchestrator-only selection (`switch-project`, `ensure_orchestrator`,
    `--services task-orchestrator`) takes no instance lock at all.
  - **start**: the worktree `_start_services` runs under the lock, then the orchestrator
    `_start_services` runs after the lock is released.
  - **restart** (`:1424-1455`) keeps the old order, "every stop before any start; a failed stop
    starts nothing":
    1. Orchestrator `_stop_services`, before taking the lock.
    2. Under one acquisition: worktree `_stop_services`; merge the stop parts; return the merged
       stop result if it is FAIL (non-dry); then worktree `_start_services`.
    3. Orchestrator `_start_services`, after the lock is released.
  - In a split run the orchestrator `_start_services` gets `write_artifacts=False`
    (`lifecycle.py:1778`: `write_runtime_artifacts(..., dry_run=dry_run or not
    kw.get("write_artifacts", True))`). It therefore writes nothing into the runtime dir outside
    the lock and does not overwrite the compose override the worktree part wrote. Without the
    split, artifacts are written exactly as before.
- `lifecycle.py:1467` new `_merge_parts(parts, selected)`. With one part it returns that part
  unchanged. With several it builds one result:
  - service entries are ordered stably by first index in `selected`, so the order equals a
    single call's;
  - status is FAIL over PASS_WITH_WARNINGS over PASS (PLANNED if dry), which equals a single
    call's OR of `overall_fail`/`overall_unknown`;
  - exit code is the maximum of the parts;
  - blocking findings and warnings are concatenated, runtime artifacts deduplicated in order,
    and the first part's next actions kept.
- `launcher.py:502` `ensure_backend` passes `hold_instance_lock=False`, because it holds the
  instance lock at `:489` and `instance_lock` is not re-entrant. `launcher.py:590`
  `ensure_orchestrator` passes `hold_instance_lock=False` explicitly; it holds the reserved
  lock at `:577`, and an orchestrator-only start takes no instance lock anyway.
- The CLI sites in `mcp_commands.py` (not mine, unchanged) keep the default `True`.

### Caller table and the locks held at each acquisition

"Held" means the locks this process already holds when it takes the next lock.

| Call site (current HEAD + working tree) | Passes | Instance-lock acquisition | Held at that moment | `:7890` acquisitions in the call and what is held then | `launch.lock` taken twice? |
|---|---|---|---|---|---|
| CLI `start` (`mcp_commands.py:177` from `start` :222, `up --repo` :551) | default `True` | once around the worktree part (`lifecycle.py:1458`); none for an orchestrator-only selection; none if dry | nothing (preflight `_resolve_ports` registry lock and `_to_start_gate` reserved lock are released before) | preflight `_to_start_gate` (`:693`): nothing held. Orchestrator start (`:2120`): nothing held, the instance lock was released before | no |
| CLI `restart` (`mcp_commands.py:177` from `restart` :275) | default `True` | once (`lifecycle.py:1428`) covering worktree stop and start | nothing (the orchestrator stop runs before, taking only the registry lock inside `save_state_locked`, then releasing it) | preflight gate: nothing held. Orchestrator start: nothing held | no |
| CLI `stop` (`mcp_commands.py:177` from `stop` :251, `down --repo` :631) | default `True` | once (`lifecycle.py:1361`), as before | nothing | none: `_stop_services` never takes it | no |
| CLI `status` (`:698`) | default | none (returns before the branches) | n/a | none (status skips the start gate) | no |
| `switch-project`, `run_lifecycle("start", services=["task-orchestrator"])` (`mcp_commands.py:512`) | default `True` | **none**: the selection has no worktree service | n/a | already holds reserved (`:477`); the gate and `_start_services` re-enter it (re-entrant per thread) | no |
| launcher `ensure_backend` (`launcher.py:494`) | `hold_instance_lock=False` | none inside the lifecycle; the launcher's own acquisition at `launcher.py:489` happens with nothing held | n/a | none (conport or dope-memory only) | no: the lifecycle does not take it |
| launcher `ensure_orchestrator` (`launcher.py:580`) | `hold_instance_lock=False` | none | n/a | holds reserved (`:577`); the lifecycle re-enters it | no |
| launcher `launch()` attach (`launcher.py:869`) | n/a | once, for the attach record and the `instance.json` marker | nothing | none | no: released before `_run_reaper` and before `ensure_backend`'s own acquisition |
| reaper `_reap_one` (`reap.py:899`) | n/a | once per candidate (non-blocking on automatic runs) | nothing (CLI `reap`, hooks, and launcher `_run_reaper` after the attach lock is released) | none | no |

Locks nested inside an instance-lock hold: the registry lock (`locked_reload_and_save`,
`save_state_locked`) and the provision lock (ConPort tenant). Both are allowed in that order
by D7 and `locks.py`.

No path holds `launch.lock` while it takes the `:7890` lock. No path takes `launch.lock` twice
in one process. No path takes the registry lock and then the instance lock.

### Tests

`tests/unit/test_mcp_lifecycle.py` (from line 1166). They use a recording `instance_lock`, a
recording `reserved_port_lock`, and spies on `_start_services`/`_stop_services` that record
whether the instance lock is held:
- `test_worktree_start_and_restart_hold_the_instance_lock_once[start|restart]` (1247): for
  conport and dope-memory, `launch.lock` of the right runtime dir is taken exactly once. The
  parts are `[start(wt, held)]`, or for restart `[stop(wt, held), start(wt, held)]`: one
  acquisition.
- `test_the_orchestrator_part_never_runs_under_the_instance_lock[start|restart]` (1264): for
  conport, dope-memory and task-orchestrator:
  - the instance lock is taken exactly once;
  - every reserved-lock entry (preflight gate and orchestrator start) happens with the
    instance lock not held;
  - the instance lock is released before the orchestrator start, and that start's first lock
    is the reserved lock;
  - parts are `start(wt, held), start(TO, free)`, and for restart
    `stop(TO, free), stop(wt, held), start(wt, held), start(TO, free)`;
  - the compose override on disk still names conport (not overwritten by the orchestrator
    part).
- `test_no_instance_lock_without_hold_instance_lock_or_in_a_dry_run` (1300), parametrized
  over start/restart and worktree / mixed / orchestrator-only selections: `instance_lock`
  raises if called, both with `hold_instance_lock=False` and with `dry_run=True`.
- `test_an_orchestrator_only_start_takes_no_instance_lock` (1315): the `switch-project` shape.
- `test_a_split_run_returns_what_one_call_returns` (1344), 12 cases over start/restart,
  `up_rc` 0/1 (success and FAIL), and selections `[conport, dope-memory, TO]`,
  `[TO, conport]`, `[dope-memory, TO, conport]`. The split run's operation, status, exit
  code, per-service `(service, action)` order, findings, warnings, artifact names and next
  actions equal those of the unsplit single call (`hold_instance_lock=False`).
- `test_a_failed_stop_in_a_split_restart_starts_nothing` (1358): a failing `docker stop` in a
  mixed restart returns FAIL with exit 1 and runs no `up` and no wrapper, identical to the
  single-call result.
- `test_run_lifecycle_holds_the_instance_lock_by_default` (1396): the argument is
  keyword-only with default `True`.

`tests/unit/test_mcp_launcher.py`:
- `test_ensure_backend_and_orchestrator_pass_hold_instance_lock_false` (1495). The existing
  fake lifecycles already accept `**kwargs`.

RED before the change (all lifecycle tests):
```
E       TypeError: run_lifecycle() got an unexpected keyword argument 'hold_instance_lock'   (x19)
E       AssertionError: assert [] == [('instance',...h-crm-8a86'))]                            (x4)
E       KeyError: 'hold_instance_lock'
24 failed, 35 passed
```
(`test_an_orchestrator_only_start_takes_no_instance_lock` passed before the change, as it
should: it is a guard.)

Launcher RED: `E AssertionError: assert ['missing'] == [False]`, 1 failed.

GREEN: lifecycle 59 passed; launcher 43 passed; reap + launcher + lifecycle 181 passed.

### Residual (B2)

The orchestrator start is not serialized against a reap's removal of the runtime dir. The
reaper never touches orchestrator containers, registry entries or leases. A concurrent reap of
an idle worktree during a CLI orchestrator start can only fail that start, for example when
its artifact write races an `rmtree`.

An orchestrator-only start still writes `mcp.env`, the override and the plan into the runtime
dir outside the instance lock, as before. If that write follows a reap, it recreates a dir
without the `instance.json` marker, which reap never collects (Low; no containers, no ports).

## B3. Crashed launchers become idle candidates (Codex P2): DONE

Change:
- `reap.py:406` new `_effective_last_detach(runtime_dir) -> Optional[float]`:
  - returns the newer of `last_detach`'s mtime and the newest dead attach record's mtime;
  - a record counts only if its name is a positive integer and `_pid_alive(pid)` is false;
  - it never unlinks or stamps anything;
  - an unreadable `attached/` returns `None`.
- `reap.py:401` `_last_detach_age` now goes through the helper. It is used in `plan_reap`'s
  idle computation (`reap.py:625`) and in `_still_eligible` (`reap.py:381`).
- **Choice: `_still_eligible` uses the new helper**, so the check under the lock evaluates
  exactly the planning predicate. After `live_attachments(prune=True)` has stamped
  `last_detach`, both give the same value. A record whose unlink failed still agrees. A
  launcher that dies between the prune and the check counts as younger, which gives `stale`
  (the conservative direction).

Tests:
- `test_a_dead_attach_record_makes_an_idle_candidate_and_planning_writes_nothing` (1491): the
  dry run yields `idle` and leaves `attached/` and the absent `last_detach` untouched. Under the
  lock, a spy on `_still_eligible` shows the record pruned and `last_detach` stamped before the
  re-check; the candidate is reaped.
- `test_a_young_dead_attach_record_is_not_idle` (1525).
- `test_a_last_detach_newer_than_the_dead_record_wins` (1533).
- `test_effective_last_detach_reads_only_dead_numeric_records` (1544).
- `test_effective_last_detach_of_an_unreadable_attached_dir_is_none` (1566).
- Existing test changed: `test_a_stale_only_run_leaves_reap_last_untouched` (1299). Its premise
  was that planning cannot see a dead record, which B3 removes. The record is now injected
  after planning, through a wrapper on `reap.apply_reap`, so the test still checks what it was
  written for.

RED: `assert [] == ['idle']` and `AttributeError ... '_effective_last_detach'` (x3); 4 failed,
67 passed. GREEN: 71 passed.

Locks: none. The helper is read-only.

## B4. Build-only runtime dirs are reaped (acceptance finding 2): DONE

Launcher:
- `launcher.py:737` `_instance_marker_fields` builds `project_id`, `worktree_hash`,
  `worktree_root` and `project_root` with the same derivation as `runtime_dir_for`. It returns
  `None`, and nothing is written, when the identity has no project id or worktree root.
- `launcher.py:759` `_write_instance_marker`:
  - writes only when the marker is missing or a field differs;
  - writes a tmp file (`O_EXCL`, mode 0600), then `os.replace`;
  - the content is identity fields plus `written_at` only;
  - any `OSError` prints one stderr line and never refuses the launch.
- `launcher.py:869-871`: called inside the existing attach-time `instance_lock` in `launch()`.

Reap:
- `INSTANCE_MARKER` and `INSTANCE_MARKER_FIELDS` (`reap.py:129-130`).
- `_read_instance_marker` (`:438`).
- `_live_build` (`:458`), the launcher's live-build rule without importing the launcher.
  Unreadable means live (fail closed).
- `_dir_only_candidates` (`:492`), a third source called from `plan_reap` (`:694`).
- `ReapCandidate.dir_only` (`:300`). `to_dict` now also emits `state_only` and `dir_only`.
- `_still_eligible`: a dir-only candidate qualifies only while its worktree is gone and no
  build is live; never on idle.
- `_reap_one` on a dir-only candidate: the empty container list means no docker call
  (verified in the test). It releases no entries, then removes the dir.

Tests:
- Launcher: build-only refusal leaves a correct 0600 marker and a second launch does not
  rewrite it (inode and `mtime_ns` unchanged); a marker with different fields is rewritten; a
  failed write never refuses a launch.
- Reap, 8 tests:
  - a marker with a missing worktree becomes a candidate and `apply_reap` removes the dir;
  - a live build is not listed, and the same pid file past the build budget is listed;
  - a marker that does not match its dir is ignored;
  - an existing worktree is never reaped on idle;
  - no marker, a malformed marker or an unsafe hash is ignored;
  - a registry entry or container excludes the dir from this source;
  - an attached launcher excludes it;
  - the check under the lock turns a build started after planning, or a recreated idle
    worktree, into `stale`.

RED: reap 4 failed (`'ReapCandidate' object has no attribute 'dir_only'`, etc.); launcher 3
failed (`FileNotFoundError: .../instance.json`, etc.). GREEN: reap 79, launcher 42 at that
point.

Locks: no new acquisition. The marker is written under the existing attach-time instance lock,
the only lock held at that point, and the marker write takes no lock. Planning takes no lock.
`_reap_one` uses its existing acquisition (see the B2 table).

## B5. Docs: DONE (append-only, plus the requested how-to fix)

- `docs/02-how-to/mcp-setup-other-repos.md`, "Cleanup: `dopemux mcp reap`" section:
  - a `state_error` sentence appended to the paragraph about skipped instances;
  - the `instance.json` sentence appended to the last paragraph;
  - the sentence "An instance recorded by an older launcher (no `last_detach` file) is reaped
    only when its worktree path is missing" rewritten so it is true after B3: "An instance with
    neither a `last_detach` file nor a dead attach record (one recorded by an older launcher)
    is reaped only when its worktree path is missing. A launcher killed outright (SIGKILL)
    leaves a dead attach record; its time counts as the last detach, so the instance still
    goes idle, and when a later reap or full `stop` prunes it, `last_detach` takes that
    record's time."
  - Nothing else in the how-to changed.
- `claudedocs/mcp-just-works-design-2026-11-05.md`: five bullets appended at the end of
  "## Implementation amendments (2026-11-07)" (5 insertions, 0 deletions): B1; B2 (the scope
  split, why: D7 order and the ABBA deadlock with `switch-project`, and the residual); B3; B4;
  and the T7 bullet verbatim. The T7 names were verified in `native_hooks.py`:
  `dopemux:events` (:100), `native_hook_activity` (:101), `DOPEMUX_ACTIVITY_EVENT_STREAM`
  (:171), the per-session heartbeat limit, and the `DOPEMUX_NATIVE_HOOK_EVENTS_ENABLED` switch.
  `hook_status.json` is written only by the legacy `hooks/claude_code_hooks.py:98`.
- `scripts/docs_validator.py` and `scripts/docs_frontmatter_guard.py`, run with
  `.venv/bin/python`, exit 0 on both files.

## Final focused test run

```
.venv/bin/python -m pytest tests/unit/test_mcp_reap.py tests/unit/test_mcp_lifecycle.py tests/unit/test_mcp_launcher.py tests/unit/test_mcp_locks.py tests/unit/test_mcp_switch_project.py tests/unit/test_mcp_commands_lifecycle.py tests/unit/test_mcp_lifecycle_ports_from_leases.py tests/test_native_hooks_workflow.py -q -p no:cacheprovider
258 passed in 12.70s
```

Per file:

| File | Passed |
|---|---|
| reap | 79 |
| lifecycle | 59 |
| launcher | 43 |
| locks | 25 |
| switch_project | 8 |
| commands_lifecycle | 20 |
| lifecycle_ports_from_leases | 12 |
| native_hooks_workflow | 12 |

The other MCP tests that drive `run_lifecycle` (`test_mcp_commands_repo_catalog.py`,
`test_mcp_conport_tenant.py`, `test_mcp_identity_git_only.py`) also pass: 71 passed. The
baseline before any change was 136 for reap + launcher + lifecycle; it is now 181 (45 new test
cases). Not run, per the brief: the full suite and `make test-fast`.

## Formatting, lint, types

The worktree `.venv` has no black, isort or mypy. I used the main checkout's
`/Users/hue/code/dopemux-mvp/.venv/bin/` tools (black 26.3.1, isort 8.0.1, mypy 1.19.1) with
the worktree's `pyproject.toml`.
- **black/isort.** `reap.py`, `launcher.py`, `test_mcp_reap.py` and `test_mcp_launcher.py`
  were clean at `0cde3a921`, were formatted whole and are clean now.
  `lifecycle.py` and `test_mcp_lifecycle.py` were **not** black-clean at base (and
  `lifecycle.py` not isort-clean), so I did not reformat them whole. My new lifecycle code was
  hand-formatted to black style, and my test block was formatted on its own. black's remaining
  hunks are pre-existing (32 now vs 33 at base; none in new code). isort's only finding is
  pre-existing (`lifecycle.py:702`).
- **ruff** (worktree `.venv`) on the 6 Python files: 5 findings, the same 5 pre-existing F841s
  as at base, so no new ones.
- **mypy** (`--explicit-package-bases --ignore-missing-imports` on lifecycle, reap and
  launcher): 0 errors in `reap.py` and `launcher.py`. In `lifecycle.py`, the same 2 errors as
  at base (`_ports_for_service` arg-type, `names` annotation), so none added. Totals: "17
  errors in 7 files" now and on a `git archive 0cde3a921` copy with the same config.

## Self-review findings

- Every lock acquisition is listed in the B2 table. No path holds `launch.lock` while it takes
  `:7890`. `launch.lock` is taken at most once per process path. No path takes the registry
  lock and then the instance lock.
- Without a split, behaviour equals before plus the lock: a single `_start_services` or
  `_stop_services` call with the same arguments, so the launcher (`False`), dry runs,
  worktree-only and orchestrator-only selections return exactly what they returned before.
- A split run is checked against the single call for success, FAIL, reordered selections and
  a failed restart stop.
- `worktree_lock` is created once and entered at most once; creating it has no side effect
  (generator context manager).
- Planning in reap stays read-only. Fail-closed choices: an unreadable `attached/` returns
  `None`; an unreadable dir or pid file counts as a live build; a malformed or foreign marker
  is ignored; symlinked dirs are skipped.
- Secrets: the marker holds identity ids and paths only. No test prints `mcp.env`.

## Residuals and concerns

Residuals (known, low):
1. **B2:** the orchestrator start is not serialized against a reap's runtime-dir removal (see
   the B2 residual). It can only fail that start. An orchestrator-only start can recreate an
   unmarked runtime dir after a reap; reap never collects such a dir.
2. **Dir-only candidates need a readable, `OK` runtime registry.** A host whose
   `instances.json` does not exist yet gets no dir-only candidates from the CLI or from
   automatic runs. `maybe_reap` also returns early when the registry has no instances. Left
   as is.
3. **`_entry_for is None` is matched literally.** It also covers a corrupt or ambiguous pair
   (two worktree roots, one hash). Practically impossible, because the hash is derived from the
   path.

Concerns (no action requested; for the record):
4. `dopemux mcp reap --json` candidate objects gain `state_only` and `dir_only` keys. The change
   is additive; nothing compares the exact dict.
5. In a split start, `start-plan.json` lists only the worktree-scoped services; nothing reads
   the file. `mcp.env` and the compose override are identical to before.
6. Formatting and type checks used the main checkout's tools (see above).
7. Your WIP commit `e57d2b10c` holds B1, B3 and B4. Everything after it is uncommitted in the
   working tree, as instructed.

---

## Fix round 1 (review: IMPORTANT 1, MINOR 1, M2–M8)

Status of this round: **DONE_WITH_CONCERNS**. Every listed item is fixed. The new concern is
a pre-existing restart defect that needs your ruling (concern N1 below).

Base: HEAD `a59327f4d` (the previous round, committed by you). The working-tree delta is
uncommitted and unstaged:

| File | + | - |
|---|---|---|
| `src/dopemux/mcp/lifecycle.py` | 510 | 251 |
| `src/dopemux/mcp/reap.py` | 14 | 7 |
| `tests/unit/test_mcp_lifecycle.py` | 214 | 0 |
| `tests/unit/test_mcp_reap.py` | 55 | 0 |
| `docs/02-how-to/mcp-setup-other-repos.md` | 12 | 6 |
| `claudedocs/mcp-just-works-design-2026-11-05.md` | 3 | 3 (only my own amendment bullets) |

Most of the `lifecycle.py` delta is the preflight block moved verbatim into two helpers;
`git diff --color-moved=zebra` shows it as moved.

### IMPORTANT 1: facts re-taken under the instance lock (ruling (a))

- `lifecycle.py:826` `_Facts` and `lifecycle.py:836` `_mutable_facts(op, *,
  orchestrator_gate, ...)`. This is the preflight's mutable step, moved verbatim and in its
  original order:
  1. runtime registry load (+ `REGISTRY_PARSE_ERROR`);
  2. `di.inspect_running_containers`;
  3. `_resolve_ports` (+ `PORT_ALLOCATION_BLOCKED`);
  4. the task-orchestrator gate, only when `orchestrator_gate`;
  5. the start-only lease consistency check;
  6. `CATALOG_SERVICE_UNKNOWN`/`PORT_UNSET` and the task-orchestrator default port;
  7. `_collision_checks`;
  8. the blocking dedupe.

  Callers pass in the findings that do not change (identity, envrc, `.mcp.json`, doctor),
  and the helper appends to a copy, so the findings keep their original order. The gate stays
  between ports and leases, which matters because the launcher reports the first blocking
  code.
- `lifecycle.py:1080` `_blocked_result(...)` is the preflight's blocked branch, moved verbatim.
- `run_lifecycle`:
  - Container names and labels (pure functions of the identity) are now computed before the
    facts.
  - `facts_kw` (`:1335-1349`) is built once, and the preflight is
    `_mutable_facts(op, orchestrator_gate=True, **facts_kw)`. Dry runs, status, stop and the
    orchestrator part keep using these preflight values.
  - `facts_under_lock()` (`:1485`) runs `_mutable_facts(op, orchestrator_gate=False,
    **facts_kw)` with the full selection. If the fresh findings block, it returns the same
    blocked result the preflight would. Otherwise it returns the fresh
    `registry`/`docker`/`ports`.
  - It is called first thing inside `with worktree_lock:`: for start at `:1624`, for restart
    at `:1585`, before the worktree `_stop_services`. The fresh values replace the preflight
    ones for the worktree `_stop_services` and `_start_services`.
  - It runs only when the worktree lock is real. That is never for a dry run, never with
    `hold_instance_lock=False`, and never for an orchestrator-only selection.
- When nothing changed in between, the second call computes the same facts: the same docker
  snapshot, leases already allocated (so no new allocation), the same findings. The result
  therefore equals one call. `test_a_split_run_returns_what_one_call_returns` (12 cases)
  still passes. The instance lock is not taken before the preflight, so `:7890` is never held
  across a worktree start.

Test: `test_a_reap_finishing_while_the_cli_waits_for_the_lock_never_leaves_stale_state
[start|restart]` (`test_mcp_lifecycle.py:1486`). It follows the reviewer's probe:
- **World** (`_lease_world`, `:1406`): `_stop_world` with the envrc port lines removed, so
  ports come from leases, and a docker fake that a reap empties.
- **Interleaving** (`_reap_while_waiting`, `:1430`): `lc.instance_lock` is patched so that
  entering it first runs a real `reap.apply_reap` for the instance. The reap stops and removes
  both containers, releases the leases, marks entries stopped and removes the runtime dir; the
  test asserts it reaped.
- **Assertions**:
  - no `already_running`;
  - `compose up` is called twice (a real start) and the result is PASS with exit 0;
  - the lifecycle issues no `docker stop` against the gone names (for restart, the stop half
    sees them gone);
  - registry entries for conport and dope-memory are `running`, and every port variable in
    them equals an active lease of this worktree, so registry and leases are consistent.

RED, run against the pre-fix `lifecycle.py` (copied aside, swapped in, run, restored; sha1
`c039a0f0…` matches after the restore):
```
E       AssertionError: assert ('conport', 'already_running') not in [('conport', 'already_running'), ('dope-memory', 'already_running')]   (start)
E       AssertionError: assert ('conport', 'already_running') not in [('conport', 'already_running'), ('dope-memory', 'already_running')]   (restart)
```
GREEN: both pass, and the full lifecycle file passes (64).

### MINOR 1: images build before `launch.lock`

- `lifecycle.py:1858` `_ImageStep`; `lifecycle.py:1867` `_plan_image`, the probe and the
  missing/unknown findings extracted verbatim from `_start_services`; `lifecycle.py:1907`
  `_prebuild_images`.
- `run_lifecycle` (`:1521`): when the worktree lock will be taken, `_prebuild_images(inside,
  ...)` runs before it. For a restart that is also before the orchestrator stop. For each of
  conport and dope-memory that the preflight did not see running (the same skip
  `_start_services` applies), it probes and, if the image is missing, runs `compose build`
  with `build_timeout_secs()`. The build uses the build-only inputs
  (`dr.compose_build_inputs`: `compose.build.yml`, plus an empty `mcp.env` if none exists),
  which the launcher and `mcp init` already use.
- `_start_services` (`:2137`, `:2206`): a step taken before the lock is reused, with no second
  probe and no second build. Its findings (`IMAGE_MISSING_WILL_BUILD`, then `IMAGE_BUILT` or
  `IMAGE_BUILD_FAILED`) and `build_result` appear in the service entry as before. Unlocked
  runs and the orchestrator part keep the inline path unchanged.

Tests:
- `test_a_missing_image_is_built_before_the_instance_lock_is_taken[start|restart]` (`:1544`)
  records, in order, the build commands, the lock enter/exit and the `compose up` commands. It
  asserts exactly `build:conport, build:dope-memory, lock, up:conport, up:dope-memory, unlock`;
  that the entry still carries `IMAGE_MISSING_WILL_BUILD` and `IMAGE_BUILT` with a 0 exit
  code; that every build has the `build_timeout_secs()` budget; and that every build uses
  `<runtime_dir>/compose.build.yml`.
- `test_an_unlocked_start_keeps_building_inline` (`:1591`) checks that with
  `hold_instance_lock=False` the builds still run inside `_start_services`. It is a guard and
  passed before the change too.

RED against the pre-fix `lifecycle.py`: `AssertionError: assert ['lock', 'bui...ry',
'unlock'] == ['build:conpo...ry', 'unlock']` for both start and restart. GREEN: pass.

Unchanged existing tests: `test_should_build_then_up_with_budgets_when_image_missing_in_apply`
still sees conport calls in the order `inspect, build, up`, and the build-failure, unknown
presence and interpolation-env tests pass. A pre-built entry's build command names
`compose.build.yml` instead of `compose.override.yml`; no test compares it.

### Minors

- **M2.** The how-to `state_error` sentence and the design B1 bullet now say what actually
  happens. The two registries are saved one after the other with no rollback, so the one that
  saved is updated (with a corrupt lease file the entries are still marked stopped) and the
  failing one stays as it was. The runtime dir stays. A later run finishes it as a state-only
  candidate once the worktree is gone, after a person fixes a corrupt file; while the worktree
  exists, its next start rewrites the state.
- **M3.** `test_a_corrupt_lease_file_is_a_state_error_with_the_registry_still_saved`
  (`test_mcp_reap.py:1769`) uses a real corrupt `port-leases.json`. It pins the outcome:
  `state_error`; "unreadable; left as is" in the errors; both containers removed; registry
  entries `stopped`; the lease file byte-identical; the runtime dir kept. A second run with the
  file still corrupt gives `state_error` again. After the lease file is replaced with a valid
  one, a third run reaps the instance and removes the dir. It passes on the B1 code as is: it
  pins existing behaviour and is not a RED test.
- **M4.** The how-to now says: "the record's attach time (its mtime, which nothing refreshes)
  counts as the last detach".
- **M5.** The how-to `instance.json` sentence now adds that such a dir is left while a
  detached build may still be running, and that automatic runs see it only while the runtime
  registry lists at least one instance (no run sees it while that file is missing or
  unreadable).
- **M6.** New `reap.py:189` `_is_pid_text` (`text.isascii() and text.isdigit() and int(text)
  > 0`), used in `live_attachments` (`:247`, pre-existing code with the same flaw),
  `_effective_last_detach` (`:433`) and `_live_build` (`:490`).
  `test_non_ascii_digits_are_never_parsed_as_pids` (`:1797`) puts an attach record named `²`
  and a pid file containing `²` and checks the results are 0, `None` and `False`. RED:
  `ValueError: invalid literal for int() with base 10: '²'`.
- **M7.** `_dir_only_candidates` (`reap.py:527`) rejects a marker whose `worktree_root` is not
  absolute, failing closed. `test_a_marker_with_a_relative_worktree_root_is_ignored`
  (`:1809`); RED: the candidate was listed.
- **M8.** The design B4 bullet now says that under the instance lock the re-check
  re-evaluates the worktree-gone, live-attachment and live-build conditions (never idle), and
  that it does not re-check that the pair still has no registry entry or container. It also
  states the absolute-root rule.
- **Minor 1 and Important 1 docs.** One sentence added to the design B2 bullet ("Fix round 1:
  ... taken again ...; and a missing image is built before the lock is taken").

### Updated lock table (changes against the previous round)

| Step | Where | Locks held when it runs | Locks it takes |
|---|---|---|---|
| Preflight `_mutable_facts(orchestrator_gate=True)` | `run_lifecycle:1349` | caller's only: none on the CLI; reserved for `switch-project` and `ensure_orchestrator`; instance for `ensure_backend` | registry lock inside `_resolve_ports` (instance or reserved before it is D7-legal; re-entry of reserved for the orchestrator gate) |
| **Pre-build** `_prebuild_images` (new) | `run_lifecycle:1521`, CLI start/restart with a worktree part only | **none** (preflight locks released; before the instance lock; for a restart, before the orchestrator stop) | none (docker image inspect, `compose build`, writes `compose.build.yml`/`mcp.env` placeholder) |
| Restart orchestrator stop | `:1583` | none | registry lock inside `save_state_locked` |
| Instance lock (worktree part) | `:1584` restart / `:1623` start | none | `launch.lock`, exactly once |
| **Re-snapshot** `facts_under_lock` → `_mutable_facts(orchestrator_gate=False)` (new) | `:1585` / `:1624` | **instance lock** | registry lock inside `_resolve_ports` (instance → registry, D7-legal); **no `:7890`** (gate off) |
| Worktree `_stop_services` / `_start_services` | under the instance lock | instance lock | registry lock, provision lock (instance → registry/provision, D7-legal); no `:7890` (no orchestrator in this part) |
| Orchestrator `_start_services` | after the lock is released | none (CLI); reserved (`switch-project`, `ensure_orchestrator`) | reserved `:7890` (re-entrant), then registry |

No path holds `launch.lock` while it takes `:7890`. `launch.lock` is taken at most once per
process path. No path takes the registry lock and then the instance lock. The launcher rows of
the earlier table are unchanged: the launcher passes `hold_instance_lock=False`, so it never
runs the pre-build or the re-snapshot.

### Formatting, lint, types (this round)

- black (main checkout's 26.3.1, worktree config): `reap.py` and `test_mcp_reap.py` are clean.
  `lifecycle.py` has 32 black hunks, the same count as at `a59327f4d`; all are pre-existing
  lines, including the code moved verbatim, and none is in new code. My new
  `test_mcp_lifecycle.py` blocks were formatted on their own. isort is clean on the test files
  and `reap.py`.
- ruff (worktree `.venv`): the same 5 pre-existing F841s; none new.
- mypy (main checkout's 1.19.1): 0 errors in `reap.py` and `launcher.py`. `lifecycle.py` has
  the same 2 pre-existing errors; the `_ports_for_service` one moved with the code into
  `_blocked_result`. "17 errors in 7 files", unchanged.

### Tests (this round)

```
.venv/bin/python -m pytest tests/unit/test_mcp_reap.py tests/unit/test_mcp_lifecycle.py tests/unit/test_mcp_launcher.py tests/unit/test_mcp_locks.py tests/unit/test_mcp_switch_project.py tests/unit/test_mcp_commands_lifecycle.py tests/unit/test_mcp_lifecycle_ports_from_leases.py tests/test_native_hooks_workflow.py tests/unit/test_mcp_commands_repo_catalog.py -q -p no:cacheprovider
274 passed in 13.51s
```

| File | Passed |
|---|---|
| reap | 82 |
| lifecycle | 64 |
| launcher | 43 |
| commands_repo_catalog | 8 |
| (others as before) | |

Also run: `tests/unit/test_mcp_conport_tenant.py` and `tests/unit/test_mcp_identity_git_only.py`,
63 passed. Not run: the full suite.

### New finding needing a ruling

**N1. Pre-existing restart defect, present at base `0cde3a921`, not introduced by B2.**
`restart` passes ONE pre-stop docker snapshot to both halves. `_stop_services` stops the
running sidecars, then `_start_services` finds them in that same snapshot and reports
`already_running`. No `compose up` runs, and the result is PASS with the sidecars stopped.

Probe (scratch script, real lifecycle with the `_stop_world` fakes), identical with
`hold_instance_lock=False` and `True`:
```
STATUS PASS ACTIONS [('conport', 'already_running'), ('dope-memory', 'already_running')]
STOPS [['docker', 'stop', '...-conport'], ['docker', 'stop', '...-dope-memory']]
UPS 0
```
The orchestrator part of a restart has the same shape.

The fix-round re-snapshot happens before the stop, so it removes the reap-interleaving
variant (tested above) but not this one.

Proposed fix, **not implemented** because it changes restart behaviour beyond the ruling:
re-inspect docker after the stop half, inside the same instance-lock acquisition for the
worktree part and before the orchestrator start, and pass that snapshot to the starts.

### Residuals (updated)

1. **B2:** the orchestrator start is not serialized against a reap's runtime-dir removal; at
   worst that start fails. An orchestrator-only start can recreate an unmarked runtime dir
   after a reap.
2. **Dir-only candidates need a readable registry with status `OK`.** None are found when
   `instances.json` is missing; automatic runs skip planning when the registry has no
   instances.
3. **`_entry_for is None` matched literally** (a corrupt or ambiguous pair). Practically
   impossible.
4. **New:** the pre-build writes `compose.build.yml` (and an empty `mcp.env` placeholder if
   none exists) into the runtime dir outside the instance lock. A reap removing the dir at that
   moment can only make that build fail, which is reported. If a reap removed the containers
   while the run waited for the lock and the image is also missing, the build happens inline
   under the lock, because the preflight saw the sidecar running and skipped the pre-build.
5. **New:** with a pre-build, a conport whose tenant then fails to resolve under the lock has
   had its image built. Today no build would have run. The entry still lists
   `IMAGE_MISSING_WILL_BUILD` and does not mention the completed build.
6. **New:** in a split restart, a blocking finding that only the re-check under the lock sees
   returns the blocked result after the orchestrator was already stopped (its stop runs before
   the lock). This happens only in a race.
7. **M9 (noted, not fixed, per your ruling):** the review's "name-vs-content compare" and the
   duplicated `restart_stop_kw` kwargs.

---

## Fix round 2 (ruling on N1, and residual 6)

Status of this round: **DONE_WITH_CONCERNS**. N1 is fixed and residual 6 is decided and
implemented. One small residual remains (dry-run restart plans, below).

Base: HEAD `a479eb2b2` (fix round 1, committed by you). The working-tree delta is uncommitted
and unstaged: `src/dopemux/mcp/lifecycle.py` +51/-13, `tests/unit/test_mcp_lifecycle.py`
+189, `claudedocs/mcp-just-works-design-2026-11-05.md` 1/1 (one sentence added to my own B2
amendment bullet). `progress.md` at the worktree root is untracked; it is not mine and I left
it alone.

### N1: a restart starts what it just stopped

What changed:
- `lifecycle.py:1582` `docker_after_stop()` (restart branch). For a non-dry run it re-reads
  `di.inspect_running_containers(runner=docker_runner)` after the stops; a dry run reads
  nothing.
- **Worktree half:** the snapshot is taken inside the SAME instance-lock acquisition, after
  the worktree `_stop_services` succeeded and before the worktree `_start_services`. It is
  merged last: `{**start_kw, **fresh, **docker_after_stop()}`.
- **Orchestrator half:** the orchestrator start also gets a post-stop snapshot, read after the
  lock is released, right before its start.
- **Is the orchestrator half already covered by its own re-inspect under `:7890`? No.**
  `_start_services` first evaluates
  `existing = _already_running_managed(docker, cname, ...)` against the snapshot it was
  given. With the pre-stop snapshot, the stopped orchestrator still matches, so it is reported
  `already_running` and the start path (the wrapper's re-inspect and gate under `:7890`) is
  never reached. So it gets the same post-stop re-read.

Which facts are re-read, decided from the code:
- **docker:** re-read. It is the only fact the stop half invalidates.
- **ports:** kept. A restart's `_stop_services` gets no `release_state`, so
  `_release_stopped_state` does not run and the leases stand. The re-check under the lock
  already refreshed the ports for the reap case.
- **runtime registry:** not re-read. The stop half marks entries stopped on disk.
  `_start_services` uses the in-memory registry object only for `parse_status` and in-memory
  upserts, and its final write is `locked_reload_and_save`, which reloads the file under the
  registry lock and applies only this run's records.

Locks: the worktree re-read happens while the instance lock is held and takes no lock (a
`docker ps`). The orchestrator re-read happens with nothing held. Neither takes `:7890`.

Tests (`tests/unit/test_mcp_lifecycle.py`):
- `test_a_restart_of_running_sidecars_starts_them_again[hold=True|False]` (`:1667`).
  `_running_world` (`:1623`) is `_stop_world` with a docker fake that follows `docker stop`
  and `compose up`, and a port-free check that follows them too. Assertions:
  - both running sidecars are stopped, then `compose up` runs for conport and for dope-memory
    in order;
  - actions are `[("conport", "started"), ("dope-memory", "started")]`, never
    `already_running`, and the result is PASS with exit 0;
  - both containers are alive afterwards;
  - the registry entries are `running`.

  Both the locked CLI path and the unlocked single call are covered.
- `test_every_restart_start_reads_docker_after_the_stops` (`:1697`), a mixed restart. A
  wrapper around `di.inspect_running_containers` numbers every snapshot. The worktree start and
  the orchestrator start must each receive a snapshot taken after the last stop.
- `test_a_reap_finishing_while_the_cli_waits_for_the_lock_never_leaves_stale_state[restart]`
  (fix round 1) still passes.

RED, run against the fix-round-1 `lifecycle.py` (`git show a479eb2b2:...` swapped in, run,
restored; sha1 `8daa49b77baf` matches after the restore):
```
E       AssertionError: assert [] == ['conport', 'dope-memory']        (hold=True: no compose up)
E       AssertionError: assert [] == ['conport', 'dope-memory']        (hold=False)
E           AssertionError: (['conport', 'dope-memory'], [('ps', 0), ('stopped', ['task-orchestrator']), ('ps', 1), ('stopped', ['conport', 'dope-memory']), ('start', ['conport', 'dope-memory'], 1), ('start', ['task-orchestrator'], 0), ...])
E           assert 2 > 3
```
In the same run the reap-while-waiting restart test passed, as before. GREEN: all pass;
`test_mcp_lifecycle.py` 69 passed.

### Residual 6: a split restart blocked by the re-check under the lock

Decision: **restore the orchestrator and report the worktree part as blocked.**
- One call (no split) checks blocking findings before it stops anything. In a split restart the
  orchestrator half is stopped outside the lock first, and only then does the re-check under
  the lock run. If that re-check blocks, which can only happen in a race, the orchestrator
  would otherwise be left stopped.
- `lifecycle.py:1614-1636`: when the re-check blocks and the orchestrator stop part reported
  any entry `stopped`, the orchestrator is started again after the instance lock is released.
  It uses `_start_services(selected=[task-orchestrator], write_artifacts=False, ...)` with a
  post-stop docker snapshot. That start takes `:7890` with nothing held, so `launch.lock` is
  never held while `:7890` is taken.
- The result merges the blocked result (worktree services only, `blocked`, blocking findings,
  the preflight's next actions) with the orchestrator's start entry. It is FAIL with exit 1.
- If the orchestrator stop part reported nothing `stopped` (it was not running, or its stop
  failed so it presumably still runs), the plain blocked result is returned and nothing is
  started, which leaves the orchestrator as it was.
- Not changed, deliberately: when a **stop** fails (worktree or orchestrator), a restart still
  starts nothing. That is exactly one call's documented semantics ("a failed stop starts
  nothing"), so an orchestrator stopped before a failing worktree stop stays stopped there.

Test: `test_a_split_restart_blocked_under_the_lock_restores_the_orchestrator[was_running=True|False]`
(`:1759`). The orchestrator stop is faked as `stopped` or `already_stopped`, and
`_mutable_facts` is wrapped so that only the re-check under the lock adds a blocking finding.
- `was_running=True`: the parts are `stop(TO, free)` then `start(TO, free)`; the orchestrator
  start comes after `instance-released`; the TO entry is `started`; the worktree entries are
  `blocked`; FAIL, exit 1, with the blocking code reported.
- `was_running=False`: no orchestrator start, and every entry is `blocked`.

RED (round-1 code): `was_running=True` failed because no orchestrator start happened.
`was_running=False` passed before the change; it is a guard.

### Checks (this round)

- **Focused list** (brief list + `test_mcp_commands_lifecycle` + `test_mcp_switch_project` +
  `test_mcp_commands_repo_catalog`): **279 passed**. Also `test_mcp_conport_tenant` +
  `test_mcp_identity_git_only`: 63 passed. The full suite was not run.
- **black** (main checkout's 26.3.1): `lifecycle.py` has 32 hunks, equal to `a479eb2b2`, none
  in new code; the new test code was formatted on its own.
- **ruff**: the same 5 pre-existing F841s.
- **mypy**: `lifecycle.py` has the same 2 pre-existing errors; `reap.py` and `launcher.py` are
  clean; "17 errors in 7 files", unchanged.
- **Docs**: the design B2 bullet gained one "Fix round 2" sentence (the post-stop read and the
  orchestrator restore). `docs_validator` and `docs_frontmatter_guard` exit 0. The how-to is
  unchanged. Its claim that `dopemux mcp restart --services conport` recreates a container
  from a new image is now backed by an actual `compose up` after the stop; before this fix the
  restart only stopped the container.

### Residuals (additions)

8. **A dry-run restart plan still shows a running sidecar as `already_running`.** In a dry run
   nothing is stopped, so no post-stop snapshot exists and the start plan is built from the
   pre-stop snapshot, as before. A real restart now starts it. Left as is; a plan-only
   correction would have to simulate the stop's effect on the snapshot.

Residuals 1–7 from fix round 1 are unchanged, except residual 6, which this round resolves as
described above.

---

## Fix round 3 (re-review minors, last round before the freeze)

Status of this round: **DONE**. Items 1–6 and the optional initialisations are done. The
stop-path change (item 4) is contained, so it was made rather than deferred. The residuals
listed earlier are unchanged except where noted.

Base: HEAD `3f9dc74e1` (round 2, committed by you). The working-tree delta is uncommitted
and unstaged:
- `src/dopemux/mcp/lifecycle.py` +98/-41
- `tests/unit/test_mcp_lifecycle.py` +207/-11
- `claudedocs/mcp-just-works-design-2026-11-05.md` 1/1 (my own B2 bullet)

RED for every item was taken against `git show 3f9dc74e1:src/dopemux/mcp/lifecycle.py` (swapped
in, run, restored; sha1 `2e35870d4a9b` matches after the restore).

### 1. A restart pre-builds the sidecars it will stop and start again

- `_prebuild_images(..., include_running=False)` (`lifecycle.py:1985`). A start still skips
  sidecars the preflight saw running. A restart passes `include_running=op == "restart"`
  (`:1561`) and builds them too; building while the old container runs only retags the shared
  image.
- Test `test_a_restart_with_a_missing_image_builds_before_the_lock` (`test_mcp_lifecycle.py:1862`)
  covers the documented forced-rebuild flow: a running conport, its image missing until a
  `compose build` ran, then `restart --services conport`. Expected events, exactly:
  `build:conport, lock, stop, up:conport, unlock`. The entry is `started` with `IMAGE_BUILT`.
- RED: `['lock', 'sto...rt', 'unlock'] == ['build:conpo...rt', 'unlock']`, the reviewer's
  probe order. GREEN: pass.
- The design B2 bullet now qualifies "never": the build still runs under the lock when a reap
  removed the containers while the run waited and the image is also missing (residual 4).

### 2. A failed orchestrator stop is never followed by a restore

- `lifecycle.py:1656-1664`: the restore condition now also requires the orchestrator stop
  part's `status != "FAIL"`.
- `test_a_split_restart_blocked_under_the_lock_restores_the_orchestrator` (`:1759`) is now
  parametrized `was_running | not_running | stop_failed`. `stop_failed` has one entry
  `stopped`, one `failed`, and status FAIL. Expected: no orchestrator start, and every entry
  `blocked`.
- RED (`stop_failed`): the orchestrator start ran. GREEN: pass.

### 3. The orchestrator stop reads docker again after the pre-build

- The restart branch's snapshot helper was renamed `docker_now()` (`:1613`). The
  orchestrator stop of a split restart now uses `{**restart_stop_kw, **docker_now()}`
  (`:1634`), read right before that stop and after the possibly long pre-build. A dry run
  reads nothing, as before.
- The round-2 snapshot-order test only covered the starts. New test
  `test_a_split_restart_reads_docker_again_before_the_orchestrator_stop` (`:1889`) numbers
  every docker snapshot. With missing images, so a pre-build happens, the snapshot the
  orchestrator stop used must have been read after the build.
- RED: `assert 0 > 1` (the stop used the preflight snapshot, read before the build). GREEN:
  pass.

### 4. A CLI `stop` re-takes the facts under its existing lock

- Contained, about the size of the start path's call, so it is done:
  - `lifecycle.py:1474` runs `_mutable_facts(op, orchestrator_gate=False, **facts_kw)` inside
    the existing `with instance_lock(runtime_dir):`.
  - If the fresh findings contain a stop-blocking one, it returns `_blocked_result`.
    Otherwise `_stop_services` gets the fresh `registry`/`docker`/`ports`.
  - The stop-blocking rule moved out of the preflight into `_STOP_HARD_CODES` (`:1081`) and
    `_stop_blocking()` (`:1086`). Behaviour is unchanged: all findings block when one is
    hard (registry unreadable, identity unknown, docker unavailable), otherwise none. Both the
    preflight and the re-check use it.
- **Locks.** For a stop, `_resolve_ports` is called with `allocate=False` and returns before
  its `registry_lock`. The re-check therefore takes no lock: a registry read, a `docker ps`
  and a lease read. Then `_stop_services` takes the registry lock as before
  (instance → registry). No `:7890`.
- **Resulting status.** If a reap finished while the CLI `stop` waited, the stop sees nothing
  running and every entry is `already_stopped`. No `docker stop` runs. `stopped` is empty, so
  no registry save happens. The release step releases already-released leases (no-op), finds
  no live launcher and the runtime dir already gone (tolerated). The result is **PASS, exit 0**.
- Test `test_a_reap_finishing_while_a_cli_stop_waits_issues_no_stop_of_gone_names` (`:1933`)
  uses the round-1 reap replay. Its docker fake refuses `docker stop` of a gone container
  with "No such container", as real docker does. Expected: no `docker stop` call, PASS
  exit 0, every action `already_stopped`, runtime dir gone.
- RED: `assert not [['docker', 'stop', '...-conport'], ['docker', 'stop', '...-dope-memory']]`;
  with real docker that pre-fix path ends FAIL. GREEN: pass.
- The existing stop tests are unchanged and pass, including the stop-under-lock event order
  and the dry run taking no lock.

### 5. Design B2 bullet

One amendment bullet (mine) now says, in order of the bullet:
- the task-orchestrator owner gate is preflight-only and is not re-run under the lock (the
  orchestrator part never runs under it and re-checks its owner under the reserved lock);
- the pre-build covers a restart's running sidecars, with the "except" for residual 4;
- build inputs that cannot be written become `IMAGE_BUILD_FAILED`;
- a failed orchestrator stop is never followed by a restore;
- fix round 3: the orchestrator stop's re-read, and the CLI `stop` re-check with its PASS
  outcome.

`docs_validator` and `docs_frontmatter_guard` exit 0. The how-to is unchanged.

### 6. Paths that were untested

- **The start path's `return blocked` under the lock.**
  `test_a_start_blocked_under_the_lock_starts_nothing` (`:1978`), mixed start, only the
  re-check under the lock blocks. Expected: FAIL exit 1 with the blocking code; conport,
  dope-memory and the orchestrator all `blocked`; no `_start_services` call; no `up` and no
  `build`. It passed before the change too: it adds coverage of an existing path and is not a
  RED test.
- **Pre-build `OSError`.** `_prebuild_images` wraps `_plan_image` (`:2036`). An `OSError`
  from `compose_build_inputs` becomes a step with a failed `build_result` (exit 1, stderr
  "build inputs in <runtime dir> could not be written: ..."). `_start_services` reports that
  as `IMAGE_BUILD_FAILED`, action `failed`, and runs no `up` for that service. Nothing is
  raised out of `run_lifecycle` (fail closed).
  `test_a_build_input_write_failure_is_a_build_failure_not_a_crash` (`:1998`) patches
  `dr.compose_build_inputs` to raise `OSError(30, "Read-only file system")` with images
  missing. Expected: FAIL exit 1; both services `failed` with `IMAGE_BUILD_FAILED` naming the
  error; no `up` and no `build`.
- RED: `OSError: [Errno 30] Read-only file system: ...` raised out of `run_lifecycle`. GREEN:
  pass.

### Optional initialisations

- The restart branch now declares `stops: List[LifecycleResult] = []`,
  `starts: List[LifecycleResult] = []` and `stop_res: Optional[LifecycleResult] = None`
  before the lock. The dry-run plan mapping is guarded with `and stop_res is not None`; it is
  always set in a dry run.
- The stop branch's fresh facts are named `now`, so they do not shadow `fresh` (a dict) in the
  start and restart branches. mypy had flagged that.

### Lock table, changes in this round

| Step | Locks held | Locks taken |
|---|---|---|
| CLI `stop` re-check `_mutable_facts(orchestrator_gate=False)` (new) | instance lock | none (allocate off: no registry lock); then `_stop_services` takes the registry lock as before |
| Restart orchestrator stop, `docker_now()` re-read (new) | none | none (a `docker ps`), then the registry lock inside `_stop_services` |
| Restart pre-build, now also for running sidecars | none (before the lock) | none |
| Orchestrator restore start, unchanged position (after the lock) | none | reserved `:7890` (re-entrant), registry |

No path holds `launch.lock` while it takes `:7890`. `launch.lock` is taken at most once per
process path. No path takes the registry lock and then the instance lock.

### Checks (this round)

- **Focused list, as in round 2** (brief list + `test_mcp_commands_lifecycle` +
  `test_mcp_switch_project` + `test_mcp_commands_repo_catalog`): **285 passed**.
  `test_mcp_lifecycle.py` alone: 75. `test_mcp_conport_tenant` + `test_mcp_identity_git_only`:
  63 passed. The full suite was not run.
- **black** (main checkout's 26.3.1): `lifecycle.py` has 32 hunks, equal to `3f9dc74e1`, none
  in new code. The new test code was formatted on its own; isort is clean on the test file.
- **ruff**: the same 5 pre-existing F841s.
- **mypy**: `lifecycle.py` has the same 2 pre-existing errors; `reap.py` and `launcher.py` are
  clean; "17 errors in 7 files", unchanged.

### Residuals after round 3

1–3, 5, 7 and 8 are as listed before. Residual 4 is now stated in the design bullet. Residual 6
is resolved: the orchestrator is restored when it was running and its stop did not fail.

---

## Fix round 4 (IMPORTANT 1: docker re-reads fail closed; MINOR 2)

Status of this round: **DONE**. Base: HEAD `eac840c8b` (round 3, committed by you). The
working-tree delta is uncommitted and unstaged:
- `src/dopemux/mcp/lifecycle.py` +152/-51
- `tests/unit/test_mcp_lifecycle.py` +148/-1
- `claudedocs/mcp-just-works-design-2026-11-05.md` 1/1 (one "Fix round 4" sentence in my own
  B2 bullet; validator and frontmatter guard exit 0)

RED was taken against `git show eac840c8b:src/dopemux/mcp/lifecycle.py` (swapped in, run,
restored; sha1 `4169245057f5` matches after the restore).

### IMPORTANT 1: every docker snapshot re-read under or after the lock fails closed

New helpers in `lifecycle.py`:
- `_docker_unavailable_finding(snapshot, service=None)` (`:1080`) returns `[DOCKER_UNAVAILABLE
  (FAIL)]` when `snapshot.available` is False, else `[]`.
- `_docker_failed_part(op, services, findings, *, not_done, ...)` (`:1101`) returns FAIL
  (exit 1) for that part. Each service gets action `failed`, reason "docker could not be
  read; not stopped/started", the finding in `findings` and `blocking_findings`, and no
  commands.

The preflight snapshot is never used as a fallback. Where each check applies:

| Read | Where | On failure |
|---|---|---|
| CLI `stop` re-read under its lock | `:1534`, `_stop_blocking(now.blocking + _docker_unavailable_finding(now.docker))` | `DOCKER_UNAVAILABLE` is a hard stop code, so `_blocked_result`: FAIL exit 1, nothing stopped, no lease released, no registry change, runtime dir kept |
| Orchestrator read **before its stop** (split restart) | `:1709` | Nothing has been stopped yet, so the whole run is blocked as a preflight finding would block it: `_blocked_result` for every selected service (all `blocked`), FAIL exit 1. **Worktree half: blocked and untouched** (no stop, no start) |
| Worktree **post-stop** read (inside the lock, after the worktree stop) | `:1739` | The worktree half's start part is a `_docker_failed_part` (`failed`, "not started"). No `compose up` and no start from an empty snapshot. The orchestrator half then makes its own read |
| Orchestrator read **before its start** (normal path, and the residual-6 restore) | `:1775`, `:1765` | The orchestrator part is a `_docker_failed_part` (`failed`, "not started"). Never `already_running` from an unread snapshot, and no wrapper call |

The start/restart re-check under the lock (`facts_under_lock`) already failed closed: for
start/restart `_mutable_facts` adds the collision findings, which return `DOCKER_UNAVAILABLE`
for an unavailable snapshot. That is unchanged.

`docker_now(part, not_done)` now returns `({"docker": snapshot}, None)`, or
`({}, failed part)` when the read fails, or `({}, None)` in a dry run.

**Locks:** none of the new checks takes a lock. The reads are a `docker ps`; the helpers only
build results. Every acquisition is where it was in round 3: no `launch.lock` while `:7890` is
taken, `launch.lock` at most once per process path, never registry before instance.

Tests (`tests/unit/test_mcp_lifecycle.py`). `_failing_on(docker, n...)` makes the given
`docker ps` calls fail like a dead daemon (exit 1, "Cannot connect to the Docker daemon"):
- **(a)** `test_a_stop_whose_locked_docker_read_fails_releases_nothing` (`:2045`). The second
  `docker ps` (the re-read under the lock) fails. Expected: FAIL exit 1 with
  `DOCKER_UNAVAILABLE`; no `docker stop`; leases `active`; runtime dir present.
  RED: `PASS == FAIL`, the reviewer's probe.
- **(b)** `test_a_split_restart_whose_orchestrator_read_fails_touches_nothing` (`:2075`). The
  read before the orchestrator stop fails. Expected: FAIL exit 1 with `DOCKER_UNAVAILABLE`; no
  `docker stop`; no `up`; no wrapper; every entry `blocked`; exactly 2 `docker ps` calls.
  RED: `PASS == FAIL`. The old code stopped and restarted everything from an empty snapshot.
- **(c)** `test_a_restart_whose_post_stop_read_fails_starts_nothing` (`:2107`), with
  `_running_world`. The third read (after the worktree stop) fails. Expected: both
  `docker stop` calls ran (the stop half); no `compose up`; both services `failed`; FAIL exit
  1 with `DOCKER_UNAVAILABLE`. RED: `PASS == FAIL`.
- **(d)** `test_a_split_restart_whose_orchestrator_start_read_fails_fails_that_half`
  (`:2134`). The fifth read (before the orchestrator start) fails. Expected: the orchestrator
  is `failed`, not `already_running`; no wrapper call; FAIL exit 1 with `DOCKER_UNAVAILABLE`;
  exactly 5 reads. RED: `6 == 5` (the old code went on into the start and re-inspected under
  `:7890`).

GREEN: all pass.

### MINOR 2: a failed pre-build keeps the probe's finding; image name computed once

`_prebuild_images` (`:2119`ff) now works in this order:
1. Compute `image = dr.compose_image_name(...)` once, before anything that can fail later.
   An unreadable Dockerfile raises there, exactly as on the inline path; nothing in an
   `except` block can raise any more.
2. Name the planned build command from the paths `compose_build_inputs` writes
   (`<runtime_dir>/compose.build.yml`, `<runtime_dir>/mcp.env`), which writes nothing.
3. Run `_plan_image(..., image=image)` (new optional argument): the probe, plus
   `IMAGE_MISSING_WILL_BUILD`.
4. Only when the image is missing, call `compose_build_inputs`:
   - an `OSError` there sets a failed `build_result` (exit 1, "build inputs in ... could not
     be written: ...") and keeps the planned command and the probe's finding;
   - otherwise the build runs as before, with the same command.

The failed entry therefore lists the planned build command and the never-run `up` (the same
convention as an inline build failure), and its findings are `IMAGE_MISSING_WILL_BUILD`
followed by `IMAGE_BUILD_FAILED`.

Test: `test_a_build_input_write_failure_is_a_build_failure_not_a_crash` (`:1998`) is extended.
It now also checks that the first finding is `IMAGE_MISSING_WILL_BUILD`, that
`IMAGE_BUILD_FAILED` is present, that the first command names `compose.build.yml`, and that
`build_result.exit_code == 1`. RED: the finding was missing (`['CONPORT_LEG...'] ==
['IMAGE_MISSING_WILL_BUILD']`). GREEN: pass.

### Checks (this round)

- **Focused list, as in round 3**: **289 passed**. `test_mcp_lifecycle.py` alone: 79.
  `test_mcp_conport_tenant` + `test_mcp_identity_git_only`: 63 passed. The full suite was not
  run.
- **black** (main checkout's 26.3.1): `lifecycle.py` has 32 hunks, equal to `eac840c8b`, none
  in new code. The test code was formatted on its own; isort is clean.
- **ruff**: the same 5 pre-existing F841s.
- **mypy**: `lifecycle.py` has the same 2 pre-existing errors; `reap.py` and `launcher.py` are
  clean; "17 errors in 7 files", unchanged.

### Residuals after round 4

Unchanged from round 3. Two notes:
- **Not covered: the unlocked paths.** `hold_instance_lock=False` and dry runs still use the
  preflight snapshot for a `stop`. With the doctor run, which is the CLI default, its
  `DOCKER_UNAVAILABLE` already blocks there. Only `skip_doctor=True` combined with
  `hold_instance_lock=False` (no production caller) would plan from an unavailable snapshot.
- **Restart with a failed worktree post-stop read.** The orchestrator half still makes its own
  read and starts if docker answers again by then. Only the worktree half is `failed`.

---

## Final-review fix round

Status of this round: **DONE_WITH_CONCERNS**. Every code item, test and doc change is done
except one. **I did not edit the `.claude/claude.md` sentence of D2.** My operating rules do
not let an instruction relayed by another agent authorize a CLAUDE.md change, so the owner or
the controller has to apply it directly; the exact text is below.

Base: HEAD `dcd16a74b` (round 4, committed by you). The working-tree delta is uncommitted and
unstaged (`git diff --numstat`):

| File | + | - |
|---|---|---|
| `src/dopemux/mcp/lifecycle.py` | 26 | 11 |
| `src/dopemux/mcp/docker_runtime.py` | 39 | 7 |
| `src/dopemux/mcp/reap.py` | 8 | 5 |
| `src/dopemux/mcp/locks.py` | 5 | 0 |
| `src/dopemux/mcp/launcher.py` | 2 | 2 |
| `src/dopemux/commands/mcp_commands.py` | 7 | 3 |
| `tests/unit/test_mcp_lifecycle.py` | 191 | 1 |
| `tests/unit/test_mcp_reap.py` | 51 | 0 |
| `tests/unit/test_mcp_launcher.py` | 42 | 0 |
| `tests/unit/test_mcp_runtime_launcher.py` | 34 | 0 |
| `tests/unit/test_mcp_switch_project.py` | 19 | 0 |
| `docs/02-how-to/mcp-setup-other-repos.md` | 24 | 18 |
| `claudedocs/mcp-just-works-design-2026-11-05.md` | 2 | 1 |
| `AGENTS.md` | 4 | 3 |

The sealed paths were not touched. RED evidence below was taken against
`git show dcd16a74b:` copies of `lifecycle.py`, `reap.py` and `docker_runtime.py` (swapped in,
run, restored; the working-tree diff is back afterwards).

### Code

**C1: a start with no compose sidecar writes nothing into the runtime dir.**
- `lifecycle.py:2261`: `skip_artifacts = not compose_services or not kw.get("write_artifacts",
  True)`, and `write_runtime_artifacts(..., dry_run=dry_run or skip_artifacts)`. This covers
  `ensure_orchestrator`, `switch-project`, `start --services task-orchestrator` and the
  orchestrator part of a split run.
- The result's `runtime_artifacts` is `[]` when nothing was written (`:2710`). A split run's
  merged list still comes from the worktree part.
- Test: `test_an_orchestrator_only_start_leaves_the_worktree_artifacts_alone`
  (`test_mcp_lifecycle.py:2177`). Existing `compose.override.yml`, `mcp.env` and
  `start-plan.json` must be byte-identical after an orchestrator-only start.
- RED: `'# no compose services\n' == 'services:\n ..._name: ours\n'` (the probe's finding).
  GREEN: pass.
- This also removes most of residual 1: an orchestrator-only start can no longer recreate a
  runtime dir after a reap.

**C2: a blocked split restart reports the orchestrator stop that ran.**
- `lifecycle.py:1758-1774`. "A stop ran" means an entry `stopped` or `failed` in the
  orchestrator stop part; if none ran, the plain blocked result is returned (as before).
- If a stop ran and failed, or stopped nothing cleanly, the result is
  `_merge_parts([blocked worktree part, *stop parts])`. Its containers, actions and
  `docker stop` results are reported, and nothing is started.
- The clean-stop restore path is unchanged.
- Test: the `stop_failed` case of
  `test_a_split_restart_blocked_under_the_lock_restores_the_orchestrator` now expects the
  orchestrator entries `[("task-orchestrator-x", "stopped"), ("task-orchestrator-y",
  "failed")]` in order, not `blocked`.
- RED: `[('task-orche...', 'blocked')] == [...('task-orchestrator-y', 'failed')]`. GREEN: pass.

**C3: the build inputs are published atomically.**
- `docker_runtime.py:529` new `_replace_text_atomically(path, text)`:
  - writes a tmp file `.compose.build.yml.<pid>.<8 hex>.tmp` (`O_EXCL`, 0666 minus the umask,
    as `write_text` gives);
  - chmods it to the existing file's mode when there is one;
  - then calls `os.replace`, and removes the tmp file on any failure.
- `compose_build_inputs` uses it for `compose.build.yml`.
- The empty `mcp.env` placeholder is created only if missing, with one
  `os.open(O_CREAT | O_EXCL)` (`:573`). This is an atomic create that never replaces a file a
  concurrent writer has just made; a tmp+rename would clobber it.
- Test: `test_build_inputs_are_published_atomically` (`test_mcp_runtime_launcher.py:408`). It
  records `os.replace`: the override arrives via a `.compose.build.yml.*.tmp` rename, the
  placeholder is empty, a second call replaces the override again and keeps its 0640 mode, an
  existing `mcp.env` keeps its content, and no tmp file is left.
- RED: `assert ([])` (no rename at all). GREEN: pass.

**C4: an attached-only run leaves `reap.last` as it was.**
- `reap.py:1180`: the not-attempted set is now `{cap, deadline, locked, attached, stale}`. The
  module and `maybe_reap` docstrings say so.
- Test: `test_an_attached_only_run_leaves_reap_last_untouched` (`test_mcp_reap.py:1824`). A
  launcher attaches between plan and apply; the expected skip reasons are `["attached"]`, with
  no docker call and the state file absent.
- RED: `assert not True` (the throttle was consumed). GREEN: pass.

**C5: `dopemux mcp reap --help`** (`mcp_commands.py`, docstring) now says two more things. A
launcher killed outright leaves a dead attach record whose attach time counts as the detach. A
runtime dir a launcher marked (`instance.json`) that never got a sidecar is removed once its
worktree is gone and no launcher or detached image build still uses it, never for idleness. I
rendered it with `CliRunner`.

**C6:** `test_a_blocked_split_restart_whose_restore_read_fails_starts_nothing` (`:2210`)
uses the residual-6 setup with the fourth docker read (the restore's pre-start read) failing.
Expected: FAIL exit 1 with `DOCKER_UNAVAILABLE`; worktree `blocked` and orchestrator `failed`;
no start part; no wrapper. It already passed on `dcd16a74b`: it is coverage of the round-4
code, not a RED test.

### Tests the final reviewer named

- **T1** `test_switch_project_loads_the_target_checkouts_catalog`
  (`test_mcp_switch_project.py:314`). `_load_catalog` is recorded and must be called once with
  the resolved `--repo`, and the lifecycle must receive that catalog object. Coverage; it
  passed on base.
- **T2** `test_a_symlinked_runtime_dir_is_never_a_dir_only_candidate`
  (`test_mcp_reap.py:1854`). A marked dir outside the runtime root, symlinked in under the
  right name, is not listed; the same dir as a real directory is listed (control). Coverage;
  it passed on base.
- **T3** `test_the_marker_is_written_while_the_instance_lock_is_held`
  (`test_mcp_launcher.py:1518`). Spies on `instance_lock` and `_write_instance_marker` must give
  exactly `lock, marker(held=True), unlock`, and the marker must exist. Coverage; it passed on
  base.
- **T4** `test_no_deadlock_with_a_reserved_lock_holder_that_wants_launch_lock`
  (`test_mcp_lifecycle.py:2256`). Real flocks; about 0.1 s; run 6 times, stable.
  - A helper thread waits until the CLI run (in a worker thread) holds `launch.lock`, then
    takes the real `:7890` lock and asks for the same `launch.lock`. That is the old ABBA
    partner.
  - The CLI `run_lifecycle("start", ["conport", "task-orchestrator"])` runs with stubbed
    docker and compose and must finish within 5 s.
  - Asserted:
    - all three `:7890` acquisitions in the CLI thread happen with the instance lock not held
      (the preflight gate, the orchestrator start, its re-entrant owner check);
    - the order is: main acquires instance, helper acquires `:7890`, main releases instance,
      helper acquires instance;
    - the orchestrator start gets `:7890` only after the helper let go of it.
  - It passes on base. With the ruled-out whole-selection lock it would deadlock and fail on
    the 5 s join; the threads are daemons, so the test run itself never hangs.

### Docs: each changed sentence against the code

| Doc and sentence (new text, short) | Code it rests on | TRUE? |
|---|---|---|
| how-to "Current limitations": a SIGKILLed launcher counts as detached at its attach time (record mtime, never refreshed), reapable as idle 20 min after that once no other launcher is attached (D1) | `reap._effective_last_detach` reads dead records' mtime; `attach()` writes a record once and nothing re-touches it; `plan_reap` idle needs `live_attachments(prune=False) == 0` | TRUE |
| how-to (two places) and AGENTS.md: images are shared by every worktree and project that runs the same dopemux checkout, one key per checkout path and Dockerfile version; the first launch per checkout and Dockerfile version builds (D2) | `docker_runtime.image_source_key`: sha256(product root path) + Dockerfile bytes; `compose_image_name` | TRUE |
| `locks.py`: `reserved_port_lock` and `instance_lock` are never nested, neither inside the other (D3) | the B2 lock table: CLI start/restart worktree part (instance only); orchestrator part, `switch-project`, `ensure_orchestrator` (reserved only); `ensure_backend`, stop, `launch()` attach, reap (instance only, no reserved) | TRUE |
| design B2 "Why the split": never nested (`locks.py` states it, D7 does not); the lifecycle and launcher comments now cite the `locks.py` rule instead of "D7's order" (D3) | as above; the D7 text (design §5) names the two locks separately with no nesting rule | TRUE |
| how-to: a lock is held by a launcher attaching or starting, or by a CLI `start`/`restart`/`stop` (`locked`) (D4) | `launcher.launch` attach (`:869`), `ensure_backend` (`:489`); `run_lifecycle` worktree lock and stop lock; `maybe_reap` takes it with `blocking=False` | TRUE |
| how-to: a full stop also releases leases and removes the runtime dir unless a launcher is still attached (then the dir stays and the stop warns) (D5) | `_release_stopped_state`: `live_attachments > 0` gives warning `RUNTIME_DIR_KEPT_LIVE_LAUNCHERS` and no rmtree | TRUE |
| how-to re-check bullet: attached → `attached`; otherwise `stale` when the worktree is present and not idle 20 min (a launcher that came and went restarts the clock); a build-only dir is `stale` when its worktree is back or a build runs (D5) | `_reap_one`: `live_attachments(prune=True) > 0` → `attached`; `_still_eligible`: worktree gone → eligible, else idle via `_effective_last_detach`; `dir_only` → gone and no `_live_build` | TRUE |
| design B2: every docker re-read this branch adds fails closed; residual: the orchestrator branch's own re-inspect under `:7890` treats an unreadable docker as no owner and relies on the port probe (D6) | `docker_now`, the stop re-read with `_docker_unavailable_finding`; `_to_start_gate`: `if docker.available:` owner matching, else the `is_free` port probe | TRUE |
| design B2 residual: a start without a compose sidecar writes nothing into the runtime dir; the reaper never touches orchestrator containers, entries or leases (C1) | `skip_artifacts`; `plan_reap` (worktree scope only) and `_owned_by` (never the orchestrator) | TRUE |
| design amendments, new bullet: `--repo` loads the target's catalog for init/start/stop/restart/status/up/down/switch-project/repair-config and `launch --root` (`$DOPEMUX_MCP_CATALOG`, else repo-local, else bundled); deferred: `doctor --repo`, `doctor --profile --repo`, `profile show --repo` (D7) | `mcp_commands.py`: `_run_lifecycle_cli` `:172`, switch-project `:421`, init `:2175`, repair-config `:2937`, `launcher._load_catalog(launch_root)`; `_catalog_path` precedence `:904`; deferred `mcp_doctor_cmd` `:2539`, `_mcp_doctor_profile` `:2668`, `mcp_profile_show_cmd` `:2752` (all `_load_catalog()`) | TRUE |
| `reap --help` (C5) | `_effective_last_detach`; `_dir_only_candidates` with `_live_build` and the attachment check | TRUE |

**D2, not applied, `.claude/claude.md` line ~269.** Proposed replacement for the one sentence
(apply directly). Current: "Images are one per service and Dockerfile version
(`dopemux-<service>:<key>`), shared by every worktree and project: only the first launch on a
host per Dockerfile version builds (`LAUNCH_IMAGE_BUILDING`, then `/mcp reconnect all`); later
worktrees reuse them and reap never removes them." Proposed: "Images are one per service and
Dockerfile version (`dopemux-<service>:<key>`), shared by every worktree and project that runs
the same dopemux checkout (one key per checkout path and Dockerfile version): only the first
launch per checkout and Dockerfile version builds (`LAUNCH_IMAGE_BUILDING`, then `/mcp
reconnect all`); later worktrees reuse them and reap never removes them."

### Checks

- **Tests:** brief's focused list + `test_mcp_commands_lifecycle` + `test_mcp_switch_project` +
  `test_mcp_commands_repo_catalog` + `tests/unit/test_docs_no_envrc_recipe.py` +
  `tests/unit/test_mcp_runtime_launcher.py` (the `compose_build_inputs` tests, per
  `grep -rl compose_build_inputs tests/`): **339 passed**. Per file: reap 84, lifecycle 82,
  launcher 44, switch_project 9, docs_no_envrc 11, runtime_launcher 32.
  `test_mcp_conport_tenant` + `test_mcp_identity_git_only`: 63 passed. The full suite was not
  run.
- **Docs validators:**
  - how-to and design doc: `docs_validator` 0, `docs_frontmatter_guard` 0.
  - `AGENTS.md`: both exit 1 with "Missing YAML frontmatter". This is identical at
    `dcd16a74b`: AGENTS.md has never had frontmatter, so it is pre-existing and not changed
    here.
- **black/isort** (main checkout's tools): no new hunks. reap, launcher, locks and the test
  files are 0. `docker_runtime` 9 and `mcp_commands` 71 are equal to base. `lifecycle` 32 is
  equal to base. `test_mcp_lifecycle` 21 equals base (my blocks were formatted on their own).
  isort is unchanged everywhere.
- **ruff:** the same pre-existing findings (5 F841 and one F401 `dataclasses.field` in
  `docker_runtime.py`, present at base); none new.
- **mypy:** lifecycle has the same 2 pre-existing errors; reap, launcher, locks and
  docker_runtime have none; "17 errors in 7 files", unchanged.

### Residuals (as ruled, unchanged)

These stay as residuals, as you ruled:
- dead code carried over verbatim (`... or True` filters, the unreachable orchestrator
  branch, `if not is_free(...): pass`, the
  `"already_running" if not dry_run else "already_running"` expression);
- a dry-run restart still shows `already_running`;
- duplicate concurrent builds (pre-build vs the launcher's pid guard);
- launchers waiting on `launch.lock` behind long CLI holds;
- orchestrator downtime during a split restart, including the lock wait.

Earlier residuals 2, 3, 5, 7 and 8 stand. Residual 1 is reduced by C1 (an orchestrator start
no longer writes into the runtime dir). Residual 4 stays as stated in the design.

---

## Micro round (text-level, before the freeze)

Status: **DONE**. Base: HEAD `fec505f29`. Uncommitted and unstaged:
- `src/dopemux/mcp/lifecycle.py` +3/-1
- `src/dopemux/mcp/reap.py` +3/-2 (docstring only)
- `tests/unit/test_mcp_lifecycle.py` +20/-1
- `docs/02-how-to/mcp-setup-other-repos.md` +3/-2
- `claudedocs/mcp-just-works-design-2026-11-05.md` 1/1

1. **Orchestrator-only dry-run plan.** In `lifecycle.py`, the dry-run service entry's
   `runtime_files` now applies the same `skip_artifacts` rule as the real run and
   `runtime_artifacts`: `[] if skip_artifacts else list(artifact_paths.values())`.
   `test_an_orchestrator_only_start_leaves_the_worktree_artifacts_alone` now also checks that
   the real run's `runtime_artifacts == []`. It then runs `--dry-run` for the orchestrator
   alone and checks status `PLANNED`, `runtime_artifacts == []` and the one entry's
   `runtime_files == []`. The test now creates the product dir once, because `_product()` is
   not idempotent.
   RED: `assert [['/private/v...t-plan.json']] == [[]]`. GREEN: pass.
2. **How-to re-check bullet.** It now reads: "Under its lock each candidate is checked again,
   first pruning dead attach records (which can stamp `last_detach` from them); when it no
   longer qualifies there is no docker call and no other change: ...". This matches
   `_reap_one`, which calls `live_attachments(prune=True)` (unlink, plus `_stamp_last_detach`)
   before both the `attached` and the `stale` decision.
3. **Per-checkout image wording.**
   - `reap.py` module docstring: "one image per service is shared by every worktree and project
     that runs the same dopemux checkout (one key per checkout path and Dockerfile version)".
   - Design amendments, image bullet: "Every worktree and project that runs that checkout
     shares it (one key per checkout path and Dockerfile version) ... T1 holds for every later
     worktree of that checkout. The first launch per checkout and Dockerfile version still
     builds ...". Both rest on `image_source_key` (product root path plus Dockerfile bytes).

Parked by ruling and not changed: a refused orchestrator stop (entries `blocked`) is dropped
from a blocked split restart's report.

Checks:
- `tests/unit/test_mcp_lifecycle.py` + `tests/unit/test_mcp_reap.py`: **166 passed**.
- `docs_validator` and `docs_frontmatter_guard` on the how-to and the design doc: exit 0.
- black: `reap.py` 0 hunks; `lifecycle.py` 32 and `test_mcp_lifecycle.py` 21, equal to base.

The `.claude/claude.md` sentence from D2 is still yours or the owner's to apply (see the
final-review round).

---

## Task B5: state-only candidates also qualify on idle (Codex connector, `357f6ab99`)

Status: **DONE**. Base: HEAD `357f6ab99`. Uncommitted and unstaged:

| File | + | - |
|---|---|---|
| `src/dopemux/mcp/reap.py` | 52 | 25 |
| `tests/unit/test_mcp_reap.py` | 90 | 0 |
| `docs/02-how-to/mcp-setup-other-repos.md` | 6 | 5 |
| `claudedocs/mcp-just-works-design-2026-11-05.md` | 1 | 0 (appended bullet) |

### Change (`reap.py`)

- New `_plan_reason(worktree_root, runtime_dir, *, now, idle_s, exists)` (`:414`). It
  returns `worktree_missing` if the worktree is gone; otherwise `idle` once `idle_s` has passed
  since the effective last detach (`_last_detach_age`, built on `_effective_last_detach` as in
  B3); otherwise `None`. This is the container loop's former inline logic, now used by both
  loops (`:653` container loop, `:702` state-only loop).
- **State-only (registry-pair) loop.** The unconditional
  `if not _worktree_gone(...): continue` is gone. In order:
  1. `live_attachments(prune=False) > 0` → skip (kept);
  2. `_plan_reason(...)` is `None` → skip;
  3. the `unfinished` requirement (a running non-orchestrator entry, active leases, or an
     existing runtime dir) is kept unchanged;
  4. the candidate carries the computed reason (`idle` or `worktree_missing`).
- Ordering is unchanged: container candidates first, then state-only, then dir-only. Dir-only
  (marker) candidates stay `worktree_missing`-only, as ruled.
- **Under the lock.** `_still_eligible` re-evaluates both reasons for any non-dir-only
  candidate (worktree gone → eligible; else idle via `_last_detach_age`). `_reap_one` handles
  an idle state-only candidate exactly like a `worktree_missing` one: `_runtime_dir_is_ours`,
  instance lock, prune, re-check, `_stop_and_remove` over an empty `container_ids` (no docker
  call), `_release_state`, `rmtree`.
- `_owned_by` code is unchanged: a state-only candidate owns every non-orchestrator service
  and the empty service. Only its docstring changed: "(no container left; its worktree gone or
  idle)".
- The module docstring, the `plan_reap` docstring and the `registry_busy` comment now state
  the new rule.
- **Locks:** no new or moved acquisition. Planning stays read-only and lock-free; `_reap_one`
  takes the same instance lock with the registry lock inside, as before.

### Tests (`tests/unit/test_mcp_reap.py`)

Fixture `_idle_state_leftover`: a present worktree, a `running` conport entry, an active
lease, and the runtime dir with `last_detach`.
- **(a)** `test_an_idle_state_only_pair_is_planned_and_finished_while_the_worktree_exists`
  (`:1888`). `last_detach` older than `idle_s`. Planned as `(state_only, "idle", not
  dir_only)`; `apply_reap` reaps it with no docker call, the entry `stopped`, the lease
  `released` and the dir removed.
- **(b)** `test_a_recently_detached_state_only_pair_is_not_a_candidate` (`:1910`). A fresh
  `last_detach` gives no candidate.
- **(c)** `test_an_attached_state_only_pair_is_not_a_candidate` (`:1919`). A live attachment
  gives no candidate.
- **(d)** `test_a_state_error_leftover_of_an_idle_reap_is_finished_while_the_worktree_exists`
  (`:1927`), the reported scenario.
  1. An idle container reap of a present worktree whose state save fails (the `state_error`
     fixture) removes the container, keeps the entry `running` and keeps the dir.
  2. The next plan, with no containers left, yields `(state_only, "idle")`.
  3. Its apply finishes it: no docker call, entry `stopped`, lease `released`, dir removed.
- **(e)** The existing `worktree_missing` state-only and dir-only tests are unchanged and pass.

**RED/GREEN.** RED, run against `git show 357f6ab99:src/dopemux/mcp/reap.py` (swapped in,
run, restored; sha1 `db09022b144b` matches after the restore):
```
E       AssertionError: assert [] == [(True, 'idle', False)]     (a)
E       AssertionError: assert [] == [(True, 'idle')]            (d)
2 failed, 2 passed   ((b), (c) are guards and pass on both)
```
GREEN: `test_mcp_reap.py` 88 passed.

### Docs

- **How-to, reap section.** The `registry_busy` bullet and the `state_error` sentence now say
  that a later run finishes the leftover as a state-only candidate "once it has been idle 20
  minutes, or when the worktree is gone". The `state_error` one adds that a corrupt file needs
  a person first. A start of the worktree before that rewrites the state.
- **Design amendments.** One bullet is appended at the end: "State-only candidates also
  qualify on idle (Task B5, Codex connector review of `357f6ab99`)". It supersedes "a later
  run finishes it, as a state-only candidate once the worktree is gone" in the audit-2 bullet
  and the same clause in the codex F1 bullet.
- **`reap --help`.** Unchanged: it already says "its worktree no longer exists, or it has been
  idle (last launcher detached) for 20 minutes", with no state-only-specific rule.
- Both docs: `docs_validator` 0, `docs_frontmatter_guard` 0.

### Checks

- **Tests:** the brief's final focused list (reap, lifecycle, launcher, locks,
  switch_project, commands_lifecycle, ports_from_leases, native_hooks_workflow):
  **292 passed**.
- **Formatting and lint:** black and isort are clean on `reap.py` and `test_mcp_reap.py`.
  ruff: "All checks passed!". mypy: 0 errors in `reap.py` (17 elsewhere, unchanged).

### Residual (new, for a ruling if wanted; not implemented)

An idle state-only candidate whose runtime dir holds a live detached image build is not
excluded the way a dir-only candidate is: `_live_build` is applied only to dir-only
candidates. A detached build still running more than `idle_s` (20 min) after the last
launcher detached, which the default 30 min build budget allows, could have its `build.log` and
pid file removed by an idle reap of a pair that has stale state. Impact: a later launch starts
a second build. Low.

---

## Task B5 round 1: a live detached build excludes every candidate kind

Status: **DONE**. Base: HEAD `979c1eb6a`. Uncommitted and unstaged:

| File | + | - |
|---|---|---|
| `src/dopemux/mcp/reap.py` | 14 | 5 |
| `tests/unit/test_mcp_reap.py` | 57 | 0 |
| `src/dopemux/commands/mcp_commands.py` | 5 | 4 (reap help) |
| `docs/02-how-to/mcp-setup-other-repos.md` | 5 | 4 |
| `claudedocs/mcp-just-works-design-2026-11-05.md` | 1 | 0 (appended bullet) |

### Change (`reap.py`)

- **Planning.** In `plan_reap`, both registry-joined loops now skip the pair when
  `_live_build(runtime_dir, now)` is true, right after the live-attachment check: the
  container loop at `:658` and the state-only loop at `:706`. This is the dir-only scan's
  check: a `build-*.pid` whose pid is alive and that is at most `build_timeout_secs()` old.
  An unreadable runtime dir or pid file counts as live (fail closed).
- **Under the lock.** `_still_eligible` (`:404`) now returns False first when
  `_live_build(cand.runtime_dir, now)` is true, for every candidate kind. A build that started
  between plan and apply therefore leaves the candidate `stale`, with no docker call and no
  state change. Dir-only candidates keep their rule otherwise (worktree gone, never idle).
- The module docstring has a new bullet stating the rule.
- **Locks:** no new or moved acquisition. `_live_build` only reads the runtime dir.

### Tests (`tests/unit/test_mcp_reap.py`)

- **(a)** `test_an_idle_container_pair_with_a_live_build_is_not_planned` (`:1965`). An idle
  container pair is planned as `idle` (control); with a live, young `build-conport.pid` it is
  not planned.
- **(b)** `test_an_idle_state_only_pair_with_a_live_build_is_not_planned` (`:1978`). The same
  for an idle state-only pair.
- **(c)** `test_a_dead_or_stale_build_pid_does_not_block_a_reap[dead|past_the_build_budget]`
  (`:1990`). A dead pid, or a pid file older than the build budget, still lets both the
  state-only and the container pair be planned as `idle`.
- **(d)** `test_a_build_that_started_after_planning_makes_the_candidate_stale` (`:2005`). An
  idle candidate is planned, then a live build appears. `apply_reap` gives `["stale"]` with no
  docker call; the registry is still `running`; the pid file is kept.

RED, run against `git show HEAD:src/dopemux/mcp/reap.py` (swapped in, run, restored; sha1
`a7157c7d1ee2` matches after the restore): (a), (b) and (d) failed with
`assert [ReapCandidat...r_only=False)] == []`. (c) passed on both, as a guard. GREEN:
`test_mcp_reap.py` 93 passed.

### Docs

- **How-to, reap section.**
  - The rule sentence now ends "..., and never while a detached image build is running in its
    runtime dir."
  - The re-check bullet now says any candidate is skipped as `stale` while a detached image
    build is running in its runtime dir, and a build-only runtime dir also when its worktree is
    back.
- **`dopemux mcp reap --help`.** "...; never while a detached image build is running in its
  runtime dir."
- **Design amendments.** One appended bullet, "A live detached build excludes every candidate
  kind (Task B5 round 1)". It extends the dir-only exclusion from the build-only runtime dirs
  bullet to container and state-only candidates, at planning and under the lock.
- Both docs: `docs_validator` 0, `docs_frontmatter_guard` 0.

### Checks

- **Tests:** the brief's final focused list: **297 passed**.
- **Formatting and lint:**
  - black and isort are clean on `reap.py` and `test_mcp_reap.py`.
  - `mcp_commands.py` has 72 black hunks, equal to HEAD.
  - ruff: "All checks passed!" on the reap files.
  - mypy: no errors in `reap.py` (17 elsewhere, unchanged).

---

## Task B5 round 2: container check under the lock; idle needs real state

Status: **DONE**. Base: HEAD `1dfaf8829`. Uncommitted and unstaged:

| File | + | - |
|---|---|---|
| `src/dopemux/mcp/reap.py` | 64 | 7 |
| `tests/unit/test_mcp_reap.py` | 107 | 4 |
| `docs/02-how-to/mcp-setup-other-repos.md` | 3 | 1 |
| `claudedocs/mcp-just-works-design-2026-11-05.md` | 1 | 0 (appended bullet) |

### 1. A state-only or dir-only candidate checks docker under the lock

- New `_pair_may_have_containers(cand, runner, *, call_timeout, out_of_time)` (`reap.py:874`)
  runs one read-only call: `docker ps -a --filter label=dopemux.project_id=<id> --filter
  label=dopemux.worktree_hash=<hash> --format {{.ID}}`.
  - It goes through the run's `runner` with `timeout=call_timeout()`, the same bound as every
    docker call; on automatic runs that is `min(cmd_timeout_s, time left)`.
  - It returns True, which means fail closed, when any id is listed, when the call exits
    non-zero (unavailable, or `run_cmd`'s 124 timeout), when it raises, or when no time is
    left.
  - The task-orchestrator's wrapper labels carry no `dopemux.worktree_hash`
    (`task-orchestrator-http-singleton.sh:201-210`), so a running orchestrator never matches.
- `_reap_one` (`:1005`): for `cand.state_only` (which includes dir-only), after the
  attachment check and `_still_eligible`, and before `_stop_and_remove`/`_release_state`, a
  True result skips the candidate as `stale`: no state change, no rmtree. A CLI start that
  created containers and running entries between plan and lock is therefore never released
  and orphaned.
- No update timestamp was used. Registry records carry `updated_at`, but the container check
  is the required one, and it is sufficient: a start that changed the state also created
  containers.
- **Locks held at the new docker call:** the instance lock only, as for `_stop_and_remove`.
  It takes no lock itself.

### 2. Idle needs a running entry or an active lease

`plan_reap`'s state-only loop (`:731`): `unfinished` is now (a running non-orchestrator entry)
OR (active leases) OR (`state_reason == "worktree_missing"` and the runtime dir exists). A
runtime dir alone therefore qualifies only a missing worktree, as for dir-only candidates.

### Tests (`tests/unit/test_mcp_reap.py`)

- `test_a_state_only_candidate_whose_pair_got_containers_is_stale[containers_appeared|inspection_failed]`
  (`:2057`). An idle state-only candidate is planned. At apply, `docker ps -a` lists a
  container, or fails with exit 1. Expected:
  - skipped as `stale`;
  - exactly one docker call: the pair inspection, carrying both label filters;
  - that call has `timeout=3.0` from `cmd_timeout_s`;
  - registry and lease files byte-identical, runtime dir kept.
- `test_a_dir_only_candidate_whose_pair_got_containers_is_stale` (`:2084`). The same for a
  marker dir.
- `test_an_idle_state_only_pair_needs_more_than_a_runtime_dir` (`:2097`). Stopped entry,
  released lease, an existing dir, an old `last_detach` and the worktree present: not a
  candidate. With the worktree removed: a `worktree_missing` state-only candidate.
- **Updated assertions, same intent ("no container touched").** Four existing tests asserted
  `runner.calls == []` for state-only or dir-only candidates that are reaped:
  `test_state_only_candidate_finishes_a_reap_killed_after_docker_rm`, the dir-only candidate
  test, and Task B5 (a) and (d). They now assert that the only docker call is the read-only
  pair inspection.

RED, run against `git show HEAD:src/dopemux/mcp/reap.py` (swapped in, run, restored; sha1
`48b87a8529a7` matches after the restore): 4 failed. Both parametrized cases and the dir-only
case were reaped instead of `stale`; the runtime-dir-only idle pair was planned. GREEN:
`test_mcp_reap.py` 97 passed.

### Docs

- **How-to re-check bullet.** Added: "A candidate with no container left (a state-only or
  build-only one) is skipped as `stale` when `docker ps -a` lists a container for it again (a
  start since the plan) or does not answer."
  - I checked the existing "later run finishes it ... once it has been idle 20 minutes"
    sentences against the new rule. A `registry_busy` leftover keeps its running entries and
    active leases, so idle still qualifies. A `state_error` leftover keeps at least one of the
    two unless the lease file is corrupt, and that case is already worded "a corrupt file needs
    a person first". Both sentences stay true; no change.
- **Design amendments.** One appended bullet, "State-only candidates: a container check under
  the lock, and idle needs real state (Task B5 round 2)". It narrows the Task B5 bullet's
  "unfinished state (... or a runtime dir)" for idle pairs.
- **`reap.py`.** The module docstring and the `plan_reap` docstring state both rules.
- **`reap --help`.** It states no state-only condition, so it is unchanged.
- Both docs: `docs_validator` 0, `docs_frontmatter_guard` 0.

### Checks

- **Tests:** the brief's final focused list: **301 passed**.
- **Formatting and lint:** black and isort are clean on `reap.py` and `test_mcp_reap.py`.
  ruff: "All checks passed!". mypy: no errors in `reap.py` (17 elsewhere, unchanged).

---

## Task B5 micro round

Status: **DONE**. Base: HEAD `1cfa8d6e0`. Uncommitted and unstaged:

| File | + | - |
|---|---|---|
| `src/dopemux/mcp/reap.py` | 5 | 1 |
| `tests/unit/test_mcp_reap.py` | 27 | 1 |
| `docs/02-how-to/mcp-setup-other-repos.md` | 3 | 2 |
| `claudedocs/mcp-just-works-design-2026-11-05.md` | 1 | 1 (only the round-2 bullet, the last one) |

### 1. Design doc, round-2 bullet (the last bullet; older bullets untouched)

- Its filter description now reads "filtered by `dopemux.managed=true` (the planner's own
  filter) and its pair's `dopemux.project_id` and `dopemux.worktree_hash`".
- Two supersession sentences are appended to it:
  - It supersedes the build-only runtime dirs bullet's "it does not re-check that the pair
    still has no registry entry or container": under the lock a dir-only candidate now checks
    for containers.
  - It supersedes "(no docker call, state released, runtime dir removed)" in the Task B5
    bullet: an idle state-only candidate now makes one read-only `docker ps -a` before its
    state is released and its runtime dir removed.

### 2. How-to re-check bullet

It now reads "when it no longer qualifies there is no docker call that changes anything and no
other change: ...". The rest of the sentence is unchanged.

### 3. The pair check uses the planner's managed filter

- `_pair_may_have_containers` (`reap.py:899`) now also passes
  `--filter label=dopemux.managed=true` (via `dr.LABEL_MANAGED`). An unmanaged container that
  happens to carry the pair's two labels can no longer keep a state-only candidate `stale`
  forever. The docstring says so.
- The test helper `_pair_inspection` now also requires `label=dopemux.managed=true`.
- RED, with the helper tightened before the code change: the 6 tests that use the helper
  failed, plus the new test below. GREEN: all pass.

### 4. The exception path

- New `test_a_state_only_candidate_whose_pair_check_raises_is_stale`
  (`test_mcp_reap.py:2123`). The runner raises `OSError` on the pair check. Expected:
  - skipped as `stale`;
  - `report.errors == []`;
  - exactly one call, the pair inspection with all three filters;
  - registry and lease files byte-identical, runtime dir kept.
- The fail-closed `except` branch existed already; the test was RED only on the new
  managed-filter assertion.
- **No time left.** That case stays `stale`, as you ruled. It has the same throttle effect as
  `deadline`: both are in `maybe_reap`'s not-attempted set, so an automatic run that attempted
  nothing else leaves `reap.last` as it was.

### Checks

- **Tests:** `tests/unit/test_mcp_reap.py`: **98 passed**.
- **Docs validators** (how-to and design doc): `docs_validator` 0, `docs_frontmatter_guard` 0.
- **Formatting and lint:** black and isort are clean on `reap.py` and `test_mcp_reap.py`.
  ruff: "All checks passed!". mypy: no errors in `reap.py`.
- **Locks:** unchanged. The pair check still runs with only the instance lock held and takes
  none itself.

---

## Task B6: every candidate re-inspects its pair under the lock (Codex connector, `2e08a3b7c`)

Status: **DONE**. Base: HEAD `2e08a3b7c`. Uncommitted and unstaged:

| File | + | - |
|---|---|---|
| `src/dopemux/mcp/reap.py` | 44 | 24 |
| `tests/unit/test_mcp_reap.py` | 94 | 8 |
| `docs/02-how-to/mcp-setup-other-repos.md` | 4 | 3 |
| `claudedocs/mcp-just-works-design-2026-11-05.md` | 1 | 0 (appended bullet) |

### Change (`reap.py`)

- `_pair_may_have_containers` (bool) is replaced by `_pair_container_ids` (`:879`). It runs
  the same single read-only `docker ps -a` with the same three filters
  (`dopemux.managed=true`, the pair's project id and worktree hash) and the same bounds:
  - no time left gives `None` without a call;
  - the call gets `timeout=call_timeout()`;
  - a non-zero exit (including `run_cmd`'s 124 timeout) or an exception gives `None`;
  - otherwise it returns the set of listed ids.
- `_unplanned_ids(listed, planned)` (`:927`) returns the listed ids that match no planned id.
  A prefix match in either direction counts, so a 12-char plan id and a full docker id of
  the same container match; the planner truncates to 12.
- `_reap_one` (`:1033`) now runs the inspection for **every** candidate, under the instance
  lock, after the attachment check and `_still_eligible`, and before `_stop_and_remove`:
  - `None`, or any listed id the plan did not list → skip as `stale`: no stop, no state
    change, runtime dir kept. The next run plans the pair afresh.
  - Listed ids that are a subset of the plan (some or all planned containers already gone,
    no new ones) → proceed as before. `_stop_and_remove` tolerates gone ids, and releasing
    the state is correct because nothing else is alive.
  - State-only and dir-only candidates plan no ids, so any listed container makes them
    `stale`: the same as round 2, now one shared code path.
- There is one inspection per candidate.
- **Locks held at the call:** the instance lock only, as at `_stop_and_remove`. The call takes
  no lock.

### Tests (`tests/unit/test_mcp_reap.py`)

Fixture `_idle_container_world`: an idle pair planned with `a1` (conport) and `a2`
(dope-memory), plus leases and a runtime dir.
- **(a)** `test_a_replacement_container_since_the_plan_makes_the_candidate_stale` (`:2173`).
  The pair check lists `b1` (the old ids are gone). Expected: `stale`; exactly one docker
  call, the pair inspection (no stop or rm); lease and registry files byte-identical; runtime
  dir kept.
- **(b)** `test_planned_containers_partly_or_all_gone_are_still_reaped[["a1"]|["a1","a2"]|[]]`
  (`:2191`). Reaped as before: the pair check comes first, then stop and rm, the registry is
  `stopped` and the dir removed.
- `test_a_planned_id_listed_in_full_length_still_matches` (`:2209`). A full-length listed id
  matches the planned short id, and the candidate is reaped.
- **(c)** `test_a_container_candidate_whose_pair_check_fails_is_stale[1|124]` (`:2220`).
  Unavailable docker, or the timeout exit code: `stale`, one call, no state change.
- **(d)** Existing tests adjusted for the new first call, with intent unchanged:
  - the orchestrator-never-stopped test: pair check first, then exactly stop and rm;
  - the bounds/cap test: the first call is the pair check, and all calls still get
    `timeout=10.0`;
  - the deadline test: the per-call burn is 40 s instead of 60 s (3 calls now), and the
    second candidate is still skipped as `deadline`;
  - `maybe_reap`'s deadline-from-call test: burn 20 s instead of 30 s, same assertion;
  - the time-left cap test: three timeouts of 4.0 (pair check, stop, rm) instead of two.

RED, run against `git show HEAD:src/dopemux/mcp/reap.py` (swapped in, run, restored; sha1
`0c71b4c7f33b` matches after the restore): (a) and (c) failed because the candidate was
reaped. (b) failed only on "the pair check comes first". The full-id test passed on both.
GREEN: `test_mcp_reap.py` 105 passed.

### Docs

- **How-to re-check bullet.** "Before anything is stopped, one read-only `docker ps -a`
  lists the pair's containers: any candidate whose pair shows a container the plan did not
  list (a start or restart since the plan) is skipped as `stale`, and so is one whose
  `docker ps -a` does not answer."
- **Design amendments.** One appended bullet, "Every candidate re-inspects its pair under
  the lock (Task B6, Codex connector review of `2e08a3b7c`)". It supersedes the round-2
  bullet's limit of the inspection to state-only and dir-only candidates.
- **`reap.py` module docstring.** A new bullet states the rule for all candidates. The
  state-only bullet now refers to it.
- **`reap --help`.** It states no inspection rule, so it is unchanged.
- Both docs: `docs_validator` 0, `docs_frontmatter_guard` 0.

### Checks

- **Tests:** the brief's final focused list: **309 passed**. That includes the lifecycle
  reap-while-waiting tests, whose replayed reap now also makes the pair call through its fake
  runner.
- **Formatting and lint:** black and isort are clean on `reap.py` and `test_mcp_reap.py`.
  ruff: "All checks passed!". mypy: no errors in `reap.py` (17 elsewhere, unchanged).

**B6 one-liner (HEAD `556171674`).** `_pair_container_ids` (`reap.py:908`) also passes
`--filter label=dopemux.scope=worktree` (`_REAPABLE_SCOPE`), so the check matches exactly what
the planner groups, and a project-scoped container carrying the pair's labels cannot make a
candidate `stale` forever.
- `_pair_inspection` now requires the fourth filter. RED, with the helper tightened before
  the code change: 14 tests failed. GREEN: `test_mcp_reap.py` 105 passed.
- The `reap.py` docstrings and the design B6 bullet name the scope filter. Only the B6 bullet,
  the last one, was edited.
- Checks: docs validators exit 0 on both docs; black is clean; ruff "All checks passed!".
- Delta: `reap.py` +8/-5, the test file +1, the design doc 1/1. Not staged, not committed.

---

## Task B7: lease identity in reap (B7-1) and re-leasing envrc ports on start (B7-2)

Status: **DONE_WITH_CONCERNS**. Two interpretive choices in B7-2 need a yes or no from you;
both are at the end of the B7-2 subsection. Base: HEAD `71866e4d1`. Uncommitted and
unstaged:

| File | + | - |
|---|---|---|
| `src/dopemux/mcp/reap.py` | 65 | 10 |
| `src/dopemux/mcp/lifecycle.py` | 56 | 2 |
| `tests/unit/test_mcp_reap.py` | 101 | 0 |
| `tests/unit/test_mcp_lifecycle_ports_from_leases.py` | 171 | 0 |
| `tests/unit/test_mcp_lifecycle.py` | 30 | 0 (fixture) |
| `docs/02-how-to/mcp-setup-other-repos.md` | 8 | 2 |
| `claudedocs/mcp-just-works-design-2026-11-05.md` | 2 | 0 (two appended bullets) |

RED for both items was taken against `git show HEAD:` copies of `reap.py` and `lifecycle.py`
(swapped in, run, restored; sha1 `5996456c763a` and `9bcd5e8467d4` match after the restore).

### B7-1: reap matches leases by the lease registry's identity rule

- New `ReapCandidate.project_root: str = ""` (`reap.py:325`). Planning fills it from the
  registry entry (container and state-only loops) or from the marker (dir-only). `to_dict` is
  unchanged.
- New `_lease_is_the_pairs(leases, lease, *, worktree_root, project_root, worktree_hash,
  project_id)` (`:602`). It requires the same worktree root (trailing `/` ignored, as before),
  then delegates to `PortLeaseRegistry.identity_matches(...)`, the rule the allocator and the
  lifecycle's `_leased_ports` use. With the same worktree root, a different `project_id`
  (directory name vs hashed id) still matches; a different `worktree_hash` excludes.
- `_has_active_leases` (`:631`, which now also takes `project_root` and `worktree_hash`) and
  `_release_leases` (`:824`) both use it, in place of the exact `project_id` comparison. Those
  were the only lease project-id comparisons in reap.
- The scope filter (worktree), the orchestrator exclusion and `_owned_by` are unchanged.
- **Locks:** `_release_leases` still runs inside `_release_state`'s registry lock, inside the
  instance lock, as before. No new acquisition.

Tests (`tests/unit/test_mcp_reap.py`), with leases as `allocate_ports()` writes them
(`project_id` = directory name, plus `worktree_hash` and `project_root`):
- `test_an_allocator_lease_counts_and_is_released_by_identity` (`:2279`). A removed worktree
  has stopped entries and no runtime dir, so only the allocator lease keeps it alive.
  - `_has_active_leases` counts the lease, so a state-only `worktree_missing` candidate is
    planned, carrying `project_root`.
  - `apply_reap` releases the lease.
  - Another worktree's lease with the same directory-name `project_id` stays `active`.
- `test_releasing_an_allocator_lease_through_a_container_reap` (`:2300`). The same release
  and non-release through a container candidate.
- `test_the_dry_run_json_lists_a_pair_kept_alive_only_by_an_allocator_lease` (`:2318`).
  `dopemux mcp reap --json` lists the state-only candidate and changes nothing. The dry-run
  JSON has no active-lease count field, so its candidate list is the observable effect.

RED: all three failed (no candidate; lease still `active`; empty JSON candidates). GREEN: pass.

### B7-2: envrc ports are re-leased on start

`_resolve_ports` (`lifecycle.py`):
- With `allocate` and a known worktree and project root, it reads this identity's active
  leases for the leased services' variables (`_leased_ports`, a lock-free read).
- An env/envrc port counts **only when this identity's lease for that variable is on that
  very port** (`:417`). Otherwise the value is dropped from the trusted map and stays a
  preference in `existing_envrc=env` for the existing locked `allocate_ports` call:
  - this identity's existing lease for the variable wins (the allocator's reuse step);
  - with none (after `init` then `stop`), the preferred port is leased when no other lease
    holds it and `is_free_fn` says free;
  - otherwise a fresh port is leased, and the returned port replaces the envrc's.
- `allocate=False` callers (status, doctor, stop) are unchanged.
- The second `_resolve_ports` call under the instance lock (B2 fix round 1) then finds the
  lease and trusts the value, so both passes agree.
- **Own-container guard.** New `_ports_published_by_this_instance(docker, identity)`
  (`:354`) and an `alloc_is_free` wrapper (`:455`). A port this worktree's own running managed
  sidecar publishes (same `project_id` and `worktree_hash` labels) counts as free for the
  allocation, so a preferred port it holds is leased as it is rather than rebound. This covers
  a lease file lost while the sidecars run.
- **Locks:** the allocation still uses only the existing `registry_lock`, held only for the
  release/allocate-and-save step, in the same place. The new lease read and the docker scan
  take no lock.

Tests (`tests/unit/test_mcp_lifecycle_ports_from_leases.py`). `_init_then_stop` runs a real
`mcp_commands._allocate_ports` (what `init` calls), writes an envrc with those ports, then
releases every lease (what a full `stop` does).
- `test_a_start_after_init_and_stop_re_leases_the_envrc_ports` (`:524`). Expected: an active
  lease per variable equal to the envrc port, and the planned ports match it.
- `test_an_envrc_port_another_worktree_leased_is_replaced` (`:533`). Another worktree's
  active lease holds the envrc `CONPORT_MCP_PORT`. Expected: start gets a different port, our
  lease is for the new one, and the three free ports are leased exactly as the envrc names
  them.
- `test_allocate_false_still_returns_the_envrc_ports_unleased` (`:565`). Envrc ports are
  returned and no lease is written.
- `test_the_launcher_cold_start_shape_re_leases_too` (`:580`). This is the call
  `ensure_backend` makes: `run_lifecycle("start", services=["conport"],
  hold_instance_lock=False, trust_env=False)`, non-dry. Expected: the conport variables are
  re-leased at the envrc ports.
- `test_an_envrc_port_this_instances_own_container_publishes_is_adopted` (`:610`). Leases are
  gone, the ports are busy, and this worktree's own conport publishes them. Expected: they are
  leased as they are, not rebound.
- **Fixture change, intent unchanged.** `test_mcp_lifecycle.py` `_running_world` now gives
  its running sidecars active leases for the envrc ports, which is what a start leaves.
  `_stop_world`'s leases carry no `port_var`, so the restart test would otherwise have
  re-leased onto different ports.

RED: (1), (2), (4) and the own-container test failed. Before the fix (2) was blocked by
`LEASE_BELONGS_TO_OTHER_PROJECT`, and the others wrote no lease. (3) passed on both, as a
guard. GREEN: all pass.

**Interpretive choices (please confirm or rule otherwise):**
1. "Backed" means this identity holds an active lease for the variable on the same port. If
   the identity holds a lease on a different port, the envrc value is a preference and the
   existing lease wins (the allocator's reuse step). It does not re-lease the envrc port, as a
   literal reading of "create/upsert a lease with that exact port" could suggest. Reason: it
   is stable across the preflight and the re-check under the lock, and it makes the envrc
   informational. Consequence: the start's `LEASE_ENVRC_MISMATCH` check can no longer fire for
   leased services. `doctor` still reports the mismatch as a FAIL finding, but it is not in
   `BLOCKING_FINDING_CODES`.
2. The own-container guard is an addition. Without it, a lost lease file plus running sidecars
   would rebind the ports on the next start, and the registry would record ports the running
   containers do not publish.

### Docs

- **How-to.**
  - "The env file is informational": on a start (CLI or launcher), a port the file names
    counts only when this worktree holds the active lease for that port. Otherwise this
    worktree's existing lease for that variable wins. With none (for example after a `stop`)
    the port is re-leased if no other lease holds it and it is free, or replaced by a newly
    leased port when it is taken.
  - Reap safety rules: leases are matched by the worktree root, so a lease `init` or a
    launcher wrote (directory-name project id) is released like one with the hashed id.
- **Design amendments.** Two appended bullets, B7-1 and B7-2.
- Both docs: `docs_validator` 0, `docs_frontmatter_guard` 0.

### Checks

- **Tests:**
  - Brief's final focused list + `test_mcp_lifecycle_ports_from_leases.py` +
    `test_mcp_port_allocator.py`: **339 passed**.
  - `test_mcp_conport_tenant` + `test_mcp_identity_git_only` + `test_mcp_commands_repo_catalog`:
    104 passed.
  - The full suite was not run.
- **black:** clean on `reap.py`, `test_mcp_reap.py` and `test_mcp_lifecycle_ports_from_leases.py`.
  `lifecycle.py` 32 and `test_mcp_lifecycle.py` 21 hunks, equal to HEAD. isort is clean.
- **ruff:** the same 5 pre-existing F841s.
- **mypy:** `lifecycle.py` has the same 2 pre-existing errors; `reap.py` has none; "17 errors
  in 7 files", unchanged.

---

## Task B7 micro round

Status: **DONE**. Base: HEAD `9e3c78ba3`. Uncommitted and unstaged:

| File | + | - |
|---|---|---|
| `src/dopemux/mcp/lifecycle.py` | 11 | 8 |
| `tests/unit/test_mcp_lifecycle.py` | 66 | 8 |
| `tests/unit/test_mcp_lifecycle_ports_from_leases.py` | 34 | 0 |
| `tests/unit/test_mcp_reap.py` | 34 | 0 |

### 1. flake8 F811

In `_resolve_ports`, `own_or_free(port)` is now defined once. It returns
`port in own_ports or base_is_free(port)`, where `base_is_free = is_free_fn or port_is_free`.
A single annotated assignment then picks the allocator's free check:
`alloc_is_free: Optional[Callable[[int], bool]] = own_or_free if own_ports else is_free_fn`.

Behaviour is unchanged: with no own ports the allocator gets the caller's `is_free_fn`, which
may be `None`, so its own default applies, exactly as before.

`flake8 --select F,E7,E9,W6 --isolated src/dopemux/mcp/lifecycle.py` (main checkout's
flake8): 5 findings before, now **4** (the pre-existing F841s `port_map`, `catalog`, `ports`,
`doctor`).

### 2. Docstring

The first paragraph of `_resolve_ports` now starts "Order without ``allocate``: ports an
envrc/process env already names win; otherwise the active leases bound to this
project/worktree. With ``allocate`` the next paragraph decides which env ports count, and the
rest are allocated and persisted as new leases under ``registry_lock``."

### 3. Tests

- **(a)** `test_a_port_another_worktrees_container_publishes_is_not_adopted`
  (`test_mcp_lifecycle_ports_from_leases.py`). A container of the same project but another
  `worktree_hash` publishes the preferred envrc `CONPORT_MCP_PORT`, and that port is busy.
  Expected: `_resolve_ports` rebinds to a fresh port, our lease is for that port, and the
  other variables keep their envrc ports.
- **(b)** `test_a_same_root_lease_with_another_worktree_hash_is_not_the_pairs`
  (`test_mcp_reap.py`). `_lease_is_the_pairs` returns False for a same-root lease with
  `worktree_hash="ffff"` and True for the pair's own lease. A state-only reap then releases
  the pair's lease and leaves the foreign-hash one `active`.
- **(c)** `test_a_restart_of_legacy_unleased_sidecars_keeps_their_published_ports[hold=True|False]`
  (`test_mcp_lifecycle.py`), the mirror of the start test. `_running_world` gains
  `leased=False` (legacy sidecars with no lease for their envrc ports) and
  `publish_ports=True` (the docker rows publish each sidecar's envrc ports). The restart
  passes, runs `compose up` for both, leases exactly the envrc ports (3040, 3041, 4040, 3060)
  and leaves both registry entries `running`.
- **Evidence the guard is what (c) tests.** With the guard disabled in a temporary copy
  (`own_ports = set()`, restored afterwards; sha1 `f20c50eac9e3` matches), both cases of (c)
  and the existing own-container start test fail: the ports were rebound to fresh ones, for
  example `DOPE_MEMORY_PORT` 3020 instead of 3060. (a) passes either way, as it should: it
  asserts no adoption.
- (a) and (b) are coverage of the B7 code, not RED tests.

### Checks

- `tests/unit/test_mcp_lifecycle.py` + `tests/unit/test_mcp_lifecycle_ports_from_leases.py` +
  `tests/unit/test_mcp_reap.py`: **211 passed**. One run took 132 s under host load; a rerun
  took 10.6 s, and the slowest test is the existing 1.96 s registry-lock wait.
- black: clean on `test_mcp_reap.py` and `test_mcp_lifecycle_ports_from_leases.py`.
  `lifecycle.py` 32 and `test_mcp_lifecycle.py` 21 hunks, equal to HEAD.
- mypy: `lifecycle.py` has the same 2 pre-existing errors.
- Locks: unchanged.
