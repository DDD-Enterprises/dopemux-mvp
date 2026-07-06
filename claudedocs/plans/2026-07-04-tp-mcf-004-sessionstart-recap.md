# TP-MCF-004 — Bounded SessionStart Recap Injection (Implementation Plan)

> **For agentic workers:** Execute this plan task-by-task via superpowers:subagent-driven-development or superpowers:executing-plans if available; otherwise execute the checkbox (`- [ ]`) steps literally, in order, committing exactly where the plan says. Read the master plan first: `claudedocs/plans/2026-07-04-memory-context-fabric-build-plan.md` (global constraints + hand-off protocol).
**Date**: 2026-07-04 · **Packet**: TP-MCF-004 (Memory Context Fabric, Injection Phase 1) · **Status**: PLAN (ready for execution)
**Branch**: `claude/memory-context-fabric` · **Worktree**: `/Users/hue/code/dopemux-mvp/.claude/worktrees/trusting-engelbart-d2fbfe`
**Interpreter**: `mise exec -- python` (Python 3.12.13 — verified; do NOT use bare `python3`, the harness one is 3.9)

---

## 0. Goal

Extend the **existing** `native_hooks.py` SessionStart injection path with a **bounded, token-budgeted, authority-labeled Top-3 recap** read **directly from the local chronicle SQLite ledger**. No semantic fusion. No ConPort calls. No dope-context calls. **No network calls at all** — the dope-memory HTTP service may be down (it is down right now), so the recap is a direct local read.

### Authority documents (read before executing; all committed in this repo)

| Doc | What it governs here |
|---|---|
| `claudedocs/memory-context-fabric-design-2026-07-04.md` §4, §6 row TP-MCF-004 | scope gates: token budget, Top-3 default, authority labels, **no semantic fusion** |
| `claudedocs/memory-context-fabric-interfaces-2026-07-04.md` §2.4, §4 | `ContextBundle`/`ContextItem` schemas (implement **exactly**); invariants 5 (provenance only lowers trust), 6 (token budget), 7 (graceful degradation) |
| `claudedocs/tp-mcf-001-authority-map-2026-07-04.md` §1 Domain E | `native_hooks.py:335-351` SessionStart injection is the extension point |

### Grounded runtime facts (verified against code in this worktree — cite these, do not re-derive)

1. **SessionStart handler** — `src/dopemux/claude/native_hooks.py:335-351`, method `NativeHookAdapter._on_session_start`. It composes three existing injections and returns hook output:
   ```python
   def _on_session_start(self) -> Tuple[int, Dict[str, Any]]:
       reset_edit_counter(self.project_root, self.session_id)
       mcp_health = emit_mcp_health(self.project_root)
       orch_ctx = emit_session_context(self.project_root)
       state = self._active_state()
       if not state:
           combined = "\n\n".join(filter(None, [mcp_health, orch_ctx]))
           if combined:
               return self._allow(additional_context=combined, hook_event_name="SessionStart")
           return self._allow()
       workflow_ctx = _workflow_context_lines(state, include_gates=True)
       combined = "\n\n".join(filter(None, [mcp_health, orch_ctx, workflow_ctx]))
       return self._allow(
           system_message=f"Dopemux workflow mode: {state.mode}",
           additional_context=combined or None,
           hook_event_name="SessionStart",
       )
   ```
   The recap is appended as a **fourth part** of that same `"\n\n".join(filter(None, [...]))` composition (third part in the no-workflow branch). Fail-open style to mirror: the module's try/except import fallbacks (`native_hooks.py:30-74`) and `_emit_bounded_hook_error_capture`'s outer `try/except Exception: return None` (`native_hooks.py:166-194`); also `handle_event`'s blanket reliability fallback (`native_hooks.py:331-332`).
2. **Ledger path resolution** — `src/dopemux/memory/capture_client.py:255-259`:
   ```python
   def _resolve_ledger_path(repo_root: Path) -> Path:
       override = os.getenv("DOPEMUX_CAPTURE_LEDGER_PATH", "").strip()
       if override:
           return Path(override).expanduser().resolve()
       return (repo_root / ".dopemux" / "chronicle.sqlite").resolve()
   ```
   We **reuse this function** (import it), we do not copy it — the read path can then never drift from the write path.
3. **Chronicle schema** — `services/working-memory-assistant/chronicle/schema.sql`. Columns we query:
   - `work_log_entries` (schema.sql:29-81): `id, workspace_id, instance_id, session_id, ts_utc, category (CHECK), entry_type (CHECK), summary, details_json, outcome, importance_score, tags_json, source_event_id, source_event_type, source_adapter, source_event_ts_utc, promotion_rule, promotion_ts_utc, created_at_utc, updated_at_utc` (+ optional linkage columns).
   - `raw_activity_events` (schema.sql:5-20): `id, workspace_id, instance_id, session_id, ts_utc, event_type, source, payload_json, redaction_level, ttl_days, created_at_utc`.
4. **Token heuristic (repo convention — verified by grep)** — `src/dopemux/freeflow.py:220-221`:
   ```python
   def estimate_text_tokens(value: str) -> int:
       return max(1, (len(value or "") + 3) // 4)
   ```
   and `src/dopemux/mcp/broker.py:943` (`return len(result) // 4  # Rough tokens estimation`), `src/dopemux/ux/wizard/cost_profiles.py:146` (`input_tokens ≈ corpus_chars / 4`). We adopt the freeflow ceil-division form with constant `TOKENS_PER_CHAR_DIVISOR = 4`.
5. **Read-only SQLite pattern (repo precedent)** — `src/dopemux/orchestrator/canonical_readview.py:21-36` (`_connect_ro`: percent-encoded `db_path.resolve().as_uri() + "?mode=ro"`, `sqlite3.connect(uri, uri=True)`, existence check first — the comment there explains why `as_uri()` is required so URI metacharacters can't bypass `mode=ro`) and `src/dopemux/memory/global_rollup.py:194-198` (`_connect_project_read_only`, same `mode=ro` idea against **this exact chronicle ledger**). We mirror `canonical_readview._connect_ro` (the safer of the two).
6. **Session-boundary event type** — `services/working-memory-assistant/eventbus_consumer.py:384` treats `event_type == "session.ended"` as the explicit session-end signal. Recap optionally reads the most recent such row from `raw_activity_events` for a "Last session ended at X" line (best-effort; absent rows are fine).
7. **Candidate-decision markers** — `promotion_rule = "conversation_candidate_v1"` and trust `"conversation-derived"` are defined by the authority map §4 (TP-MCF-003 schema). **Grep-verified: no code emits these values yet** — the recap must still label such rows correctly the day TP-MCF-003 lands, using literal string constants.
8. **Existing test files (verified present)** —
   - `tests/test_native_hooks_workflow.py` — the real native-hooks test file (7 tests, all passing at baseline; verified by running it). Its `handle_event("SessionStart", {...})` pattern (lines 36-61) is what our hook tests extend.
   - `tests/unit/test_memory_capture_client.py` — hermetic-ledger precedent: monkeypatches `DOPEMUX_CAPTURE_LEDGER_PATH` to a `tmp_path` file (lines 47-49). Our tests build the tmp ledger by applying `schema.sql` directly with `executescript` (no Redis, no service).
9. **ISO-parse convention** — `src/dopemux/freeflow.py:202-210` `parse_iso_datetime` (tolerates `Z` suffix, returns UTC-aware). We mirror it.

### Architecture of the change

```
SessionStart hook (sync, must never fail)
  └─ _emit_recap_context(project_root)          [native_hooks.py — NEW, fail-open wrapper]
       ├─ kill switch: DOPEMUX_RECAP_INJECTION=off → None
       ├─ lazy import of dopemux.memory.recap    (ImportError can never break the hook module)
       ├─ resolve_ledger_path(project_root)      [reuses capture_client._resolve_ledger_path]
       ├─ build_recap_bundle(workspace_id, ledger_path)   [recap.py — NEW]
       │    ├─ _connect_ro(...)  file:...?mode=ro  → structurally read-only
       │    ├─ SELECT top rows from work_log_entries (bounded LIMIT 50) + newest session.ended
       │    ├─ window (hours_back) → authority labels → sort most-recent-first → Top-k
       │    └─ token budget: header + whole items, prefix-keep, drop rest, truncated flag
       └─ render_recap(bundle) → "## Memory recap (last 24h)" markdown block
  └─ combined = "\n\n".join(filter(None, [mcp_health, orch_ctx, (workflow_ctx), recap_ctx]))
```

### Files touched (complete list — touch nothing else)

| File | Action |
|---|---|
| `src/dopemux/memory/recap.py` | **NEW** — schemas, read path, budget, renderer |
| `tests/unit/test_recap.py` | **NEW** — hermetic unit tests |
| `src/dopemux/claude/native_hooks.py` | **EDIT** — `_emit_recap_context` helper + `_on_session_start` composition |
| `tests/test_native_hooks_workflow.py` | **EDIT** — append hook-wiring tests |

Do **not** edit `src/dopemux/memory/__init__.py` (recap is imported lazily by the hook; keeping the package `__init__` untouched keeps import cost and blast radius at zero). Do **not** edit `schema.sql`, `capture_client.py`, or any `.claude/` config.

### Global constraints (every task)

- **TDD**: write the failing test first, run it (RED), implement, run again (GREEN). Never skip the RED run.
- **One commit per task**, staging only that task's files. Do not commit unrelated dirty files that may pre-exist in the worktree.
- Run all commands **from the worktree root**: `/Users/hue/code/dopemux-mvp/.claude/worktrees/trusting-engelbart-d2fbfe`.
- **Hermetic tests**: no Redis, no HTTP, no Docker, no dope-memory service. Local SQLite + `tmp_path` only.
- **Fail-open invariant**: no code path added to `native_hooks.py` may raise out of `_on_session_start`. Missing ledger / empty ledger / malformed rows / corrupt file → inject nothing.
- **Read-only invariant (structural)**: recap opens the ledger via `file:...?mode=ro` URI only. No INSERT/UPDATE/DELETE anywhere in `recap.py`.
- **Interfaces §2.4 exactly**: `ContextBundle(items, token_cost, truncated, workspace_id)`, `ContextItem(content, source_system, authority_label, trust, freshness, provenance)` — these names and this order.

### Pre-flight (no commit)

```bash
cd /Users/hue/code/dopemux-mvp/.claude/worktrees/trusting-engelbart-d2fbfe
git status --short            # note pre-existing dirty files; leave them alone
git branch --show-current     # expected: claude/memory-context-fabric
mise exec -- python --version # expected: Python 3.12.13
mise exec -- python -m pytest tests/test_native_hooks_workflow.py -q
```
Expected last output: `7 passed` (dots line `.......`). If the baseline is not 7 passed, STOP and report — do not build on a broken baseline.

---

## Task 1 — Contracts: `ContextItem` / `ContextBundle` + token estimator

**Files**: `tests/unit/test_recap.py` (new), `src/dopemux/memory/recap.py` (new)
**Interfaces produced**: `recap.ContextItem`, `recap.ContextBundle` (interfaces doc §2.4, exact), `recap.estimate_tokens(text) -> int`, constants `TOKENS_PER_CHAR_DIVISOR`, `RECAP_TITLE`.

### Steps

- [ ] **1.1 (RED)** Create `tests/unit/test_recap.py` with exactly this content. Note the deliberate style: everything is referenced through the `recap` module namespace (`recap.build_recap_bundle`, not a `from`-import), so later tasks' tests fail with a clean `AttributeError` instead of breaking collection.

```python
"""Hermetic tests for the TP-MCF-004 SessionStart recap module.

Builds a tmp_path chronicle by applying the canonical schema
(services/working-memory-assistant/chronicle/schema.sql) directly -- the same
schema the runtime ledger uses (capture_client._resolve_wma_schema_path).
No Redis, no HTTP, no dope-memory service, no network.
"""

from __future__ import annotations

import hashlib
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from dopemux.memory import recap

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    REPO_ROOT / "services" / "working-memory-assistant" / "chronicle" / "schema.sql"
)

WORKSPACE = "/test/workspace"


def _utc_iso(*, hours_ago: float = 0.0) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


def _make_ledger(tmp_path: Path) -> Path:
    """Apply the canonical chronicle schema to a fresh tmp SQLite file."""
    ledger = tmp_path / "chronicle.sqlite"
    conn = sqlite3.connect(str(ledger))
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()
    return ledger


def _insert_work_log_entry(
    ledger: Path,
    *,
    summary: str,
    hours_ago: float = 1.0,
    workspace_id: str = WORKSPACE,
    entry_type: str = "decision",
    category: str = "implementation",
    outcome: str = "success",
    promotion_rule: str = "eventbus_promotion_v1",
    ts_utc: str | None = None,
) -> str:
    """Insert a curated chronicle row satisfying every NOT NULL/CHECK constraint."""
    entry_id = uuid.uuid4().hex
    ts = ts_utc if ts_utc is not None else _utc_iso(hours_ago=hours_ago)
    now = _utc_iso()
    conn = sqlite3.connect(str(ledger))
    try:
        conn.execute(
            """
            INSERT INTO work_log_entries (
                id, workspace_id, instance_id, session_id, ts_utc,
                category, entry_type, summary, outcome, importance_score,
                tags_json,
                source_event_id, source_event_type, source_adapter,
                source_event_ts_utc, promotion_rule, promotion_ts_utc,
                created_at_utc, updated_at_utc
            ) VALUES (?, ?, 'A', NULL, ?, ?, ?, ?, ?, 5, '[]',
                      ?, 'decision.logged', 'test', ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                workspace_id,
                ts,
                category,
                entry_type,
                summary,
                outcome,
                f"evt-{entry_id}",
                ts,
                promotion_rule,
                now,
                now,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return entry_id


def _insert_session_ended(
    ledger: Path, *, hours_ago: float = 2.0, workspace_id: str = WORKSPACE
) -> str:
    """Insert a raw session-boundary event (event_type per eventbus_consumer.py:384)."""
    event_id = uuid.uuid4().hex
    ts = _utc_iso(hours_ago=hours_ago)
    conn = sqlite3.connect(str(ledger))
    try:
        conn.execute(
            """
            INSERT INTO raw_activity_events (
                id, workspace_id, instance_id, session_id, ts_utc,
                event_type, source, payload_json, redaction_level,
                ttl_days, created_at_utc
            ) VALUES (?, ?, 'A', NULL, ?, 'session.ended', 'test', '{}',
                      'strict', 7, ?)
            """,
            (event_id, workspace_id, ts, _utc_iso()),
        )
        conn.commit()
    finally:
        conn.close()
    return event_id


class TestContracts:
    """interfaces doc §2.4 -- field names and order are the contract."""

    def test_context_item_fields_match_interfaces_2_4(self):
        item = recap.ContextItem(
            content="decision: x [success]",
            source_system="dope-memory",
            authority_label="canonical",
            trust="high",
            freshness="2026-07-04T00:00:00+00:00",
            provenance={"entry_id": "abc"},
        )
        assert list(item.__dataclass_fields__) == [
            "content",
            "source_system",
            "authority_label",
            "trust",
            "freshness",
            "provenance",
        ]
        assert item.provenance == {"entry_id": "abc"}

    def test_context_bundle_fields_match_interfaces_2_4(self):
        bundle = recap.ContextBundle(
            items=[], token_cost=0, truncated=False, workspace_id="w"
        )
        assert list(bundle.__dataclass_fields__) == [
            "items",
            "token_cost",
            "truncated",
            "workspace_id",
        ]

    def test_estimate_tokens_matches_repo_char_div_4_convention(self):
        # freeflow.py:220-221 -- max(1, (len + 3) // 4)
        assert recap.TOKENS_PER_CHAR_DIVISOR == 4
        assert recap.estimate_tokens("") == 1
        assert recap.estimate_tokens("abcd") == 1
        assert recap.estimate_tokens("abcde") == 2
        assert recap.estimate_tokens("x" * 400) == 100
```

- [ ] **1.2 (RED run)**
```bash
mise exec -- python -m pytest tests/unit/test_recap.py -q
```
Expected output: collection error, `1 error` — `ModuleNotFoundError: No module named 'dopemux.memory.recap'`.

- [ ] **1.3 (GREEN)** Create `src/dopemux/memory/recap.py` with exactly this content:

```python
"""Bounded SessionStart recap over the local chronicle ledger (TP-MCF-004).

Design authority:
- claudedocs/memory-context-fabric-design-2026-07-04.md §4 (Injection Phase 1),
  §6 row TP-MCF-004 (token budget, Top-3, authority labels, NO semantic fusion)
- claudedocs/memory-context-fabric-interfaces-2026-07-04.md §2.4 (schemas),
  §4 invariants 5 (provenance only lowers trust), 6 (token budget),
  7 (graceful degradation)
- claudedocs/tp-mcf-001-authority-map-2026-07-04.md §1 Domain E

Hard constraints:
- LOCAL SQLite read ONLY. No network, no ConPort, no dope-context, no HTTP.
  The dope-memory HTTP service may be down; this module never depends on it.
- Read-only by construction: the ledger is opened via a ``file:...?mode=ro``
  SQLite URI (mirrors src/dopemux/orchestrator/canonical_readview.py:21-36
  and src/dopemux/memory/global_rollup.py:194-198), so this module is
  structurally incapable of writing to the chronicle.
- Fail-open: missing ledger / empty ledger / malformed rows / corrupt file
  => ``None``. The SessionStart hook must never break because of this module.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from dopemux.memory.capture_client import (
    _resolve_ledger_path as _capture_resolve_ledger_path,
)

# --- Token estimation --------------------------------------------------------
# Repo convention: ~4 chars per token, ceil division.
# Verified precedents: src/dopemux/freeflow.py:220-221 (estimate_text_tokens),
# src/dopemux/mcp/broker.py:943, src/dopemux/ux/wizard/cost_profiles.py:146.
TOKENS_PER_CHAR_DIVISOR = 4


def estimate_tokens(text: str) -> int:
    """Conservative char//4 token estimate (mirrors freeflow.estimate_text_tokens)."""
    length = len(text or "")
    return max(1, (length + TOKENS_PER_CHAR_DIVISOR - 1) // TOKENS_PER_CHAR_DIVISOR)


# --- Authority / trust vocabulary (interfaces doc §2.4, exact strings) --------
AUTHORITY_CANONICAL = "canonical"
AUTHORITY_CONVERSATION_INFERRED = "conversation-inferred"
TRUST_HIGH = "high"
TRUST_CONVERSATION_DERIVED = "conversation-derived"

# TP-MCF-003 candidate-decision marker (authority map §4). No writer emits this
# value yet (grep-verified 2026-07-04); recap must still label such rows
# correctly the day promotion lands.
CONVERSATION_CANDIDATE_PROMOTION_RULE = "conversation_candidate_v1"

# Session-boundary raw event type (services/.../eventbus_consumer.py:384).
SESSION_BOUNDARY_EVENT_TYPE = "session.ended"

# Fixed recap block title (TP-MCF-004 contract; hours_back default is 24).
RECAP_TITLE = "## Memory recap (last 24h)"

# Bounded work: never scan more than this many chronicle rows per recap.
_FETCH_LIMIT = 50
# Bounded latency: SQLite busy timeout in seconds (hook runs synchronously).
_SQLITE_TIMEOUT_SECONDS = 1.0


@dataclass
class ContextItem:
    """interfaces doc §2.4 ContextItem -- field names/order are contract."""

    content: str
    source_system: str  # "dope-memory" | "conport" | "dope-context"
    authority_label: str  # "canonical" | "mirror" | "derived" | "conversation-inferred"
    trust: str  # "high" | "conversation-derived"
    freshness: str  # ISO timestamp
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextBundle:
    """interfaces doc §2.4 ContextBundle -- field names/order are contract."""

    items: list[ContextItem] = field(default_factory=list)
    token_cost: int = 0  # enforced <= budget (invariant 6)
    truncated: bool = False
    workspace_id: str = ""
```

- [ ] **1.4 (GREEN run)**
```bash
mise exec -- python -m pytest tests/unit/test_recap.py -q
```
Expected output: `3 passed`.

- [ ] **1.5 (Commit)**
```bash
git add src/dopemux/memory/recap.py tests/unit/test_recap.py
git commit -m "feat(memory): TP-MCF-004 ContextBundle/ContextItem contracts + token estimator"
git log --oneline -1   # verify the commit landed on claude/memory-context-fabric
```

---

## Task 2 — Read path: `resolve_ledger_path`, `_connect_ro`, `build_recap_bundle`

**Files**: `tests/unit/test_recap.py` (append), `src/dopemux/memory/recap.py` (append)
**Interfaces produced**:
- `recap.resolve_ledger_path(repo_root: Path) -> Path` — delegates to `capture_client._resolve_ledger_path` (env `DOPEMUX_CAPTURE_LEDGER_PATH` override, else `<repo>/.dopemux/chronicle.sqlite`).
- `recap._connect_ro(ledger_path: Path) -> sqlite3.Connection` — strictly read-only, mirrors `canonical_readview.py:21-36`.
- `recap.build_recap_bundle(workspace_id: str, ledger_path: Path, *, hours_back: int = 24, k: int = 3, token_budget: int = 700) -> ContextBundle | None` — **exactly this signature** (the token budget is *accepted* in this task and *enforced* in Task 3).

Behavior contract for this task: Top-`k` most recent `work_log_entries` within `hours_back` for the given `workspace_id`; curated rows → `authority_label="canonical"`, `trust="high"`; rows with `promotion_rule="conversation_candidate_v1"` → `authority_label="conversation-inferred"`, `trust="conversation-derived"`; optional "Last session ended at X" item from the newest `raw_activity_events` row with `event_type='session.ended'` (window-gated, does not count against `k`); all items sorted most-recent-first; missing/empty/corrupt ledger and malformed rows → `None` / skipped, never an exception.

### Steps

- [ ] **2.1 (RED)** Append to `tests/unit/test_recap.py`:

```python
class TestResolveLedgerPath:
    """Reuses capture_client._resolve_ledger_path (capture_client.py:255-259)."""

    def test_env_override_wins(self, tmp_path, monkeypatch):
        override = tmp_path / "custom.sqlite"
        monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(override))
        assert recap.resolve_ledger_path(tmp_path) == override.resolve()

    def test_default_is_dot_dopemux_chronicle(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DOPEMUX_CAPTURE_LEDGER_PATH", raising=False)
        expected = (tmp_path / ".dopemux" / "chronicle.sqlite").resolve()
        assert recap.resolve_ledger_path(tmp_path) == expected


class TestBuildRecapBundle:
    def test_top_k_selection_and_ordering_most_recent_first(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        for idx, hours in enumerate([5.0, 4.0, 3.0, 2.0, 1.0]):
            _insert_work_log_entry(ledger, summary=f"entry-{idx}", hours_ago=hours)
        bundle = recap.build_recap_bundle(WORKSPACE, ledger)
        assert bundle is not None
        assert len(bundle.items) == 3  # Top-3 default (design spec §6 TP-MCF-004)
        assert "entry-4" in bundle.items[0].content  # 1h ago -- newest first
        assert "entry-3" in bundle.items[1].content
        assert "entry-2" in bundle.items[2].content
        assert bundle.workspace_id == WORKSPACE
        assert bundle.truncated is False

    def test_hours_back_window_excludes_stale_rows(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        _insert_work_log_entry(ledger, summary="fresh-row", hours_ago=1.0)
        _insert_work_log_entry(ledger, summary="stale-row", hours_ago=30.0)
        bundle = recap.build_recap_bundle(WORKSPACE, ledger, hours_back=24)
        assert bundle is not None
        contents = [item.content for item in bundle.items]
        assert any("fresh-row" in c for c in contents)
        assert not any("stale-row" in c for c in contents)

    def test_workspace_isolation(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        _insert_work_log_entry(
            ledger, summary="other-workspace-row", workspace_id="/elsewhere"
        )
        assert recap.build_recap_bundle(WORKSPACE, ledger) is None

    def test_curated_rows_labeled_canonical_high_trust(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        entry_id = _insert_work_log_entry(ledger, summary="curated-row")
        bundle = recap.build_recap_bundle(WORKSPACE, ledger)
        assert bundle is not None
        item = bundle.items[0]
        assert item.authority_label == "canonical"
        assert item.trust == "high"
        assert item.source_system == "dope-memory"
        assert item.provenance["entry_id"] == entry_id
        assert item.provenance["source_event_id"] == f"evt-{entry_id}"

    def test_candidate_rows_labeled_conversation_inferred(self, tmp_path):
        # Invariant 5 (interfaces §4): provenance only LOWERS trust.
        ledger = _make_ledger(tmp_path)
        _insert_work_log_entry(
            ledger,
            summary="candidate-row",
            promotion_rule="conversation_candidate_v1",
        )
        bundle = recap.build_recap_bundle(WORKSPACE, ledger)
        assert bundle is not None
        item = bundle.items[0]
        assert item.authority_label == "conversation-inferred"
        assert item.trust == "conversation-derived"

    def test_session_boundary_item_ordered_by_recency(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        _insert_work_log_entry(ledger, summary="work-row", hours_ago=1.0)
        _insert_session_ended(ledger, hours_ago=2.0)
        bundle = recap.build_recap_bundle(WORKSPACE, ledger)
        assert bundle is not None
        assert len(bundle.items) == 2  # boundary does not count against k
        assert bundle.items[-1].content.startswith("Last session ended at ")
        assert bundle.items[-1].provenance == {"event_type": "session.ended"}
        assert bundle.items[-1].authority_label == "canonical"

    def test_missing_ledger_returns_none(self, tmp_path):
        assert recap.build_recap_bundle(WORKSPACE, tmp_path / "nope.sqlite") is None

    def test_empty_ledger_returns_none(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        assert recap.build_recap_bundle(WORKSPACE, ledger) is None

    def test_corrupt_ledger_returns_none(self, tmp_path):
        garbage = tmp_path / "chronicle.sqlite"
        garbage.write_bytes(b"\x00garbage not a sqlite file\xff" * 64)
        assert recap.build_recap_bundle(WORKSPACE, garbage) is None

    def test_malformed_timestamp_rows_are_skipped_not_fatal(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        _insert_work_log_entry(ledger, summary="good-row", hours_ago=1.0)
        _insert_work_log_entry(ledger, summary="bad-ts-row", ts_utc="not-a-timestamp")
        bundle = recap.build_recap_bundle(WORKSPACE, ledger)
        assert bundle is not None
        contents = [item.content for item in bundle.items]
        assert any("good-row" in c for c in contents)
        assert not any("bad-ts-row" in c for c in contents)
```

- [ ] **2.2 (RED run)**
```bash
mise exec -- python -m pytest tests/unit/test_recap.py -q
```
Expected output: `12 failed, 3 passed` — every failure an `AttributeError: module 'dopemux.memory.recap' has no attribute ...` (`resolve_ledger_path` / `build_recap_bundle`).

- [ ] **2.3 (GREEN)** Append to `src/dopemux/memory/recap.py` (after the `ContextBundle` dataclass, end of file):

```python
def resolve_ledger_path(repo_root: Path) -> Path:
    """Chronicle ledger location.

    Delegates to ``capture_client._resolve_ledger_path`` (capture_client.py:255-259):
    ``DOPEMUX_CAPTURE_LEDGER_PATH`` env override, else
    ``<repo_root>/.dopemux/chronicle.sqlite``. Reuse -- not a copy -- so the
    read path can never drift from the write path.
    """
    return _capture_resolve_ledger_path(repo_root)


def _connect_ro(ledger_path: Path) -> sqlite3.Connection:
    """Open the ledger strictly read-only.

    Mirrors ``canonical_readview._connect_ro`` (canonical_readview.py:21-36):
    the ``file:`` URI is built from the percent-encoded absolute path
    (``as_uri()``) so URI metacharacters in the path (``?``/``#``) cannot be
    parsed as query/fragment and silently bypass ``mode=ro``.
    """
    if not ledger_path.exists():
        raise FileNotFoundError(f"chronicle ledger not found: {ledger_path}")
    uri = ledger_path.resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=_SQLITE_TIMEOUT_SECONDS)
    conn.row_factory = sqlite3.Row
    return conn


def _parse_iso_utc(value: Optional[str]) -> Optional[datetime]:
    """Tolerant ISO-8601 parse (mirrors freeflow.parse_iso_datetime:202-210)."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _item_from_row(row: sqlite3.Row) -> ContextItem:
    """Map one curated work_log_entries row to an authority-labeled item."""
    promotion_rule = str(row["promotion_rule"] or "")
    if promotion_rule == CONVERSATION_CANDIDATE_PROMOTION_RULE:
        authority_label = AUTHORITY_CONVERSATION_INFERRED
        trust = TRUST_CONVERSATION_DERIVED
    else:
        authority_label = AUTHORITY_CANONICAL
        trust = TRUST_HIGH
    content = f"{row['entry_type']}: {row['summary']} [{row['outcome']}]"
    return ContextItem(
        content=content,
        source_system="dope-memory",
        authority_label=authority_label,
        trust=trust,
        freshness=str(row["ts_utc"]),
        provenance={
            "entry_id": row["id"],
            "source_event_id": row["source_event_id"],
        },
    )


def render_item_line(item: ContextItem) -> str:
    """One recap line: ``- [authority_label] content (freshness)``."""
    return f"- [{item.authority_label}] {item.content} ({item.freshness})"


def build_recap_bundle(
    workspace_id: str,
    ledger_path: Path,
    *,
    hours_back: int = 24,
    k: int = 3,
    token_budget: int = 700,
) -> ContextBundle | None:
    """Assemble a bounded recap bundle from the local chronicle. Fail-open.

    Returns ``None`` (inject nothing) on: missing ledger, corrupt/locked
    ledger, no rows for this workspace inside the window. Never raises to the
    caller and never writes (the connection is ``mode=ro`` by construction).
    """
    try:
        conn = _connect_ro(ledger_path)
    except (FileNotFoundError, OSError, ValueError, sqlite3.Error):
        return None

    try:
        rows = conn.execute(
            """
            SELECT id, ts_utc, entry_type, summary, outcome,
                   promotion_rule, source_event_id
            FROM work_log_entries
            WHERE workspace_id = ?
            ORDER BY ts_utc DESC
            LIMIT ?
            """,
            (workspace_id, _FETCH_LIMIT),
        ).fetchall()
        boundary_row = conn.execute(
            """
            SELECT ts_utc FROM raw_activity_events
            WHERE workspace_id = ? AND event_type = ?
            ORDER BY ts_utc DESC
            LIMIT 1
            """,
            (workspace_id, SESSION_BOUNDARY_EVENT_TYPE),
        ).fetchone()
    except sqlite3.Error:
        # Corrupt file, locked DB, or unexpected schema: inject nothing.
        return None
    finally:
        try:
            conn.close()
        except Exception:  # pragma: no cover - close is best-effort
            pass

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    worklog: list[tuple[datetime, ContextItem]] = []
    for row in rows:
        ts = _parse_iso_utc(row["ts_utc"])
        if ts is None or ts < cutoff:
            continue  # malformed or stale rows are skipped, never fatal
        try:
            worklog.append((ts, _item_from_row(row)))
        except (KeyError, IndexError, TypeError):
            continue

    # Deterministic most-recent-first, robust to mixed ISO tz spellings
    # (Python-side parse+sort; the SQL ORDER BY only pre-limits the scan).
    worklog.sort(key=lambda pair: pair[0], reverse=True)
    dated = worklog[:k]

    if boundary_row is not None:
        boundary_ts = _parse_iso_utc(boundary_row["ts_utc"])
        if boundary_ts is not None and boundary_ts >= cutoff:
            dated.append(
                (
                    boundary_ts,
                    ContextItem(
                        content=f"Last session ended at {boundary_row['ts_utc']}",
                        source_system="dope-memory",
                        authority_label=AUTHORITY_CANONICAL,
                        trust=TRUST_HIGH,
                        freshness=str(boundary_row["ts_utc"]),
                        provenance={"event_type": SESSION_BOUNDARY_EVENT_TYPE},
                    ),
                )
            )

    dated.sort(key=lambda pair: pair[0], reverse=True)
    items = [item for _, item in dated]
    if not items:
        return None

    token_cost = estimate_tokens(RECAP_TITLE) + sum(
        estimate_tokens(render_item_line(item)) for item in items
    )
    return ContextBundle(
        items=items,
        token_cost=token_cost,
        truncated=False,
        workspace_id=workspace_id,
    )
```

- [ ] **2.4 (GREEN run)**
```bash
mise exec -- python -m pytest tests/unit/test_recap.py -q
```
Expected output: `15 passed`.

- [ ] **2.5 (Commit)**
```bash
git add src/dopemux/memory/recap.py tests/unit/test_recap.py
git commit -m "feat(memory): TP-MCF-004 read-only chronicle recap builder (top-k, window, authority labels, fail-open)"
```

---

## Task 3 — Token-budget truncation (invariant 6)

**Files**: `tests/unit/test_recap.py` (append), `src/dopemux/memory/recap.py` (edit `build_recap_bundle` tail)
**Behavior contract**: `bundle.token_cost <= token_budget` always. Cost = title line + one rendered line per item, using `estimate_tokens`. Enforcement drops **whole items**: keep the most-recent-first prefix, `break` at the first item that would overflow, set `truncated=True`. If nothing fits, return `None`.

### Steps

- [ ] **3.1 (RED)** Append to `tests/unit/test_recap.py`:

```python
class TestTokenBudget:
    """Invariant 6 (interfaces §4): every bundle respects the budget."""

    def test_budget_drops_whole_items_and_sets_truncated(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        _insert_work_log_entry(ledger, summary="short recent entry", hours_ago=1.0)
        _insert_work_log_entry(ledger, summary="y" * 4000, hours_ago=2.0)
        bundle = recap.build_recap_bundle(WORKSPACE, ledger, token_budget=60)
        assert bundle is not None
        assert bundle.truncated is True
        assert bundle.token_cost <= 60
        assert len(bundle.items) == 1  # prefix kept: newest item only
        assert "short recent entry" in bundle.items[0].content

    def test_nothing_fits_returns_none(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        _insert_work_log_entry(ledger, summary="z" * 4000, hours_ago=1.0)
        assert recap.build_recap_bundle(WORKSPACE, ledger, token_budget=50) is None

    def test_default_budget_700_enforced(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        for idx in range(3):
            _insert_work_log_entry(
                ledger, summary=f"e{idx} " + "w" * 900, hours_ago=1.0 + idx
            )
        bundle = recap.build_recap_bundle(WORKSPACE, ledger)
        assert bundle is not None
        assert bundle.token_cost <= 700
        assert bundle.truncated is True
        assert len(bundle.items) == 2  # ~243 tokens/line: 2 fit, 3rd overflows
```

- [ ] **3.2 (RED run)**
```bash
mise exec -- python -m pytest tests/unit/test_recap.py -q
```
Expected output: `3 failed, 15 passed` (the three `TestTokenBudget` tests fail: `truncated` is still always `False` / `token_cost` exceeds budget).

- [ ] **3.3 (GREEN)** In `src/dopemux/memory/recap.py`, replace the tail of `build_recap_bundle` — exactly this block:

```python
    dated.sort(key=lambda pair: pair[0], reverse=True)
    items = [item for _, item in dated]
    if not items:
        return None

    token_cost = estimate_tokens(RECAP_TITLE) + sum(
        estimate_tokens(render_item_line(item)) for item in items
    )
    return ContextBundle(
        items=items,
        token_cost=token_cost,
        truncated=False,
        workspace_id=workspace_id,
    )
```

with this block:

```python
    dated.sort(key=lambda pair: pair[0], reverse=True)
    items = [item for _, item in dated]
    if not items:
        return None

    # Invariant 6: enforce the budget by dropping WHOLE items. Keep the
    # most-recent-first prefix; the first overflowing item ends the bundle
    # (older items are strictly lower priority than newer ones).
    kept: list[ContextItem] = []
    truncated = False
    total = estimate_tokens(RECAP_TITLE)
    for item in items:
        cost = estimate_tokens(render_item_line(item))
        if total + cost > token_budget:
            truncated = True
            break
        total += cost
        kept.append(item)

    if not kept:
        return None

    return ContextBundle(
        items=kept,
        token_cost=total,
        truncated=truncated,
        workspace_id=workspace_id,
    )
```

- [ ] **3.4 (GREEN run)**
```bash
mise exec -- python -m pytest tests/unit/test_recap.py -q
```
Expected output: `18 passed`.

- [ ] **3.5 (Commit)**
```bash
git add src/dopemux/memory/recap.py tests/unit/test_recap.py
git commit -m "feat(memory): TP-MCF-004 token-budget truncation for recap bundles"
```

---

## Task 4 — Renderer: `render_recap`

**Files**: `tests/unit/test_recap.py` (append), `src/dopemux/memory/recap.py` (append)
**Interface produced**: `recap.render_recap(bundle: ContextBundle) -> str` — compact markdown block, title line exactly `## Memory recap (last 24h)`, then one line per item in bundle order (already most-recent-first): `- [authority_label] content (freshness)`. Deterministic: same bundle → same string.

### Steps

- [ ] **4.1 (RED)** Append to `tests/unit/test_recap.py`:

```python
class TestRenderRecap:
    def test_title_and_line_format(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        _insert_work_log_entry(ledger, summary="ship recap", hours_ago=1.0)
        bundle = recap.build_recap_bundle(WORKSPACE, ledger)
        assert bundle is not None
        text = recap.render_recap(bundle)
        lines = text.splitlines()
        assert lines[0] == "## Memory recap (last 24h)"
        assert lines[1].startswith("- [canonical] decision: ship recap [success] (")
        assert lines[1].endswith(")")
        assert len(lines) == 1 + len(bundle.items)

    def test_render_is_deterministic(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        _insert_work_log_entry(ledger, summary="alpha-entry", hours_ago=1.0)
        _insert_work_log_entry(ledger, summary="bravo-entry", hours_ago=2.0)
        bundle = recap.build_recap_bundle(WORKSPACE, ledger)
        assert bundle is not None
        assert recap.render_recap(bundle) == recap.render_recap(bundle)

    def test_render_most_recent_first(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        _insert_work_log_entry(ledger, summary="alpha-entry", hours_ago=3.0)
        _insert_work_log_entry(ledger, summary="bravo-entry", hours_ago=2.0)
        _insert_work_log_entry(ledger, summary="charlie-entry", hours_ago=1.0)
        bundle = recap.build_recap_bundle(WORKSPACE, ledger)
        assert bundle is not None
        text = recap.render_recap(bundle)
        assert (
            text.index("charlie-entry")
            < text.index("bravo-entry")
            < text.index("alpha-entry")
        )
```

- [ ] **4.2 (RED run)**
```bash
mise exec -- python -m pytest tests/unit/test_recap.py -q
```
Expected output: `3 failed, 18 passed` (`AttributeError: ... has no attribute 'render_recap'`).

- [ ] **4.3 (GREEN)** Append to `src/dopemux/memory/recap.py` (end of file):

```python
def render_recap(bundle: ContextBundle) -> str:
    """Compact markdown recap block.

    Deterministic: the bundle's items are already ordered most-recent-first
    by ``build_recap_bundle``; this function adds no reordering, no clock
    reads, no randomness.
    """
    lines = [RECAP_TITLE]
    lines.extend(render_item_line(item) for item in bundle.items)
    return "\n".join(lines)
```

- [ ] **4.4 (GREEN run)**
```bash
mise exec -- python -m pytest tests/unit/test_recap.py -q
```
Expected output: `21 passed`.

- [ ] **4.5 (Commit)**
```bash
git add src/dopemux/memory/recap.py tests/unit/test_recap.py
git commit -m "feat(memory): TP-MCF-004 deterministic markdown recap renderer"
```

---

## Task 5 — Read-only invariant locks (structural, not aspirational)

**Files**: `tests/unit/test_recap.py` (append). **No implementation change expected** — Task 2 already made `mode=ro` the implementation choice; these tests lock it so a future edit that "helpfully" opens the ledger read-write fails CI.

These are invariant-lock tests over an already-made structural decision, so they are expected to pass on first run (no RED phase is achievable; that is acceptable here and must be stated in the commit message).

### Steps

- [ ] **5.1** Append to `tests/unit/test_recap.py`:

```python
class TestReadOnlyInvariant:
    """recap.py must be structurally incapable of chronicle writes."""

    def test_connection_rejects_writes(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        conn = recap._connect_ro(ledger)
        try:
            with pytest.raises(sqlite3.OperationalError):
                conn.execute(
                    "INSERT INTO raw_activity_events "
                    "(id, workspace_id, instance_id, ts_utc, event_type, "
                    " source, payload_json, created_at_utc) "
                    "VALUES ('x', 'w', 'A', 't', 'e', 's', '{}', 't')"
                )
            with pytest.raises(sqlite3.OperationalError):
                conn.execute("UPDATE work_log_entries SET summary = 'clobbered'")
            with pytest.raises(sqlite3.OperationalError):
                conn.execute("DELETE FROM work_log_entries")
        finally:
            conn.close()

    def test_build_recap_leaves_ledger_bytes_untouched(self, tmp_path):
        ledger = _make_ledger(tmp_path)
        _insert_work_log_entry(ledger, summary="untouched-row", hours_ago=1.0)
        before = hashlib.sha256(ledger.read_bytes()).hexdigest()
        bundle = recap.build_recap_bundle(WORKSPACE, ledger)
        assert bundle is not None
        after = hashlib.sha256(ledger.read_bytes()).hexdigest()
        assert before == after

    def test_recap_source_contains_no_write_sql(self):
        source = Path(recap.__file__).read_text(encoding="utf-8").upper()
        for verb in (
            "INSERT INTO",
            "DELETE FROM",
            "CREATE TABLE",
            "DROP TABLE",
            "ALTER TABLE",
        ):
            assert verb not in source, f"write SQL verb found in recap.py: {verb}"
```

- [ ] **5.2 (Run — expected green immediately)**
```bash
mise exec -- python -m pytest tests/unit/test_recap.py -q
```
Expected output: `24 passed`. If `test_connection_rejects_writes` fails, the implementation is NOT read-only — stop and fix `_connect_ro` before anything else; do not weaken the test.

- [ ] **5.3 (Commit)**
```bash
git add tests/unit/test_recap.py
git commit -m "test(memory): TP-MCF-004 structural read-only invariant locks (no RED phase: locks an existing mode=ro choice)"
```

---

## Task 6 — Hook wiring: SessionStart appends the recap as a fourth part

**Files**: `tests/test_native_hooks_workflow.py` (append), `src/dopemux/claude/native_hooks.py` (two edits)
**Interfaces produced**:
- `native_hooks._recap_injection_enabled() -> bool` — env kill switch `DOPEMUX_RECAP_INJECTION` (default on; `off`/`0`/`false`/`no` disable).
- `native_hooks._emit_recap_context(project_root: Path) -> Optional[str]` — fail-open wrapper; **lazy-imports** `dopemux.memory.recap` inside the function body so even an `ImportError` in the new module can never break hook startup (mirrors the module's top-level try/except import fallbacks at `native_hooks.py:30-74`).
- `_on_session_start` composition gains `recap_ctx` as the **last** element of the existing `"\n\n".join(filter(None, [...]))` calls at `native_hooks.py:341` and `:346`.

### Steps

- [ ] **6.1 (RED)** Append to the END of `tests/test_native_hooks_workflow.py` (the block is deliberately self-contained — it carries its own imports so the patch is append-only and cannot conflict with the existing import lines):

```python
# --- TP-MCF-004: SessionStart recap wiring -----------------------------------
# Hermetic: tmp ledger built from the canonical chronicle schema; no Redis,
# no dope-memory service (which may be down -- the recap is a local read).

import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

_RECAP_REPO_ROOT = Path(__file__).resolve().parents[1]
_RECAP_SCHEMA = (
    _RECAP_REPO_ROOT
    / "services"
    / "working-memory-assistant"
    / "chronicle"
    / "schema.sql"
)


def _recap_ledger_with_entry(tmp_path, workspace_id: str) -> Path:
    ledger = tmp_path / "chronicle.sqlite"
    conn = sqlite3.connect(str(ledger))
    try:
        conn.executescript(_RECAP_SCHEMA.read_text(encoding="utf-8"))
        ts = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        now = datetime.now(timezone.utc).isoformat()
        entry_id = uuid.uuid4().hex
        conn.execute(
            """
            INSERT INTO work_log_entries (
                id, workspace_id, instance_id, session_id, ts_utc,
                category, entry_type, summary, outcome, importance_score,
                tags_json,
                source_event_id, source_event_type, source_adapter,
                source_event_ts_utc, promotion_rule, promotion_ts_utc,
                created_at_utc, updated_at_utc
            ) VALUES (?, ?, 'A', NULL, ?, 'implementation', 'decision',
                      'recap smoke entry', 'success', 5, '[]',
                      ?, 'decision.logged', 'test', ?,
                      'eventbus_promotion_v1', ?, ?, ?)
            """,
            (entry_id, workspace_id, ts, f"evt-{entry_id}", ts, now, now, now),
        )
        conn.commit()
    finally:
        conn.close()
    return ledger


def _session_start_context(response) -> str:
    return (response.get("hookSpecificOutput") or {}).get("additionalContext", "") or ""


def test_session_start_appends_recap_from_local_ledger(tmp_path, monkeypatch):
    workspace_id = str(Path(tmp_path).resolve())
    ledger = _recap_ledger_with_entry(tmp_path, workspace_id)
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger))
    monkeypatch.delenv("DOPEMUX_RECAP_INJECTION", raising=False)

    response = handle_event(
        "SessionStart",
        {"cwd": str(tmp_path), "env": {"DOPEMUX_INSTANCE_ID": "main"}},
    )

    context = _session_start_context(response)
    assert "## Memory recap (last 24h)" in context
    assert "recap smoke entry" in context
    assert "[canonical]" in context


def test_session_start_recap_appended_after_workflow_context(tmp_path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(tmp_path))
    workspace_id = str(Path(tmp_path).resolve())
    ledger = _recap_ledger_with_entry(tmp_path, workspace_id)
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger))
    monkeypatch.delenv("DOPEMUX_RECAP_INJECTION", raising=False)

    kernel = WorkflowKernel(tmp_path)
    kernel.create_or_resume(
        workflow_id="wf-recap",
        instance_id="main",
        mode="internal",
        max_iterations=5,
        max_minutes=30,
        completion_token="DONE",
    )

    response = handle_event(
        "SessionStart",
        {"cwd": str(tmp_path), "env": {"DOPEMUX_INSTANCE_ID": "main"}},
    )
    context = _session_start_context(response)
    assert "Dopemux workflow wf-recap is active." in context
    assert "## Memory recap (last 24h)" in context
    # Recap is the FOURTH part: it comes after the workflow context.
    assert context.index("Dopemux workflow wf-recap is active.") < context.index(
        "## Memory recap (last 24h)"
    )


def test_session_start_recap_kill_switch(tmp_path, monkeypatch):
    workspace_id = str(Path(tmp_path).resolve())
    ledger = _recap_ledger_with_entry(tmp_path, workspace_id)
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger))
    monkeypatch.setenv("DOPEMUX_RECAP_INJECTION", "off")

    response = handle_event(
        "SessionStart",
        {"cwd": str(tmp_path), "env": {"DOPEMUX_INSTANCE_ID": "main"}},
    )
    assert "## Memory recap (last 24h)" not in _session_start_context(response)


def test_session_start_survives_corrupt_ledger(tmp_path, monkeypatch):
    garbage = tmp_path / "chronicle.sqlite"
    garbage.write_bytes(b"\x00not sqlite\xff" * 128)
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(garbage))
    monkeypatch.delenv("DOPEMUX_RECAP_INJECTION", raising=False)

    response = handle_event(
        "SessionStart",
        {"cwd": str(tmp_path), "env": {"DOPEMUX_INSTANCE_ID": "main"}},
    )
    # Fail-open: no exception, no recap section, hook not blocked.
    assert "## Memory recap (last 24h)" not in _session_start_context(response)
    assert response.get("decision") != "block"


def test_session_start_without_ledger_injects_no_recap(tmp_path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(tmp_path / "absent.sqlite"))
    monkeypatch.delenv("DOPEMUX_RECAP_INJECTION", raising=False)

    response = handle_event(
        "SessionStart",
        {"cwd": str(tmp_path), "env": {"DOPEMUX_INSTANCE_ID": "main"}},
    )
    assert "## Memory recap (last 24h)" not in _session_start_context(response)
```

- [ ] **6.2 (RED run)**
```bash
mise exec -- python -m pytest tests/test_native_hooks_workflow.py -q
```
Expected output: `2 failed, 10 passed`. Only the two **positive** tests fail (`test_session_start_appends_recap_from_local_ledger`, `test_session_start_recap_appended_after_workflow_context`); the three **absence** tests (kill switch / corrupt / no ledger) pass trivially before wiring exists — they become meaningful regression guards after 6.3.

- [ ] **6.3 (GREEN, edit 1 of 2)** In `src/dopemux/claude/native_hooks.py`, insert the two helpers immediately before `def _response_text(...)` (currently line 197). Replace this exact text:

```python
def _response_text(payload: Dict[str, Any]) -> str:
```

with:

```python
RECAP_KILL_SWITCH_ENV = "DOPEMUX_RECAP_INJECTION"
_RECAP_DISABLED_VALUES = {"off", "0", "false", "no"}


def _recap_injection_enabled() -> bool:
    """Env kill switch for SessionStart recap injection (default: on)."""
    configured = os.environ.get(RECAP_KILL_SWITCH_ENV, "on").strip().lower()
    return configured not in _RECAP_DISABLED_VALUES


def _emit_recap_context(project_root: Path) -> Optional[str]:
    """Bounded chronicle recap for SessionStart injection (TP-MCF-004).

    Fail-open by construction, mirroring this module's try/except import
    fallbacks (native_hooks.py:30-74) and the best-effort style of
    ``_emit_bounded_hook_error_capture``: ANY failure -- missing/corrupt
    ledger, import error, schema drift -- returns ``None`` and never breaks
    session start. Local SQLite read only (``mode=ro``): no network, no
    ConPort, no dope-context, no dope-memory HTTP (the service may be down).
    The import is lazy so a broken recap module cannot break hook startup.
    """
    if not _recap_injection_enabled():
        return None
    try:
        from dopemux.memory.recap import (
            build_recap_bundle,
            render_recap,
            resolve_ledger_path,
        )

        ledger_path = resolve_ledger_path(project_root)
        bundle = build_recap_bundle(str(project_root), ledger_path)
        if bundle is None:
            return None
        return render_recap(bundle)
    except Exception:
        return None


def _response_text(payload: Dict[str, Any]) -> str:
```

- [ ] **6.4 (GREEN, edit 2 of 2)** In `src/dopemux/claude/native_hooks.py`, replace the whole `_on_session_start` method (lines 335-351 pre-edit; the exact current text is quoted in §0 fact 1). Replace:

```python
    def _on_session_start(self) -> Tuple[int, Dict[str, Any]]:
        reset_edit_counter(self.project_root, self.session_id)
        mcp_health = emit_mcp_health(self.project_root)
        orch_ctx = emit_session_context(self.project_root)
        state = self._active_state()
        if not state:
            combined = "\n\n".join(filter(None, [mcp_health, orch_ctx]))
            if combined:
                return self._allow(additional_context=combined, hook_event_name="SessionStart")
            return self._allow()
        workflow_ctx = _workflow_context_lines(state, include_gates=True)
        combined = "\n\n".join(filter(None, [mcp_health, orch_ctx, workflow_ctx]))
        return self._allow(
            system_message=f"Dopemux workflow mode: {state.mode}",
            additional_context=combined or None,
            hook_event_name="SessionStart",
        )
```

with:

```python
    def _on_session_start(self) -> Tuple[int, Dict[str, Any]]:
        reset_edit_counter(self.project_root, self.session_id)
        mcp_health = emit_mcp_health(self.project_root)
        orch_ctx = emit_session_context(self.project_root)
        recap_ctx = _emit_recap_context(self.project_root)
        state = self._active_state()
        if not state:
            combined = "\n\n".join(filter(None, [mcp_health, orch_ctx, recap_ctx]))
            if combined:
                return self._allow(additional_context=combined, hook_event_name="SessionStart")
            return self._allow()
        workflow_ctx = _workflow_context_lines(state, include_gates=True)
        combined = "\n\n".join(filter(None, [mcp_health, orch_ctx, workflow_ctx, recap_ctx]))
        return self._allow(
            system_message=f"Dopemux workflow mode: {state.mode}",
            additional_context=combined or None,
            hook_event_name="SessionStart",
        )
```

Nothing else in `native_hooks.py` changes. The recap is the last (fourth) element of the same `filter(None, [...])` composition, so a `None` recap leaves the pre-existing output byte-identical.

- [ ] **6.5 (GREEN run)**
```bash
mise exec -- python -m pytest tests/test_native_hooks_workflow.py -q
```
Expected output: `12 passed` (7 pre-existing + 5 new).

- [ ] **6.6 (Commit)**
```bash
git add src/dopemux/claude/native_hooks.py tests/test_native_hooks_workflow.py
git commit -m "feat(hooks): TP-MCF-004 SessionStart recap injection (fourth context part, DOPEMUX_RECAP_INJECTION kill switch)"
```

---

## Task 7 — Final verification: targeted suite + proof gate (no code changes)

- [ ] **7.1 Full targeted suite**
```bash
mise exec -- python -m pytest tests/unit/test_recap.py tests/test_native_hooks_workflow.py -q
```
Expected output: `36 passed` (24 recap unit + 12 native-hooks). Any other count = investigate before reporting done.

- [ ] **7.2 Adjacent regression check** (recap imports `capture_client`; prove the spine is unharmed)
```bash
mise exec -- python -m pytest tests/unit/test_memory_capture_client.py -q
```
Expected output: all tests pass (same count as a pre-change run of this file; if it was failing before your change, report it as pre-existing, do not fix it here).

- [ ] **7.3 Diff-scope check**
```bash
git status --short
git diff --stat main...HEAD -- src tests
```
Expected: exactly four files changed across the series — `src/dopemux/memory/recap.py`, `tests/unit/test_recap.py`, `src/dopemux/claude/native_hooks.py`, `tests/test_native_hooks_workflow.py`. Anything else in the diff = out of scope, revert it.

- [ ] **7.4 Proof-gate checklist** (map each gate to its test; all must be checked)

| Gate | Test(s) | Invariant |
|---|---|---|
| Token budget | `TestTokenBudget::*` (3 tests) | interfaces §4 inv. 6: `token_cost <= budget`, whole-item truncation, `truncated` flag |
| Authority labels | `test_curated_rows_labeled_canonical_high_trust`, `test_candidate_rows_labeled_conversation_inferred` | interfaces §4 inv. 5: provenance only lowers trust; `conversation_candidate_v1` → conversation-inferred/conversation-derived |
| Fail-open | `test_missing_ledger_returns_none`, `test_empty_ledger_returns_none`, `test_corrupt_ledger_returns_none`, `test_malformed_timestamp_rows_are_skipped_not_fatal`, `test_session_start_survives_corrupt_ledger`, `test_session_start_without_ledger_injects_no_recap` | interfaces §4 inv. 7: degrade gracefully, never break session start |
| Read-only | `TestReadOnlyInvariant::*` (3 tests) | structural `mode=ro`; ledger bytes untouched; no write SQL in source |
| Kill switch | `test_session_start_recap_kill_switch` | `DOPEMUX_RECAP_INJECTION=off` disables; default on |
| Top-3 + ordering | `test_top_k_selection_and_ordering_most_recent_first`, `test_render_most_recent_first` | design spec §6 TP-MCF-004: Top-3 default, deterministic most-recent-first |
| No semantic fusion / no network | code review of `recap.py` imports (`sqlite3`, `dataclasses`, `datetime`, `pathlib`, `typing`, `capture_client` only — no `redis`, no `httpx`/`requests`, no conport/dope-context clients) | design spec §6 TP-MCF-004 hard gate |

- [ ] **7.5 Report** with the repo's required final structure (Change Summary · Authority Used · Analysis Performed · Validation PASS/FAIL/NOT_RUN · Remaining Uncertainty · Files Touched · Git State · Rollback Plan · Requested Next Step). Rollback for the whole series: `git revert` the task commits in reverse order, or reset the branch to the pre-series SHA recorded in pre-flight.

---

## Appendix A — Known residual risks (document in the final report, do not "fix" silently)

1. **WAL read-only edge**: the production ledger runs `PRAGMA journal_mode = WAL` (`capture_client.py:527`). Read-only opens of a WAL database can fail in rare states (e.g. `-shm` absent and not creatable). `global_rollup.py:194-198` already ships this exact `mode=ro` pattern against the same ledger, and any such failure is caught by the fail-open `except sqlite3.Error` → `None`. Accepted: a recap silently absent in that edge, never a broken session.
2. **Lexicographic SQL pre-limit**: `ORDER BY ts_utc DESC LIMIT 50` orders ISO strings lexicographically. Mixed `Z` vs `+00:00` spellings order correctly at second granularity except for identical instants; correctness of the final ordering is guaranteed by the Python-side parse+sort, and the 50-row pre-limit is a bounded-work tradeoff (a workspace with >50 chronicle rows inside 24h could theoretically have a fresh row outside the scan window — acceptable for a recap).
3. **`session.ended` rows may not exist** in `raw_activity_events` today (the consumer at `eventbus_consumer.py:384` reads a Redis stream the hooks don't feed — authority map §3 gap 1). The boundary line is best-effort by design; its absence is not a defect.
4. **Fixed title** `## Memory recap (last 24h)` does not vary with `hours_back` — the title is the TP-MCF-004 contract string; `hours_back` is an internal parameter defaulted to 24 and not overridden by the hook.

## Appendix B — Self-review (performed at plan time)

- **Invariant coverage**: all 5 hard invariants from the packet spec are test-gated (see 7.4); interfaces §4 invariants 5/6/7 each map to at least one named test.
- **Placeholder scan**: no TODO/TBD/`...`-elision in any code block; every code block is complete and paste-ready; all SQL placeholder counts verified against their parameter tuples (13/13 and 8/8 for `work_log_entries` inserts, 4/4 for `raw_activity_events`).
- **Signature consistency**: `build_recap_bundle(workspace_id: str, ledger_path: Path, *, hours_back: int = 24, k: int = 3, token_budget: int = 700) -> ContextBundle | None` matches the packet text; `ContextItem`/`ContextBundle` field names and order match interfaces §2.4 exactly (`content, source_system, authority_label, trust, freshness, provenance` / `items, token_cost, truncated, workspace_id`); trust vocabulary is exactly `"high" | "conversation-derived"`, authority labels drawn from `"canonical" | "mirror" | "derived" | "conversation-inferred"` (recap emits only `canonical` and `conversation-inferred`).
- **Groundedness**: every cited line number was read in this worktree on 2026-07-04 baseline (`native_hooks.py:335-351`, `capture_client.py:255-259` and `:527`, `schema.sql:5-20`/`:29-81`, `freeflow.py:202-210`/`:220-221`, `broker.py:943`, `canonical_readview.py:21-36`, `global_rollup.py:194-198`, `eventbus_consumer.py:384`); baseline `tests/test_native_hooks_workflow.py` = 7 passed was verified by an actual run.



