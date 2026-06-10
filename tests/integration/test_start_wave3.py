"""
Integration tests for dopemux start --role fix (3A-1).

Verifies:
- setup_project_config accepts role= keyword without TypeError
- Doctrine files (.claude/CLAUDE.md) are NOT clobbered when role is supplied

Note: The doctrine-preservation test relies on macOS case-insensitive FS where
.claude/CLAUDE.md == .claude/claude.md. On case-sensitive Linux CI, CLAUDE.md and
claude.md are distinct files, making this test less sensitive to the guard; it still
passes correctly here (darwin).
"""

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from dopemux.claude.configurator import ClaudeConfigurator


# ---------------------------------------------------------------------------
# Minimal ConfigManager fixture (mirrors tests/conftest.py pattern)
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_project(tmp_path):
    """Temporary project directory scoped to a single test."""
    return tmp_path


@pytest.fixture
def config_manager_minimal():
    """
    Minimal ConfigManager suitable for ClaudeConfigurator construction,
    following the conftest.py pattern (patch _init_paths + _get_default_config).
    """
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    try:
        with patch("dopemux.config.manager.ConfigManager._init_paths") as mock_init_paths:
            from dopemux.config.manager import ConfigPaths
            mock_init_paths.return_value = ConfigPaths(
                global_config=tmp / "global.yaml",
                user_config=tmp / "config.yaml",
                project_config=tmp / "project.yaml",
                cache_dir=tmp / "cache",
                data_dir=tmp / "data",
            )
            from dopemux.config.manager import ConfigManager
            manager = ConfigManager()
            minimal_config = {
                "version": "1.0",
                "adhd_profile": {
                    "focus_duration_avg": 25,
                    "break_interval": 5,
                    "distraction_sensitivity": 0.5,
                    "hyperfocus_tendency": False,
                    "notification_style": "gentle",
                    "visual_complexity": "minimal",
                },
                "mcp_servers": {},
                "attention": {
                    "enabled": True,
                    "sample_interval": 5,
                    "keystroke_threshold": 2.0,
                    "context_switch_threshold": 3,
                    "adaptation_enabled": True,
                },
                "context": {
                    "enabled": True,
                    "auto_save_interval": 30,
                    "max_sessions": 50,
                    "compression": True,
                    "backup_enabled": True,
                },
            }
            with patch.object(manager, "_get_default_config", return_value=minimal_config):
                yield manager
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Test 1: role= keyword must not raise TypeError
# ---------------------------------------------------------------------------

def test_setup_project_config_accepts_role_without_crash(config_manager_minimal, tmp_project):
    """
    setup_project_config(tmp_path, role="developer") must not raise TypeError.
    This was broken before fix: the method had no role param, so passing role=
    raised TypeError immediately.
    """
    configurator = ClaudeConfigurator(config_manager_minimal)
    # Must not raise
    configurator.setup_project_config(tmp_project, role="developer")


# ---------------------------------------------------------------------------
# Test 2: Pre-existing doctrine file must not be clobbered
# ---------------------------------------------------------------------------

def test_setup_project_config_role_preserves_doctrine(config_manager_minimal, tmp_project):
    """
    When role= is supplied and .claude/CLAUDE.md already exists, the file must
    be left byte-for-byte intact — not overwritten by the generic template generator.

    On macOS (case-insensitive), .claude/CLAUDE.md == .claude/claude.md, so the
    _create_claude_md call that unconditionally writes .claude/claude.md would destroy
    the real doctrine. This guard is the clobber hazard the fix must prevent.
    """
    sentinel = "# SENTINEL DOCTRINE"

    # Pre-create the doctrine file (upper-case, as the real project uses)
    claude_dir = tmp_project / ".claude"
    claude_dir.mkdir(exist_ok=True)
    doctrine_file = claude_dir / "CLAUDE.md"
    doctrine_file.write_text(sentinel)

    configurator = ClaudeConfigurator(config_manager_minimal)
    configurator.setup_project_config(tmp_project, role="developer")

    # CLAUDE.md must still contain the sentinel
    assert doctrine_file.read_text() == sentinel, (
        "CLAUDE.md was clobbered by setup_project_config when role= was supplied"
    )

    # On case-insensitive FS, claude.md is the SAME file; verify the alias too
    claude_md_lower = claude_dir / "claude.md"
    # Path.resolve() will point to the same inode on case-insensitive FS
    if claude_md_lower.resolve() == doctrine_file.resolve():
        # Same file — already checked above
        pass
    else:
        # Case-sensitive FS: CLAUDE.md and claude.md are distinct. The lower-case
        # file may or may not have been created; what matters is CLAUDE.md is intact.
        pass
