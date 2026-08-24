from __future__ import annotations

from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[3]
PROMPT_ROOT = ROOT / "services" / "repo-truth-extractor" / "promptsets" / "v4"
C9_PROMPT = PROMPT_ROOT / "prompts" / "PROMPT_C9_MERGE___NORMALIZE___QA.md"

C9_OUTPUTS = (
    "SERVICE_ENTRYPOINTS.json",
    "EVENTBUS_SURFACE.json",
    "EVENT_PRODUCERS.json",
    "EVENT_CONSUMERS.json",
    "DOPE_MEMORY_CODE_SURFACE.json",
    "TRINITY_ENFORCEMENT_SURFACE.json",
    "REFUSAL_AND_GUARDRAILS_SURFACE.json",
    "TASKX_INTEGRATION_SURFACE.json",
    "WORKFLOW_RUNNER_SURFACE.json",
    "DETERMINISM_RISK_LOCATIONS.json",
    "IDEMPOTENCY_RISK_LOCATIONS.json",
    "CONCURRENCY_RISK_LOCATIONS.json",
    "PYTHON_API_SURFACE.json",
    "SERVICE_ENDPOINT_SURFACE.json",
    "SERVICE_CATALOG.json",
    "CODE_SURFACES_QA.json",
)

RICH_PRODUCER_PROMPTS = {
    "SERVICE_ENTRYPOINTS.json": "PROMPT_C1_SERVICE_ENTRYPOINTS.md",
    "EVENTBUS_SURFACE.json": "PROMPT_C2_EVENTBUS_WIRING_TRUTH_SURFACES.md",
    "EVENT_PRODUCERS.json": "PROMPT_C2_EVENTBUS_WIRING_TRUTH_SURFACES.md",
    "EVENT_CONSUMERS.json": "PROMPT_C2_EVENTBUS_WIRING_TRUTH_SURFACES.md",
    "DETERMINISM_RISK_LOCATIONS.json": (
        "PROMPT_C8_DETERMINISM___IDEMPOTENCY___CONCURRENCY_LOCATION_SCANS.md"
    ),
    "IDEMPOTENCY_RISK_LOCATIONS.json": (
        "PROMPT_C8_DETERMINISM___IDEMPOTENCY___CONCURRENCY_LOCATION_SCANS.md"
    ),
    "CONCURRENCY_RISK_LOCATIONS.json": (
        "PROMPT_C8_DETERMINISM___IDEMPOTENCY___CONCURRENCY_LOCATION_SCANS.md"
    ),
}

POST_C9_ARTIFACTS = {
    "LEANTIME_INTEGRATION_SURFACE.json",
    "AGENT_ORCHESTRATION_SURFACE.json",
    "ADHD_ENGINE_SURFACE.json",
    "MODULE_DEPENDENCY_GRAPH.json",
    "SERVICE_DEPENDENCY_GRAPH.json",
    "COGNITIVE_FEATURES_SURFACE.json",
}


def _section(text: str, name: str) -> str:
    match = re.search(
        rf"^## {re.escape(name)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match is not None, f"missing section: {name}"
    return match.group("body")


def _declared_outputs(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"^- `([^`]+\.json)`\s*$", _section(text, "Outputs"), re.MULTILINE))


def _schema_outputs(text: str) -> tuple[str, ...]:
    return tuple(
        re.findall(r"^  - `([^`]+\.json)`\s*$", _section(text, "Schema"), re.MULTILINE)
    )


def _required_item_fields(text: str, artifact_name: str) -> tuple[str, ...]:
    schema = _section(text, "Schema")
    contract = re.search(
        rf"^  - `{re.escape(artifact_name)}`\s*$\n(?P<body>.*?)(?=^  - `|\Z)",
        schema,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert contract is not None, f"missing schema contract: {artifact_name}"
    fields = re.search(r"`required_item_fields`: `([^`]+)`", contract.group("body"))
    assert fields is not None, f"missing required_item_fields: {artifact_name}"
    return tuple(field.strip() for field in fields.group(1).split(","))


def test_promptset_c9_outputs_schema_and_registry_are_identical_and_ordered() -> None:
    text = C9_PROMPT.read_text(encoding="utf-8")
    promptset = yaml.safe_load((PROMPT_ROOT / "promptset.yaml").read_text(encoding="utf-8"))
    artifacts = yaml.safe_load((PROMPT_ROOT / "artifacts.yaml").read_text(encoding="utf-8"))
    c9 = next(row for row in promptset["phases"]["C"]["steps"] if row["step_id"] == "C9")
    registered_c9_outputs = {
        row["artifact_name"]
        for row in artifacts["artifacts"]
        if row.get("phase") == "C" and row.get("canonical_writer_step_id") == "C9"
    }

    assert _declared_outputs(text) == C9_OUTPUTS
    assert _schema_outputs(text) == C9_OUTPUTS
    assert tuple(c9["outputs"]) == C9_OUTPUTS
    assert registered_c9_outputs == set(C9_OUTPUTS)
    assert not POST_C9_ARTIFACTS.intersection(text.split("## Shared Rules", 1)[0])


def test_promptset_c9_preserves_rich_producer_fields_without_renaming() -> None:
    c9_text = C9_PROMPT.read_text(encoding="utf-8")

    for artifact_name, producer_filename in RICH_PRODUCER_PROMPTS.items():
        producer_text = (PROMPT_ROOT / "prompts" / producer_filename).read_text(encoding="utf-8")
        assert _required_item_fields(c9_text, artifact_name) == _required_item_fields(
            producer_text, artifact_name
        )

    c9_schema_outputs = set(_schema_outputs(c9_text))
    assert "API_DASHBOARD_SURFACE.json" not in c9_schema_outputs
    assert "SECRETS_RISK_LOCATIONS.json" not in c9_schema_outputs


def test_promptset_c9_procedure_names_every_output_and_forbids_field_loss() -> None:
    text = C9_PROMPT.read_text(encoding="utf-8")
    procedure = _section(text, "Extraction Procedure")

    assert "CODE_MERGED" not in procedure
    assert "CODE_QA" not in procedure
    assert "Do not rename, remove, or replace producer fields" in procedure
    assert "API_DASHBOARD_SURFACE.json remains C7-owned" in procedure
    assert "SECRETS_RISK_LOCATIONS.json remains C8-owned" in procedure
    for artifact_name in C9_OUTPUTS:
        assert artifact_name in procedure
