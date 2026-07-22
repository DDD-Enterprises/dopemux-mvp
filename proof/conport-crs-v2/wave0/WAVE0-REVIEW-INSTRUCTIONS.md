# ConPort CRS v2 Wave 1 Review Instructions

Review exact ADR digests and base-to-reviewed-commit patch in this package. Reviewer must be independent from Wave 0 author.

Return `ACCEPTED`, `REJECTED`, or `CHANGES_REQUIRED`. Acceptance applies only to exact packaged digests and does not authorize implementation, runtime mutation, merge, or Wave 2+ execution.

Explicitly answer all thirteen questions in `synthesis/CONPORT-ADR-CHANGE-SET.md` section 7. Verify target ADR remains proposed in Wave 0, existing accepted ADRs remain effective, proposal blocks do not silently amend accepted authority, index reflects file-authoritative current status, and all changed paths remain documentation/proof only.

Custody checks:

1. Verify package SHA-256 using adjacent `.sha256` file.
2. Verify every entry against `MANIFEST.json`.
3. Verify candidate ZIP identity recorded in `wave0-proof/WAVE0-SOURCE-CUSTODY.json`.
4. Verify reviewed ADR commit is `a5b9006aa3f5a95f81e4bab324931ade71ee8b31` over baseline `5a9f8f7b5d4a03be323723a92baf3c4e162d5b65`.
5. Treat `UNKNOWN` and `NOT_RUN` as unresolved; do not promote them to PASS.

Custody re-review may be limited to bundle, ancestry, tree, patch, and packaged-byte verification because ADR content remains pinned to reviewed commit `a5b9006aa3f5a95f81e4bab324931ade71ee8b31`. Follow `wave0-proof/WAVE0-CUSTODY-VERIFY.md`; verify every check in `wave0-proof/WAVE0-GIT-CUSTODY.json` and every row in `wave0-proof/WAVE0-GIT-CUSTODY-FILES.json`.
