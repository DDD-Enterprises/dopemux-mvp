"""TP-RTE-TRUTH-R2-003 — cap-enforcement hardening + ledger atomicity +
--llm-temperature.

MANDATORY-VERIFICATION tests for the three defects fixed by this packet:

  1. F-13 (A2-7 one-call overshoot) is covered by
     tests/test_run_extraction_v5_cost_cap.py::
     test_record_request_cost_refuses_breach_before_recording_spend and
     tests/test_costing_seam.py::
     test_spend_tracker_refuses_breach_before_recording_spend (plus the
     cost_cap_mode="post_hoc" companion tests proving the field is wired,
     not decorative).

  2. F-15 (SPEND_LEDGER.json non-atomic write) is covered here by
     test_write_json_atomic_survives_a_crash_before_the_atomic_replace.

  3. F-38/A2-8 (--llm-temperature flag; gpt-5 omission rule) is covered
     here by the test_llm_temperature_* tests below.

Each test in this file is written to FAIL if its corresponding fix is
reverted (see the packet's PROOF.json for the manual revert-and-rerun
mutation check performed for every test in this suite).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = REPO_ROOT / "services" / "repo-truth-extractor"


def _load_module(name: str, relative_path: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, SERVICE_ROOT / relative_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_runner():
    return _load_module("run_extraction_v5_r2_003", "run_extraction_v5.py")


def _make_cfg(runner: Any, **overrides: Any) -> Any:
    payload = {
        "dry_run": False,
        "max_files_docs": 35,
        "max_files_code": 20,
        "max_chars": 650000,
        "max_request_bytes": 200000,
        "file_truncate_chars": 70000,
        "home_scan_mode": "safe",
        "resume": False,
        "fail_fast_auth": True,
        "gemini_auth_mode": "auto",
        "gemini_transport": "sdk",
        "openai_transport": "openai_sdk",
        "xai_transport": "openai_sdk",
        "retry_policy": "default",
        "retry_max_attempts": 1,
        "retry_base_seconds": 0.0,
        "retry_max_seconds": 0.0,
        "phase_auth_fail_threshold": 1,
        "partition_workers": 1,
        "debug_phase_inputs": False,
        "fail_fast_missing_inputs": False,
        "routing_policy": "balanced_openrouter",
    }
    payload.update(overrides)
    return runner.RunnerConfig(**payload)


# ---------------------------------------------------------------------------
# F-15: atomic spend ledger writes (tmp file + os.replace)
# ---------------------------------------------------------------------------


def test_write_json_atomic_survives_a_crash_before_the_atomic_replace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simulate a process crash between "new content fully staged to a temp
    file" and "atomic rename into place" (the only window write_json_atomic
    leaves open). The durable target file must come through completely
    unchanged -- not truncated, not partially overwritten."""
    runner = _load_runner()
    target = tmp_path / "spend_ledger.json"

    original_payload = {
        "run_id": "run-durability-001",
        "total_cost_usd": 1.23,
        "cost_abort_triggered": False,
        "entries": [{"sequence": 1, "cost_usd": 1.23}],
    }
    runner.write_json_atomic(target, original_payload)
    original_bytes = target.read_bytes()
    assert b"1.23" in original_bytes

    def _simulated_crash(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("simulated crash: process killed before os.replace()")

    monkeypatch.setattr(runner.os, "replace", _simulated_crash)

    new_payload = {
        "run_id": "run-durability-001",
        "total_cost_usd": 999.99,
        "cost_abort_triggered": True,
        "entries": [{"sequence": 1, "cost_usd": 1.23}, {"sequence": 2, "cost_usd": 998.76}],
    }
    with pytest.raises(OSError):
        runner.write_json_atomic(target, new_payload)

    # The previous ledger contents must survive intact -- byte-for-byte,
    # not just "still valid JSON".
    assert target.read_bytes() == original_bytes
    survived = json.loads(target.read_text(encoding="utf-8"))
    assert survived["total_cost_usd"] == 1.23
    assert survived["cost_abort_triggered"] is False
    assert len(survived["entries"]) == 1

    # No leftover temp file from the failed write (best-effort cleanup).
    leftovers = [
        p for p in tmp_path.iterdir() if p.name.startswith(".spend_ledger.json.")
    ]
    assert leftovers == []


def test_write_json_atomic_writes_to_a_temp_file_in_the_same_directory_then_replaces(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Directly proves the atomic-write mechanism: a temp file is created in
    the SAME directory as the target (required for os.replace to be atomic
    on POSIX -- cross-filesystem renames are not atomic), and os.replace is
    the only thing that makes the new content visible at the target path."""
    runner = _load_runner()
    target = tmp_path / "spend_ledger.json"

    seen_tmp_paths: list[Path] = []
    real_replace = runner.os.replace

    def _spy_replace(src: Any, dst: Any) -> None:
        seen_tmp_paths.append(Path(src))
        assert Path(src).parent == Path(dst).parent
        real_replace(src, dst)

    monkeypatch.setattr(runner.os, "replace", _spy_replace)

    runner.write_json_atomic(target, {"hello": "world"})

    assert len(seen_tmp_paths) == 1
    assert seen_tmp_paths[0].name.startswith(".spend_ledger.json.")
    assert seen_tmp_paths[0].name.endswith(".tmp")
    assert not seen_tmp_paths[0].exists()  # renamed away
    assert json.loads(target.read_text(encoding="utf-8")) == {"hello": "world"}


def test_spend_ledger_snapshot_is_wired_to_the_atomic_writer(tmp_path: Path) -> None:
    """CostingDeps.write_json (the callable _write_spend_ledger_snapshot
    uses) must be the atomic writer, not the plain non-atomic write_json --
    otherwise F-15 is fixed in isolation but never actually reaches the
    money log at runtime."""
    runner = _load_runner()
    deps = runner._costing_deps()
    assert deps.write_json is runner.write_json_atomic
    assert deps.write_json is not runner.write_json


# ---------------------------------------------------------------------------
# F-38/A2-8: --llm-temperature (range-validated, gpt-5 omission preserved)
# ---------------------------------------------------------------------------


def test_llm_temperature_range_gate_accepts_boundaries_and_rejects_outside() -> None:
    runner = _load_runner()
    assert runner._llm_temperature_out_of_range(0.0) is False
    assert runner._llm_temperature_out_of_range(2.0) is False
    assert runner._llm_temperature_out_of_range(0.1) is False
    assert runner._llm_temperature_out_of_range(1.999) is False
    assert runner._llm_temperature_out_of_range(-0.01) is True
    assert runner._llm_temperature_out_of_range(2.01) is True
    assert runner._llm_temperature_out_of_range(5.0) is True


def test_cli_args_parser_exposes_llm_temperature_flag_with_default() -> None:
    runner = _load_runner()
    parser = runner.build_parser()
    args = parser.parse_args(["--phase", "A"])
    assert args.llm_temperature == pytest.approx(0.1)

    args2 = parser.parse_args(["--phase", "A", "--llm-temperature", "0.7"])
    assert args2.llm_temperature == pytest.approx(0.7)


def test_build_chat_payload_threads_custom_temperature_for_non_gpt5_models() -> None:
    """The operator-facing flag must actually change what is sent: a
    non-gpt-5 model gets the configured temperature verbatim."""
    runner = _load_runner()

    payload_default = runner.build_chat_payload(
        provider="openai",
        model_id="gpt-4o-mini",
        system_prompt="system",
        user_content="user",
    )
    assert payload_default["temperature"] == pytest.approx(0.1)

    payload_custom = runner.build_chat_payload(
        provider="openai",
        model_id="gpt-4o-mini",
        system_prompt="system",
        user_content="user",
        default_temperature=1.7,
    )
    assert payload_custom["temperature"] == pytest.approx(1.7)

    payload_xai = runner.build_chat_payload(
        provider="xai",
        model_id="grok-4.3",
        system_prompt="system",
        user_content="user",
        default_temperature=0.0,
    )
    assert payload_xai["temperature"] == pytest.approx(0.0)


def test_build_chat_payload_omits_temperature_for_gpt5_regardless_of_flag() -> None:
    """CRITICAL: the gpt-5 omission rule (resolve_temperature) must survive
    the new flag untouched. Even an operator explicitly requesting a custom
    --llm-temperature must NOT get a temperature parameter sent to a gpt-5
    model -- those models reject the parameter outright."""
    runner = _load_runner()

    for custom_temperature in (0.0, 0.1, 0.7, 1.5, 2.0):
        payload = runner.build_chat_payload(
            provider="openai",
            model_id="gpt-5.5",
            system_prompt="system",
            user_content="user",
            default_temperature=custom_temperature,
        )
        assert "temperature" not in payload, (
            f"gpt-5 payload must omit temperature even with "
            f"default_temperature={custom_temperature}"
        )

    # Non-gpt-5 openai models are unaffected by the carve-out.
    payload_mini = runner.build_chat_payload(
        provider="openai",
        model_id="gpt-4o-mini",
        system_prompt="system",
        user_content="user",
        default_temperature=1.2,
    )
    assert payload_mini["temperature"] == pytest.approx(1.2)


def test_runner_config_llm_temperature_defaults_and_is_settable() -> None:
    runner = _load_runner()
    cfg_default = _make_cfg(runner)
    assert cfg_default.llm_temperature == pytest.approx(0.1)

    cfg_custom = _make_cfg(runner, llm_temperature=0.42)
    payload = runner.build_chat_payload(
        provider="openai",
        model_id="gpt-4o-mini",
        system_prompt="system",
        user_content="user",
        default_temperature=cfg_custom.llm_temperature,
    )
    assert payload["temperature"] == pytest.approx(0.42)


def test_call_llm_threads_runner_config_temperature_into_gemini_native_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """llm_runtime.call_llm's Gemini native-SDK branch built its own config
    dict with a hardcoded 0.1 (a second, independent hardcode site from
    build_chat_payload's). Prove RunnerConfig.llm_temperature reaches it."""
    llm_runtime = _load_module("llm_runtime_r2_003", "llm_runtime.py")
    runner = _load_runner()

    captured_configs: list[dict] = []

    class _FakeGeminiModels:
        def generate_content(self, *, model: str, contents: str, config: dict):
            captured_configs.append(config)

            class _Resp:
                pass

            return _Resp()

    class _FakeGeminiClient:
        models = _FakeGeminiModels()

    cfg = _make_cfg(runner, llm_temperature=1.8)

    deps = llm_runtime.LLMRuntimeDeps(
        live_llm_calls_blocked_for_tests=lambda: False,
        live_llm_tests_env="RTE_TEST_LIVE_OK",
        llm_base_url=lambda _provider, _cfg: "https://example.test/v1beta",
        transport_for_provider=lambda _provider, _cfg: "gemini_sdk",
        resolve_api_key=lambda _provider, api_key_env: ("test-key", api_key_env),
        build_chat_payload=runner.build_chat_payload,
        serialize_payload_body=lambda payload: json.dumps(payload).encode("utf-8"),
        measure_payload_bytes_from_body=lambda body: len(body),
        gemini_auth_mode_sequence=lambda _mode, _base_url: ["sdk_api_key"],
        make_url=lambda *a, **k: "https://example.test/v1beta/models",
        make_headers=lambda *a, **k: {},
        sdk_auth_present_flags=lambda *a, **k: {"has_auth": True},
        build_auth_present_flags=lambda *a, **k: {"has_auth": True},
        endpoint_effective=lambda url: url,
        endpoint_fingerprint=lambda url: {"endpoint_fingerprint_hash": "x"},
        provider_signature=lambda *a, **k: "sig",
        get_http_session=lambda: None,
        get_gemini_client=lambda api_key, timeout_seconds=None: _FakeGeminiClient(),
        extract_text_from_gemini_response=lambda resp: "OK",
        get_xai_client=lambda api_key: None,
        get_openrouter_client=lambda api_key: None,
        get_openai_client=lambda base_url, api_key: None,
        extract_text_from_chat_completion=lambda resp: "OK",
        summarize_llm_response=lambda **k: {},
        exception_status_code=lambda exc: None,
        exception_response_text=lambda exc: "",
        classify_failure_type=lambda *a, **k: "unknown",
        extract_provider_error_reason=lambda text: None,
        sanitize_error_text=lambda text: text,
        capture_exception_metadata=lambda exc: {},
        new_trace_id=lambda: "trace",
        new_span_id=lambda: "span",
        cost_abort_failure_meta=lambda **k: {},
        should_retry=lambda *a, **k: False,
        backoff_seconds=lambda *a, **k: 0.0,
        is_spend_aborted=lambda: False,
        sha256_text=lambda p: "sha",
        runner_script=SERVICE_ROOT / "run_extraction_v5.py",
        is_auth_classified_failure=lambda reason: False,
        classify_escalation_class=lambda *a, **k: "none",
        is_break_glass_opus_route=lambda route: False,
        provider_api_key_env={"gemini": "GEMINI_API_KEY"},
        max_files_for_phase=lambda *a, **k: 10,
        estimate_text_tokens=lambda text, model: len(text) // 4,
        project_output_tokens=lambda n: n // 10,
        check_projected_cost_limit=lambda **k: None,
        accumulate_runtime_spend=lambda **k: None,
        cost_limit_exceeded_error=RuntimeError,
        now_iso=lambda: "2026-07-27T00:00:00+00:00",
        strip_outer_json_fence=lambda text: text,
        extract_first_fenced_json_block=lambda text: None,
        extract_first_json_object=lambda text: None,
        is_semantic_eof_eligible=lambda exc, text: False,
        try_repair_json_truncation=lambda text, exc: None,
    )

    result = llm_runtime.call_llm(
        deps,
        provider="gemini",
        model_id="gemini-3-flash-preview",
        api_key_env="GEMINI_API_KEY",
        system_prompt="You are a test.",
        user_content="Say OK.",
        cfg=cfg,
    )

    assert result["ok"] is True
    assert len(captured_configs) == 1
    assert captured_configs[0]["temperature"] == pytest.approx(1.8)
