# Adversarial corpus — 0007T

Fixtures under `tests/fixtures/dcp/trusted_input/`:
- forged_attested.json
- forged_route_decision.json
- boolean_string_coercion.json
- empty.json

All assert `is_execution_eligible` is False and serialized trust is refused.
No mutation adapter enabled. Residual: historical `RouteDecision.is_runnable` may still accept forged ALLOWED+CLEAR+OPERATOR.
