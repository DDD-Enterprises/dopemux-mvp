import json

import pytest

from clink import get_registry
from clink.agents import AgentOutput
from clink.parsers.base import ParsedCLIResponse
from clink.registry import ClinkRegistry
from tools.clink import MAX_RESPONSE_CHARS, CLinkTool


@pytest.mark.asyncio
async def test_clink_tool_execute(monkeypatch):
    tool = CLinkTool()

    async def fake_run(**kwargs):
        return AgentOutput(
            parsed=ParsedCLIResponse(content="Hello from Gemini", metadata={"model_used": "gemini-2.5-pro"}),
            sanitized_command=["gemini", "-o", "json"],
            returncode=0,
            stdout='{"response": "Hello from Gemini"}',
            stderr="",
            duration_seconds=0.42,
            parser_name="gemini_json",
            output_file_content=None,
        )

    class DummyAgent:
        async def run(self, **kwargs):
            return await fake_run(**kwargs)

    def fake_create_agent(client):
        return DummyAgent()

    monkeypatch.setattr("tools.clink.create_agent", fake_create_agent)

    arguments = {
        "prompt": "Summarize the project",
        "cli_name": "gemini",
        "role": "default",
        "files": [],
        "images": [],
    }

    results = await tool.execute(arguments)
    assert len(results) == 1

    payload = json.loads(results[0].text)
    assert payload["status"] in {"success", "continuation_available"}
    assert "Hello from Gemini" in payload["content"]
    metadata = payload.get("metadata", {})
    assert metadata.get("cli_name") == "gemini"
    assert metadata.get("command") == ["gemini", "-o", "json"]


def test_registry_lists_roles():
    registry = get_registry()
    clients = registry.list_clients()
    assert {"codex", "gemini"}.issubset(set(clients))
    roles = registry.list_roles("gemini")
    assert "default" in roles
    assert "default" in registry.list_roles("codex")


def test_registry_includes_test_specialist_role():
    registry = get_registry()
    for cli_name in ("gemini", "codex", "claude"):
        roles = registry.list_roles(cli_name)
        assert "test-specialist" in roles


@pytest.mark.asyncio
async def test_clink_tool_defaults_to_first_cli(monkeypatch):
    tool = CLinkTool()

    async def fake_run(**kwargs):
        return AgentOutput(
            parsed=ParsedCLIResponse(content="Default CLI response", metadata={"events": ["foo"]}),
            sanitized_command=["gemini"],
            returncode=0,
            stdout='{"response": "Default CLI response"}',
            stderr="",
            duration_seconds=0.1,
            parser_name="gemini_json",
            output_file_content=None,
        )

    class DummyAgent:
        async def run(self, **kwargs):
            return await fake_run(**kwargs)

    monkeypatch.setattr("tools.clink.create_agent", lambda client: DummyAgent())

    arguments = {
        "prompt": "Hello",
        "files": [],
        "images": [],
    }

    result = await tool.execute(arguments)
    payload = json.loads(result[0].text)
    metadata = payload.get("metadata", {})
    assert metadata.get("cli_name") == tool._default_cli_name
    assert metadata.get("events_removed_for_normal") is True


@pytest.mark.asyncio
async def test_clink_tool_truncates_large_output(monkeypatch):
    tool = CLinkTool()

    summary_section = "<SUMMARY>This is the condensed summary.</SUMMARY>"
    long_text = "A" * (MAX_RESPONSE_CHARS + 500) + summary_section

    async def fake_run(**kwargs):
        return AgentOutput(
            parsed=ParsedCLIResponse(content=long_text, metadata={"events": ["event1", "event2"]}),
            sanitized_command=["codex"],
            returncode=0,
            stdout="{}",
            stderr="",
            duration_seconds=0.2,
            parser_name="codex_jsonl",
            output_file_content=None,
        )

    class DummyAgent:
        async def run(self, **kwargs):
            return await fake_run(**kwargs)

    monkeypatch.setattr("tools.clink.create_agent", lambda client: DummyAgent())

    arguments = {
        "prompt": "Summarize",
        "cli_name": tool._default_cli_name,
        "files": [],
        "images": [],
    }

    result = await tool.execute(arguments)
    payload = json.loads(result[0].text)
    assert payload["status"] in {"success", "continuation_available"}
    assert payload["content"].strip() == "This is the condensed summary."
    metadata = payload.get("metadata", {})
    assert metadata.get("output_summarized") is True
    assert metadata.get("events_removed_for_normal") is True
    assert metadata.get("output_original_length") == len(long_text)


@pytest.mark.asyncio
async def test_clink_tool_truncates_without_summary(monkeypatch):
    tool = CLinkTool()

    long_text = "B" * (MAX_RESPONSE_CHARS + 1000)

    async def fake_run(**kwargs):
        return AgentOutput(
            parsed=ParsedCLIResponse(content=long_text, metadata={"events": ["event"]}),
            sanitized_command=["codex"],
            returncode=0,
            stdout="{}",
            stderr="",
            duration_seconds=0.2,
            parser_name="codex_jsonl",
            output_file_content=None,
        )

    class DummyAgent:
        async def run(self, **kwargs):
            return await fake_run(**kwargs)

    monkeypatch.setattr("tools.clink.create_agent", lambda client: DummyAgent())

    arguments = {
        "prompt": "Summarize",
        "cli_name": tool._default_cli_name,
        "files": [],
        "images": [],
    }

    result = await tool.execute(arguments)
    payload = json.loads(result[0].text)
    assert payload["status"] in {"success", "continuation_available"}
    assert "exceeding the configured clink limit" in payload["content"]
    metadata = payload.get("metadata", {})
    assert metadata.get("output_truncated") is True
    assert metadata.get("events_removed_for_normal") is True
    assert metadata.get("output_original_length") == len(long_text)


def test_clink_tool_omits_readonly_hint_while_configs_carry_mutation_flags(monkeypatch, tmp_path):
    """CLinkTool must not advertise readOnlyHint=True while any shipped client
    config carries a mutation-capable flag.

    Test structure:
      1. PREMISE — using a fresh ClinkRegistry isolated from user overrides and
         env-injected paths, confirm at least one shipped client config still
         carries a known mutation flag. If this premise ever stops holding (e.g.,
         configs are cleaned up upstream), the assertion fails loudly so the
         get_annotations() decision can be revisited.
      2. CONTRACT — CLinkTool.get_annotations() must not assert readOnlyHint=True.
    """
    # Isolate the registry from user overrides (~/.zen/cli_clients) and any
    # CLI_CLIENTS_CONFIG_PATH the developer/CI happens to set, so the premise
    # check sees only the shipped configs.
    monkeypatch.delenv("CLI_CLIENTS_CONFIG_PATH", raising=False)
    monkeypatch.setattr("clink.registry.USER_CONFIG_DIR", tmp_path / "no_user_configs")

    registry = ClinkRegistry()

    # Mutation flags known to ship in conf/cli_clients/{claude,gemini,codex}.json.
    # Single-token flags: presence is enough. Pair-form flags require matching value.
    single_token_mutation_flags = {"--yolo", "--dangerously-bypass-approvals-and-sandbox"}
    pair_form_mutation_flags = {("--permission-mode", "acceptEdits")}

    def carries_mutation_flag(args: list[str]) -> bool:
        if any(flag in args for flag in single_token_mutation_flags):
            return True
        for i in range(len(args) - 1):
            if (args[i], args[i + 1]) in pair_form_mutation_flags:
                return True
        return False

    offenders: list[str] = []
    for name in registry.list_clients():
        client = registry.get_client(name)
        client_args = list(client.internal_args) + list(client.config_args)
        if carries_mutation_flag(client_args):
            offenders.append(name)
            continue
        for role_name, role in client.roles.items():
            if carries_mutation_flag(list(role.role_args)):
                offenders.append(f"{name}:{role_name}")
                break

    assert offenders, (
        "Premise no longer holds: no shipped CLI client config in conf/cli_clients/ "
        "carries a known mutation flag. If configs were intentionally cleaned, "
        "revisit CLinkTool.get_annotations() — it currently returns None precisely "
        "because shipped configs are mutation-capable."
    )

    tool = CLinkTool()
    annotations = tool.get_annotations()
    assert annotations is None or not annotations.get("readOnlyHint"), (
        f"CLinkTool.get_annotations() must not assert readOnlyHint=True while "
        f"shipped configs carry mutation flags ({offenders}). Got: {annotations!r}"
    )
