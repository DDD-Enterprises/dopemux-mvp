# Embedded Audit Report

## Identity

- Packet: `TP-DMX-MCP-DOCTOR-FORMULA-RESERVED-001`
- PR: 1256
- Audited content head: `806a9a73174a58a53dcdaa2a0b04627a16568f23`
- Implementer: Grok 4.6 (not the auditor)
- Requested auditor model: `gemini-3.1-pro-high`
- Provider-attested model: `gemini-3.1-pro-high` (structured `model_used`; envelope SUCCESS; no fallback)
- Schema `auditor_model`: `gemini-3.1-pro-high`
- Auditor tool: `agy`
- Session/conversation: `0f6e6c46-52be-4d0e-abcb-ca832d81ca89`
- Verdict: **PASS**

## Findings

1. **F1 INFO RESOLVED** — Severity matrix applied correctly to port collisions. Formula reserved-port collisions are safely neutralized to WARN if explicit configured envrc overrides do not collide. Configured collisions remain FAIL.
1. **F2 INFO RESOLVED** — Compose placeholder correctly isolated. The DOPECON_BRIDGE_TOKEN dummy placeholder allows compose parse but is excluded from runtime mcp.env generation. Explicit task-orchestrator start strictly requires a real token.
1. **F3 INFO RESOLVED** — Foreign compose parsing hazard bypassed. Foreign compose.yml files are properly ignored by doctor when --repo specifies a different path, preventing false alarms.

## Remaining risks

- none

## Summary

The embedded audit verified the implementation of TP-DMX-MCP-DOCTOR-FORMULA-RESERVED-001. The reserved port severity rules correctly distinguish between pure-formula and configured ports. The DOPECON_BRIDGE_TOKEN interpolation placeholder is properly used and safely excluded from mcp.env. Foreign compose.yml parsing hazards are successfully bypassed when explicitly setting the repo path. Explicit compose boot for task-orchestrator correctly fails closed without a true token. The unit tests provide full coverage for these intent criteria. No secrets, scope creep, or out-of-scope changes were identified.
