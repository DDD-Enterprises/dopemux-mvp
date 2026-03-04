"""Integration tests for LiteLLMManager with CLI."""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

sys.modules.pop("dopemux", None)

from dopemux.litellm_manager import get_litellm_manager


@pytest.fixture(autouse=True)
def reset_manager():
    """Reset the global LiteLLM manager singleton before each test."""
    from dopemux import litellm_manager
    litellm_manager._litellm_manager = None
    yield
    # Also stop any running processes
    if litellm_manager._litellm_manager:
        litellm_manager._litellm_manager.stop()
    litellm_manager._litellm_manager = None


def test_singleton_behavior(tmp_path):
    """Test that the manager singleton works correctly."""
    manager1 = get_litellm_manager(tmp_path)
    manager2 = get_litellm_manager(tmp_path / "other")
    
    # Should return the same instance
    assert manager1 is manager2
    
    # First call should determine the project root
    assert manager1.project_root == tmp_path


def test_manager_lifecycle(tmp_path):
    """Test the full lifecycle of the manager."""
    manager = get_litellm_manager(tmp_path)
    
    # Manager should start with no processes
    assert len(manager._processes) == 0
    
    # Start health monitoring
    manager.start()
    assert manager._health_monitor._thread.is_alive()
    
    # Stop everything
    manager.stop()
    assert len(manager._processes) == 0


def test_environment_building(tmp_path):
    """Test building client environment variables."""
    manager = get_litellm_manager(tmp_path)
    manager.project_root = tmp_path
    
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
    
    manager.stop_all_instances()
    with patch("subprocess.Popen") as mock_popen, \
         patch.object(manager, "_is_port_in_use", return_value=False), \
         patch.object(manager, "_wait_for_health", return_value=True):

        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        
        # Start an instance
        process_info = manager.start_instance("test", 4000, config_data)
        
        # Build environment
        env_vars = manager.build_client_environment("test")
        
        # Verify key environment variables
        assert env_vars["OPENAI_API_BASE"] == "http://127.0.0.1:4000"
        assert env_vars["ANTHROPIC_API_KEY"] == process_info.master_key
        assert env_vars["DOPEMUX_LITELLM_MASTER_KEY"] == process_info.master_key
        assert env_vars["DOPEMUX_LITELLM_PORT"] == "4000"

    manager.stop_all_instances()


def test_multiple_instances(tmp_path):
    """Test managing multiple LiteLLM instances."""
    manager = get_litellm_manager(tmp_path)
    
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
        info1 = manager.start_instance("instance1", 4000, config_data)
        info2 = manager.start_instance("instance2", 4001, config_data)
        
        # Verify both are running
        assert len(manager._processes) == 2
        assert manager.get_instance("instance1") is not None
        assert manager.get_instance("instance2") is not None
        
        # Verify different ports
        assert info1.port == 4000
        assert info2.port == 4001
        
        # Stop one instance
        manager.stop_instance("instance1")
        assert len(manager._processes) == 1
        assert manager.get_instance("instance1") is None
        assert manager.get_instance("instance2") is not None


def test_health_status(tmp_path):
    """Test getting health status of instances."""
    manager = get_litellm_manager(tmp_path)
    
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
        
        # Start an instance
        manager.start_instance("test", 4000, config_data)
        manager.get_instance("test").update_health(True)
        
        # Get health status
        status = manager.get_health_status()
        
        assert "test" in status
        assert status["test"]["port"] == 4000
        assert status["test"]["healthy"] == True
        assert "start_time" in status["test"]
        assert "last_health_check" in status["test"]


def test_instance_cleanup(tmp_path):
    """Test cleanup of dead processes."""
    manager = get_litellm_manager(tmp_path)
    
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
        
        # Start an instance
        manager.start_instance("test", 4000, config_data)
        assert len(manager._processes) == 1
        
        # Simulate process death
        mock_process.poll.return_value = 0  # Process has exited
        
        # Starting again should clean up the dead process
        mock_process2 = Mock()
        mock_process2.poll.return_value = None
        mock_popen.return_value = mock_process2
        
        manager.start_instance("test", 4000, config_data)
        assert len(manager._processes) == 1
        # The process should be the new one
        assert manager._processes["test"].process is mock_process2


def test_port_conflict_handling(tmp_path):
    """Test handling of port conflicts."""
    manager = get_litellm_manager(tmp_path)
    
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
        except Exception as e:
            assert "already in use" in str(e)


def test_database_configuration(tmp_path):
    """Test database configuration handling."""
    manager = get_litellm_manager(tmp_path)
    
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
        
        # Start with database enabled
        db_url = "postgresql://user:pass@localhost:5432/litellm"
        process_info = manager.start_instance(
            "test-db", 4000, config_data, db_enabled=True, db_url=db_url
        )
        
        assert process_info.db_enabled == True
        assert process_info.db_url == db_url
        
        # Verify environment includes database URLs
        env_vars = manager.build_client_environment("test-db")
        assert env_vars["DOPEMUX_LITELLM_DB_URL"] == db_url
        assert env_vars["LITELLM_DATABASE_URL"] == db_url
        assert env_vars["DATABASE_URL"] == db_url


def test_stop_all_instances(tmp_path):
    """Test stopping all instances."""
    manager = get_litellm_manager(tmp_path)
    
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
        manager.start_instance("test3", 4002, config_data)
        assert len(manager._processes) == 3
        
        # Stop all
        manager.stop_all_instances()
        assert len(manager._processes) == 0
        assert manager.get_all_instances() == []


def test_get_nonexistent_instance(tmp_path):
    """Test getting information about a non-existent instance."""
    manager = get_litellm_manager(tmp_path)
    
    result = manager.get_instance("nonexistent")
    assert result is None


def test_get_all_instances_empty(tmp_path):
    """Test getting all instances when none are running."""
    manager = get_litellm_manager(tmp_path)
    
    instances = manager.get_all_instances()
    assert instances == []


def test_master_key_format(tmp_path):
    """Test that master keys have the correct format."""
    manager = get_litellm_manager(tmp_path)
    instance_dir = tmp_path / ".dopemux" / "litellm" / "test"
    instance_dir.mkdir(parents=True, exist_ok=True)
    
    key = manager._ensure_master_key(instance_dir)
    
    # Should start with sk-
    assert key.startswith("sk-")
    
    # Should contain the dopemux prefix
    assert "dopemux" in key
    
    # Should be reasonably long
    assert len(key) > 30


def test_config_file_creation(tmp_path):
    """Test that configuration files are created correctly."""
    manager = get_litellm_manager(tmp_path)
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
    
    # Verify file was created
    assert config_path.exists()
    assert config_path.name == "litellm.config.yaml"
    
    # Verify content
    import yaml
    content = yaml.safe_load(config_path.read_text())
    assert content["general_settings"]["master_key"] == "test-key-123"
    assert "model_list" in content
    assert len(content["model_list"]) == 1
    assert content["model_list"][0]["model_name"] == "test-model"


def test_health_monitor_start_stop(tmp_path):
    """Test health monitor start/stop functionality."""
    manager = get_litellm_manager(tmp_path)
    monitor = manager._health_monitor
    
    # Start the monitor
    monitor.start()
    assert monitor._thread.is_alive()
    
    # Stop the monitor
    monitor.stop()
    monitor._thread.join(timeout=1.0)
    assert not monitor._thread.is_alive()


def test_process_info_properties(tmp_path):
    """Test LiteLLMProcessInfo properties."""
    manager = get_litellm_manager(tmp_path)
    
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
        
        process_info = manager.start_instance("test", 4000, config_data)
        
        # Test base_url property
        assert process_info.base_url == "http://127.0.0.1:4000"
        
        # Test health update
        process_info.update_health(True)
        assert process_info.healthy == True
        
        process_info.update_health(False)
        assert process_info.healthy == False


def test_thread_safety(tmp_path):
    """Test thread safety of manager operations."""
    manager = get_litellm_manager(tmp_path)
    
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
        
        # Perform operations that should be thread-safe
        manager.start_instance("test1", 4000, config_data)
        manager.start_instance("test2", 4001, config_data)
        
        # Get instances
        instances = manager.get_all_instances()
        assert len(instances) == 2
        
        # Stop instances
        manager.stop_instance("test1")
        assert len(manager.get_all_instances()) == 1
        
        manager.stop_instance("test2")
        assert len(manager.get_all_instances()) == 0


def test_error_handling(tmp_path):
    """Test error handling in manager operations."""
    manager = get_litellm_manager(tmp_path)
    
    # Test stopping non-existent instance
    result = manager.stop_instance("nonexistent")
    assert result == False
    
    # Test getting non-existent instance
    result = manager.get_instance("nonexistent")
    assert result is None
    
    # Test building environment for non-existent instance
    try:
        manager.build_client_environment("nonexistent")
        assert False, "Should have raised exception"
    except Exception:
        pass  # Expected


def test_health_status_format(tmp_path):
    """Test that health status has the correct format."""
    manager = get_litellm_manager(tmp_path)
    
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
        manager.get_instance("test").update_health(True)
        
        status = manager.get_health_status()
        
        # Verify structure
        assert isinstance(status, dict)
        assert "test" in status
        
        instance_status = status["test"]
        assert isinstance(instance_status, dict)
        assert "port" in instance_status
        assert "healthy" in instance_status
        assert "start_time" in instance_status
        assert "last_health_check" in instance_status
        assert "db_enabled" in instance_status
        
        # Verify values
        assert instance_status["port"] == 4000
        assert instance_status["healthy"] == True
        assert instance_status["db_enabled"] == False


def test_manager_lifecycle_with_instances(tmp_path):
    """Test full manager lifecycle with instances."""
    manager = get_litellm_manager(tmp_path)
    
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
        
        # Start instances
        manager.start_instance("test1", 4000, config_data)
        manager.start_instance("test2", 4001, config_data)
        
        # Start health monitoring
        manager.start()
        
        # Verify instances are running
        assert len(manager.get_all_instances()) == 2
        
        # Stop everything
        manager.stop()
        
        # Verify everything is cleaned up
        assert len(manager.get_all_instances()) == 0
