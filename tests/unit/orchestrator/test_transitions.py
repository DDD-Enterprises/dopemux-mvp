import os
import shutil
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from dopemux.orchestrator.transitions import apply_transition, TransitionReceipt
from dopemux.orchestrator.idempotency import IdempotencyStore, IdempotencyState


class TestTransitions:
    @pytest.fixture(autouse=True)
    def setup_temp_xdg(self, monkeypatch):
        # Redirect HOME to avoid writing to real XDG share in tests
        self.temp_dir = tempfile.mkdtemp()
        monkeypatch.setenv("HOME", self.temp_dir)
        yield
        shutil.rmtree(self.temp_dir)

    def test_apply_transition_refused_on_invalid_phrase(self):
        res = apply_transition(
            workflow_id="wf-1",
            transition_name="start",
            idempotency_key="idem-1",
            proof_id="p-1",
            approval_phrase="invalid phrase",
        )
        assert res.success is False
        assert res.status == "REFUSED"
        assert "Invalid" in res.error

    def test_apply_transition_success(self, monkeypatch):
        # Mock SyncTaskOrchestratorAdapter
        mock_adapter = MagicMock()
        mock_adapter.transition.return_value = {
            "schema_version": "1",
            "workflow_id": "wf-1",
            "transition": "start",
            "idempotency_key": "idem-1",
            "actor": "operator",
            "canonical_writer": "task-orchestrator",
            "receipt": {
                "proof_id": "p-1",
                "operation": "workflow transition start",
                "status": "accepted",
            },
        }
        monkeypatch.setattr(
            "dopemux.pm.adapters.orchestrator.SyncTaskOrchestratorAdapter",
            lambda *args, **kwargs: mock_adapter,
        )

        phrase = "I AUTHORIZE workflow transition start ON dopemux-mvp USING task-orchestrator WITH PROOF p-1"
        res = apply_transition(
            workflow_id="wf-1",
            transition_name="start",
            idempotency_key="idem-1",
            proof_id="p-1",
            approval_phrase=phrase,
        )

        assert res.success is True
        assert res.status == "SUCCESS"
        assert res.response_envelope["receipt"]["status"] == "accepted"

    def test_apply_transition_envelope_validation_failure(self, monkeypatch):
        # Return invalid envelope (missing receipt)
        mock_adapter = MagicMock()
        mock_adapter.transition.return_value = {
            "schema_version": "1",
            "workflow_id": "wf-1",
            "transition": "start",
            "idempotency_key": "idem-1",
            "actor": "operator",
            "canonical_writer": "task-orchestrator",
        }
        monkeypatch.setattr(
            "dopemux.pm.adapters.orchestrator.SyncTaskOrchestratorAdapter",
            lambda *args, **kwargs: mock_adapter,
        )

        phrase = "I AUTHORIZE workflow transition start ON dopemux-mvp USING task-orchestrator WITH PROOF p-1"
        res = apply_transition(
            workflow_id="wf-1",
            transition_name="start",
            idempotency_key="idem-1",
            proof_id="p-1",
            approval_phrase=phrase,
        )

        assert res.success is False
        assert res.status == "FAILED"
        assert "validation failed" in res.error

    def test_apply_transition_idempotency_replay(self, monkeypatch):
        # 1. First call successful
        mock_adapter = MagicMock()
        mock_adapter.transition.return_value = {
            "schema_version": "1",
            "workflow_id": "wf-1",
            "transition": "start",
            "idempotency_key": "idem-1",
            "actor": "operator",
            "canonical_writer": "task-orchestrator",
            "receipt": {
                "proof_id": "p-1",
                "operation": "workflow transition start",
                "status": "accepted",
            },
        }
        monkeypatch.setattr(
            "dopemux.pm.adapters.orchestrator.SyncTaskOrchestratorAdapter",
            lambda *args, **kwargs: mock_adapter,
        )

        phrase = "I AUTHORIZE workflow transition start ON dopemux-mvp USING task-orchestrator WITH PROOF p-1"
        res1 = apply_transition(
            workflow_id="wf-1",
            transition_name="start",
            idempotency_key="idem-1",
            proof_id="p-1",
            approval_phrase=phrase,
        )
        assert res1.success is True

        # 2. Second call with same idempotency_key triggers replay without hitting adapter again
        mock_adapter.transition.reset_mock()
        res2 = apply_transition(
            workflow_id="wf-1",
            transition_name="start",
            idempotency_key="idem-1",
            proof_id="p-1",
            approval_phrase=phrase,
        )
        assert res2.success is True
        assert res2.status == "SUCCESS"
        mock_adapter.transition.assert_not_called()

    def test_preview_purity_ast(self):
        import ast
        from pathlib import Path
        
        module_path = Path("src/dopemux/orchestrator/operator_workflows.py")
        tree = ast.parse(module_path.read_text())
        
        # Verify that transitions.py or apply_transition is never imported or called in operator_workflows.py
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert "transitions" not in node.module
                for alias in node.names:
                    assert "apply_transition" not in alias.name
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "transitions" not in alias.name

