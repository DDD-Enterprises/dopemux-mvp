# Excluded loose artifacts

Source directory: `/tmp/dmx-g0-lite-pr1274-audit`

Included under direct-route names:

- `PAL_CLINK_AUDIT_INPUT.md` as `DIRECT_CLAUDE_AUDIT_PROMPT.md`; prompt bytes
  were reused by direct Claude Code CLI, while PAL/clink execution was not.
- `CANDIDATE_UNIFIED_DIFF.txt`.
- `CANDIDATE_CHANGED_FILES.txt`.
- `INSTRUCTION_LIKE_CONTENT.json`.

Excluded because they describe the rejected, noncontrolling CI PAL/clink route:

- `AUDITOR_REPORT.md`.
- `AUDITOR_ROUTE.json`.
- `LOCAL_AUDIT_ATTESTATION.json`.
- `PAL_CLINK_AUDIT_OUTPUT.json`.
- `PAL_CLINK_AUDIT_RUNNER_OUTPUT.json`.
- `PROOF.json`.
- `ROUTE_PROBE_OUTPUTS.json`.

Direct Claude stdout was not captured as a loose file. Its structured result,
route custody, exact invocation, model disclosures, verdict, findings, and risks
are preserved in `DIRECT_CLAUDE_AUDIT_RESULT.json`,
`DIRECT_CLAUDE_AUDIT_CUSTODY.json`, canonical `PROOF.json`, and
`AUDITOR_REPORT.md`.
