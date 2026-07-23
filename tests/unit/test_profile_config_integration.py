import json
from pathlib import Path

import pytest

from dopemux.claude_config import ClaudeConfig
from dopemux.profile_models import Profile


@pytest.fixture
def sample_config() -> dict:
    return {
        "env": {"MCP_TOOL_TIMEOUT": "120000"},
        "statusLine": {"type": "command", "command": "echo status"},
        "alwaysThinkingEnabled": False,
        "mcpServers": {
            "conport": {"type": "stdio"},
            "serena": {"type": "stdio"},
            "zen": {"type": "stdio"},
            "pal": {"type": "stdio"},
            "gpt-researcher": {"type": "stdio"},
        },
    }


@pytest.fixture
def claude_config(tmp_path: Path, sample_config: dict) -> ClaudeConfig:
    config_path = tmp_path / "settings.json"
    config_path.write_text(json.dumps(sample_config, indent=2), encoding="utf-8")
    return ClaudeConfig(config_path=config_path)


def test_full_profile_matches_existing_mcp_inventory(claude_config: ClaudeConfig, sample_config: dict):
    full_profile = Profile(
        name="full",
        display_name="Full",
        description="Full test profile",
        mcps=["conport", "serena-v2", "zen", "pal", "gpt-researcher"],
    )

    new_config = claude_config.apply_profile(full_profile, create_backup=False)
    assert set(new_config["mcpServers"].keys()) == set(sample_config["mcpServers"].keys())


def test_developer_profile_has_three_mcps(claude_config: ClaudeConfig):
    developer_profile = Profile(
        name="developer",
        display_name="Developer",
        description="Developer test profile",
        mcps=["conport", "serena-v2", "zen"],
    )

    new_config = claude_config.apply_profile(developer_profile, create_backup=False)
    assert set(new_config["mcpServers"].keys()) == {"conport", "serena", "zen"}
    assert len(new_config["mcpServers"]) == 3


def test_backup_and_rollback_round_trip(claude_config: ClaudeConfig, sample_config: dict):
    developer_profile = Profile(
        name="developer",
        display_name="Developer",
        description="Developer test profile",
        mcps=["conport", "serena-v2", "zen"],
    )

    backup_path = claude_config.backup_config()
    claude_config.apply_profile(developer_profile, create_backup=False)
    claude_config.rollback_to_backup(backup_path)

    restored = claude_config.read_config()
    assert set(restored["mcpServers"].keys()) == set(sample_config["mcpServers"].keys())
