# TP-MCF-002 — Transcript Ingest → Raw Ledger Only — Implementation Plan

> **For agentic workers:** Execute this plan task-by-task via superpowers:subagent-driven-development or superpowers:executing-plans if available; otherwise execute the checkbox (`- [ ]`) steps literally, in order, committing exactly where the plan says. Read the master plan first: `claudedocs/plans/2026-07-04-memory-context-fabric-build-plan.md` (global constraints + hand-off protocol).
**Packet**: TP-MCF-002 (Memory Context Fabric, phase 002)
**Date**: 2026-07-04
**Status**: READY TO BUILD (spec-derived; all invariants test-gated below)
**Authority**: `claudedocs/memory-context-fabric-design-2026-07-04.md` (v3, esp. §2, §5, §6 row TP-MCF-002), `claudedocs/tp-mcf-001-authority-map-2026-07-04.md` (§1 Domain A, §3 gap register, §4 TP-MCF-002 spec), `claudedocs/memory-context-fabric-interfaces-2026-07-04.md` (§2.1 CaptureEnvelope, §2.2 taxonomy, §4 invariants).

---

## 0. Header block — read this before writing any code

**Goal**: build a transcript-file ingest adapter that parses Claude Code session transcript JSONL into turn events and writes **only** to the dope-memory raw ledger (`raw_activity_events`) via `capture_client.emit_capture_event()`. No ConPort writes. No dope-context writes. No Redis requirement. No file-watcher daemon (that is a later packet — this ships the one-shot, re-runnable ingest primitive).

**Architecture**: one new pure-function module (`src/dopemux/memory/transcript_ingest.py`) plus one new CLI subcommand (`dopemux memory ingest-transcript <path>`) added to the *existing* `memory` Click group in `src/dopemux/commands/memory_commands.py`. The module calls the existing capture spine (`dopemux.memory.capture_client.emit_capture_event`) directly — it does not reimplement redaction, dedup, or ledger writes. It adds one new local safety artifact: a quarantine directory `.dopemux/quarantine/transcript/`.

**Tech stack**: Python 3.12 (repo interpreter: `mise exec -- python`), stdlib `json`/`pathlib`/`hashlib`/`dataclasses`, pytest for tests, Click for the CLI subcommand (matches the existing `memory` group's framework).

**Global constraints (apply to every task below)**:
- Always run Python via `mise exec -- python` (this repo pins 3.12; harness `python3` is 3.9.6 and will not satisfy type-hint syntax used here, e.g. `str | None`).
- Always run tests via `mise exec -- python -m pytest <path> -v` from the repo root. Targeted paths only — do not run the full suite until the final task.
- **Editable-install trap for manual CLI smoke tests**: this workspace's `dopemux` package may be `pip install -e`'d against a *different* checkout (e.g. the main repo, not this worktree) — `mise exec -- python -c "import dopemux.cli"` can silently resolve code from the wrong tree. `pytest` avoids this (it inserts the worktree's `tests/`+`src/` onto `sys.path` via rootdir detection), so the pytest commands in this plan are trustworthy as written. If you manually smoke-test the CLI outside pytest (e.g. `python -m dopemux.cli memory ingest-transcript --help`), prefix with `PYTHONPATH=src` from the repo root to force worktree-local resolution, and verify with `python -c "import dopemux.commands.memory_commands as m; print(m.__file__)"` that the printed path is under *this* worktree before trusting the output.
- Every test that touches the ledger MUST set `DOPEMUX_CAPTURE_LEDGER_PATH` to a `tmp_path`-derived file (via `monkeypatch.setenv`) — this is the existing hermetic-ledger convention used throughout `tests/unit/test_memory_capture_client.py`. Never let a test touch the real repo `.dopemux/chronicle.sqlite`.
- Every test that touches quarantine MUST write into a `tmp_path`-derived directory, never the real repo `.dopemux/quarantine/`.
- `repo_root=` passed to `emit_capture_event` in tests should be the real repo root (`Path(__file__).resolve().parents[2]` from `tests/unit/`, matching the existing `REPO_ROOT` constant pattern in `test_memory_capture_client.py`) so the WMA schema/migrations/redactor loaders resolve correctly — the ledger *location* is what `DOPEMUX_CAPTURE_LEDGER_PATH` overrides, not the schema/redactor source.
- TDD discipline per task: write the failing test → run it and confirm it fails for the right reason → write the minimal implementation → run again and confirm it passes → commit. Do not write implementation before seeing the red test.
- Do not modify `capture_client.py`, `redactor.py`, `promotion.py`, or `PROMOTABLE_CAPTURE_EVENT_TYPES`. This packet is additive only. `transcript.*` event types are **non-promotable** (raw-ledger-only) and must never be added to any promotable allowlist.
- Codex transcript support is **out of scope**. This packet targets Claude Code's on-disk JSONL transcript format only.
- A file-watcher daemon is **out of scope**. This packet delivers a one-shot, idempotent, re-runnable `ingest_transcript_file()` — the primitive that a future watcher will call per-line.

**File-level scope for this packet** (nothing else should change):
- Create: `src/dopemux/memory/transcript_ingest.py`
- Create: `tests/unit/test_transcript_ingest.py`
- Create: `tests/unit/test_cli_memory_ingest_transcript.py`
- Modify: `src/dopemux/commands/memory_commands.py` (append one new `@memory.command`)
- Do NOT modify: `src/dopemux/cli.py` (the `memory` group is already registered at `cli.py:3219-3221`; no new registration needed), `src/dopemux/memory/capture_client.py`, `services/working-memory-assistant/promotion/redactor.py`, `services/working-memory-assistant/promotion/promotion.py`.

---

## 1. Task 1 — Transcript format spike (no code; produces the parse contract)

This task is research, not implementation. It exists because the design spec (§7 "Open decisions / risks") flags the transcript JSONL schema/location as an unresolved spike, and the authority map (§4 TP-MCF-002) requires it be done first. Do not skip it and do not guess the schema — verify it.

### 1.1 Locate the transcript file

Claude Code writes session transcripts under `~/.claude/projects/<project-slug>/<session-uuid>.jsonl`. The `<project-slug>` derivation is **not a simple `/`→`-` substitution** — do not hardcode a transform in shipped code (the CLI takes an explicit file path argument, so this is spike-only discovery, never runtime logic). Find the directory by listing and grepping for your repo name:

```bash
ls ~/.claude/projects/ | grep -i "$(basename "$(git rev-parse --show-toplevel)" | tr '[:upper:]' '[:lower:]')"
```

Expected output: one or more directory names containing your repo's basename (e.g. `-Users-hue-code-dopemux-mvp`). Pick the directory that matches your actual working tree (main repo root, not a worktree subpath, unless you are actively in a worktree session with its own recorded transcripts).

Then list transcript files in that directory, newest first:

```bash
ls -t ~/.claude/projects/<matched-dir>/*.jsonl | head -5
```

Expected output: one or more `<uuid>.jsonl` files, most-recently-modified first.

### 1.2 Inspect the schema

Pick the most recent non-empty file and inspect the first several lines:

```bash
FILE=$(ls -t ~/.claude/projects/<matched-dir>/*.jsonl | head -1)
wc -l "$FILE"
sed -n '1p' "$FILE" | mise exec -- python -m json.tool
sed -n '2p' "$FILE" | mise exec -- python -m json.tool
sed -n '3p' "$FILE" | mise exec -- python -m json.tool
```

**Do not** pipe multiple lines through `python -m json.tool` at once (`head -3 "$FILE" | python -m json.tool`) — each line is a separate top-level JSON object, and `json.tool` only parses a single JSON document, so multi-line input raises `Extra data: line 2 column 1`. Inspect one line per invocation, or use the script below.

To see the full distribution of record shapes in the file, run this one-off (not committed) diagnostic:

```bash
mise exec -- python -c "
import json
types = {}
with open('$FILE') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        t = obj.get('type', '<none>')
        types[t] = types.get(t, 0) + 1
print(types)
"
```

**Record the observed schema in your plan-execution notes** (a scratch note, PR description, or task-orchestrator note — not a new committed doc). At minimum record: the set of top-level `type` values seen, and for `type in {"user", "assistant"}` the shape of the `message` field.

### 1.3 The verified schema (baseline — confirm it still holds for your transcript, note any drift)

This is what was observed against a real 660-line Claude Code transcript at plan-authoring time. Treat it as the baseline; if your `type` distribution differs meaningfully, note the drift before proceeding — the parser in Task 2 is built against this shape.

Top-level record `type` values seen: `queue-operation`, `attachment`, `user`, `last-prompt`, `assistant`, `system`, `pr-link`, `mode`. Only `user` and `assistant` carry conversation turns; everything else is harness bookkeeping and must be skipped.

**`type: "user"` record** (fields relevant to parsing):
```json
{
  "type": "user",
  "isMeta": false,
  "message": {
    "role": "user",
    "content": "<command-message>review</command-message>\n<command-name>/review</command-name>..."
  },
  "sessionId": "6e030b42-66a3-46e3-9588-f1c3cceb683f",
  "timestamp": "2026-07-05T04:22:54.799Z",
  "uuid": "8c9d1f8a-48f7-4437-95e7-aa9a1440006c"
}
```
`message.content` for a `user` record is **either a plain string** (the common case — human prompt text, sometimes wrapped in `<command-message>`/`<task-notification>` tags by the harness) **or a list** of content items, one of which may be `{"type": "tool_result", "tool_use_id": ..., "content": ...}` (a tool result reported back as a user-role turn — this is how Claude Code's transcript format represents tool results, not a separate top-level `type`).

**`type: "assistant"` record**:
```json
{
  "type": "assistant",
  "message": {
    "role": "assistant",
    "content": [
      {"type": "thinking", "thinking": "...", "signature": "..."},
      {"type": "tool_use", "id": "toolu_01Bdgx5jH9xquXjydWLMMgJa", "name": "Bash",
       "input": {"command": "gh pr list ...", "description": "List open PRs"}}
    ]
  },
  "sessionId": "6e030b42-66a3-46e3-9588-f1c3cceb683f",
  "timestamp": "2026-07-05T04:23:00.362Z",
  "uuid": "67867dfb-8e2b-4b4a-a3e9-0e29c5b4ec9b"
}
```
`message.content` for an `assistant` record is always a list of content items: `thinking`, `text`, and/or `tool_use`. A single assistant line commonly carries both prose (`text`) and one or more `tool_use` items.

Records with `isMeta: true` are harness-synthesized user turns (task notifications, command echoes) — some are legitimate conversation, but per this packet's scope they are treated the same as ordinary user turns (not specially filtered) **except** malformed/unparseable ones, which fail open to `skipped`. (A future packet may choose to exclude `isMeta` turns from promotion — out of scope here; this packet is raw-ledger-only.)

### 1.4 The parse contract (locked — do not redesign in Task 2)

`TranscriptTurn` has exactly these fields:

| Field | Type | Source | Notes |
|---|---|---|---|
| `turn_type` | `str` | derived | one of `"user_prompt"`, `"assistant_response"`, `"tool_call"`, `"tool_result"` |
| `ts` | `str \| None` | `timestamp` | **REQUIRED to emit** — `None` means the record is quarantined, never ingested with `now()` |
| `session_id` | `str \| None` | `sessionId` | |
| `content` | `Any` | `message.content` | preserved **losslessly** (string or list) — no per-tool splitting in this packet |

**Turn-type classification is one line → at most one turn**, decided by this exact priority (verified empirically against the 660-line sample: `user_prompt=11, assistant_response=167, tool_call=92, tool_result=92`, `skipped=298`, totals reconcile):

1. Top-level `type` not in `{"user", "assistant"}` → skip (return `None`).
2. `message` missing or not a dict → skip.
3. `message.role == "user"` AND `message.content` is a list containing any item with `type == "tool_result"` → `turn_type = "tool_result"`.
4. `message.role == "user"` (content is a string, or a list with no `tool_result` item) → `turn_type = "user_prompt"`.
5. `message.role == "assistant"` AND `message.content` is a list containing any item with `type == "tool_use"` → `turn_type = "tool_call"`.
6. `message.role == "assistant"` (content has no `tool_use` item, e.g. pure `thinking`/`text`) → `turn_type = "assistant_response"`.
7. Any other `role` value → skip.

No proof-gate task is needed for this section — it is design record, verified by the Task 2 tests below.

---

## 2. Task 2 — `parse_transcript_line` (pure parser, no I/O)

### Files
- **Create**: `src/dopemux/memory/transcript_ingest.py`
- **Test**: `tests/unit/test_transcript_ingest.py`

### Interfaces
- **Produces**: `TranscriptTurn` (frozen dataclass), `parse_transcript_line(line: str) -> TranscriptTurn | None`

### Steps

- [ ] **2.1 — Write the failing test file.**

Create `tests/unit/test_transcript_ingest.py`:

```python
"""Tests for transcript-file ingest into the dope-memory raw ledger (TP-MCF-002)."""

import json
import sqlite3
from pathlib import Path

import pytest

from dopemux.memory.transcript_ingest import (
    TranscriptTurn,
    parse_transcript_line,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


# --- Realistic fixture lines, trimmed from an actual Claude Code transcript ---
# Real field names verified in Task 1: type, message.role, message.content,
# timestamp, sessionId, isMeta.

USER_PROMPT_LINE = json.dumps(
    {
        "type": "user",
        "isMeta": False,
        "message": {
            "role": "user",
            "content": "<command-message>review</command-message>\n"
            "<command-name>/review</command-name>\n"
            "<command-args>open prs deeply and comment findings</command-args>",
        },
        "sessionId": "6e030b42-66a3-46e3-9588-f1c3cceb683f",
        "timestamp": "2026-07-05T04:22:54.799Z",
        "uuid": "8c9d1f8a-48f7-4437-95e7-aa9a1440006c",
    }
)

ASSISTANT_RESPONSE_LINE = json.dumps(
    {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [
                {"type": "thinking", "thinking": "considering PRs", "signature": "sig"},
                {"type": "text", "text": "I'll list the open PRs now."},
            ],
        },
        "sessionId": "6e030b42-66a3-46e3-9588-f1c3cceb683f",
        "timestamp": "2026-07-05T04:23:00.362Z",
        "uuid": "67867dfb-8e2b-4b4a-a3e9-0e29c5b4ec9b",
    }
)

TOOL_CALL_LINE = json.dumps(
    {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_01Bdgx5jH9xquXjydWLMMgJa",
                    "name": "Bash",
                    "input": {
                        "command": "gh pr list --state open --json number,title",
                        "description": "List open PRs",
                    },
                }
            ],
        },
        "sessionId": "6e030b42-66a3-46e3-9588-f1c3cceb683f",
        "timestamp": "2026-07-05T04:23:01.981Z",
        "uuid": "05bf6989-d0a7-4fb0-af45-7e435a8d9a4e",
    }
)

TOOL_RESULT_LINE = json.dumps(
    {
        "type": "user",
        "isMeta": False,
        "message": {
            "role": "user",
            "content": [
                {
                    "tool_use_id": "toolu_01Bdgx5jH9xquXjydWLMMgJa",
                    "type": "tool_result",
                    "content": '[{"number":1008,"title":"Harden Serena F001"}]',
                }
            ],
        },
        "sessionId": "6e030b42-66a3-46e3-9588-f1c3cceb683f",
        "timestamp": "2026-07-05T04:23:03.584Z",
        "uuid": "46727f0c-d90a-4e44-aed6-782a07b8de9a",
    }
)

NON_TURN_ATTACHMENT_LINE = json.dumps(
    {
        "type": "attachment",
        "attachment": {"type": "hook_success", "hookName": "SessionStart:startup"},
        "sessionId": "6e030b42-66a3-46e3-9588-f1c3cceb683f",
        "timestamp": "2026-07-05T04:22:53.476Z",
        "uuid": "52e9791c-560a-4129-bb80-9ef2cc44a542",
    }
)

QUEUE_OP_LINE = json.dumps(
    {
        "type": "queue-operation",
        "operation": "enqueue",
        "timestamp": "2026-07-05T04:22:53.878Z",
        "sessionId": "6e030b42-66a3-46e3-9588-f1c3cceb683f",
    }
)

MISSING_TS_LINE = json.dumps(
    {
        "type": "user",
        "isMeta": False,
        "message": {"role": "user", "content": "no timestamp on this one"},
        "sessionId": "6e030b42-66a3-46e3-9588-f1c3cceb683f",
        "uuid": "no-ts-0001",
    }
)


def test_parse_user_prompt_line():
    turn = parse_transcript_line(USER_PROMPT_LINE)
    assert turn is not None
    assert turn.turn_type == "user_prompt"
    assert turn.ts == "2026-07-05T04:22:54.799Z"
    assert turn.session_id == "6e030b42-66a3-46e3-9588-f1c3cceb683f"
    assert "/review" in turn.content


def test_parse_assistant_response_line():
    turn = parse_transcript_line(ASSISTANT_RESPONSE_LINE)
    assert turn is not None
    assert turn.turn_type == "assistant_response"
    assert turn.ts == "2026-07-05T04:23:00.362Z"
    assert isinstance(turn.content, list)


def test_parse_tool_call_line():
    turn = parse_transcript_line(TOOL_CALL_LINE)
    assert turn is not None
    assert turn.turn_type == "tool_call"
    assert turn.ts == "2026-07-05T04:23:01.981Z"


def test_parse_tool_result_line():
    turn = parse_transcript_line(TOOL_RESULT_LINE)
    assert turn is not None
    assert turn.turn_type == "tool_result"
    assert turn.ts == "2026-07-05T04:23:03.584Z"


def test_parse_skips_non_turn_attachment_record():
    assert parse_transcript_line(NON_TURN_ATTACHMENT_LINE) is None


def test_parse_skips_queue_operation_record():
    assert parse_transcript_line(QUEUE_OP_LINE) is None


def test_parse_skips_blank_line():
    assert parse_transcript_line("") is None
    assert parse_transcript_line("   \n") is None


def test_parse_skips_malformed_json_never_raises():
    # Fail-open per turn: a malformed line must not raise out of the parser.
    assert parse_transcript_line("{not valid json") is None


def test_parse_missing_timestamp_returns_turn_with_ts_none():
    # ts is REQUIRED to *emit*, but the parser itself must not raise or invent
    # a timestamp — it returns a turn with ts=None so the ingest loop can
    # quarantine it (invariant 3). The parser never calls datetime.now().
    turn = parse_transcript_line(MISSING_TS_LINE)
    assert turn is not None
    assert turn.ts is None
```

- [ ] **2.2 — Run the test file and confirm it fails on import** (module doesn't exist yet):

```bash
cd /Users/hue/code/dopemux-mvp/.claude/worktrees/trusting-engelbart-d2fbfe
mise exec -- python -m pytest tests/unit/test_transcript_ingest.py -v
```

Expected output: `ModuleNotFoundError: No module named 'dopemux.memory.transcript_ingest'` (collection error, all tests error out).

- [ ] **2.3 — Write the minimal implementation.**

Create `src/dopemux/memory/transcript_ingest.py`:

```python
"""Transcript-file ingest adapter (TP-MCF-002).

Parses Claude Code session transcript JSONL into TranscriptTurn records and
writes them to the dope-memory raw ledger (`raw_activity_events`) via the
existing capture spine — `dopemux.memory.capture_client.emit_capture_event`.

Hard invariants (see claudedocs/tp-mcf-001-authority-map-2026-07-04.md §4 and
claudedocs/memory-context-fabric-interfaces-2026-07-04.md §4):
  1. No ConPort writes, no dope-context writes, no Redis requirement in this
     module. This module imports neither `conport` nor `dope_context`.
  2. A turn without a source timestamp is NEVER ingested with `datetime.now()`
     — it is quarantined instead.
  3. Redaction failure (the WMA redactor's fail-closed sentinel) routes the
     turn to quarantine, never the queryable ledger.
  4. Ingest is idempotent: re-running against the same file produces the same
     ledger row count (deterministic event_id + INSERT OR IGNORE, inherited
     from capture_client).
  5. Fail-open per turn: a malformed line increments `skipped`, never raises
     out of `ingest_transcript_file`.

Codex transcript support and a file-watcher daemon are explicitly OUT OF
SCOPE for this module — see the plan this module was built from.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .capture_client import (
    _deterministic_event_id,
    _load_wma_redactor,
    emit_capture_event,
)

TRANSCRIPT_EVENT_TYPES = frozenset(
    {
        "transcript.user_prompt",
        "transcript.assistant_response",
        "transcript.tool_call",
        "transcript.tool_result",
    }
)

_TURN_TYPE_TO_EVENT_TYPE = {
    "user_prompt": "transcript.user_prompt",
    "assistant_response": "transcript.assistant_response",
    "tool_call": "transcript.tool_call",
    "tool_result": "transcript.tool_result",
}


@dataclass(frozen=True)
class TranscriptTurn:
    """One parsed transcript record. One line maps to at most one turn."""

    turn_type: str  # user_prompt | assistant_response | tool_call | tool_result
    ts: Optional[str]  # source timestamp; None means "no source ts observed"
    session_id: Optional[str]
    content: Any  # message.content, preserved losslessly (str or list)


@dataclass(frozen=True)
class IngestResult:
    """Counters for one ingest_transcript_file() run."""

    ingested: int
    skipped: int
    quarantined: int
    duplicate: int


def _has_content_item_type(content: Any, item_type: str) -> bool:
    if not isinstance(content, list):
        return False
    return any(
        isinstance(item, dict) and item.get("type") == item_type for item in content
    )


def parse_transcript_line(line: str) -> Optional[TranscriptTurn]:
    """Parse one JSONL line into a TranscriptTurn, or None if not a turn.

    Never raises: malformed JSON, missing fields, and non-turn record types
    all return None so the caller can fail open (invariant: skipped, not
    raised).
    """
    stripped = line.strip()
    if not stripped:
        return None

    try:
        obj = json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        return None

    if not isinstance(obj, dict):
        return None

    record_type = obj.get("type")
    if record_type not in ("user", "assistant"):
        return None

    message = obj.get("message")
    if not isinstance(message, dict):
        return None

    role = message.get("role")
    content = message.get("content")

    if role == "user":
        turn_type = (
            "tool_result"
            if _has_content_item_type(content, "tool_result")
            else "user_prompt"
        )
    elif role == "assistant":
        turn_type = (
            "tool_call"
            if _has_content_item_type(content, "tool_use")
            else "assistant_response"
        )
    else:
        return None

    ts = obj.get("timestamp")
    if not isinstance(ts, str) or not ts:
        ts = None

    session_id = obj.get("sessionId")
    if not isinstance(session_id, str) or not session_id:
        session_id = None

    return TranscriptTurn(
        turn_type=turn_type,
        ts=ts,
        session_id=session_id,
        content=content,
    )
```

- [ ] **2.4 — Run the test file and confirm it passes:**

```bash
mise exec -- python -m pytest tests/unit/test_transcript_ingest.py -v
```

Expected output: 10 tests pass (`test_parse_user_prompt_line`, `test_parse_assistant_response_line`, `test_parse_tool_call_line`, `test_parse_tool_result_line`, `test_parse_skips_non_turn_attachment_record`, `test_parse_skips_queue_operation_record`, `test_parse_skips_blank_line`, `test_parse_skips_malformed_json_never_raises`, `test_parse_missing_timestamp_returns_turn_with_ts_none`) — 9 test functions, some with multiple asserts; `9 passed`.

- [ ] **2.5 — Commit.**

```bash
git add src/dopemux/memory/transcript_ingest.py tests/unit/test_transcript_ingest.py
git commit -m "$(cat <<'EOF'
feat(memory): add transcript-line parser for TP-MCF-002 ingest adapter

Adds parse_transcript_line() — a pure, never-raising parser that turns one
Claude Code transcript JSONL record into a TranscriptTurn (or None for
non-turn/malformed records). Classification rule (one line -> at most one
turn) verified empirically against a real 660-line transcript. Missing
source timestamps are preserved as ts=None, never invented, so the ingest
loop (next commit) can quarantine them per TP-MCF-002 invariant 3.
EOF
)"
```

---

## 3. Task 3 — `turn_to_capture_envelope` (turn → CaptureEnvelope shape)

### Files
- **Modify**: `src/dopemux/memory/transcript_ingest.py`
- **Test**: `tests/unit/test_transcript_ingest.py` (append)

### Interfaces
- **Consumes**: `TranscriptTurn` (from Task 2)
- **Produces**: `turn_to_capture_envelope(turn: TranscriptTurn, workspace_id: str) -> dict`

### Steps

- [ ] **3.1 — Append the failing test to `tests/unit/test_transcript_ingest.py`:**

```python
from dopemux.memory.transcript_ingest import turn_to_capture_envelope


def test_turn_to_capture_envelope_maps_fields():
    turn = TranscriptTurn(
        turn_type="user_prompt",
        ts="2026-07-05T04:22:54.799Z",
        session_id="6e030b42-66a3-46e3-9588-f1c3cceb683f",
        content="hello world",
    )
    envelope = turn_to_capture_envelope(turn, workspace_id="/repo/root")

    assert envelope["event_type"] == "transcript.user_prompt"
    assert envelope["source"] == "transcript"
    assert envelope["ts_utc"] == "2026-07-05T04:22:54.799Z"
    assert envelope["session_id"] == "6e030b42-66a3-46e3-9588-f1c3cceb683f"
    assert envelope["workspace_id"] == "/repo/root"
    assert envelope["payload"] == {"content": "hello world"}


def test_turn_to_capture_envelope_maps_all_turn_types():
    for turn_type, expected_event_type in [
        ("user_prompt", "transcript.user_prompt"),
        ("assistant_response", "transcript.assistant_response"),
        ("tool_call", "transcript.tool_call"),
        ("tool_result", "transcript.tool_result"),
    ]:
        turn = TranscriptTurn(
            turn_type=turn_type,
            ts="2026-07-05T04:23:00.000Z",
            session_id="sess-1",
            content=[{"type": "text", "text": "x"}],
        )
        envelope = turn_to_capture_envelope(turn, workspace_id="/repo/root")
        assert envelope["event_type"] == expected_event_type
```

- [ ] **3.2 — Run and confirm failure:**

```bash
mise exec -- python -m pytest tests/unit/test_transcript_ingest.py -v -k turn_to_capture_envelope
```

Expected output: `ImportError: cannot import name 'turn_to_capture_envelope'`.

- [ ] **3.3 — Add the function to `src/dopemux/memory/transcript_ingest.py`** (insert after `parse_transcript_line`):

```python
def turn_to_capture_envelope(turn: TranscriptTurn, workspace_id: str) -> dict[str, Any]:
    """Map a TranscriptTurn to the CaptureEnvelope shape emit_capture_event expects.

    Per the interfaces spec (§2.1): ts is the SOURCE timestamp, passed through
    as ts_utc so emit_capture_event never falls back to datetime.now()
    (capture_client.py:493). Callers MUST NOT call this with turn.ts is None —
    ingest_transcript_file() quarantines those turns before reaching here.
    """
    event_type = _TURN_TYPE_TO_EVENT_TYPE[turn.turn_type]
    return {
        "event_type": event_type,
        "source": "transcript",
        "ts_utc": turn.ts,
        "session_id": turn.session_id,
        "workspace_id": workspace_id,
        "payload": {"content": turn.content},
    }
```

- [ ] **3.4 — Run and confirm pass:**

```bash
mise exec -- python -m pytest tests/unit/test_transcript_ingest.py -v
```

Expected output: all previous 9 tests plus these 2 new tests pass — `11 passed`.

- [ ] **3.5 — Commit.**

```bash
git add src/dopemux/memory/transcript_ingest.py tests/unit/test_transcript_ingest.py
git commit -m "$(cat <<'EOF'
feat(memory): map transcript turns to CaptureEnvelope shape

Adds turn_to_capture_envelope() mapping TranscriptTurn -> the dict shape
emit_capture_event() expects, with source="transcript" and ts_utc set from
the turn's own source timestamp (never a now() fallback). Event types are
transcript.{user_prompt,assistant_response,tool_call,tool_result} — raw-
ledger-only per the taxonomy in the interfaces spec §2.2, deliberately not
added to PROMOTABLE_CAPTURE_EVENT_TYPES.
EOF
)"
```

---

## 4. Task 4 — Quarantine writer (missing-ts + redaction-failure safety artifact)

This is the highest-risk task in the packet — get invariants 3 and 4 (from the original packet spec) exactly right: missing timestamp → quarantine, and redaction *failure* (not redaction *success on a secret*) → quarantine.

### Files
- **Modify**: `src/dopemux/memory/transcript_ingest.py`
- **Test**: `tests/unit/test_transcript_ingest.py` (append)

### Interfaces
- **Produces**: `write_quarantine_record(*, quarantine_dir: Path, event_id: str, ts: str | None, session_id: str | None, reason: str, original_keys: list[str], source_path: Path, source_line: int) -> Path`

### Steps

- [ ] **4.1 — Append the failing tests:**

```python
from dopemux.memory.transcript_ingest import write_quarantine_record


def test_write_quarantine_record_contains_only_the_five_safe_fields(tmp_path):
    quarantine_dir = tmp_path / "quarantine" / "transcript"
    source_path = tmp_path / "session.jsonl"
    source_path.write_text("irrelevant\n", encoding="utf-8")

    written = write_quarantine_record(
        quarantine_dir=quarantine_dir,
        event_id="evt-abc123",
        ts=None,
        session_id="sess-1",
        reason="missing_source_timestamp",
        original_keys=["role", "content"],
        source_path=source_path,
        source_line=7,
    )

    assert written.exists()
    assert written.parent == quarantine_dir
    assert written.name == "evt-abc123.json"

    record = json.loads(written.read_text(encoding="utf-8"))
    assert set(record.keys()) == {
        "event_id",
        "ts",
        "session_id",
        "reason",
        "original_keys",
        "source_path",
        "source_line",
    }
    assert record["event_id"] == "evt-abc123"
    assert record["ts"] is None
    assert record["session_id"] == "sess-1"
    assert record["reason"] == "missing_source_timestamp"
    assert record["original_keys"] == ["role", "content"]
    assert record["source_path"] == str(source_path)
    assert record["source_line"] == 7

    # No raw payload content anywhere in the file.
    raw_text = written.read_text(encoding="utf-8")
    assert "irrelevant" not in raw_text


def test_write_quarantine_record_is_idempotent_same_event_id(tmp_path):
    quarantine_dir = tmp_path / "quarantine" / "transcript"
    source_path = tmp_path / "session.jsonl"
    source_path.write_text("line one\n", encoding="utf-8")

    first = write_quarantine_record(
        quarantine_dir=quarantine_dir,
        event_id="evt-dup",
        ts=None,
        session_id="sess-1",
        reason="missing_source_timestamp",
        original_keys=[],
        source_path=source_path,
        source_line=1,
    )
    second = write_quarantine_record(
        quarantine_dir=quarantine_dir,
        event_id="evt-dup",
        ts=None,
        session_id="sess-1",
        reason="missing_source_timestamp",
        original_keys=[],
        source_path=source_path,
        source_line=1,
    )

    assert first == second
    assert len(list(quarantine_dir.glob("*.json"))) == 1
```

- [ ] **4.2 — Run and confirm failure:**

```bash
mise exec -- python -m pytest tests/unit/test_transcript_ingest.py -v -k write_quarantine_record
```

Expected output: `ImportError: cannot import name 'write_quarantine_record'`.

- [ ] **4.3 — Add the function to `src/dopemux/memory/transcript_ingest.py`:**

```python
def write_quarantine_record(
    *,
    quarantine_dir: Path,
    event_id: str,
    ts: Optional[str],
    session_id: Optional[str],
    reason: str,
    original_keys: list[str],
    source_path: Path,
    source_line: int,
) -> Path:
    """Write a quarantine safety artifact for a turn that must NOT reach the
    queryable ledger.

    Quarantine is not memory truth: never searched, promoted, mirrored, or
    projected (interfaces spec §2.2, §4 invariant 3). The record holds ONLY
    {event_id, ts, session_id, reason, original_keys, source_path,
    source_line} — no payload content. The raw line stays in the source
    transcript file; we store a reference (path + line number) so an
    operator can go look, deliberately, rather than have the content mirrored
    into a second location.

    Idempotent: writing the same event_id twice overwrites the same file
    with identical content (deterministic event_id -> deterministic path).
    """
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "event_id": event_id,
        "ts": ts,
        "session_id": session_id,
        "reason": reason,
        "original_keys": list(original_keys),
        "source_path": str(source_path),
        "source_line": source_line,
    }
    target = quarantine_dir / f"{event_id}.json"
    target.write_text(
        json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return target
```

- [ ] **4.4 — Run and confirm pass:**

```bash
mise exec -- python -m pytest tests/unit/test_transcript_ingest.py -v
```

Expected output: all prior tests plus these 2 new tests pass — `13 passed`.

- [ ] **4.5 — Commit.**

```bash
git add src/dopemux/memory/transcript_ingest.py tests/unit/test_transcript_ingest.py
git commit -m "$(cat <<'EOF'
feat(memory): add quarantine writer for missing-ts and redaction-failure turns

Adds write_quarantine_record() writing .dopemux/quarantine/transcript/
<event_id>.json containing ONLY {event_id, ts, session_id, reason,
original_keys, source_path, source_line} -- no payload content. This is the
named local safety artifact required by TP-MCF-002 (quarantine is not
memory truth: never searched/promoted/mirrored/projected). Deterministic
event_id makes re-writing the same quarantined turn idempotent.
EOF
)"
```

---

## 5. Task 5 — `ingest_transcript_file` (the orchestrating loop)

This wires Tasks 2-4 together plus the redaction-failure detection and the `emit_capture_event` call. This is where all seven hard invariants from the prompt converge into one function.

### Files
- **Modify**: `src/dopemux/memory/transcript_ingest.py`
- **Test**: `tests/unit/test_transcript_ingest.py` (append)

### Interfaces
- **Consumes**: `capture_client.emit_capture_event(event: dict, *, mode, repo_root, emit_event_bus) -> CaptureResult`, `capture_client._load_wma_redactor(repo_root) -> Redactor`, `capture_client._deterministic_event_id(*, event_type, session_id, ts_utc, payload) -> str`
- **Produces**: `ingest_transcript_file(path: Path, workspace_id: str, repo_root: Path) -> IngestResult`

### Steps

- [ ] **5.1 — Append the failing tests.** These are the proof-gate tests the packet spec requires (redaction test, replay test, stable-timestamp test) plus baseline ingest and fail-open tests.

```python
import sqlite3


def _count_ledger_rows(ledger_path: Path) -> int:
    # If every turn in the file was quarantined (or skipped), emit_capture_event
    # never ran, so the ledger file/schema was never created. Treat that as a
    # valid "zero rows" outcome rather than an error — do not let this helper
    # raise sqlite3.OperationalError("no such table") on a fully-quarantined run.
    if not ledger_path.exists():
        return 0
    conn = sqlite3.connect(str(ledger_path))
    try:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='raw_activity_events'"
        )
        if cursor.fetchone() is None:
            return 0
        return int(conn.execute("SELECT COUNT(*) FROM raw_activity_events").fetchone()[0])
    finally:
        conn.close()


def _ledger_row(ledger_path: Path, event_id: str) -> dict:
    conn = sqlite3.connect(str(ledger_path))
    try:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM raw_activity_events WHERE id = ?", (event_id,)
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    return dict(row)


def _write_transcript(tmp_path: Path, lines: list[str]) -> Path:
    path = tmp_path / "session.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_ingest_transcript_file_writes_only_to_raw_ledger(tmp_path, monkeypatch):
    from dopemux.memory.transcript_ingest import ingest_transcript_file

    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    transcript_path = _write_transcript(
        tmp_path,
        [USER_PROMPT_LINE, ASSISTANT_RESPONSE_LINE, TOOL_CALL_LINE, TOOL_RESULT_LINE],
    )

    result = ingest_transcript_file(
        transcript_path, workspace_id=str(REPO_ROOT), repo_root=REPO_ROOT
    )

    assert result.ingested == 4
    assert result.skipped == 0
    assert result.quarantined == 0
    assert result.duplicate == 0
    assert _count_ledger_rows(ledger_path) == 4


def test_ingest_transcript_file_skips_non_turn_and_malformed_lines(tmp_path, monkeypatch):
    from dopemux.memory.transcript_ingest import ingest_transcript_file

    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    transcript_path = _write_transcript(
        tmp_path,
        [
            USER_PROMPT_LINE,
            NON_TURN_ATTACHMENT_LINE,
            QUEUE_OP_LINE,
            "{this is not valid json",
        ],
    )

    result = ingest_transcript_file(
        transcript_path, workspace_id=str(REPO_ROOT), repo_root=REPO_ROOT
    )

    # 1 real turn ingested; attachment + queue-op + malformed = skipped.
    # Note: _write_transcript joins lines with "\n" and appends a trailing
    # "\n" -- do not add a separate "" list entry expecting an extra skipped
    # count for it; the trailing newline is consumed by file-line iteration,
    # not turned into its own line entry. Verified empirically: 4 input
    # lines -> 1 ingested + 3 skipped, totals reconcile.
    assert result.ingested == 1
    assert result.skipped == 3
    assert result.quarantined == 0
    assert _count_ledger_rows(ledger_path) == 1


def test_ingest_transcript_file_quarantines_missing_timestamp_turn(tmp_path, monkeypatch):
    """Invariant: a turn without a source timestamp is NEVER ingested with
    now() -- it goes to quarantine instead."""
    from dopemux.memory.transcript_ingest import ingest_transcript_file

    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))
    quarantine_dir = tmp_path / ".dopemux" / "quarantine" / "transcript"
    monkeypatch.setenv("DOPEMUX_QUARANTINE_DIR", str(quarantine_dir))

    transcript_path = _write_transcript(tmp_path, [MISSING_TS_LINE])

    result = ingest_transcript_file(
        transcript_path, workspace_id=str(REPO_ROOT), repo_root=REPO_ROOT
    )

    assert result.ingested == 0
    assert result.quarantined == 1
    # Nothing reached the queryable ledger for this turn.
    assert _count_ledger_rows(ledger_path) == 0

    quarantine_files = list(quarantine_dir.glob("*.json"))
    assert len(quarantine_files) == 1
    record = json.loads(quarantine_files[0].read_text(encoding="utf-8"))
    assert record["reason"] == "missing_source_timestamp"
    assert record["ts"] is None
    # No raw payload content in the quarantine file.
    assert "no timestamp on this one" not in quarantine_files[0].read_text(encoding="utf-8")


def test_ingest_transcript_file_quarantines_on_redaction_failure(tmp_path, monkeypatch):
    """Invariant: redaction FAILURE (the redactor's fail-closed sentinel,
    {"redaction_error": True, ...}) routes to quarantine, never the queryable
    ledger. This is distinct from redaction SUCCESS scrubbing a secret (see
    the next test) -- only the exception path quarantines."""
    import dopemux.memory.transcript_ingest as ingest_module

    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))
    quarantine_dir = tmp_path / ".dopemux" / "quarantine" / "transcript"
    monkeypatch.setenv("DOPEMUX_QUARANTINE_DIR", str(quarantine_dir))

    class _FailingRedactor:
        def redact_payload(self, payload):
            return {"redaction_error": True, "original_keys": list(payload.keys())}

    monkeypatch.setattr(
        ingest_module, "_load_wma_redactor", lambda repo_root: _FailingRedactor()
    )

    transcript_path = _write_transcript(tmp_path, [USER_PROMPT_LINE])

    result = ingest_module.ingest_transcript_file(
        transcript_path, workspace_id=str(REPO_ROOT), repo_root=REPO_ROOT
    )

    assert result.ingested == 0
    assert result.quarantined == 1
    assert _count_ledger_rows(ledger_path) == 0

    quarantine_files = list(quarantine_dir.glob("*.json"))
    assert len(quarantine_files) == 1
    record = json.loads(quarantine_files[0].read_text(encoding="utf-8"))
    assert record["reason"] == "redaction_failed"
    assert "content" in record["original_keys"]
    # No raw payload content in the quarantine file.
    assert "/review" not in quarantine_files[0].read_text(encoding="utf-8")


def test_ingest_transcript_file_scrubs_secret_and_still_ingests(tmp_path, monkeypatch):
    """Contrast case: a secret-bearing turn whose redaction SUCCEEDS (the
    normal case -- the real Redactor scrubs and returns normally) is
    ingested with the secret scrubbed, not quarantined. Only redaction
    *failure* (the exception path) quarantines."""
    from dopemux.memory.transcript_ingest import ingest_transcript_file

    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    secret_line = json.dumps(
        {
            "type": "user",
            "isMeta": False,
            "message": {
                "role": "user",
                "content": "here is my token: Bearer abcdef1234567890",
            },
            "sessionId": "sess-secret",
            "timestamp": "2026-07-05T05:00:00.000Z",
            "uuid": "secret-line-0001",
        }
    )
    transcript_path = _write_transcript(tmp_path, [secret_line])

    result = ingest_transcript_file(
        transcript_path, workspace_id=str(REPO_ROOT), repo_root=REPO_ROOT
    )

    assert result.ingested == 1
    assert result.quarantined == 0
    assert _count_ledger_rows(ledger_path) == 1


def test_ingest_transcript_file_is_idempotent_on_replay(tmp_path, monkeypatch):
    """Deterministic event_id + INSERT OR IGNORE (inherited from
    capture_client) makes re-ingesting the same file safe. Run 2 must not
    grow the ledger, and run 2's ingested count must be 0 (everything is now
    a duplicate)."""
    from dopemux.memory.transcript_ingest import ingest_transcript_file

    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    transcript_path = _write_transcript(
        tmp_path,
        [USER_PROMPT_LINE, ASSISTANT_RESPONSE_LINE, TOOL_CALL_LINE, TOOL_RESULT_LINE],
    )

    run1 = ingest_transcript_file(
        transcript_path, workspace_id=str(REPO_ROOT), repo_root=REPO_ROOT
    )
    count_after_run1 = _count_ledger_rows(ledger_path)

    run2 = ingest_transcript_file(
        transcript_path, workspace_id=str(REPO_ROOT), repo_root=REPO_ROOT
    )
    count_after_run2 = _count_ledger_rows(ledger_path)

    assert count_after_run1 == count_after_run2
    assert run2.ingested == 0
    assert (run1.ingested + run1.duplicate) == (run2.ingested + run2.duplicate)
    assert run1.quarantined == run2.quarantined
    assert run1.skipped == run2.skipped


def test_ingest_transcript_file_stores_source_timestamp_not_now(tmp_path, monkeypatch):
    """The ledger row's ts_utc must equal the transcript's own timestamp --
    never datetime.now() (capture_client.py:493's fallback must never be
    reached for a turn that has a source ts)."""
    from dopemux.memory.transcript_ingest import ingest_transcript_file

    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    transcript_path = _write_transcript(tmp_path, [USER_PROMPT_LINE])

    ingest_transcript_file(
        transcript_path, workspace_id=str(REPO_ROOT), repo_root=REPO_ROOT
    )

    conn = sqlite3.connect(str(ledger_path))
    try:
        row = conn.execute(
            "SELECT ts_utc, event_type, source FROM raw_activity_events"
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    ts_utc, event_type, source = row
    assert ts_utc == "2026-07-05T04:22:54.799Z"
    assert event_type == "transcript.user_prompt"
    assert source == "transcript"


def test_ingest_transcript_file_never_raises_on_fully_malformed_file(tmp_path, monkeypatch):
    """Fail-open for the session: a file full of garbage must not raise out
    of ingest_transcript_file."""
    from dopemux.memory.transcript_ingest import ingest_transcript_file

    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    transcript_path = _write_transcript(
        tmp_path, ["{garbage", "not json at all", "[]", "null"]
    )

    result = ingest_transcript_file(
        transcript_path, workspace_id=str(REPO_ROOT), repo_root=REPO_ROOT
    )

    assert result.ingested == 0
    assert result.skipped == 4
    assert result.quarantined == 0


def test_ingest_transcript_file_no_conport_or_dope_context_imports():
    """Structural invariant: the Fabric package imports no plane's storage
    internals. This module must import neither conport nor dope_context.

    Checks actual `import`/`from ... import` statement lines only, not
    prose -- this module's own docstring legitimately names the invariant
    ("must import neither conport nor dope_context"), and a naive whole-file
    substring check would trip on its own documentation. Only import lines
    count."""
    module_path = REPO_ROOT / "src" / "dopemux" / "memory" / "transcript_ingest.py"
    import_lines = [
        stripped
        for line in module_path.read_text(encoding="utf-8").splitlines()
        if (stripped := line.strip()).startswith("import ")
        or stripped.startswith("from ")
    ]
    for stripped in import_lines:
        assert "conport" not in stripped
        assert "dope_context" not in stripped
        assert "dope-context" not in stripped
```

- [ ] **5.2 — Run and confirm failure:**

```bash
mise exec -- python -m pytest tests/unit/test_transcript_ingest.py -v -k ingest_transcript_file
```

Expected output: `ImportError: cannot import name 'ingest_transcript_file'` (and the last test, which reads the file directly rather than importing, will pass trivially once the file exists with no forbidden imports — but it still needs `ingest_transcript_file` defined to be meaningful; expect an import error across this whole batch first).

- [ ] **5.3 — Add the function to `src/dopemux/memory/transcript_ingest.py`** (append at the end of the file):

```python
import os


def _quarantine_dir_for(repo_root: Path) -> Path:
    override = os.getenv("DOPEMUX_QUARANTINE_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (repo_root / ".dopemux" / "quarantine" / "transcript").resolve()


def ingest_transcript_file(
    path: Path, workspace_id: str, repo_root: Path
) -> IngestResult:
    """Parse a transcript JSONL file and write each turn to the raw ledger.

    Writes ONLY to dope-memory's raw_activity_events via
    capture_client.emit_capture_event() -- no ConPort writes, no dope-context
    writes, no Redis requirement (emit_event_bus=False, explicit).

    Per-line fail-open: a malformed line increments `skipped` and never
    raises out of this function. A turn missing its source timestamp, or
    whose redaction fails, is quarantined (never ingested with now(), never
    written to the queryable ledger).
    """
    ingested = 0
    skipped = 0
    quarantined = 0
    duplicate = 0

    quarantine_dir = _quarantine_dir_for(repo_root)
    redactor = _load_wma_redactor(repo_root)

    with path.open("r", encoding="utf-8") as fh:
        for line_number, raw_line in enumerate(fh, start=1):
            try:
                turn = parse_transcript_line(raw_line)
                if turn is None:
                    skipped += 1
                    continue

                payload = {"content": turn.content}

                if not turn.ts:
                    event_id = _deterministic_event_id(
                        event_type=_TURN_TYPE_TO_EVENT_TYPE[turn.turn_type],
                        session_id=turn.session_id,
                        ts_utc="",
                        payload=payload,
                    )
                    write_quarantine_record(
                        quarantine_dir=quarantine_dir,
                        event_id=event_id,
                        ts=turn.ts,
                        session_id=turn.session_id,
                        reason="missing_source_timestamp",
                        original_keys=sorted(payload.keys()),
                        source_path=path,
                        source_line=line_number,
                    )
                    quarantined += 1
                    continue

                redacted_payload = redactor.redact_payload(payload)
                if isinstance(redacted_payload, dict) and redacted_payload.get(
                    "redaction_error"
                ):
                    event_id = _deterministic_event_id(
                        event_type=_TURN_TYPE_TO_EVENT_TYPE[turn.turn_type],
                        session_id=turn.session_id,
                        ts_utc=turn.ts,
                        payload=payload,
                    )
                    write_quarantine_record(
                        quarantine_dir=quarantine_dir,
                        event_id=event_id,
                        ts=turn.ts,
                        session_id=turn.session_id,
                        reason="redaction_failed",
                        original_keys=list(
                            redacted_payload.get("original_keys", [])
                        ),
                        source_path=path,
                        source_line=line_number,
                    )
                    quarantined += 1
                    continue

                envelope = turn_to_capture_envelope(turn, workspace_id=workspace_id)
                result = emit_capture_event(
                    envelope,
                    mode="cli",
                    repo_root=repo_root,
                    emit_event_bus=False,
                )
                if result.inserted:
                    ingested += 1
                else:
                    duplicate += 1
            except Exception:
                # Fail-open per turn: never let one bad line break the whole
                # ingest run (invariant 7).
                skipped += 1
                continue

    return IngestResult(
        ingested=ingested,
        skipped=skipped,
        quarantined=quarantined,
        duplicate=duplicate,
    )
```

Note the redaction check runs on `{"content": turn.content}` — the same shape `turn_to_capture_envelope` will build into `payload`, so the redactor sees exactly what would be stored. This deliberately duplicates the payload shape rather than calling `turn_to_capture_envelope` twice with different intents (once to probe redaction, once to emit) — `emit_capture_event` runs its own redaction pass internally too (`capture_client.py:500-501`), which is harmless (the WMA redactor is idempotent on already-redacted or already-safe payloads) and is not duplicated logic we own — it's the existing spine's own defense in depth.

- [ ] **5.4 — Run and confirm pass:**

```bash
mise exec -- python -m pytest tests/unit/test_transcript_ingest.py -v
```

Expected output: all tests pass — `22 passed` (13 from Tasks 2-4 plus 9 new in this task; the malformed-line skip test uses one fewer fixture line than a naive count suggests — see the inline note in its assertion block above).

- [ ] **5.5 — Commit.**

```bash
git add src/dopemux/memory/transcript_ingest.py tests/unit/test_transcript_ingest.py
git commit -m "$(cat <<'EOF'
feat(memory): add ingest_transcript_file orchestrating loop (TP-MCF-002)

Wires parse_transcript_line + turn_to_capture_envelope + write_quarantine_record
into ingest_transcript_file(path, workspace_id, repo_root) -> IngestResult.

Hard invariants proven by test:
- missing source timestamp -> quarantine, never datetime.now() fallback
- redaction FAILURE (redactor's {"redaction_error": True} sentinel) ->
  quarantine, never the queryable ledger -- distinct from redaction SUCCESS
  scrubbing a secret (which still ingests, secret redacted)
- re-ingesting the same file is idempotent (ledger row count unchanged,
  run-2 ingested == 0)
- malformed lines increment skipped, never raise
- no ConPort or dope-context imports in this module (structural test)

Writes only to raw_activity_events via the existing capture_client spine;
emit_event_bus explicitly False. No file-watcher daemon in this packet.
EOF
)"
```

---

## 6. Task 6 — CLI subcommand `dopemux memory ingest-transcript`

The `memory` Click group already exists and is registered in `src/dopemux/cli.py:3219-3221` (`from .commands.memory_commands import memory` / `cli.add_command(memory)`). No new group registration is needed — this task only adds one `@memory.command()` to the existing file, modeled on the working `capture emit` command (which correctly calls `capture_client.emit_capture_event`), **not** on `capture copilot` (which imports a non-existent `dopemux.memory.adapters` module — a pre-existing bug in this codebase, out of scope for this packet; do not mirror or attempt to fix it here).

### Files
- **Modify**: `src/dopemux/commands/memory_commands.py`
- **Create**: `tests/unit/test_cli_memory_ingest_transcript.py`

### Interfaces
- **Consumes**: `dopemux.memory.transcript_ingest.ingest_transcript_file`
- **Produces**: CLI command `dopemux memory ingest-transcript <path> [--workspace-id TEXT] [--repo-root PATH]`

**Import style note (verified, not optional)**: every other command in this file (`emit`, `copilot`, `copilot_list`) imports its dependencies lazily, inside the function body. That convention was tried for this command and **fails the CLI test**: `monkeypatch.setattr(memory_commands_module, "ingest_transcript_file", ...)` sets an attribute on the module namespace that a function-local `from dopemux.memory.transcript_ingest import ingest_transcript_file` never reads (the local import re-binds the name inside the function's own scope at call time, shadowing the monkeypatched module attribute). Step 6.3 below imports `ingest_transcript_file` at **module level** (top of `memory_commands.py`, alongside the other top-level imports) specifically so the monkeypatch target and the name the function actually calls are the same object. Do not lazy-import this one dependency even though the surrounding commands do.

### Steps

- [ ] **6.1 — Write the failing CLI test.** Create `tests/unit/test_cli_memory_ingest_transcript.py`:

```python
from pathlib import Path

from click.testing import CliRunner

import dopemux.commands.memory_commands as memory_commands_module
from dopemux.cli import cli
from dopemux.memory.transcript_ingest import IngestResult


def test_ingest_transcript_cli_invokes_ingest_function(monkeypatch, tmp_path):
    calls = {}

    def _fake_ingest(path, workspace_id, repo_root):
        calls["path"] = path
        calls["workspace_id"] = workspace_id
        calls["repo_root"] = repo_root
        return IngestResult(ingested=3, skipped=1, quarantined=0, duplicate=0)

    monkeypatch.setattr(
        memory_commands_module, "ingest_transcript_file", _fake_ingest, raising=False
    )

    transcript_path = tmp_path / "session.jsonl"
    transcript_path.write_text('{"type":"user"}\n', encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["memory", "ingest-transcript", str(transcript_path)],
    )

    assert result.exit_code == 0, result.output
    assert calls["path"] == transcript_path
    assert "3" in result.output  # ingested count surfaced to the operator
    assert "1" in result.output  # skipped count surfaced to the operator


def test_ingest_transcript_cli_rejects_missing_file():
    runner = CliRunner()
    result = runner.invoke(
        cli, ["memory", "ingest-transcript", "/nonexistent/path/session.jsonl"]
    )
    assert result.exit_code != 0
```

- [ ] **6.2 — Run and confirm failure:**

```bash
mise exec -- python -m pytest tests/unit/test_cli_memory_ingest_transcript.py -v
```

Expected output: `test_ingest_transcript_cli_invokes_ingest_function` fails (`Error: No such command 'ingest-transcript'` in `result.output`, non-zero exit code); `test_ingest_transcript_cli_rejects_missing_file` passes trivially (command doesn't exist, so it already exits non-zero) — confirm by reading output, don't rely on the second test alone to prove red state.

- [ ] **6.3 — Add the module-level import, then the command, to `src/dopemux/commands/memory_commands.py`.**

First, add one import line near the top of the file, immediately after the existing `from ..ui.theme import ...` line (do not add it inside a function body — see the import-style note above):

```python
from ..memory.transcript_ingest import ingest_transcript_file
```

Then insert the command itself immediately before the `# EASY LAUNCH SHORTCUTS` marker comment near the end of the file (after the `copilot_list` function, before line 390's comment block):

```python
@memory.command("ingest-transcript")
@click.argument(
    "transcript_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--workspace-id",
    type=str,
    default=None,
    help="🗂️  Workspace Coordinate: Override workspace_id (default: repo root path).",
)
@click.option(
    "--repo-root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="🔬 Repository Coordinate: Project root for ledger synchronization.",
)
def ingest_transcript(
    transcript_path: Path, workspace_id: Optional[str], repo_root: Optional[Path]
):
    """
    📼 Transcript Ingest: Parse a Claude Code session JSONL into the raw ledger

    Reads a Claude Code session transcript file (~/.claude/projects/<slug>/
    <uuid>.jsonl) and writes each conversation turn to the per-project raw
    ledger (raw_activity_events) via the capture spine. Writes ONLY to the
    raw ledger -- no ConPort writes, no dope-context writes. Turns without a
    source timestamp, or whose redaction fails, are quarantined instead of
    ingested. Safe to re-run: ingest is idempotent.
    """
    from dopemux.memory.capture_client import resolve_repo_root_strict

    root = repo_root.resolve() if repo_root else resolve_repo_root_strict()
    ws_id = workspace_id or str(root)

    result = ingest_transcript_file(transcript_path, workspace_id=ws_id, repo_root=root)

    console.logger.info(f"[success]✓[/success] Transcript ingest complete: {transcript_path}")
    console.logger.info(f"  Ingested:    {result.ingested}")
    console.logger.info(f"  Duplicate:   {result.duplicate}")
    console.logger.info(f"  Quarantined: {result.quarantined}")
    console.logger.info(f"  Skipped:     {result.skipped}")
```

Note: the function body calls the bare name `ingest_transcript_file(...)`, which Python resolves against the **module's global namespace** at call time — that's the module-level import you added at the top of the file in this step. `monkeypatch.setattr(memory_commands_module, "ingest_transcript_file", _fake_ingest, raising=False)` replaces that same global binding, so the function picks up the fake on the next call. This only works because the import is module-level; it was verified to fail (the fake is never invoked, `calls` dict stays empty, `KeyError` on `calls["path"]`) when the import was tried inside the function body instead, because a function-local `from ... import` creates a name binding private to that call, invisible to `monkeypatch.setattr` on the module object.

- [ ] **6.4 — Run and confirm pass:**

```bash
mise exec -- python -m pytest tests/unit/test_cli_memory_ingest_transcript.py -v
```

Expected output: both tests pass — `2 passed`. If `test_ingest_transcript_cli_invokes_ingest_function` fails with the fake never being called (real ledger touched instead), apply the module-level-import fix described in 6.3 and re-run.

- [ ] **6.5 — Run the full transcript_ingest + CLI test files together to confirm no interaction issues:**

```bash
mise exec -- python -m pytest tests/unit/test_transcript_ingest.py tests/unit/test_cli_memory_ingest_transcript.py -v
```

Expected output: `24 passed` (22 from `test_transcript_ingest.py` + 2 from `test_cli_memory_ingest_transcript.py`).

- [ ] **6.6 — Commit.**

```bash
git add src/dopemux/commands/memory_commands.py tests/unit/test_cli_memory_ingest_transcript.py
git commit -m "$(cat <<'EOF'
feat(cli): add `dopemux memory ingest-transcript` command (TP-MCF-002)

Adds ingest-transcript to the existing `memory` Click group (already
registered in cli.py:3219-3221 -- no new group registration needed).
Modeled on the working `capture emit` command, not `capture copilot` (which
imports a non-existent adapters module -- pre-existing bug, untouched here).

Usage: dopemux memory ingest-transcript <path-to-session.jsonl>
       [--workspace-id TEXT] [--repo-root PATH]
EOF
)"
```

---

## 7. Task 7 — Final verification: full targeted suite + proof-gate checklist

### 7.1 Run the full targeted suite

```bash
cd /Users/hue/code/dopemux-mvp/.claude/worktrees/trusting-engelbart-d2fbfe
mise exec -- python -m pytest tests/unit/test_transcript_ingest.py tests/unit/test_cli_memory_ingest_transcript.py tests/unit/test_memory_capture_client.py -v
```

Expected output: all tests pass — `47 passed` (22 in `test_transcript_ingest.py` + 2 in `test_cli_memory_ingest_transcript.py` + 23 pre-existing in `test_memory_capture_client.py`, which must be unaffected since this packet does not modify `capture_client.py`). This exact combination (22+2+23=47) was run and confirmed passing during plan authoring — see the governance footer. Confirm exit code 0.

### 7.2 Proof-gate checklist (from `claudedocs/tp-mcf-001-authority-map-2026-07-04.md` §4 TP-MCF-002 and `claudedocs/memory-context-fabric-design-2026-07-04.md` §5)

Run each check and record PASS/FAIL — do not mark anything PASS without having actually run it in this session:

- [ ] **git status before/after** — run `git status` and `git diff --stat` now; confirm only the files listed in §0 "File-level scope" changed:

```bash
git status
git diff --stat main...HEAD
```

- [ ] **Redaction test** (secret never reaches the ledger on redaction failure): `test_ingest_transcript_file_quarantines_on_redaction_failure` — already run and passing in Task 5.

- [ ] **Redaction-success contrast test** (a scrubbed secret still ingests, proving quarantine is keyed off failure, not secret-presence): `test_ingest_transcript_file_scrubs_secret_and_still_ingests` — already run and passing in Task 5.

- [ ] **Replay/idempotency test** (re-ingest produces identical ledger row count, rejects nothing new on the second pass): `test_ingest_transcript_file_is_idempotent_on_replay` — already run and passing in Task 5.

- [ ] **Stable-timestamp test** (missing source ts never falls back to `now()`, quarantines instead; and a present source ts is stored verbatim in `ts_utc`): `test_ingest_transcript_file_quarantines_missing_timestamp_turn` + `test_ingest_transcript_file_stores_source_timestamp_not_now` — already run and passing in Task 5.

- [ ] **No-ConPort / no-dope-context-write test**: `test_ingest_transcript_file_no_conport_or_dope_context_imports` — already run and passing in Task 5 (this is the authoritative check; it scans only `import`/`from` statement lines, not prose). Additionally run this repo-wide grep restricted to actual import lines, to double-check no ConPort/dope-context call was introduced anywhere in this packet's files — note this grep is intentionally narrower than a whole-file substring search, because both files' docstrings/comments legitimately *name* the invariant ("no ConPort writes, no dope-context writes") in prose, which is expected and must not be flagged:

```bash
grep -nE "^\s*(import|from) .*(conport|dope_context|dope-context)" src/dopemux/memory/transcript_ingest.py src/dopemux/commands/memory_commands.py
```

Expected output: no matches (exit code 1 from grep). Do **not** use an unanchored `grep -n "conport\|dope_context"` here — it will match the docstring/comment prose in both files (confirmed during plan verification) and produce a false-FAIL reading; the import-anchored pattern above is the correct check.

- [ ] **Fail-open test** (malformed lines never raise out of `ingest_transcript_file`): `test_ingest_transcript_file_never_raises_on_fully_malformed_file` + `test_ingest_transcript_file_skips_non_turn_and_malformed_lines` — already run and passing in Task 5.

- [ ] **Non-promotable event types confirmed**: run this check to confirm `transcript.*` was never added to the promotable allowlist:

```bash
grep -n "transcript\." src/dopemux/memory/capture_client.py services/working-memory-assistant/promotion/promotion.py
```

Expected output: no matches in either file (this packet must not touch `PROMOTABLE_CAPTURE_EVENT_TYPES` in `capture_client.py` or the allowlist in `promotion.py`).

- [ ] **Command outputs + exit codes** — capture the final full-suite run's exit code:

```bash
mise exec -- python -m pytest tests/unit/test_transcript_ingest.py tests/unit/test_cli_memory_ingest_transcript.py tests/unit/test_memory_capture_client.py -v; echo "exit code: $?"
```

Expected: `exit code: 0`.

### 7.3 Do not commit this task

Task 7 is verification-only — there is nothing to commit. If any check fails, return to the relevant task, fix under TDD (failing assertion → minimal fix → passing), and re-run this section before considering the packet done.

### 7.4 What is explicitly NOT built in this packet (confirm scope discipline)

- No file-watcher daemon (ambient watching arrives with the Fabric service, a later packet).
- No Codex transcript format support (Claude Code JSONL only).
- No promotion to the curated chronicle (`work_log_entries`) — that is TP-MCF-003, which also requires the `conversation.decision_candidate` event/schema this packet deliberately does not touch.
- No ConPort writes, no dope-context writes, no semantic indexing of transcript content.
- No changes to `capture_client.py`, `redactor.py`, or `promotion.py`.

---

## Governance footer

**Authority used**: `claudedocs/memory-context-fabric-design-2026-07-04.md` (v3), `claudedocs/tp-mcf-001-authority-map-2026-07-04.md`, `claudedocs/memory-context-fabric-interfaces-2026-07-04.md`; runtime code `src/dopemux/memory/capture_client.py`, `services/working-memory-assistant/promotion/redactor.py`, `src/dopemux/commands/memory_commands.py`, `src/dopemux/cli.py`; existing test patterns in `tests/unit/test_memory_capture_client.py` and `tests/unit/test_cli_capture_commands.py`; a real 660-line Claude Code session transcript (`~/.claude/projects/-Users-hue-code-dopemux-mvp/6e030b42-66a3-46e3-9588-f1c3cceb683f.jsonl`) inspected directly to verify the JSONL schema and validate the turn-classification rule (counts reconciled: `user_prompt=11, assistant_response=167, tool_call=92, tool_result=92, skipped=298`, total 660).
**Validation**: plan-authoring only — the code in this plan has not been executed; every "expected output" above is a prediction based on the parser logic and existing `capture_client` behavior, not an observed test run. The implementing agent must actually run every command and confirm PASS before proceeding to the next step — do not mark a step done without having seen the real output.
**Rollback**: `git reset --hard <commit-before-task-1>` or, per-task, `git revert <task-commit-sha>`; no schema/migration changes are made, so rollback is a pure file/commit reversal with no data-shape cleanup required. The one stateful artifact this packet introduces (`.dopemux/quarantine/transcript/*.json` files) is git-ignorable and safe to delete manually if a real repo run needs to be undone.
