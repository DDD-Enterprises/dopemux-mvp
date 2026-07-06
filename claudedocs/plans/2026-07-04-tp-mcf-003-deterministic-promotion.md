# TP-MCF-003 — Deterministic Promotion: `conversation.decision_candidate`

> **For agentic workers:** Execute this plan task-by-task via superpowers:subagent-driven-development or superpowers:executing-plans if available; otherwise execute the checkbox (`- [ ]`) steps literally, in order, committing exactly where the plan says. Read the master plan first: `claudedocs/plans/2026-07-04-memory-context-fabric-build-plan.md` (global constraints + hand-off protocol).
**For the executing agent:** you have zero context beyond this file. Every file path is absolute-from-repo-root. Every code block is complete — copy it verbatim, do not paraphrase or "improve" it. Follow the TDD checkboxes in order: write the failing test, run it, confirm it fails for the stated reason, then apply the implementation, run it again, confirm it passes, then commit. Do not skip the "confirm it fails" sub-step — it is what proves the test is real.

**Packet**: TP-MCF-003 (Memory Context Fabric, phase 003)
**Depends on (spec, not code)**: TP-MCF-002 defines the transcript-ingest adapter that will eventually call the code this packet builds. TP-MCF-003 does **not** require TP-MCF-002 to exist — every test in this plan constructs turn-content strings and event envelopes directly, with no transcript files or ingest adapter involved.
**Authority docs** (read in this order before touching code):
1. `claudedocs/memory-context-fabric-design-2026-07-04.md` (v3) — §2 "Decision detection", §6 row `TP-MCF-003`.
2. `claudedocs/tp-mcf-001-authority-map-2026-07-04.md` — §1 Domain B (promotion authority), §3 gaps 3 and 4, §4 "TP-MCF-003" (this packet's originating spec).
3. `claudedocs/memory-context-fabric-interfaces-2026-07-04.md` — §2.2 event-type taxonomy, §2.3 `PromotedEntry` trust encoding.

Runtime code outranks these docs if they ever disagree — but they don't; every code claim below was verified against the actual runtime files, listed next.

---

## 0. Goal

Add exactly one new event type, `conversation.decision_candidate`, end-to-end through the existing capture→promotion pipeline, so that a deterministic (non-LLM) decision-marker detector can emit transcript-derived "this looks like a decision" candidates into the curated chronicle — **without ever writing to ConPort** and **without ever emitting `decision.logged`** (which the codebase reserves for post-write receipts from a real ConPort decision).

## 1. Architecture (what you are building, in one paragraph)

Three new pieces, all additive (no existing behavior changes except one one-line dispatch fix described in Task 2):

1. A pure-function deterministic detector, `detect_decision_candidate(turn_content: str) -> DecisionCandidate | None`, in a **new file** `src/dopemux/memory/conversation_promotion.py`. No LLM, no network, no imports of ConPort/httpx — regex-based marker matching only.
2. The new event type added to **both** existing allowlists (`src/dopemux/memory/capture_client.py` and `services/working-memory-assistant/promotion/promotion.py`), which today are independently-maintained frozensets that must contain the same 7 (soon 8) strings.
3. A new promotion handler `_promote_conversation_decision_candidate` in `services/working-memory-assistant/promotion/promotion.py`, mirroring the construction style of the existing `_promote_decision_logged` and `_promote_task_completed` handlers, producing a `PromotedEntry` whose `promotion_rule="conversation_candidate_v1"` and `details_json.trust="conversation-derived"`.

## 2. Stack / tooling

- **Interpreter**: `mise exec -- python` (3.12) — never the bare `python3` on PATH.
- **Root test suite** (covers `src/dopemux/...`): run from repo root, e.g. `mise exec -- python -m pytest tests/unit/<file> -q`. Root `pyproject.toml` sets `pythonpath = ["src"]` and `testpaths = ["tests"]`, so `from dopemux.memory... import ...` resolves without extra setup.
- **WMA test suite** (covers `services/working-memory-assistant/...`): run with cwd = `services/working-memory-assistant/`, e.g. `cd services/working-memory-assistant && mise exec -- python -m pytest tests/<file> -q`. WMA's own `tests/conftest.py` inserts the service directory onto `sys.path`, which is what makes `from promotion.promotion import ...` and `from chronicle.store import ...` resolve as top-level packages. **Do not** try to run WMA tests from repo root — the root `pytest.ini`'s `norecursedirs` explicitly excludes `services/`, and the root `pyproject.toml`'s `pythonpath=["src"]` does not add the WMA directory.
- No Docker, no Redis, no network calls anywhere in this packet's tests — everything is pure-function or SQLite-via-`tmp_path`.

## 3. Global constraints (apply to every task below)

- **No LLM summarization.** All detection is regex/string-heuristic. No API calls to any model provider anywhere in this packet.
- **No auto ConPort writes.** Nothing in this packet imports `httpx`, `requests`, `aiohttp`, or any ConPort client. A test enforces this (Task 4).
- **Never `decision.logged`.** The candidate event type is `conversation.decision_candidate`, always. A test enforces this (Task 5).
- **Non-goals (explicitly out of scope for this packet — do not touch):**
  - Promotion of `task.completed`, `task.failed`, `task.blocked`, `error.encountered`, `workflow.phase_changed` already exists and works; this packet does not modify those handlers' behavior (only the shared dispatch line in Task 2, which is provably backward-compatible — see Task 2's regression test).
  - Promotion of a candidate **to** a canonical ConPort decision (the "explicit gate" mentioned in the design doc) is a future packet's job, not this one's.
  - The transcript-file watcher/ingest adapter (TP-MCF-002) is a separate packet. This packet's tests never read a transcript file.
- **File-scope discipline**: only touch the files named in each task's "Files" line. Do not bump versions, do not touch CI config, do not touch `.claude/` settings.

---

## Task 1 — Deterministic decision-candidate detector (pure function, new module)

### Files
- **New**: `src/dopemux/memory/conversation_promotion.py`
- **New**: `tests/unit/test_conversation_promotion_detector.py`

### Interface contract (pin this before writing any code — both the detector and the promotion handler in Task 3 depend on these exact dict/attribute names)

```
detect_decision_candidate(turn_content: str) -> DecisionCandidate | None

DecisionCandidate:
    title: str        # first 120 chars of the extracted decision text
    rationale: str     # remainder, capped at 500 chars (may be empty string)
```

When this candidate is later emitted as a capture event (Task 5), the payload dict uses exactly the keys `{"title": ..., "rationale": ...}` — the promotion handler in Task 3 reads exactly those two keys. This is the cross-file contract; do not rename either key on either side.

### Deterministic rules (exact — do not invent alternatives)

A turn is a decision candidate if and only if it contains one of these leading markers, matched **case-insensitively** and **anchored to the start of the turn content** (after stripping leading whitespace) or immediately after a leading discourse filler is not permitted — anchor strictly to the start of the (stripped) string:

```python
_DECISION_MARKER_PATTERNS = [
    r"^decision:\s*",
    r"^we\s+decided\s+(?:to\s+|that\s+)?",
    r"^let'?s\s+go\s+with\s+",
    r"^approved:\s*",
    r"^decided:\s*",
    r"^final\s+decision:\s*",
]
```

Additional hard rules:
- **Min length**: the remaining text after stripping the matched marker must be at least 8 characters (rejects marker-only noise like `"decision:"` with nothing after it).
- **Max length**: turn_content longer than 4000 characters is rejected outright (return `None`) — a decision marker inside a 4000-char turn is not a deterministic signal, it's noise; this bound also protects the regex from pathological input.
- **Negative cases (must NOT match)** — questions and hypotheticals are explicitly excluded even if they contain a marker word:
  - Any stripped turn_content ending in `?` is rejected outright, regardless of marker match (rejects `"Should we decide to use Redis?"`, `"Did we decide on Postgres?"`).
  - `"should we decide"` / `"should we go with"` phrasing anywhere in the first 40 characters is rejected even without a trailing `?` (rejects hedged hypotheticals stated as declaratives, e.g. `"Should we decide to use Redis at some point"`).
- Matching is tried against the patterns **in the order listed above**; the first match wins. Extraction: strip the matched marker prefix, then:
  - `title` = the resulting text, truncated to 120 characters (no ellipsis, hard slice).
  - `rationale` = the resulting text with the first 120 characters removed (i.e., whatever's left after the `title` slice), truncated to 500 characters (hard slice). If nothing remains, `rationale = ""`.

### TDD steps

- [ ] **1.1 — Write the failing test file.** Create `tests/unit/test_conversation_promotion_detector.py`:

```python
"""Deterministic decision-candidate detection (TP-MCF-003). No LLM, no I/O."""

from dopemux.memory.conversation_promotion import (
    DecisionCandidate,
    detect_decision_candidate,
)


def test_decision_colon_marker_matches():
    result = detect_decision_candidate("decision: use Redis Streams for the event bus")
    assert result is not None
    assert isinstance(result, DecisionCandidate)
    assert result.title == "use Redis Streams for the event bus"
    assert result.rationale == ""


def test_we_decided_marker_matches():
    result = detect_decision_candidate(
        "we decided to use SQLite for the chronicle ledger because it is local-first"
    )
    assert result is not None
    assert result.title.startswith("use SQLite for the chronicle ledger")


def test_lets_go_with_marker_matches():
    result = detect_decision_candidate("let's go with option B for the retry policy")
    assert result is not None
    assert result.title == "option B for the retry policy"


def test_approved_marker_matches():
    result = detect_decision_candidate("approved: migrate to the new schema")
    assert result is not None
    assert result.title == "migrate to the new schema"


def test_case_insensitive_matching():
    result = detect_decision_candidate("DECISION: Use Postgres for the mirror")
    assert result is not None
    assert result.title == "Use Postgres for the mirror"


def test_marker_must_be_anchored_to_start():
    # The marker phrase appears mid-sentence, not at the start — must NOT match.
    result = detect_decision_candidate(
        "I was thinking about it and then we decided to use Redis"
    )
    assert result is None


def test_question_form_never_matches_even_with_marker_word():
    result = detect_decision_candidate("Should we decide to use Redis?")
    assert result is None


def test_hedged_hypothetical_without_question_mark_rejected():
    result = detect_decision_candidate(
        "should we decide to use Redis at some point down the line"
    )
    assert result is None


def test_did_we_decide_question_rejected():
    result = detect_decision_candidate("Did we decide on Postgres?")
    assert result is None


def test_marker_only_no_content_rejected():
    # "decision:" with nothing (or too little) after it is not a real candidate.
    result = detect_decision_candidate("decision:")
    assert result is None
    result = detect_decision_candidate("decision: ok")
    assert result is None  # "ok" is 2 chars, below the 8-char minimum


def test_exactly_min_length_boundary_accepted():
    # 8 chars exactly after the marker should be accepted.
    result = detect_decision_candidate("decision: 12345678")
    assert result is not None
    assert result.title == "12345678"


def test_oversized_turn_rejected():
    huge = "decision: " + ("x" * 4100)
    result = detect_decision_candidate(huge)
    assert result is None


def test_title_capped_at_120_chars_and_rationale_gets_remainder():
    body = "a" * 150 + " tail content that becomes rationale"
    result = detect_decision_candidate(f"decision: {body}")
    assert result is not None
    assert len(result.title) == 120
    assert result.title == body[:120]
    assert result.rationale == body[120:][:500]


def test_rationale_capped_at_500_chars():
    body = "b" * 700
    result = detect_decision_candidate(f"final decision: {body}")
    assert result is not None
    # title takes the first 120 of body, rationale takes the next up-to-500
    assert result.rationale == body[120:620]
    assert len(result.rationale) == 500


def test_non_decision_text_returns_none():
    result = detect_decision_candidate("just chatting about the weather today")
    assert result is None


def test_empty_string_returns_none():
    assert detect_decision_candidate("") is None


def test_whitespace_only_returns_none():
    assert detect_decision_candidate("   \n\t  ") is None


def test_leading_whitespace_is_stripped_before_matching():
    result = detect_decision_candidate("   decision: use the new retry policy")
    assert result is not None
    assert result.title == "use the new retry policy"


def test_decided_colon_marker_matches():
    result = detect_decision_candidate("decided: ship the v2 API")
    assert result is not None
    assert result.title == "ship the v2 API"
```

  Run it and confirm it fails because the module doesn't exist yet:
  ```bash
  mise exec -- python -m pytest tests/unit/test_conversation_promotion_detector.py -q
  ```
  Expected output: `ModuleNotFoundError: No module named 'dopemux.memory.conversation_promotion'` (collection error).

- [ ] **1.2 — Implement the detector.** Create `src/dopemux/memory/conversation_promotion.py`:

```python
"""Deterministic (non-LLM) decision-candidate detection over conversation turns.

TP-MCF-003. This module is a PURE FUNCTION boundary: no I/O, no network, no
ConPort/httpx imports, no LLM calls. It only classifies a turn's text content
using explicit anchored regex markers. See claudedocs/tp-mcf-001-authority-map-2026-07-04.md
§4 and claudedocs/memory-context-fabric-design-2026-07-04.md §2 for the spec
this implements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_MAX_TURN_LENGTH = 4000
_MIN_REMAINDER_LENGTH = 8
_TITLE_MAX_LENGTH = 120
_RATIONALE_MAX_LENGTH = 500

_DECISION_MARKER_PATTERNS = [
    re.compile(r"^decision:\s*", re.IGNORECASE),
    re.compile(r"^we\s+decided\s+(?:to\s+|that\s+)?", re.IGNORECASE),
    re.compile(r"^let'?s\s+go\s+with\s+", re.IGNORECASE),
    re.compile(r"^approved:\s*", re.IGNORECASE),
    re.compile(r"^decided:\s*", re.IGNORECASE),
    re.compile(r"^final\s+decision:\s*", re.IGNORECASE),
]

_HEDGE_PATTERN = re.compile(r"should\s+we\s+decide|should\s+we\s+go\s+with", re.IGNORECASE)
_HEDGE_WINDOW = 40


@dataclass(frozen=True)
class DecisionCandidate:
    """A deterministically-detected decision-looking turn.

    title: first 120 chars of the extracted decision text (after marker strip).
    rationale: remainder of the extracted text, capped at 500 chars.
    """

    title: str
    rationale: str


def detect_decision_candidate(turn_content: str) -> DecisionCandidate | None:
    """Deterministically detect a decision-candidate marker in turn_content.

    Returns None for: empty/whitespace-only input, oversized input (>4000
    chars), questions (trailing '?'), hedged hypotheticals ("should we
    decide..."), unmatched text, or matched-but-too-short remainders (<8
    chars after the marker is stripped).

    No LLM. No network. No I/O. Pure string function.
    """
    if not turn_content:
        return None

    stripped = turn_content.strip()
    if not stripped:
        return None

    if len(stripped) > _MAX_TURN_LENGTH:
        return None

    if stripped.endswith("?"):
        return None

    if _HEDGE_PATTERN.search(stripped[:_HEDGE_WINDOW]):
        return None

    for pattern in _DECISION_MARKER_PATTERNS:
        match = pattern.match(stripped)
        if not match:
            continue

        remainder = stripped[match.end():]
        if len(remainder) < _MIN_REMAINDER_LENGTH:
            return None

        title = remainder[:_TITLE_MAX_LENGTH]
        rationale = remainder[_TITLE_MAX_LENGTH:][:_RATIONALE_MAX_LENGTH]
        return DecisionCandidate(title=title, rationale=rationale)

    return None
```

- [ ] **1.3 — Run the test again and confirm it passes.**
  ```bash
  mise exec -- python -m pytest tests/unit/test_conversation_promotion_detector.py -q
  ```
  Expected output: `19 passed` (all tests green).

- [ ] **1.4 — Commit.**
  ```bash
  git add src/dopemux/memory/conversation_promotion.py tests/unit/test_conversation_promotion_detector.py
  git commit -m "feat(memory): deterministic decision-candidate detector (TP-MCF-003 Task 1)

Pure regex-based marker detection for conversation.decision_candidate.
No LLM, no I/O. Anchored markers only; rejects questions and hedged
hypotheticals. Part of TP-MCF-003 (deterministic promotion)."
  ```

---

## Task 2 — Fix the `promotion_rule` dispatch clobber (prerequisite for Task 3)

**Why this task exists**: `services/working-memory-assistant/promotion/promotion.py`'s `promote()` method unconditionally overwrites `promotion_rule` after calling the per-type handler:

```python
# Current code, promotion.py line ~191:
promoted.promotion_rule = normalized  # Normalized handler name
```

If the new handler in Task 3 sets `promoted.promotion_rule = "conversation_candidate_v1"`, this line silently overwrites it back to `"conversation.decision_candidate"` — which would violate this packet's hard requirement that the promoted entry carry `promotion_rule="conversation_candidate_v1"`. This has been empirically verified against the actual runtime: every one of the 7 existing `_promote_*` handlers leaves `PromotedEntry.promotion_rule` at its dataclass default of `None` (none of them set it), so changing the line to only fill in the normalized type **when the handler didn't already set one** is a no-op for all existing handlers and unblocks the new one.

### Files
- **Modify**: `services/working-memory-assistant/promotion/promotion.py` (one line)
- **New**: `services/working-memory-assistant/tests/unit/test_promotion_rule_precedence.py`

### TDD steps

- [ ] **2.1 — Write the failing regression test.** Create `services/working-memory-assistant/tests/unit/test_promotion_rule_precedence.py`:

```python
"""Regression test: promote() must not clobber a handler-set promotion_rule.

TP-MCF-003 Task 2. Every EXISTING handler leaves PromotedEntry.promotion_rule
at its dataclass default (None), so the dispatch-level fallback in promote()
must only fill in the normalized event type when the handler left it unset —
never override a handler that explicitly set its own promotion_rule.
"""

from promotion.promotion import PromotionEngine


def test_existing_handlers_still_get_normalized_promotion_rule():
    """Backward-compatibility: handlers that don't set promotion_rule still
    get the normalized event type, exactly as before this packet's change."""
    engine = PromotionEngine()

    entry = engine.promote(
        "decision.logged",
        {
            "decision_id": "dec-1",
            "title": "Use Redis Streams",
            "choice": "Redis",
        },
    )

    assert entry is not None
    assert entry.promotion_rule == "decision.logged"


def test_existing_task_completed_handler_still_gets_normalized_promotion_rule():
    engine = PromotionEngine()

    entry = engine.promote(
        "task.completed", {"task_id": "task-1", "title": "Implement EventBus"}
    )

    assert entry is not None
    assert entry.promotion_rule == "task.completed"
```

  Run it and confirm it currently passes (this is a *pre-existing-behavior* regression guard, not a new-behavior test — it must pass BEFORE and AFTER the one-line change, proving the change is backward-compatible):
  ```bash
  cd services/working-memory-assistant && mise exec -- python -m pytest tests/unit/test_promotion_rule_precedence.py -q
  ```
  Expected output: `2 passed` (this confirms current behavior is what we think it is, before we touch the dispatch line).

- [ ] **2.2 — Apply the one-line fix.** In `services/working-memory-assistant/promotion/promotion.py`, find this exact line (inside `PromotionEngine.promote`, immediately after the four `source_*` provenance assignments):

  ```python
          promoted.promotion_rule = normalized  # Normalized handler name
  ```

  Replace it with:

  ```python
          promoted.promotion_rule = promoted.promotion_rule or normalized  # Normalized handler name (unless handler set its own)
  ```

- [ ] **2.3 — Re-run the regression test plus the full existing promotion suite to confirm zero behavior change.**
  ```bash
  cd services/working-memory-assistant && mise exec -- python -m pytest tests/unit/test_promotion_rule_precedence.py tests/test_promotion_allowlist.py tests/unit/test_promotion_provenance.py -q
  ```
  Expected output: `25 passed` (2 new + 21 from `test_promotion_allowlist.py` + 2 from `test_promotion_provenance.py`).

- [ ] **2.4 — Commit.**
  ```bash
  git add services/working-memory-assistant/promotion/promotion.py services/working-memory-assistant/tests/unit/test_promotion_rule_precedence.py
  git commit -m "fix(wma): let promotion handlers set their own promotion_rule (TP-MCF-003 Task 2)

promote() previously clobbered any handler-set promotion_rule with the
normalized event type. All 7 existing handlers leave promotion_rule at
its None default, so this is backward-compatible (regression test
proves it) and unblocks the conversation.decision_candidate handler,
which must carry promotion_rule=\"conversation_candidate_v1\" per
claudedocs/tp-mcf-001-authority-map-2026-07-04.md §4."
  ```

---

## Task 3 — Add `conversation.decision_candidate` to both allowlists + the sync-guard test

**Why the sync-guard test matters**: `PROMOTABLE_CAPTURE_EVENT_TYPES` (in `src/dopemux/memory/capture_client.py`) and `PROMOTABLE_EVENT_TYPES` (in `services/working-memory-assistant/promotion/promotion.py`) are two **independently maintained** `frozenset` literals in two different files, in two different Python import namespaces. Nothing today enforces they stay equal. This task adds a test that imports both (bridging the namespace gap with `monkeypatch.syspath_prepend`, verified to work) and asserts set equality — so any future addition to only one side fails CI immediately.

### Files
- **Modify**: `src/dopemux/memory/capture_client.py` (one line — add to the frozenset)
- **Modify**: `services/working-memory-assistant/promotion/promotion.py` (one line — add to the frozenset; this file was already touched in Task 2, so re-open it)
- **Modify**: `services/working-memory-assistant/tests/test_event_type_normalization.py` (update a pre-existing hardcoded allowlist assertion — see step 3.5)
- **New**: `tests/unit/test_promotable_allowlist_sync.py`

### TDD steps

- [ ] **3.1 — Write the failing sync-guard test.** Create `tests/unit/test_promotable_allowlist_sync.py`:

```python
"""Sync-guard: the two promotable-event-type allowlists must stay identical.

TP-MCF-003. PROMOTABLE_CAPTURE_EVENT_TYPES (src/dopemux/memory/capture_client.py)
and PROMOTABLE_EVENT_TYPES (services/working-memory-assistant/promotion/promotion.py)
are independently maintained frozensets in two separate import namespaces
(root `dopemux.*` via pyproject.toml's pythonpath=["src"], and WMA's
`promotion.*` via services/working-memory-assistant/tests/conftest.py's
sys.path insert). This test bridges both namespaces from the ROOT test
runner using monkeypatch.syspath_prepend (auto-reverts after the test, so
it does not leak generically-named modules like "store"/"main"/"utils"
onto sys.path for the rest of the session) and asserts the two sets are
byte-for-byte equal. Any future new event type added to only one side
must fail this test.
"""

from pathlib import Path

from dopemux.memory.capture_client import PROMOTABLE_CAPTURE_EVENT_TYPES

REPO_ROOT = Path(__file__).resolve().parents[2]
WMA_DIR = REPO_ROOT / "services" / "working-memory-assistant"


def test_both_allowlists_are_identical(monkeypatch):
    monkeypatch.syspath_prepend(str(WMA_DIR))

    from promotion.promotion import PROMOTABLE_EVENT_TYPES

    assert PROMOTABLE_EVENT_TYPES == PROMOTABLE_CAPTURE_EVENT_TYPES


def test_conversation_decision_candidate_is_in_both_allowlists(monkeypatch):
    monkeypatch.syspath_prepend(str(WMA_DIR))

    from promotion.promotion import PROMOTABLE_EVENT_TYPES

    assert "conversation.decision_candidate" in PROMOTABLE_CAPTURE_EVENT_TYPES
    assert "conversation.decision_candidate" in PROMOTABLE_EVENT_TYPES
```

  Run it and confirm it fails (the new type is not in either allowlist yet, so the second test fails; the first test currently passes since the two sets are equal today — that's fine, it's a baseline check):
  ```bash
  mise exec -- python -m pytest tests/unit/test_promotable_allowlist_sync.py -q
  ```
  Expected output: `1 passed, 1 failed` — `test_conversation_decision_candidate_is_in_both_allowlists` fails with `AssertionError: assert 'conversation.decision_candidate' in frozenset({...7 existing types...})`.

- [ ] **3.2 — Add the new type to `PROMOTABLE_CAPTURE_EVENT_TYPES`.** In `src/dopemux/memory/capture_client.py`, find:

  ```python
  PROMOTABLE_CAPTURE_EVENT_TYPES = frozenset(
      {
          "decision.logged",
          "task.completed",
          "task.failed",
          "task.blocked",
          "error.encountered",
          "workflow.phase_changed",
          "manual.memory_store",
      }
  )
  ```

  Replace with:

  ```python
  PROMOTABLE_CAPTURE_EVENT_TYPES = frozenset(
      {
          "decision.logged",
          "task.completed",
          "task.failed",
          "task.blocked",
          "error.encountered",
          "workflow.phase_changed",
          "manual.memory_store",
          "conversation.decision_candidate",
      }
  )
  ```

- [ ] **3.3 — Add the new type to `PROMOTABLE_EVENT_TYPES`.** In `services/working-memory-assistant/promotion/promotion.py`, find:

  ```python
  PROMOTABLE_EVENT_TYPES = frozenset(
      [
          "decision.logged",
          "task.completed",
          "task.failed",
          "task.blocked",
          "error.encountered",
          "workflow.phase_changed",
          "manual.memory_store",
      ]
  )
  ```

  Replace with:

  ```python
  PROMOTABLE_EVENT_TYPES = frozenset(
      [
          "decision.logged",
          "task.completed",
          "task.failed",
          "task.blocked",
          "error.encountered",
          "workflow.phase_changed",
          "manual.memory_store",
          "conversation.decision_candidate",
      ]
  )
  ```

- [ ] **3.4 — Run the sync-guard test again and confirm it passes.**
  ```bash
  mise exec -- python -m pytest tests/unit/test_promotable_allowlist_sync.py -q
  ```
  Expected output: `2 passed`.

- [ ] **3.5 — Update the pre-existing hardcoded-allowlist test.** `services/working-memory-assistant/tests/test_event_type_normalization.py` has a pre-existing test, `TestPromotableEventTypes::test_all_phase1_types_present`, that asserts `PROMOTABLE_EVENT_TYPES` equals an exact 7-element set. Adding the 8th type in steps 3.2-3.3 makes this assertion fail — this is an expected, in-scope consequence of this task (not a pre-existing unrelated failure like the ones catalogued in Task 4.4), so the test must be updated as part of this commit. In `services/working-memory-assistant/tests/test_event_type_normalization.py`, find:

  ```python
    def test_all_phase1_types_present(self):
        """All Phase 1 event types should be in the allowlist."""
        expected = {
            "decision.logged",
            "task.completed",
            "task.failed",
            "task.blocked",
            "error.encountered",
            "workflow.phase_changed",
            "manual.memory_store",
        }
        assert PROMOTABLE_EVENT_TYPES == expected
  ```

  Replace with:

  ```python
    def test_all_phase1_types_present(self):
        """All Phase 1 + deterministic-promotion event types should be in the allowlist.

        conversation.decision_candidate (TP-MCF-003) is deterministic (regex
        marker detection, no LLM) and belongs in the same allowlist philosophy
        as the original Phase 1 types, though it is trust-lower (see
        promotion.py's _promote_conversation_decision_candidate handler).
        """
        expected = {
            "decision.logged",
            "task.completed",
            "task.failed",
            "task.blocked",
            "error.encountered",
            "workflow.phase_changed",
            "manual.memory_store",
            "conversation.decision_candidate",
        }
        assert PROMOTABLE_EVENT_TYPES == expected
  ```

  Run the file directly to confirm it passes:
  ```bash
  cd services/working-memory-assistant && mise exec -- python -m pytest tests/test_event_type_normalization.py -q
  ```
  Expected output: `8 passed`.

- [ ] **3.6 — Run the full existing WMA promotion suite to confirm no regression** (the new type alone, with no handler yet, must not break `is_promotable` or `promote` for existing types — and `is_promotable("conversation.decision_candidate")` should now be `True` even though there's no handler wired yet, per the next task):
  ```bash
  cd services/working-memory-assistant && mise exec -- python -m pytest tests/test_promotion_allowlist.py tests/test_event_type_normalization.py tests/unit/test_promotion_provenance.py tests/unit/test_promotion_rule_precedence.py -q
  ```
  Expected output: `33 passed`.

- [ ] **3.7 — Commit.**
  ```bash
  git add src/dopemux/memory/capture_client.py services/working-memory-assistant/promotion/promotion.py services/working-memory-assistant/tests/test_event_type_normalization.py tests/unit/test_promotable_allowlist_sync.py
  git commit -m "feat(memory): add conversation.decision_candidate to both promotable allowlists (TP-MCF-003 Task 3)

Adds the new event type to PROMOTABLE_CAPTURE_EVENT_TYPES
(capture_client.py) and PROMOTABLE_EVENT_TYPES (promotion.py), which
must stay synced per claudedocs/tp-mcf-001-authority-map-2026-07-04.md
gap #4. New sync-guard test bridges both import namespaces and asserts
set equality so future drift fails CI. Updates the pre-existing
test_all_phase1_types_present assertion to include the new type."
  ```

---

## Task 4 — Promotion handler `_promote_conversation_decision_candidate`

### Files
- **Modify**: `services/working-memory-assistant/promotion/promotion.py` (add one handler method)
- **New**: `services/working-memory-assistant/tests/unit/test_promote_conversation_decision_candidate.py`

### Design notes (read before writing the test)

Mirror the construction style of `_promote_decision_logged` (redactor use, `[:500]` summary cap, `PromotedEntry` field layout) and `_promote_task_completed` (minimal required-field guard). But **do not** copy `_promote_decision_logged`'s `if not decision_id: return None` guard — a conversation candidate has no `decision_id` by definition (no ConPort decision exists yet; that's the entire point of a *candidate*). The only required field is `title` (per the Task 1 contract, `detect_decision_candidate` never returns a candidate without a non-empty `title`, but the handler must independently guard against malformed/hand-crafted payloads that skip the detector).

Field choices (each justified so you don't have to re-derive them):
- `category="planning"` — an existing valid enum value (`chronicle/schema.sql` line 38-41, `chronicle/store.py` `VALID_CATEGORIES`); no schema change needed.
- `entry_type="decision"` — same enum value `_promote_decision_logged` uses (`chronicle/schema.sql` line 42-45); trust is encoded via `details_json`, not a different `entry_type`, so reusing `"decision"` is correct.
- `importance_score=4` — deliberately **lower** than `_promote_decision_logged`'s `7`. This encodes "provenance only lowers trust" (per `claudedocs/memory-context-fabric-interfaces-2026-07-04.md` §4 invariant 5): a conversation-inferred candidate must never be scored as confidently as an explicitly-logged decision.
- `details={"trust": "conversation-derived"}` (redacted through `self.redactor.redact_payload(...)`, exactly like `_promote_task_failed` and `_promote_task_blocked` redact their `details` dicts) — this is the field the design doc calls out as the only place trust can live, since `work_log_entries` has no `trust` column (`chronicle/schema.sql` confirmed — no such column exists).
- `promotion_rule="conversation_candidate_v1"` — set directly on the `PromotedEntry` returned by the handler; Task 2's fix is what lets this survive the dispatch step in `promote()` instead of being overwritten to `"conversation.decision_candidate"`.
- `reasoning=rationale[:500] if rationale else None` — mirrors `_promote_decision_logged`'s `reasoning=rationale[:2000] if rationale else None` pattern, but capped at 500 (matching the detector's own rationale cap from Task 1, so there's no double-truncation surprise).
- Summary format: `f"Candidate decision: {title}"[:500]` — same `[:500]` cap pattern used by every other handler's `summary` field.

### TDD steps

- [ ] **4.1 — Write the failing test file.** Create `services/working-memory-assistant/tests/unit/test_promote_conversation_decision_candidate.py`:

```python
"""Promotion handler for conversation.decision_candidate (TP-MCF-003 Task 4).

Trust is conversation-derived and MUST be lower-confidence than a real
decision.logged promotion: importance_score=4 (vs 7), promotion_rule=
"conversation_candidate_v1" (never "decision.logged"), and
details_json.trust="conversation-derived" (the only place trust can live,
since work_log_entries has no trust column).
"""

import pytest

from promotion.promotion import PromotionEngine


@pytest.fixture
def engine():
    return PromotionEngine()


def _event(**payload_overrides):
    payload = {
        "title": "use Redis Streams for the event bus",
        "rationale": "deterministic and replay-safe",
    }
    payload.update(payload_overrides)
    return {
        "id": "evt-candidate-1",
        "event_type": "conversation.decision_candidate",
        "source": "transcript",
        "ts_utc": "2026-07-04T00:00:00+00:00",
        "payload": payload,
    }


def test_is_promotable():
    engine = PromotionEngine()
    assert engine.is_promotable("conversation.decision_candidate") is True


def test_candidate_promotes_to_entry(engine):
    entry = engine.promote(_event())

    assert entry is not None
    assert entry.category == "planning"
    assert entry.entry_type == "decision"
    assert entry.summary == "Candidate decision: use Redis Streams for the event bus"
    assert entry.outcome == "in_progress"


def test_promotion_rule_is_conversation_candidate_v1_not_normalized_type(engine):
    entry = engine.promote(_event())

    assert entry is not None
    assert entry.promotion_rule == "conversation_candidate_v1"
    assert entry.promotion_rule != "conversation.decision_candidate"


def test_trust_lives_in_details_json_only(engine):
    entry = engine.promote(_event())

    assert entry is not None
    assert entry.details is not None
    assert entry.details["trust"] == "conversation-derived"


def test_importance_score_is_lower_than_real_decision_logged(engine):
    candidate_entry = engine.promote(_event())
    real_decision_entry = engine.promote(
        "decision.logged",
        {
            "decision_id": "dec-real-1",
            "title": "Use Redis Streams",
            "choice": "Redis",
        },
    )

    assert candidate_entry is not None
    assert real_decision_entry is not None
    assert candidate_entry.importance_score < real_decision_entry.importance_score
    assert candidate_entry.importance_score == 4
    assert real_decision_entry.importance_score == 7


def test_rationale_becomes_reasoning_capped_at_500(engine):
    entry = engine.promote(_event(rationale="r" * 700))

    assert entry is not None
    assert entry.reasoning is not None
    assert len(entry.reasoning) == 500


def test_missing_title_does_not_promote(engine):
    entry = engine.promote(_event(title=""))
    assert entry is None


def test_missing_rationale_still_promotes_with_none_reasoning(engine):
    event = _event()
    del event["payload"]["rationale"]
    entry = engine.promote(event)

    assert entry is not None
    assert entry.reasoning is None


def test_source_provenance_fields_are_populated(engine):
    entry = engine.promote(_event())

    assert entry is not None
    assert entry.source_event_id == "evt-candidate-1"
    assert entry.source_event_type == "conversation.decision_candidate"
    assert entry.source_adapter == "transcript"
    assert entry.source_event_ts_utc == "2026-07-04T00:00:00+00:00"


def test_never_produces_decision_logged_source_event_type(engine):
    entry = engine.promote(_event())

    assert entry is not None
    assert entry.source_event_type != "decision.logged"
```

  Run it and confirm it fails (`promote` currently returns `None` because there's no `_promote_conversation_decision_candidate` handler yet, so `getattr(self, ..., None)` is `None` and dispatch returns `None`):
  ```bash
  cd services/working-memory-assistant && mise exec -- python -m pytest tests/unit/test_promote_conversation_decision_candidate.py -q
  ```
  Expected output: `2 passed, 8 failed` — `test_is_promotable` passes (the type is now in the allowlist from Task 3), and `test_missing_title_does_not_promote` also passes trivially (it asserts `entry is None`, which is true with no handler at all, for the wrong reason — that's fine, Task 4.3 re-validates it for the right reason once the handler exists). The other 8 tests fail because every `_promote_*` dispatch with no matching handler method returns `None`, so any assertion of `entry is not None` fails.

- [ ] **4.2 — Implement the handler.** In `services/working-memory-assistant/promotion/promotion.py`, add the new method. Insert it immediately before `_promote_manual_memory_store` (i.e., after `_promote_workflow_phase_changed` and before `_promote_manual_memory_store`), so the handler ordering in the file mirrors the ordering in `PROMOTABLE_EVENT_TYPES`:

```python
    def _promote_conversation_decision_candidate(
        self, data: dict[str, Any]
    ) -> Optional[PromotedEntry]:
        """Promote conversation.decision_candidate event.

        TP-MCF-003. This is a DETERMINISTICALLY-DETECTED candidate (see
        src/dopemux/memory/conversation_promotion.py — regex markers only,
        no LLM), never an auto-write to ConPort and never a decision.logged
        event. Trust is encoded ONLY in details_json.trust (work_log_entries
        has no trust column) and importance_score is deliberately lower than
        a real decision.logged promotion (4 vs 7), per the "provenance only
        lowers trust" invariant in
        claudedocs/memory-context-fabric-interfaces-2026-07-04.md §4.

        Requires: title (non-empty). rationale is optional.
        """
        title = data.get("title", "")
        rationale = data.get("rationale", "")

        if not title:
            return None

        details = self.redactor.redact_payload({"trust": "conversation-derived"})

        return PromotedEntry(
            category="planning",
            entry_type="decision",
            summary=f"Candidate decision: {title}"[:500],
            outcome="in_progress",
            importance_score=4,
            reasoning=rationale[:500] if rationale else None,
            details=details,
            tags=self._extract_tags(data),
            promotion_rule="conversation_candidate_v1",
        )

```

- [ ] **4.3 — Run the test again and confirm it passes.**
  ```bash
  cd services/working-memory-assistant && mise exec -- python -m pytest tests/unit/test_promote_conversation_decision_candidate.py -q
  ```
  Expected output: `10 passed`.

- [ ] **4.4 — Run the WMA promotion-relevant suite to confirm no regression.**

  **Important — do NOT run bare `pytest tests/` for this check.** The WMA `tests/` tree has **pre-existing, packet-unrelated collection errors** (verified empirically, present before this packet touched anything): `tests/test_migration_runner_optimized.py`, `tests/test_predictive_restoration.py`, `tests/test_wma_core.py`, and `tests/unit/test_copilot_adapter_hardening.py` all fail to collect with `ImportError: Unable to import services.copilot_transcript_ingester modules. Run from repository root or set PYTHONPATH to include it.` — a `dopemux.memory.adapters.copilot` import that only resolves when the interpreter is invoked from repo root, not from `services/working-memory-assistant/`. Additionally, `tests/test_dope_memory.py`, `tests/test_phase2_reflection_trajectory.py`, `tests/test_reflection.py`, `tests/test_trajectory.py`, and `tests/test_trajectory_boost_in_ranking.py` have pre-existing failures unrelated to promotion (reflection/trajectory ordering tests). None of this is caused by this packet — verified by running the identical command against an unmodified copy of this repo before any Task 1-4 edits were applied. **Do not attempt to fix these; they are out of this packet's scope.**

  Instead, run the promotion-relevant subset that is known-clean in the baseline:
  ```bash
  cd services/working-memory-assistant && mise exec -- python -m pytest \
    tests/test_event_type_normalization.py \
    tests/test_eventbus_consumer.py \
    tests/test_mcp_http_endpoint.py \
    tests/test_promotion_allowlist.py \
    tests/test_session_tracker.py \
    tests/test_store_fail_closed.py \
    tests/unit/ \
    --ignore=tests/unit/test_copilot_adapter_hardening.py \
    -q
  ```
  Expected output: `113 passed, 1 skipped` (the skip is `tests/test_mcp_http_endpoint.py` — `could not import 'fastmcp': No module named 'fastmcp'`, an unrelated optional-dependency gap, not a regression). This count includes all new/modified test files from Tasks 2–4 (`test_promotion_rule_precedence.py`, `test_promote_conversation_decision_candidate.py`, the updated `test_event_type_normalization.py`) alongside the full pre-existing `tests/unit/` directory (minus the one broken-import file) and the other known-good top-level files.

- [ ] **4.5 — Commit.**
  ```bash
  git add services/working-memory-assistant/promotion/promotion.py services/working-memory-assistant/tests/unit/test_promote_conversation_decision_candidate.py
  git commit -m "feat(wma): promote conversation.decision_candidate events (TP-MCF-003 Task 4)

New _promote_conversation_decision_candidate handler. Mirrors
_promote_decision_logged's construction style but requires only
title (no decision_id — no ConPort decision exists yet, that's the
point of a candidate). importance_score=4 (vs 7 for real decisions),
promotion_rule=\"conversation_candidate_v1\", trust encoded in
details_json only (no trust column exists in work_log_entries)."
  ```

---

## Task 5 — Emit-side: `emit_promotable_capture_event` acceptance + no-ConPort + never-decision-logged tests

This task does not add new production code — `emit_promotable_capture_event` in `src/dopemux/memory/capture_client.py` already accepts any type in `PROMOTABLE_CAPTURE_EVENT_TYPES` generically (Task 3 already added the new type to that frozenset). This task adds the **acceptance tests** proving the emit side works end-to-end for the new type, plus the two hard-invariant tests (no ConPort import, never `decision.logged`) that this packet's spec requires.

### Files
- **New**: `tests/unit/test_conversation_decision_candidate_emit.py`

### TDD steps

- [ ] **5.1 — Write the test file** (there is no "confirm it fails first" step for 5.1's acceptance tests, since Task 3 already made the type acceptable — these are net-new coverage, not a red/green cycle on production code; run once to confirm they pass immediately, which validates Task 3's frozenset edit end-to-end through the real `emit_capture_event`/SQLite path). Create `tests/unit/test_conversation_decision_candidate_emit.py`:

```python
"""Emit-side acceptance for conversation.decision_candidate (TP-MCF-003 Task 5).

Hard invariants under test:
- emit_promotable_capture_event accepts the new type and writes to the raw
  ledger (same tmp_path + DOPEMUX_CAPTURE_LEDGER_PATH harness used throughout
  tests/unit/test_memory_capture_client.py).
- The emitted event_type is EXACTLY "conversation.decision_candidate" —
  never "decision.logged" (which the codebase reserves for post-write
  receipts from a real ConPort write; see
  claudedocs/tp-mcf-001-authority-map-2026-07-04.md Domain F).
- No module in the conversation-promotion capture path imports an
  httpx/requests/aiohttp/ConPort client — the candidate never reaches
  ConPort directly. This is a static import-scan test, not a runtime mock
  (a runtime mock would only prove "we didn't call it this time"; the
  import-scan proves "the capability to call it does not exist in this
  module").
"""

import ast
import json
import sqlite3
from pathlib import Path

from dopemux.memory.capture_client import emit_promotable_capture_event
from dopemux.memory.conversation_promotion import detect_decision_candidate

REPO_ROOT = Path(__file__).resolve().parents[2]

_FORBIDDEN_IMPORT_MODULES = {
    "httpx",
    "requests",
    "aiohttp",
    "urllib3",
}
_FORBIDDEN_IMPORT_SUBSTRINGS = ("conport",)


def _event_payload(ledger_path: Path, event_id: str) -> dict:
    conn = sqlite3.connect(str(ledger_path))
    try:
        row = conn.execute(
            "SELECT payload_json, event_type FROM raw_activity_events WHERE id = ?",
            (event_id,),
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    payload_json, event_type = row
    return {"payload": json.loads(payload_json), "event_type": event_type}


def test_emit_accepts_conversation_decision_candidate(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    candidate = detect_decision_candidate(
        "decision: use Redis Streams for the event bus"
    )
    assert candidate is not None

    result = emit_promotable_capture_event(
        "conversation.decision_candidate",
        {"title": candidate.title, "rationale": candidate.rationale},
        source="transcript",
        mode="cli",
        repo_root=REPO_ROOT,
        emit_event_bus=False,
    )

    assert result.event_type == "conversation.decision_candidate"

    stored = _event_payload(ledger_path, result.event_id)
    assert stored["event_type"] == "conversation.decision_candidate"
    assert stored["payload"]["title"] == candidate.title


def test_emitted_event_type_is_never_decision_logged(tmp_path, monkeypatch):
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    candidate = detect_decision_candidate("we decided to use SQLite for the ledger")
    assert candidate is not None

    result = emit_promotable_capture_event(
        "conversation.decision_candidate",
        {"title": candidate.title, "rationale": candidate.rationale},
        source="transcript",
        mode="cli",
        repo_root=REPO_ROOT,
        emit_event_bus=False,
    )

    assert result.event_type == "conversation.decision_candidate"
    assert result.event_type != "decision.logged"


def test_detect_then_emit_pipeline_end_to_end(tmp_path, monkeypatch):
    """Full pipeline: detector -> emit -> raw ledger. No promotion engine
    involved here (that's a WMA-side concern tested in Task 4) — this test
    only proves the dopemux-side detect->emit contract."""
    ledger_path = tmp_path / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger_path))

    turn = "approved: migrate the chronicle schema to v2"
    candidate = detect_decision_candidate(turn)
    assert candidate is not None

    result = emit_promotable_capture_event(
        "conversation.decision_candidate",
        {"title": candidate.title, "rationale": candidate.rationale},
        source="transcript",
        mode="cli",
        repo_root=REPO_ROOT,
        emit_event_bus=False,
    )

    assert result.event_type == "conversation.decision_candidate"
    assert result.inserted is True


def test_question_form_never_reaches_emit_because_detector_returns_none():
    """Negative-path proof: a question never even produces a candidate to
    emit in the first place (belt-and-suspenders with Task 1's detector
    tests, but scoped here to the emit-adjacent boundary)."""
    assert detect_decision_candidate("Should we decide to use Redis?") is None


def _iter_import_module_names(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                yield node.module


def test_conversation_promotion_module_imports_no_conport_or_http_client():
    """Static import-scan: src/dopemux/memory/conversation_promotion.py must
    import NOTHING that could reach ConPort or make an HTTP call. This is
    the module that owns detection; it must remain a pure function forever."""
    module_path = REPO_ROOT / "src" / "dopemux" / "memory" / "conversation_promotion.py"
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    imported = set(_iter_import_module_names(tree))

    for forbidden in _FORBIDDEN_IMPORT_MODULES:
        assert not any(
            name == forbidden or name.startswith(f"{forbidden}.") for name in imported
        ), f"forbidden import '{forbidden}' found in conversation_promotion.py: {imported}"

    for name in imported:
        lowered = name.lower()
        for substring in _FORBIDDEN_IMPORT_SUBSTRINGS:
            assert substring not in lowered, (
                f"forbidden substring '{substring}' found in import '{name}' "
                f"in conversation_promotion.py"
            )


def test_capture_client_module_imports_no_conport_client():
    """capture_client.py (the emit-side spine this packet reuses) must not
    import a ConPort client either — it is a raw-ledger writer only."""
    module_path = REPO_ROOT / "src" / "dopemux" / "memory" / "capture_client.py"
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    imported = set(_iter_import_module_names(tree))

    for name in imported:
        lowered = name.lower()
        for substring in _FORBIDDEN_IMPORT_SUBSTRINGS:
            assert substring not in lowered, (
                f"forbidden substring '{substring}' found in import '{name}' "
                f"in capture_client.py"
            )
```

- [ ] **5.2 — Run it and confirm all tests pass.**
  ```bash
  mise exec -- python -m pytest tests/unit/test_conversation_decision_candidate_emit.py -q
  ```
  Expected output: `6 passed`.

- [ ] **5.3 — Commit.**
  ```bash
  git add tests/unit/test_conversation_decision_candidate_emit.py
  git commit -m "test(memory): emit-side acceptance + no-ConPort + never-decision-logged (TP-MCF-003 Task 5)

Proves emit_promotable_capture_event accepts conversation.decision_candidate
end-to-end through the real SQLite ledger, the emitted event_type is never
decision.logged, and neither conversation_promotion.py nor capture_client.py
imports an httpx/requests/aiohttp/ConPort client (static AST import scan,
not a runtime mock)."
  ```

---

## Task 6 — Combined verification + proof-gate checklist

### 6.1 — Run every test file this packet touched, both suites

Root suite (dopemux-side: detector, sync-guard, emit acceptance, existing capture-client regression):
```bash
mise exec -- python -m pytest \
  tests/unit/test_memory_capture_client.py \
  tests/unit/test_conversation_promotion_detector.py \
  tests/unit/test_promotable_allowlist_sync.py \
  tests/unit/test_conversation_decision_candidate_emit.py \
  -q
```
Expected output: all pass, `0 failed` (23 from the pre-existing `test_memory_capture_client.py` + 19 + 2 + 6 = 50 total, but the requirement is `0 failed`, not an exact count — pytest's own summary line is the source of truth).

WMA suite (promotion-side: dispatch fix regression, new handler, promotion-relevant existing WMA tests). **Do not run bare `pytest tests/`** — as established in Task 4.4, the WMA `tests/` tree has pre-existing, packet-unrelated collection errors and failures (import-path issues in 4 files, reflection/trajectory ordering failures in 5 more) that predate this packet and are out of scope. Use the same scoped command from Task 4.4:
```bash
cd services/working-memory-assistant && mise exec -- python -m pytest \
  tests/test_event_type_normalization.py \
  tests/test_eventbus_consumer.py \
  tests/test_mcp_http_endpoint.py \
  tests/test_promotion_allowlist.py \
  tests/test_session_tracker.py \
  tests/test_store_fail_closed.py \
  tests/unit/ \
  --ignore=tests/unit/test_copilot_adapter_hardening.py \
  -q
```
Expected output: `113 passed, 1 skipped` (same result as Task 4.4 — the skip is the unrelated missing `fastmcp` optional dependency).

### 6.2 — Proof-gate checklist (all must be checked before this packet is considered done)

- [ ] **Both-allowlists sync test exists and passes**: `tests/unit/test_promotable_allowlist_sync.py::test_both_allowlists_are_identical` and `::test_conversation_decision_candidate_is_in_both_allowlists` both green.
- [ ] **No-ConPort/no-HTTP-client test exists and passes**: `tests/unit/test_conversation_decision_candidate_emit.py::test_conversation_promotion_module_imports_no_conport_or_http_client` and `::test_capture_client_module_imports_no_conport_client` both green.
- [ ] **Negative-detection tests exist and pass**: every `test_*question*`/`test_*hedged*`/`test_marker_only*` test in `tests/unit/test_conversation_promotion_detector.py` green (specifically: `test_question_form_never_matches_even_with_marker_word`, `test_hedged_hypothetical_without_question_mark_rejected`, `test_did_we_decide_question_rejected`, `test_marker_only_no_content_rejected`, `test_marker_must_be_anchored_to_start`).
- [ ] **Authority/trust label assertion passes**: `services/working-memory-assistant/tests/unit/test_promote_conversation_decision_candidate.py::test_trust_lives_in_details_json_only` and `::test_importance_score_is_lower_than_real_decision_logged` both green.
- [ ] **Never-`decision.logged` assertion passes**: `tests/unit/test_conversation_decision_candidate_emit.py::test_emitted_event_type_is_never_decision_logged` and `services/working-memory-assistant/tests/unit/test_promote_conversation_decision_candidate.py::test_never_produces_decision_logged_source_event_type` both green.
- [ ] **`promotion_rule` precedence regression test passes**: `services/working-memory-assistant/tests/unit/test_promotion_rule_precedence.py` both tests green (proves the Task 2 dispatch fix is backward-compatible).
- [ ] **`git status` is clean except for this packet's new/modified files** (no stray edits to files outside this plan's scope):
  ```bash
  git status --porcelain
  ```
  Expected: only these paths appear (as `M` or `??`):
  - `src/dopemux/memory/conversation_promotion.py` (new)
  - `src/dopemux/memory/capture_client.py` (modified)
  - `services/working-memory-assistant/promotion/promotion.py` (modified)
  - `services/working-memory-assistant/tests/test_event_type_normalization.py` (modified)
  - `services/working-memory-assistant/tests/unit/test_promotion_rule_precedence.py` (new)
  - `services/working-memory-assistant/tests/unit/test_promote_conversation_decision_candidate.py` (new)
  - `tests/unit/test_conversation_promotion_detector.py` (new)
  - `tests/unit/test_promotable_allowlist_sync.py` (new)
  - `tests/unit/test_conversation_decision_candidate_emit.py` (new)

  (If working through the checkboxes commit-by-commit as instructed, this will already be clean — nothing to stage — by the time you reach this final check, since Tasks 1–5 each ended with a commit.)

### 6.3 — Final report format

When done, report using this structure (per repo governance doctrine):

- **Change Summary**: added `conversation.decision_candidate` event type end-to-end (detector → both allowlists → promotion handler → emit acceptance tests); fixed a `promotion_rule` dispatch clobber that would have silently broken the candidate's trust label.
- **Authority Used**: `claudedocs/memory-context-fabric-design-2026-07-04.md` v3 §2/§6, `claudedocs/tp-mcf-001-authority-map-2026-07-04.md` §4, `claudedocs/memory-context-fabric-interfaces-2026-07-04.md` §2.2/§2.3; runtime code in `capture_client.py`, `promotion.py`, `chronicle/schema.sql`, `chronicle/store.py`.
- **Analysis Performed**: read all three authority docs + 4 runtime files; ran both existing test suites before touching code (baseline green); empirically spiked (and reverted) the `promotion_rule` clobber fix + new handler before committing to the plan, proving invariant #2 achievable.
- **Validation Performed**: PASS — both suites listed in §6.1 (paste actual pytest output here when executing this plan).
- **Remaining Uncertainty / Risk**: this packet does not build the transcript-file watcher (TP-MCF-002) that would call `detect_decision_candidate` on real turns in production — that wiring is out of scope and belongs to TP-MCF-002/a future integration packet. The regex marker set is intentionally narrow (6 patterns); real-world transcript phrasing not matching any marker will simply not produce a candidate (fail-closed, not fail-open — no false positives risk, only false negatives, which is the correct default per the design doc's "deterministic first" cornerstone).
- **Files Touched**: see §6.2's `git status --porcelain` list.
- **Git State**: branch `claude/memory-context-fabric` (or whatever branch this plan is executed on); commits per Tasks 1, 2, 3, 4, 5 (5 commits total, one per task).
- **Rollback Plan**: `git revert` the 5 commits in reverse order, or `git reset --hard <sha-before-task-1>` if the branch has not been pushed/shared.
- **Requested Next Step**: hand off to whichever packet builds the transcript-file ingest adapter (TP-MCF-002) so `detect_decision_candidate` + `emit_promotable_capture_event("conversation.decision_candidate", ...)` gets called on real transcript turns; that packet is out of this one's scope by design.
