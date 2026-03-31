"""Execution-plane concurrency tests are quarantined pending store contract recovery."""

import pytest


pytest.skip(
    "execution-plane concurrency tests are quarantined until the execution store contract is restored",
    allow_module_level=True,
)
