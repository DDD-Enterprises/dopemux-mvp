# Embedded Audit Report — PR #1182

- **Packet**: TP-REPLAN-BASELINE-1182-REPAIR-001
- **Content head audited**: `73563a4aa92bd37b77c61ef52ecf1c52b011bcf6`
- **Generated**: 2026-08-03T01:31:09Z
- **Supervisor exception**: AUTHORIZE_CODEX_AS_FORMAL_AUDITOR_EXCEPTION
- **Real auditor**: codex-cli 0.146.0 / gpt-5.5 / session `019fc539-2385-77a2-86b2-b7ca80f7d84f`
- **Schema carriers** (allOf only, not real auditor): claude-code-cli / sonnet
- **Status**: PASS_WITH_RISKS

## Findings
1. **RESOLVED** Re-pin after main merge invalidated prior b738 proof (`delta_touches_code`).
2. **RESOLVED** Load-plan BLOCKS edge claim 23→22.
3. **ACCEPTED_RISK** Codex formal-auditor exception / schema carriers.
4. **RESOLVED** Deterministic 539-item export invariants hold.

## Residual risks
- Wave 0 operator-controlled.
- Local-signed attestation path (CI Claude may be unprovisioned).
