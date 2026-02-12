import pytest
from unittest.mock import MagicMock, patch
from dopemux.config.manager import ConfigManager

@pytest.fixture
def mock_registry():
    """Mock the MCP registry for testing."""
    with patch("dopemux.config.manager.MCPRegistry") as MockRegistry:
        registry_instance = MockRegistry.return_value
        
        # Setup mock server definition
        mock_server = MagicMock()
        mock_server.name = "test-server"
        mock_server.transport = "http"
        mock_server.docker.service = "test-service"
        mock_server.docker.port = 8888
        mock_server.docker.compose_file = "docker-compose.yml"
        # Important: set local to None to avoid MagicMock concatenation errors
        mock_server.local = None
        
        registry_instance.get_server.return_value = mock_server
        yield registry_instance

def test_config_generation_docker_http(mock_registry):
    """Test config generation for HTTP server in Docker mode."""
    # Mock _detect_docker_mode to return True
    with patch.object(ConfigManager, "_detect_docker_mode", return_value=True):
        manager = ConfigManager()
        
        # Test _generate_server_config directly
        config = manager._generate_server_config(mock_registry, "test-server", "docker")
        
        assert config is not None
        assert config["command"] == "python"
        assert "-m" in config["args"]
        assert "dopemux.mcp.http_stdio_bridge" in config["args"]
        assert "--base-url" in config["args"]
        assert "http://localhost:8888" in config["args"]

def test_config_generation_docker_stdio(mock_registry):
    """Test config generation for stdio server in Docker mode."""
    mock_server = mock_registry.get_server.return_value
    mock_server.transport = "stdio"
    
    with patch.object(ConfigManager, "_detect_docker_mode", return_value=True):
        manager = ConfigManager()
        config = manager._generate_server_config(mock_registry, "test-server", "docker")
        
        assert config is not None
        assert config["command"] == "docker"
        assert "compose" in config["args"]
        assert "exec" in config["args"]
        assert "-T" in config["args"]
        assert "test-service" in config["args"]

def test_no_host_paths_in_defaults():
    """Test that default configuration does not contain host-specific paths."""
    config_manager = ConfigManager()
    defaults = config_manager._get_default_mcp_servers()
    
    for name, config in defaults.items():
        args = config.get("args", [])
        
        for arg in args:
            if isinstance(arg, str):
                assert "/Users/" not in arg, f"Found host path in {name}: {arg}"
