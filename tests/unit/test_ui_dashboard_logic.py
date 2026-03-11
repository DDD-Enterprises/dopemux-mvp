from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "ui-dashboard-backend" / "app.py"
)


@pytest.fixture(scope="module")
def dashboard_backend_module():
    spec = importlib.util.spec_from_file_location("ui_dashboard_backend_app", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "load, expected_status",
    [
        (0.0, "low"),
        (0.29, "low"),
        (0.3, "optimal"),
        (0.59, "optimal"),
        (0.6, "high"),
        (0.79, "high"),
        (0.8, "critical"),
        (1.0, "critical"),
        (-0.5, "low"),
        (1.5, "critical"),
    ],
)
def test_status_from_load_boundaries(dashboard_backend_module, load, expected_status):
    assert dashboard_backend_module._status_from_load(load) == expected_status


@pytest.mark.parametrize(
    "value, minimum, maximum, expected",
    [
        (0.5, 0.0, 1.0, 0.5),
        (-0.1, 0.0, 1.0, 0.0),
        (1.1, 0.0, 1.0, 1.0),
        (5.0, 2.0, 4.0, 4.0),
        (1.0, 2.0, 4.0, 2.0),
    ],
)
def test_clamp(dashboard_backend_module, value, minimum, maximum, expected):
    assert dashboard_backend_module._clamp(value, minimum, maximum) == expected


def test_recommendation_for_status(dashboard_backend_module):
    assert (
        dashboard_backend_module._recommendation_for_status("low")
        == "Good window for deep, complex work. Protect focus for the next 45 minutes."
    )
    assert (
        dashboard_backend_module._recommendation_for_status("optimal")
        == "Continue current work patterns with short, planned breaks."
    )
    assert (
        dashboard_backend_module._recommendation_for_status("high")
        == "Reduce scope, batch interruptions, and finish one task before switching."
    )
    assert (
        dashboard_backend_module._recommendation_for_status("critical")
        == "Mandatory break now; switch to a low-complexity recovery task afterward."
    )
    # Test fallback
    assert (
        dashboard_backend_module._recommendation_for_status("unknown")
        == "Continue current work patterns with short, planned breaks."
    )
