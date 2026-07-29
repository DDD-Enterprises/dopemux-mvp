# Trusted Input Design — DMX-DCP-MODEL-ROUTING-MVP-0007I

## Goal

Add an auditable **capability** object so raw / restored routing inputs cannot
confer mutation or runner execution eligibility.

## Design

| Element | Behavior |
|---|---|
| `TrustedInputCapability` | Frozen dataclass; requires private module mint token |
| `is_execution_eligible(source, capability=None)` | Fail-closed gate |
| `active_trusted_adapters()` | Always `[]` in this packet |
| `refuse_serialized_trust` | Rejects attested/trusted/adapter_id markers |
| `capability_from_any` | Always raises |

## Explicit non-claims

- `active_trusted_adapters: []`
- `serialized_trust_supported: false`
- `raw_input_execution_eligible: false`
- `runtime_execution_added: false`
- Python privacy is **not** cryptographic isolation
- `RouteDecision.is_runnable` is **not** rewritten (out of allowlist); new consumers must use `is_execution_eligible`
- No mutation-authorized adapter is enabled (deferred to 0007A)

## Why is_runnable was not changed

NEXT-TRANCHE-001 allowlist forbids `routing_model.py` / `routing_classifier.py` /
`dcp_commands.py`. Closing the historical `from_dict` → `is_runnable` forge path
requires 0007T/0007A (or R2 authorized wider scope) after this capability lands.
