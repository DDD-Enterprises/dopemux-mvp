# Palette Proof Requirements

**Packet:** TP-DMX-COCKPIT-COMMAND-PALETTE-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)

This file defines the proof and audit/event receipt expectations the Command Palette must satisfy at every routing outcome. Proof requirements are inherited from `SAFE_ACTION_GATE_SPEC.md` §3 and `UNKNOWN_DRIFT_QUEUE_SPEC.md` §1, §6. The palette is a broker; it does not produce execution proof itself, but it produces routing-receipt proof that pairs with downstream execution proof.

## 1. Proof By Outcome

| Outcome | Palette-side proof | Downstream proof (where execution happens) |
| --- | --- | --- |
| `Inspect` (no execution) | Routing receipt: `palette_request_id`, timestamp (UTC), `command_path`, `authority_domain`, `safe_ui_exposure`, `activation_status`. Inspect view captures inspect result + source authority + timestamp (T0/T0i per gate spec). | Inspect result and source authority captured by Inspect drawer. |
| `CopyCommand` (no execution) | Routing receipt + clipboard event: `palette_request_id`, timestamp, `command_path`, `cwd_target`, `output_target`, `safe_ui_exposure`, fully resolved invocation copied to clipboard, evidence-stream entry "CLIPBOARD_COPY". | None (operator runs externally). |
| `OpenSafeActionGate` (gate handles execution) | Handoff receipt: `palette_request_id`, `palette_index_row_hash`, timestamp, target gate tier, target proof requirement, handoff outcome (`accepted`/`refused`/`rerouted`). | `SAFE_ACTION_GATE_SPEC.md` §3 proof per tier (T1–T6). |
| `OpenSettingsAdminRuntime` (surface invokes gate) | Handoff receipt: `palette_request_id`, `palette_index_row_hash`, timestamp, `flow_group`, `proposed_gate_tier`, handoff outcome. | Settings/Admin/Runtime surface captures admin gate proof (config diff, before/after, exit code). |
| `ShowBlockedReason` (no execution) | Routing receipt + blocked-display proof: `palette_request_id`, timestamp, `command_path`, `safe_ui_exposure == BLOCKED_IN_COCKPIT`, `blocked_reason`, replacement command (if any), required external workflow (if any). | None (no execution). |
| `ShowUnknownDriftReason` (no execution) | Routing receipt + unknown-display proof: `palette_request_id`, timestamp, `command_path` (or `UNKNOWN`), `trigger_reason`, `unknown_reason`, `required_investigation_packet` (when known). | None (no execution). |

## 2. Proof Content By Class (Mapping To Tier)

The palette's `proof_requirement` field on each row maps directly to the gate tier the row will use. The mapping is normative and unchanged from `SAFE_ACTION_GATE_SPEC.md` §3.

| Class / Tier | Proof captured |
| --- | --- |
| `T0` (`DISPLAY_ONLY`) | Inspect result + source authority + timestamp. |
| `T0i` (`INSPECT_ACTION`) | Command path + exit/result summary + source authority. |
| `T1` (`CONFIRM_REQUIRED`, generated artifact) | Artifact path + checksum/summary; logged to evidence. |
| `T2` (`CONFIRM_REQUIRED`, config mutation) | Config diff or post-action status; logged. |
| `T3` (`CONFIRM_REQUIRED`, write local) | Filesystem diff, artifact path, or exit code. |
| `T4` (`CONFIRM_REQUIRED`, write remote) | Remote receipt or API result captured. |
| `T5` (`CONFIRM_REQUIRED`, start/stop service) | Post-action status / log evidence + exit code. |
| `T6` (`CONFIRM_REQUIRED`, execution handoff) | Exit code + proof path + validation summary. |
| `TX` (`BLOCKED_IN_COCKPIT`) | Block reason + replacement command (if any) + evidence of attempted selection. |
| `TU` (`UNKNOWN`) | Reason unknown + required investigation packet id. |

## 3. Audit / Event Receipt Schema

Every palette routing emits a receipt to the evidence stream. The schema:

```
{
  "palette_request_id": "<UUID>",
  "palette_index_row_hash": "<sha256>",
  "timestamp_utc": "<ISO-8601>",
  "command_path": "<string or UNKNOWN>",
  "parent_group": "<string>",
  "authority_domain": "<one of ten or UNKNOWN>",
  "canonical_writer": "<string or UNKNOWN>",
  "safe_ui_exposure": "<one of seven>",
  "cockpit_placement": "<one of nine>",
  "current_cockpit_coverage": "<one of four>",
  "activation_status": "<one of four>",
  "selected_outcome": "<one of six>",
  "gate_tier": "<one of T0..T6, TX, TU>",
  "proof_requirement": "<one of ten>",
  "handoff_outcome": "<accepted|refused|rerouted|inspect|copy|blocked|unknown>",
  "refusal_reason": "<one of enumerated reasons or null>"
}
```

The receipt is recorded for every routing decision the palette makes, including `Inspect`, `CopyCommand`, blocked, and unknown. The runtime packet (`TP-DMX-COCKPIT-RUNTIME-RENDER-001`) is responsible for wiring the evidence stream; this packet defines the schema.

## 4. Stale Proof Detection (Read-Only In Palette)

The palette does not detect stale proof itself. It surfaces stale-proof rows when the runtime tags them. When tagged:

- The row gains a `stale_proof` badge in the result row.
- Selecting the row routes to Unknown/Drift Queue with `trigger_reason = STALE_PROOF`.
- The queue documents the missing proof and the required action: re-execute the gated action and capture proof, or mark the action `EXTERNAL_ONLY`.

## 5. External-Only And Copy-Command Proof

For rows whose execution authority lives outside Cockpit (`safe_ui_exposure == EXTERNAL_ONLY`):

- The palette captures the `CopyCommand` event as the proof: clipboard log entry with `command_path`, `cwd_target`, `output_target`, timestamp, `palette_request_id`.
- No Cockpit-side execution proof is captured.
- The external authority owner is documented in the routing receipt for traceability.

## 6. Refused Handoff Proof

A refused handoff (e.g. `PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §3 refusal triggers) produces:

- Routing receipt with `handoff_outcome = refused`.
- `refusal_reason` set to one of the enumerated reasons.
- Re-route receipt for the next destination (Unknown/Drift Queue, blocked display, or alternate surface).

The palette never silently drops a refused handoff.

## 7. Audit Integrity Requirements

- Every receipt is append-only in the evidence stream; receipts are never edited or deleted by the palette.
- `palette_request_id` is unique per click; a single operator selection produces exactly one routing receipt.
- `palette_index_row_hash` is recomputed at handoff time from the live index row; if it differs from the rendered preview's hash, the palette displays `INDEX_DRIFT` and re-renders the preview before allowing handoff.
- Receipts include UTC timestamps and are never rewritten with local-time values.

## 8. Forbidden In Proof Behavior

- Suppressing the routing receipt for any outcome.
- Reusing a `palette_request_id` across selections.
- Producing a success chip before downstream proof exists.
- Marking a stale-proof row as fresh inside the palette.
- Capturing a `CopyCommand` event without recording the resolved invocation in the receipt.
- Recording a handoff as `accepted` when downstream surfaces refused it.

## 9. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md` §3, §4
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md` §1, §6
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_PALETTE_SPEC.md` §3, §6
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/COMMAND_PALETTE_INDEX_SCHEMA.json`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SETTINGS_RUNTIME_HANDOFF.md`
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md`
