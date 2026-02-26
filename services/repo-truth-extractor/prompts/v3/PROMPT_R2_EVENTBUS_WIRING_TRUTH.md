OUTPUTS:
- EVENTBUS_WIRING_TRUTH.md

Goal: EVENTBUS_WIRING_TRUTH.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce event bus wiring truth.

MUST INCLUDE:
- Event bus implementations/adapters
- Event names/topics (literal where evidenced)
- Producer mapping: event -> producers
- Consumer mapping: event -> handlers/subscribers
- Dispatch paths from producer call to consumer execution
- Control-plane impacts on routing

OUTPUT TABLE:
Event | Producers (CODE refs) | Consumers (CODE refs) | Adapter/Bus (CODE refs)

RULES:
- If event name is computed, mark as (computed) with evidence.
- No guessing missing event names.
