from dopemux.mcp.registry import MCPRegistry

def test_registry_loading():
    """Test that the registry loads correctly from the default file."""
    registry = MCPRegistry()
    assert len(registry.list_servers()) > 0
    
    # Check for critical servers
    assert registry.get_server("conport") is not None
    assert registry.get_server("serena") is not None
    assert registry.get_server("claude-context") is not None
    
def test_server_definition_schema():
    """Test that server definitions have the expected fields."""
    registry = MCPRegistry()
    conport = registry.get_server("conport")
    assert conport.transport == "http"
    assert conport.docker.service == "conport"
    assert conport.docker.port == 3004
    assert conport.docker.health_url == "http://localhost:3004/health"

def test_registry_uniqueness():
    """Test that names are unique (implicitly true by dict storage, but good to check count)."""
    registry = MCPRegistry()
    names = [s.name for s in registry.list_servers()]
    assert len(names) == len(set(names))
