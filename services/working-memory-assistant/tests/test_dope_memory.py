"""
Tests for Dope-Memory Chronicle Store and Promotion Engine.

Covers:
- Redaction regex replacement
- Denylist path hashing
- Payload size cap
- Promotion eligibility
- Sorting determinism
- Cursor pagination
"""

import json
import pytest
from pathlib import Path
import tempfile

from chronicle.store import ChronicleStore
from promotion.redactor import Redactor
from promotion.promotion import PromotionEngine


class TestRedactor:
    """Tests for the Redaction engine."""

    def setup_method(self):
        self.redactor = Redactor()

    def test_aws_key_redaction(self):
        """AWS Access Key IDs are redacted."""
        payload = {"key": "AKIAIOSFODNN7EXAMPLE"}
        result = self.redactor.redact_payload(payload)
        assert "AKIA" not in result["key"]
        assert "[REDACTED:AWS_KEY_ID]" in result["key"]

    def test_jwt_redaction(self):
        """JWTs are redacted."""
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        # Use "data" not "token" - "token" is a sensitive key that gets dropped
        payload = {"data": jwt}
        result = self.redactor.redact_payload(payload)
        assert "eyJ" not in result["data"]
        assert "[REDACTED:JWT]" in result["data"]

    def test_bearer_token_redaction(self):
        """Bearer tokens are redacted."""
        payload = {"auth": "Bearer abc123def456"}
        result = self.redactor.redact_payload(payload)
        assert "abc123" not in result["auth"]
        assert "[REDACTED:BEARER]" in result["auth"]

    def test_private_key_redaction(self):
        """Private key blocks are redacted."""
        # Use "content" not "key" - and match the supported key type pattern
        payload = {
            "content": "-----BEGIN PRIVATE KEY-----\nMIIEpAIBAAKCAQEA\n-----END PRIVATE KEY-----"
        }
        result = self.redactor.redact_payload(payload)
        assert "BEGIN PRIVATE" not in result["content"]
        assert "[REDACTED:PRIVATE_KEY]" in result["content"]

    def test_github_token_redaction(self):
        """GitHub tokens are redacted."""
        # Use "value" not "token" - "token" is a sensitive key that gets dropped
        payload = {"value": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}
        result = self.redactor.redact_payload(payload)
        assert "ghp_" not in result["value"]
        assert "[REDACTED:GITHUB_TOKEN]" in result["value"]

    def test_openai_key_redaction(self):
        """OpenAI keys are redacted."""
        payload = {"api_key": "sk-proj-abcdefghijklmnopqrstuvwx"}
        # Note: api_key is a sensitive key name, so it gets dropped entirely
        result = self.redactor.redact_payload(payload)
        assert "api_key" not in result

    def test_sensitive_key_dropped(self):
        """Sensitive key names are dropped entirely."""
        payload = {
            "password": "secret123",
            "api_key": "sk-xxx",
            "normal_field": "keep this",
        }
        result = self.redactor.redact_payload(payload)
        assert "password" not in result
        assert "api_key" not in result
        assert result["normal_field"] == "keep this"

    def test_denylist_path_hashing(self):
        """Denied paths are hashed, not stored raw."""
        result = self.redactor.redact_file_path(".env")
        assert "path" not in result
        assert "path_hash" in result
        assert result["note"] == "denied_path"

        result = self.redactor.redact_file_path("secrets/api.txt")
        assert "path" not in result
        assert "path_hash" in result

        result = self.redactor.redact_file_path("~/.ssh/id_rsa")
        assert "path_hash" in result

    def test_allowed_path_preserved(self):
        """Normal paths are preserved."""
        result = self.redactor.redact_file_path("src/main.py")
        assert result["path"] == "src/main.py"
        assert "path_hash" not in result

    def test_payload_size_cap(self):
        """Payloads over 64KB are truncated."""
        large_payload = {"data": "x" * 100_000}
        result = self.redactor.redact_payload(large_payload)
        assert result.get("truncated") is True
        assert "original_size" in result

    def test_redaction_fail_closed(self):
        """Failed redaction returns safe minimal payload."""
        # Test with a difficult-to-serialize object would go here
        # For now, just verify the method exists
        payload = {"normal": "data"}
        result = self.redactor.redact_payload(payload)
        assert "normal" in result


class TestPromotionEngine:
    """Tests for the Promotion engine."""

    def setup_method(self):
        self.engine = PromotionEngine()

    def test_decision_logged_promotes(self):
        """decision.logged creates a curated entry."""
        data = {
            "decision_id": "d123",
            "title": "Use PostgreSQL for storage",
            "choice": "PostgreSQL",
            "rationale": "Best for our needs",
        }
        result = self.engine.promote("decision.logged", data)
        assert result is not None
        assert result.category == "planning"
        assert result.entry_type == "decision"
        assert result.importance_score == 7
        assert "PostgreSQL" in result.summary

    def test_task_failed_promotes(self):
        """task.failed creates a curated entry."""
        data = {
            "task_id": "t456",
            "title": "Deploy to production",
            "error": {"message": "Connection timeout"},
        }
        result = self.engine.promote("task.failed", data)
        assert result is not None
        assert result.category == "debugging"
        assert result.entry_type == "error"
        assert result.outcome == "failed"

    def test_file_modified_not_promoted(self):
        """file.modified does not create a curated entry."""
        data = {"path": "src/main.py", "action": "modified"}
        result = self.engine.promote("file.modified", data)
        assert result is None

    def test_manual_store_promotes(self):
        """manual.memory_store creates a curated entry."""
        data = {
            "category": "debugging",
            "entry_type": "blocker",
            "summary": "Database connection issues",
            "importance_score": 8,
        }
        result = self.engine.promote("manual.memory_store", data)
        assert result is not None
        assert result.category == "debugging"
        assert result.entry_type == "blocker"
        assert result.importance_score == 8

    def test_tag_extraction_order(self):
        """Tags preserve explicit order, then sorted inferred."""
        data = {
            "tags": ["zebra", "alpha"],
            "service": "api",
        }
        tags = self.engine._extract_tags(data)
        assert tags[:2] == ["zebra", "alpha"]
        assert "service:api" in tags

    def test_tag_cap_at_12(self):
        """Tags are capped at 12."""
        data = {"tags": [f"tag{i}" for i in range(20)]}
        tags = self.engine._extract_tags(data)
        assert len(tags) == 12


class TestChronicleStore:
    """Tests for the Chronicle store."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.store = ChronicleStore(self.db_path)
        self.store.initialize_schema()

    def teardown_method(self):
        self.store.close()

    def test_insert_and_search_entry(self):
        """Entries can be inserted and searched."""
        entry_id = self.store.insert_work_log_entry(
            workspace_id="ws1",
            instance_id="A",
            category="planning",
            entry_type="decision",
            summary="Decided to use auth tokens",
            importance_score=7,
            tags=["auth", "security"],
        )
        assert entry_id is not None

        results = self.store.search_work_log(
            workspace_id="ws1",
            instance_id="A",
            query="auth",
        )
        assert len(results) == 1
        assert results[0]["summary"] == "Decided to use auth tokens"

    def test_deterministic_ordering(self):
        """Results are ordered by importance DESC, ts DESC, id ASC."""
        # Insert entries with different importance scores
        self.store.insert_work_log_entry(
            workspace_id="ws1",
            instance_id="A",
            category="debugging",
            entry_type="error",
            summary="Low importance error",
            importance_score=3,
        )
        self.store.insert_work_log_entry(
            workspace_id="ws1",
            instance_id="A",
            category="planning",
            entry_type="decision",
            summary="High importance decision",
            importance_score=9,
        )
        self.store.insert_work_log_entry(
            workspace_id="ws1",
            instance_id="A",
            category="implementation",
            entry_type="milestone",
            summary="Medium importance milestone",
            importance_score=5,
        )

        results = self.store.search_work_log(
            workspace_id="ws1",
            instance_id="A",
        )

        # Verify ordering: highest importance first
        assert results[0]["importance_score"] == 9
        assert results[1]["importance_score"] == 5
        assert results[2]["importance_score"] == 3

    def test_cursor_pagination_no_overlap(self):
        """Cursor pagination returns no overlapping results."""
        # Insert 10 entries
        ids = []
        for i in range(10):
            entry_id = self.store.insert_work_log_entry(
                workspace_id="ws1",
                instance_id="A",
                category="implementation",
                entry_type="milestone",
                summary=f"Entry {i}",
                importance_score=5,
            )
            ids.append(entry_id)

        # Paginate through all
        all_results = []
        cursor = None
        while True:
            results = self.store.search_work_log(
                workspace_id="ws1",
                instance_id="A",
                limit=3,
                cursor=cursor,
            )
            if not results:
                break
            all_results.extend(results)

            # Build cursor from last result
            last = results[-1]
            cursor = (last["importance_score"], last["ts_utc"], last["id"])

            if len(results) < 3:
                break

        # Verify no duplicates
        result_ids = [r["id"] for r in all_results]
        assert len(result_ids) == len(set(result_ids)), "Duplicate entries found"
        assert len(result_ids) == 10

    def test_workspace_isolation(self):
        """Entries from different workspaces are isolated."""
        self.store.insert_work_log_entry(
            workspace_id="ws1",
            instance_id="A",
            category="planning",
            entry_type="decision",
            summary="WS1 decision",
        )
        self.store.insert_work_log_entry(
            workspace_id="ws2",
            instance_id="A",
            category="planning",
            entry_type="decision",
            summary="WS2 decision",
        )

        ws1_results = self.store.search_work_log(
            workspace_id="ws1",
            instance_id="A",
        )
        ws2_results = self.store.search_work_log(
            workspace_id="ws2",
            instance_id="A",
        )

        assert len(ws1_results) == 1
        assert ws1_results[0]["summary"] == "WS1 decision"
        assert len(ws2_results) == 1
        assert ws2_results[0]["summary"] == "WS2 decision"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
