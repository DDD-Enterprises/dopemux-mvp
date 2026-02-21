from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_gitmodules_declares_taskx_submodule() -> None:
    gitmodules = (REPO_ROOT / ".gitmodules").read_text(encoding="utf-8")
    assert '[submodule "vendor/taskx"]' in gitmodules
    assert "path = vendor/taskx" in gitmodules
    assert "url = https://github.com/hu3mann/taskX.git" in gitmodules


def test_ci_workflow_uses_submodule_not_taskx_pin() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci-complete.yml").read_text(encoding="utf-8")
    assert "submodules: recursive" in workflow
    assert "vendor/taskx" in workflow
    assert ".taskx-pin" not in workflow


def test_taskx_wrapper_requires_vendor_submodule() -> None:
    wrapper = (REPO_ROOT / "scripts" / "taskx").read_text(encoding="utf-8")
    assert "TASKX_SOURCE_DIR=\"$REPO_ROOT/vendor/taskx\"" in wrapper
    assert ".taskx-pin" not in wrapper
