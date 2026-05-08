from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_docs_filename_hygiene.py"
POLICY_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "docs_hygiene"
    / "docs_placement_policy.yaml"
)

SPEC = importlib.util.spec_from_file_location("check_docs_filename_hygiene", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _policy():
    return MODULE._load_policy(POLICY_PATH)


def test_slugify_stem_basic_cases():
    assert MODULE._slugify_stem("My File_Name") == "my-file-name"
    assert MODULE._slugify_stem("ADR-207-PHASE-1-IMPLEMENTATION-PLAN") == "adr-207-phase-1-implementation-plan"
    assert MODULE._slugify_stem("døpemux-brand-system") == "dopemux-brand-system"


def test_quarantine_and_keeper_are_exempt_from_rename():
    policy = _policy()
    quarantine = MODULE.classify_filename(
        rel_path="docs/04-explanation/history/sourceFiles/legacy.md",
        policy=policy,
    )
    keeper = MODULE.classify_filename(
        rel_path="docs/00-MASTER-INDEX.md",
        policy=policy,
    )
    assert quarantine.status == "quarantine"
    assert keeper.status == "exempt"


def test_needs_rename_detected_for_non_kebab_name():
    record = MODULE.classify_filename(
        rel_path="docs/03-reference/services/Server Registry.md",
        policy=_policy(),
    )
    assert record.status == "needs_rename"
    assert record.target_path == "docs/03-reference/services/server-registry.md"


def test_kebab_filename_is_ok():
    record = MODULE.classify_filename(
        rel_path="docs/03-reference/services/task-orchestrator.md",
        policy=_policy(),
    )
    assert record.status == "ok"
    assert record.target_path is None
