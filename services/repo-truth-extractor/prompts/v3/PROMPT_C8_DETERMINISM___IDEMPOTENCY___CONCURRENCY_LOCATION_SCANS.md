OUTPUTS:
- DETERMINISM_RISK_LOCATIONS.json
- IDEMPOTENCY_RISK_LOCATIONS.json
- CONCURRENCY_RISK_LOCATIONS.json
- SECRETS_RISK_LOCATIONS.json

Goal: DETERMINISM_RISK_LOCATIONS.json, IDEMPOTENCY_RISK_LOCATIONS.json, CONCURRENCY_RISK_LOCATIONS.json, SECRETS_RISK_LOCATIONS.json

Prompt:
- Scan for:
  - Non-deterministic functions (random, time, uuid) in critical paths.
  - Concurrency risks (global state mutation, race conditions).
  - Idempotency risks (DB writes without keys, retries with side effects).
  - Secrets patterns (APi keys, tokens).
```markdown

OUTPUTS:
	•	CONCURRENCY_RISK_LOCATIONS.json
	•	DETERMINISM_RISK_LOCATIONS.json
	•	IDEMPOTENCY_RISK_LOCATIONS.json
	•	SECRETS_RISK_LOCATIONS.json
```
