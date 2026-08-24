"""TP-RTE-TRUTH-R3-005a -- phase M recast + H9 sha256 + E-phase contract repairs.

CONSOLIDATED-FINDINGS.md findings covered:

  F-21 (CRIT, A3b F-1/F-2): Phase M (M0-M6) procedures mandated "query live state" and
  "compile extracted data with timestamps and provenance" -- infeasible for a text-in/
  text-out LLM (no live DB/network/MCP access) and directly contradicting the binding
  Determinism Rules ("Norm outputs MUST NOT contain: generated_at, timestamp, created_at,
  updated_at, run_id"). H9's HOMECTRL_NORM_MANIFEST additionally required a per-item
  `sha256` the model cannot compute.

  F-25 (HIGH, A3b F-3): six E-phase procedures (E1-E6) referenced upstream artifact names
  that do not exist in the declared contracts (`EXECUTION_INVENTORY.json` instead of the
  real `EXEC_INVENTORY.json`, etc.), and E5/E6 had disjoint required-item-field sets
  between their Schema section and their own Extraction Procedure ("Build ... Items" step).

  F-37 (MED, A3b F-13): M3/M4/M5 hardcoded `implementer="GPT-5.3-Codex"` provenance in
  their Legacy Context blocks -- false metadata whenever any other model executes the step.

Lane-binding note (see CLAUDE.md "IMPORTANT LANE TRUTH" / AGENTS.md Sec 12 dispatch):
the `.schema.json` files under promptsets/v4/schemas/ are NOT loaded at request time. The
request-time OpenAI JSON-schema is built by
`lib.structured_output_contracts._generic_item_schema`, which unions
`artifact_meta["required_fields"]` (from artifacts.yaml) with
`artifact_meta["prompt_required_item_fields"]` -- and the latter is parsed live, per run,
straight out of each prompt's own `` `required_item_fields`: `...` `` backtick line by
`lib.phase_contract_map._required_item_fields_by_artifact` (regex `_REQUIRED_FIELDS_RE`).
So editing that backtick line in the prompt .md file *is* the request-time-binding fix for
the H9 sha256 removal and the E5/E6 field-set repairs below -- no schema/artifacts.yaml
edit is needed or made for those two findings. The E1-E6 "Load `EXECUTION_INVENTORY.json`"
prose fix is a pure prompt-instruction-text change (the artifact name emitted was already
listed correctly in each prompt's own `## Outputs`/`## Schema`; only the mid-procedure
prose reference to a nonexistent upstream file name was fixed) and does not touch any
binding lane at all -- it only removes a claim about an artifact that does not exist.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SERVICE_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = SERVICE_ROOT / "promptsets" / "v4" / "prompts"

M_PHASE_STEP_IDS = ["M0", "M1", "M2", "M3", "M4", "M5", "M6"]
M_PHASE_FILENAMES = {
    "M0": "PROMPT_M0_RUNTIME_EXPORT_INVENTORY.md",
    "M1": "PROMPT_M1_SQLITE_SCHEMA_SNAPSHOTS.md",
    "M2": "PROMPT_M2_SQLITE_TABLE_COUNTS.md",
    "M3": "PROMPT_M3_CONPORT_EXPORT_SAFE.md",
    "M4": "PROMPT_M4_DOPE_CONTEXT_EXPORT_SAFE.md",
    "M5": "PROMPT_M5_MCP_HEALTH_EXPORT_SAFE.md",
    "M6": "PROMPT_M6_RUNTIME_EXPORT_INDEX.md",
}
H9_PATH = PROMPTS_DIR / "PROMPT_H9_MERGE___QA.md"

E_PHASE_FILENAMES = {
    "E1": "PROMPT_E1_BOOTSTRAP_COMMANDS_SURFACE.md",
    "E2": "PROMPT_E2_ENV_LOADING___CONFIG_CHAIN.md",
    "E3": "PROMPT_E3_SERVICE_STARTUP_GRAPH.md",
    "E4": "PROMPT_E4_RUNTIME_MODES___DELTA_REPORT.md",
    "E5": "PROMPT_E5_ARTIFACT_OUTPUTS___LOGS___STATE.md",
    "E6": "PROMPT_E6_EXECUTION_RISKS___ORDERING___STATE_DEPENDENCY.md",
}

# Real upstream artifact names (confirmed by each prompt's own `## Inputs` section and by
# artifacts.yaml E-phase entries). The pre-fix prose referenced names that do not exist.
NONEXISTENT_UPSTREAM_NAMES = (
    "EXECUTION_INVENTORY.json",
    "EXECUTION_PARTITIONS.json",
    "SERVICE_STARTUP_GRAPH.json",
    "ENV_LOADING_CONFIG_CHAIN.json",
)


def _read(step_id_to_filename: dict[str, str], step_id: str) -> str:
    return (PROMPTS_DIR / step_id_to_filename[step_id]).read_text(encoding="utf-8")


# --- F-21a: M-phase "query live state" fabrication-by-construction -----------------------


@pytest.mark.parametrize("step_id", M_PHASE_STEP_IDS)
def test_m_phase_no_longer_mandates_live_state_query(step_id: str) -> None:
    text = _read(M_PHASE_FILENAMES, step_id)
    assert "query live state" not in text, (
        f"{M_PHASE_FILENAMES[step_id]} still instructs the LLM to 'query live state' -- "
        "infeasible for a text-in/text-out model (F-21)"
    )


@pytest.mark.parametrize("step_id", M_PHASE_STEP_IDS)
def test_m_phase_no_longer_mandates_timestamps_in_output(step_id: str) -> None:
    text = _read(M_PHASE_FILENAMES, step_id)
    assert "with timestamps and provenance" not in text, (
        f"{M_PHASE_FILENAMES[step_id]} still tells the model to compile output "
        "'with timestamps and provenance', contradicting PROMPTSET_RULES.md's binding "
        "Determinism Rules (F-21)"
    )


@pytest.mark.parametrize("step_id", M_PHASE_STEP_IDS)
def test_m_phase_extraction_procedure_declares_no_live_access_and_unknown_fallback(
    step_id: str,
) -> None:
    """Positive assertion: the recast text must itself state the no-live-access boundary
    and the UNKNOWN/Anti-Fabrication fallback, not merely delete the old wording."""
    text = _read(M_PHASE_FILENAMES, step_id)
    assert "no live database, network, filesystem-probe, or MCP access" in text
    assert "UNKNOWN" in text
    assert "missing_evidence_reason" in text
    assert "Anti-Fabrication Rules" in text


def test_m_phase_determinism_forbidden_keys_named_explicitly() -> None:
    """Every M-phase step must itself spell out the forbidden determinism keys, not just
    point at the rules file -- this is the concrete text that resolves the two-contract
    conflict A3b flagged (a model shown a contradiction resolves it arbitrarily)."""
    for step_id in M_PHASE_STEP_IDS:
        text = _read(M_PHASE_FILENAMES, step_id)
        for forbidden_key in ("generated_at", "timestamp", "created_at", "updated_at", "run_id"):
            assert f"`{forbidden_key}`" in text, (
                f"{M_PHASE_FILENAMES[step_id]} extraction procedure no longer names "
                f"forbidden determinism key {forbidden_key!r}"
            )


# --- F-21b: H9 uncomputable per-item sha256 -----------------------------------------------


def test_h9_homectrl_norm_manifest_no_longer_requires_sha256() -> None:
    text = H9_PATH.read_text(encoding="utf-8")
    match = re.search(
        r"`HOMECTRL_NORM_MANIFEST\.json`.*?`required_item_fields`:\s*`([^`]+)`",
        text,
        re.DOTALL,
    )
    assert match is not None, "could not locate HOMECTRL_NORM_MANIFEST required_item_fields line"
    fields = [f.strip() for f in match.group(1).split(",")]
    assert "sha256" not in fields, (
        f"HOMECTRL_NORM_MANIFEST.json still requires sha256 (uncomputable by an LLM): {fields}"
    )
    # Sanity: the other real fields must still be present (this is a subtraction, not a
    # rewrite of the whole contract).
    assert {"id", "artifact_name", "writer_step_id", "evidence"}.issubset(set(fields))


def test_h9_prompt_body_has_no_other_sha256_reference() -> None:
    text = H9_PATH.read_text(encoding="utf-8")
    assert "sha256" not in text


# --- F-37: hardcoded implementer="GPT-5.3-Codex" provenance in M3/M4/M5 ------------------


@pytest.mark.parametrize("step_id", ["M3", "M4", "M5"])
def test_m_phase_safe_export_no_longer_hardcodes_implementer_provenance(step_id: str) -> None:
    text = _read(M_PHASE_FILENAMES, step_id)
    assert "GPT-5.3-Codex" not in text, (
        f"{M_PHASE_FILENAMES[step_id]} still hardcodes implementer=\"GPT-5.3-Codex\" -- "
        "false provenance metadata whenever a different model executes this step (F-37)"
    )
    assert "Codex CLI/Desktop" not in text


# --- F-25: E-phase nonexistent upstream artifact-name references -------------------------


@pytest.mark.parametrize("step_id", ["E1", "E2", "E3", "E4", "E5", "E6"])
def test_e_phase_procedure_does_not_reference_nonexistent_upstream_names(step_id: str) -> None:
    text = _read(E_PHASE_FILENAMES, step_id)
    hits = [name for name in NONEXISTENT_UPSTREAM_NAMES if name in text]
    assert hits == [], (
        f"{E_PHASE_FILENAMES[step_id]} still references nonexistent upstream artifact "
        f"name(s) {hits} (F-25); real names are declared in this step's own ## Inputs "
        "section (EXEC_INVENTORY.json, EXEC_PARTITIONS.json, EXEC_STARTUP_GRAPH.json, "
        "EXEC_ENV_CHAIN.json)"
    )


@pytest.mark.parametrize(
    "step_id,expected_name",
    [
        ("E1", "EXEC_INVENTORY.json"),
        ("E2", "EXEC_INVENTORY.json"),
        ("E3", "EXEC_INVENTORY.json"),
        ("E4", "EXEC_INVENTORY.json"),
        ("E5", "EXEC_INVENTORY.json"),
        ("E6", "EXEC_INVENTORY.json"),
    ],
)
def test_e_phase_step_1_loads_the_real_declared_upstream_inventory_name(
    step_id: str, expected_name: str
) -> None:
    text = _read(E_PHASE_FILENAMES, step_id)
    step_one = text.split("## Extraction Procedure", 1)[1].splitlines()[1]
    assert expected_name in step_one, (
        f"{E_PHASE_FILENAMES[step_id]} step 1 does not load the real upstream artifact "
        f"{expected_name!r}: {step_one!r}"
    )


# --- F-25: E5/E6 disjoint required-field sets (contract vs. procedure) -------------------


def test_e5_required_item_fields_match_what_the_procedure_actually_builds() -> None:
    text = E_PHASE_FILENAMES and _read(E_PHASE_FILENAMES, "E5")
    match = re.search(r"`required_item_fields`:\s*`([^`]+)`", text)
    assert match is not None
    fields = {f.strip() for f in match.group(1).split(",")}
    # The old generic `component, symbol` placeholders must be gone...
    assert "symbol" not in fields
    # ...replaced by the domain fields the "Build Output Items" step actually populates.
    for domain_field in ("artifact_path", "persistence_type", "component_owner"):
        assert domain_field in fields, (
            f"EXEC_ARTIFACT_SURFACE.json required_item_fields missing {domain_field!r}; "
            f"got {sorted(fields)}"
        )
        assert f"`{domain_field}`" in text, (
            f"E5 procedure text no longer mentions {domain_field!r} even though the "
            "contract requires it"
        )


def test_e6_required_item_fields_match_what_the_procedure_actually_builds() -> None:
    text = _read(E_PHASE_FILENAMES, "E6")
    match = re.search(r"`required_item_fields`:\s*`([^`]+)`", text)
    assert match is not None
    fields = {f.strip() for f in match.group(1).split(",")}
    for domain_field in ("risk_type", "severity", "mitigation_evidence"):
        assert domain_field in fields, (
            f"EXEC_RISK_FACTS.json required_item_fields missing {domain_field!r}; "
            f"got {sorted(fields)}"
        )
        assert f"`{domain_field}`" in text, (
            f"E6 procedure text no longer mentions {domain_field!r} even though the "
            "contract requires it"
        )
    # severity vocabulary reused from the promptset's existing critical|high|medium|low
    # set (B3/C8/C14), not a newly coined scale.
    assert "`critical`" in text and "`high`" in text and "`medium`" in text and "`low`" in text


def test_e6_step_1_loads_the_real_declared_upstream_names_for_startup_and_env_chain() -> None:
    text = _read(E_PHASE_FILENAMES, "E6")
    step_one = text.split("## Extraction Procedure", 1)[1].splitlines()[1]
    assert "EXEC_STARTUP_GRAPH.json" in step_one
    assert "EXEC_ENV_CHAIN.json" in step_one
