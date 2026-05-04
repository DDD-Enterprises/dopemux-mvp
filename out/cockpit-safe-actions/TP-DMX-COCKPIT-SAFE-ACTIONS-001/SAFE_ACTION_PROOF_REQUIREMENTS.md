# Safe Action Gate Proof Requirements

**Packet:** TP-DMX-COCKPIT-SAFE-ACTIONS-001
**Status:** PRIMITIVE-LEVEL DESIGN SPECIFICATION (NO RUNTIME)

This file defines the post-action proof the Safe Action Gate must capture per tier. Proof is required for any completion claim. Missing proof escalates the row into the Unknown/Drift Queue with a `STALE_PROOF_GATE` tag. The gate captures proof emitted by the runtime authority owner; this packet does not implement runtime emission (see `TP-DMX-COCKPIT-RUNTIME-RENDER-001`).

## 1. Apex Rule: Proof Is Required For Completion Claims

The gate must:

- **Require proof to claim completion.** No success state, success chip, or completion event is emitted by the gate before the post-action proof has been captured per the tier's requirement.
- **Treat confirmation as intent, not proof.** The operator's confirm click is the operator's intent to run; it is **not** proof that the action ran.
- **Treat handoff as initiation, not proof.** The runtime authority's acknowledgment of handoff is initiation; proof requires the action's actual outcome.
- **Treat preflight green as readiness, not proof.** Preflight readiness means fields are resolved; it is not proof of execution.
- **Tag stale proof.** When proof is required but missing or expired, the row is tagged `STALE_PROOF` and surfaced via Overview drift summary and the Unknown/Drift Queue.

## 2. Proof Required Per Tier

| Tier | Proof category | Proof artifacts (required) | Proof artifacts (optional, when governance allows) |
| --- | --- | --- | --- |
| T0 | `INSPECT_RESULT_AND_TIMESTAMP` | View timestamp (UTC); source authority label captured at view time. | Last observed value snapshot. |
| T0i | `INSPECT_RESULT_AND_TIMESTAMP` (inspect class) | Command path; exit/result summary; source authority label; UTC timestamp. | Diagnostic output excerpt; environment snapshot. |
| T1 | `ARTIFACT_AND_CHECKSUM` | Artifact path; artifact checksum or content summary; UTC timestamp. | Exit code if invoked through a runner; runner id; runner branch/cwd. |
| T2 | `CONFIG_DIFF_OR_STATUS` | Config diff (before → after) **or** before/after status when diff is not derivable; command exit code; UTC timestamp. | Config target (file or service); validator output excerpt. |
| T3 | `FILESYSTEM_DIFF_OR_EXIT_CODE` | Filesystem path; action verb (`create`/`append`/`replace`/`delete`); result; exit code; UTC timestamp. | File checksum after write; rollback path verified. |
| T4 | `REMOTE_RECEIPT` | Remote endpoint; remote actor; remote status code; idempotency key (echoed); UTC timestamp. | Captured response excerpt where governance allows; correlation id from remote service. |
| T5 | `SERVICE_STATUS_AND_LOG` | Post-state status (`running`/`stopped`/etc.); log excerpt covering the transition; exit code; UTC timestamp. | Pre-state snapshot (echoed) for delta evidence; service version. |
| T6 | `TP_RUNNER_PROOF` | Exit code; proof path; validation summary; UTC timestamp. | TP id (echoed); runner id (echoed); branch (echoed); proof hash. |
| TX | `BLOCK_REASON_RECORD` | Block reason; replacement command (if any); evidence of attempted selection (UTC timestamp + originating surface); operator id if available. | Required external workflow reference. |
| TU | `INVESTIGATION_PACKET_REFERENCE` | Unknown reason; required investigation packet reference (or `INVESTIGATION_PACKET_REQUIRED` if not yet known); UTC timestamp. | Last activation status; last evidence reference. |

## 3. Proof Capture Flow

For executable tiers (T1–T6), the proof capture flow is:

1. Operator confirms in the gate (per `SAFE_ACTION_CONFIRMATION_FLOWS.md`).
2. Gate hands off to runtime authority owner identified by `canonical_writer`.
3. Runtime authority executes (out of scope this packet).
4. Runtime authority emits proof event with the artifacts above.
5. Gate captures the proof event:
   - Records proof on the gate event/receipt.
   - Validates that all required artifacts for the tier are present.
   - If any required artifact is missing: emits `PROOF_INCOMPLETE` event/receipt and tags row `STALE_PROOF`.
6. Gate updates the gate event/receipt with `proof_status: captured` (or `proof_status: incomplete`).
7. Operator sees the completed-with-proof state per `SAFE_ACTION_GATE_UI_PRIMITIVES.md`.

For non-executable tiers (T0, T0i, TX, TU), proof is captured at view/inspect/refusal time:

- T0: source authority + timestamp at display time.
- T0i: command + exit/result summary + source authority at inspect time.
- TX: block reason + evidence of selection at the time the operator viewed the blocked row.
- TU: unknown reason + required investigation packet at the time the operator viewed the unknown row.

## 4. Stale Proof Detection And Routing

The runtime is responsible for detecting stale proof. The gate displays the stale-proof state when the runtime tags it. When tagged:

- The gate event/receipt for the action has `proof_status: stale`.
- The row gains a `stale_proof` badge in any surface that displays it (Overview drift summary, Palette result row, Unknown/Drift Queue).
- Selecting the row in the palette routes to the Unknown/Drift Queue with `trigger_reason = STALE_PROOF` per `PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md` §1.
- The Unknown/Drift Queue documents the missing proof and the required action: re-execute the gated action and capture proof, or mark the action `EXTERNAL_ONLY` if proof cannot be captured (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §5 stale-proof row).

## 5. Proof Cannot Be Forged Or Pre-Computed

The gate must:

- Capture proof only after execution returns from the runtime authority owner. No pre-computed proof.
- Refuse to display a "completed" state for a tier that has not produced its required proof artifacts.
- Refuse to mark a row "completed with proof" when `proof_status: incomplete` or `proof_status: stale`.
- Refuse to suppress a proof event/receipt; even if the operator dismisses the gate, the receipt is recorded.

## 6. Proof Data Hygiene

- **No secrets in proof artifacts.** Remote receipts capture `endpoint`, `actor`, `status`, and an excerpt where governance allows; the gate must redact tokens, passwords, API keys, or PII.
- **Append-only.** Proof events/receipts are append-only; the gate never edits or deletes a recorded proof.
- **UTC timestamps.** All proof timestamps are ISO-8601 UTC. The gate never rewrites them with local-time values.
- **Correlation preserved.** Every proof event/receipt carries `gate_request_id` and `palette_request_id` (when applicable) for end-to-end audit.

## 7. Proof Required For Completion Claims (Examples)

| Action class | Confirmation alone | Confirmation + proof |
| --- | --- | --- |
| `./scripts/dopetask collect-evidence` (T1 generated artifact) | Operator confirmed; runtime acknowledged. | Artifact path + checksum captured; gate event/receipt updated; row marked completed with proof. |
| `dopemux routing` config change (T2 config mutation) | Operator confirmed; admin gate accepted. | Config diff + exit code captured; row marked completed with proof. |
| MCP server start (T5 service start) | Operator confirmed (with typed service id). | Post-state status + log excerpt + exit code captured; row marked completed with proof. |
| TP run (T6 execution handoff) | Operator confirmed (with typed TP id); runner accepted handoff. | Exit code + proof path + validation summary captured; row marked completed with proof. |
| `./scripts/dopetask commit-run` (TX blocked) | n/a — never confirmable. | Block reason record + evidence of attempted selection captured. |
| `dopemux genetic` (TU unknown) | n/a — never confirmable. | Unknown reason + required investigation packet captured. |

The "Confirmation alone" column is **not** a completion claim. Only the "Confirmation + proof" column qualifies.

## 8. Forbidden In Proof Capture

- Marking a row "completed with proof" before proof artifacts have been recorded.
- Emitting a success chip before proof exists (`PALETTE_PROOF_REQUIREMENTS.md` §8).
- Substituting confirmation receipts for execution proof.
- Substituting preflight render evidence for execution proof.
- Reusing proof from a prior run.
- Recording proof without `gate_request_id` correlation.
- Storing secrets, tokens, passwords, or PII in proof artifacts.
- Editing or deleting proof events/receipts.
- Auto-retrying a stale-proof action (`UNKNOWN_DRIFT_QUEUE_SPEC.md` §3).

## 9. Proof And Claude Design Boundary

This packet defines the proof contract. Final screens, runtime emission, and proof-display final designs are blocked at the Claude Design boundary (`CLAUDE_DESIGN_SAFE_ACTION_BLOCKERS.md`, `CLAUDE_DESIGN_BLOCKERS.md`). Claude Design may receive Safe Action Gate primitive sketches **after** this packet is accepted, but final screens depicting proof states remain blocked until the runtime renderer packet completes.

## 10. Source Artifacts

- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/SAFE_ACTION_GATE_SPEC.md` §3, §4
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/COMMAND_EXPOSURE_POLICY.json:classes.required_evidence_or_proof`
- `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/UNKNOWN_DRIFT_QUEUE_SPEC.md` §1, §5
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_PROOF_REQUIREMENTS.md` §1–§8
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_SAFE_ACTION_GATE_HANDOFF.md` §5
- `out/cockpit-command-palette/TP-DMX-COCKPIT-COMMAND-PALETTE-001/PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md` §1
