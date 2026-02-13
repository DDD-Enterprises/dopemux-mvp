"""Tests for PM status dialect mapping tables."""

from dopemux.pm.mapping import (
    CANONICAL_TO_CONPORT,
    CANONICAL_TO_ORCHESTRATOR,
    CANONICAL_TO_TASKMASTER,
    CONPORT_TO_CANONICAL,
    LOSSY_MAPPINGS,
    ORCHESTRATOR_LOSSY_REASONS,
    ORCHESTRATOR_TO_CANONICAL,
    TASKMASTER_TO_CANONICAL,
)
from dopemux.pm.models import PMTaskStatus


class TestMappingTableCompleteness:
    """All mapping tables should only contain canonical PMTaskStatus values."""

    def test_orchestrator_to_canonical_values_are_canonical(self):
        for status in ORCHESTRATOR_TO_CANONICAL.values():
            assert isinstance(status, PMTaskStatus)

    def test_conport_to_canonical_values_are_canonical(self):
        for status in CONPORT_TO_CANONICAL.values():
            assert isinstance(status, PMTaskStatus)

    def test_taskmaster_to_canonical_values_are_canonical(self):
        for status in TASKMASTER_TO_CANONICAL.values():
            assert isinstance(status, PMTaskStatus)

    def test_canonical_to_orchestrator_covers_all_statuses(self):
        """Every canonical status has an orchestrator mapping."""
        for status in PMTaskStatus:
            assert status in CANONICAL_TO_ORCHESTRATOR

    def test_canonical_to_conport_covers_all_statuses(self):
        for status in PMTaskStatus:
            assert status in CANONICAL_TO_CONPORT

    def test_canonical_to_taskmaster_covers_all_statuses(self):
        for status in PMTaskStatus:
            assert status in CANONICAL_TO_TASKMASTER


class TestOrchestatorMapping:
    """Orchestrator dialect mapping specifics."""

    def test_lossless_mappings(self):
        assert ORCHESTRATOR_TO_CANONICAL["pending"] == PMTaskStatus.TODO
        assert ORCHESTRATOR_TO_CANONICAL["in_progress"] == PMTaskStatus.IN_PROGRESS
        assert ORCHESTRATOR_TO_CANONICAL["completed"] == PMTaskStatus.DONE
        assert ORCHESTRATOR_TO_CANONICAL["blocked"] == PMTaskStatus.BLOCKED

    def test_lossy_adhd_states_map_to_blocked(self):
        assert ORCHESTRATOR_TO_CANONICAL["needs_break"] == PMTaskStatus.BLOCKED
        assert ORCHESTRATOR_TO_CANONICAL["context_switch"] == PMTaskStatus.BLOCKED
        assert ORCHESTRATOR_TO_CANONICAL["paused"] == PMTaskStatus.BLOCKED

    def test_lossy_reasons_documented(self):
        """Every lossy orchestrator mapping has a reason string."""
        for status in ["needs_break", "context_switch", "paused"]:
            assert status in ORCHESTRATOR_LOSSY_REASONS
            assert len(ORCHESTRATOR_LOSSY_REASONS[status]) > 0


class TestConPortMapping:
    """ConPort dialect mapping specifics."""

    def test_bidirectional_lossless(self):
        """Lossless ConPort statuses roundtrip correctly."""
        for conport_str, canonical in CONPORT_TO_CANONICAL.items():
            assert CANONICAL_TO_CONPORT[canonical] == conport_str


class TestLossyMappingDocumentation:
    """All lossy mappings must be explicitly documented."""

    def test_lossy_mappings_not_empty(self):
        assert len(LOSSY_MAPPINGS) > 0

    def test_all_entries_have_required_fields(self):
        required_keys = {"source", "dialect_status", "canonical_status", "reason"}
        for entry in LOSSY_MAPPINGS:
            assert required_keys.issubset(entry.keys()), f"Missing keys in {entry}"

    def test_canonical_statuses_in_lossy_are_valid(self):
        valid_values = {s.value for s in PMTaskStatus}
        for entry in LOSSY_MAPPINGS:
            canonical = entry["canonical_status"]
            # Allow both enum values and descriptive strings for reverse mappings
            if canonical in valid_values:
                continue
            # Reverse mappings use orchestrator dialect values
            assert "reverse" in entry.get("dialect_status", ""), (
                f"Non-canonical status '{canonical}' in lossy mapping without "
                f"'reverse' marker: {entry}"
            )
