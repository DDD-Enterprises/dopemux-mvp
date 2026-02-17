# EXECUTABLE PROMPT: F - Determinism + Concurrency + Idempotency Risk Scan

---

## YOUR ROLE

You are a **mechanical pattern scanner**. Find code patterns that pose determinism, concurrency, or idempotency risks. Report exact matches — no severity judgments, no "this is bad."

---

## TASK

Scan the provided Python files and produce ONE JSON file:
1. `DETERMINISM_RISKS.json`

---

## OUTPUT: DETERMINISM_RISKS.json

For each pattern match, emit:

```json
{
  "path": "services/chronicle/events.py",
  "line_range": [45, 45],
  "domain": "risk_determinism",
  "kind": "risk",
  "risk_type": "nondeterministic_id",
  "name": "uuid.uuid4",
  "matched_text": "event_id = str(uuid.uuid4())",
  "context_before": "def create_event(event_type, payload):",
  "context_after": "return EventEnvelope(event_id=event_id, ...)"
}
```

---

## SCAN PATTERNS

### A) risk_determinism

| Pattern                                                 | risk_type               |
| ------------------------------------------------------- | ----------------------- |
| `random.*` / `secrets.choice` / `secrets.token_*`       | `randomness`            |
| `uuid.uuid4()` / `uuid.uuid1()`                         | `nondeterministic_id`   |
| `datetime.now()` / `time.time()` / `time.monotonic()`   | `nondeterministic_time` |
| `dict(...)` / `set(...)` iteration used to build output | `unordered_iteration`   |
| `hash(...)` on mutable objects                          | `unstable_hash`         |

### B) risk_concurrency

| Pattern                                           | risk_type         |
| ------------------------------------------------- | ----------------- |
| `async def` / `await` / `asyncio.*`               | `async_pipeline`  |
| `threading.Thread` / `multiprocessing.Process`    | `thread_process`  |
| `concurrent.futures.*`                            | `thread_pool`     |
| `BackgroundTask` / `background_tasks.add_task`    | `background_task` |
| Retry/backoff with `jitter` or no max_retries cap | `unbounded_retry` |

### C) risk_idempotency

| Pattern                                                       | risk_type                    |
| ------------------------------------------------------------- | ---------------------------- |
| `UPDATE ... SET` / `DELETE FROM` on evidence/audit tables     | `destructive_write`          |
| `INSERT INTO` without `ON CONFLICT` / without idempotency key | `non_idempotent_insert`      |
| Multi-step DB operations without transaction wrapper          | `non_transactional_pipeline` |
| `cursor.executemany` without dedup                            | `batch_without_dedup`        |

---

## FIELD DEFINITIONS

- **matched_text**: The exact line of code that matched (≤ 120 chars)
- **context_before**: 1 line before the match (function signature, etc.)
- **context_after**: 1 line after the match
- **domain**: One of `risk_determinism`, `risk_concurrency`, `risk_idempotency`

---

## HARD RULES

1. **No severity scores** — do not rate risks
2. **No recommendations** — do not say "should" or "fix"
3. **Exact match only** — report the literal code pattern
4. **JSON only** — no markdown, no prose
5. **ASCII only**
6. **Deterministic sorting** — by domain, then path, then line_range
7. **path + line_range required** on every item

---

## OUTPUT FORMAT

```json
{
  "artifact_type": "DETERMINISM_RISKS",
  "generated_at_utc": "2026-02-15T22:00:00Z",
  "source_artifact": "WORKING_TREE",
  "items": [...]
}
```

---

## BEGIN EXTRACTION

Process the provided context files and produce the JSON output now.
