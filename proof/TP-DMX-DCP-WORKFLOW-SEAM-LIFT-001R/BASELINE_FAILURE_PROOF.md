---
id: TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R
stage: PRE_PUSH_REPAIR
artifact: BASELINE_FAILURE_PROOF
---
# Baseline-failure proof — `test_16_no_forbidden_files_modified`

Required by supervisor decision (`SEAM_LIFT_001R_LOCAL_REVIEW=ACCEPT_WITH_DETERMINISTIC_PROOF_REPAIR`):
prove that `tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified`
fails identically on unmodified `origin/main` and on the Phase A implementation head
`9e113e68d0`, so the failure is classified as a pre-existing stale-anchor artifact
and not a regression introduced by this packet.

## Method

Two clean, detached `git worktree add --detach` checkouts (no working-tree state
carried over, no shared cache):

```bash
git worktree add --detach /tmp/seam-lift-baseline-main origin/main
git worktree add --detach /tmp/seam-lift-candidate-9e113e68d0 9e113e68d0
```

Identical command run in each:

```bash
python3 -m pytest -q tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified
```

Both worktrees removed (`git worktree remove --force`) after capturing output —
scratch only, no retained state.

## Results

| | `origin/main` (`ff08e573b4259ac7456dae1a9985968603e9111d`) | `9e113e68d0` (Phase A candidate) |
|---|---|---|
| Exit code | 1 (FAIL) | 1 (FAIL) |
| Test outcome | 1 failed | 1 failed |

`diff` of the full captured stdout+stderr of both runs: **empty** (byte-identical),
confirmed via `diff /tmp/seam-lift-baseline-main-output.txt /tmp/seam-lift-candidate-9e113e68d0-output.txt`
exiting `0`.

## Normalized failure message

```
AssertionError: Forbidden files in git diff:
.github/workflows/ci-complete.yml
.github/workflows/clobber-guard.yml
.github/workflows/ddd-release-gate.yml
.github/workflows/docker-scout.yml
.github/workflows/embedded-audit.yml
.github/workflows/gemini-plan-execute.yml
.github/workflows/gemini-review.yml
.github/workflows/pr-steward.yml
```

Identical file list, identical order, in both runs.

## Root cause (unchanged by this packet)

The test does not diff against `origin/main`'s parent commit or against this
packet's own base. It reads a **fixed historical base ref** embedded in an
unrelated packet's markdown:

```
task-packets/TP-DCP-0002.md:20: **Base**: `main` @ `68f7435f6` (TP-DCP-0001 merge commit)
```

`_packet_base_ref()` regex-extracts `68f7435f6` from that line and diffs
`68f7435f6...HEAD`. Since `68f7435f6` predates many since-merged PRs that
legitimately touched `.github/workflows/*`, the assertion fails on **any**
commit reachable from that stale anchor — independent of what this packet
changes. This packet does not modify `task-packets/TP-DCP-0002.md`, so the
anchor is unchanged by Phase A.

**Fixed historical base ref**: `68f7435f6` (TP-DCP-0001 merge commit, per
`task-packets/TP-DCP-0002.md`).

## Classification

```
main exit code:        1 (FAIL)
candidate exit code:   1 (FAIL)
signatures:             IDENTICAL
classification:         BASELINE_EXISTING_STALE_ANCHOR, non-blocking
```

Per the supervisor's required classification table: `main` and candidate both
FAIL with an identical signature → `IDENTICAL` → `BASELINE_EXISTING_STALE_ANCHOR`,
non-blocking. This is **not** `BLOCKED_REGRESSION` (that requires main PASS /
candidate FAIL) and **not** `NEEDS_SUPERVISOR` (that requires a different
failure). No repair or suppression of this test was made or attempted, per
instruction.
