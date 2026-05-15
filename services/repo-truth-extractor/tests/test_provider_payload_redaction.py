from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from _v5_smoke_helpers import load_runner_module
import llm_runtime
from lib.prescan.corpus_walker import CorpusWalker
from lib.prescan.grok_passes import PASS_IDS, GrokPassRunner
from lib.prescan.models import FileEntry, PrescanConfig
from output_safety import sanitize_text_for_provider_payload


SAFE_HASH = "a" * 64
SAFE_MODEL = "grok-4.20-beta-0309-non-reasoning"
SAFE_PATH = "services/repo-truth-extractor/run_extraction_v5.py"


def _secret_values() -> dict[str, str]:
    return {
        "api_key": "sk-" + ("A" * 24) + "9z",
        "token": "tok_" + ("B" * 26) + "7q",
        "bearer": "Bearer " + ("C" * 26) + "8r",
        "password": "pw-" + ("D" * 24) + "9s",
        "webhook": "whsec_" + ("E" * 30) + "0t",
        "long_literal": "Ab3" + ("Cd" * 22),
        "aws_key": "AKIA" + ("F" * 16),
        "private_key": (
            "-----BEGIN PRIVATE KEY-----\n"
            + ("M" * 64)
            + "\n-----END PRIVATE KEY-----"
        ),
    }


def _secret_fixture_text() -> tuple[str, dict[str, str]]:
    values = _secret_values()
    return (
        "\n".join(
            [
                f"api_key = \"{values['api_key']}\"",
                f"Authorization: {values['bearer']}",
                f"token: {values['token']}",
                f"password={values['password']}",
                f"webhook_secret = \"{values['webhook']}\"",
                f"private_key = \"{values['private_key']}\"",
                f"loose_token = {values['long_literal']}",
                f"aws_access_key_id = {values['aws_key']}",
                f"sha256 = {SAFE_HASH}",
                f"model = {SAFE_MODEL}",
                f"path = {SAFE_PATH}",
                "ordinary prose remains available for provider context",
            ]
        )
        + "\n",
        values,
    )


def _assert_values_redacted(rendered: str, values: dict[str, str]) -> None:
    for raw_value in values.values():
        assert raw_value not in rendered
    assert values["bearer"].split()[-1] not in rendered
    assert "[REDACTED" in rendered


def test_provider_payload_sanitizer_redacts_secret_shapes_but_preserves_context() -> None:
    fixture_text, values = _secret_fixture_text()

    sanitized = sanitize_text_for_provider_payload(fixture_text)

    _assert_values_redacted(sanitized, values)
    assert SAFE_HASH in sanitized
    assert SAFE_MODEL in sanitized
    assert SAFE_PATH in sanitized
    assert "ordinary prose remains available" in sanitized


def test_grok_file_preview_redacts_secret_shaped_file_content(tmp_path: Path) -> None:
    fixture_text, values = _secret_fixture_text()
    source_path = tmp_path / "src" / "app.py"
    source_path.parent.mkdir(parents=True)
    source_path.write_text(fixture_text, encoding="utf-8")
    runner = GrokPassRunner(PrescanConfig(repo_root=tmp_path, output_dir=tmp_path / "out"))

    preview = runner._get_file_preview(
        FileEntry(rel_path="src/app.py", size_bytes=len(fixture_text), extension=".py")
    )

    _assert_values_redacted(preview, values)
    assert SAFE_HASH in preview
    assert SAFE_PATH in preview


def test_grok_pass_payload_builders_sanitize_nested_content_without_provider_call(
    tmp_path: Path,
) -> None:
    fixture_text, values = _secret_fixture_text()
    runner = GrokPassRunner(PrescanConfig(repo_root=tmp_path, output_dir=tmp_path / "out"))
    called_provider = False

    def fail_if_called(*_args: Any, **_kwargs: Any) -> None:
        nonlocal called_provider
        called_provider = True
        raise AssertionError("provider boundary should not be invoked by payload builders")

    runner._call_grok = fail_if_called  # type: ignore[method-assign]
    intelligence = {
        "duplicate_groups": {
            "dup-1": [
                {
                    "rel_path": SAFE_PATH,
                    "content_hash": SAFE_HASH,
                    "preview": fixture_text,
                }
            ]
        },
        "version_chains": {"chain-1": [SAFE_PATH]},
        "corpus_summary": {
            "included_files": 1,
            "notes": fixture_text,
            "content_hash": SAFE_HASH,
        },
        "code_intelligence": {
            SAFE_PATH: {
                "symbols": [{"name": "handler"}],
                "complexity_score": 3,
                "api_surfaces": [fixture_text],
            }
        },
        "ghost_files": [{"path": SAFE_PATH, "notes": fixture_text}],
        "extraction_hints": {"planned_features": [{"path": SAFE_PATH, "notes": fixture_text}]},
        "cost_estimate": {"model_id": SAFE_MODEL, "notes": fixture_text},
    }
    prior = {
        "dedup": {"reasoning": fixture_text},
        "discover": {"hidden_features": [{"path": SAFE_PATH, "description": fixture_text}]},
        "feasibility": {"planned_features": [{"path": SAFE_PATH, "reasoning": fixture_text}]},
    }

    for pass_id in PASS_IDS:
        payload = runner._build_provider_payload(pass_id, intelligence, prior)
        rendered = json.dumps(payload, sort_keys=True)
        _assert_values_redacted(rendered, values)
        assert SAFE_PATH in rendered
        assert SAFE_HASH in rendered or pass_id in {"discover", "feasibility", "optimize"}

    assert called_provider is False


def test_grok_execute_pass_sends_only_sanitized_payload_to_provider_boundary(
    tmp_path: Path,
) -> None:
    fixture_text, values = _secret_fixture_text()
    config = PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
        allow_online_llm=True,
    )
    runner = GrokPassRunner(config)
    captured: dict[str, str] = {}

    def fake_call_grok(
        pass_id: str,
        payload: str,
        candidate: dict[str, Any],
        attempt_record: Any,
        est_tokens: int = 0,
    ) -> dict[str, Any]:
        del pass_id, candidate, attempt_record, est_tokens
        captured["payload"] = payload
        return {"duplicate_assessments": []}

    runner._call_grok = fake_call_grok  # type: ignore[method-assign]
    result = runner._execute_pass(
        "dedup",
        {
            "duplicate_groups": {
                "dup-1": [{"rel_path": SAFE_PATH, "preview": fixture_text}]
            },
            "version_chains": {},
            "corpus_summary": {"content_hash": SAFE_HASH},
        },
        {},
        {"candidate_routes": {"dedup": [{"provider": "mock", "model_id": "mock", "api_key_env": "MOCK_KEY"}]}},
    )

    assert result == {"duplicate_assessments": []}
    _assert_values_redacted(captured["payload"], values)
    assert SAFE_PATH in captured["payload"]
    assert SAFE_HASH in captured["payload"]


def test_path_exclusions_remain_and_env_templates_are_preview_sanitized(
    tmp_path: Path,
) -> None:
    fixture_text, values = _secret_fixture_text()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('safe')\n", encoding="utf-8")
    (tmp_path / ".env").write_text(fixture_text, encoding="utf-8")
    (tmp_path / ".env.local").write_text(fixture_text, encoding="utf-8")
    (tmp_path / "deploy.key").write_text(fixture_text, encoding="utf-8")
    (tmp_path / "id_rsa").write_text(fixture_text, encoding="utf-8")
    (tmp_path / ".env.example").write_text(fixture_text, encoding="utf-8")

    config = PrescanConfig(repo_root=tmp_path, output_dir=tmp_path / "out")
    entries = CorpusWalker(config).walk()
    included = {entry.rel_path for entry in entries if entry.include}
    observed = {entry.rel_path for entry in entries}

    assert ".env" not in observed
    assert ".env.local" not in observed
    assert "deploy.key" not in observed
    assert "id_rsa" not in observed
    assert ".env.example" in included

    runner = GrokPassRunner(config)
    preview = runner._get_file_preview(
        FileEntry(
            rel_path=".env.example",
            size_bytes=len(fixture_text),
            extension=".example",
        )
    )
    _assert_values_redacted(preview, values)
    assert SAFE_HASH in preview


def test_v5_chat_payload_builder_redacts_before_request_body_construction() -> None:
    runner = load_runner_module()
    fixture_text, values = _secret_fixture_text()

    payload = runner.build_chat_payload(
        "xai",
        SAFE_MODEL,
        "System prompt names api_key but does not assign one.",
        fixture_text,
        force_json_output=True,
    )
    rendered = runner.serialize_payload_body(payload).decode("utf-8")

    _assert_values_redacted(rendered, values)
    assert "System prompt names api_key" in rendered
    assert SAFE_MODEL in rendered
    assert SAFE_PATH in rendered


def test_v5_batch_request_builder_redacts_before_batch_body_serialization() -> None:
    runner = load_runner_module()
    fixture_text, values = _secret_fixture_text()

    request = runner.build_v5_batch_request(
        custom_id="D_P0001",
        model_id=SAFE_MODEL,
        system_prompt=fixture_text,
        user_content=fixture_text,
        provider="xai",
        selected_route=("xai", SAFE_MODEL, "XAI_API_KEY"),
        transport="openai_sdk",
        strict_contract_required=False,
        step_contract=None,
        artifact_names=("DOC_INDEX.part1.json",),
        force_json_output=True,
        metadata={"phase": "D", "step_id": "D1", "partition_id": "D_P0001"},
    )
    rendered = json.dumps(
        {
            "system_prompt": request.system_prompt,
            "user_content": request.user_content,
            "model_id": request.model_id,
            "metadata": request.metadata,
        },
        sort_keys=True,
    )

    _assert_values_redacted(rendered, values)
    assert SAFE_MODEL in rendered
    assert SAFE_PATH in rendered


def test_llm_runtime_sanitizes_prompts_before_dependency_payload_build() -> None:
    fixture_text, values = _secret_fixture_text()
    captured: dict[str, str] = {}

    def build_chat_payload(
        provider: str,
        model_id: str,
        system_prompt: str,
        user_content: str,
        **_kwargs: Any,
    ) -> dict[str, Any]:
        captured["system_prompt"] = system_prompt
        captured["user_content"] = user_content
        return {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }

    deps = llm_runtime.LLMRuntimeDeps(
        live_llm_calls_blocked_for_tests=lambda: False,
        live_llm_tests_env="RTE_TEST_LIVE_OK",
        llm_base_url=lambda _provider, _cfg: "https://example.test/v1",
        transport_for_provider=lambda _provider, _cfg: "openai_sdk",
        resolve_api_key=lambda _provider, api_key_env: ("", api_key_env),
        build_chat_payload=build_chat_payload,
        serialize_payload_body=lambda payload: json.dumps(payload),
        measure_payload_bytes_from_body=lambda body: len(body),
        gemini_auth_mode_sequence=lambda _mode, _base_url: ["sdk_bearer"],
        make_url=lambda _provider, base_url, _cfg, _api_key, _mode: base_url + "/chat/completions",
        make_headers=lambda *_args: {},
        sdk_auth_present_flags=lambda _provider, present: {"bearer": present},
        build_auth_present_flags=lambda _headers, _query_key: {},
        endpoint_effective=lambda url: url,
        endpoint_fingerprint=lambda _url: {"endpoint_sha256": SAFE_HASH},
        provider_signature=lambda provider, model_id, endpoint_url, _mode: f"{provider}:{model_id}:{endpoint_url}",
        get_http_session=lambda: None,
        get_gemini_client=lambda _api_key: None,
        extract_text_from_gemini_response=lambda _response: "",
        get_xai_client=lambda _api_key: None,
        get_openrouter_client=lambda _api_key: None,
        get_openai_client=lambda _unused, _api_key: None,
        extract_text_from_chat_completion=lambda _response: "",
        summarize_llm_response=lambda **_kwargs: {},
        exception_status_code=lambda _exc: None,
        exception_response_text=lambda _exc: "",
        classify_failure_type=lambda _status, _body, _text: "unknown",
        extract_provider_error_reason=lambda _body: None,
        sanitize_error_text=lambda text: text,
        capture_exception_metadata=lambda _exc: {},
        new_trace_id=lambda: "trace-test",
        new_span_id=lambda: "span-test",
        cost_abort_failure_meta=lambda **kwargs: dict(kwargs),
        should_retry=lambda _status, _failure, _exc, _policy: False,
        backoff_seconds=lambda _attempt, _base, _max: 0.0,
        is_spend_aborted=lambda: False,
        sha256_text=lambda _path: SAFE_HASH,
        runner_script=Path("run_extraction_v5.py"),
        is_auth_classified_failure=lambda _failure: False,
        classify_escalation_class=lambda **_kwargs: "none",
        is_break_glass_opus_route=lambda _route: False,
        provider_api_key_env={"xai": "XAI_API_KEY"},
        max_files_for_phase=lambda _phase, _cfg: 1,
        estimate_text_tokens=lambda system, user: len(system) + len(user),
        project_output_tokens=lambda input_tokens: input_tokens,
        check_projected_cost_limit=lambda **_kwargs: None,
        accumulate_runtime_spend=lambda **_kwargs: None,
        cost_limit_exceeded_error=RuntimeError,
        now_iso=lambda: "2026-05-15T00:00:00+00:00",
        strip_outer_json_fence=lambda _text: None,
        extract_first_fenced_json_block=lambda _text: None,
        extract_first_json_object=lambda _text: None,
        is_semantic_eof_eligible=lambda _exc, _text: False,
        try_repair_json_truncation=lambda _text, _exc: None,
    )

    result = llm_runtime.call_llm(
        deps,
        provider="xai",
        model_id=SAFE_MODEL,
        api_key_env="XAI_API_KEY",
        system_prompt=fixture_text,
        user_content=fixture_text,
        cfg=SimpleNamespace(gemini_auth_mode="auto"),
    )

    assert result["ok"] is False
    assert result["meta"]["failure_type"] == "auth_missing"
    _assert_values_redacted(captured["system_prompt"], values)
    _assert_values_redacted(captured["user_content"], values)
    assert SAFE_HASH in captured["user_content"]
    assert SAFE_MODEL in captured["user_content"]


def test_comparison_lane_projects_cost_from_sanitized_provider_payload(
    tmp_path: Path,
) -> None:
    fixture_text, values = _secret_fixture_text()
    token_projection_inputs: dict[str, str] = {}
    cost_gate_inputs: dict[str, int] = {}

    def estimate_text_tokens(system: str, user: str) -> int:
        token_projection_inputs["system"] = system
        token_projection_inputs["user"] = user
        return len(system) + len(user)

    def check_projected_cost_limit(_cfg: Any, **kwargs: Any) -> None:
        cost_gate_inputs["input_tokens"] = int(kwargs["input_tokens"])

    deps = llm_runtime.LLMRuntimeDeps(
        live_llm_calls_blocked_for_tests=lambda: False,
        live_llm_tests_env="RTE_TEST_LIVE_OK",
        llm_base_url=lambda _provider, _cfg: "https://example.test/v1",
        transport_for_provider=lambda _provider, _cfg: "openai_sdk",
        resolve_api_key=lambda _provider, api_key_env: ("", api_key_env),
        build_chat_payload=lambda *_args, **_kwargs: {},
        serialize_payload_body=lambda payload: json.dumps(payload),
        measure_payload_bytes_from_body=lambda body: len(body),
        gemini_auth_mode_sequence=lambda _mode, _base_url: ["sdk_bearer"],
        make_url=lambda _provider, base_url, _cfg, _api_key, _mode: base_url + "/chat/completions",
        make_headers=lambda *_args: {},
        sdk_auth_present_flags=lambda _provider, present: {"bearer": present},
        build_auth_present_flags=lambda _headers, _query_key: {},
        endpoint_effective=lambda url: url,
        endpoint_fingerprint=lambda _url: {"endpoint_sha256": SAFE_HASH},
        provider_signature=lambda provider, model_id, endpoint_url, _mode: f"{provider}:{model_id}:{endpoint_url}",
        get_http_session=lambda: None,
        get_gemini_client=lambda _api_key: None,
        extract_text_from_gemini_response=lambda _response: "",
        get_xai_client=lambda _api_key: None,
        get_openrouter_client=lambda _api_key: None,
        get_openai_client=lambda _unused, _api_key: None,
        extract_text_from_chat_completion=lambda _response: "",
        summarize_llm_response=lambda **_kwargs: {},
        exception_status_code=lambda _exc: None,
        exception_response_text=lambda _exc: "",
        classify_failure_type=lambda _status, _body, _text: "unknown",
        extract_provider_error_reason=lambda _body: None,
        sanitize_error_text=lambda text: text,
        capture_exception_metadata=lambda _exc: {},
        new_trace_id=lambda: "trace-test",
        new_span_id=lambda: "span-test",
        cost_abort_failure_meta=lambda **kwargs: dict(kwargs),
        should_retry=lambda _status, _failure, _exc, _policy: False,
        backoff_seconds=lambda _attempt, _base, _max: 0.0,
        is_spend_aborted=lambda: False,
        sha256_text=lambda _path: SAFE_HASH,
        runner_script=Path("run_extraction_v5.py"),
        is_auth_classified_failure=lambda _failure: False,
        classify_escalation_class=lambda **_kwargs: "none",
        is_break_glass_opus_route=lambda _route: False,
        provider_api_key_env={"xai": "XAI_API_KEY"},
        max_files_for_phase=lambda _phase, _cfg: 1,
        estimate_text_tokens=estimate_text_tokens,
        project_output_tokens=lambda input_tokens: input_tokens,
        check_projected_cost_limit=check_projected_cost_limit,
        accumulate_runtime_spend=lambda **_kwargs: None,
        cost_limit_exceeded_error=RuntimeError,
        now_iso=lambda: "2026-05-15T00:00:00+00:00",
        strip_outer_json_fence=lambda _text: None,
        extract_first_fenced_json_block=lambda _text: None,
        extract_first_json_object=lambda _text: None,
        is_semantic_eof_eligible=lambda _exc, _text: False,
        try_repair_json_truncation=lambda _text, _exc: None,
    )

    results = llm_runtime.run_comparison_lane(
        deps,
        phase="D",
        step_id="D1",
        partitions=[{"id": "P1", "paths": [SAFE_PATH]}],
        phase_dir=tmp_path,
        cfg=SimpleNamespace(
            compare_provider="xai",
            compare_model=SAFE_MODEL,
            file_truncate_chars=1000,
            home_scan_mode="safe",
            max_chars=1000,
            router=None,
        ),
        prompt_text=fixture_text,
        output_artifacts=("RESULT.json",),
        build_partition_context_fn=lambda **_kwargs: (fixture_text, {}),
        call_llm_fn=lambda **_kwargs: {"text": '{"ok": true}', "meta": {"status_code": 200}},
        parse_json_from_response_fn=lambda text, metadata_out=None: json.loads(text),
        coerce_artifacts_from_response_fn=lambda parsed, _raw, _expected: [
            {"artifact_name": "RESULT.json", "payload": parsed}
        ],
        finalize_response_parse_provenance=lambda provenance, **_kwargs: provenance,
        log_response_parse_repair=lambda _provenance: None,
    )

    assert results[0]["success"] is True
    _assert_values_redacted(token_projection_inputs["system"], values)
    _assert_values_redacted(token_projection_inputs["user"], values)
    assert cost_gate_inputs["input_tokens"] == len(token_projection_inputs["system"]) + len(
        token_projection_inputs["user"]
    )
