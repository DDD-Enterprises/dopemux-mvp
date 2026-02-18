import importlib.util
from pathlib import Path
import sys


def _load_runner_module():
    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    module_path = root / "UPGRADES" / "run_extraction_v3.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_classify_llm_failure_nonretryable_auth_marker():
    runner = _load_runner_module()
    result = runner.classify_llm_failure(
        provider="gemini",
        status=401,
        err_msg="API key not found",
        err_type="auth_error",
        err_code="",
        exception=None,
    )
    assert result["kind"] == "nonretryable"


def test_classify_failure_payload_and_rate_are_deterministic():
    runner = _load_runner_module()
    payload = runner.classify_failure(
        error_text="request payload size exceeds limit",
        http_status=413,
        provider_hint="openai",
    )
    rate = runner.classify_failure(
        error_text="rate limit exceeded",
        http_status=429,
        provider_hint="gemini",
    )
    assert payload["type"] == "shrink"
    assert rate["type"] == "rate"


def test_compute_request_hash_is_deterministic():
    runner = _load_runner_module()
    value_a = runner.compute_request_hash("system", "payload")
    value_b = runner.compute_request_hash("system", "payload")
    value_c = runner.compute_request_hash("system", "payload-changed")
    assert value_a == value_b
    assert value_a != value_c


def test_next_shrink_action_split_first_then_reduce():
    runner = _load_runner_module()
    budget = {"max_chars": 100000, "file_truncate_chars": 10000, "max_files": 80}
    action_0, budget_0, stage_0 = runner.next_shrink_action(
        shrink_stage=0,
        budget=budget,
        files_count=40,
        split_depth=0,
        prefer_split_first=True,
        min_files_per_part=12,
        max_split_depth=4,
        active_partition_count=1,
        max_partitions_per_step=64,
    )
    assert action_0 == "split"
    assert budget_0 == budget
    assert stage_0 == 1

    action_1, budget_1, stage_1 = runner.next_shrink_action(
        shrink_stage=1,
        budget=budget,
        files_count=8,
        split_depth=2,
        prefer_split_first=True,
        min_files_per_part=12,
        max_split_depth=4,
        active_partition_count=10,
        max_partitions_per_step=64,
    )
    assert action_1 == "reduce_files"
    assert budget_1["max_files"] < budget["max_files"]
    assert stage_1 == 2


def test_choose_recovery_action_fail_for_auth():
    runner = _load_runner_module()
    action = runner.choose_recovery_action(
        classification={"type": "auth", "reason": "status_401"},
        partition_state={
            "shrink_stage": 0,
            "budget": {"max_chars": 100000, "file_truncate_chars": 12000, "max_files": 60},
            "files_count": 30,
            "split_depth": 0,
            "prefer_split_first": True,
            "min_files_per_part": 12,
            "max_split_depth": 4,
            "active_partition_count": 1,
            "max_partitions_per_step": 64,
            "shrink_files_mult": 0.7,
            "shrink_trunc_mult": 0.7,
            "shrink_maxchars_mult": 0.8,
        },
    )
    assert action == "fail"
