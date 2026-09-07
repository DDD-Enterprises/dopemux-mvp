# Mutation Evidence — TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-002

Isolated anti-vacuity mutation per packet §4/§9.

## Procedure (single mutation, reset-isolated)

1. `IMPLEMENTATION_HEAD=d1b6539f446085992e1e5e9e9535d51b429c4d9a` — verified clean tree
   (`git status --porcelain` empty, `git diff` empty) before mutating.
2. Applied exactly one named, reversible mutation to
   `src/dopemux/dcp/red_lane_scanner.py`: neutered `_has_control_chars()` to
   unconditionally `return False`, via `sed` targeting the function's single
   `return` statement.
3. Landed change count asserted non-zero: 1 line changed (`git diff
   --unified=0` showed 1 removed / 1 added line under `return`).
4. Ran the full 13-probe regression matrix from §3.2 to completion — every
   probe's status and finding categories were collected before any single
   expectation was evaluated (no early abort).
5. Restored the clean implementation head via `git checkout --
   src/dopemux/dcp/red_lane_scanner.py`; verified `git status --porcelain`
   empty and `HEAD` unchanged afterward; re-ran the primary probe
   (`scripts/dopetask\n`) post-restore and confirmed `Status.BLOCKED` again.

`red_lane_rules.py` was not part of this mutation (it is read-only and
unmutated for this packet), so there was only one mutation to isolate.

## Per-probe results (all 13, collected before any assertion)

| probe_class | probe (repr) | expected_status | actual_status | finding_categories |
|---|---|---|---|---|
| exact_match | `'scripts/dopetask\n'` | UNKNOWN | UNKNOWN | [] |
| exact_match | `'scripts/taskx\r'` | UNKNOWN | UNKNOWN | [] |
| exact_match | `'scripts/batch_resolve_and_merge.py\t'` | UNKNOWN | UNKNOWN | [] |
| exact_match | `'src/dopemux_pr_merge_specialist/queue_drain.py\x7f'` | UNKNOWN | UNKNOWN | [] |
| exact_match | `'dopemux_pr_merge_specialist/queue_drain.py\n'` | UNKNOWN | UNKNOWN | [] |
| arbitrary_malformed | `'docs/readme.md\n'` | UNKNOWN | UNKNOWN | [] |
| arbitrary_malformed | `'some/totally/unrelated/file.txt\x01'` | UNKNOWN | UNKNOWN | [] |
| wildcard_exemption_spoof | `'services/dope-context/src/\nsecret.py'` | BLOCKED | BLOCKED | [FORBIDDEN_PATH] |
| wildcard_exemption_spoof | `'services/dope-context/src/index_profile.py\n'` | BLOCKED | BLOCKED | [FORBIDDEN_PATH] |
| wildcard_exemption_spoof | `'.github/workflows/embedded-audit.yml\n'` | BLOCKED | BLOCKED | [FORBIDDEN_PATH] |
| wildcard_exemption_spoof | `'services/task-orchestrator/x/\ny'` | BLOCKED | BLOCKED | [FORBIDDEN_PATH] |
| wildcard_exemption_spoof | `'services/dope-context/src/index_profile.py\t'` | BLOCKED | BLOCKED | [FORBIDDEN_PATH] |
| wildcard_exemption_spoof | `'services/dope-context/src/index_profile.py\r'` | BLOCKED | BLOCKED | [FORBIDDEN_PATH] |

## Result

`MUTATION_RESULT=BITES`. The 5 exact-match probes and 2 arbitrary-malformed
probes (7 total) revert fully to `Status.UNKNOWN` with zero findings under
the mutation — the true original bypass this packet closes. The 6
wildcard/exemption-spoof probes remain `Status.BLOCKED` via the independent,
unmutated `FORBIDDEN_PATH` rule in `red_lane_rules.py` (only their finding
category is affected — `MALFORMED_PATH_CONTROL_CHARACTER` no longer fires,
`FORBIDDEN_PATH` still does). All 13 probes were collected before evaluation;
none of the 6 wildcard/exemption-spoof probes were misreported as reverting
to `UNKNOWN` — the exact accuracy defect a live PR #1325 review finding
(thread `PRRT_kwDOPyIw986fya9B`) caught in round 2 of the unauthorized
implementation this packet supersedes.

`EARLY_ABORT=NO`. `MUTATION_MATRIX_PROBES_EXECUTED=13`.

## Durable regression protection

This same mutation (via `monkeypatch`, not a source edit) is also codified as
a permanent pytest test,
`test_isolated_mutation_control_character_short_circuit` in
`tests/dcp/test_dcp_0005_red_lane_scanner.py`, asserting the identical 7/6
split on every future test run — so a future accidental regression of the
short-circuit is caught automatically, not only at packet-execution time.
