"""Optional pytest plugin: keep other suites off the real keychain.

Once W05 lands, the existing tests of these writers reach `dopemux.auth.get_token`.
On a Mac with issued tokens that would read the real keychain. Run those suites with

    PYTHONPATH=tests/unit/runner_memory_2a_r2_w05 pytest -p keychain_guard_plugin ...

and every `get_token` fails with KeychainError, which is the Linux-container case.
"""

import importlib

import pytest


@pytest.fixture(autouse=True)
def _no_real_keychain(monkeypatch):
    keychain = importlib.import_module("dopemux.auth.keychain")
    monkeypatch.setattr(keychain, "SECURITY_BIN", "/nonexistent/security")
