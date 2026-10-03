"""Invariant tests for the development model-routing governance policy.

Covers:
  * config/ai/model-routing.policy.yaml  (stages, provider_routes, proof reqs)
  * .github/agents/*.agent.md            (tool-scope invariants per stage lane)

These are governance invariants, not runtime behavior: read/plan/review/audit
lanes must not be able to edit or execute, and OpenRouter must stay a broker.
"""

import json
from pathlib import Path
import tomllib

import pytest
import yaml

pytestmark = pytest.mark.config

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPO_ROOT / "config" / "ai" / "model-routing.policy.yaml"
AGENTS_DIR = REPO_ROOT / ".github" / "agents"

EXPECTED_STAGES = {
    "cheap_read",
    "investigation",
    "planner_strong",
    "implementer_standard",
    "judge_strong",
    "self_audit",
}
EXPECTED_PROVIDERS = {
    "codex",
    "copilot",
    "claude_code",
    "agy",
    "gemini_cli",
    "xai",
    "moonshot",
    "openrouter",
}
EXPECTED_VERDICTS = {"PASS", "PASS_WITH_RISKS", "FAIL", "NEEDS_SUPERVISOR", "SKIPPED"}

# Lanes that must never carry edit/execute tools.
READ_ONLY_AGENTS = {
    "dopemux-reader",
    "dopemux-planner",
    "dopemux-reviewer",
    "dopemux-auditor",
}
# Lanes that are allowed to edit (scoped by packet/allowlist in their own body).
EDIT_AGENTS = {"dopemux-implementer", "dopemux-testgen"}


def _load_policy() -> dict:
    assert POLICY_PATH.exists(), f"missing policy file: {POLICY_PATH}"
    return yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))


def _agent_frontmatter(name: str) -> dict:
    path = AGENTS_DIR / f"{name}.agent.md"
    assert path.exists(), f"missing agent file: {path}"
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0].strip() == "---", f"{path} has no YAML frontmatter"
    # closing fence is the next line that is exactly '---'
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    assert end is not None, f"{path} frontmatter is not closed"
    data = yaml.safe_load("\n".join(lines[1:end]))
    assert isinstance(data, dict), f"{path} frontmatter did not parse to a mapping"
    return data


def test_policy_parses_and_has_core_shape():
    policy = _load_policy()
    assert policy["version"] == 1
    assert policy["status"] == "proposed_governance_policy"
    assert policy["authority"] == "advisory_until_runtime_wiring_verified"
    principles = set(policy.get("principles", []))
    assert "openrouter_is_broker_not_model_family" in principles
    assert "cheap_reads_are_not_cheap_decisions" in principles


def test_all_stages_present():
    policy = _load_policy()
    assert EXPECTED_STAGES.issubset(set(policy["stages"]))


def test_all_providers_present():
    policy = _load_policy()
    assert EXPECTED_PROVIDERS.issubset(set(policy["provider_routes"]))


def test_openrouter_notes_identify_it_as_broker():
    openrouter = _load_policy()["provider_routes"]["openrouter"]
    notes = openrouter.get("notes", [])
    assert any("BROKER" in note or "broker" in note for note in notes), (
        "openrouter provider_routes entry must note it is a broker"
    )


def test_openrouter_is_named_but_inactive():
    # Contract risk: openrouter block/enum value must never be deleted, but
    # it must be marked inactive now that cheaperinference is the live broker.
    openrouter = _load_policy()["provider_routes"]["openrouter"]
    assert openrouter.get("active") is False, (
        "openrouter provider_routes entry must be marked active: false"
    )
    assert openrouter.get("role") == "broker"


def test_cheaperinference_is_the_active_broker():
    policy = _load_policy()
    assert "cheaperinference" in policy["provider_routes"], (
        "cheaperinference must be present as a provider_routes broker entry"
    )
    cheaperinference = policy["provider_routes"]["cheaperinference"]
    assert cheaperinference.get("active") is True
    assert cheaperinference.get("role") == "broker"
    assert cheaperinference.get("base_url") == "https://api.cheaperinference.com/v1"
    assert cheaperinference.get("api_key_env") == "CHEAPERINFERENCE_API_KEY"
    notes = cheaperinference.get("notes", [])
    assert any("broker" in note or "BROKER" in note for note in notes), (
        "cheaperinference provider_routes entry must note it is a broker"
    )


def test_cheaperinference_capabilities_are_honestly_stated():
    capabilities = _load_policy()["provider_routes"]["cheaperinference"]["capabilities"]
    assert capabilities["fallback"] == "supported"
    assert capabilities["price_caps"] == "supported"
    # Single-upstream broker: no per-request ZDR/data-policy selector or
    # underlying-provider diversity/order control, unlike OpenRouter.
    assert capabilities["zdr_filtering"] == "not_supported"
    assert capabilities["provider_order"] == "not_supported"


def test_read_lanes_may_not_edit_or_decide():
    stages = _load_policy()["stages"]
    for stage in (
        "cheap_read",
        "investigation",
        "planner_strong",
        "judge_strong",
        "self_audit",
    ):
        assert stages[stage].get("may_edit") is False, f"{stage} must not be able to edit"
    # cheap/investigation explicitly may not decide
    assert stages["cheap_read"].get("may_decide") is False
    assert stages["investigation"].get("may_decide") is False


def test_implementer_slot_requires_approved_packet_and_allowlist():
    stage = _load_policy()["stages"]["implementer_standard"]
    assert stage["may_edit"] is True
    requires = stage.get("requires", [])
    assert any("approved task packet" in str(r) for r in requires), (
        "implementer_standard must require an approved task packet"
    )
    assert any("allowlist" in str(r) for r in requires), (
        "implementer_standard must require a file allowlist"
    )


def test_self_audit_verdicts_match_embedded_audit_schema():
    stage = _load_policy()["stages"]["self_audit"]
    assert EXPECTED_VERDICTS.issubset(set(stage["verdict_values"]))


def test_copilot_routes_reference_agent_files_that_exist():
    copilot = _load_policy()["provider_routes"]["copilot"]
    for stage, ref in copilot.items():
        if not isinstance(ref, str):
            continue  # skip the notes list
        assert ref.endswith(".agent.md"), f"copilot {stage} should map to an agent file"
        assert (REPO_ROOT / ref).exists(), f"referenced agent file missing: {ref}"


def test_read_only_agents_have_no_edit_or_execute_tools():
    for name in READ_ONLY_AGENTS:
        tools = set(_agent_frontmatter(name)["tools"])
        assert "edit" not in tools, f"{name} must not have the edit tool"
        assert "execute" not in tools, f"{name} must not have the execute tool"


def test_edit_agents_have_edit_tool():
    for name in EDIT_AGENTS:
        tools = set(_agent_frontmatter(name)["tools"])
        assert "edit" in tools, f"{name} should have the edit tool"


@pytest.mark.parametrize("key", ["default_subagent_model", "default_subagent_reasoning_effort"])
def test_codex_subagents_have_explicit_economical_defaults(key):
    config = tomllib.loads((REPO_ROOT / ".codex/config.toml").read_text())
    assert config["agents"].get(key), f"missing explicit {key}; expensive inheritance risk"
    assert config["agents"]["default_subagent_model"] == "gpt-6-luna"
    assert config["agents"]["default_subagent_reasoning_effort"] == "medium"


@pytest.mark.parametrize("provider", ["codex"])
def test_declared_role_routes_resolve_and_match_pins(provider):
    routes = _load_policy()["provider_routes"][provider]
    for role, route in routes["role_models"].items():
        path = REPO_ROOT / route["file"]
        assert path.is_file(), f"missing role {role}: {path}"
        text = path.read_text()
        if provider == "codex":
            data = tomllib.loads(text)
            assert data.get("model") == route["model"]
            assert data.get("model_reasoning_effort") == route["effort"]
            assert data["model"] != "inherit"
            assert "astra" not in data["model"].lower()
        else:
            data = yaml.safe_load(text.split("---", 2)[1])
            assert data.get("model") == route["model"]
            assert data["model"] != "inherit"
    for stage in EXPECTED_STAGES - {"self_audit"}:
        assert (REPO_ROOT / routes[stage]).is_file()


@pytest.mark.parametrize("role", ["dmx-explorer", "dmx-housekeeper", "dmx-reviewer"])
def test_dmx_evidence_roles_preserve_read_only_boundary(role):
    data = tomllib.loads((REPO_ROOT / f".codex/agents/{role}.toml").read_text())
    assert data["sandbox_mode"] == "read-only"
    assert "Do not edit files" in data["developer_instructions"] or "editing files" in data["developer_instructions"]


def test_codex_review_cannot_be_promoted_to_formal_audit():
    routes = _load_policy()["provider_routes"]
    assert routes["codex"]["self_audit"] == "FORBIDDEN_FORMAL_AUDITOR"
    reviewer = tomllib.loads((REPO_ROOT / routes["codex"]["judge_strong"]).read_text())
    assert "Advisory code review only" in reviewer["developer_instructions"]
    assert "never the formal embedded auditor" in reviewer["developer_instructions"]
    schema = json.loads((REPO_ROOT / "schemas/proof/embedded_audit.schema.json").read_text())
    assert routes["claude_code"]["self_audit"] in schema["properties"]["auditor_model"]["enum"]


def test_cost_first_policy_preserves_evidence_economy_budget():
    policy = _load_policy()
    assert "cheapest_adequate_qualified_model" in policy["principles"]
    assert "lowest_sufficient_supported_effort" in policy["principles"]
    for lane in ("L2_material", "L3_red_lane"):
        budget = policy["evidence_economy"]["lanes"][lane]
        assert budget["implementer_model_calls"] == 1
        assert budget["auditor_model_calls"] == 1
