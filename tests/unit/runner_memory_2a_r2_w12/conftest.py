"""Fixtures for the Wave 2A R2 W12 tests (omitted write ids default to the binding).

dope-memory modules are top-level imports, so the service directory goes on
``sys.path`` (appended, never prepended, so the service's ``utils.py`` cannot
shadow the repo's ``utils`` package).  The ConPort fixtures (fake pool, REST
client, scoped module loader) are the W02 ones, re-exported here.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from ..runner_memory_2a_r2_w02.conftest import (  # noqa: F401  (re-exported fixtures)
    enhanced_server_module,
    load_conport_module,
    make_rest_server,
    rest_client,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICE_DIR = REPO_ROOT / "services" / "working-memory-assistant"

if str(SERVICE_DIR) not in sys.path:
    sys.path.append(str(SERVICE_DIR))


@pytest.fixture()
def ledger_path(tmp_path, monkeypatch) -> Path:
    path = tmp_path / "ledger" / "chronicle.sqlite"
    monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(path))
    return path
