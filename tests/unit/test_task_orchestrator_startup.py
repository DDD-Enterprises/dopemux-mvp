from __future__ import annotations

import asyncio
import builtins
import importlib.util
import sys
import uuid
from pathlib import Path

import pytest


WORKTREE_ROOT = Path(__file__).resolve().parents[2]
SERVICE_ROOT = WORKTREE_ROOT / "services" / "task-orchestrator"
MODULE_PATH = SERVICE_ROOT / "app" / "main.py"
SRC_PATH = WORKTREE_ROOT / "src"


def _purge_app_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            sys.modules.pop(module_name, None)


def _load_main_module(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_app_main_imports_without_preconfigured_src_path(monkeypatch: pytest.MonkeyPatch):
    _purge_app_modules()

    original_path = list(sys.path)
    monkeypatch.setattr(sys, "path", [str(SERVICE_ROOT)] + [p for p in original_path if p != str(SRC_PATH)])

    module = _load_main_module(f"task_orchestrator_startup_{uuid.uuid4().hex}")

    assert callable(module.get_workspace_root)
    assert str(SRC_PATH) in sys.path


def test_create_plane_coordinator_fallback_raises_runtime_error(monkeypatch: pytest.MonkeyPatch):
    _purge_app_modules()

    original_path = list(sys.path)
    monkeypatch.setattr(sys, "path", [str(SERVICE_ROOT)] + [p for p in original_path if p != str(SRC_PATH)])

    original_import = builtins.__import__

    def failing_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level == 1 and name == "core.coordinator":
            raise ImportError("forced relative coordinator import failure")
        if level == 0 and name == "app.core.coordinator":
            raise ImportError("forced absolute coordinator import failure")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", failing_import)

    module = _load_main_module(f"task_orchestrator_startup_fallback_{uuid.uuid4().hex}")

    with pytest.raises(RuntimeError, match="forced absolute coordinator import failure"):
        asyncio.run(module.create_plane_coordinator("workspace-123"))
