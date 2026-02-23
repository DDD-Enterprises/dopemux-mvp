---
id: TP-PM-ARCH-04B
title: 'PM Plane Phase 4B: Canonical pm.* Events + Adapters (no types.py unless forced)'
type: explanation
owner: '@hu3mann'
model: gpt-5.3-codex
branch: codex/pm-plane/arch-04b
depends_on:
- TP-PM-ARCH-04A
date: '2026-02-12'
status: ready
author: '@hu3mann'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: 'PM Plane Phase 4B: Canonical pm.* Events + Adapters (no types.py unless
  forced) (explanation) for dopemux documentation and developer workflows.'
---
# TP-PM-ARCH-04B
## Canonical pm.* Events + Adapters (Opus-locked rules)

### Objective
Introduce a **canonical pm.* event envelope** and **pure adapters** that convert existing PM-ish event surfaces into that envelope, while **avoiding edits** to `src/dopemux/events/types.py` unless tests prove it is required.

Publish into the existing bus by constructing a plain event dict:
- `namespace = "pm.<...>"`
- `payload = {"envelope": <pm_envelope_dict>}`

No EventBus imports inside `dopemux.pm.*`.

---

## Scope

### IN
- `dopemux.pm.events`
- `PMEventType` (exact list below)
- `canonical_json()` stable serializer
- `sha256_hex()` helper
- `create_pm_event(...)` factory producing an envelope dict
- `dopemux.pm.adapters`
- `taskmaster_event_to_pm(event_type: str, data: dict, source: str="taskmaster") -> dict`
- `orchestrator_event_to_pm(coord_event_like, source: str="task-orchestrator") -> dict`
- `pm_to_bus_event(envelope: dict) -> dict` (returns `{namespace, payload}`)
- Unit tests for determinism, mapping, breadcrumbs, and Trinity boundary

### OUT
- persistence backend
- ConPort linkage, decision logging
- service wiring under `services/`
- Leantime sync
- moving service-level tests
- any refactors to existing event systems

---

## Hard Invariants (binding)

### I1. Event ID determinism
`event_id = sha256(canonical_json(envelope_core))`

`canonical_json` rules:
- JSON keys sorted
- datetime serialized as UTC ISO8601 with trailing `Z`
- no whitespace variance
- stable list ordering (do not sort lists, preserve as provided)

### I2. Task ID policy (Opus Decision #1)
Derive canonical `task_id` by:
1) If source provides stable source_task_id:
- `task_id = sha256(f"{source}:{source_task_id}")`
2) Else fallback:
- `task_id = sha256(f"{source}:{norm(title)}:{norm(description)}")`

`norm(x)`:
- lowercase
- strip
- collapse internal whitespace to single spaces

### I3. Idempotency location
Idempotency is NOT stored on PMTask. It is only carried on event envelope fields:
- `idempotency_key` is an envelope field
- Replays with identical inputs must produce identical `event_id`

### I4. Trinity boundary
`src/dopemux/pm/*` must not import:
- `services.*`
- `dopemux.mcp`
- `dopemux.event_bus`

### I5. Lossy mappings must be explicit
If you cannot preserve semantics, include breadcrumbs:
- `payload["dialect_event_type"]`
- `payload["dialect_status"]` (when applicable)
- `payload["mapping_reason"]` (string)

### I6. No types.py edit unless forced
Default path: do NOT touch `src/dopemux/events/types.py`.
Only edit if tests demonstrate the bus requires strict class instances.

---

## Canonical Event Types (exact set)
- `pm.task.created`
- `pm.task.updated`
- `pm.task.status_changed`
- `pm.task.blocked`
- `pm.task.completed`
- `pm.decision.linked`
- `pm.sync.requested`
- `pm.sync.succeeded`
- `pm.sync.failed`

---

## Files to Create / Edit

### NEW
1) `src/dopemux/pm/events.py`
2) `src/dopemux/pm/adapters.py`

### NEW tests
1) `tests/unit/pm/test_pm_events.py`
2) `tests/unit/pm/test_pm_adapters.py`

### OPTIONAL (only if forced)
1) `src/dopemux/events/types.py`

---

## Implementation Notes

### `src/dopemux/pm/events.py`
Must include:
- `PM_EVENT_TYPES` constant list OR Enum-like class (tests must enforce exact 9 values)
- `canonical_json(obj) -> str`
- `sha256_hex(s: str) -> str`
- `event_id_for_envelope_core(core: dict) -> str`
- `create_pm_event(...) -> dict` that returns:

Envelope dict fields:
- `event_id: str`
- `event_type: str`
- `ts_utc: str` (UTC ISO8601 with Z, or datetime that canonical_json serializes to that)
- `idempotency_key: str`
- `source: str`
- `task_id: str`
- `payload: dict`

### `src/dopemux/pm/adapters.py`
Must include:
- `normalize_text(s: str) -> str`
- `canonical_task_id(source: str, source_task_id: str|None, title: str|None, description: str|None) -> str`
- `taskmaster_event_to_pm(...)` mappings:
- `"taskmaster.task.created"` -> `pm.task.created`
- `"taskmaster.task.status_updated"` -> `pm.task.status_changed`
- `"taskmaster.task.completed"` -> `pm.task.completed`
- include dialect breadcrumbs in payload
- `orchestrator_event_to_pm(coord_event_like, ...)` duck-typed support:
- event type in: `.event_type` or `.type` or `["event_type"]` or `["type"]`
- task id in: `.task_id` or `["task_id"]` or nested `.payload/.data`
- map common names:
- `task_created` -> `pm.task.created`
- `task_updated` -> `pm.task.updated`
- `task_completed` -> `pm.task.completed`
- unknown types degrade to `pm.task.updated` with `mapping_reason`
- `pm_to_bus_event(envelope)` returns:
- `{"namespace": envelope["event_type"], "payload": {"envelope": envelope}}`
- namespace must start with `pm.`

---

## Tests

### `tests/unit/pm/test_pm_events.py`
Must test:
1) PM event types are exactly the 9 values, no more, no less
2) `canonical_json` is stable (dict key order changes do not change output)
3) `create_pm_event` deterministic:
- same inputs -> same `event_id`
4) `event_id` changes when payload changes
5) datetime formatting is stable and includes `Z`

### `tests/unit/pm/test_pm_adapters.py`
Must test:
1) taskmaster mappings cover created, status_updated, completed
2) orchestrator mappings cover task_created, task_updated, task_completed
3) unknown orchestrator event produces pm.task.updated and includes `mapping_reason`
4) dialect breadcrumbs are present for lossy mappings
5) task id policy:
- when source_task_id present, created_at never influences
- fallback uses normalized title + description

---

## Pre-flight Commands (paste outputs)
```bash
git checkout codex/pm-plane/arch-04a
git status --porcelain

git checkout -b codex/pm-plane/arch-04b
git status --porcelain

python -m pytest tests/unit/pm/ --collect-only | tail -n 30
```

---

Execution Commands (paste outputs)

```bash
python -m pytest tests/unit/pm/test_pm_events.py tests/unit/pm/test_pm_adapters.py -v --tb=short
python -m pytest tests/unit/pm/ -v --tb=short

python -c "from dopemux.pm.events import create_pm_event; print('OK')"
python -c "from dopemux.pm.adapters import taskmaster_event_to_pm, orchestrator_event_to_pm, pm_to_bus_event; print('OK')"
```

Trinity Boundary Quick Check (paste output)

```bash
python - <<'PY'
import ast, pathlib
bad=[]
for p in pathlib.Path("src/dopemux/pm").rglob("*.py"):
    t=ast.parse(p.read_text())
    for n in ast.walk(t):
        if isinstance(n,(ast.Import,ast.ImportFrom)):
            mod = (n.module or "") if isinstance(n,ast.ImportFrom) else " ".join(a.name for a in n.names)
            if any(x in mod for x in ["services.", "dopemux.mcp", "dopemux.event_bus"]):
                bad.append((str(p), mod))
print("OK" if not bad else "BAD")
for row in bad:
    print(row)
PY
```

---

Commit Plan (sequenced)

Commit B1 (code)

Message:
- `pm: phase4 packet b pm.* event envelope + adapters (deterministic ids)`

Commit B2 (tests)

Message:
- `test(pm): add deterministic pm.* envelope + adapter mapping tests`

If small and clean, squash into one commit, but default is two commits.

After commits:

```bash
git status --porcelain
git log --oneline -n 3
git push -u origin codex/pm-plane/arch-04b
```

---

Acceptance Criteria
1. PM event type set is exactly the 9 canonical values
1. event_id deterministic with canonical_json hashing
1. taskmaster mappings cover: created, status_updated, completed
1. orchestrator mappings cover: task_created, task_updated, task_completed, plus graceful unknown handling
1. pm_to_bus_event() returns dict with namespace starting pm.
1. No edits to src/dopemux/events/types.py unless forced by evidence from failing tests
1. pytest tests/unit/pm/ passes with 0 failures

---

Stop Conditions
- STOP if implementing adapters requires importing services/* types
- STOP if Packet A task id policy must change again
- STOP if the bus requires strict event class instances (provide failure output and the exact consumer expectation)
- STOP if baseline pytest tests/unit/pm/ fails before any Packet B changes

---

Rollback

```bash
git reset --hard HEAD
git checkout codex/pm-plane/arch-04a

rm -f src/dopemux/pm/events.py src/dopemux/pm/adapters.py
rm -f tests/unit/pm/test_pm_events.py tests/unit/pm/test_pm_adapters.py
```

### Tiny slicing note (to reduce Opus usage)
Run **implementation** with `gpt-5.3-codex`, then only bring Opus back for a **5-minute audit pass** on:
- canonical_json determinism
- task_id derivation correctness
- lossy mapping breadcrumbs
- accidental Trinity leaks
