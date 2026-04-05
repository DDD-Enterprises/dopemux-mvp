from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_docs_hygiene.py"
POLICY_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "docs_hygiene"
    / "docs_placement_policy.yaml"
)

SPEC = importlib.util.spec_from_file_location("check_docs_hygiene", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _policy():
    return MODULE._load_policy(POLICY_PATH)


def test_canonical_path_is_ok():
    record = MODULE.classify_path(
        rel_path="docs/03-reference/services/task-orchestrator.md",
        frontmatter_type=None,
        policy=_policy(),
    )
    assert record.zone == "active"
    assert record.status == "ok"
    assert record.target_path is None


def test_quarantine_path_is_quarantine_zone():
    record = MODULE.classify_path(
        rel_path="docs/04-explanation/history/sourceFiles/legacy.md",
        frontmatter_type=None,
        policy=_policy(),
    )
    assert record.zone == "quarantine"
    assert record.status == "quarantine"
    assert record.target_path is None


def test_noncanonical_spec_path_maps_to_reference_spec():
    record = MODULE.classify_path(
        rel_path="docs/spec/dope-memory/v1/00-overview.md",
        frontmatter_type=None,
        policy=_policy(),
    )
    assert record.status == "needs_relocation"
    assert record.rule_id == "map-spec"
    assert record.target_path == "docs/03-reference/spec/dope-memory/v1/00-overview.md"


def test_nested_drift_archive_and_audit_reports_map_deterministically():
    policy = _policy()
    archive_record = MODULE.classify_path(
        rel_path="docs/04-explanation/archive/session-notes/2025-10/note.md",
        frontmatter_type=None,
        policy=policy,
    )
    audit_record = MODULE.classify_path(
        rel_path="docs/04-explanation/audit-reports/phase-1.md",
        frontmatter_type=None,
        policy=policy,
    )
    assert archive_record.status == "needs_relocation"
    assert archive_record.rule_id == "map-explanation-archive"
    assert archive_record.target_path == "docs/archive/session-notes/2025-10/note.md"
    assert audit_record.status == "needs_relocation"
    assert audit_record.rule_id == "map-explanation-audit-reports"
    assert audit_record.target_path == "docs/05-audit-reports/phase-1.md"


def test_root_allowlist_keeps_master_index_and_relocates_other_root_docs():
    policy = _policy()
    keeper = MODULE.classify_path(
        rel_path="docs/00-MASTER-INDEX.md",
        frontmatter_type="explanation",
        policy=policy,
    )
    moved = MODULE.classify_path(
        rel_path="docs/checklist-2.md",
        frontmatter_type="explanation",
        policy=policy,
    )
    assert keeper.status == "ok"
    assert keeper.rule_id == "root-keeper"
    assert moved.status == "needs_relocation"
    assert moved.rule_id == "root-override"
    assert moved.target_path == "docs/02-how-to/root-relocated/checklist-2.md"


def test_root_token_rule_applies_when_no_override():
    record = MODULE.classify_path(
        rel_path="docs/DEPLOYMENT_STATUS_NOTE.md",
        frontmatter_type=None,
        policy=_policy(),
    )
    assert record.status == "needs_relocation"
    assert record.rule_id == "root-token-audit-report"
    assert record.target_path == "docs/05-audit-reports/root-relocated/DEPLOYMENT_STATUS_NOTE.md"
