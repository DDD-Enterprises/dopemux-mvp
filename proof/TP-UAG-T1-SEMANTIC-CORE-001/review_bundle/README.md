# Review Bundle — TP-UAG-T1-SEMANTIC-CORE-001

Independent Claude Code (Sonnet) embedded-audit evidence for the UAG
semantic-core branch at HEAD
`06d515dfd6c968d4a8a0c379f71f38998a62b49f` (PR #1309).

## Contents

| File | Purpose |
|------|---------|
| `audit_prompt.txt` | The independent auditor prompt (trusted task + authority framing, repo/PR/head binding). |
| `auditor_raw_output.txt` | Raw structured output of the independent Claude Code (Sonnet) session: verdict PASS_WITH_RISKS, closure corroboration with exact file/line references, findings AUD-01/AUD-02, validation_status NOT_RUN (static analysis only). |
| `audit_diff.txt` | Unified diff of the audited branch surface that was reviewed. |
| `changed_files.txt` | List of changed source files in the audit scope. |
| `instruction_like_scan.json` | Prompt-injection-style content scan result (`detected: false`). |
| `README.md` | This index. |

## Notes

- The audit was performed by a separate Claude Code session (Tier-1 route #2,
  Sonnet), not by the implementing agent, satisfying the independence
  requirement.
- Verdict is **PASS_WITH_RISKS**: hardening closures F-1..F-4, F-7, F-8
  corroborated; two LOW findings (AUD-01 `is_sha256` trailing-newline gap,
  AUD-02 tautological test assertion) remain OPEN and are carried in
  `remaining_risks` / `residual_risks`.
- Deterministic suites (72 unit / 187 contract / ruff / diff-check /
  change-contract) were run by the implementer; the auditor ran static analysis
  only (tools/MCP-disabled).
- Signed local attestation (OpenSSH namespace `dopemux-embedded-audit`) binds
  these verified bytes to PR #1309 at head `06d515dfd`.
