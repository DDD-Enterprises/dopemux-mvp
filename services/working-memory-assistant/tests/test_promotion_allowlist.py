"""
Tests for the Phase 1 promotion allowlist.

Verifies that only the specified high-signal event types are promoted,
and non-allowlisted types are correctly rejected.
"""

import pytest

from promotion.promotion import PromotionEngine, normalize_event_type


class TestPromotionAllowlist:
    """Tests for Phase 1 strict allowlist enforcement."""

    @pytest.fixture
    def engine(self):
        return PromotionEngine()

    # ─────────────────────────────────────────────────────────────────
    # Allowed types should promote
    # ─────────────────────────────────────────────────────────────────

    def test_decision_logged_promotes(self, engine):
        """decision.logged should be promotable."""
        assert engine.is_promotable("decision.logged") is True

        entry = engine.promote(
            "decision.logged",
            {
                "decision_id": "dec-123",
                "title": "Use Redis Streams",
                "choice": "Redis",
                "rationale": "Proven reliability",
            },
        )
        assert entry is not None
        assert entry.entry_type == "decision"

    def test_task_completed_promotes(self, engine):
        """task.completed should be promotable."""
        assert engine.is_promotable("task.completed") is True

        entry = engine.promote(
            "task.completed", {"task_id": "task-1", "title": "Implement EventBus"}
        )
        assert entry is not None
        assert entry.entry_type == "milestone"

    def test_task_failed_promotes(self, engine):
        """task.failed should be promotable."""
        assert engine.is_promotable("task.failed") is True

        entry = engine.promote(
            "task.failed",
            {"task_id": "task-2", "title": "Deploy", "error": "Connection timeout"},
        )
        assert entry is not None
        assert entry.entry_type == "error"

    def test_task_blocked_promotes(self, engine):
        """task.blocked should be promotable."""
        assert engine.is_promotable("task.blocked") is True

        entry = engine.promote(
            "task.blocked",
            {"task_id": "task-3", "title": "Review", "reason": "Waiting for approval"},
        )
        assert entry is not None
        assert entry.entry_type == "blocker"

    def test_error_encountered_promotes(self, engine):
        """error.encountered should be promotable."""
        assert engine.is_promotable("error.encountered") is True

        entry = engine.promote(
            "error.encountered", {"message": "TypeError: undefined variable"}
        )
        assert entry is not None
        assert entry.entry_type == "error"

    def test_workflow_phase_changed_promotes(self, engine):
        """workflow.phase_changed should be promotable."""
        assert engine.is_promotable("workflow.phase_changed") is True

        entry = engine.promote(
            "workflow.phase_changed",
            {"from_phase": "planning", "to_phase": "implementation"},
        )
        assert entry is not None
        assert entry.entry_type == "workflow_transition"

    def test_manual_memory_store_promotes(self, engine):
        """manual.memory_store should be promotable."""
        assert engine.is_promotable("manual.memory_store") is True

        entry = engine.promote(
            "manual.memory_store",
            {
                "category": "planning",
                "entry_type": "manual_note",
                "summary": "User note",
            },
        )
        assert entry is not None
        assert entry.entry_type == "manual_note"

    # ─────────────────────────────────────────────────────────────────
    # Underscore variants should also work (via normalization)
    # ─────────────────────────────────────────────────────────────────

    def test_underscore_decision_logged_promotes(self, engine):
        """decision_logged (underscore) should normalize and promote."""
        assert engine.is_promotable("decision_logged") is True

        entry = engine.promote(
            "decision_logged",
            {"decision_id": "dec-456", "title": "Test underscore", "choice": "Yes"},
        )
        assert entry is not None

    def test_underscore_task_failed_promotes(self, engine):
        """task_failed (underscore) should normalize and promote."""
        assert engine.is_promotable("task_failed") is True

    # ─────────────────────────────────────────────────────────────────
    # Non-allowlisted types should NOT promote
    # ─────────────────────────────────────────────────────────────────

    def test_file_saved_does_not_promote(self, engine):
        """file.saved is not in Phase 1 allowlist."""
        assert engine.is_promotable("file.saved") is False
        assert engine.promote("file.saved", {"path": "/test.py"}) is None

    def test_git_commit_does_not_promote(self, engine):
        """git.commit is not in Phase 1 allowlist."""
        assert engine.is_promotable("git.commit") is False
        assert engine.promote("git.commit", {"sha": "abc123"}) is None

    def test_chat_message_does_not_promote(self, engine):
        """chat.message is not in Phase 1 allowlist."""
        assert engine.is_promotable("chat.message") is False
        assert engine.promote("chat.message", {"content": "Hello"}) is None

    def test_cursor_moved_does_not_promote(self, engine):
        """cursor.moved is not in Phase 1 allowlist."""
        assert engine.is_promotable("cursor.moved") is False
        assert engine.promote("cursor.moved", {"line": 10}) is None

    def test_unknown_type_does_not_promote(self, engine):
        """Completely unknown types should not promote."""
        assert engine.is_promotable("unknown.event") is False
        assert engine.is_promotable("random_thing") is False
        assert engine.promote("custom.internal.event", {"data": "test"}) is None

    # ─────────────────────────────────────────────────────────────────
    # Promotion requires valid data (not just allowlisted type)
    # ─────────────────────────────────────────────────────────────────

    def test_decision_logged_requires_valid_data(self, engine):
        """decision.logged needs decision_id, title, and choice/rationale."""
        # Missing decision_id
        assert engine.promote("decision.logged", {"title": "Test"}) is None

        # Missing title
        assert engine.promote("decision.logged", {"decision_id": "dec-1"}) is None

        # Missing both choice and rationale
        assert (
            engine.promote(
                "decision.logged", {"decision_id": "dec-1", "title": "Test"}
            )
            is None
        )

        # Valid (has choice)
        entry = engine.promote(
            "decision.logged",
            {"decision_id": "dec-1", "title": "Test", "choice": "Option A"},
        )
        assert entry is not None

        # Valid (has rationale)
        entry = engine.promote(
            "decision.logged",
            {"decision_id": "dec-1", "title": "Test", "rationale": "Because..."},
        )
        assert entry is not None
