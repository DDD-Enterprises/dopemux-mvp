import json
from pathlib import Path

import yaml

from dopemux.profile_manager import ProfileManager


def _write_profile(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _build_manager(tmp_path: Path) -> tuple[ProfileManager, Path, Path]:
    dopemux_home = tmp_path / ".dopemux-home"
    profiles_dir = dopemux_home / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)

    _write_profile(
        profiles_dir / "developer.yaml",
        {
            "name": "developer",
            "description": "Developer profile",
            "mcp_servers": {
                "required": ["conport"],
                "enabled": ["zen", "pal"],
            },
        },
    )
    _write_profile(
        profiles_dir / "full.yaml",
        {
            "name": "full",
            "description": "Full profile",
            "mcp_servers": {
                "required": ["conport"],
                "enabled": ["zen", "pal", "serena"],
            },
        },
    )

    workspace = tmp_path / "workspace"
    (workspace / ".dopemux").mkdir(parents=True, exist_ok=True)

    manager = ProfileManager(dopemux_home=dopemux_home)
    return manager, workspace, tmp_path


def _write_claude_config(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_detect_profile_uses_embedded_active_profile_and_caches(tmp_path: Path):
    manager, workspace, root = _build_manager(tmp_path)
    config_path = _write_claude_config(
        root / ".claude" / "settings.json",
        {
            "_dopemux_active_profile": "developer",
            "mcpServers": {"conport": {}, "zen": {}, "pal": {}},
        },
    )

    detected = manager.detect_profile_from_claude_config(
        workspace=workspace,
        config_path=config_path,
        cache_result=True,
    )

    assert detected == "developer"
    assert manager.get_active_profile(workspace) == "developer"


def test_detect_profile_matches_exact_mcp_set(tmp_path: Path):
    manager, workspace, root = _build_manager(tmp_path)
    config_path = _write_claude_config(
        root / ".claude" / "settings.json",
        {"mcpServers": {"dopemux-conport": {}, "dopemux-zen": {}, "dopemux-pal": {}}},
    )

    detected = manager.detect_profile_from_claude_config(
        workspace=workspace,
        config_path=config_path,
        cache_result=True,
    )

    assert detected == "developer"
    assert manager.get_active_profile(workspace) == "developer"


def test_detect_profile_uses_overlap_threshold(tmp_path: Path):
    manager, workspace, root = _build_manager(tmp_path)
    config_path = _write_claude_config(
        root / ".claude" / "settings.json",
        {"mcpServers": {"dopemux-conport": {}, "dopemux-zen": {}, "dopemux-pal": {}, "dopemux-serena": {}, "litellm": {}}},
    )

    detected = manager.detect_profile_from_claude_config(
        workspace=workspace,
        config_path=config_path,
        cache_result=False,
    )

    # full profile overlaps 4/5 selected MCPs and meets the >=0.8 threshold.
    assert detected == "full"
    assert manager.get_active_profile(workspace) is None


def test_detect_profile_returns_none_when_match_is_weak(tmp_path: Path):
    manager, workspace, root = _build_manager(tmp_path)
    config_path = _write_claude_config(
        root / ".claude" / "settings.json",
        {"mcpServers": {"morph-llm": {}, "magic-mcp": {}}},
    )

    detected = manager.detect_profile_from_claude_config(
        workspace=workspace,
        config_path=config_path,
        cache_result=True,
    )

    assert detected is None
    assert manager.get_active_profile(workspace) is None
