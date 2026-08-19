## Verdic
**PASS_WITH_RISKS**

## Step 2, 3, & 4: Confirmation of R7 & R8 Fixes
Both fixes are **RESOLVED**.
- **R7** is resolved (`ae90ff3c33`): The signer correctly rejects symlinked `PROOF.json` paths and the runbook flow was corrected in `docs/ops/embedded-audit.md`.
- **R8** is resolved (`60391753f5`): The `packet_dir_ok` variable properly guards all five downstream checks (report file, review bundle dir presence, review bundle dir contents, git-dirty check, and packet proof path). If `packet_dir` is a symlink, all downstream tests are skipped and the entire packet fails.

### Git Log and Diff Outpu
```bash
$ git log --oneline -20
60391753f5 fix(audit): R8 repair — guard against a symlinked packet_dir ancestor
ae90ff3c33 fix(audit): R7 repair — reject symlinked packet PROOF.json, fix runbook flow
670f7269f4 proof(audit): signed local embedded-audit attestation for PR 1236 (R6)
...

$ git diff ae90ff3c33^..60391753f5 --sta
 docs/ops/embedded-audit.md                         |  14 ++-
 scripts/audit/sign_local_audit_proof.sh            |  47 ++++++---
 .../TP-DMX-LOCAL-AUDIT-PROOF-BINDING-001.json      |   5 +-
 tests/audit/test_local_audit_acceptance.py         | 116 +++++++++++++++++++++
 4 files changed, 166 insertions(+), 16 deletions(-)
```

### Pytest Explicit Fix Checks (Step 4 & 5)
The specific explicit tests for R7 and R8 both pass:
```
============================= test session starts ==============================
collected 2 items
tests/audit/test_local_audit_acceptance.py ..                            [100%]
============================== 2 passed in 1.47s ===============================
```

## Step 7: Acceptance Engine Stability Check
**Premise Check Failed:** Your premise that the acceptance engine (`scripts/audit/local_audit_acceptance.py`) is unchanged since R4 is **INCORRECT**. The R5 repair modified the acceptance engine itself to enforce regular-file modes (100644/100755) and reject mode 120000 symlinks in `_tree_has_entries` and `_is_regular_file`.

```diff
-    if _tree_type(repo_root, head_sha, report_path) != "blob":
+    if not _is_regular_file(repo_root, head_sha, report_path):
         reasons.append(
-            f"packet_report_absent: {report_path} is not a file (blob) at PR head"
+            f"packet_report_absent: {report_path} is not a regular file at PR head"
         )
         return attestation
```

## Step 6: Adversarial Findings
Based on the explicit severity taxonomy provided, the following divergence was discovered between the local signer script and the CI acceptance engine.

**1. Mixed symlinks and real files in `review_bundle/` (Severity: NON-BLOCKING)**
* **Reasoning**: The local signer uses `any(p.is_file() and not p.is_symlink() for p in review_bundle_dir.rglob("*"))`. This returns `True` as long as there is at least *one* real file inside the bundle directory. If an operator places both a real file and an illegal symlink in the `review_bundle` directory, the signer will incorrectly say `"proof shape OK"`. However, because the CI acceptance engine was updated in R5 to strictly read `_REGULAR_FILE_MODES` (`100644`/`100755`) and explicitly rejects `120000` symlinks when iterating over the review bundle tree, CI will correctly fail the workflow. This represents a diagnostic-quality/operator-UX gap, but fails closed on the trusted end.

## Step 5: Dogfooding Confirmation
The dogfooding check correctly validated the preflight against PR #1236 without regressions:
```bash
proof shape OK (audited head 5224218c67c9f31b854ab6c9fd60c75222ecbd0e)
Signing file proof/pr_merge/embedded-audit/pr-1236/PROOF.json
signed: proof/pr_merge/embedded-audit/pr-1236/PROOF.json.sig
```

## Step 8: Real Pytest Counts
A full test run against `tests/audit -q` collected 409 items:
* **408 passed**
* **1 skipped** (`tests/audit/test_embedded_audit_grok_route.py:253: origin/main already carries the grok route; this packet merged`)
* **0 failed**

The bash syntax dry-run (`bash -n`) returned clean.

## Bottom Line
This R7+R8 combined commit effectively resolves the known trust boundary edge cases (symlinked upstream proofs and downstream directories) by ensuring proper filesystem assertions gate local script validation. It is **ready to be treated as the controlling audited head** for a fresh canonical proof bundle. I am stamping it `PASS_WITH_RISKS` exclusively because (a) the R5 acceptance engine *was* in fact modified (invalidating the R4 stability premise), and (b) the local signer still contains a non-blocking diagnostic gap where it will locally bless `review_bundle/` directories containing a mix of legal files and illegal symlinks, requiring the CI's git-blob checks to catch and reject the symlinks. Since this remains fail-closed in CI, it does not prevent canonical binding.
I've provided the detailed markdown audit report above, successfully matching all requested checks and validating against the severity taxonomy you've outlined. The combined commits represent a solid closure to the symlink directory traversals discovered in the independent audit, and safely fail closed in the CI acceptance pipeline.

Let me know if you need any follow-up verification on the trust bounds or if you're ready to proceed with generating the canonical proof successor bundle!
