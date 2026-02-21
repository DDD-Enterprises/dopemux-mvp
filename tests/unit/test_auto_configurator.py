import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from dopemux.auto_configurator import WorktreeAutoConfigurator

class TestWorktreeAutoConfigurator:
    @pytest.fixture
    def config_path(self, tmp_path):
        path = tmp_path / ".claude.json"
        return path

    @pytest.fixture
    def configurator(self, config_path):
        return WorktreeAutoConfigurator(claude_config_path=config_path)

    @pytest.fixture
    def sample_config(self):
        return {
            "projects": {
                "/work/project1": {
                    "mcpServers": {
                        "conport": {
                            "type": "sse",
                            "args": ["--workspace_id", "/work/project1"]
                        },
                        "dope-context": {
                            "type": "sse",
                            "command": "/work/project1/services/dope-context/run_mcp.sh"
                        }
                    }
                }
            }
        }

    def test_init_default_path(self, monkeypatch):
        monkeypatch.setenv("HOME", "/mock/home")
        configurator = WorktreeAutoConfigurator()
        assert configurator.claude_config_path == Path("/mock/home/.claude.json")

    def test_init_custom_path(self):
        custom_path = Path("/custom/path.json")
        configurator = WorktreeAutoConfigurator(claude_config_path=custom_path)
        assert configurator.claude_config_path == custom_path

    def test_needs_update_missing_config(self, configurator):
        assert configurator.needs_update(Path("/work/project1")) is False

    def test_needs_update_workspace_not_in_config(self, configurator, sample_config, config_path):
        config_path.write_text(json.dumps(sample_config))
        assert configurator.needs_update(Path("/work/project2")) is False

    def test_needs_update_no_changes_needed(self, configurator, sample_config, config_path):
        config_path.write_text(json.dumps(sample_config))
        assert configurator.needs_update(Path("/work/project1")) is False

    def test_needs_update_conport_stale(self, configurator, sample_config, config_path):
        sample_config["projects"]["/work/project1"]["mcpServers"]["conport"]["args"] = ["--workspace_id", "/work/old_project"]
        config_path.write_text(json.dumps(sample_config))
        assert configurator.needs_update(Path("/work/project1")) is True

    def test_needs_update_conport_missing_arg(self, configurator, sample_config, config_path):
        sample_config["projects"]["/work/project1"]["mcpServers"]["conport"]["args"] = []
        config_path.write_text(json.dumps(sample_config))
        assert configurator.needs_update(Path("/work/project1")) is True

    def test_needs_update_dope_context_stale(self, configurator, sample_config, config_path):
        sample_config["projects"]["/work/project1"]["mcpServers"]["dope-context"]["command"] = "/work/old_project/services/dope-context/run_mcp.sh"
        config_path.write_text(json.dumps(sample_config))
        assert configurator.needs_update(Path("/work/project1")) is True

    def test_configure_workspace_dry_run(self, configurator, sample_config, config_path):
        sample_config["projects"]["/work/project1"]["mcpServers"]["conport"]["args"] = ["--workspace_id", "/work/old_project"]
        config_path.write_text(json.dumps(sample_config))

        success, message = configurator.configure_workspace(workspace=Path("/work/project1"), dry_run=True)

        assert success is True
        assert "Would update" in message
        # Verify file NOT changed
        with open(config_path) as f:
            data = json.load(f)
            assert data["projects"]["/work/project1"]["mcpServers"]["conport"]["args"][1] == "/work/old_project"

    def test_configure_workspace_success(self, configurator, sample_config, config_path):
        sample_config["projects"]["/work/project1"]["mcpServers"]["conport"]["args"] = ["--workspace_id", "/work/old_project"]
        config_path.write_text(json.dumps(sample_config))

        success, message = configurator.configure_workspace(workspace=Path("/work/project1"), dry_run=False)

        assert success is True
        assert "Updated" in message
        # Verify file CHANGED
        with open(config_path) as f:
            data = json.load(f)
            assert data["projects"]["/work/project1"]["mcpServers"]["conport"]["args"][1] == "/work/project1"

        # Verify backup created
        backups = list(config_path.parent.glob(".claude.json.backup.*"))
        assert len(backups) == 1

    def test_configure_workspace_legacy_mode(self, monkeypatch, config_path):
        monkeypatch.setenv("DOPEMUX_LEGACY_DETECTION", "1")
        configurator = WorktreeAutoConfigurator(claude_config_path=config_path)
        success, message = configurator.configure_workspace(workspace=Path("/work/project1"))
        assert success is False
        assert "Legacy mode" in message

    def test_get_status(self, configurator, config_path):
        with patch("dopemux.auto_configurator.get_workspace_root", return_value=Path("/work/project1")), \
             patch("dopemux.auto_configurator.get_workspace_info", return_value={"mock": "info"}):
            status = configurator.get_status()
            assert status["enabled"] is True
            assert status["current_workspace"] == "/work/project1"
            assert status["config_exists"] is False

    def test_update_dope_context_command_logic(self, configurator):
        old_command = "/old/path/services/dope-context/run_mcp.sh"
        new_workspace = Path("/new/workspace")
        new_command = configurator._update_dope_context_command(old_command, new_workspace)
        assert new_command == "/new/workspace/services/dope-context/run_mcp.sh"

    def test_update_dope_context_command_no_services(self, configurator):
        old_command = "/some/other/command.sh"
        new_workspace = Path("/new/workspace")
        new_command = configurator._update_dope_context_command(old_command, new_workspace)
        assert new_command == old_command

    def test_update_conport_args_missing_workspace_id(self, configurator):
        args = ["--other", "val"]
        new_workspace = Path("/new/workspace")
        new_args = configurator._update_conport_args(args, new_workspace)
        assert "--workspace_id" in new_args
        assert new_args[new_args.index("--workspace_id") + 1] == "/new/workspace"
