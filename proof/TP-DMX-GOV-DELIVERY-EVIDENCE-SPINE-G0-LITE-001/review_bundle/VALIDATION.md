# Validation ledger

Audited content head: `eeebed83fc57621fb731c1d81acdb3a2412f6eef`

## PASS

- `python -m jsonschema -i task-packets/TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-G0-LITE-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` — exit `0`.
- `python3 scripts/governance/validate_change_contract.py --base origin/main --head HEAD --format text` — exit `0`; `status=PASS`, `max_lane=L0`, `paths=1`.
- `pre-commit run --from-ref origin/main --to-ref HEAD` — exit `0` after sandbox retry with linked-worktree index access.
- `git diff --check origin/main...HEAD` — exit `0`.
- packet secret-shape scan — no matches.
- ordinary CI workflow `32812797232` — completed `success` at audited head.
- direct Claude Code CLI audit — exit `0`; `PASS_WITH_RISKS`.

## FAIL

- None in deterministic packet validation.

## NOT_RUN / blocked

- Auditor-side validators: `NOT_RUN` because direct Claude invocation had tools and MCP disabled.
- Canonical proof validation: pending proof-only successor creation, then required.
- Signed PR-scoped local attestation: `NOT_RUN`; operator signing authority not inferred.
- PR Steward readiness: blocked until canonical proof is committed and an accepted exact-head PR audit route exists.
- G0-Lite payload implementation: `NOT_RUN`; supervisor implementation authority record absent on `origin/main`.

## Noncontrolling prior route

CI PAL/clink audit run `32812797276` returned `NEEDS_SUPERVISOR` because its
runner reported `Credit balance is too low`. Operator directed use of direct
Claude CLI instead. No PAL/clink verdict was reused.
