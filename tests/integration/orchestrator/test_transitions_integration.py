import os
import shutil
import tempfile
import pytest
from click.testing import CliRunner

from src.dopemux.cli import cli


class TestTransitionsIntegration:
    @pytest.fixture(autouse=True)
    def setup_temp_xdg(self, monkeypatch):
        # Redirect HOME to avoid writing to real XDG share in tests
        self.temp_dir = tempfile.mkdtemp()
        monkeypatch.setenv("HOME", self.temp_dir)
        yield
        shutil.rmtree(self.temp_dir)

    def test_record_transition_cli_refusal(self):
        # Missing/invalid approval phrase should cause CLI non-zero exit
        result = CliRunner().invoke(
            cli,
            [
                "orchestrator",
                "transition",
                "apply",
                "--workflow-id",
                "wf-1",
                "--transition-name",
                "start",
                "--idempotency-key",
                "idem-key-1",
                "--proof-id",
                "p-123",
                "--approval-phrase",
                "invalid phrase",
            ],
        )
        assert result.exit_code != 0
        assert "refused" in result.output

    def test_record_transition_cli_success(self, monkeypatch):
        from unittest.mock import MagicMock
        mock_adapter = MagicMock()
        mock_adapter.transition.return_value = {
            "schema_version": "1",
            "workflow_id": "wf-1",
            "transition": "start",
            "idempotency_key": "idem-key-1",
            "actor": "operator",
            "canonical_writer": "task-orchestrator",
            "receipt": {
                "proof_id": "p-123",
                "operation": "workflow transition start",
                "status": "accepted",
            },
        }

        monkeypatch.setattr(
            "dopemux.pm.adapters.orchestrator.SyncTaskOrchestratorAdapter",
            lambda *args, **kwargs: mock_adapter,
        )

        phrase = "I AUTHORIZE workflow transition start ON dopemux-mvp USING task-orchestrator WITH PROOF p-123"
        result = CliRunner().invoke(
            cli,
            [
                "orchestrator",
                "transition",
                "apply",
                "--workflow-id",
                "wf-1",
                "--transition-name",
                "start",
                "--idempotency-key",
                "idem-key-1",
                "--proof-id",
                "p-123",
                "--approval-phrase",
                phrase,
                "--json-output",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "SUCCESS" in result.output
        assert "accepted" in result.output

    def test_record_transition_cli_envelope_failure(self, monkeypatch):
        from unittest.mock import MagicMock
        mock_adapter = MagicMock()
        # Invalid envelope (missing receipt)
        mock_adapter.transition.return_value = {
            "schema_version": "1",
            "workflow_id": "wf-1",
            "transition": "start",
            "idempotency_key": "idem-key-1",
            "actor": "operator",
            "canonical_writer": "task-orchestrator",
        }

        monkeypatch.setattr(
            "dopemux.pm.adapters.orchestrator.SyncTaskOrchestratorAdapter",
            lambda *args, **kwargs: mock_adapter,
        )

        phrase = "I AUTHORIZE workflow transition start ON dopemux-mvp USING task-orchestrator WITH PROOF p-123"
        result = CliRunner().invoke(
            cli,
            [
                "orchestrator",
                "transition",
                "apply",
                "--workflow-id",
                "wf-1",
                "--transition-name",
                "start",
                "--idempotency-key",
                "idem-key-1",
                "--proof-id",
                "p-123",
                "--approval-phrase",
                phrase,
                "--json-output",
            ],
        )
        assert result.exit_code != 0
        assert "failed" in result.output
        assert "validation failed" in result.output
