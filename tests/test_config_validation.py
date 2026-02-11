import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from dopemux.claude_config import ClaudeConfig, ClaudeConfigError

class TestConfigValidation:
    
    @pytest.fixture
    def mock_path(self):
        return MagicMock(spec=Path)

    def test_validate_structure_valid(self):
        """Test validation with valid config."""
        config_obj = ClaudeConfig()
        valid_config = {
            "mcpServers": {
                "server1": {"command": "test"}
            }
        }
        # Should not raise
        config_obj._validate_config_structure(valid_config)

    def test_validate_structure_invalid_type(self):
        """Test validation with non-dict config."""
        config_obj = ClaudeConfig()
        with pytest.raises(ClaudeConfigError, match="Configuration must be a dictionary"):
            config_obj._validate_config_structure(["not", "a", "dict"])

    def test_validate_structure_invalid_mcp_section(self):
        """Test validation with invalid mcpServers section."""
        config_obj = ClaudeConfig()
        invalid_config = {
            "mcpServers": ["not", "a", "dict"]
        }
        with pytest.raises(ClaudeConfigError, match="'mcpServers' must be a dictionary"):
            config_obj._validate_config_structure(invalid_config)

    def test_validate_structure_invalid_server_config(self):
        """Test validation with invalid server config."""
        config_obj = ClaudeConfig()
        invalid_config = {
            "mcpServers": {
                "server1": "not a dict"
            }
        }
        with pytest.raises(ClaudeConfigError, match="Configuration for MCP server 'server1' must be a dictionary"):
            config_obj._validate_config_structure(invalid_config)

    @patch('dopemux.claude_config.open')
    @patch('dopemux.claude_config.Path.replace')
    def test_write_config_validates(self, mock_replace, mock_open, tmp_path):
        """Test that write_config calls validation."""
        # Setup
        config_path = tmp_path / "settings.json"
        config_obj = ClaudeConfig(config_path)
        
        # Mock invalid logic to ensure validation catches it before writing
        # But here we just pass valid config and verify flow, 
        # or pass invalid data types to see it fail early.
        
        invalid_data = ["not a dict"]
        
        # Should raise before even trying to open file
        with pytest.raises(ClaudeConfigError):
            config_obj.write_config(invalid_data)
            
        # Verify open was NOT called (validation happens first)
        mock_open.assert_not_called()

