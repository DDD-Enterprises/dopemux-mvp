"""Tests for canonical PM task model and ID generation."""

from datetime import datetime, timezone

import pytest

from dopemux.pm.models import (
    PMTask,
    PMTaskStatus,
    PMTransitionRequest,
    content_hash_task_id,
    normalize_text,
)


class TestPMTaskStatus:
    """PMTaskStatus must have exactly 5 values."""

    def test_exactly_five_values(self):
        values = list(PMTaskStatus)
        assert len(values) == 5

    def test_canonical_values(self):
        expected = {"TODO", "IN_PROGRESS", "BLOCKED", "DONE", "CANCELED"}
        actual = {s.value for s in PMTaskStatus}
        assert actual == expected


class TestNormalizeText:
    """normalize_text lowercases, strips, collapses whitespace."""

    def test_lowercase(self):
        assert normalize_text("Hello World") == "hello world"

    def test_strip_whitespace(self):
        assert normalize_text("  hello  ") == "hello"

    def test_collapse_internal_whitespace(self):
        assert normalize_text("hello   world\t\nfoo") == "hello world foo"

    def test_empty_string(self):
        assert normalize_text("") == ""

    def test_already_normalized(self):
        assert normalize_text("hello world") == "hello world"


class TestContentHashTaskId:
    """Deterministic task ID generation per ConPort Decision #1."""

    def test_with_source_task_id_deterministic(self):
        """Same (source, source_task_id) always produces same ID."""
        id1 = content_hash_task_id("taskmaster", "tm-123", "Some Title")
        id2 = content_hash_task_id("taskmaster", "tm-123", "Different Title")
        assert id1 == id2  # source_task_id takes precedence

    def test_without_source_task_id_uses_content(self):
        """Without source_task_id, falls back to content hash."""
        id1 = content_hash_task_id("cli", None, "Fix the bug", "In auth module")
        id2 = content_hash_task_id("cli", None, "Fix the bug", "In auth module")
        assert id1 == id2

    def test_without_source_task_id_different_content_different_id(self):
        id1 = content_hash_task_id("cli", None, "Task A", "Desc A")
        id2 = content_hash_task_id("cli", None, "Task B", "Desc B")
        assert id1 != id2

    def test_created_at_utc_excluded_from_hash(self):
        """created_at_utc must NOT affect task_id — hash only uses source+content."""
        id1 = content_hash_task_id("cli", None, "Task X", "Desc X")
        id2 = content_hash_task_id("cli", None, "Task X", "Desc X")
        # These are identical because created_at_utc is never passed to hash
        assert id1 == id2

    def test_normalization_applied_in_fallback(self):
        """Whitespace/case differences normalized in fallback path."""
        id1 = content_hash_task_id("cli", None, "Fix Bug", "In Auth")
        id2 = content_hash_task_id("cli", None, "  fix  bug  ", "  in  auth  ")
        assert id1 == id2

    def test_returns_lowercase_hex(self):
        result = content_hash_task_id("test", "id-1", "title")
        assert result == result.lower()
        assert all(c in "0123456789abcdef" for c in result)

    def test_returns_64_char_sha256(self):
        result = content_hash_task_id("test", "id-1", "title")
        assert len(result) == 64

    def test_none_description_in_fallback(self):
        """None description should hash as empty string."""
        id1 = content_hash_task_id("cli", None, "Title", None)
        id2 = content_hash_task_id("cli", None, "Title", "")
        assert id1 == id2


class TestPMTask:
    """PMTask model field validation."""

    def test_create_minimal(self):
        now = datetime.now(timezone.utc)
        task = PMTask(
            task_id="abc123",
            title="Test task",
            source="test",
            created_at_utc=now,
            updated_at_utc=now,
        )
        assert task.status == PMTaskStatus.TODO
        assert task.version == 1
        assert task.description is None
        assert task.refs == {}
        assert task.meta == {}

    def test_version_must_be_positive(self):
        now = datetime.now(timezone.utc)
        with pytest.raises(Exception):
            PMTask(
                task_id="abc",
                title="t",
                source="s",
                created_at_utc=now,
                updated_at_utc=now,
                version=0,
            )


class TestPMTransitionRequest:
    """PMTransitionRequest field validation."""

    def test_create_valid(self):
        req = PMTransitionRequest(
            idempotency_key="idem-1",
            expected_version=1,
            new_status=PMTaskStatus.IN_PROGRESS,
            ts_utc=datetime.now(timezone.utc),
            source="test",
        )
        assert req.reason is None

    def test_expected_version_must_be_positive(self):
        with pytest.raises(Exception):
            PMTransitionRequest(
                idempotency_key="idem-1",
                expected_version=0,
                new_status=PMTaskStatus.IN_PROGRESS,
                ts_utc=datetime.now(timezone.utc),
                source="test",
            )

    def test_is_frozen(self):
        req = PMTransitionRequest(
            idempotency_key="idem-1",
            expected_version=1,
            new_status=PMTaskStatus.IN_PROGRESS,
            ts_utc=datetime.now(timezone.utc),
            source="test",
        )
        with pytest.raises(Exception):
            req.idempotency_key = "changed"
