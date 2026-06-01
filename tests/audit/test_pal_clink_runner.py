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
    PalClinkAuditOutput,
    build_invocation,
    run_audit,
    run_audit_and_capture_verdict,
)
from scripts.audit.route_schema import AuditRoute

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "audit" / "pal_clink_audit_output.schema.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
