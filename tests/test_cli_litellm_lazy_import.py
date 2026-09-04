"""Regression tests for keeping generic CLI imports offline from LiteLLM."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"


def _run_isolated_python(script: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_PATH)
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_litellm_proxy_import_does_not_import_litellm() -> None:
    result = _run_isolated_python(
        """
        import builtins
        import sys

        original_import = builtins.__import__

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "litellm" or name.startswith("litellm."):
                raise RuntimeError(f"blocked litellm import: {name}")
            return original_import(name, globals, locals, fromlist, level)

        builtins.__import__ = guarded_import
        import dopemux.litellm_proxy

        if "litellm" in sys.modules:
            raise AssertionError("litellm present in sys.modules after import")
        """
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_generic_cli_import_offline_no_litellm_no_network() -> None:
    result = _run_isolated_python(
        """
        import builtins
        import socket
        import sys

        original_import = builtins.__import__

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "litellm" or name.startswith("litellm."):
                raise RuntimeError(f"blocked litellm import: {name}")
            return original_import(name, globals, locals, fromlist, level)

        def blocked_network(*args, **kwargs):
            raise RuntimeError("network attempted during CLI import")

        builtins.__import__ = guarded_import
        socket.socket.connect = blocked_network
        socket.socket.connect_ex = blocked_network
        socket.create_connection = blocked_network

        import dopemux.cli

        if "litellm" in sys.modules:
            raise AssertionError("litellm present in sys.modules after CLI import")
        """
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_sync_litellm_database_imports_litellm_lazily(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def blocked_network(*args: object, **kwargs: object) -> None:
        raise RuntimeError("network attempted during lazy LiteLLM import")

    monkeypatch.setattr(socket.socket, "connect", blocked_network)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked_network)
    monkeypatch.setattr(socket, "create_connection", blocked_network)

    import dopemux.litellm_proxy

    monkeypatch.setattr("dopemux.litellm_proxy.shutil.which", lambda _: "/usr/bin/prisma")

    class PrismaBlocked(RuntimeError):
        pass

    def blocked_prisma(*args: object, **kwargs: object) -> None:
        raise PrismaBlocked("prisma execution intentionally blocked")

    monkeypatch.setattr("dopemux.litellm_proxy.subprocess.run", blocked_prisma)

    sys.modules.pop("litellm", None)
    assert "litellm" not in sys.modules

    try:
        dopemux.litellm_proxy.sync_litellm_database(
            tmp_path, "postgresql://user:pass@localhost:5432/litellm"
        )
    except PrismaBlocked:
        pass

    assert "litellm" in sys.modules
