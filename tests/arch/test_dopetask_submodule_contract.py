from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_gitmodules_has_no_dopetask_submodule() -> None:
    gitmodules = (REPO_ROOT / ".gitmodules").read_text(encoding="utf-8")
    assert '[submodule "vendor/dopetask"]' not in gitmodules
    assert "path = vendor/dopetask" not in gitmodules


def test_ci_workflow_uses_dopetask_pin_not_submodule() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci-complete.yml").read_text(encoding="utf-8")
    assert ".dopetask-pin" in workflow
    assert "vendor/dopetask" not in workflow


def test_dopetask_wrapper_uses_pip_not_submodule() -> None:
    wrapper = (REPO_ROOT / "scripts" / "dopetask").read_text(encoding="utf-8")
    assert 'DOPETASK_PIN="$REPO_ROOT/.dopetask-pin"' in wrapper
    assert 'install=pip' in wrapper
    assert "DOPETASK_SOURCE_DIR=\"$REPO_ROOT/vendor/dopetask\"" not in wrapper
