"""TP-RTE-TRUTH-R3-005b -- S7 rewrite (production stub feeding S11/S12).

CONSOLIDATED-FINDINGS.md finding covered:

  F-22 (CRIT, A3c C1): `PROMPT_S7_OVERSEER_AGENT_FLOW_DESIGN.md` self-admitted it was a
  "structural stub to pass v5 linting" with instruction-rewrite "deferred to Opus", and its
  own Schema section called its output "highly unstructured markdown" -- with no citation
  requirement and no anti-fabrication guardrail on the overseer:agent narrative it produces.
  S7 is a *required* input to `PROMPT_S11_DOCUMENTATION_GENERATION.md` (Section 6: "Agent
  Orchestration") and to `PROMPT_S12_STABILITY_SIGNATURE.md` (hashed into the stability
  signature), so an unstructured/fabricated S7 body propagates directly into the
  consolidation doc and the regression signature.

Lane-binding note (see CLAUDE.md "IMPORTANT LANE TRUTH" / AGENTS.md Sec 12 dispatch): S7's
own `artifacts.yaml` entry (`kind: markdown`, `merge_strategy: markdown_concat`,
`required_fields: []`) is untouched by this packet -- markdown-kind outputs never reach
`lib.structured_output_contracts` (grep confirms zero markdown-kind handling there), so
there is no request-time JSON-schema lane to bind for this step. The change made here is
prompt-content only: the Schema section's "Required output content contracts" / "Required
citation shape" text (mirroring the already-implemented S8/S9/S10 convention) and the
Extraction Procedure text reach the model verbatim as part of the rendered prompt body --
that IS the binding surface for a markdown synthesis step. No schemas/*.schema.json,
artifacts.yaml, or promptset.yaml edit was needed or made.
"""

from __future__ import annotations

import re
from pathlib import Path

from lib.promptgen.template_renderer import validate_rendered_prompt

SERVICE_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = SERVICE_ROOT / "promptsets" / "v4" / "prompts"
S7_PATH = PROMPTS_DIR / "PROMPT_S7_OVERSEER_AGENT_FLOW_DESIGN.md"
S11_PATH = PROMPTS_DIR / "PROMPT_S11_DOCUMENTATION_GENERATION.md"
ARTIFACTS_PATH = SERVICE_ROOT / "promptsets" / "v4" / "artifacts.yaml"

REQUIRED_SECTIONS = [
    "Goal",
    "Inputs",
    "Outputs",
    "Schema",
    "Extraction Procedure",
    "Evidence Rules",
    "Determinism Rules",
    "Anti-Fabrication Rules",
    "Failure Modes",
]

REQUIRED_UPSTREAM_ARTIFACTS = (
    "AGENT_ORCHESTRATION_SURFACE.json",
    "HOOK_CONTRACT_SURFACE.json",
    "EVENT_FLOW_GRAPH.json",
    "EDITOR_INTEGRATION_SURFACE.json",
)

# Real required_item_fields of the four upstream artifacts, confirmed by grepping each
# upstream prompt's own `required_item_fields:` backtick line (PROMPT_C12, PROMPT_A13 x2,
# PROMPT_A11) -- not invented for this rewrite.
REAL_UPSTREAM_FIELDS = (
    "agent_type",  # C12 AGENT_ORCHESTRATION_SURFACE.json
    "item_type",  # C12
    "trigger_source",  # A13 HOOK_CONTRACT_SURFACE.json
    "handler_path",  # A13
    "event_types",  # A13 (hook side; plural)
    "transport_mechanism",  # A13
    "lifecycle_phase",  # A13
    "source",  # A13 EVENT_FLOW_GRAPH.json
    "target",  # A13
    "event_type",  # A13 (edge side; singular)
    "direction",  # A13
    "editor_type",  # A11 EDITOR_INTEGRATION_SURFACE.json
    "config_key",  # A11
    "config_value",  # A11
    "scope",  # A11
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# --- F-22: self-admitted stub language removed --------------------------------------------


def test_s7_no_longer_self_admits_stub_status() -> None:
    text = _read(S7_PATH)
    assert "structural stub" not in text, (
        "PROMPT_S7 still self-admits it is a 'structural stub' -- F-22 requires a real "
        "structured step, not an admitted placeholder"
    )
    assert "deferred to Opus" not in text
    assert "highly unstructured markdown" not in text


# --- F-22: real structured contract present, matching S8-S12 quality bar -------------------


def test_s7_declares_required_output_content_contracts_like_s8_s12() -> None:
    text = _read(S7_PATH)
    assert "Required output content contracts" in text
    assert "Required citation shape" in text
    assert "EVIDENCE: <artifact_filename>#<item_id>" in text


def test_s7_declares_all_six_sections() -> None:
    text = _read(S7_PATH)
    for section_name in (
        "Agent Inventory",
        "Overseer Identification",
        "Hook & Event Wiring",
        "Editor Integration Surface",
        "Overseer:Agent Flow Narrative",
        "Coverage Notes / Unknowns",
    ):
        assert section_name in text, f"PROMPT_S7 missing declared output section {section_name!r}"


def test_s7_forbids_inventing_an_overseer_when_none_is_evidenced() -> None:
    text = _read(S7_PATH)
    assert "No overseer entity found in AGENT_ORCHESTRATION_SURFACE.json" in text
    assert "instead of inventing one" in text or "rather than naming an unevidenced overseer" in text


def test_s7_handles_missing_artifacts_with_explicit_marker() -> None:
    text = _read(S7_PATH)
    assert "Source artifact not available" in text


def test_s7_emits_exactly_declared_output_and_nothing_else() -> None:
    text = _read(S7_PATH)
    assert "Emit exactly the declared output and no additional files" in text


# --- F-22: required upstream artifacts declared, no schema/kind drift ----------------------


def test_s7_declares_the_four_real_upstream_json_artifacts_as_required() -> None:
    text = _read(S7_PATH)
    inputs_section = text.split("## Inputs", 1)[1].split("## Outputs", 1)[0]
    required_block = inputs_section.split("Required upstream artifacts", 1)[1].split(
        "Optional synthesis helpers", 1
    )[0]
    for artifact_name in REQUIRED_UPSTREAM_ARTIFACTS:
        assert artifact_name in required_block, (
            f"PROMPT_S7 no longer declares {artifact_name!r} as a required upstream input"
        )


def test_s7_extraction_procedure_only_references_real_upstream_item_fields() -> None:
    """Every domain field the procedure names must be one this test independently
    confirmed (via grep of each upstream prompt's own required_item_fields line) actually
    exists on that artifact -- guards against re-introducing an invented field name."""
    text = _read(S7_PATH)
    for field in REAL_UPSTREAM_FIELDS:
        assert f"`{field}`" in text, f"PROMPT_S7 no longer mentions real upstream field {field!r}"


def test_s7_output_kind_and_merge_strategy_unchanged_in_artifacts_yaml() -> None:
    """F-31/R3-005e lesson: never let a rewrite silently drift the declared artifact kind.
    S7 emits markdown (not json_item_list); this packet must not touch artifacts.yaml, and
    the runtime-recognized kind/merge_strategy for S7 must stay exactly what run_extraction_v4/v5
    already implement."""
    artifacts_text = _read(ARTIFACTS_PATH)
    match = re.search(
        r"artifact_name:\s*S7_OVERSEER_AGENT_FLOW_DESIGN\.md\n"
        r"(?:.*\n)*?"
        r"\s*kind:\s*(\S+)\n"
        r"(?:.*\n)*?"
        r"\s*merge_strategy:\s*(\S+)",
        artifacts_text,
    )
    assert match is not None, "could not locate S7_OVERSEER_AGENT_FLOW_DESIGN.md artifacts.yaml entry"
    kind, merge_strategy = match.group(1), match.group(2)
    assert kind == "markdown", f"S7 artifact kind drifted to {kind!r} (must stay 'markdown')"
    assert merge_strategy == "markdown_concat", (
        f"S7 merge_strategy drifted to {merge_strategy!r} (must stay 'markdown_concat')"
    )


# --- F-22: section-length contract (promptset required_prompt_sections gate) ---------------


def test_s7_satisfies_promptset_section_and_length_contract() -> None:
    text = _read(S7_PATH)
    result = validate_rendered_prompt(text, required_sections=REQUIRED_SECTIONS)
    assert result["valid"] is True, result["issues"]
    assert result["sections_missing"] == []


# --- Downstream input-contract regression guard (S11 already names S7 by filename) ---------


def test_s11_still_declares_s7_as_a_required_upstream_input() -> None:
    """Not a behavior this packet changes -- a guard that the S11/S12 input contract this
    packet was scoped to feed is exactly what it was verified to be before the rewrite."""
    text = _read(S11_PATH)
    assert "S7_OVERSEER_AGENT_FLOW_DESIGN.md" in text
