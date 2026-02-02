"""
Tests for event type normalization in the Promotion Engine.

Per Phase 1 spec: event types should be in canonical dotted form (e.g., decision.logged).
The normalizer handles underscore variants for defensive robustness.
"""

import pytest

from promotion.promotion import normalize_event_type, PROMOTABLE_EVENT_TYPES


class TestEventTypeNormalization:
    """Tests for normalize_event_type function."""

    def test_dotted_input_stays_dotted(self):
        """Dotted input should pass through unchanged."""
        assert normalize_event_type("decision.logged") == "decision.logged"
        assert normalize_event_type("task.completed") == "task.completed"
        assert normalize_event_type("error.encountered") == "error.encountered"
        assert normalize_event_type("workflow.phase_changed") == "workflow.phase_changed"

    def test_underscore_converts_to_dotted(self):
        """Underscore input should convert to dotted form."""
        assert normalize_event_type("decision_logged") == "decision.logged"
        assert normalize_event_type("task_completed") == "task.completed"
        assert normalize_event_type("task_failed") == "task.failed"
        assert normalize_event_type("manual_memory_store") == "manual.memory.store"

    def test_whitespace_trimmed(self):
        """Leading/trailing whitespace should be trimmed."""
        assert normalize_event_type("  decision.logged  ") == "decision.logged"
        assert normalize_event_type("\ttask.failed\n") == "task.failed"

    def test_case_normalized_to_lowercase(self):
        """Event types should be lowercased."""
        assert normalize_event_type("Decision.Logged") == "decision.logged"
        assert normalize_event_type("TASK.COMPLETED") == "task.completed"
        assert normalize_event_type("Task_Failed") == "task.failed"

    def test_empty_input_returns_unknown(self):
        """Empty/None input should return 'unknown'."""
        assert normalize_event_type("") == "unknown"
        assert normalize_event_type("   ") == "unknown"


    def test_unknown_types_pass_through(self):
        """Unknown types should still normalize but won't match allowlist."""
        assert normalize_event_type("custom.event") == "custom.event"
        assert normalize_event_type("custom_event") == "custom.event"


class TestPromotableEventTypes:
    """Verify PROMOTABLE_EVENT_TYPES contains expected Phase 1 types."""

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

    def test_no_underscore_variants_in_allowlist(self):
        """Allowlist should use dotted forms (underscores in segments are OK)."""
        for event_type in PROMOTABLE_EVENT_TYPES:
            # All types should have at least one dot
            assert "." in event_type
            # Types should be dotted hierarchy, not flat underscore
            # (e.g., 'decision.logged' not 'decision_logged')
            # Note: 'workflow.phase_changed' has underscore in segment which is valid
