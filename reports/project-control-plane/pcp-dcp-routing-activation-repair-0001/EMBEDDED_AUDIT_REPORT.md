# Embedded Audit Report

- **auditor_tool:** code-reviewer subagent (independent session)
- **auditor_model:** composer-2.5-fast
- **invocation:** META-TP-DMX-PCP-DCP-ROUTING-ACTIVATION-REPAIR-0001 slice 8
- **exit_code:** 0
- **auditor_verdict:** PASS_WITH_RISKS

## Findings (8 questions)

| Question | Verdict |
|---|---|
| Unsigned READY reach writer? | PASS — `NoTrustedIssuerVerifier` blocks before writer |
| Writer without SOURCE authority entry? | PASS — `FailClosedAuthorityBinding` / `binding_from_entries` |
| OpenRouter free/private SELECTED? | PASS (contract) — schema `allOf` forbids |
| SELECTED unknown provider/model/runner? | PASS (contract) — schema forbids |
| DCP proof family missing silently? | PASS — manifest mapping + tests |
| PR Steward READY with missing evidence? | PASS — `INCOMPLETE_INTAKE` + schema gates |
| `dopemux.pcp` packaged/importable? | PASS — wheel test + pyproject packages |
| Top-level CLI inert for live writes? | PASS — no bridge/mutate commands |

## Fixes applied during audit cycle

- Vendored PCP schemas for wheel import (`dopemux.pcp` / `dopemux.pcp.bridge` package-data)
- Lazy schema loading in `fastapi_bridge.py` and `exporter.py`

## Remaining risks

- DCP route-decision constraints are contract-level; runtime routers may not validate unless integrated
- Production activation still requires explicit trusted verifier + authority map injection