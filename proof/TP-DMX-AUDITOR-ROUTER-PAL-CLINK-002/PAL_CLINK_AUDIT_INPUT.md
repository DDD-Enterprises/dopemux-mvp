# PAL Clink Audit Input

Packet: `TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002`

Requested host-side action for a future handoff:

1. Run PAL MCP clink from a persistent-auth host environment using `claude-audit` or `gemini-audit`.
2. Use role `codereviewer`.
3. Review this branch as a partial bootstrap:
   - missing auditor-router baseline on `origin/main`
   - PAL clink bridge-tier classification by static config inspection
   - schema and docs updates
   - proof status downgrade to `PASS_WITH_BLOCKERS`
4. Save raw ToolOutput JSON as `PAL_CLINK_AUDIT_OUTPUT.json`.
5. Normalize the output into `AUDITOR_REPORT.md`.

Do not treat router route selection as an audit verdict.
