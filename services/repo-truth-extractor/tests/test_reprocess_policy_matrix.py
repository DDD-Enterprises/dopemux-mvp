from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "lib" / "reprocess_policy.py"
    spec = importlib.util.spec_from_file_location("reprocess_policy", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_policy_matrix_parse_truncation_routes_to_shrink_lane() -> None:
    module = _load_module()
    action = module.decide_action(final_failure_type="parse", parse_shape="truncated_string")
    assert action["action"] == "rerun_shrink_on_truncation"
    assert action["rerun"] is True


def test_policy_matrix_rate_limit_routes_to_conservative_rerun() -> None:
    module = _load_module()
    action = module.decide_action(final_failure_type="quota_or_billing", parse_shape=None)
    assert action["action"] == "rerun_conservative"
    assert action["partition_workers"] == 1


def test_policy_matrix_auth_disables_auto_rerun() -> None:
    module = _load_module()
    action = module.decide_action(final_failure_type="auth", parse_shape=None)
    assert action["action"] == "manual_auth_fix"
    assert action["rerun"] is False


def test_policy_matrix_io_persist_regenerates_success() -> None:
    module = _load_module()
    action = module.decide_action(final_failure_type="io_persist", parse_shape=None)
    assert action["action"] == "rerun_regenerate_success"
    assert action["rerun"] is True


def test_policy_matrix_parse_other_unbalanced_routes_to_shrink_lane() -> None:
    module = _load_module()
    action = module.decide_action(
        final_failure_type="parse",
        parse_shape="other",
        parse_shape_row={
            "shape": "other",
            "quotes_mod2": 0,
            "unmatched_closer_count": 2,
            "has_unmatched_closer": True,
        },
    )
    assert action["action"] == "rerun_shrink_on_malformed"
    assert action["rerun"] is True
