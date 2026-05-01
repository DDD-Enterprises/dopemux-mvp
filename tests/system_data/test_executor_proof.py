import json

from dopemux.system_data.executor import execute_plan
from dopemux.system_data.models import PlanItem, ToolReport, stable_json
from dopemux.system_data.proof import write_proof


def _action(path: str) -> PlanItem:
    return PlanItem(
        action_id="A0001",
        target_finding_id="F1",
        path=path,
        action_type="clear_safe_path",
        dry_run_supported=True,
        requires_confirmation=False,
        destructive_level="low",
        expected_reclaim_bytes=10,
        preconditions=(),
        rollback_mode="none",
        blocked_reason=None,
        execution_order=1,
        rationale="test",
    )


def test_dry_run_does_not_mutate(tmp_path):
    target = tmp_path / "cache"
    target.mkdir()
    (target / "file").write_text("x", encoding="utf-8")

    records = execute_plan((_action(str(target)),), dry_run=True, proof_dir=tmp_path / "proof")

    assert target.exists()
    assert not (tmp_path / "proof").exists()
    assert records[0].status == "planned"
    assert records[0].dry_run is True
    assert records[0].manifest_path is None


def test_execute_safe_clear_writes_manifest(tmp_path):
    target = tmp_path / "cache"
    target.mkdir()
    (target / "file").write_text("x", encoding="utf-8")

    records = execute_plan((_action(str(target)),), dry_run=False, yes=True, proof_dir=tmp_path / "proof")

    assert not target.exists()
    assert records[0].status == "executed"
    assert records[0].manifest_path


def test_stable_json_sorts_keys():
    assert stable_json({"b": 1, "a": 2}).splitlines()[1].strip().startswith('"a"')


def test_write_proof_json_shape(tmp_path):
    proof_path = tmp_path / "proof.json"

    bundle = write_proof(
        proof_path,
        repo_root=tmp_path,
        tool_report=ToolReport(required=(), statuses=()),
        implementation={"files_added": []},
        tests={"commands": []},
        runtime_validation={"sample": {}},
        docs={"files": []},
        acceptance={"criteria": []},
        unresolved=[],
    )

    data = json.loads(proof_path.read_text(encoding="utf-8"))
    assert data["tp_id"] == "TP-OPS-MAC-SCRUBBER-001"
    assert bundle.schema_version == "system-data-proof.v1"
