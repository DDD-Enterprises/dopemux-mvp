# Clean R1 Implementation Notes

## Scope

Independent reconstruction on
`codex/control-tower-supervisor-kit-clean-r1` from
`46b35b3cb0192d69a45cb41ed55df6ba34201e0e`. No donor commit was merged or
cherry-picked. Existing KIT and PR 1335 audit/signature files remain historical
and unchanged.

## Implemented

- Stream every staged regular-file byte without an arbitrary size rejection.
- Preserve secret candidates across chunk boundaries and arbitrary assignment
  whitespace; fail closed on unreadable, partial, special, symlink, traversal,
  or staging-drift conditions.
- Execute installed route and RETURN schemas using a fail-closed stdlib subset;
  apply route cross-field policy separately.
- Require nonblank, schema-valid RETURN reason and decision fields.
- Limit default runner inventory to local executable/version probes; model
  catalog discovery requires `--probe-models`.
- Bind caller, Task Packet, route, repository, canonical proof when present,
  RETURN metadata, root manifest, and package identity.
- Verify ZIP structure, canonical paths, scan receipt, inventory hashes/sizes,
  checksums, and identities; retain explicitly named `--crc-only` mode.
- Scope Control Tower routing to supervised packets/workstreams and retain
  ordinary repository/user/local model selection.
- Wire the standard-library kit matrix into pre-commit for local and CI use.

## Test Development

Initial RED: 14 tests, exit 1, 2 failures and 12 missing-API errors. Preserved in
`red-test-receipt.json`. A separate live probe showed a normalized ZIP alias
could escape coverage; preserved in `zip-alias-red-receipt.json`. Subsequent
streaming probes exposed an exempt-prefix nested assignment and an unbounded
`sk-` candidate; the behavioral RED is preserved in
`scanner-streaming-red-receipt.json` and `staged-byte-scan-red.log`; both cases
are now in the matrix.

Current focused matrix before committed-range validation: 23 tests, exit 0,
with raw output in `unittest-full.log`.
Includes an actual clean 20,000,001-byte proof package and a generated staged
diff secret that blocks with no ZIP output.

## Validation State

- PASS: focused standard-library matrix, 23 tests.
- PASS: packet canonical schema, Python compilation, JSON parsing, current route
  validation, `git diff --check`, and focused Control Tower pre-commit hook.
- FAIL then PASS: default Python lacked `jsonschema`; the canonical packet check
  passed with the existing dopetask tool environment. The first pre-commit
  attempt lacked an executable, the second could not write its default cache,
  and the third could not resolve configured hook repositories. The authorized
  explicit pre-commit 4.5.1 executable passed after using an isolated cache and
  fetching configured environments. Raw outcomes remain in validation logs.
- NOT_RUN: committed-range change-contract and full from/to pre-commit checks;
  they require the provisional local content commit.
- NOT_RUN: final independent model audit, intentionally deferred while PR 1330
  remains open.
- NOT_RUN: push, draft PR, CI, review harvest, merge.

## Rollback

Reviewed revert of only the clean-r1 successor commits. Do not reset, rewrite
history, delete branches, or mutate preserved donor/historical evidence.
