"""TP-RTE-TRUTH-R3-005d -- merge-scope + duplicate-surface content fixes.

Findings covered (CONSOLIDATED-FINDINGS.md):
  F-28 (HIGH) -- G9 merge/QA excludes G5/G6/G7 (the three schema-backed G-phase
    artifacts); A99 merge procedure loads "A1-A13" but only ever merges/QAs A1-A10,
    orphaning A11/A12/A13 outputs from phase coverage.
  F-32 (HIGH, scoped to B2/C4 only for this packet) -- REFUSAL_GUARDRAILS_SURFACE (B2)
    and REFUSAL_AND_GUARDRAILS_SURFACE (C4) are duplicate/near-duplicate refusal-rails
    surfaces with no canonical-writer arbitration declared between them.

These tests pin prompt CONTENT only (no kind/merge_strategy/canonical_writer_step_id/
schema changes were made -- artifacts.yaml is untouched and remains the authority for
those fields; see git diff for this packet). Confirmed by grep that neither
lib/promptgen/*.py nor run_extraction_v4.py/run_extraction_v5.py parse the "Upstream
normalized artifacts available to this step" bullet list programmatically -- it is
prose delivered to the model, not a machine-read input-wiring declaration.
"""

from __future__ import annotations

import re
from pathlib import Path

PROMPT_ROOT = Path(__file__).resolve().parents[1] / "promptsets" / "v4" / "prompts"

G9_PROMPT = PROMPT_ROOT / "PROMPT_G9_MERGE___QA.md"
A99_PROMPT = PROMPT_ROOT / "PROMPT_A99_MERGE___QA.md"
B2_PROMPT = PROMPT_ROOT / "PROMPT_B2_REFUSAL_RAILS___GUARDRAILS_SURFACE.md"
C4_PROMPT = PROMPT_ROOT / "PROMPT_C4_TRINITY_BOUNDARY_ENFORCEMENT_SURFACES.md"


def _section(text: str, name: str) -> str:
    match = re.search(
        rf"^## {re.escape(name)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match is not None, f"missing section: {name}"
    return match.group("body")


_ORDERED_LIST_LINE_RE = re.compile(r"^\s*(\d+)\.\s+")


def _numbering_is_monotonic(section_body: str) -> bool:
    previous = None
    for raw_line in section_body.splitlines():
        m = _ORDERED_LIST_LINE_RE.match(raw_line)
        if not m:
            continue
        current = int(m.group(1))
        if previous is not None and current <= previous:
            return False
        previous = current
    return True


# ---------------------------------------------------------------------------
# F-28 half 1: G9 merge scope must cover G5/G6/G7 (AUTH_FLOW_SURFACE,
# DEPENDENCY_HEALTH_SURFACE, TECHNICAL_DEBT_REGISTER).
# ---------------------------------------------------------------------------


def test_g9_upstream_inputs_include_g5_g6_g7_outputs() -> None:
    text = G9_PROMPT.read_text(encoding="utf-8")
    inputs = _section(text, "Inputs")
    for artifact in (
        "AUTH_FLOW_SURFACE.json",
        "DEPENDENCY_HEALTH_SURFACE.json",
        "TECHNICAL_DEBT_REGISTER.json",
    ):
        assert artifact in inputs, f"G9 Inputs missing upstream reference to {artifact}"


def test_g9_extraction_procedure_merges_and_qas_g5_g6_g7() -> None:
    text = G9_PROMPT.read_text(encoding="utf-8")
    procedure = _section(text, "Extraction Procedure")
    for artifact in (
        "AUTH_FLOW_SURFACE.json",
        "DEPENDENCY_HEALTH_SURFACE.json",
        "TECHNICAL_DEBT_REGISTER.json",
    ):
        assert artifact in procedure, (
            f"G9 Extraction Procedure never references {artifact} -- "
            "G5/G6/G7 remain orphaned from merge + QA coverage (F-28)"
        )
    # G9's own output contract (kind/merge_strategy/canonical_writer_step_id) must be
    # untouched by this content fix -- this is the exact class of bug that forced the
    # R3-005e revert (declaring/changing a value the runtime doesn't handle).
    schema = _section(text, "Schema")
    assert "`canonical_writer_step_id`: `G9`" in schema
    assert schema.count("`kind`: `json_item_list`") == 2  # GOV_MERGED.json + GOV_QA.json
    assert "`merge_strategy`: `itemlist_by_id`" in schema


# ---------------------------------------------------------------------------
# F-28 half 2: A99 merge procedure loads "A1-A13" but must cover A11/A12/A13
# outputs (EDITOR_INTEGRATION_SURFACE, CLI_COMMAND_SURFACE, HOOK_CONTRACT_SURFACE,
# EVENT_FLOW_GRAPH) in its QA/manifest coverage, without re-declaring them under a
# different canonical_writer_step_id (they are self-canonical per artifacts.yaml).
# ---------------------------------------------------------------------------


def test_a99_upstream_inputs_include_a11_a12_a13_outputs() -> None:
    text = A99_PROMPT.read_text(encoding="utf-8")
    inputs = _section(text, "Inputs")
    for artifact in (
        "EDITOR_INTEGRATION_SURFACE.json",
        "CLI_COMMAND_SURFACE.json",
        "HOOK_CONTRACT_SURFACE.json",
        "EVENT_FLOW_GRAPH.json",
    ):
        assert artifact in inputs, f"A99 Inputs missing upstream reference to {artifact}"


def test_a99_extraction_procedure_covers_a11_a12_a13_in_qa_and_manifest() -> None:
    text = A99_PROMPT.read_text(encoding="utf-8")
    procedure = _section(text, "Extraction Procedure")
    for artifact in (
        "EDITOR_INTEGRATION_SURFACE.json",
        "CLI_COMMAND_SURFACE.json",
        "HOOK_CONTRACT_SURFACE.json",
        "EVENT_FLOW_GRAPH.json",
    ):
        assert artifact in procedure, (
            f"A99 Extraction Procedure never references {artifact} -- "
            "A11/A12/A13 remain orphaned from QA/manifest coverage (F-28)"
        )


def test_a99_does_not_reassign_a11_a12_a13_canonical_ownership() -> None:
    """A11/A12/A13 outputs stay self-canonical in artifacts.yaml (A11/A12/A13) --
    A99's Outputs/Schema sections (its own machine-parsed contract surface) must NOT
    grow entries for EDITOR_INTEGRATION_SURFACE.json et al., which would collide with
    their declared canonical_writer_step_id and duplicate an artifact under two writers.
    """
    text = A99_PROMPT.read_text(encoding="utf-8")
    outputs = _section(text, "Outputs")
    schema = _section(text, "Schema")
    for artifact in (
        "EDITOR_INTEGRATION_SURFACE.json",
        "CLI_COMMAND_SURFACE.json",
        "HOOK_CONTRACT_SURFACE.json",
        "EVENT_FLOW_GRAPH.json",
    ):
        assert artifact not in outputs, (
            f"{artifact} must not become an A99 Output -- it is self-canonical "
            "under A11/A12/A13 per artifacts.yaml"
        )
        assert artifact not in schema


# ---------------------------------------------------------------------------
# F-32 (B2/C4 slice): canonical-writer arbitration between REFUSAL_GUARDRAILS_SURFACE
# (B2) and REFUSAL_AND_GUARDRAILS_SURFACE (C4/C9).
# ---------------------------------------------------------------------------


def test_b2_declares_itself_canonical_and_references_c4_twin() -> None:
    text = B2_PROMPT.read_text(encoding="utf-8")
    goal = _section(text, "Goal")
    assert "canonical" in goal.lower()
    assert "REFUSAL_AND_GUARDRAILS_SURFACE.json" in goal
    inputs = _section(text, "Inputs")
    assert "REFUSAL_AND_GUARDRAILS_SURFACE.json" in inputs
    procedure = _section(text, "Extraction Procedure")
    assert "REFUSAL_AND_GUARDRAILS_SURFACE.json" in procedure
    # B2's own output contract must be untouched by this content fix.
    schema = _section(text, "Schema")
    assert "`canonical_writer_step_id`: `B2`" in schema
    assert "`kind`: `json_item_list`" in schema
    assert "`merge_strategy`: `itemlist_by_id`" in schema


def test_c4_narrows_scope_and_defers_to_b2_twin() -> None:
    text = C4_PROMPT.read_text(encoding="utf-8")
    goal = _section(text, "Goal")
    assert "REFUSAL_GUARDRAILS_SURFACE.json" in goal
    assert "PROMPT_B2" in goal or "B2" in goal
    procedure = _section(text, "Extraction Procedure")
    assert "B2" in procedure
    # C4's own output contract (still merged by C9, unchanged) must be untouched.
    schema = _section(text, "Schema")
    assert schema.count("`canonical_writer_step_id`: `C9`") == 2
    assert "REFUSAL_AND_GUARDRAILS_SURFACE.json" in _section(text, "Outputs")


def test_b2_extraction_procedure_step_numbering_stays_monotonic() -> None:
    """Regression pin: inserting a new merge-arbitration step into B2's numbered
    Extraction Procedure must not leave a duplicated/non-monotonic step number --
    exactly the F-35-class defect this program is otherwise trying to clean up.
    """
    text = B2_PROMPT.read_text(encoding="utf-8")
    procedure = _section(text, "Extraction Procedure")
    assert _numbering_is_monotonic(procedure), (
        f"B2 Extraction Procedure has non-monotonic step numbering:\n{procedure}"
    )
