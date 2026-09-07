# Mutation evidence — TP-DMX-PR1304-RED-LANE-PATH-REGEX-HARDENING-002

Isolated per packet section 4: worktree reset to the clean implementation
commit before the mutation, mutation applied and its landed change count
asserted, full regression matrix re-run, worktree reset again after.

## Mutation: remove the control-character short-circuit

**Needle:** the body of `_has_control_chars` in
`src/dopemux/dcp/red_lane_scanner.py`, changed from
`return bool(_CONTROL_CHARS.search(s))` to `return False`.

**Landed replacement count:** 1 (asserted non-zero before running tests; the
mutation script fails loudly on any other count).

**Result — every probe's status collected, not just the first failure**
(automated review on this packet's PR correctly flagged an earlier version
of this evidence for stopping at the first failing assertion in a bare
`for`/`assert` loop; the test suite was subsequently parametrized with
`@pytest.mark.parametrize` so each probe is its own independent test case,
and this run reflects that fix):

```
14 failed, 6 passed, 33 deselected
(ran with: pytest tests/dcp/test_dcp_0005_red_lane_scanner.py -q -k control_char)
```

All 13 probes in `_CONTROL_CHARACTER_BLOCK_PROBES` failed under the
mutation — exact-match, wildcard, exemption-spoof, and arbitrary-malformed
cases alike — plus
`test_scanner_control_char_short_circuit_skips_filesystem_access`:

```
FAILED ...test_scanner_blocks_control_character_paths[scripts/dopetask\n]
FAILED ...test_scanner_blocks_control_character_paths[scripts/taskx\r]
FAILED ...test_scanner_blocks_control_character_paths[scripts/batch_resolve_and_merge.py\t]
FAILED ...test_scanner_blocks_control_character_paths[src/dopemux_pr_merge_specialist/queue_drain.py\x7f]
FAILED ...test_scanner_blocks_control_character_paths[dopemux_pr_merge_specialist/queue_drain.py\n]
FAILED ...test_scanner_blocks_control_character_paths[services/dope-context/src/\nsecret.py]
FAILED ...test_scanner_blocks_control_character_paths[services/dope-context/src/index_profile.py\n]
FAILED ...test_scanner_blocks_control_character_paths[services/task-orchestrator/x/\ny]
FAILED ...test_scanner_blocks_control_character_paths[services/dope-context/src/index_profile.py\t]
FAILED ...test_scanner_blocks_control_character_paths[services/dope-context/src/index_profile.py\r]
FAILED ...test_scanner_blocks_control_character_paths[.github/workflows/embedded-audit.yml\n]
FAILED ...test_scanner_blocks_control_character_paths[docs/readme.md\n]
FAILED ...test_scanner_blocks_control_character_paths[some/totally/unrelated/file.txt\x01]
FAILED ...test_scanner_control_char_short_circuit_skips_filesystem_access
```

Each failure is `Status.UNKNOWN` where `Status.BLOCKED` was expected — the
exact shape of the original silent bypass in packet section 1.3.

The 6 remaining tests that stayed green under this mutation are exactly the
ALLOW-case tests
(`test_scanner_legitimate_paths_unaffected_by_control_char_guard`, one per
clean-control probe) — correctly unaffected, since they assert the
*absence* of a `MALFORMED_PATH_CONTROL_CHARACTER` finding, which the
mutation does not introduce.

This is non-vacuous and now exhaustive: every probe the fix claims to
protect is independently shown to regress to the original silent-bypass
behavior when the fix is removed, not just the first one a loop happened to
reach.

## Restore

The clean implementation was restored from a pre-mutation snapshot
(`cp` copy taken before the mutation) and verified:

- `tests/dcp/test_dcp_0005_red_lane_scanner.py -q` → 53 passed
  (32 baseline + 21 new, after parametrization expanded the 2
  control-character test functions into 19 individual cases)
- `tests/dcp/ -q --deselect test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified` → 206 passed, 1 deselected
- `tests/test_dcp_surface_guard.py -q` → 44 passed

## Donor content integrity (fixes the pin-the-digest finding)

`git show 353bd8b245beb2c137f1ef94b45227d885328fed:tests/dcp/test_dcp_0005_red_lane_scanner.py | sha256sum`
must equal `2fa3ea27e4ebfea51932f0a7ac90680498c950d5ed9149c5788a67cb6a88eb20`.
This value is pinned in the packet document (section 3.2) as the expected
result, not merely recorded ad hoc after the fact — reproduced identically
across two separate fetches in this session.

## Note on the deselected test

`tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified`
fails independently of this packet's change. It reads a base-ref marker from
an unrelated packet document (`task-packets/TP-DCP-0002.md`) and diffs
`base_ref...HEAD`; that marker is stale relative to current `main`, so the
symmetric-difference range now includes unrelated `.github/workflows/*.yml`
changes from PR #1328 (the CI audit-evidence-gate overhaul), which trips the
test's `.github/workflows/` forbidden-prefix check. Reproduced on a fresh
checkout of `origin/main` at `6a728f74c...` with no packet changes applied at
all (fails there too, with a different proximate error due to a shallow
clone missing the stale ref entirely) — this is pre-existing environmental
fragility, not a regression introduced by this packet, and repairing it is
out of this packet's scope (`task-packets/TP-DCP-0002.md` is not in
`RUNTIME_MUTATION`, `TEST_MUTATION`, or `READ_ONLY`).

## Note on a fabricated review finding (not acted on)

An automated review comment on this PR claimed
`git merge-base --is-ancestor 582862ea5f9d9fa56fd1221b22d53036778706b2 66595692314c2d9f30082584483d419f5f218987`
exits 1, implying the audited commit is not an ancestor of the PR's actual
lineage. Independently checked: `66595692314c2d9f30082584483d419f5f218987`
does not exist as a git object anywhere in this repository
(`git cat-file -t` fails), and the real check —
`git merge-base --is-ancestor 582862ea5f9d9fa56fd1221b22d53036778706b2 HEAD`
against the actual current PR head — returns true. CI's own
`independent embedded audit` check independently confirms the same result
(`PASS`). This finding is factually wrong and was not acted on; replied to
the thread with this evidence rather than making an unnecessary change.
