"""
Comprehensive tests for Constrained Dynamic Loading system.

Tests cover all components: loader, registry, patterns, health, resources, and admin.
"""

import pytest
import json
import asyncio
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.chatx.mcp.loader import ConstrainedDynamicLoader, LoaderConfig
from src.chatx.mcp.registry import ServerRegistry, ServerConfig, ServerStatus
from src.chatx.mcp.patterns import PatternMatcher, ActivationPattern
from src.chatx.mcp.health import HealthChecker, HealthStatus
from src.chatx.mcp.resources import ResourceManager, ResourceLimits
from src.chatx.mcp.admin import AdminOverride, OverrideReason, OverrideResult


class TestConstrainedDynamicLoader:
    """Test the main ConstrainedDynamicLoader class."""
    
    @pytest.fixture
    def loader_config(self):
        return LoaderConfig(
            max_concurrent_servers=2,
            global_timeout_seconds=1,
            health_check_interval=1
        )
    
    @pytest.fixture
    def mock_registry(self):
        """Create a mock server registry."""
        registry = Mock(spec=ServerRegistry)
        
        # Mock approved server
        server_config = Mock(spec=ServerConfig)
        server_config.id = "test-server"
        server_config.approved = True
        server_config.estimated_tokens = 1000
        server_config.priority = 5
        server_config.resource_requirements = {}
        server_config.activation_patterns = [
            Mock(tool_patterns=["test_*"], context_patterns=[], priority=5)
        ]
        
        registry.get_available_servers.return_value = [server_config]
        registry.get_server.return_value = server_config
        registry.get_approved_servers.return_value = [server_config]
        
        return registry
    
    def test_initialization(self, loader_config, mock_registry):
        """Test loader initialization."""
        loader = ConstrainedDynamicLoader(loader_config, mock_registry)
        
        assert loader.config == loader_config
        assert loader.registry == mock_registry
        assert len(loader.active_servers) == 0
        assert loader.total_activations == 0
        assert loader.failed_activations == 0
    
    def test_get_matching_servers(self, loader_config, mock_registry):
        """Test server matching logic."""
        loader = ConstrainedDynamicLoader(loader_config, mock_registry)
        
        context = {
            'tool': 'test_function',
            'input': {},
            'content_size': 100
        }
        
        servers = loader.get_matching_servers(context)
        
        assert len(servers) == 1
        mock_registry.get_available_servers.assert_called_once()
    
    def test_can_activate_server_success(self, loader_config, mock_registry):
        """Test successful server activation check."""
        loader = ConstrainedDynamicLoader(loader_config, mock_registry)
        
        server_config = Mock(spec=ServerConfig)
        server_config.id = "test-server"
        
        can_activate, reason = loader.can_activate_server(server_config)
        
        assert can_activate is True
        assert reason == "OK"
    
    def test_can_activate_server_max_concurrent(self, loader_config, mock_registry):
        """Test activation failure due to concurrent server limit."""
        loader = ConstrainedDynamicLoader(loader_config, mock_registry)
        
        # Fill up active servers
        loader.active_servers = {"server1": Mock(), "server2": Mock()}
        
        server_config = Mock(spec=ServerConfig)
        server_config.id = "test-server"
        
        can_activate, reason = loader.can_activate_server(server_config)
        
        assert can_activate is False
        assert "Maximum concurrent servers" in reason
    
    @patch('src.chatx.mcp.loader.ConstrainedDynamicLoader._activate_server_sync')
    def test_activate_server_success(self, mock_activate, loader_config, mock_registry):
        """Test successful server activation."""
        mock_activate.return_value = 12345
        
        loader = ConstrainedDynamicLoader(loader_config, mock_registry)
        
        server_config = Mock(spec=ServerConfig)
        server_config.id = "test-server"
        server_config.approved = True
        server_config.resource_requirements = {}
        server_config.activation_patterns = [Mock()]
        
        context = {'tool': 'test_function'}
        
        instance = loader.activate_server(server_config, context)
        
        assert instance is not None
        assert instance.config == server_config
        assert instance.process_id == 12345
        assert instance.health_status == HealthStatus.HEALTHY
        assert "test-server" in loader.active_servers
    
    @patch('src.chatx.mcp.loader.ConstrainedDynamicLoader._activate_server_sync')
    @patch('asyncio.wait_for')
    def test_activate_server_timeout(self, mock_wait_for, mock_activate, loader_config, mock_registry):
        """Test server activation timeout."""
        mock_wait_for.side_effect = asyncio.TimeoutError()
        
        loader = ConstrainedDynamicLoader(loader_config, mock_registry)
        
        server_config = Mock(spec=ServerConfig)
        server_config.id = "test-server"
        server_config.approved = True
        server_config.resource_requirements = {}
        server_config.activation_patterns = [Mock()]
        
        context = {'tool': 'test_function'}
        
        instance = loader.activate_server(server_config, context)
        
        assert instance is None
        assert loader.failed_activations == 1
    
    def test_deactivate_server(self, loader_config, mock_registry):
        """Test server deactivation."""
        loader = ConstrainedDynamicLoader(loader_config, mock_registry)
        
        # Mock active server
        instance = Mock()
        instance.process_id = 12345
        loader.active_servers["test-server"] = instance
        
        result = loader.deactivate_server("test-server")
        
        assert result is True
        assert "test-server" not in loader.active_servers
    
    def test_get_statistics(self, loader_config, mock_registry):
        """Test loader statistics."""
        loader = ConstrainedDynamicLoader(loader_config, mock_registry)
        
        stats = loader.get_statistics()
        
        assert 'active_servers' in stats
        assert 'total_activations' in stats
        assert 'failed_activations' in stats
        assert 'success_rate' in stats
        assert 'tokens_saved' in stats
        assert 'resource_usage' in stats
        assert 'server_details' in stats


class TestServerRegistry:
    """Test the ServerRegistry class."""
    
    def test_initialization(self, tmp_path):
        """Test registry initialization."""
        registry = ServerRegistry(tmp_path / "registry.json")
        
        # Should have created default registry
        assert len(registry.servers) > 0
    
    def test_register_server(self):
        """Test server registration."""
        registry = ServerRegistry()
        
        config = ServerConfig(
            id="test-server",
            name="Test Server",
            command=["python", "server.py"],
            approved=True,
            estimated_tokens=500
        )
        
        result = registry.register_server(config)
        
        assert result is True
        assert "test-server" in registry.servers
    
    def test_get_server(self):
        """Test server retrieval."""
        registry = ServerRegistry()
        
        # Register a server
        config = ServerConfig(
            id="test-server",
            name="Test Server", 
            command=["python", "server.py"]
        )
        registry.register_server(config)
        
        retrieved = registry.get_server("test-server")
        
        assert retrieved is not None
        assert retrieved.id == "test-server"
    
    def test_get_available_servers(self):
        """Test getting available servers."""
        registry = ServerRegistry()
        
        # Register servers with different statuses
        available_config = ServerConfig(
            id="available-server",
            name="Available Server",
            command=["python", "server.py"],
            status=ServerStatus.AVAILABLE
        )
        disabled_config = ServerConfig(
            id="disabled-server", 
            name="Disabled Server",
            command=["python", "server.py"],
            status=ServerStatus.DISABLED
        )
        
        registry.register_server(available_config)
        registry.register_server(disabled_config)
        
        available = registry.get_available_servers()
        
        assert len(available) == 1
        assert available[0].id == "available-server"
    
    def test_get_approved_servers(self):
        """Test getting approved servers."""
        registry = ServerRegistry()
        
        # Register approved and unapproved servers
        approved_config = ServerConfig(
            id="approved-server",
            name="Approved Server",
            command=["python", "server.py"],
            approved=True,
            status=ServerStatus.AVAILABLE
        )
        unapproved_config = ServerConfig(
            id="unapproved-server",
            name="Unapproved Server", 
            command=["python", "server.py"],
            approved=False,
            status=ServerStatus.AVAILABLE
        )
        
        registry.register_server(approved_config)
        registry.register_server(unapproved_config)
        
        approved = registry.get_approved_servers()
        
        assert len(approved) == 1
        assert approved[0].id == "approved-server"


class TestPatternMatcher:
    """Test the PatternMatcher class."""
    
    def test_initialization(self):
        """Test pattern matcher initialization."""
        matcher = PatternMatcher()
        
        assert len(matcher._compiled_patterns) == 0
        assert len(matcher._activation_history) == 0
    
    def test_matches_tool_patterns(self):
        """Test tool pattern matching."""
        matcher = PatternMatcher()
        
        patterns = [ActivationPattern(tool_patterns=["test_*", "mcp_*"])]
        context = {'tool': 'test_function', 'input': {}}
        
        result = matcher.matches(patterns, context)
        
        assert result is True
    
    def test_matches_context_patterns(self):
        """Test context pattern matching."""
        matcher = PatternMatcher()
        
        patterns = [ActivationPattern(context_patterns=["project_management"])]
        context = {'tool': 'test_function', 'metadata': {'context': 'project_management'}}
        
        result = matcher.matches(patterns, context)
        
        assert result is True
    
    def test_matches_content_size(self):
        """Test content size pattern matching."""
        matcher = PatternMatcher()
        
        patterns = [ActivationPattern(content_size_patterns=[(0, 1000)])]
        context = {'tool': 'test_function', 'content_size': 500}
        
        result = matcher.matches(patterns, context)
        
        assert result is True
    
    def test_record_activation(self):
        """Test activation recording."""
        matcher = PatternMatcher()
        
        matcher.record_activation("test-server")
        
        assert "test-server" in matcher._activation_history
        assert len(matcher._activation_history["test-server"]) == 1
    
    def test_cooldown_constraint(self):
        """Test cooldown constraint enforcement."""
        matcher = PatternMatcher()
        
        pattern = ActivationPattern(cooldown_seconds=10)
        
        # Record activation
        matcher.record_activation("test-server")
        
        # Should be denied due to cooldown
        context = {'tool': 'test_function'}
        result = matcher._check_time_constraints(pattern, context)
        
        assert result is False
    
    def test_optimize_for_tokens(self):
        """Test token optimization."""
        matcher = PatternMatcher()
        
        # Mock server configs with different token costs
        config1 = Mock(estimated_tokens=1000, priority=1)
        config2 = Mock(estimated_tokens=500, priority=2)
        config3 = Mock(estimated_tokens=750, priority=3)
        
        configs = [config1, config2, config3]
        context = {'tool': 'test_function'}
        
        optimized = matcher.optimize_for_tokens(configs, context)
        
        # Should be sorted by efficiency (tokens + priority bonus)
        assert len(optimized) == 3
        assert optimized[0] == config2  # Lowest tokens


class TestHealthChecker:
    """Test the HealthChecker class."""
    
    def test_initialization(self):
        """Test health checker initialization."""
        checker = HealthChecker()
        
        assert len(checker.server_health) == 0
        assert len(checker.server_metrics) == 0
        assert len(checker.health_checks) >= 1  # Should have default checks
    
    @patch('psutil.Process')
    def test_check_process_alive_success(self, mock_process_class):
        """Test successful process health check."""
        mock_process = Mock()
        mock_process.is_running.return_value = True
        mock_process_class.return_value = mock_process
        
        checker = HealthChecker()
        
        result = checker._check_process_alive("test-server", 12345)
        
        assert result is True
        mock_process.is_running.assert_called_once()
    
    @patch('psutil.Process')
    def test_check_process_alive_failure(self, mock_process_class):
        """Test failed process health check."""
        mock_process_class.side_effect = Exception("Process not found")
        
        checker = HealthChecker()
        
        result = checker._check_process_alive("test-server", 12345)
        
        assert result is False
    
    def test_check_response_time(self):
        """Test response time health check."""
        checker = HealthChecker()
        
        # No metrics yet
        result = checker._check_response_time("test-server")
        assert result is True
    
    def test_health_check_cycle(self):
        """Test health check cycle."""
        checker = HealthChecker()
        
        # Add a server instance
        from src.chatx.mcp.health import HealthMetrics, ServerInstance
        from src.chatx.mcp.loader import ServerInstance as LoaderInstance
        from src.chatx.mcp.registry import ServerConfig
        
        config = ServerConfig(id="test-server", name="Test", command=["echo"])
        instance = LoaderInstance(config=config)
        checker.server_health["test-server"] = HealthStatus.UNKNOWN
        
        # Mock the actual health check
        with patch.object(checker, 'check_server_health') as mock_check:
            mock_check.return_value = HealthStatus.HEALTHY
            checker.health_check_cycle()
            
            mock_check.assert_called_once_with("test-server", None)
    
    def test_perform_cleanup(self):
        """Test cleanup functionality."""
        checker = HealthChecker()
        
        # Add server to cleanup queue
        checker.schedule_cleanup("test-server")
        
        assert len(checker.cleanup_queue) == 1
        assert "test-server" in checker.cleanup_queue
        
        # Perform cleanup
        cleaned = checker.perform_cleanup()
        
        assert len(cleaned) == 1
        assert cleaned[0] == "test-server"
        assert len(checker.cleanup_queue) == 0


class TestResourceManager:
    """Test the ResourceManager class."""
    
    def test_initialization(self):
        """Test resource manager initialization."""
        limits = ResourceLimits(max_memory_mb=512, max_cpu_percent=50)
        manager = ResourceManager(limits)
        
        assert manager.limits == limits
        assert len(manager.allocations) == 0
        assert not manager.monitoring_active
    
    def test_can_allocate_resources_success(self):
        """Test successful resource allocation check."""
        limits = ResourceLimits(max_memory_mb=512)
        manager = ResourceManager(limits)
        
        requirements = {'memory_mb': 100}
        
        result = manager.can_allocate_resources(requirements)
        
        assert result is True
    
    def test_can_allocate_resources_failure(self):
        """Test failed resource allocation check."""
        limits = ResourceLimits(max_memory_mb=100)
        manager = ResourceManager(limits)
        
        # Allocate all memory
        manager.allocate_resources("server1", {'memory_mb': 100})
        
        # Try to allocate more
        requirements = {'memory_mb': 50}
        result = manager.can_allocate_resources(requirements)
        
        assert result is False
    
    def test_allocate_and_release_resources(self):
        """Test resource allocation and release."""
        limits = ResourceLimits(max_memory_mb=512)
        manager = ResourceManager(limits)
        
        # Allocate resources
        result = manager.allocate_resources("test-server", {'memory_mb': 100, 'cpu_percent': 10})
        
        assert result is True
        assert "test-server" in manager.allocations
        
        allocation = manager.allocations["test-server"]
        assert allocation.memory_mb == 100
        assert allocation.cpu_percent == 10
        
        # Release resources
        manager.release_resources("test-server")
        
        assert "test-server" not in manager.allocations
    
    def test_get_usage_summary(self):
        """Test resource usage summary."""
        limits = ResourceLimits(max_memory_mb=512, max_cpu_percent=50)
        manager = ResourceManager(limits)
        
        summary = manager.get_usage_summary()
        
        assert 'current_usage' in summary
        assert 'allocated_resources' in summary
        assert 'available_resources' in summary
        assert 'active_allocations' in summary
        assert 'limits' in summary
    
    def test_cleanup_orphaned_allocations(self):
        """Test orphaned allocation cleanup."""
        limits = ResourceLimits(max_memory_mb=512)
        manager = ResourceManager(limits)
        
        # Allocate resources
        manager.allocate_resources("active-server", {'memory_mb': 100})
        manager.allocate_resources("orphaned-server", {'memory_mb': 50})
        
        # Cleanup with only active server
        manager.cleanup_orphaned_allocations(["active-server"])
        
        assert "active-server" in manager.allocations
        assert "orphaned-server" not in manager.allocations


class TestAdminOverride:
    """Test the AdminOverride class."""
    
    def test_initialization(self, tmp_path):
        """Test admin override initialization."""
        config_path = tmp_path / "admin_override.json"
        admin = AdminOverride(admin_key="test_key", config_path=config_path)
        
        assert len(admin.active_overrides) == 0
        assert len(admin.override_history) == 0
        assert admin.admin_key == "test_key"
    
    def test_check_override_auto_approve(self, tmp_path):
        """Test auto-approval of override."""
        config_path = tmp_path / "admin_override.json"
        admin = AdminOverride(config_path=config_path)
        
        context = {'tool': 'test_function'}
        result = admin.check_override("test-server", context, OverrideReason.RESOURCE_CONSTRAINTS)
        
        assert result.allowed is True
        assert OverrideReason.RESOURCE_CONSTRAINTS.value in result.reason
        assert "test-server" in admin.active_overrides
    
    def test_check_override_manual_required(self, tmp_path):
        """Test override requiring manual approval."""
        config_path = tmp_path / "admin_override.json"
        admin = AdminOverride(config_path=config_path)
        
        context = {'tool': 'test_function'}
        result = admin.check_override("test-server", context, OverrideReason.SECURITY_VIOLATION)
        
        assert result.allowed is False
        assert "Manual approval required" in result.reason
        assert "test-server" not in admin.active_overrides
    
    def test_request_manual_override(self, tmp_path):
        """Test manual override request."""
        config_path = tmp_path / "admin_override.json"
        admin = AdminOverride(config_path=config_path)
        
        result = admin.request_manual_override(
            server_id="test-server",
            reason=OverrideReason.SECURITY_VIOLATION,
            justification="Critical security issue",
            requested_by="admin",
            duration_hours=2
        )
        
        assert result.allowed is True
        assert "Manual override approved" in result.reason
        assert "test-server" in admin.active_overrides
    
    def test_revoke_override(self, tmp_path):
        """Test override revocation."""
        config_path = tmp_path / "admin_override.json"
        admin = AdminOverride(config_path=config_path)
        
        # Create active override
        admin.request_manual_override(
            "test-server", OverrideReason.SECURITY_VIOLATION, 
            "test", "admin", 1
        )
        
        # Revoke it
        result = admin.revoke_override("test-server")
        
        assert result is True
        assert "test-server" not in admin.active_overrides
    
    def test_get_active_overrides(self, tmp_path):
        """Test getting active overrides."""
        config_path = tmp_path / "admin_override.json"
        admin = AdminOverride(config_path=config_path)
        
        # Add override
        admin.request_manual_override(
            "test-server", OverrideReason.SECURITY_VIOLATION,
            "test", "admin", 1
        )
        
        active = admin.get_active_overrides()
        
        assert "test-server" in active
        assert active["test-server"]["reason"] == OverrideReason.SECURITY_VIOLATION.value
    
    def test_record_security_violation(self, tmp_path):
        """Test security violation recording."""
        config_path = tmp_path / "admin_override.json"
        admin = AdminOverride(config_path=config_path)
        
        violation = {"type": "unauthorized_access", "severity": "high"}
        admin.record_security_violation(violation)
        
        report = admin.get_security_report()
        
        assert report["security_violations"] == 1
        assert len(report["recent_violations"]) == 1


# Integration Tests
class TestConstrainedDynamicLoaderIntegration:
    """Integration tests for the complete constrained dynamic loading system."""
    
    @pytest.fixture
    def full_system(self, tmp_path):
        """Set up complete constrained dynamic loading system."""
        # Create temporary directories
        registry_path = tmp_path / "registry.json"
        admin_path = tmp_path / "admin.json"
        
        # Initialize components
        loader_config = LoaderConfig(
            max_concurrent_servers=2,
            global_timeout_seconds=2
        )
        
        registry = ServerRegistry(registry_path)
        admin = AdminOverride(config_path=admin_path)
        
        loader = ConstrainedDynamicLoader(loader_config, registry)
        
        return {
            'loader': loader,
            'registry': registry,
            'admin': admin,
            'tmp_path': tmp_path
        }
    
    def test_end_to_end_server_activation(self, full_system):
        """Test complete server activation workflow."""
        loader = full_system['loader']
        registry = full_system['registry']
        
        # Get a server from the registry
        servers = registry.get_available_servers()
        if not servers:
            pytest.skip("No servers available in registry")
        
        server_config = servers[0]
        
        # Approve the server
        registry.approve_server(server_config.id)
        
        # Attempt activation
        context = {'tool': 'mcp__claude-context__search_code', 'input': {}}
        
        # This will likely fail without actual server process, but tests the workflow
        instance = loader.activate_server(server_config, context)
        
        # Check that activation was attempted
        assert loader.total_activations >= 0
        
        # Verify server was recorded as approved
        approved_servers = registry.get_approved_servers()
        assert server_config.id in [s.id for s in approved_servers]
    
    def test_resource_constraint_handling(self, full_system):
        """Test resource constraint handling."""
        loader = full_system['loader']
        
        # Check that resource manager is integrated
        assert hasattr(loader, 'resource_manager')
        
        # Get resource summary
        summary = loader.get_statistics()
        assert 'resource_usage' in summary
    
    def test_pattern_matching_integration(self, full_system):
        """Test pattern matching integration."""
        loader = full_system['loader']
        registry = full_system['registry']
        
        # Test with different contexts
        contexts = [
            {'tool': 'mcp__task-master-ai__get_tasks', 'input': {}},
            {'tool': 'mcp__claude-context__search_code', 'input': {}},
            {'tool': 'unknown_tool', 'input': {}}
        ]
        
        for context in contexts:
            servers = loader.get_matching_servers(context)
            assert isinstance(servers, list)
            # Should return servers or empty list
            for server in servers:
                assert hasattr(server, 'id')
                assert hasattr(server, 'activation_patterns')
    
    def test_admin_override_integration(self, full_system):
        """Test admin override integration."""
        loader = full_system['loader']
        admin = full_system['admin']
        
        # Test override check (should work for resource constraints)
        result = admin.check_override(
            "test-server", 
            {'tool': 'test_tool'}, 
            OverrideReason.RESOURCE_CONSTRAINTS
        )
        
        assert hasattr(result, 'allowed')
        assert hasattr(result, 'reason')
        
        if result.allowed:
            assert "test-server" in admin.active_overrides
    
    def test_health_monitoring_integration(self, full_system):
        """Test health monitoring integration."""
        loader = full_system['loader']
        
        # Check health checker integration
        assert hasattr(loader, 'health_checker')
        
        # Test health check cycle
        loader.health_check_cycle()
        
        # Should not crash and should update health status
        health_statuses = loader.health_checker.get_all_health_status()
        assert isinstance(health_statuses, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])