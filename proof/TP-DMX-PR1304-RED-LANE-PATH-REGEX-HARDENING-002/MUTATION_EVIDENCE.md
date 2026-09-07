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

**Result:** `test_scanner_blocks_control_character_paths` fails on the
**first** probe in `_CONTROL_CHARACTER_BLOCK_PROBES`, which is the exact-match
bypass this packet exists to close:

```
AssertionError: scripts/dopetask
assert <Status.UNKNOWN: 'UNKNOWN'> == <Status.BLOCKED: 'BLOCKED'>
  - BLOCKED
  + UNKNOWN
```

`test_scanner_control_char_short_circuit_skips_filesystem_access` also fails
under the same mutation (its arbitrary-malformed-path probe likewise reverts
to `Status.UNKNOWN`).

Full suite result under mutation: `2 failed, 34 passed` —
`tests/dcp/test_dcp_0005_red_lane_scanner.py -q`.

This is non-vacuous: the failing probe under mutation
(`scripts/dopetask\n`) is precisely the path that was silently bypassing the
scanner on unmodified `main` before this packet's fix (see packet section
1.3). The mutation reproduces the original defect; the fix's absence
reintroduces it; the tests catch it.

## Restore

The clean implementation was restored from a pre-mutation snapshot
(`cp` copy taken before the mutation) and verified:

- `tests/dcp/test_dcp_0005_red_lane_scanner.py -q` → 36 passed
- `tests/dcp/ -q --deselect test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified` → 189 passed, 1 deselected
- `tests/test_dcp_surface_guard.py -q` → 44 passed

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
