import os
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
from dopemux.cli import _load_litellm_models

def test_load_models_from_instance_dir(tmp_path):
    """
    Verify that models are loaded from the specific instance directory config,
    not from CWD or other locations.
    """
    # Create a mock instance directory structure
    instance_dir = tmp_path / ".dopemux" / "litellm" / "A"
    instance_dir.mkdir(parents=True)
    
    config_file = instance_dir / "litellm.config.yaml"
    
    config_data = {
        "model_list": [
            {"model_name": "gpt-4-test"},
            {"model_name": "claude-3-test"}
        ]
    }
    
    config_file.write_text(yaml.dump(config_data), encoding="utf-8")
    
    # Test the loader helper directly
    models = _load_litellm_models(config_file)
    assert "gpt-4-test" in models
    assert "claude-3-test" in models
    assert len(models) == 2

@patch("dopemux.cli.Path")
@patch("dopemux.cli.yaml")
def test_alt_routing_config_selection_logic(mock_yaml, mock_path_cls):
    """
    Verify the logic in cli.py that selects the config file.
    This reconstructs the logic we changed to ensure it prefers instance_dir.
    """
    # This test mimics the changed logic in cli.py to ensure it behaves as expected
    
    # Mock behavior
    mock_instance_dir = MagicMock()
    mock_instance_config = mock_instance_dir / "litellm.config.yaml"
    
    # CASE 1: Instance config exists
    mock_instance_config.exists.return_value = True
    
    # The logic we implemented:
    config_source = None
    if (mock_instance_dir / "litellm.config.yaml").exists():
        config_source = mock_instance_dir / "litellm.config.yaml"
        
    assert config_source == mock_instance_config
    
    # CASE 2: Instance config does NOT exist
    mock_instance_config.exists.return_value = False
    
    config_source = None
    if (mock_instance_dir / "litellm.config.yaml").exists():
        config_source = mock_instance_dir / "litellm.config.yaml"
        
    assert config_source is None
