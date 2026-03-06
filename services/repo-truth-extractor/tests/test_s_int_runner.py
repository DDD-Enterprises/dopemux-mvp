from __future__ import annotations

import importlib
import json
from pathlib import Path
import subprocess
import sys


def _load_run_s_int():
    root = Path(__file__).resolve().parents[3]
    service_root = root / "services" / "repo-truth-extractor"
    if str(service_root) not in sys.path:
        sys.path.insert(0, str(service_root))
    return importlib.import_module("s_int.run_s_int")


def _fixture_repo(tmp_path: Path) -> Path:
    (tmp_path / "services" / "alpha").mkdir(parents=True, exist_ok=True)
    (tmp_path / "services" / "alpha" / "main.py").write_text("# webhook\n", encoding="utf-8")
    (tmp_path / "docker" / "mcp-servers-source" / "demo").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docker" / "mcp-servers-source" / "demo" / "server.py").write_text("mcp = True\n", encoding="utf-8")
    return tmp_path


def _fake_payload(step_id: str):
    if step_id == "S16":
        return {"status": "OK", "findings": [{"server_id": "mcp.demo", "status": "OK", "notes": []}], "missing_evidence": []}
    if step_id == "S17":
        return {"status": "OK", "hooks": [{"path": "services/alpha/main.py", "term": "webhook", "line": 1}], "missing_evidence": []}
    if step_id == "S18":
        return {"status": "OK", "contracts": [{"contract_id": "TRINITY", "coverage": "partial"}], "missing_evidence": []}
    if step_id == "S19":
        return {"status": "OK", "categories": [{"category": "operator", "grade": "B", "notes": []}], "missing_evidence": []}
    return {"status": "OK", "milestones": [{"milestone_id": "M1", "title": "Ship S_INT"}], "risks": [], "missing_evidence": []}


def test_run_s_int_writes_outputs(tmp_path: Path) -> None:
    module = _load_run_s_int()
    repo_root = _fixture_repo(tmp_path)
    out_root = tmp_path / "proof" / "s_int"

    def fake_executor(step, rendered_prompt, schema, prior_outputs):  # type: ignore[no-untyped-def]
        assert "S_INT_INPUT" in rendered_prompt
        return {"payload": _fake_payload(step.step_id)}

    summary = module.run_s_int(repo_root, "sint_run", dry_run=False, out_root=out_root, prompt_executor=fake_executor)
    assert summary["status"] == "OK"
    run_root = out_root / "sint_run"
    assert (run_root / "S_INT_MACHINE_SUMMARY.json").exists()
    assert (run_root / "S_INT_SUMMARY.md").exists()
    assert (run_root / "S_INT_CHECKLIST.md").exists()
    assert (run_root / "S_INT_FAIL_CLOSED.md").exists()


def test_run_s_int_dry_run_via_v4_cli(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    script = root / "services" / "repo-truth-extractor" / "run_extraction_v4.py"
    result = subprocess.run(
        [sys.executable, str(script), "--phase", "S_INT", "--dry-run", "--run-id", "sint_v4_dry"],
        cwd=str(tmp_path),
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    assert payload["status"] == "DRY_RUN"
    assert (tmp_path / "proof" / "s_int" / "sint_v4_dry" / "S_INT_MACHINE_SUMMARY.json").exists()
