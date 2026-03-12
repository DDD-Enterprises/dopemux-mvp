from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _workflow_cli() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "templates"
        / "skills"
        / "pr-docgen-sync"
        / "scripts"
        / "pr_docgen_sync_workflow.py"
    )


def _init_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=tmp_path, check=True)


def test_e2e_json_output_contains_required_sections(tmp_path: Path):
    _init_repo(tmp_path)

    for rel in [
        "docs/docs_index.yaml",
        "docs/00-MASTER-INDEX.md",
        "docs/INDEX.md",
        "docs/01-tutorials/overview.md",
        "docs/02-how-to/overview.md",
        "docs/03-reference/overview.md",
        "docs/03-reference/documentation-catalog.md",
        "docs/04-explanation/overview.md",
    ]:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith(".yaml"):
            p.write_text("version: '1.0'\n", encoding="utf-8")
        else:
            p.write_text("# x\n", encoding="utf-8")

    ref_doc = tmp_path / "docs" / "03-reference" / "example.md"
    ref_doc.write_text(
        """---
id: ex
title: Ex
type: reference
owner: '@x'
author: '@x'
date: '2026-03-11'
last_review: '2026-03-11'
next_review: '2026-06-11'
prelude: ex
---
# Example
""",
        encoding="utf-8",
    )

    howto_doc = tmp_path / "docs" / "02-how-to" / "example.md"
    howto_doc.write_text(
        """---
id: how
title: How
type: how-to
owner: '@x'
author: '@x'
date: '2026-03-11'
last_review: '2026-03-11'
next_review: '2026-06-11'
prelude: how
---
# How
""",
        encoding="utf-8",
    )

    exp_doc = tmp_path / "docs" / "04-explanation" / "example.md"
    exp_doc.write_text(
        """---
id: exp
title: Exp
type: explanation
owner: '@x'
author: '@x'
date: '2026-03-11'
last_review: '2026-03-11'
next_review: '2026-06-11'
prelude: exp
---
# Exp
""",
        encoding="utf-8",
    )

    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True)

    (tmp_path / "docs" / "docs_index.yaml").write_text("version: '1.1'\n", encoding="utf-8")
    ref_doc.write_text(ref_doc.read_text(encoding="utf-8") + "\nupdate\n", encoding="utf-8")
    howto_doc.write_text(howto_doc.read_text(encoding="utf-8") + "\nupdate\n", encoding="utf-8")
    exp_doc.write_text(exp_doc.read_text(encoding="utf-8") + "\nupdate\n", encoding="utf-8")

    cmd = [
        sys.executable,
        str(_workflow_cli()),
        "--repo-root",
        str(tmp_path),
        "--baseline",
        "main...HEAD",
        "--format",
        "json",
        "--sync-tickets",
        "off",
        "--no-ledger-write",
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode in {0, 2}, proc.stderr

    payload = json.loads(proc.stdout)
    assert "impact_map" in payload
    assert "doc_type_coverage_matrix" in payload
    assert "index_reconciliation_checklist" in payload
    assert "layout_audit" in payload
    assert "layout_report" in payload
    assert "layout_followup_ledger" in payload
    assert "ticket_sync_results" in payload
