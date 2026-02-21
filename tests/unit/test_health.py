import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import json
from datetime import datetime

import pytest

# Mock psutil and docker before importing HealthChecker
mock_psutil = MagicMock()
sys.modules["psutil"] = mock_psutil

mock_docker = MagicMock()
sys.modules["docker"] = mock_docker

# Mock rich submodules if needed
mock_rich_panel = MagicMock()
sys.modules["rich.panel"] = mock_rich_panel
mock_rich_table = MagicMock()
sys.modules["rich.table"] = mock_rich_table

import dopemux.health as health_module
from dopemux.health import HealthChecker, HealthStatus, ServiceHealth

# Ensure tests always patch the module references used by HealthChecker,
# even if dopemux.health was imported earlier by another test module.
health_module.psutil = mock_psutil
health_module.docker = mock_docker

class TestHealthChecker:
    @pytest.fixture
    def health_checker(self, temp_project_dir):
        return HealthChecker(project_path=temp_project_dir)

    def test_init(self, temp_project_dir):
        checker = HealthChecker(project_path=temp_project_dir)
        assert checker.project_path == temp_project_dir
        assert checker.docker_client is not None
        assert "dopemux_core" in checker.checks

    def test_init_no_docker(self, temp_project_dir):
        with patch("dopemux.health.docker.from_env", side_effect=Exception("Docker failed")):
            checker = HealthChecker(project_path=temp_project_dir)
            assert checker.docker_client is None

    def test_check_all(self, health_checker):
        with patch.object(health_checker, "checks") as mock_checks:
            mock_check_func = MagicMock(return_value=ServiceHealth(
                name="test", status=HealthStatus.HEALTHY, message="OK", details={}
            ))
            mock_checks.items.return_value = [("test_check", mock_check_func)]

            results = health_checker.check_all()

            assert "test_check" in results
            assert results["test_check"].status == HealthStatus.HEALTHY
            assert results["test_check"].response_time_ms >= 0
            assert isinstance(results["test_check"].last_check, datetime)

    def test_check_all_exception(self, health_checker):
        with patch.object(health_checker, "checks") as mock_checks:
            mock_check_func = MagicMock(side_effect=Exception("Check failed"))
            mock_checks.items.return_value = [("fail_check", mock_check_func)]

            results = health_checker.check_all()

            assert "fail_check" in results
            assert results["fail_check"].status == HealthStatus.CRITICAL
            assert "Health check failed" in results["fail_check"].message

    def test_quick_status(self, health_checker):
        with patch.object(health_checker, "check_all") as mock_check_all:
            mock_check_all.return_value = {
                "core": ServiceHealth(name="core", status=HealthStatus.HEALTHY, message="All good", details={})
            }

            status = health_checker.quick_status()
            assert "core" in status
            assert "healthy" in status["core"]

    def test_check_dopemux_core_not_initialized(self, health_checker, temp_project_dir):
        result = health_checker._check_dopemux_core()
        assert result.status == HealthStatus.CRITICAL
        assert "not initialized" in result.message

    def test_check_dopemux_core_healthy(self, health_checker, temp_project_dir):
        (temp_project_dir / ".dopemux").mkdir()
        (temp_project_dir / ".claude").mkdir()
        (temp_project_dir / ".dopemux" / "config.json").touch()
        (temp_project_dir / ".claude" / "config.json").touch()
        (temp_project_dir / ".claude" / "claude.md").touch()

        result = health_checker._check_dopemux_core()
        assert result.status == HealthStatus.HEALTHY
        assert "Core configuration valid" in result.message

    def test_check_dopemux_core_missing_files(self, health_checker, temp_project_dir):
        (temp_project_dir / ".dopemux").mkdir()
        (temp_project_dir / ".claude").mkdir()

        result = health_checker._check_dopemux_core()
        assert result.status == HealthStatus.WARNING
        assert "Missing 3 config files" in result.message

    def test_check_dope_brainz_running(self, health_checker):
        mock_proc = MagicMock()
        mock_proc.info = {"pid": 123, "name": "python", "cmdline": ["python", "dope_brainz.py"]}
        mock_psutil.process_iter.return_value = [mock_proc]

        result = health_checker._check_dope_brainz()
        assert result.status == HealthStatus.HEALTHY
        assert "DopeBrainz running" in result.message

    def test_check_dope_brainz_not_running(self, health_checker):
        mock_psutil.process_iter.return_value = []

        result = health_checker._check_dope_brainz()
        assert result.status == HealthStatus.WARNING
        assert "DopeBrainz not running" in result.message

    def test_check_mcp_servers_running(self, health_checker):
        mock_proc = MagicMock()
        mock_proc.info = {"pid": 456, "name": "node", "cmdline": ["mcp-server-git"], "status": "running"}
        mock_proc.memory_info.return_value.rss = 100 * 1024 * 1024
        mock_proc.cpu_percent.return_value = 1.0
        mock_psutil.process_iter.return_value = [mock_proc]

        result = health_checker._check_mcp_servers()
        assert result.status == HealthStatus.HEALTHY
        assert "MCP servers healthy" in result.message

    def test_check_docker_services_not_available(self, health_checker):
        health_checker.docker_client = None
        result = health_checker._check_docker_services()
        assert result.status == HealthStatus.WARNING
        assert "Docker not available" in result.message

    def test_check_docker_services_healthy(self, health_checker):
        mock_container = MagicMock()
        mock_container.name = "mcp-server"
        mock_container.status = "running"
        mock_container.image.tags = ["mcp-image:latest"]
        mock_container.ports = {}
        health_checker.docker_client.containers.list.return_value = [mock_container]

        result = health_checker._check_docker_services()
        assert result.status == HealthStatus.HEALTHY
        assert "All Docker MCP services healthy" in result.message

    def test_check_docker_services_some_down(self, health_checker):
        mock_container1 = MagicMock(name="c1")
        mock_container1.name = "mcp-server-1"
        mock_container1.status = "running"
        mock_container1.image.tags = ["mcp-image:latest"]

        mock_container2 = MagicMock(name="c2")
        mock_container2.name = "mcp-server-2"
        mock_container2.status = "exited"
        mock_container2.image.tags = ["mcp-image:latest"]

        health_checker.docker_client.containers.list.return_value = [mock_container1, mock_container2]

        result = health_checker._check_docker_services()
        assert result.status == HealthStatus.WARNING
        assert "Some Docker MCP services down" in result.message

    def test_check_system_resources_healthy(self, health_checker):
        mock_psutil.cpu_percent.return_value = 10.0
        mock_psutil.virtual_memory.return_value.percent = 40.0
        mock_psutil.disk_usage.return_value.percent = 50.0

        result = health_checker._check_system_resources()
        assert result.status == HealthStatus.HEALTHY
        assert "System resources healthy" in result.message

    def test_check_system_resources_warning(self, health_checker):
        mock_psutil.cpu_percent.return_value = 90.0
        mock_psutil.virtual_memory.return_value.percent = 20.0
        mock_psutil.disk_usage.return_value.percent = 20.0

        result = health_checker._check_system_resources()
        assert result.status == HealthStatus.WARNING
        assert "High CPU usage" in result.message

    def test_check_adhd_features_active(self, health_checker, temp_project_dir):
        dopemux_dir = temp_project_dir / ".dopemux"
        dopemux_dir.mkdir()

        attention_file = dopemux_dir / "attention.json"
        with open(attention_file, "w") as f:
            json.dump({"last_check": "now", "focus_score": 0.8}, f)

        context_file = dopemux_dir / "context.json"
        with open(context_file, "w") as f:
            json.dump({"last_save": "now", "sessions": []}, f)

        result = health_checker._check_adhd_features()
        assert result.status == HealthStatus.HEALTHY
        assert "All ADHD features active" in result.message

    def test_check_adhd_features_partially_active(self, health_checker, temp_project_dir):
        dopemux_dir = temp_project_dir / ".dopemux"
        dopemux_dir.mkdir()

        attention_file = dopemux_dir / "attention.json"
        with open(attention_file, "w") as f:
            json.dump({"last_check": "now", "focus_score": 0.8}, f)

        result = health_checker._check_adhd_features()
        assert result.status == HealthStatus.WARNING
        assert "Some ADHD features inactive" in result.message

    def test_display_health_report(self, health_checker):
        results = {
            "core": ServiceHealth(name="core", status=HealthStatus.HEALTHY, message="OK", details={"detail": "value"})
        }
        health_checker.display_health_report(results, detailed=True)

    def test_format_for_slash_command(self, health_checker):
        results = {
            "core": ServiceHealth(name="core", status=HealthStatus.HEALTHY, message="OK", details={})
        }
        formatted = health_checker.format_for_slash_command(results)
        assert "core" in formatted.lower()
        assert "OK" in formatted

    def test_restart_unhealthy_services(self, health_checker):
        with patch.object(health_checker, "check_all") as mock_check_all:
            mock_check_all.return_value = {
                "core": ServiceHealth(name="core", status=HealthStatus.CRITICAL, message="FAIL", details={})
            }
            restarted = health_checker.restart_unhealthy_services()
            assert restarted == []
