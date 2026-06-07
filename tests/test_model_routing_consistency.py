"""Cross-artifact consistency tests for model routing governance.

Validates that stages defined in config/ai/model-routing.schema.json
remain consistent across:
  - config/ai/model-routing.policy.yaml
  - task-packets/TEMPLATE_TASK_PACKET.md
  - AGENTS.md
  - .github/agents/*.agent.md

Fail closed: missing files or missing stage references are errors.
"""

import json
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.config

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "config" / "ai" / "model-routing.schema.json"
POLICY_PATH = REPO_ROOT / "config" / "ai" / "model-routing.policy.yaml"
TEMPLATE_PATH = REPO_ROOT / "task-packets" / "TEMPLATE_TASK_PACKET.md"
AGENTS_MD_PATH = REPO_ROOT / "AGENTS.md"
AGENTS_DIR = REPO_ROOT / ".github" / "agents"


def _load_schema() -> dict:
    assert SCHEMA_PATH.exists(), f"routing schema missing: {SCHEMA_PATH}"
    data = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert "stages" in data, "schema must have a 'stages' key"
    assert isinstance(data["stages"], list), "schema 'stages' must be a list"
    assert data["stages"], "schema 'stages' must not be empty"
    return data


def _load_policy() -> dict:
    assert POLICY_PATH.exists(), f"policy file missing: {POLICY_PATH}"
    return yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))


CANONICAL_STAGES = frozenset(
    {
        "cheap_read",
        "investigation",
        "planner_strong",
        "implementer_standard",
        "judge_strong",
        "self_audit",
    }
)


def test_schema_loads_and_has_canonical_stages():
    schema = _load_schema()
    assert set(schema["stages"]) == CANONICAL_STAGES, (
        f"schema stages {set(schema['stages'])} do not match canonical set {CANONICAL_STAGES}"
    )


def test_schema_stages_match_policy_yaml_exactly():
    schema_stages = set(_load_schema()["stages"])
    policy_stages = set(_load_policy()["stages"].keys())
    only_in_schema = schema_stages - policy_stages
    only_in_policy = policy_stages - schema_stages
    assert not only_in_schema, f"stages in schema but not in policy YAML: {only_in_schema}"
    assert not only_in_policy, f"stages in policy YAML but not in schema: {only_in_policy}"


def test_template_references_all_schema_stages():
    schema_stages = _load_schema()["stages"]
    assert TEMPLATE_PATH.exists(), f"template missing: {TEMPLATE_PATH}"
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    missing = [s for s in schema_stages if s not in text]
    assert not missing, (
        f"{TEMPLATE_PATH.name} is missing stage references: {missing}. "
        "Add all stage names to the Model Routing Record section."
    )


def test_agents_md_references_policy_file():
    assert AGENTS_MD_PATH.exists(), f"AGENTS.md missing: {AGENTS_MD_PATH}"
    text = AGENTS_MD_PATH.read_text(encoding="utf-8")
    assert "config/ai/model-routing.policy.yaml" in text, (
        "AGENTS.md must reference config/ai/model-routing.policy.yaml"
    )


def test_copilot_routed_agents_reference_their_stage():
    schema_stages = set(_load_schema()["stages"])
    copilot = _load_policy()["provider_routes"]["copilot"]
    # Build agent-file → stages-it-is-mapped-to, only for schema-known stages.
    agent_stage_map: dict[str, set[str]] = {}
    for stage, ref in copilot.items():
        if not isinstance(ref, str) or not ref.endswith(".agent.md"):
            continue
        if stage not in schema_stages:
            continue
        agent_stage_map.setdefault(ref, set()).add(stage)

    for agent_ref, mapped_stages in agent_stage_map.items():
        agent_path = REPO_ROOT / agent_ref
        assert agent_path.exists(), f"agent file missing: {agent_path}"
        text = agent_path.read_text(encoding="utf-8")
        found = {s for s in mapped_stages if s in text}
        assert found, (
            f"{agent_path.name} is mapped to stages {sorted(mapped_stages)} in copilot "
            "routes but references none of them — add the stage name as a comment or "
            "inline reference so drift is detectable"
        )


def test_no_unknown_stages_in_policy():
    schema_stages = set(_load_schema()["stages"])
    policy_stages = set(_load_policy()["stages"].keys())
    unknown = policy_stages - schema_stages
    assert not unknown, f"unknown stages in policy (not in schema): {unknown}"


def test_no_missing_stages_in_policy():
    schema_stages = set(_load_schema()["stages"])
    policy_stages = set(_load_policy()["stages"].keys())
    missing = schema_stages - policy_stages
    assert not missing, f"stages missing from policy (present in schema): {missing}"
