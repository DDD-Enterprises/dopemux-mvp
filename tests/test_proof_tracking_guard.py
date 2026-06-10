"""
Tests for .claude/hooks/proof_tracking_guard.py

Mirrors the style of tests/test_orchestrator_enforcement_hooks.py.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_HOOKS_DIR = Path(__file__).resolve().parents[1] / ".claude" / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from proof_tracking_guard import TRACK_TIER, on_proof_write  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_side_effect(ignore_rc: int = 0, ls_rc: int = 1):
    """Return a subprocess.run side-effect that routes by command content."""
    def _run(cmd, **kwargs):
        result = MagicMock()
        if "check-ignore" in cmd:
            result.returncode = ignore_rc
        elif "ls-files" in cmd:
            result.returncode = ls_rc
        else:
            result.returncode = 0
        return result
    return _run


# ---------------------------------------------------------------------------
# Core advisory cases
# ---------------------------------------------------------------------------

def test_gitignored_and_untracked_emits_advisory(tmp_path):
    """Write to proof/TP-X/PROOF.json: ignored (0) + untracked (1) → advisory."""
    fp = str(tmp_path / "proof" / "TP-X" / "PROOF.json")
    with patch("proof_tracking_guard.subprocess.run", side_effect=_run_side_effect(0, 1)):
        result = on_proof_write(tmp_path, fp, "sess-1")
    assert result is not None
    assert "git add -f" in result
    assert "PROOF.json" in result
    assert "TP-DMX-PROOF-TRACKING-POLICY-001" in result
    assert "red-line" in result


def test_already_tracked_returns_none(tmp_path):
    """Already force-added (ls-files exit 0) → None."""
    fp = str(tmp_path / "proof" / "TP-X" / "PROOF.json")
    with patch("proof_tracking_guard.subprocess.run", side_effect=_run_side_effect(0, 0)):
        result = on_proof_write(tmp_path, fp, "sess-2")
    assert result is None


def test_not_ignored_returns_none(tmp_path):
    """check-ignore exit 1 (not ignored) → None; ls-files not called."""
    fp = str(tmp_path / "proof" / "TP-X" / "PROOF.json")
    with patch("proof_tracking_guard.subprocess.run", side_effect=_run_side_effect(1, 1)) as mock:
        result = on_proof_write(tmp_path, fp, "sess-3")
    assert result is None
    # ls-files should not have been reached
    calls = [c.args[0] for c in mock.call_args_list]
    assert not any("ls-files" in " ".join(c) for c in calls)


# ---------------------------------------------------------------------------
# TRACK_TIER gating
# ---------------------------------------------------------------------------

def test_do_not_track_file_returns_none_no_subprocess(tmp_path):
    """proof/TP-X/raw_stdout.log is not TRACK-tier → None, no subprocess."""
    fp = str(tmp_path / "proof" / "TP-X" / "raw_stdout.log")
    with patch("proof_tracking_guard.subprocess.run") as mock:
        result = on_proof_write(tmp_path, fp, "sess-4")
    assert result is None
    mock.assert_not_called()


def test_all_track_tier_filenames_handled(tmp_path):
    """Each TRACK_TIER filename triggers advisory (when ignored+untracked)."""
    for name in TRACK_TIER:
        fp = str(tmp_path / "proof" / "TP-Y" / name)
        with patch("proof_tracking_guard.subprocess.run", side_effect=_run_side_effect(0, 1)):
            result = on_proof_write(tmp_path, fp, f"sess-{name}")
        assert result is not None, f"Expected advisory for {name}"


# ---------------------------------------------------------------------------
# Path filtering
# ---------------------------------------------------------------------------

def test_non_proof_path_no_subprocess(tmp_path):
    """src/something.py → None, zero subprocess calls."""
    fp = str(tmp_path / "src" / "something.py")
    with patch("proof_tracking_guard.subprocess.run") as mock:
        result = on_proof_write(tmp_path, fp, "sess-5")
    assert result is None
    mock.assert_not_called()


def test_path_with_proof_in_name_but_not_under_proof_dir(tmp_path):
    """src/dcp/proof_utils.py — 'proof' in path but not under proof/ → None."""
    fp = str(tmp_path / "src" / "dcp" / "proof_utils.py")
    with patch("proof_tracking_guard.subprocess.run") as mock:
        result = on_proof_write(tmp_path, fp, "sess-6")
    assert result is None
    mock.assert_not_called()


# ---------------------------------------------------------------------------
# Failure resilience
# ---------------------------------------------------------------------------

def test_git_exception_returns_none(tmp_path):
    """git missing / erroring → None, no exception propagated."""
    fp = str(tmp_path / "proof" / "TP-X" / "PROOF.json")
    with patch("proof_tracking_guard.subprocess.run", side_effect=Exception("git not found")):
        result = on_proof_write(tmp_path, fp, "sess-7")
    assert result is None


def test_timeout_returns_none(tmp_path):
    """subprocess.TimeoutExpired → None, no exception propagated."""
    import subprocess
    fp = str(tmp_path / "proof" / "TP-X" / "PROOF.json")
    with patch("proof_tracking_guard.subprocess.run",
               side_effect=subprocess.TimeoutExpired(cmd="git", timeout=1)):
        result = on_proof_write(tmp_path, fp, "sess-8")
    assert result is None


# ---------------------------------------------------------------------------
# Cooldown
# ---------------------------------------------------------------------------

def test_cooldown_same_session(tmp_path):
    """Second call same session + path → None (cache suppresses)."""
    fp = str(tmp_path / "proof" / "TP-X" / "PROOF.json")
    with patch("proof_tracking_guard.subprocess.run", side_effect=_run_side_effect(0, 1)):
        first = on_proof_write(tmp_path, fp, "sess-A")
    assert first is not None

    with patch("proof_tracking_guard.subprocess.run") as mock2:
        second = on_proof_write(tmp_path, fp, "sess-A")
    assert second is None
    mock2.assert_not_called()


def test_cooldown_different_session(tmp_path):
    """Different session_id → not suppressed by cache."""
    fp = str(tmp_path / "proof" / "TP-X" / "PROOF.json")
    with patch("proof_tracking_guard.subprocess.run", side_effect=_run_side_effect(0, 1)):
        first = on_proof_write(tmp_path, fp, "sess-A")
    assert first is not None

    with patch("proof_tracking_guard.subprocess.run", side_effect=_run_side_effect(0, 1)):
        second = on_proof_write(tmp_path, fp, "sess-B")
    assert second is not None


# ---------------------------------------------------------------------------
# TRACK_TIER completeness (policy parity)
# ---------------------------------------------------------------------------

def test_track_tier_matches_policy():
    """TRACK_TIER must contain every file listed in TP-DMX-PROOF-TRACKING-POLICY-001."""
    required = {
        "PROOF.json", "SUMMARY.md", "AUDIT.md", "MERGE_READINESS.json",
        "VALIDATION.md", "CMD_SUMMARY.md", "MODEL_ROUTING.json", "MANIFEST.json",
    }
    assert required <= TRACK_TIER, f"Missing: {required - TRACK_TIER}"
