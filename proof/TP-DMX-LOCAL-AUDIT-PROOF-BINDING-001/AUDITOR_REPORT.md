# Auditor Report — TP-DMX-LOCAL-AUDIT-PROOF-BINDING-001 (controlling: R4)

**Audited commit**: `8e9b802729a1e273221b9d217239fbcca657a5ad`
**Auditor**: `agy` / `gemini-3.1-pro-high`, `--mode plan`, read-only git worktree audit

This is the CONTROLLING report. It supersedes the R1 (`ab57983171`/`05c41b3e6b`),
R2 (`cdc83dda65`), and R3 (`a26474698c`) audits preserved in `review_bundle/`
as non-controlling historical evidence.

## Verdict: PASS

Independent verification of the R4 commit `8e9b802729` on
`feat/local-audit-proof-binding-001`, addressing a fresh finding from live
review on PR #1236.

### Finding disposition

**P2 (PACKET_ID colliding with the reserved `pr_merge` namespace)**:
**RESOLVED**. Pre-fix vulnerability independently reproduced: the trusted
schema's `report_path` pattern's `[^/]+` wildcard matches
`proof/pr_merge/AUDITOR_REPORT.md`, deriving `packet_id = "pr_merge"` prior
to R4 — which would widen the diff-scope allow-list to `proof/pr_merge/`,
the SHARED root every PR's own signed proof lives under, letting a proof
successor touch or delete any other PR's attestation while the
proof-only-delta check still passed. `_extract_packet_id` now explicitly
rejects a derived segment equal to `RESERVED_PACKET_NAMESPACE`, itself
derived from `PROOF_DIR_TEMPLATE` (the same constant the PR-scoped proof
path uses) so it cannot silently drift out of sync. Confirmed by directly
running both new regression tests (2 passed).

### Adversarial analysis (independently performed)
Checked for residual bypasses of the same shape: path traversal is
structurally impossible (`[^/]+` forbids `/`), and substring/prefix tricks
against the `path.startswith(f"{packet_dir}/")` check fail because git diff
paths are normalized and the literal trailing-slash comparison rejects any
partial match (e.g. `pr` vs `pr_merge`, or a trailing space). No residual
widening vector found.

### Pytest counts (real execution, not summarized)
- `tests/audit`: **400 passed, 1 skipped**

### Newly-introduced risks / regressions vs R1-R3
None identified. The R4 diff is minimal and purely additive — a single
explicit rejection condition inside `_extract_packet_id`, preserving all
prior schema/policy, signer-preflight, and object-type checks.

### Bottom line
Commit `8e9b802729` closes the final scope-widening bypass and is ready to
be treated as the controlling audited head for this canonical proof bundle.

---

Full raw transcript and prompt: `review_bundle/AGY_AUDIT_R4_RAW.json`,
`review_bundle/AGY_AUDIT_R4_PROMPT.md`. One prior invocation attempt for
this round was killed externally before producing output (empty response,
"timeout waiting for response") — preserved as
`review_bundle/AGY_AUDIT_R4_ATTEMPT1_KILLED_NONCONTROLLING.json` and
explicitly NOT promoted to any verdict. R1, R2, and R3 audits remain in
`review_bundle/` as superseded historical evidence, not controlling.
