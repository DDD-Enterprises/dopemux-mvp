"""Tests for scripts/audit/pal_clink_runner.py."""
from __future__ import annotations

import json
import subprocess
import types
from pathlib import Path

import jsonschema
import pytest

from scripts.audit.auditor_router import _CLINK_CONF_DIR, load_route_from_clink_config
from scripts.audit.pal_clink_runner import (
    MAX_AUDIT_OUTPUT_BYTES,
    PalClinkAuditOutput,
    build_invocation,
    parse_audit_json_object,
    run_audit,
    run_audit_and_capture_payload,
    run_audit_and_capture_verdict,
    _verdict_payload_from_output,
)
from scripts.audit.route_schema import AuditRoute
from tools.auditor_router.pal_clink import normalize_pal_clink_audit_output

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "audit" / "pal_clink_audit_output.schema.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------



_PASS_EVIDENCE = {
    "rationale": "Runner capture path inspected; no blocking findings in fixture payload.",
    "inspected_paths": ["scripts/audit/pal_clink_runner.py"],
    "evidence_refs": ["fixture:pal-clink-runner"],
    "validation_status": "NOT_RUN",
}

def _make_subprocess_run(
    returncode: int = 0,
    stdout: bytes = b"",
    stderr: bytes = b"",
):
    def fake(argv, *, input, capture_output, timeout, env):
        return subprocess.CompletedProcess(argv, returncode, stdout, stderr)

    return fake


def _timeout_subprocess_run(argv, *, input, capture_output, timeout, env):
    raise subprocess.TimeoutExpired(argv, timeout)


def _always_found(cmd: str) -> str:
    return f"/usr/bin/{cmd}"


def _never_found(cmd: str) -> None:
    return None


def _make_route(
    cli_name: str = "claude-audit",
    command: str = "claude",
    additional_args: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> AuditRoute:
    return AuditRoute(
        cli_name=cli_name,
        command=command,
        priority=0,
        additional_args=additional_args or [],
        env=env or {},
    )


def _output_as_dict(out: PalClinkAuditOutput) -> dict:
    return {
        "cli_name": out.cli_name,
        "exit_code": out.exit_code,
        "stdout": out.stdout,
        "stderr": out.stderr,
        "timed_out": out.timed_out,
        "error": out.error,
        "duration_seconds": out.duration_seconds,
    }


# ---------------------------------------------------------------------------
# build_invocation
# ---------------------------------------------------------------------------


class TestBuildInvocation:
    def test_command_only_when_no_additional_args(self) -> None:
        route = _make_route(command="claude", additional_args=[])
        assert build_invocation(route) == ["claude"]

    def test_includes_additional_args(self) -> None:
        route = _make_route(
            command="claude",
            additional_args=["--permission-mode", "plan", "--model", "sonnet"],
        )
        assert build_invocation(route) == [
            "claude",
            "--permission-mode",
            "plan",
            "--model",
            "sonnet",
        ]

    def test_additional_args_order_preserved(self) -> None:
        route = _make_route(command="gemini", additional_args=["--a", "--b", "--c"])
        assert build_invocation(route) == ["gemini", "--a", "--b", "--c"]

    def test_claude_audit_real_config(self) -> None:
        route = load_route_from_clink_config(_CLINK_CONF_DIR / "claude-audit.json", priority=0)
        argv = build_invocation(route)
        assert argv[0] == "claude"
        assert "--model" in argv

    def test_claude_audit_real_config_is_noninteractive_and_tool_free(self) -> None:
        route = load_route_from_clink_config(_CLINK_CONF_DIR / "claude-audit.json", priority=0)
        argv = build_invocation(route)

        assert "--print" in argv
        assert argv[argv.index("--tools") + 1] == ""
        assert "--strict-mcp-config" in argv
        assert "--safe-mode" in argv
        assert "--no-session-persistence" in argv

    def test_gemini_audit_real_config(self) -> None:
        route = load_route_from_clink_config(_CLINK_CONF_DIR / "gemini-audit.json", priority=1)
        argv = build_invocation(route)
        assert argv[0] == "gemini"
        assert "--telemetry" in argv


# ---------------------------------------------------------------------------
# run_audit — pre-flight guards
# ---------------------------------------------------------------------------


class TestRunAuditPreflight:
    def test_codex_cli_name_raises(self) -> None:
        fake_route = types.SimpleNamespace(
            cli_name="codex",
            command="some-cmd",
            additional_args=[],
            env={},
        )
        with pytest.raises(ValueError, match="Forbidden CLI"):
            run_audit(
                fake_route,
                "prompt",
                which_fn=_always_found,
                subprocess_run=_make_subprocess_run(),
            )

    def test_codex_audit_cli_name_raises(self) -> None:
        fake_route = types.SimpleNamespace(
            cli_name="codex-audit",
            command="some-cmd",
            additional_args=[],
            env={},
        )
        with pytest.raises(ValueError, match="Forbidden CLI"):
            run_audit(
                fake_route,
                "prompt",
                which_fn=_always_found,
                subprocess_run=_make_subprocess_run(),
            )

    def test_codex_command_raises_even_with_safe_cli_name(self) -> None:
        fake_route = types.SimpleNamespace(
            cli_name="claude-audit",
            command="codex",
            additional_args=[],
            env={},
        )
        with pytest.raises(ValueError, match="Forbidden CLI"):
            run_audit(
                fake_route,
                "prompt",
                which_fn=_always_found,
                subprocess_run=_make_subprocess_run(),
            )

    def test_command_not_found_returns_error_output(self) -> None:
        route = _make_route()
        out = run_audit(route, "prompt", which_fn=_never_found, subprocess_run=_make_subprocess_run())
        assert out.exit_code is None
        assert out.timed_out is False
        assert out.error is not None
        assert "not found" in out.error

    def test_command_not_found_duration_is_none(self) -> None:
        route = _make_route()
        out = run_audit(route, "prompt", which_fn=_never_found, subprocess_run=_make_subprocess_run())
        assert out.duration_seconds is None

    def test_command_not_found_cli_name_preserved(self) -> None:
        route = _make_route(cli_name="claude-audit")
        out = run_audit(route, "prompt", which_fn=_never_found, subprocess_run=_make_subprocess_run())
        assert out.cli_name == "claude-audit"

    def test_command_not_found_stdout_and_stderr_empty(self) -> None:
        route = _make_route()
        out = run_audit(route, "prompt", which_fn=_never_found, subprocess_run=_make_subprocess_run())
        assert out.stdout == ""
        assert out.stderr == ""


# ---------------------------------------------------------------------------
# run_audit — success / failure
# ---------------------------------------------------------------------------


class TestRunAuditExecution:
    def test_success_exit_code_zero(self) -> None:
        route = _make_route()
        out = run_audit(route, "prompt", which_fn=_always_found, subprocess_run=_make_subprocess_run(0))
        assert out.exit_code == 0
        assert out.timed_out is False
        assert out.error is None

    def test_nonzero_exit_code_preserved(self) -> None:
        route = _make_route()
        out = run_audit(route, "prompt", which_fn=_always_found, subprocess_run=_make_subprocess_run(1))
        assert out.exit_code == 1

    def test_exit_code_two_preserved(self) -> None:
        route = _make_route()
        out = run_audit(route, "prompt", which_fn=_always_found, subprocess_run=_make_subprocess_run(2))
        assert out.exit_code == 2

    def test_stdout_captured(self) -> None:
        route = _make_route()
        out = run_audit(
            route,
            "prompt",
            which_fn=_always_found,
            subprocess_run=_make_subprocess_run(stdout=b"hello output"),
        )
        assert out.stdout == "hello output"

    def test_stderr_captured(self) -> None:
        route = _make_route()
        out = run_audit(
            route,
            "prompt",
            which_fn=_always_found,
            subprocess_run=_make_subprocess_run(stderr=b"error log"),
        )
        assert out.stderr == "error log"

    def test_cli_name_preserved_claude(self) -> None:
        route = _make_route(cli_name="claude-audit", command="claude")
        out = run_audit(route, "prompt", which_fn=_always_found, subprocess_run=_make_subprocess_run())
        assert out.cli_name == "claude-audit"

    def test_cli_name_preserved_gemini(self) -> None:
        route = _make_route(cli_name="gemini-audit", command="gemini")
        out = run_audit(route, "prompt", which_fn=_always_found, subprocess_run=_make_subprocess_run())
        assert out.cli_name == "gemini-audit"

    def test_duration_is_nonnegative_on_success(self) -> None:
        route = _make_route()
        out = run_audit(route, "prompt", which_fn=_always_found, subprocess_run=_make_subprocess_run())
        assert out.duration_seconds is not None
        assert out.duration_seconds >= 0.0

    def test_invalid_utf8_stdout_replaced(self) -> None:
        route = _make_route()
        out = run_audit(
            route,
            "prompt",
            which_fn=_always_found,
            subprocess_run=_make_subprocess_run(stdout=b"\xff\xfe invalid"),
        )
        assert isinstance(out.stdout, str)


# ---------------------------------------------------------------------------
# run_audit — timeout
# ---------------------------------------------------------------------------


class TestRunAuditTimeout:
    def test_timeout_sets_timed_out_true(self) -> None:
        route = _make_route()
        out = run_audit(
            route,
            "prompt",
            which_fn=_always_found,
            subprocess_run=_timeout_subprocess_run,
            timeout_seconds=1.0,
        )
        assert out.timed_out is True

    def test_timeout_exit_code_is_none(self) -> None:
        route = _make_route()
        out = run_audit(
            route,
            "prompt",
            which_fn=_always_found,
            subprocess_run=_timeout_subprocess_run,
            timeout_seconds=1.0,
        )
        assert out.exit_code is None

    def test_timeout_error_message_present(self) -> None:
        route = _make_route()
        out = run_audit(
            route,
            "prompt",
            which_fn=_always_found,
            subprocess_run=_timeout_subprocess_run,
            timeout_seconds=1.0,
        )
        assert out.error is not None
        assert "timed out" in out.error

    def test_timeout_duration_is_nonnegative(self) -> None:
        route = _make_route()
        out = run_audit(
            route,
            "prompt",
            which_fn=_always_found,
            subprocess_run=_timeout_subprocess_run,
            timeout_seconds=1.0,
        )
        assert out.duration_seconds is not None
        assert out.duration_seconds >= 0.0

    def test_timeout_stdout_and_stderr_empty(self) -> None:
        route = _make_route()
        out = run_audit(
            route,
            "prompt",
            which_fn=_always_found,
            subprocess_run=_timeout_subprocess_run,
            timeout_seconds=1.0,
        )
        assert out.stdout == ""
        assert out.stderr == ""


# ---------------------------------------------------------------------------
# run_audit — stdin and env
# ---------------------------------------------------------------------------


class TestRunAuditStdinAndEnv:
    def test_empty_prompt_passed_as_empty_bytes(self) -> None:
        captured: dict = {}

        def capture_run(argv, *, input, capture_output, timeout, env):
            captured["input"] = input
            return subprocess.CompletedProcess(argv, 0, b"", b"")

        route = _make_route()
        run_audit(route, "", which_fn=_always_found, subprocess_run=capture_run)
        assert captured["input"] == b""

    def test_prompt_passed_as_stdin(self) -> None:
        captured: dict = {}

        def capture_run(argv, *, input, capture_output, timeout, env):
            captured["input"] = input
            return subprocess.CompletedProcess(argv, 0, b"", b"")

        route = _make_route()
        run_audit(route, "my audit prompt", which_fn=_always_found, subprocess_run=capture_run)
        assert captured["input"] == b"my audit prompt"

    def test_env_merged_with_os_environ(self) -> None:
        captured: dict = {}

        def capture_run(argv, *, input, capture_output, timeout, env):
            captured["env"] = env
            return subprocess.CompletedProcess(argv, 0, b"", b"")

        route = _make_route(env={"MY_AUDIT_KEY": "audit_value"})
        run_audit(route, "prompt", which_fn=_always_found, subprocess_run=capture_run)
        assert "MY_AUDIT_KEY" in captured["env"]
        assert captured["env"]["MY_AUDIT_KEY"] == "audit_value"

    def test_route_env_overrides_os_environ(self) -> None:
        captured: dict = {}

        def capture_run(argv, *, input, capture_output, timeout, env):
            captured["env"] = env
            return subprocess.CompletedProcess(argv, 0, b"", b"")

        route = _make_route(env={"PATH": "overridden_path_value"})
        run_audit(route, "prompt", which_fn=_always_found, subprocess_run=capture_run)
        assert captured["env"]["PATH"] == "overridden_path_value"

    def test_argv_passed_to_subprocess(self) -> None:
        captured: dict = {}

        def capture_run(argv, *, input, capture_output, timeout, env):
            captured["argv"] = argv
            return subprocess.CompletedProcess(argv, 0, b"", b"")

        route = _make_route(command="claude", additional_args=["--permission-mode", "plan"])
        run_audit(route, "prompt", which_fn=_always_found, subprocess_run=capture_run)
        assert captured["argv"] == ["claude", "--permission-mode", "plan"]


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


class TestPalClinkAuditOutputSchema:
    def _schema(self) -> dict:
        return json.loads(SCHEMA_PATH.read_text())

    def test_successful_output_validates(self) -> None:
        route = _make_route()
        out = run_audit(route, "prompt", which_fn=_always_found, subprocess_run=_make_subprocess_run())
        jsonschema.validate(_output_as_dict(out), self._schema())

    def test_timeout_output_validates(self) -> None:
        route = _make_route()
        out = run_audit(
            route,
            "prompt",
            which_fn=_always_found,
            subprocess_run=_timeout_subprocess_run,
            timeout_seconds=1.0,
        )
        jsonschema.validate(_output_as_dict(out), self._schema())

    def test_preflight_failure_output_validates(self) -> None:
        route = _make_route()
        out = run_audit(route, "prompt", which_fn=_never_found, subprocess_run=_make_subprocess_run())
        jsonschema.validate(_output_as_dict(out), self._schema())

    def test_nonzero_exit_output_validates(self) -> None:
        route = _make_route()
        out = run_audit(route, "prompt", which_fn=_always_found, subprocess_run=_make_subprocess_run(2))
        jsonschema.validate(_output_as_dict(out), self._schema())


# ---------------------------------------------------------------------------
# run_audit_and_capture_verdict
# ---------------------------------------------------------------------------


class TestRunAuditAndCaptureVerdict:
    def test_success_writes_raw_output_report_and_embedded_audit(
        self, tmp_path: Path
    ) -> None:
        route = _make_route(cli_name="claude-audit", command="claude")
        route_record = {
            "tool": "pal-mcp-clink",
            "underlying_cli": "claude",
            "clink_client_name": "claude-audit",
            "audit_safe_config_proven": True,
            "clink_mutation_flags_detected": [],
            "invocation_template": (
                "pal-clink --client claude-audit --role codereviewer "
                "--input PAL_CLINK_AUDIT_INPUT.md "
                "--output PAL_CLINK_AUDIT_OUTPUT.json"
            ),
        }
        raw_output_path = tmp_path / "PAL_CLINK_AUDIT_OUTPUT.json"
        report_file_path = tmp_path / "AUDITOR_REPORT.md"

        embedded = run_audit_and_capture_verdict(
            route,
            "audit prompt",
            route_record=route_record,
            raw_output_path=raw_output_path,
            report_path="proof/TP-DMX-PALCLINK-VERDICT-101/AUDITOR_REPORT.md",
            report_file_path=report_file_path,
            which_fn=_always_found,
            subprocess_run=_make_subprocess_run(
                stdout=json.dumps(
                    {
                        "status": "success",
                        "verdict": "PASS",
                        "findings": [],
                        "risks": [],
                        "rationale": "Runner capture path inspected; no blocking findings in fixture payload.",
                        "inspected_paths": ["scripts/audit/pal_clink_runner.py"],
                        "evidence_refs": ["fixture:pal-clink-runner"],
                        "validation_status": "NOT_RUN",
                    }
                ).encode("utf-8")
            ),
        )

        raw_output = json.loads(raw_output_path.read_text(encoding="utf-8"))
        jsonschema.validate(raw_output, json.loads(SCHEMA_PATH.read_text()))
        assert embedded["status"] == "PASS"
        assert embedded["auditor_tool"] == "pal-mcp-clink"
        assert embedded["report_path"] == "proof/TP-DMX-PALCLINK-VERDICT-101/AUDITOR_REPORT.md"
        assert "PAL clink audit verdict: PASS" in report_file_path.read_text(
            encoding="utf-8"
        )

    def test_tool_output_content_is_parsed_before_normalization(
        self, tmp_path: Path
    ) -> None:
        route = _make_route(cli_name="claude-audit", command="claude")
        route_record = {
            "tool": "pal-mcp-clink",
            "underlying_cli": "claude",
            "clink_client_name": "claude-audit",
            "audit_safe_config_proven": True,
            "clink_mutation_flags_detected": [],
            "invocation_template": (
                "pal-clink --client claude-audit --role codereviewer "
                "--input PAL_CLINK_AUDIT_INPUT.md "
                "--output PAL_CLINK_AUDIT_OUTPUT.json"
            ),
        }
        tool_output = {
            "status": "success",
            "content": json.dumps(
                {
                    "status": "success",
                    "verdict": "PASS",
                        "findings": [],
                        "risks": [],
                        "rationale": "Runner capture path inspected; no blocking findings in fixture payload.",
                        "inspected_paths": ["scripts/audit/pal_clink_runner.py"],
                        "evidence_refs": ["fixture:pal-clink-runner"],
                        "validation_status": "NOT_RUN",
                }
            ),
            "content_type": "text",
            "metadata": {},
        }

        embedded = run_audit_and_capture_verdict(
            route,
            "audit prompt",
            route_record=route_record,
            raw_output_path=tmp_path / "PAL_CLINK_AUDIT_OUTPUT.json",
            report_path="proof/TP-DMX-PALCLINK-VERDICT-101/AUDITOR_REPORT.md",
            report_file_path=tmp_path / "AUDITOR_REPORT.md",
            which_fn=_always_found,
            subprocess_run=_make_subprocess_run(
                stdout=json.dumps(tool_output).encode("utf-8")
            ),
        )

        assert embedded["status"] == "PASS"

    def test_fixture_only_capture_blocks_even_with_pass_verdict(
        self, tmp_path: Path
    ) -> None:
        route = _make_route(cli_name="claude-audit", command="claude")
        route_record = {
            "tool": "pal-mcp-clink",
            "underlying_cli": "claude",
            "clink_client_name": "claude-audit",
            "audit_safe_config_proven": True,
            "clink_mutation_flags_detected": [],
            "invocation_template": (
                "pal-clink --client claude-audit --role codereviewer "
                "--input PAL_CLINK_AUDIT_INPUT.md "
                "--output PAL_CLINK_AUDIT_OUTPUT.json"
            ),
        }

        embedded = run_audit_and_capture_verdict(
            route,
            "audit prompt",
            route_record=route_record,
            raw_output_path=tmp_path / "PAL_CLINK_AUDIT_OUTPUT.json",
            report_path="proof/TP-DMX-PALCLINK-VERDICT-101/AUDITOR_REPORT.md",
            report_file_path=tmp_path / "AUDITOR_REPORT.md",
            which_fn=_always_found,
            subprocess_run=_make_subprocess_run(
                stdout=json.dumps(
                    {
                        "status": "success",
                        "verdict": "PASS",
                        "findings": [],
                        "risks": [
                            "Fixture run only; no live external PAL clink CLI was invoked."
                        ],
                    }
                ).encode("utf-8")
            ),
        )

        assert embedded["status"] == "NEEDS_SUPERVISOR"
        assert embedded["exit_code"] == 1


class TestRunAuditAndCapturePayload:
    def test_writes_runner_output_and_verdict_payload(self, tmp_path: Path) -> None:
        route = _make_route(cli_name="claude-audit", command="claude")
        raw_output_path = tmp_path / "PAL_CLINK_AUDIT_RUNNER_OUTPUT.json"
        pal_output_path = tmp_path / "PAL_CLINK_AUDIT_OUTPUT.json"

        payload = run_audit_and_capture_payload(
            route,
            "audit prompt",
            raw_output_path=raw_output_path,
            pal_output_path=pal_output_path,
            which_fn=_always_found,
            subprocess_run=_make_subprocess_run(
                stdout=json.dumps(
                    {
                        "status": "success",
                        "verdict": "PASS",
                        "findings": [],
                        "risks": [],
                        "rationale": "Runner capture path inspected; no blocking findings in fixture payload.",
                        "inspected_paths": ["scripts/audit/pal_clink_runner.py"],
                        "evidence_refs": ["fixture:pal-clink-runner"],
                        "validation_status": "NOT_RUN",
                    }
                ).encode("utf-8")
            ),
        )

        raw_output = json.loads(raw_output_path.read_text(encoding="utf-8"))
        captured_payload = json.loads(pal_output_path.read_text(encoding="utf-8"))
        jsonschema.validate(raw_output, json.loads(SCHEMA_PATH.read_text()))
        assert payload["verdict"] == "PASS"
        assert captured_payload["verdict"] == "PASS"


# ---------------------------------------------------------------------------
# parse_audit_json_object (fail-closed fenced JSON salvage)
# ---------------------------------------------------------------------------


_SAFE_ROUTE = {
    "tool": "pal-mcp-clink",
    "underlying_cli": "claude",
    "clink_client_name": "claude-audit",
    "audit_safe_config_proven": True,
    "clink_mutation_flags_detected": [],
    "invocation_template": (
        "pal-clink --client claude-audit --role codereviewer "
        "--input PAL_CLINK_AUDIT_INPUT.md "
        "--output PAL_CLINK_AUDIT_OUTPUT.json"
    ),
}


class TestParseAuditJsonObject:
    def test_direct_full_output_object(self) -> None:
        obj = {"verdict": "PASS", "findings": [], "risks": []}
        assert parse_audit_json_object(json.dumps(obj)) == obj
        assert parse_audit_json_object(f"  \n{json.dumps(obj)}\n  ") == obj

    def test_single_full_output_plain_fence(self) -> None:
        obj = {"verdict": "PASS_WITH_RISKS", "findings": [], "risks": ["r1"]}
        body = json.dumps(obj)
        assert parse_audit_json_object(f"```\n{body}\n```") == obj

    def test_single_full_output_json_fence(self) -> None:
        obj = {"verdict": "PASS_WITH_RISKS", "findings": [], "risks": ["r1"]}
        body = json.dumps(obj)
        assert parse_audit_json_object(f"```json\n{body}\n```") == obj
        assert parse_audit_json_object(f"  \n```json\n{body}\n```\n  ") == obj

    def test_rejects_prose_prefix_and_suffix(self) -> None:
        body = json.dumps({"verdict": "PASS"})
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object(f"Sure! Here you go:\n{body}\nHope that helps!")
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object(f"```json\n{body}\n```\nThanks!")
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object(f"Here is the result:\n```json\n{body}\n```")

    def test_rejects_brace_scraping(self) -> None:
        body = json.dumps({"verdict": "PASS"})
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object(f"prefix {body} suffix")

    def test_rejects_two_fenced_objects_explicitly(self) -> None:
        a = json.dumps({"verdict": "PASS"})
        b = json.dumps({"verdict": "FAIL"})
        text = f"```json\n{a}\n```\n```json\n{b}\n```"
        with pytest.raises(json.JSONDecodeError, match="interior fence"):
            parse_audit_json_object(text)

    def test_rejects_interior_exact_fence_line(self) -> None:
        body = json.dumps({"verdict": "PASS"})
        # Interior exact closer/opener line must fail structurally before JSON.
        with pytest.raises(json.JSONDecodeError, match="interior fence"):
            parse_audit_json_object(f"```json\n{body}\n```\n{body}\n```")
        with pytest.raises(json.JSONDecodeError, match="interior fence"):
            parse_audit_json_object(f"```\n{body}\n```json\n{body}\n```")

    def test_rejects_arrays_and_scalars(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object("[1, 2, 3]")
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object('"just a string"')
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object("42")
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object("```json\n[1, 2]\n```")

    def test_rejects_malformed_json(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object("{not json")
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object("```json\n{not json\n```")

    def test_rejects_empty_output(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object("")
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object("   \n\t  ")
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object("```json\n\n```")

    def test_rejects_malformed_fences(self) -> None:
        body = json.dumps({"verdict": "PASS"})
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object(f"```JSON\n{body}\n```")  # wrong case
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object(f"```json \n{body}\n```")  # trailing space on opener
        with pytest.raises(json.JSONDecodeError):
            # Closer line is not exact ``` (trailing spaces preserved by non-ws tail).
            parse_audit_json_object(f"```json\n{body}\n```  \n.")
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object(f"```python\n{body}\n```")
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object(f"```json\n{body}")  # missing closer
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object("```")  # incomplete

    def test_rejects_ambiguous_nested_content_outside_object(self) -> None:
        # Nested object inside prose must not be brace-scraped into a verdict.
        nested = '{"verdict":"PASS","findings":[]}'
        with pytest.raises(json.JSONDecodeError):
            parse_audit_json_object(
                f'I reviewed the change. Result follows: {nested} — approved.'
            )

    def test_accepts_exactly_at_byte_limit(self) -> None:
        prefix = '{"pad":"'
        suffix = '"}'
        pad_len = MAX_AUDIT_OUTPUT_BYTES - len(prefix.encode("utf-8")) - len(
            suffix.encode("utf-8")
        )
        assert pad_len > 0
        text = prefix + ("x" * pad_len) + suffix
        assert len(text.encode("utf-8")) == MAX_AUDIT_OUTPUT_BYTES
        assert parse_audit_json_object(text) == {"pad": "x" * pad_len}

    def test_rejects_one_byte_over_limit(self) -> None:
        prefix = '{"pad":"'
        suffix = '"}'
        pad_len = MAX_AUDIT_OUTPUT_BYTES - len(prefix.encode("utf-8")) - len(
            suffix.encode("utf-8")
        )
        text = prefix + ("x" * (pad_len + 1)) + suffix
        assert len(text.encode("utf-8")) == MAX_AUDIT_OUTPUT_BYTES + 1
        with pytest.raises(json.JSONDecodeError, match="exceeds"):
            parse_audit_json_object(text)

    def test_rejects_large_fence_like_pathological_input(self) -> None:
        # Many fence-like lines under the byte cap must still fail structure
        # (interior exact fences), never become a dict.
        chunk = "```\n"
        # Build under limit: open + many interior fence lines + close.
        interior_count = 5000
        text = "```json\n" + (chunk * interior_count) + '{"v":1}\n```'
        assert len(text.encode("utf-8")) <= MAX_AUDIT_OUTPUT_BYTES
        with pytest.raises(json.JSONDecodeError, match="interior fence"):
            parse_audit_json_object(text)

    def test_nested_tool_content_follows_same_strict_policy(self) -> None:
        good = json.dumps(
            {
                "status": "success",
                "verdict": "PASS",
                "findings": [],
                "risks": [],
                **_PASS_EVIDENCE,
            }
        )
        multi = f"```json\n{good}\n```\n```json\n{good}\n```"
        outer = json.dumps({"status": "success", "content": multi})
        # Outer envelope parses as bare object; unwrap re-parses content strictly.
        payload = _verdict_payload_from_output(
            PalClinkAuditOutput(
                cli_name="claude-audit",
                exit_code=0,
                stdout=outer,
                stderr="",
                timed_out=False,
                error=None,
                duration_seconds=0.01,
            )
        )
        # Content multi-fence rejected: outer kept without unwrapped verdict.
        assert payload.get("status") == "success"
        assert "verdict" not in payload
        embedded = normalize_pal_clink_audit_output(
            payload,
            route=_SAFE_ROUTE,
            report_path="proof/test/AUDITOR_REPORT.md",
        )
        assert embedded["status"] not in {"PASS", "PASS_WITH_RISKS", "READY"}


class TestVerdictPayloadFailClosed:
    def _ok_output(self, stdout: str) -> PalClinkAuditOutput:
        return PalClinkAuditOutput(
            cli_name="claude-audit",
            exit_code=0,
            stdout=stdout,
            stderr="",
            timed_out=False,
            error=None,
            duration_seconds=0.1,
        )

    def test_rejected_stdout_never_becomes_pass_or_ready(self) -> None:
        prose = 'Sure! {"verdict":"PASS","findings":[],"risks":[]} done.'
        payload = _verdict_payload_from_output(self._ok_output(prose))
        assert payload["status"] == "error"
        assert "verdict" not in payload
        assert any("Fail-closed JSON parse" in r for r in payload["risks"])

        embedded = normalize_pal_clink_audit_output(
            payload,
            route=_SAFE_ROUTE,
            report_path="proof/test/AUDITOR_REPORT.md",
        )
        # Rejected parse must never become a structured passing/ready verdict.
        assert embedded["status"] not in {"PASS", "PASS_WITH_RISKS", "READY"}
        assert embedded["status"] in {"NEEDS_SUPERVISOR", "FAIL", "SKIPPED"}
        assert any(
            "Fail-closed JSON parse" in r or "ToolOutput status was error" in r
            for r in embedded.get("remaining_risks") or []
        )

    def test_fenced_object_can_surface_structured_verdict(self) -> None:
        body = json.dumps(
            {
                "status": "success",
                "verdict": "PASS",
                "findings": [],
                "risks": [],
                **_PASS_EVIDENCE,
            }
        )
        payload = _verdict_payload_from_output(
            self._ok_output(f"```json\n{body}\n```")
        )
        assert payload.get("verdict") == "PASS"
        embedded = normalize_pal_clink_audit_output(
            payload,
            route=_SAFE_ROUTE,
            report_path="proof/test/AUDITOR_REPORT.md",
        )
        assert embedded["status"] == "PASS"

    def test_direct_object_unchanged(self) -> None:
        body = json.dumps(
            {
                "status": "success",
                "verdict": "PASS",
                "findings": [],
                "risks": [],
                **_PASS_EVIDENCE,
            }
        )
        payload = _verdict_payload_from_output(self._ok_output(body))
        assert payload.get("verdict") == "PASS"
