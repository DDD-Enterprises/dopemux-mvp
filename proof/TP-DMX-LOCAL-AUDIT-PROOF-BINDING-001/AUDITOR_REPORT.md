# Auditor Report — TP-DMX-LOCAL-AUDIT-PROOF-BINDING-001 (controlling: R7+R8)

**Audited commit**: `60391753f56f1df0bf3e6a9914e88059d07bd8d7`
**Auditor**: `agy` / `gemini-3.1-pro-high`, `--mode plan`, read-only git worktree audit

This is the CONTROLLING report. It supersedes the R1-R6 audits preserved in
`review_bundle/` as non-controlling historical evidence. R7 (`ae90ff3c33`)
was never independently pushed as a controlling proof before R8
(`60391753f5`) landed on top of it, so this single audit covers both
diffs together, against the exact commit that is now the controlling head.

## Verdict: PASS_WITH_RISKS

Four AGY invocations were required to obtain a controlling result:
- Attempt 1: `status: ERROR` (internal cascade-step failure — "cannot kill
  task ... task is not running (status: DONE)" — despite substantive-looking
  response content). Per standing discipline, an `ERROR` status is never
  promoted to a verdict regardless of how plausible its content reads.
  Discarded, preserved as `AGY_AUDIT_R7R8_ATTEMPT1_ERROR_STATUS_NONCONTROLLING.json`.
- Attempt 2: `status: ERROR`, pure transport timeout, empty response.
  Discarded, preserved as `AGY_AUDIT_R7R8_ATTEMPT2_TRANSPORT_ERROR_NONCONTROLLING.json`.
- Attempt 3: killed externally mid-run, `status: ERROR`, empty response.
  Discarded, preserved as `AGY_AUDIT_R7R8_ATTEMPT3_KILLED_NONCONTROLLING.json`.
- Attempt 4: clean `status: SUCCESS`. This is the controlling run
  (`AGY_AUDIT_R7R8_RAW.json` / `AGY_AUDIT_R7R8_REPORT.md`).

### Findings disposition

1. **R7 fix (symlinked packet PROOF.json not rejected)**: **RESOLVED**.
   Independently confirmed the script explicitly checks `is_symlink()` on
   `packet_proof_path`, independent of the git-dirty check.
2. **R7 fix (stale operator runbook)**: **RESOLVED**. `docs/ops/embedded-audit.md`
   now correctly documents committing the canonical packet bundle before
   running the signer.
3. **R8 fix (symlinked `packet_dir` ancestor bypassing all leaf checks)**:
   **RESOLVED**. The `packet_dir_ok` guard was independently enumerated
   against all five downstream checks it must gate (report_file,
   review_bundle_dir presence, review_bundle_dir contents, the git-dirty
   check, and packet_proof_path) and confirmed each is actually gated, not
   left ungated by omission.

### Severity taxonomy applied to this round

This audit was explicitly instructed to classify any new finding as
BLOCKING only if it would let the CI-side trusted acceptance engine
(`local_audit_acceptance.py`) accept a proof it should reject, versus
NON-BLOCKING if it is a signer-preflight-only divergence that still fails
closed in CI regardless. This mirrors the classification already applied
to the R6 gitignore-only-bundle edge case. No BLOCKING findings were
surfaced this round.

### Adversarial analysis (independently performed) — two non-blocking risks found

1. **Mixed real files and illegal symlinks inside `review_bundle/`**: the
   signer's `any(p.is_file() and not p.is_symlink() for p in
   review_bundle_dir.rglob("*"))` check returns `True` if at least one real
   file exists in the bundle, so a bundle containing both a real file and a
   stray symlink would locally read "OK". The CI acceptance engine (since
   R5) strictly enforces `_REGULAR_FILE_MODES` (100644/100755) per entry
   when walking the committed tree and rejects mode-120000 entries, so this
   fails closed in CI regardless. Non-blocking.
2. **A submodule/gitlink placed inside `review_bundle/`** and **the `proof/`
   parent directory itself being a symlink** were also raised in the
   discarded ERROR-status attempt 1 and independently corroborated in
   substance by attempt 4's own step-6 pass; both fail closed in CI (mode
   `160000` gitlinks and a symlinked `proof/` are both rejected once
   pushed, since CI reads committed git blobs, not the working tree).
   Non-blocking.

### Correction to this audit's own prompt premise

The audit prompt (`AGY_AUDIT_R7R8_PROMPT.md`) incorrectly asserted the
trusted acceptance engine (`local_audit_acceptance.py`) was unchanged since
R4. The auditor independently caught and corrected this: R5
(`5adc090065`) is the round that added `_REGULAR_FILE_MODES` and
`_is_regular_file()` to the acceptance engine itself. The accurate claim is
that the acceptance engine has been unchanged since **R5**, not R4 — R6,
R7, and R8 all repaired only the local signer's preflight
(`sign_local_audit_proof.sh`), never the CI-side engine.

### Dogfooding confirmation
`bash scripts/audit/sign_local_audit_proof.sh 1236` was run directly
against this repository's real, already-committed PR #1236 bundle in the
audit worktree. Preflight correctly printed "proof shape OK" — confirms the
R7+R8 protections introduce no false-positive rejection for the legitimate,
fully-committed case.

### Pytest counts (real execution, not summarized)
- `tests/audit`: **408 passed, 1 skipped, 0 failed**

### Bottom line
Commit `60391753f5` resolves both the R7 and R8 findings with fail-closed
logic, causes no usability regression for valid workflows (confirmed by
dogfooding), and is ready to be treated as the controlling audited head for
this canonical proof bundle. Both newly-identified risks are
signer-preflight-only diagnostic gaps; the CI-side trusted acceptance
engine remains unchanged since R5 and fails closed on every case raised
across all eight rounds to date.

### Note on the operator's `FINAL_L3_AUDIT=PASS` bootstrap gate condition
This round's controlling verdict is `PASS_WITH_RISKS`, not a bare `PASS`.
Every controlling audit since R6 has also returned `PASS_WITH_RISKS`. This
is named explicitly, not silently equated with a bare PASS, per standing
practice: whether `PASS_WITH_RISKS` (with these named, all-non-blocking
risks) satisfies the operator's literal `FINAL_L3_AUDIT=PASS` bootstrap
condition is for the operator to confirm, not assumed here.

---

Full raw transcript, prompt, and all discarded non-controlling attempts:
`review_bundle/AGY_AUDIT_R7R8_*`. R1-R6 audits remain in `review_bundle/`
as superseded historical evidence.
