---
id: TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R
stage: PRE_PUSH_REPAIR
artifact: PACKET_SCOPE_REPAIR
---
# Packet scope repair — why `001R`, not `001`

## Prior draft found

`task-packets/TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001.json` (no `R` suffix) already
existed on `main` before this session's Phase A work began. It was never
loaded/executed against this repo's canonical task-packet schema
(`docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`) — confirmed
by direct validation:

* it carries top-level keys (`background`, `status`, `authorizes_edits_to`,
  `does_not_authorize`) that are not in the canonical schema's property list,
  which has `additionalProperties: false` at the top level;
* it is missing the canonical schema's required top-level `commit` and `pr`
  objects entirely.

So it would fail `scripts/governance/validate_change_contract.py`'s
`packet_schema_fail` check (the same check that caught a similar defect in
`TP-DMX-AUDITOR-ADMISSION-OPENCODE-OPENROUTER-001.json` during that packet's
S2). It is correctly marked `"status": "DRAFT_NOT_LOADED"` inside itself.

## Scope mismatch, independent of the schema defect

Even schema issues aside, that draft's steps `S3` and `S4` commit this series
to unrelated historical work this session never touched or was asked to
touch:

* `S3`: cherry-pick / re-derive commit `94f368b8c`
  (`tools/pr_steward/workflow_run_identity.py`) from a different worktree
  branch (`worktree-pr-steward-security-approval-parity`), wiring
  `pr-steward.yml`'s identity-check step to call it.
* `S4`: extract `embedded-audit.yml`'s inline diagnostic-proof heredocs into
  a new `scripts/audit/diagnostic_proof.py` module.

Both reference a prior initiative
(`TP-DMX-AUDIT-STEWARD-CONTRACT-HYGIENE-001`) and a specific historical
commit this session has neither inspected nor been authorized to act on.
Phase A of this packet (`001R`) originated independently, triggered by the
`DCP-RED-MERGE-SEAM-0001` block hit during
`TP-DMX-AUDITOR-ADMISSION-OPENCODE-OPENROUTER-001` S3 — a different concrete
change (`schema_validate_embedded_audit()` wiring), not the identity-check or
diagnostic-proof extractions the old draft describes.

## Resolution

Per supervisor instruction: author a new, schema-valid packet,
`TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R`, scoped to exactly what this session
built and validated — the ADR, the guard carve-out, and the focused tests —
plus an explicit, not-yet-authorized placeholder step for the eventual
two-file workflow wiring. The old `001` (no `R`) draft is left untouched on
disk (not deleted, not amended — it was never loaded, so there is no
execution state to reconcile) and is superseded for this scope. Its `S3`/`S4`
historical-extraction scope is out of scope for `001R` and is not carried
forward; if that work is still wanted, it needs its own fresh packet with its
own verified premises (in particular, re-confirming commit `94f368b8c` and
branch `worktree-pr-steward-security-approval-parity` still exist and are
current, which this session has not checked).
