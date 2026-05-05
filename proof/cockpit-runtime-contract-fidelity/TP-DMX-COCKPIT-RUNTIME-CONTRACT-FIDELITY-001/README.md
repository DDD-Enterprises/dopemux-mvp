# TP-DMX-COCKPIT-RUNTIME-CONTRACT-FIDELITY-001 Proof

## Boundary State

- safe_for_claude_design: NO
- READY_FOR_CLAUDE_DESIGN: not approved
- No Claude Design upload.
- No final screen generation.
- No runtime action execution.
- No T4 remote mutation.
- No live service adapters, PM writes, memory writes, bridge writes, or canonical writes.
- Unknown / Drift Queue remains non-executing and runtime reclassification remains disabled.
- TX and TU remain non-executable.

## Implemented Repairs

- EXTERNAL_ONLY Safe Action candidates now fail closed before confirmable gate checks and route back to the originating inspect/copy surface.
- Gate receipts recompute action_row_hash from a redacted canonical candidate payload instead of trusting caller input.
- Gate receipts include the local lifecycle fields required by the accepted receipt contract: event timestamp, gate-open timestamp, confirm/proof timestamps, typed-confirmation state, diff acknowledgement, remote policy, task, service, stale-proof tag, event type, and normative schema version.
- Non-palette receipt origins now emit `palette_request_id: null`.
- Default gate_request_id derivation is stable across modeled lifecycle events for the same canonical candidate payload.
- Unknown / Drift aggregate counts now preserve UNKNOWN when any contributing aggregate item has unknown count.
- Unknown / Drift queue row hashes and queue item IDs are derived after redaction.
- Package directory resolution now supports deterministic repo-relative lookup through `.dopetaskroot` while keeping accepted package path validation fail-closed.
- Inventory tests now validate source artifact sha256 values and runtime source line counts.

## Validation Recorded

The machine-readable validation table is in `out/cockpit-runtime-contract-fidelity/TP-DMX-COCKPIT-RUNTIME-CONTRACT-FIDELITY-001/PROOF.json`.

Validated so far:

- `python -m json.tool task-packets/generated/TP-DMX-COCKPIT-RUNTIME-CONTRACT-FIDELITY-001.json >/dev/null` exit 0
- `python -m compileall -q src/dopemux tests` exit 0
- `python -m pytest tests/unit/dopemux/ui/cockpit -q` exit 0
- `python -m pytest tests/unit/test_cockpit_cli.py -q` exit 0
- `python -m pytest tests/unit/dopemux/ui/cockpit/test_inventory_regen_artifacts.py -q` exit 0
- `python -m json.tool out/cockpit-runtime-contract-fidelity/TP-DMX-COCKPIT-RUNTIME-CONTRACT-FIDELITY-001/PROOF.json >/dev/null` exit 0
- Forbidden governance grep exit 0
- Forbidden runtime-token grep exit 0
- `git diff --check` exit 0
- Packet allowlist `pre-commit run --files ...` exit 0

## UNKNOWNs

- `dopetask-canonical-spec.json` is absent in this checkout; TP validation used JSON parsing and manual root-field checks.
- Root `RULES.md`, `TRUTH_*.md`, and `SYSTEM_*.md` files are absent in this checkout.
- `proof/cockpit-merge-execute/TP-DMX-COCKPIT-MERGE-EXECUTE-001/PROOF.json` is absent.
- `proof/cockpit-merge-execute/TP-DMX-COCKPIT-MERGE-EXECUTE-001/BLOCKER_REPORT.md` is absent.
- The local receipt primitive still models receipt payloads only; it does not write an evidence stream or execute actions.

## Final Head Policy

`PROOF.json` records implementation evidence before the final commit and PR exist. Final commit SHA, pushed branch, PR URL, and any proof metadata drift are reported in closeout to avoid self-referential proof churn.
