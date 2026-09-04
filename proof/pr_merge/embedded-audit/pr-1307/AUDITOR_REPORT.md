# Embedded Audit Report — PR #1307

## PR Metadata
- **PR**: #1307 (C0-R2 Schema Publication)
- **Head SHA**: `e6a1ce530b6f061d0ef1da06af9c21d16e52eae4`
- **Base**: main (`76b446c1fd6eec3f75d026980101a90fc49b3d89`)
- **Packet**: TP-DMX-C0-R2-SCHEMA-PUBLICATION-001

## Auditor
- **Tool**: opencode-cli
- **Model**: kimi-k3 (via cheaper-inference)
- **Invocation**: `opencode run --model cheaper-inference/kimi-k3 --message <bounded audit prompt>`
- **Mode**: Read-only, no tools, no filesystem access

## Deterministic Pre-Checks (script-verified)
- 10/10 published schemas: valid JSON, valid JSON-Schema Draft-07
- 167 external $ref links: 0 dangling references
- 10/10 registered in manifest.json as DESIGN_ONLY/L0
- Contract tests: 126/126 PASS
- `git diff --check`: clean

## Model Audit Verdict: PASS_WITH_RISKS

### Findings
| ID | Severity | Status | Body |
|---|---|---|---|
| F-01 | INFO | RESOLVED | Structural consistency holds across all 10 published schemas. |
| F-02 | LOW | ACCEPTED_RISK | governed_execution_receipt ref count (33) is highest; warrants future re-check. |
| F-03 | INFO | RESOLVED | DESIGN_ONLY/L0 registration consistent with ratification publication. |
| F-04 | LOW | ACCEPTED_RISK | macro_execution_authority_ref_v2 is the only versioned name; v1 status UNKNOWN. |

### Remaining Risks
1. All 10 schemas remain design-only; runtime producer/consumer validation is NOT_RUN.
2. governed_execution_receipt ref growth should be monitored.
3. macro_execution_authority_ref_v1 status remains UNKNOWN.

## Attestation
This audit was performed independently by the opencode-cli/kimi-k3 route via cheaper-inference.
The deterministic pre-checks were verified by repo scripts. The model assessment was performed
over pre-gathered evidence with no filesystem access (pure reasoning).
