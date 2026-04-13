from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


def _load_models_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "fl_int" / "models.py"
    spec = importlib.util.spec_from_file_location("fl_int_models_governance_test", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_every_fl_int_ladder_route_has_explicit_governance_classification() -> None:
    models = _load_models_module()

    observed_routes = {
        route
        for ladder in models.FL_INT_LADDERS.values()
        for route in ladder
    }
    classified_routes = set(models.FL_INT_ROUTE_RECORD_INDEX.keys())

    assert observed_routes == classified_routes


def test_current_fl_int_ladders_are_explicitly_non_confirmed() -> None:
    models = _load_models_module()

    statuses = {
        models.route_status_for(route)
        for ladder in models.FL_INT_LADDERS.values()
        for route in ladder
    }

    assert statuses == {models.FL_INT_ROUTE_STATUS_FUTURE_TARGET}


def test_step_ladder_records_preserve_route_identity_order() -> None:
    models = _load_models_module()
    step = next(step for step in models.FL_INT_STEPS if step.step_id == "F0")

    assert [record.route for record in models.ladder_records_for_step(step)] == models.ladder_for_step(step)
