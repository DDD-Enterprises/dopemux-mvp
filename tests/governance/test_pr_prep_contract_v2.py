"""Governance test: forbidden legacy pr-prep-specialist semantics must be
absent from active canonical and compatibility contract surfaces.

Covers TP-DMX-PR-PREP-SPECIALIST-V2-001-R1: the canonical PR-pipeline
contract tree must use the V2 (L0-L3, S0-S8, schema_version 2.0.0) model,
and compatibility surfaces must not carry independent behavioral content
that could reintroduce the legacy mandatory-7-step / fixed-seven-artifact /
LOW-MEDIUM-HIGH / GO_DIRECT / PRPS-produced-MERGE_READY model.

Also covers the TP-DMX-PR-PREP-SPECIALIST-V2-001-R2 closure: three residual
canonical/compatibility file pairs (`branch-state-schema.md`,
`consensus-gate-rules.md`, `handoff-contract.md`) still carried an active
`risk_hint: LOW|MEDIUM|HIGH` schema and dangling links to the deleted
`contract-v2.md` after R1; R2 converts all six into pointer stubs.
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

CANONICAL_DIR = ROOT / "docs/03-reference/pr-pipeline/prep"
CANONICAL_MERGE_DIR = ROOT / "docs/03-reference/pr-pipeline/merge"
COMPAT_DIR = ROOT / "docs/pr_prep"
COMPAT_MERGE_DIR = ROOT / "docs/pr_merge"

# Files this packet (TP-DMX-PR-PREP-SPECIALIST-V2-001, R1) authorized touching.
IN_SCOPE_CANONICAL = [
    "skill-model.md",
    "operator-contract.md",
    "workflow-sequence.md",
    "deterministic-gate-rules.md",
    "go-no-go-criteria.md",
    "handoff-to-prms-contract.md",
    "pr-creation-policy.md",
    "high-risk-handoff-rules.md",
]
IN_SCOPE_COMPAT = IN_SCOPE_CANONICAL

# Residual files added to the allowlist by R2.
R2_RESIDUAL_FILES = [
    "branch-state-schema.md",
    "consensus-gate-rules.md",
    "handoff-contract.md",
]

ALL_IN_SCOPE_CANONICAL = IN_SCOPE_CANONICAL + R2_RESIDUAL_FILES
ALL_IN_SCOPE_COMPAT = IN_SCOPE_COMPAT + R2_RESIDUAL_FILES

# The legacy risk_hint enum as a JSON type annotation (not prose describing
# what was retired).
LEGACY_RISK_HINT_ENUM_SNIPPET = '"enum": ["LOW", "MEDIUM", "HIGH", "UNKNOWN"]'

# The literal fixed seven-artifact JSON list from the legacy handoff schema.
# Its reappearance anywhere in an active contract means the old schema crept
# back in.
LEGACY_FIXED_ARTIFACT_SNIPPET = '"BRANCH_STATE.json",\n    "BRANCH_AUDIT_REPORT.json"'

# The legacy governing_posture enum as a JSON type annotation (not prose
# describing what was retired).
LEGACY_POSTURE_ENUM_SNIPPET = '"governing_posture": "<GO_DRAFT_FIRST|GO_DIRECT|AWAIT_REVIEW>"'

LEGACY_NEXT_STEP_ENUM_SNIPPET = '"recommended_next_step": "<AWAIT_REVIEW|MERGE_READY|BLOCKED>"'


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("filename", IN_SCOPE_CANONICAL)
def test_should_not_contain_legacy_fixed_artifact_list_when_scanning_canonical_prep_tree(
    filename: str,
) -> None:
    text = _read(CANONICAL_DIR / filename)
    assert LEGACY_FIXED_ARTIFACT_SNIPPET not in text
    assert LEGACY_POSTURE_ENUM_SNIPPET not in text
    assert LEGACY_NEXT_STEP_ENUM_SNIPPET not in text


@pytest.mark.parametrize("filename", IN_SCOPE_COMPAT)
def test_should_not_contain_legacy_fixed_artifact_list_when_scanning_compat_prep_tree(
    filename: str,
) -> None:
    text = _read(COMPAT_DIR / filename)
    assert LEGACY_FIXED_ARTIFACT_SNIPPET not in text
    assert LEGACY_POSTURE_ENUM_SNIPPET not in text
    assert LEGACY_NEXT_STEP_ENUM_SNIPPET not in text


def test_should_declare_v2_handoff_schema_version_when_scanning_canonical_operator_contract() -> None:
    text = _read(CANONICAL_DIR / "operator-contract.md")
    assert '"schema_version": "2.0.0"' in text
    assert '"risk_lane": "L0|L1|L2|L3"' in text


def test_should_declare_v2_handoff_schema_version_when_scanning_canonical_merge_receiver() -> None:
    text = _read(CANONICAL_MERGE_DIR / "handoff-from-prps-contract.md")
    assert '"schema_version": "2.0.0"' in text
    assert '"risk_lane": "L0|L1|L2|L3"' in text


def test_should_declare_l0_to_l3_risk_lanes_when_scanning_canonical_operator_contract() -> None:
    text = _read(CANONICAL_DIR / "operator-contract.md")
    for lane in ("L0_DETERMINISTIC", "L1_BOUNDED", "L2_MATERIAL", "L3_RED"):
        assert lane in text


def test_should_reference_canonical_tree_when_scanning_compat_stubs() -> None:
    for filename in IN_SCOPE_COMPAT:
        text = _read(COMPAT_DIR / filename)
        assert "TP-DMX-PR-PREP-SPECIALIST-V2-001-R1" in text
        assert "03-reference/pr-pipeline/prep" in text


def test_should_not_reference_unauthorized_contract_v2_file_when_scanning_compat_tree() -> None:
    for filename in IN_SCOPE_COMPAT:
        text = _read(COMPAT_DIR / filename)
        assert "contract-v2.md" not in text
    assert not (COMPAT_DIR / "contract-v2.md").exists()


def test_should_mark_compat_merge_receiver_as_pointer_when_scanning_compat_merge_tree() -> None:
    text = _read(COMPAT_MERGE_DIR / "handoff-from-prps-contract.md")
    assert "compatibility surface only" in text
    assert "03-reference/pr-pipeline/merge" in text


@pytest.mark.parametrize("filename", R2_RESIDUAL_FILES)
def test_should_not_encode_legacy_risk_hint_enum_when_scanning_r2_residual_canonical_files(
    filename: str,
) -> None:
    text = _read(CANONICAL_DIR / filename)
    assert LEGACY_RISK_HINT_ENUM_SNIPPET not in text
    assert "contract-v2.md" not in text


@pytest.mark.parametrize("filename", R2_RESIDUAL_FILES)
def test_should_not_encode_legacy_risk_hint_enum_when_scanning_r2_residual_compat_files(
    filename: str,
) -> None:
    text = _read(COMPAT_DIR / filename)
    assert LEGACY_RISK_HINT_ENUM_SNIPPET not in text
    assert "contract-v2.md" not in text


@pytest.mark.parametrize("filename", R2_RESIDUAL_FILES)
def test_should_reference_canonical_tree_when_scanning_r2_residual_compat_stubs(
    filename: str,
) -> None:
    text = _read(COMPAT_DIR / filename)
    assert "TP-DMX-PR-PREP-SPECIALIST-V2-001-R1" in text
    assert "03-reference/pr-pipeline/prep" in text
