"""Shared fixtures for the Wave 2A R2 W01 (dope-memory identity) tests.

The dope-memory service modules are top-level imports (``chronicle``,
``mcp_http``, ``auth_identity`` ...), so the service directory must be on
``sys.path``.  It is appended (never prepended) so the service's top-level
``utils.py`` cannot shadow the repo's own ``utils`` package.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICE_DIR = REPO_ROOT / "services" / "working-memory-assistant"

if str(SERVICE_DIR) not in sys.path:
    sys.path.append(str(SERVICE_DIR))


@pytest.fixture()
def ledger_path(tmp_path, monkeypatch) -> Path:
    path = tmp_path / "ledger" / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(path))
    return path
