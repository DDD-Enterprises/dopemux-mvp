import sys
from unittest.mock import MagicMock
import pytest
from click.testing import CliRunner

from src.dopemux.cli import cli
from dopemux.orchestrator.memory_writers import write_decision, write_progress


class TestMemoryWritersIntegration:
    def test_record_decision_cli_refusal(self):
        # Missing or invalid approval phrase should cause CLI non-zero exit
        result = CliRunner().invoke(
            cli,
            [
                "orchestrator",
                "memory",
                "record_decision",
                "--task-id",
                "TP-009",
                "--content",
                "Hello decision",
                "--approval-phrase",
                "invalid phrase",
                "--proof-id",
                "p-123",
                "--idempotency-key",
                "idem-key-1",
            ],
        )
        assert result.exit_code != 0
        assert "refused" in result.output

    def test_record_decision_cli_success(self, monkeypatch):
        mock_conport = MagicMock()
        mock_conport.record_progress.return_value = MagicMock(
            success=True, canonical_id="TP-009", reconciliation_state="SYNCED"
        )

        monkeypatch.setattr(
            "dopemux.tools.conport_client.ConPortClient",
            lambda *args, **kwargs: mock_conport,
        )

        phrase = "I AUTHORIZE record_decision ON dopemux-mvp USING ConPort WITH PROOF p-123"
        result = CliRunner().invoke(
            cli,
            [
                "orchestrator",
                "memory",
                "record_decision",
                "--task-id",
                "TP-009",
                "--content",
                "Hello decision",
                "--approval-phrase",
                phrase,
                "--proof-id",
                "p-123",
                "--idempotency-key",
                "idem-key-1",
                "--json-output",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "SUCCESS" in result.output
        assert "ConPort" in result.output

    def test_record_progress_cli_partial_failure(self, monkeypatch):
        mock_conport = MagicMock()
        mock_conport.record_progress.return_value = MagicMock(
            success=True, canonical_id="TP-009", reconciliation_state="SYNCED"
        )

        # Mock non-existent memory_client module in sys.modules
        mock_memory_module = MagicMock()
        sys.modules["dopemux.tools.memory_client"] = mock_memory_module
        
        mock_memory = MagicMock()
        mock_memory.append_chronicle.side_effect = Exception("Mirror write error")
        mock_memory_module.MemoryClient.return_value = mock_memory

        monkeypatch.setattr(
            "dopemux.tools.conport_client.ConPortClient",
            lambda *args, **kwargs: mock_conport,
        )

        phrase = "I AUTHORIZE record_progress ON dopemux-mvp USING ConPort WITH PROOF p-123"
        result = CliRunner().invoke(
            cli,
            [
                "orchestrator",
                "memory",
                "record_progress",
                "--task-id",
                "TP-009",
                "--content",
                "Hello progress",
                "--approval-phrase",
                phrase,
                "--proof-id",
                "p-123",
                "--idempotency-key",
                "idem-key-1",
                "--json-output",
            ],
        )
        # Clean up sys.modules after test
        sys.modules.pop("dopemux.tools.memory_client", None)

        assert result.exit_code == 0, result.output
        assert "PARTIAL" in result.output
        assert "FAILED" in result.output  # Mirror status failed
