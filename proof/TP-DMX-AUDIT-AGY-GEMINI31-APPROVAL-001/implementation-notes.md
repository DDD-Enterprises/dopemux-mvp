# Implementation Notes

## Decision
Approve gemini-3.1-pro-high as the exact AGY auditor model identifier.

## Evidence
- AGY v1.1.9 lists gemini-3.1-pro-high
- AGY v1.1.9 does NOT list gemini-3.1-pro-preview

### Re-verification 2026-08-10 (post-rebase onto main cfa4927a88)

The original evidence above was captured at AGY v1.1.9. It was re-verified rather
than trusted, because the branch was rebased onto current main and the local AGY
build had advanced.

- AGY v1.1.11 lists gemini-3.1-pro-high
- AGY v1.1.11 does NOT list gemini-3.1-pro-preview
- The v1.1.11 model list is byte-identical to the recorded v1.1.9 list (11 entries,
  same order) — no selector drift.

Raw captures are preserved side by side in
`proof/TP-DMX-AUDIT-AGY-GEMINI31-APPROVAL-001-REPAIR-001/review_bundle/`:
`AGY_VERSION.txt` / `AGY_MODELS.txt` (original, v1.1.9) and
`AGY_VERSION_REVERIFY_20260810.txt` / `AGY_MODELS_REVERIFY_20260810.txt` (v1.1.11).

## Bootstrap Audit Rule
Use auditor_tool=agy and auditor_model=gemini under pre-change schema.
