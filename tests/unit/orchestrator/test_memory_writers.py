import pytest
from unittest.mock import MagicMock

from dopemux.orchestrator.memory_writers import (
    write_decision,
    write_progress,
    verify_approval,
)


class TestMemoryWriters:
    def test_verify_approval(self):
        proof_id = "proof-123"
        # 1. Exact match with underscore
        phrase_und = "I AUTHORIZE record_decision ON dopemux-mvp USING ConPort WITH PROOF proof-123"
        assert verify_approval(
            operation="record_decision",
            resource="dopemux-mvp",
            writer="ConPort",
            proof_id=proof_id,
            approval_phrase=phrase_und,
        ) is True

        # 2. Exact match with spaces
        phrase_spc = "I AUTHORIZE record decision ON dopemux-mvp USING ConPort WITH PROOF proof-123"
        assert verify_approval(
            operation="record_decision",
            resource="dopemux-mvp",
            writer="ConPort",
            proof_id=proof_id,
            approval_phrase=phrase_spc,
        ) is True

        # 3. Invalid phrase
        assert verify_approval(
            operation="record_decision",
            resource="dopemux-mvp",
            writer="ConPort",
            proof_id=proof_id,
            approval_phrase="I AUTHORIZE something else",
        ) is False

    def test_write_decision_refused_on_invalid_approval(self):
        mock_conport = MagicMock()
        
        res = write_decision(
            task_id="TP-009",
            content="Decision content",
            approval_phrase="invalid phrase",
            proof_id="p-123",
            source_packet="TP-DMX-ORCH-009-LIVE",
            idempotency_key="idem-abc",
            conport_client=mock_conport,
        )
        
        assert res.status == "REFUSED"
        assert "Invalid" in res.upstream_response["error"]
        mock_conport.record_progress.assert_not_called()

    def test_write_decision_success(self):
        mock_conport = MagicMock()
        
        phrase = "I AUTHORIZE record_decision ON dopemux-mvp USING ConPort WITH PROOF p-123"
        res = write_decision(
            task_id="TP-009",
            content="Decision content",
            approval_phrase=phrase,
            proof_id="p-123",
            source_packet="TP-DMX-ORCH-009-LIVE",
            idempotency_key="idem-abc",
            conport_client=mock_conport,
        )
        
        assert res.status == "SUCCESS"
        assert res.canonical_writer == "ConPort"
        assert res.mirror_writer is None
        assert res.mirror_status == "NONE"
        mock_conport.record_progress.assert_called_once_with(
            "TP-009",
            "Decision content",
            True,
            idempotency_key="idem-abc",
        )

    def test_write_progress_refused_on_invalid_approval(self):
        mock_conport = MagicMock()
        mock_memory = MagicMock()
        
        res = write_progress(
            task_id="TP-009",
            content="Progress content",
            approval_phrase="invalid phrase",
            proof_id="p-123",
            source_packet="TP-DMX-ORCH-009-LIVE",
            idempotency_key="idem-abc",
            conport_client=mock_conport,
            memory_client=mock_memory,
        )
        
        assert res.status == "REFUSED"
        mock_conport.record_progress.assert_not_called()
        mock_memory.append_chronicle.assert_not_called()

    def test_write_progress_success(self):
        mock_conport = MagicMock()
        mock_memory = MagicMock()
        mock_memory.append_chronicle.return_value = {"entry_id": "mem-789"}
        
        phrase = "I AUTHORIZE record_progress ON dopemux-mvp USING ConPort WITH PROOF p-123"
        res = write_progress(
            task_id="TP-009",
            content="Progress content",
            approval_phrase=phrase,
            proof_id="p-123",
            source_packet="TP-DMX-ORCH-009-LIVE",
            idempotency_key="idem-abc",
            conport_client=mock_conport,
            memory_client=mock_memory,
        )
        
        assert res.status == "SUCCESS"
        assert res.canonical_writer == "ConPort"
        assert res.mirror_writer == "dope-memory"
        assert res.mirror_status == "SUCCESS"
        mock_conport.record_progress.assert_called_once_with(
            "TP-009",
            "Progress content",
            False,
            idempotency_key="idem-abc",
        )
        mock_memory.append_chronicle.assert_called_once_with(
            "TP-009",
            "Progress content",
            False,
            idempotency_key="idem-abc",
        )

    def test_write_progress_partial_mirror_failure(self):
        mock_conport = MagicMock()
        mock_memory = MagicMock()
        mock_memory.append_chronicle.side_effect = Exception("Mirror write timed out")
        
        phrase = "I AUTHORIZE record_progress ON dopemux-mvp USING ConPort WITH PROOF p-123"
        res = write_progress(
            task_id="TP-009",
            content="Progress content",
            approval_phrase=phrase,
            proof_id="p-123",
            source_packet="TP-DMX-ORCH-009-LIVE",
            idempotency_key="idem-abc",
            conport_client=mock_conport,
            memory_client=mock_memory,
        )
        
        # ConPort succeeds, but mirror fails -> overall status is PARTIAL, mirror_status is FAILED
        assert res.status == "PARTIAL"
        assert res.canonical_writer == "ConPort"
        assert res.mirror_writer == "dope-memory"
        assert res.mirror_status == "FAILED"
        assert "Mirror write timed out" in res.upstream_response["mirror_error"]
        mock_conport.record_progress.assert_called_once()
