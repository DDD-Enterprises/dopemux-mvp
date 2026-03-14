---
id: REF-EXTRACTION-V5-UI
title: v5 Extractor UI — Live Output Reference
type: reference
owner: '@hu3mann'
date: '2026-03-14'
author: '@copilot'
prelude: Reference for the v5 extractor UI class live output system including partition display, retry events, escalation alerts, and provider color scheme.
last_review: '2026-03-14'
next_review: '2026-06-14'
graph_metadata:
  node_type: DocPage
  impact: medium
  relates_to:
    - services/repo-truth-extractor/run_extraction_v5.py
---
# v5 Extractor UI — Live Output Reference

The `UI` class in `run_extraction_v5.py` drives all terminal output during an
extraction run. This document covers the live display features added in the
March 2026 output overhaul.

## Output modes

| Mode | When | Behavior |
|------|------|----------|
| `rich` | Force Rich (e.g. `--ui-mode rich`) | Rich panels, spinners, colors |
| `auto` (default) | stdout is a TTY | Rich if TTY, plain otherwise |
| `plain` | stdout is not a TTY or piped | Plain `KEY=value` log lines |
| `quiet` | `--quiet` flag | Only errors; no progress output |

## Per-partition LLM display

Every partition logs which provider/model it is using before the LLM call:

```
  ▶ A:A0__A A_P0001 → openai/gpt-4.1-mini
  ▶ A:A0__A A_P0002 → anthropic/claude-3-haiku-20240307
```

Emitted by `UI.partition_start_event()`. Also written to:
- `telemetry/terminal_timeline.jsonl` as `{"type": "partition_start", ...}`

Plain mode equivalent:
```
PARTITION_START phase=A step=A0__A partition=A_P0001 provider=openai model=gpt-4.1-mini
```

## Retry events

When a partition's LLM call fails and retries, the retry is shown live before
the backoff sleep:

```
  ⟳ RETRY A:A0__A A_P0001 attempt=2/3 openai/gpt-4.1-mini status=429 reason=rate_limit wait=2.0s
  ⟳ RETRY A:A0__A A_P0001 attempt=3/3 openai/gpt-4.1-mini status=503 reason=server_error wait=4.0s
```

Emitted by `UI.retry_event()`. Also written to timeline as `{"type": "partition_retry", ...}`.

Plain mode equivalent:
```
PARTITION_RETRY phase=A step=A0__A partition=A_P0001 attempt=2/3 provider=openai model=gpt-4.1-mini status_code=429 failure_type=rate_limit delay=2.0s
```

### Retry callback wiring

`call_llm()` accepts `retry_callback: Optional[Callable] = None`. The partition
worker passes a lambda that calls `ui.retry_event(...)` for each retry. Existing
callers that don't pass `retry_callback` are unaffected (defaults to `None`).

## Escalation alerts

When a partition exhausts its primary route and escalates to a fallback:

```
  🔀 ESCALATE A:A0__A A_P0001 hop=1 openai/gpt-4.1 → anthropic/claude-3-5-sonnet reason=max_retries_exceeded
```

Emitted by `UI.escalation_event()`. Rich branch uses:
- Yellow `🔀 ESCALATE` prefix
- Red for the source route
- Cyan for the destination route
- Italic yellow for the reason

## Step progress bar

Each step shows a progress bar with aggregate counters:

```
⠙ A:A0__A [extract] openai/gpt-4.1-mini ━━━━━━━━━━━╸  42/100 0:00:18 ok=38 fail=2 skip=2 retry=4 esc=0 repair=0 sidefill=0 soft_gate=0
```

Updated by `UI.partition_result()` after each partition completes.

## Failure spotlight

When a partition fails after all retries, the failure is printed with its full
retry trace:

```
STEP_FAILURE phase=A step=A0__A partition=A_P0001 class=provider reason=rate_limit route=openai/gpt-4.1 ...
    retry trace (3 attempts):
      [1] status=429 type=rate_limit → wait 1.0s
      [2] status=429 type=rate_limit → wait 2.0s
      [3] status=503 type=server_error
```

Pass `retry_trace` from `request_meta["retry_trace"]` to `UI.failure_spotlight()`:

```python
ui.failure_spotlight(
    phase=phase,
    step_id=step_id,
    partition_id=partition_id,
    failure_class=failure_class,
    reason=reason,
    route=route,
    retry_trace=request_meta.get("retry_trace"),  # optional
)
```

## Provider color scheme

| Provider | Rich color |
|----------|-----------|
| `openai` | `bold green` |
| `anthropic` | `bold magenta` |
| `gemini` | `bold blue` |
| `xai` | `bold yellow` |
| `openrouter` | `bold cyan` |
| `mistral` | `bold orange3` |
| *(unknown)* | `bold white` |

Used by `UI._provider_color(provider)` and applied in `partition_start_event`,
`retry_event`, and `escalation_event`.

## JSONL telemetry events

All UI events are written to `<run_root>/telemetry/terminal_timeline.jsonl`.
New event types added in this release:

| `type` | Emitted by | Key fields |
|--------|-----------|-----------|
| `partition_start` | `partition_start_event()` | `phase`, `step`, `partition_id`, `provider`, `model_id` |
| `partition_retry` | `retry_event()` | `attempt`, `max_attempts`, `status_code`, `failure_type`, `delay_seconds` |

Existing events (`step_start`, `step_done`, `escalation`, `step_failure_spotlight`,
etc.) are unchanged.

## Thread safety

The `UI` class maintains `_active_partitions: Dict[str, Dict]` guarded by
`_partitions_lock: threading.Lock`. All reads and writes to `_active_partitions`
go through the lock, making it safe for parallel partition workers.

## API summary

```python
class UI:
    # New in March 2026
    def partition_start_event(self, phase, step_id, partition_id, provider, model_id) -> None
    def retry_event(self, phase, step_id, partition_id, attempt, max_attempts,
                    provider, model_id, status_code, failure_type, delay_seconds) -> None
    def _provider_color(self, provider: str) -> str

    # Enhanced in March 2026
    def escalation_event(self, phase, step_id, partition_id, reason,
                         from_route, to_route, hop) -> None
    def failure_spotlight(self, *, phase, step_id, partition_id, failure_class,
                          reason, route, ..., retry_trace=None, mode="full") -> None

# Enhanced in March 2026
def call_llm(..., retry_callback: Optional[Callable] = None) -> Dict[str, Any]
```
