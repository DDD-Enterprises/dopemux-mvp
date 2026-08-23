# Embedded Audit Report

- Packet: `TP-DMX-STEWARD-DEPENDABOT-ACTOR-1207-001` PR 1258
- Audited content head: `c70d442d697642a1606f58eb4130cf83ebc25815`
- Auditor: agy gemini-3.1-pro-high / session `dd3a62b2-8586-48aa-b691-cf6c4ace6c89`
- Verdict: **PASS**

## Summary
The PR correctly restricts the 'app/' prefix normalization exclusively for 'dependabot' variants ('app/dependabot' and 'app/dependabot[bot]') while leaving any other login untouched. This correctly prevents spoofing of human accounts (e.g. 'app/hu3mann'). The tests prove both positive normalization for dependabot and rejection of app-prefixed human/unknown logins. The change is safe, has no scope creep, and leaks no secrets.

## Findings
- **Strict app prefix matching requires code changes for new apps** (`hardcoded-app-prefix`, INFO, ACCEPTED_RISK): The implementation strictly hardcodes 'app/dependabot', meaning any future legitimate GitHub apps will require explicit code changes in _normalize_bot_login rather than just roster additions. This is an intended consequence of the fail-closed security posture.

## Remaining risks
- Future GitHub Apps with the 'app/' prefix will fail-closed and require manual PRs to update the _normalize_bot_login strict checking.
