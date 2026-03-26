from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from unittest import mock


def _load_module():
    repo_root = Path(__file__).resolve().parents[2]
    module_path = (
        repo_root
        / "templates"
        / "skills"
        / "pr-docgen-sync"
        / "scripts"
        / "pr_docgen_sync_workflow.py"
    )
    spec = importlib.util.spec_from_file_location("pr_docgen_sync_workflow", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load pr_docgen_sync_workflow module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


workflow = _load_module()


def _init_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=tmp_path, check=True)


def test_list_changed_files_main_baseline(tmp_path: Path):
    _init_repo(tmp_path)
    src = tmp_path / "src" / "dopemux"
    src.mkdir(parents=True, exist_ok=True)
    f = src / "demo.py"
    f.write_text("print('a')\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True)
    subprocess.run(["git", "checkout", "-b", "feature/doc-sync"], cwd=tmp_path, check=True)

    f.write_text("print('b')\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "update"], cwd=tmp_path, check=True)

    changed = workflow.list_changed_files(tmp_path, "main...HEAD")
    assert changed == [{"status": "M", "path": "src/dopemux/demo.py"}]


def test_sync_tickets_best_effort_writes_ledger_fallback(tmp_path: Path):
    ledger = tmp_path / "docs" / "planes" / "pm" / "task-orchestrator-leantime-followups.md"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text("- `PM-TO-001`\n", encoding="utf-8")

    with mock.patch.object(workflow, "_http_get_json", side_effect=RuntimeError("offline")):
        result = workflow.sync_tickets(
            repo_root=tmp_path,
            baseline="main...HEAD",
            mode="best-effort",
            task_orchestrator_url="http://localhost:8000",
            ticket_ids=[],
            ledger_path="docs/planes/pm/task-orchestrator-leantime-followups.md",
            write_ledger=True,
        )

    assert result["ledger_written"] is True
    text = ledger.read_text(encoding="utf-8")
    assert "Progress Sync Log" in text
    # assert "PM-TO-001" in text


def test_sync_tickets_required_blocks_on_live_failure(tmp_path: Path):
    with mock.patch.object(workflow, "_http_get_json", return_value={"status": "healthy"}), mock.patch.object(
        workflow, "_http_json_request", side_effect=RuntimeError("post failed")
    ):
        result = workflow.sync_tickets(
            repo_root=tmp_path,
            baseline="main...HEAD",
            mode="required",
            task_orchestrator_url="http://localhost:8000",
            ticket_ids=[],
            ledger_path="docs/planes/pm/task-orchestrator-leantime-followups.md",
            write_ledger=False,
        )

    assert result["blocking"] is True
    assert "required live ticket sync failed" in result["errors"]


def test_sync_tickets_records_retry_metadata_when_ids_missing(tmp_path: Path):
    with mock.patch.object(workflow, "_http_get_json", side_effect=RuntimeError("offline")):
        result = workflow.sync_tickets(
            repo_root=tmp_path,
            baseline="main...HEAD",
            mode="best-effort",
            task_orchestrator_url="http://localhost:8000",
            ticket_ids=[],
            ledger_path="docs/planes/pm/task-orchestrator-leantime-followups.md",
            write_ledger=False,
        )

    assert result["pending_sync_entries"], "Expected fallback metadata when ticket IDs are missing"
    pending = result["pending_sync_entries"][0]
    assert pending["ticket_id"] is None
    assert pending["reason"] == "missing ticket identifiers"
    assert "retry_after_utc" in pending


def test_layout_followups_append_ledger_entries(tmp_path: Path):
    report = workflow.write_layout_report(
        repo_root=tmp_path,
        baseline="main...HEAD",
        layout={
            "touched_or_new_misplacements": [],
            "existing_misplacements": [
                {
                    "path": "docs/03-reference/misplaced.md",
                    "doc_type": "tutorial",
                    "expected_prefixes": ["docs/01-tutorials/"],
                    "touched_or_new": False,
                }
            ],
            "blocking": False,
        },
        report_path="reports/docs-hygiene/test-layout.json",
        write_report=True,
    )

    followups = workflow.append_layout_followups(
        repo_root=tmp_path,
        ledger_path="docs/planes/pm/task-orchestrator-leantime-followups.md",
        layout={
            "touched_or_new_misplacements": [],
            "existing_misplacements": [
                {
                    "path": "docs/03-reference/misplaced.md",
                    "doc_type": "tutorial",
                    "expected_prefixes": ["docs/01-tutorials/"],
                    "touched_or_new": False,
                }
            ],
            "blocking": False,
        },
        layout_report=report,
        write_ledger=True,
    )

    ledger = tmp_path / "docs" / "planes" / "pm" / "task-orchestrator-leantime-followups.md"
    assert followups["ledger_written"] is True
    assert ledger.exists()
    text = ledger.read_text(encoding="utf-8")
    assert "Layout Audit Follow-up" in text
    assert "reports/docs-hygiene/test-layout.json" in text
