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

Also covers the TP-DMX-PR-PREP-SPECIALIST-V2-001-R4 closure: the R3 terminal
semantic census found 19 files outside the R1+R2+R3 allowlist (codex/vibe
adapter blueprints, `final-prep-decision-model.md`,
`post-pilot-go-no-go-criteria.md`, `post-eval-governance-options.md`, and
`ambiguity-scoring.md`, in both canonical and compat form) that actively
instructed current behavior using the retired fixed-artifact ceremony,
`risk_hint`/`Risk Hint` `LOW/MEDIUM/HIGH`, and `CREATE_READY`/
`GO_SUPERVISED_FINAL_CREATION` vocabulary. R4 converts the 9 canonical files
to deprecation stubs deferring to `operator-contract.md` and the 10 compat
files to pure pointer stubs. This module does not test the 7
`NON_BLOCKING_LOCAL_MEASUREMENT` files identified by the same census
(`base-branch-detection-rules.md`, `obligation-model.md`,
`obligation-severity-rules.md`, `evaluation-model.md`,
`section-fill-policy.md`, `pilot-case-selection-rules.md`,
`operator-review-form.md`) — the R4 ruling requires those left unedited,
using LOW/MEDIUM/HIGH as a namespaced local measurement rather than the PR
risk lane.

Also covers the TP-DMX-PR-PREP-SPECIALIST-V2-001-R6 closure: the R3/R4
scanner searched for fixed-artifact/risk-hint/GO_* vocabulary but never for
`TP-PRPS-000` or `7-step`, so it missed that the six non-codex adapter
README families (claude, cursor, gemini, jules, copilot, vibe -- both
canonical and compat copies) still actively declared
`Contract: TP-PRPS-000-1.0.0`, a "7-step canonical workflow", and
`Status: IMPLEMENTED AND COMPLIANT`. That is a false-negative census, not a
judgment call. R6 converts all 12 files to deprecation/pointer stubs
matching the codex pattern already established at R4, and separately fixes
a broken-relative-link defect the R4 compat-stub template introduced: six
files under `docs/pr_prep/adapters/{vibe,codex}/**` linked to their
canonical counterpart with two `../` hops instead of the three actually
required, so every such link 404'd.
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

# The frozen 19-path R3 ACTIVE_CONTRADICTION set repaired by R4. Canonical
# and compat filenames differ (compat copies use disambiguated names like
# `readme-2.md`), so these are paired explicitly rather than reusing one
# filename list across both trees.
R4_REPAIRED_PAIRS = [
    (
        "adapters/codex/readme.md",
        "adapters/codex/readme-2.md",
    ),
    (
        "adapters/vibe/agent-spec.md",
        "adapters/vibe/agent-blueprint.md",
    ),
    (
        "adapters/vibe/agent-spec.md",
        "adapters/vibe/template-agent.md",
    ),
    (
        "adapters/vibe/checkpoint-sequence.md",
        "adapters/vibe/checkpoint-sequence.md",
    ),
    (
        "adapters/vibe/guardrails.md",
        "adapters/vibe/guardrails-2.md",
    ),
    (
        "adapters/vibe/operator-review-form.md",
        "adapters/vibe/operator-review-form.md",
    ),
    (
        "final-prep-decision-model.md",
        "final-prep-decision-model.md",
    ),
    (
        "post-pilot-go-no-go-criteria.md",
        "post-pilot-go-no-go-criteria.md",
    ),
    (
        "post-eval-governance-options.md",
        "post-eval-governance-options.md",
    ),
    (
        "ambiguity-scoring.md",
        "ambiguity-scoring.md",
    ),
]

R4_CANONICAL_FILES = sorted({canonical for canonical, _ in R4_REPAIRED_PAIRS})
R4_COMPAT_FILES = sorted({compat for _, compat in R4_REPAIRED_PAIRS})

# Structural remnants of the retired ceremony: markdown headers/fields that
# only appear if a file still actively *defines* the checkpoint/artifact
# ceremony (as opposed to prose describing, in the past tense, that it was
# retired -- retirement prose legitimately quotes the retired literals, so
# these checks target live structural markup, not the vocabulary itself).
R4_LIVE_CEREMONY_STRUCTURE_MARKERS = (
    "## Mandatory Checkpoints",
    "**Required Artifact**:",
    "**Required Artifacts**:",
    "**HUMAN SUMMARY TEMPLATE**:",
    "### INTAKE_CHECKPOINT",
    "### CREATION_CHECKPOINT",
    "## Guardrail Rules",
    "## Checkpoint Sequence",
)

# The retired ambiguity-band decision table this file previously used to
# compete with the L0-L3 risk lanes.
LEGACY_AMBIGUITY_DECISION_TABLE_SNIPPET = "| **70–100** | `HIGH` | `BLOCK_PENDING_REVIEW` |"

# The retired live decision-criteria heading structure this file previously
# used to define GO_* postures as current governing outcomes.
LEGACY_GO_CRITERIA_HEADING_SNIPPET = "### GO_SUPERVISED_FINAL_CREATION"

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


@pytest.mark.parametrize("filename", R4_CANONICAL_FILES)
def test_should_not_encode_legacy_enum_literals_when_scanning_r4_repaired_canonical_files(
    filename: str,
) -> None:
    text = _read(CANONICAL_DIR / filename)
    for marker in R4_LIVE_CEREMONY_STRUCTURE_MARKERS:
        assert marker not in text
    assert LEGACY_FIXED_ARTIFACT_SNIPPET not in text
    assert "contract-v2.md" not in text
    assert "Superseded" in text


@pytest.mark.parametrize("filename", R4_COMPAT_FILES)
def test_should_not_encode_legacy_enum_literals_when_scanning_r4_repaired_compat_files(
    filename: str,
) -> None:
    text = _read(COMPAT_DIR / filename)
    for marker in R4_LIVE_CEREMONY_STRUCTURE_MARKERS:
        assert marker not in text
    assert LEGACY_FIXED_ARTIFACT_SNIPPET not in text
    assert "contract-v2.md" not in text


@pytest.mark.parametrize("filename", R4_COMPAT_FILES)
def test_should_reference_canonical_tree_when_scanning_r4_repaired_compat_stubs(
    filename: str,
) -> None:
    text = _read(COMPAT_DIR / filename)
    assert "TP-DMX-PR-PREP-SPECIALIST-V2-001-R1" in text
    assert "compatibility surface only" in text


def test_should_not_encode_legacy_ambiguity_decision_table_when_scanning_canonical_ambiguity_scoring() -> None:
    text = _read(CANONICAL_DIR / "ambiguity-scoring.md")
    assert LEGACY_AMBIGUITY_DECISION_TABLE_SNIPPET not in text
    assert "| Score | Level | Decision |" not in text


def test_should_not_define_legacy_pilot_go_states_as_governing_when_scanning_canonical_post_pilot_criteria() -> None:
    text = _read(CANONICAL_DIR / "post-pilot-go-no-go-criteria.md")
    assert LEGACY_GO_CRITERIA_HEADING_SNIPPET not in text
    assert "Superseded" in text


# The R4 ruling exempts these 7 files (plus their compat copies) as
# NON_BLOCKING_LOCAL_MEASUREMENT: LOW/MEDIUM/HIGH here grades a namespaced
# local quantity (confidence, obligation severity, evaluation quality,
# override severity) and does not itself gate PR creation, audit, or
# readiness. They must remain unedited by this packet.
R4_NON_BLOCKING_FILES = [
    "base-branch-detection-rules.md",
    "obligation-model.md",
    "obligation-severity-rules.md",
    "evaluation-model.md",
    "section-fill-policy.md",
    "pilot-case-selection-rules.md",
    "operator-review-form.md",
]


@pytest.mark.parametrize("filename", R4_NON_BLOCKING_FILES)
def test_should_not_declare_itself_a_pointer_stub_when_scanning_non_blocking_canonical_files(
    filename: str,
) -> None:
    text = _read(CANONICAL_DIR / filename)
    assert "compatibility surface only" not in text


# R6: the R3/R4 census scanner never searched for TP-PRPS-000 or 7-step, so
# it false-negatived these six adapter families straight through -- each
# still actively declared the retired V1 contract.
R6_ADAPTER_PLATFORMS = ["claude", "cursor", "gemini", "jules", "copilot", "vibe"]

R6_REPAIRED_PAIRS = [
    (f"adapters/{platform}/readme.md", f"adapters/{platform}/readme-2.md")
    for platform in R6_ADAPTER_PLATFORMS
]

R6_CANONICAL_FILES = sorted({canonical for canonical, _ in R6_REPAIRED_PAIRS})
R6_COMPAT_FILES = sorted({compat for _, compat in R6_REPAIRED_PAIRS})

# Live structural markers of the retired V1 adapter-compliance ceremony.
# Retirement prose legitimately quotes these as single-backtick inline code
# describing what was retired (e.g. "previously claimed `Contract:
# TP-PRPS-000-1.0.0`"); these snippets target the bold-labelled/checkmarked
# live-claim form only, never the retrospective quoting form.
R6_LIVE_V1_CONTRACT_MARKERS = (
    "**Contract**: TP-PRPS-000-1.0.0",
    "**Status**: ✅ IMPLEMENTED AND COMPLIANT",
    "✅ 7-step canonical workflow",
    "✅ Workflow: Exact 7-step sequence",
    "contract: TP-PRPS-000-1.0.0",
)


@pytest.mark.parametrize("filename", R6_CANONICAL_FILES)
def test_should_not_declare_live_v1_adapter_contract_when_scanning_r6_repaired_canonical_files(
    filename: str,
) -> None:
    text = _read(CANONICAL_DIR / filename)
    for marker in R6_LIVE_V1_CONTRACT_MARKERS:
        assert marker not in text
    assert "Superseded" in text


@pytest.mark.parametrize("filename", R6_COMPAT_FILES)
def test_should_not_declare_live_v1_adapter_contract_when_scanning_r6_repaired_compat_files(
    filename: str,
) -> None:
    text = _read(COMPAT_DIR / filename)
    for marker in R6_LIVE_V1_CONTRACT_MARKERS:
        assert marker not in text


@pytest.mark.parametrize("filename", R6_COMPAT_FILES)
def test_should_not_retain_independent_behavioral_authority_when_scanning_r6_repaired_compat_stubs(
    filename: str,
) -> None:
    text = _read(COMPAT_DIR / filename)
    assert "compatibility surface only" in text
    assert "TP-DMX-PR-PREP-SPECIALIST-V2-001-R1" in text


# R6: the R4 compat-stub template's canonical link used two "../" hops from
# docs/pr_prep/adapters/{platform}/ but three are required to reach
# docs/03-reference/**; every such link 404'd (flagged live by
# copilot-pull-request-reviewer on PR #1224). This regression test resolves
# every markdown link target on disk for every non-archive compat file, not
# just the ones already flagged, so a future template bug can't hide behind
# an incomplete file list.
_LINK_PATTERN = __import__("re").compile(r"\]\(([^)#][^)]*)\)")


def _iter_markdown_files(base: Path):
    for path in base.rglob("*.md"):
        if "archive" in path.parts:
            continue
        yield path


@pytest.mark.parametrize(
    "path",
    [p for p in _iter_markdown_files(COMPAT_DIR)],
    ids=lambda p: str(p.relative_to(ROOT)),
)
def test_should_resolve_every_relative_link_when_scanning_non_archive_compat_markdown(
    path: Path,
) -> None:
    text = path.read_text(encoding="utf-8")
    for match in _LINK_PATTERN.finditer(text):
        target = match.group(1)
        if target.startswith("http"):
            continue
        resolved = (path.parent / target).resolve()
        assert resolved.exists(), f"{path.relative_to(ROOT)} -> {target} does not resolve ({resolved})"
