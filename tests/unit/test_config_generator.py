import json
from pathlib import Path
from unittest.mock import patch

import pytest

from dopemux.config_generator import ConfigGenerator
from dopemux.profile_models import Profile


@pytest.fixture
def initial_full_config() -> dict:
    return {
        "env": {"MCP_TOOL_TIMEOUT": "120000"},
        "statusLine": {"type": "command", "command": "echo ok"},
        "alwaysThinkingEnabled": False,
        "mcpServers": {
            "conport": {"type": "stdio"},
            "zen": {"type": "stdio"},
            "serena": {"type": "stdio"},
        },
    }


@pytest.fixture
def profile_minimal() -> Profile:
    return Profile(
        name="minimal",
        display_name="Minimal",
        description="Minimal profile",
        mcps=["conport", "zen"],
    )


@pytest.fixture
def config_path(tmp_path: Path, initial_full_config: dict) -> Path:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(initial_full_config, indent=2), encoding="utf-8")
    return path


def test_write_config_creates_timestamped_backup_and_filtered_config(
    config_path: Path,
    initial_full_config: dict,
    profile_minimal: Profile,
):
    generator = ConfigGenerator(dope_brainz_config_path=config_path)

    out_path = generator.write_config(profile_minimal, backup=True)
    assert out_path == config_path

    backups = sorted(config_path.parent.glob("settings.backup.*.json"))
    assert len(backups) == 1

    backup_content = json.loads(backups[0].read_text(encoding="utf-8"))
    assert backup_content == initial_full_config

    written = json.loads(config_path.read_text(encoding="utf-8"))
    assert set(written["mcpServers"].keys()) == {"conport", "zen"}


def test_rollback_config_restores_from_backup(
    config_path: Path,
    initial_full_config: dict,
):
    generator = ConfigGenerator(dope_brainz_config_path=config_path)

    backup_path = generator._create_backup(config_path)
    config_path.write_text(json.dumps({"bad": True}), encoding="utf-8")
    generator.rollback_config(config_path, backup_path)

    restored = json.loads(config_path.read_text(encoding="utf-8"))
    assert restored == initial_full_config


def test_write_config_rolls_back_when_atomic_write_fails(
    config_path: Path,
    initial_full_config: dict,
    profile_minimal: Profile,
):
    generator = ConfigGenerator(dope_brainz_config_path=config_path)

    with patch.object(generator, "_atomic_write_json", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError):
            generator.write_config(profile_minimal, backup=True)

    restored = json.loads(config_path.read_text(encoding="utf-8"))
    assert restored == initial_full_config
