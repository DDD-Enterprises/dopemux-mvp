from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path
import sys

from _fl_int_helpers import ensure_service_root_on_path, load_run_module


def _load_output_safety_module():
    ensure_service_root_on_path()
    return importlib.import_module("output_safety")


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_gate_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "validate_pre_live_gate_v25.py"
    spec = importlib.util.spec_from_file_location("validate_pre_live_gate_v25", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_run_s_int():
    root = Path(__file__).resolve().parents[3]
    service_root = root / "services" / "repo-truth-extractor"
    if str(service_root) not in sys.path:
        sys.path.insert(0, str(service_root))
    return importlib.import_module("s_int.run_s_int")


def test_sanitize_payload_redacts_secret_fields_but_preserves_env_metadata() -> None:
    output_safety = _load_output_safety_module()
    payload = {
        "api_key": "super-secret-value",
        "api_key_env": "XAI_API_KEY",
        "api_key_present": True,
        "input_tokens": 123,
        "Authorization": "Bearer top-secret-token",
        "nested": {"password": "letmein"},
        "endpoint": "https://example.test/chat?key=abc123",
        "sha256": "abcdef1234567890",
    }

    sanitized = output_safety.sanitize_payload_for_output(payload)
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["api_key_env"] == "XAI_API_KEY"
    assert sanitized["api_key_present"] is True
    assert sanitized["input_tokens"] == 123
    assert sanitized["Authorization"] == "[REDACTED]"
    assert sanitized["nested"]["password"] == "[REDACTED]"
    assert sanitized["endpoint"].endswith("key=REDACTED")
    assert sanitized["sha256"] == "abcdef1234567890"


def test_failed_sidecar_text_redacts_provider_tokens_and_private_key_blocks() -> None:
    output_safety = _load_output_safety_module()
    provider_token = "sk-" + "RTEPKT15" + ("B" * 32)
    private_key_body = "MII" + ("C" * 48)
    text = (
        f"provider_error_reason={provider_token}\n"
        "-----BEGIN PRIVATE KEY-----\n"
        f"{private_key_body}\n"
        "-----END PRIVATE KEY-----\n"
        "safe_sha256=abcdef1234567890\n"
    )

    sanitized = output_safety.sanitize_failed_sidecar_text(text)

    assert provider_token not in sanitized
    assert private_key_body not in sanitized
    assert "[REDACTED]" in sanitized
    assert "[REDACTED PRIVATE KEY]" in sanitized
    assert "safe_sha256=abcdef1234567890" in sanitized


def test_ui_events_redact_secret_like_fields(tmp_path: Path) -> None:
    runner = _load_runner_module()
    ui = runner.UI(
        runner.UiConfig(mode="plain", quiet=True, jsonl_events=True),
        run_root=tmp_path,
        run_id="run_secret_events",
    )
    trace = ui.make_trace_context(phase="D", step_id="D1", partition_id="part-001")
    ui.llm_request_event(
        phase="D",
        step_id="D1",
        status="completed",
        trace_id=trace["trace_id"],
        span_id=trace["span_id"],
        partition_id="part-001",
        provider="openrouter",
        model_id="openai/gpt-5.3-codex",
        upstream_request_id="req_123",
        extra={
            "authorization": "Bearer top-secret-token",
            "api_key": "raw-secret",
            "api_key_env": "OPENROUTER_API_KEY",
            "endpoint_effective": "https://example.test/chat?key=abc123",
        },
    )

    rows = [json.loads(line) for line in (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    event = next(row for row in rows if row.get("type") == "llm_request_completed")
    assert event["authorization"] == "[REDACTED]"
    assert event["api_key"] == "[REDACTED]"
    assert event["api_key_env"] == "OPENROUTER_API_KEY"
    assert event["endpoint_effective"].endswith("key=REDACTED")


def test_fl_int_writer_redacts_secret_fields(tmp_path: Path) -> None:
    module = load_run_module()
    target = tmp_path / "payload.json"
    module._write_json(
        target,
        {
            "api_key": "raw-secret",
            "api_key_env": "GEMINI_API_KEY",
            "nested": {"password": "secret-password"},
        },
    )
    parsed = json.loads(target.read_text(encoding="utf-8"))
    assert parsed["api_key"] == "[REDACTED]"
    assert parsed["api_key_env"] == "GEMINI_API_KEY"
    assert parsed["nested"]["password"] == "[REDACTED]"


def test_pre_live_gate_writer_redacts_secret_fields(tmp_path: Path) -> None:
    gate = _load_gate_module()
    target = tmp_path / "VALIDATION_VERDICT.json"
    gate.write_json(
        target,
        {
            "provider_error_reason": "Authorization: Bearer top-secret-token",
            "api_key_env": "XAI_API_KEY",
            "webhook_secret": "raw-webhook-secret",
        },
    )
    parsed = json.loads(target.read_text(encoding="utf-8"))
    assert parsed["provider_error_reason"] == "Authorization: [REDACTED]"
    assert parsed["api_key_env"] == "XAI_API_KEY"
    assert parsed["webhook_secret"] == "[REDACTED]"


def test_s_int_outputs_redact_secret_fields(tmp_path: Path) -> None:
    module = _load_run_s_int()
    repo_root = tmp_path / "repo"
    (repo_root / "services" / "alpha").mkdir(parents=True, exist_ok=True)
    (repo_root / "services" / "alpha" / "main.py").write_text("# webhook\n", encoding="utf-8")
    (repo_root / "docker" / "mcp-servers-source" / "demo").mkdir(parents=True, exist_ok=True)
    (repo_root / "docker" / "mcp-servers-source" / "demo" / "server.py").write_text("mcp = True\n", encoding="utf-8")
    out_root = tmp_path / "proof" / "s_int"

    def fake_executor(step, rendered_prompt, schema, prior_outputs):  # type: ignore[no-untyped-def]
        del rendered_prompt, schema, prior_outputs
        if step.step_id == "S16":
            payload = {"status": "OK", "findings": [{"server_id": "mcp.demo", "status": "OK", "notes": []}], "missing_evidence": []}
        elif step.step_id == "S17":
            payload = {"status": "OK", "hooks": [{"path": "services/alpha/main.py", "term": "webhook", "line": 1}], "missing_evidence": []}
        elif step.step_id == "S18":
            payload = {"status": "OK", "contracts": [{"contract_id": "TRINITY", "coverage": "partial"}], "missing_evidence": []}
        elif step.step_id == "S19":
            payload = {"status": "OK", "categories": [{"category": "operator", "grade": "B", "notes": []}], "missing_evidence": []}
        else:
            payload = {"status": "OK", "milestones": [{"milestone_id": step.step_id, "title": "Ship"}], "risks": [], "missing_evidence": []}
        payload["api_key"] = "raw-secret"
        payload["api_key_env"] = "OPENAI_API_KEY"
        return {"payload": payload}

    summary = module.run_s_int(repo_root, "sint_run", dry_run=False, out_root=out_root, prompt_executor=fake_executor)
    assert summary["status"] == "OK"
    written = next(path for path in sorted((out_root / "sint_run").glob("*.json")) if path.name != "S_INT_MACHINE_SUMMARY.json")
    parsed = json.loads(written.read_text(encoding="utf-8"))
    assert parsed["api_key"] == "[REDACTED]"
    assert parsed["api_key_env"] == "OPENAI_API_KEY"
