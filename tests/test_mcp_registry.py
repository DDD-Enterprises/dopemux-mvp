from dopemux.mcp.registry import MCPRegistry


def test_registry_loading():
    """Registry should load from canonical in-repo YAML."""
    registry = MCPRegistry()
    assert len(registry.list_servers()) > 0


def test_registry_contains_required_servers():
    """Canonical keys required by config generation should exist."""
    registry = MCPRegistry()
    required = {
        "dopemux-conport",
        "dopemux-serena",
        "dopemux-desktop-commander",
        "dopemux-gpt-researcher",
        "dopemux-leantime-bridge",
        "dopemux-dope-context",
    }
    available = {server.name for server in registry.list_servers()}
    missing = required - available
    assert not missing, f"Missing required MCP entries: {sorted(missing)}"


def test_server_definition_schema():
    """Each server entry should satisfy transport requirements."""
    registry = MCPRegistry()
    for server in registry.list_servers():
        assert server.transport in {"http", "http-sse", "stdio"}
        if server.transport in {"http", "http-sse"}:
            assert server.docker is not None
            assert server.docker.port is not None
        if server.transport == "stdio":
            has_local = bool(server.local and server.local.command)
            has_docker_exec = bool(server.docker and server.docker.exec)
            assert has_local or has_docker_exec


def test_registry_uniqueness():
    """Registry names must remain unique."""
    registry = MCPRegistry()
    names = [server.name for server in registry.list_servers()]
    assert len(names) == len(set(names))
