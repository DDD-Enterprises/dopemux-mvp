# TP-DMX-AUDIT-CI-PROVENANCE-104 Validation Output

## TDD Red

`pytest -q tests/audit/test_run_embedded_audit.py`

Result before implementation: FAIL.

Expected missing-entrypoint failure was observed:

- `ModuleNotFoundError: No module named 'scripts.audit.run_embedded_audit'`

## Focused Packet Validation

`pytest -q tests/audit/test_run_embedded_audit.py`

Result: PASS (`7 passed`, including trusted-source execution, trusted-token
step isolation, default-branch manual dispatch trust, requested PR head-ref
membership verification, missing PAL output handling, and bootstrap SKIPPED
proof assertions).

`python -m json.tool task-packets/generated/TP-DMX-AUDIT-CI-PROVENANCE-104.json`

Result: PASS.

`python -m compileall -q scripts/audit/run_embedded_audit.py tests/audit/test_run_embedded_audit.py`

Result: PASS.

## Broad Validation

`python -m compileall -q scripts tests`

Initial result: FAIL.

Existing files outside the TP104 allowlist fail compilation:

- `scripts/migration/switchover.py`
- `scripts/partition_function.py`
- `scripts/submit_loop_context.py`

The user explicitly expanded scope with: `fix other compille issues`.

Fixes applied:

- `scripts/migration/switchover.py`: corrected `SchemaS witchover` to `SchemaSwitchover`.
- `scripts/partition_function.py`: preserved the tracked legacy fragment as an inert module string.
- `scripts/submit_loop_context.py`: preserved the tracked legacy fragment as an inert module string.

Final result: PASS.

## Proof Validation

`python scripts/audit/validate_audit_proof.py proof/TP-DMX-AUDIT-CI-PROVENANCE-104/PROOF.json`

Result: PASS.

`git diff --check`

Result: PASS.

`git check-ignore -q proof/TP-DMX-AUDIT-CI-PROVENANCE-104/PROOF.json; test $? -eq 1`

Result: PASS.

`pre-commit run --files <TP104 changed files>`

Result: PASS.

Changed-file hooks passed:

- docs YAML frontmatter validation
- docs knowledge graph schema validation
- prohibited documentation pattern check
- prelude token limit
- docs placement and filename hygiene
- markdownlint
- trailing whitespace
- end-of-file
- YAML check skipped because no YAML files were provided

## Replay Artifact Generation

`python -m tools.auditor_router.preflight --packet-id TP-DMX-AUDIT-CI-PROVENANCE-104 --out proof/TP-DMX-AUDIT-CI-PROVENANCE-104 --format json`

Result: PASS.

`python scripts/audit/run_embedded_audit.py --packet-id TP-DMX-AUDIT-CI-PROVENANCE-104 --repo DDD-Enterprises/dopemux-mvp --pr 756 --head-sha de21c772f623ca0f8dff04019e2836ae5ce3bb9d --route-json proof/TP-DMX-AUDIT-CI-PROVENANCE-104/AUDITOR_ROUTE.json --out proof/TP-DMX-AUDIT-CI-PROVENANCE-104 --generated-at 2026-01-01T00:00:00Z`

Result: PASS.

The generated proof records `trusted_token_status=UNKNOWN`,
`token_value_recorded=false`, and `embedded_audit.status=SKIPPED` because no
separate `EMBEDDED_AUDIT_TOKEN` or live PAL clink output was available locally.

`python scripts/audit/run_embedded_audit.py --packet-id TP-DMX-AUDIT-CI-PROVENANCE-104 --repo DDD-Enterprises/dopemux-mvp --pr 761 --head-sha ce4acffb066f8860311c76d74f5fb353d82b412c --route-json <missing> --out <tmp-artifacts> --generated-at 2026-01-01T00:00:00Z`

Result: PASS.

The missing route JSON path returned exit code 0 with a schema-valid `SKIPPED`
proof and wrote `proof/TP-DMX-AUDIT-CI-PROVENANCE-104/AUDITOR_REPORT.md` under
the temporary artifact root.

## Task Orchestrator

`mcp task-orchestrator get_context health-check`

Result: FAIL.

The MCP tool returned `Transport closed`; no Task Orchestrator state was advanced.
