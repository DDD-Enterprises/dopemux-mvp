import json
import shutil
import tempfile
from pathlib import Path
import pytest

from dopemux.orchestrator.ui.data_sources import (
    get_today_data,
    get_authority_data,
    get_packets_data,
    get_proof_data,
    get_risks_data,
    get_pr_queue_data,
    get_context_data,
    get_do_not_touch_data,
)


class TestUIDataSources:
    @pytest.fixture(autouse=True)
    def setup_temp_dirs(self):
        self.temp_dir = tempfile.mkdtemp()
        self.packets_dir = Path(self.temp_dir) / "task-packets"
        self.proof_dir = Path(self.temp_dir) / "proof"
        self.packets_dir.mkdir(parents=True, exist_ok=True)
        self.proof_dir.mkdir(parents=True, exist_ok=True)
        
        yield
        
        shutil.rmtree(self.temp_dir)

    def test_get_today_data(self):
        data = get_today_data()
        assert data["kind"] == "dashboard_snapshot"
        assert len(data["panels"]) == 8

    def test_get_authority_data(self):
        data = get_authority_data()
        assert "authority" in data
        assert "capabilities" in data
        assert len(data["capabilities"]) > 0

    def test_get_packets_data_empty(self):
        data = get_packets_data(base_dir=self.packets_dir)
        assert data == []

    def test_get_packets_data_with_file(self):
        # Create a mock packet
        packet_file = self.packets_dir / "TP-MOCK-001.json"
        packet_payload = {
            "id": "TP-MOCK-001",
            "project": "dopemux-mvp",
            "target": "Mock target",
            "invariants": [],
            "depends_on": [],
            "repo_binding": {
                "project_id": "DDD-Enterprises/dopemux-mvp",
                "repo_marker": ".dopetaskroot",
                "require_identity_match": False
            },
            "series": {
                "id": "MOCK-SERIES",
                "base_branch": "main",
                "parent_tp_id": "TP-PARENT",
                "final_packet": False
            },
            "execution": {
                "agent": "codex",
                "branch": "mock-branch",
                "base_branch": "main"
            },
            "commit": {
                "message": "mock commit",
                "allowlist": ["src/dopemux/tui/app.py"],
                "verify": []
            },
            "pr": {
                "title": "mock pr",
                "body": "mock body",
                "base": "main"
            },
            "steps": [
                {
                    "id": "step-1",
                    "task": "Mock task",
                    "validation": ["Verify mock"]
                }
            ]
        }
        packet_file.write_text(json.dumps(packet_payload))
        
        # Validate
        data = get_packets_data(base_dir=self.packets_dir)
        assert len(data) == 1
        assert data[0]["name"] == "TP-MOCK-001.json"
        assert data[0]["valid"] is True
        assert data[0]["status"] == "PASS"

    def test_get_proof_data_empty(self):
        data = get_proof_data(base_dir=self.proof_dir)
        assert data == []

    def test_get_proof_data_with_file(self):
        # Create a mock proof
        sub_dir = self.proof_dir / "TP-MOCK-001"
        sub_dir.mkdir(parents=True, exist_ok=True)
        proof_file = sub_dir / "PROOF.json"
        proof_payload = {
            "bundle_id": "TP-MOCK-PROOF",
            "run_id": "mock-run",
            "skill": "codex",
            "status": "READY_FOR_REVIEW",
            "validation_state": "PASSED",
            "created_at": "2026-05-28T12:00:00Z",
            "manifest": {
                "bundle_id": "TP-MOCK-PROOF",
                "packet_id": "TP-MOCK",
                "generated_artifacts": ["src/dopemux/tui/app.py"]
            },
            "authoritative_artifacts": ["task-packets/generated/TP-DMX-ORCH-015-TUI.json"],
            "supporting_artifacts": ["proof/dmx-orch-integration/TP-DMX-ORCH-015-TUI/PROOF.json"],
            "chain_of_custody": {
                "documented": True,
                "source_version": "TP-MOCK",
                "created_at": "2026-05-28T12:00:00Z",
                "parent_bundle_ids": []
            },
            "warnings": [],
            "blockers": []
        }
        proof_file.write_text(json.dumps(proof_payload))
        
        data = get_proof_data(base_dir=self.proof_dir)
        assert len(data) == 1
        assert data[0]["name"] == "PROOF.json"
        assert data[0]["valid"] is True

    def test_get_risks_data(self):
        data = get_risks_data()
        assert isinstance(data, list)
        for item in data:
            assert item["tier"] in {"TX", "TU", "T6"}

    def test_get_pr_queue_data(self, monkeypatch):
        monkeypatch.setattr(
            "dopemux.orchestrator.ui.data_sources.build_pr_queue",
            lambda *args, **kwargs: {"kind": "pr_queue", "entries": []}
        )
        data = get_pr_queue_data()
        assert data["kind"] == "pr_queue"

    def test_get_context_data(self, monkeypatch):
        monkeypatch.setattr(
            "dopemux.orchestrator.ui.data_sources.context_status",
            lambda *args, **kwargs: {"dope-context": {"fresh": True}, "ConPort": {"fresh": True}}
        )
        data = get_context_data()
        assert "dope-context" in data
        assert "ConPort" in data

    def test_get_do_not_touch_data(self):
        data = get_do_not_touch_data()
        assert "refusals" in data
