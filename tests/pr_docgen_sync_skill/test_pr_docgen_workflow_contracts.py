from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


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


def test_build_impact_requires_core_doc_types(tmp_path: Path):
    changed = [{"status": "M", "path": "src/dopemux/example.py"}]

    report = workflow.build_impact(changed, tmp_path)
    required = report["required_doc_types"]

    assert "reference" in required
    assert "how-to" in required
    assert "explanation" in required


def test_index_checklist_contains_canonical_set(tmp_path: Path):
    changed = [{"status": "M", "path": "src/dopemux/example.py"}]

    report = workflow.build_impact(changed, tmp_path)
    checklist_paths = {item["path"] for item in report["index_reconciliation_checklist"]}

    for canonical in workflow.CANONICAL_INDEXES:
        assert canonical in checklist_paths


def test_layout_audit_blocks_touched_misplacement(tmp_path: Path):
    bad = tmp_path / "docs" / "03-reference" / "wrong-tutorial.md"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text(
        """---
id: wrong-tutorial
title: Wrong Tutorial
type: tutorial
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-11'
last_review: '2026-03-11'
next_review: '2026-06-11'
prelude: test
---
# Wrong Tutorial
""",
        encoding="utf-8",
    )

    audit = workflow.audit_layout(
        tmp_path,
        [{"status": "A", "path": "docs/03-reference/wrong-tutorial.md"}],
    )

    assert audit["blocking"] is True
    assert len(audit["touched_or_new_misplacements"]) == 1


def test_extract_ticket_ids_from_ledger():
    text = """
### PM-TO-001
- `PM-TO-002`
- PM-TO-003
"""
    ids = workflow._extract_ticket_ids_from_ledger(text)
    assert ids == ["PM-TO-001", "PM-TO-002", "PM-TO-003"]


def test_resolve_instruction_targets_prefers_active_paths(tmp_path: Path):
    codex = tmp_path / "docs" / "03-reference" / "instructions" / "CODEX.md"
    codex.parent.mkdir(parents=True, exist_ok=True)
    codex.write_text("# CODEX\n", encoding="utf-8")

    targets = workflow._resolve_instruction_targets(tmp_path)

    assert "docs/03-reference/instructions/codex-3.md" in targets
