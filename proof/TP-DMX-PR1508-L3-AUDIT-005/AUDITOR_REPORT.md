# Auditor report

Packet: `TP-DMX-PR1508-L3-AUDIT-005`
Pull request: 1508
Audited content: `a2c1cb7c3a58600c272fe67ee71f29f811404ffc`
Auditor: `opencode-cli` / `kimi-k3`
Session: `ses_e32e0d10fffeC4qLwu6sHyi6HV`
Verdict: `PASS_WITH_RISKS`

This commit changes `.github/workflows/docs.yml` only. A merge-group run now checks `merge_group.base_sha` through `github.sha`. It no longer runs `pre-commit --all-files` when `github.event.before` is empty.

## Findings

F1 MEDIUM ACCEPTED_RISK. Push events still fall back to `pre-commit --all-files` when `github.event.before` is missing.

F2 MEDIUM ACCEPTED_RISK. The merge-group job exits 1 if `merge_group.base_sha` is not in the checkout. The workflow checks out with `fetch-depth: 0`.

F3 LOW ACCEPTED_RISK. Merge-group hooks no longer scan untouched files.

F4 LOW ACCEPTED_RISK. A missing base commit and a hook failure both fail the same job.

F5 INFO ACCEPTED_RISK. A multi-pull-request merge group checks the combined range.

No BLOCKING finding is open.
