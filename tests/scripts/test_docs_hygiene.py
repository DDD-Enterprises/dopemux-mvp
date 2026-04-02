from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


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


@pytest.mark.parametrize(
    ("source", "rule_id", "target"),
    [
        (
            "docs/arbitration/schema-validation-rules.md",
            "map-arbitration",
            "docs/03-reference/governance/arbitration/schema-validation-rules.md",
        ),
        (
            "docs/flight_deck/panel-layout.md",
            "map-flight-deck",
            "docs/03-reference/governance/flight-deck/panel-layout.md",
        ),
        (
            "docs/governance/proof-bundle-schema.md",
            "map-governance",
            "docs/03-reference/governance/proof-bundle-schema.md",
        ),
        (
            "docs/policy/review-policy.md",
            "map-policy",
            "docs/03-reference/governance/policy/review-policy.md",
        ),
        (
            "docs/learning/onboarding-program.md",
            "map-learning",
            "docs/03-reference/governance/learning/onboarding-program.md",
        ),
        (
            "docs/pr_merge/checklist.md",
            "map-pr-merge",
            "docs/03-reference/pr-pipeline/merge/checklist.md",
        ),
        (
            "docs/pr_prep/branch-state-schema.md",
            "map-pr-prep",
            "docs/03-reference/pr-pipeline/prep/branch-state-schema.md",
        ),
        (
            "docs/pr_template/default.md",
            "map-pr-template",
            "docs/03-reference/pr-pipeline/templates/default.md",
        ),
        (
            "docs/systems/conport/custom-instructions/mem4sprint-schema-and-patterns.md",
            "map-systems",
            "docs/03-reference/systems/conport/custom-instructions/mem4sprint-schema-and-patterns.md",
        ),
        (
            "docs/planes/pm/_evidence/pm-inv-01-task-schema-analysis.md",
            "map-planes",
            "docs/03-reference/planes/pm/_evidence/pm-inv-01-task-schema-analysis.md",
        ),
        (
            "docs/skills/doc-auditor.md",
            "map-skills",
            "docs/03-reference/skills/doc-auditor.md",
        ),
        (
            "docs/releases/2026-03-31.md",
            "map-releases",
            "docs/03-reference/releases/2026-03-31.md",
        ),
        (
            "docs/rollout/agent-enablement-guide.md",
            "map-rollout",
            "docs/02-how-to/rollout/agent-enablement-guide.md",
        ),
        (
            "docs/ux/brand-tokens.md",
            "map-ux",
            "docs/03-reference/ux/brand-tokens.md",
        ),
        (
            "docs/mobile/setup.md",
            "map-mobile",
            "docs/02-how-to/mobile/setup.md",
        ),
        (
            "docs/packaging/app-bundles.md",
            "map-packaging",
            "docs/02-how-to/packaging/app-bundles.md",
        ),
        (
            "docs/integrations/dopetask/adapter-schema.md",
            "map-integrations",
            "docs/04-explanation/integrations/dopetask/adapter-schema.md",
        ),
    ],
)
def test_new_relocation_rules_map_scattered_roots(source: str, rule_id: str, target: str):
    record = MODULE.classify_path(
        rel_path=source,
        frontmatter_type=None,
        policy=_policy(),
    )
    assert record.status == "needs_relocation"
    assert record.rule_id == rule_id
    assert record.target_path == target


def test_explanation_history_maps_to_archive_history_but_quarantine_stays_immutable():
    policy = _policy()
    history_record = MODULE.classify_path(
        rel_path="docs/04-explanation/history/notes/session-01.md",
        frontmatter_type=None,
        policy=policy,
    )
    quarantine_record = MODULE.classify_path(
        rel_path="docs/04-explanation/history/sourceFiles/legacy-copy.md",
        frontmatter_type=None,
        policy=policy,
    )
    assert history_record.status == "needs_relocation"
    assert history_record.rule_id == "map-explanation-history"
    assert history_record.target_path == "docs/archive/history/notes/session-01.md"
    assert quarantine_record.status == "quarantine"
    assert quarantine_record.rule_id == "quarantine"
