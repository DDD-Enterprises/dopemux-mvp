"""Tests for the LiteLLMManager class."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

sys.modules.pop("dopemux", None)

from dopemux.litellm_manager import (
    LiteLLMManager,
    LiteLLMManagerError,
    LiteLLMProcessInfo,
    LiteLLMHealthMonitor,
    get_litellm_manager,
)


def test_litellm_manager_initialization(tmp_path):
    """Test that LiteLLMManager initializes correctly."""
    manager = LiteLLMManager(tmp_path)
    assert manager.project_root == tmp_path
    assert len(manager._processes) == 0


def test_start_instance_basic(tmp_path):
    """Test starting a basic LiteLLM instance."""
    manager = LiteLLMManager(tmp_path)
    
    config_data = {
        "model_list": [
            {
                "model_name": "test-model",
                "litellm_params": {
                    "model": "test/provider-model",
                    "api_key": "os.environ/TEST_API_KEY",
                },
            }
        ],
        "litellm_settings": {
            "timeout": 90,
            "max_retries": 2,
        },
    }
    
    # Mock subprocess and health check
    with patch("subprocess.Popen") as mock_popen, \
         patch.object(manager, "_is_port_in_use", return_value=False), \
         patch.object(manager, "_wait_for_health", return_value=True):
        
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        
        process_info = manager.start_instance(
            instance_id="test",
            port=4000,
            config_data=config_data,
            db_enabled=False,
        )
        
        assert process_info.instance_id == "test"
        assert process_info.port == 4000
        assert process_info.master_key.startswith("sk-")
        assert process_info.db_enabled == False
        assert len(manager._processes) == 1
        assert "test" in manager._processes


def test_start_instance_with_database(tmp_path):
    """Test starting a LiteLLM instance with database support."""
    manager = LiteLLMManager(tmp_path)
    
    config_data = {
        "model_list": [
            {
                "model_name": "test-model",
                "litellm_params": {
                    "model": "test/provider-model",
                    "api_key": "os.environ/TEST_API_KEY",
                },
            }
        ],
    }
    
    # Mock subprocess and health check
    with patch("subprocess.Popen") as mock_popen, \
         patch.object(manager, "_is_port_in_use", return_value=False), \
         patch.object(manager, "_wait_for_health", return_value=True):
        
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        
        process_info = manager.start_instance(
            instance_id="test-db",
            port=4001,
            config_data=config_data,
            db_enabled=True,
            db_url="postgresql://user:pass@localhost:5432/litellm",
        )
        
        assert process_info.db_enabled == True
        assert process_info.db_url == "postgresql://user:pass@localhost:5432/litellm"
        
        # Verify config was written with database URL
        config_path = tmp_path / ".dopemux" / "litellm" / "test-db" / "litellm.config.yaml"
        config_content = yaml.safe_load(config_path.read_text())
        assert "database_url" in config_content["general_settings"]


def test_stop_instance(tmp_path):
    """Test stopping a running instance."""
    manager = LiteLLMManager(tmp_path)
    
    # Start an instance first
    config_data = {
        "model_list": [
            {
                "model_name": "test-model",
                "litellm_params": {
                    "model": "test/provider-model",
                    "api_key": "os.environ/TEST_API_KEY",
                },
            }
        ],
    }
    
    with patch("subprocess.Popen") as mock_popen, \
         patch.object(manager, "_is_port_in_use", return_value=False), \
         patch.object(manager, "_wait_for_health", return_value=True):
        
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        
        manager.start_instance("test", 4000, config_data)
        assert len(manager._processes) == 1
        
        # Stop the instance
        result = manager.stop_instance("test")
        assert result == True
        assert len(manager._processes) == 0


def test_stop_nonexistent_instance(tmp_path):
    """Test stopping an instance that doesn't exist."""
    manager = LiteLLMManager(tmp_path)
    result = manager.stop_instance("nonexistent")
    assert result == False


def test_build_client_environment(tmp_path):
    """Test building client environment variables."""
    manager = LiteLLMManager(tmp_path)
    
    config_data = {
        "model_list": [
            {
                "model_name": "test-model",
                "litellm_params": {
                    "model": "test/provider-model",
                    "api_key": "os.environ/TEST_API_KEY",
                },
            }
        ],
    }
    
    with patch("subprocess.Popen") as mock_popen, \
         patch.object(manager, "_is_port_in_use", return_value=False), \
         patch.object(manager, "_wait_for_health", return_value=True):
        
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        
        manager.start_instance("test", 4000, config_data)
        
        # Build environment
        env_vars = manager.build_client_environment("test")
        
        assert "OPENAI_API_BASE" in env_vars
        assert "ANTHROPIC_API_KEY" in env_vars
        assert "DOPEMUX_LITELLM_MASTER_KEY" in env_vars
        assert env_vars["OPENAI_API_BASE"] == "http://127.0.0.1:4000"


def test_get_litellm_manager_singleton():
    """Test that get_litellm_manager returns a singleton."""
    manager1 = get_litellm_manager(Path("/test/path1"))
    manager2 = get_litellm_manager(Path("/test/path2"))
    
    assert manager1 is manager2
    assert manager1.project_root == Path("/test/path1")  # First call wins


def test_port_conflict(tmp_path):
    """Test handling of port conflicts."""
    manager = LiteLLMManager(tmp_path)
    
    config_data = {
        "model_list": [
            {
                "model_name": "test-model",
                "litellm_params": {
                    "model": "test/provider-model",
                    "api_key": "os.environ/TEST_API_KEY",
                },
            }
        ],
    }
    
    # Mock port as in use
    with patch.object(manager, "_is_port_in_use", return_value=True):
        try:
            manager.start_instance("test", 4000, config_data)
            assert False, "Should have raised LiteLLMManagerError"
        except LiteLLMManagerError as e:
            assert "already in use" in str(e)


def test_health_monitoring(tmp_path):
    """Test the health monitoring functionality."""
    manager = LiteLLMManager(tmp_path)
    monitor = LiteLLMHealthMonitor(manager)
    
    # Test that monitor can be started and stopped
    monitor.start()
    assert monitor._thread.is_alive()
    
    monitor.stop()
    monitor._thread.join(timeout=1.0)
    assert not monitor._thread.is_alive()


def test_master_key_generation(tmp_path):
    """Test master key generation and persistence."""
    manager = LiteLLMManager(tmp_path)
    instance_dir = tmp_path / ".dopemux" / "litellm" / "test"
    instance_dir.mkdir(parents=True, exist_ok=True)
    
    # First call should generate a new key
    key1 = manager._ensure_master_key(instance_dir)
    assert key1.startswith("sk-")
    
    # Second call should return the same key
    key2 = manager._ensure_master_key(instance_dir)
    assert key1 == key2
    
    # Verify key was written to file
    key_path = instance_dir / "master.key"
    assert key_path.exists()
    assert key_path.read_text().strip() == key1


def test_config_preparation(tmp_path):
    """Test configuration file preparation."""
    manager = LiteLLMManager(tmp_path)
    instance_dir = tmp_path / ".dopemux" / "litellm" / "test"
    instance_dir.mkdir(parents=True, exist_ok=True)
    
    config_data = {
        "model_list": [
            {
                "model_name": "test-model",
                "litellm_params": {
                    "model": "test/provider-model",
                },
            }
        ],
    }
    
    config_path = manager._prepare_config(
        instance_dir=instance_dir,
        config_data=config_data,
        master_key="test-key-123",
        db_enabled=False,
        db_url=None,
    )
    
    assert config_path.exists()
    config_content = yaml.safe_load(config_path.read_text())
    assert config_content["general_settings"]["master_key"] == "test-key-123"
    assert "database_url" not in config_content["general_settings"]


def test_get_health_status(tmp_path):
    """Test getting health status of managed instances."""
    manager = LiteLLMManager(tmp_path)
    
    config_data = {
        "model_list": [
            {
                "model_name": "test-model",
                "litellm_params": {
                    "model": "test/provider-model",
                    "api_key": "os.environ/TEST_API_KEY",
                },
            }
        ],
    }
    
    with patch("subprocess.Popen") as mock_popen, \
         patch.object(manager, "_is_port_in_use", return_value=False), \
         patch.object(manager, "_wait_for_health", return_value=True):
        
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        
        manager.start_instance("test1", 4000, config_data)
        manager.start_instance("test2", 4001, config_data)
        
        health_status = manager.get_health_status()
        
        assert "test1" in health_status
        assert "test2" in health_status
        assert health_status["test1"]["port"] == 4000
        assert health_status["test2"]["port"] == 4001


def test_stop_all_instances(tmp_path):
    """Test stopping all running instances."""
    manager = LiteLLMManager(tmp_path)
    
    config_data = {
        "model_list": [
            {
                "model_name": "test-model",
                "litellm_params": {
                    "model": "test/provider-model",
                    "api_key": "os.environ/TEST_API_KEY",
                },
            }
        ],
    }
    
    with patch("subprocess.Popen") as mock_popen, \
         patch.object(manager, "_is_port_in_use", return_value=False), \
         patch.object(manager, "_wait_for_health", return_value=True):
        
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        
        # Start multiple instances
        manager.start_instance("test1", 4000, config_data)
        manager.start_instance("test2", 4001, config_data)
        assert len(manager._processes) == 2
        
        # Stop all
        manager.stop_all_instances()
        assert len(manager._processes) == 0


def test_instance_already_running(tmp_path):
    """Test handling of already running instance."""
    manager = LiteLLMManager(tmp_path)
    
    config_data = {
        "model_list": [
            {
                "model_name": "test-model",
                "litellm_params": {
                    "model": "test/provider-model",
                    "api_key": "os.environ/TEST_API_KEY",
                },
            }
        ],
    }
    
    with patch("subprocess.Popen") as mock_popen, \
         patch.object(manager, "_is_port_in_use", return_value=False), \
         patch.object(manager, "_wait_for_health", return_value=True):
        
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        
        # Start instance
        manager.start_instance("test", 4000, config_data)
        
        # Try to start again - should raise error
        try:
            manager.start_instance("test", 4000, config_data)
            assert False, "Should have raised LiteLLMManagerError"
        except LiteLLMManagerError as e:
            assert "already running" in str(e)


def test_health_check_failure(tmp_path):
    """Test handling of health check failure."""
    manager = LiteLLMManager(tmp_path)
    
    config_data = {
        "model_list": [
            {
                "model_name": "test-model",
                "litellm_params": {
                    "model": "test/provider-model",
                    "api_key": "os.environ/TEST_API_KEY",
                },
            }
        ],
    }
    
    with patch("subprocess.Popen") as mock_popen, \
         patch.object(manager, "_is_port_in_use", return_value=False), \
         patch.object(manager, "_wait_for_health", return_value=False):
        
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        
        try:
            manager.start_instance("test", 4000, config_data)
            assert False, "Should have raised LiteLLMManagerError"
        except LiteLLMManagerError as e:
            assert "failed to become healthy" in str(e)
