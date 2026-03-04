from unittest.mock import Mock

from dopemux.claude_config import MCP_NAME_MAPPING
from dopemux.config.manager import ConfigManager
from dopemux.mcp.registry import MCPRegistry, MCPServerDefinition


def _iter_string_values(payload):
    if isinstance(payload, dict):
        for value in payload.values():
            yield from _iter_string_values(value)
    elif isinstance(payload, list):
        for value in payload:
            yield from _iter_string_values(value)
    elif isinstance(payload, str):
        yield payload


def test_template_mcp_names_exist_in_registry():
    """Template MCP names must resolve against canonical registry keys."""
    manager = ConfigManager()
    registry = MCPRegistry()
    registry_names = {server.name for server in registry.list_servers()}
    templates = manager._get_project_templates()
    template_aliases = {
        "conport",
        "serena",
        "claude-context",
        "pal",
        "morphllm-fast-apply",
    }

    for template_name, template in templates.items():
        for server_name in template.get("mcp_servers", []):
            resolved_name = MCP_NAME_MAPPING.get(server_name, server_name)
            assert (
                server_name in template_aliases
                or server_name in registry_names
                or resolved_name in registry_names
            ), f"Template '{template_name}' references unknown MCP server '{server_name}'"


def test_config_generation_docker_http_uses_bridge():
    """HTTP and HTTP-SSE servers should use the stdio-to-HTTP bridge in docker mode."""
    manager = ConfigManager()
    server = MCPServerDefinition(
        name="http-server",
        transport="http",
        docker={
            "service": "http-server",
            "compose_file": "compose.yml",
            "port": 8888,
        },
    )
    registry = Mock()
    registry.get_server.return_value = server

    config = manager._generate_server_config(
        registry,
        "http-server",
        "docker",
        docker_compose_bin="docker compose",
    )

    assert config is not None
    assert config["command"] == "python"
    assert config["args"] == [
        "-m",
        "dopemux.mcp.http_stdio_bridge",
        "--base-url",
        "http://localhost:8888",
    ]


def test_config_generation_docker_stdio_uses_compose_exec():
    """True stdio servers in docker mode must use docker compose exec -T."""
    manager = ConfigManager()
    server = MCPServerDefinition(
        name="stdio-server",
        transport="stdio",
        docker={
            "service": "stdio-service",
            "compose_file": "compose.yml",
            "exec": ["python", "-m", "stdio.server"],
        },
    )
    registry = Mock()
    registry.get_server.return_value = server

    config = manager._generate_server_config(
        registry,
        "stdio-server",
        "docker",
        docker_compose_bin="docker compose",
    )

    assert config is not None
    assert config["command"] == "docker"
    assert config["args"] == [
        "compose",
        "-f",
        "compose.yml",
        "exec",
        "-T",
        "stdio-service",
        "python",
        "-m",
        "stdio.server",
    ]


def test_no_host_paths_in_defaults():
    """Default config generation must never hardcode local absolute user paths."""
    manager = ConfigManager()
    defaults = manager._get_default_mcp_servers(
        mcp_mode="docker",
        docker_compose_bin="docker compose",
    )

    for server_name, config in defaults.items():
        for value in _iter_string_values(config):
            assert "/Users/" not in value, f"Found host path in {server_name}: {value}"
