# Prompt F (v2): Determinism + concurrency + idempotency risk scan

**Outputs:** `DETERMINISM_RISKS.json`

---

## TASK

Produce ONE JSON file: `DETERMINISM_RISKS.json`.

## TARGET

`/Users/hue/code/dopemux-mvp` WORKING TREE.

## Scan for and emit one item per hit:

### A) risk_determinism:
- `random.*`, `secrets.choice`
- `uuid.uuid4`/`uuid1`
- `datetime.now`/`time.time`/`time.monotonic`
- dict/set iteration used to build outputs/hashes without sorting

### B) risk_concurrency:
- async/await pipelines
- threads/processes/queues
- background tasks
- retries/backoff with jitter or no cap

### C) risk_idempotency:
- UPDATE/DELETE on append-only evidence tables (if identifiable)
- inserts without idempotency keys (detect via function names and SQL snippets only)
- non-transactional multi-step pipelines

## Emit items:
- `domain=risk_determinism|risk_concurrency|risk_idempotency`
- `kind=risk`
- `name=<matched function or token>`
- `strings` include exact matched token and a 2-line excerpt.

## RULES

- No severity scores.
- No "this is bad".
- Universal schema, deterministic sorting.
