from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft7Validator

from tools.auditor_router import fixtures
from tools.auditor_router.pal_clink import (
    classify_pal_clink_route,
    detect_mutation_flags,
    discover_clink_config_paths,
    effective_args_for_config,
    inspect_clink_client_config,
    load_clink_client_config,
    normalize_pal_clink_audit_output,
)
from tools.auditor_router.policy import select_preferred_route


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "auditor_router"
CANONICAL_CLINK_PROMPT = "systemprompts/clink/default_codereviewer.txt"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_schema_valid(payload: dict, schema_path: Path) -> None:
    schema = load_json(schema_path)
    Draft7Validator.check_schema(schema)
    errors = sorted(
        Draft7Validator(schema).iter_errors(payload),
        key=lambda error: list(error.path),
    )
    assert errors == [], [error.message for error in errors]


def fixture_config_dir(name: str) -> Path:
    return FIXTURES / name / "clink_configs"


def safe_claude_config() -> dict:
    return load_json(
        fixture_config_dir("pal_clink_audit_safe_claude_available") / "claude-audit.json"
    )


def test_discover_repo_local_audit_configs() -> None:
    paths = discover_clink_config_paths(repo_root=ROOT)
    names = [path.name for path in paths]

    assert "claude-audit.json" in names
    assert "gemini-audit.json" in names
    assert "claude.json" not in names
    assert "gemini.json" not in names
    assert "codex.json" not in names


def test_reject_default_mutation_configs() -> None:
    route = classify_pal_clink_route(
        config_roots=[fixture_config_dir("pal_clink_only_mutating_configs")]
    )

    assert route["tool"] == "pal-mcp-clink"
    assert route["status"] == "TOOLING_UNSAFE"
    assert route["audit_safe_config_proven"] is False
    assert "--dangerously-skip-permissions" in route["clink_mutation_flags_detected"]


def test_reject_copilot_audit_until_runner_supported(tmp_path: Path) -> None:
    config_dir = tmp_path / "clink_configs"
    config_dir.mkdir()
    (config_dir / "copilot-audit.json").write_text(
        json.dumps(
            {
                "name": "copilot-audit",
                "runner": "copilot",
                "roles": {
                    "default": {
                        "prompt_path": "systemprompts/clink/default_codereviewer.txt",
                        "role_args": [],
                    },
                    "codereviewer": {
                        "prompt_path": "systemprompts/clink/default_codereviewer.txt",
                        "role_args": [],
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    assert discover_clink_config_paths(config_roots=[config_dir]) == []
    route = classify_pal_clink_route(config_roots=[config_dir])
    assert route["status"] == "TOOLING_UNSAFE"
    assert "Copilot" in route["reason"]


def test_accept_claude_audit_config() -> None:
    path = fixture_config_dir("pal_clink_audit_safe_claude_available") / "claude-audit.json"
    inspection = inspect_clink_client_config(path)

    assert inspection.status == "AVAILABLE"
    assert inspection.client_name == "claude-audit"
    assert inspection.underlying_cli == "claude"
    assert inspection.audit_safe_config_proven is True
    assert inspection.mutation_flags == []


def test_accept_gemini_audit_config() -> None:
    path = fixture_config_dir("pal_clink_audit_safe_gemini_available") / "gemini-audit.json"
    inspection = inspect_clink_client_config(path)

    assert inspection.status == "AVAILABLE"
    assert inspection.client_name == "gemini-audit"
    assert inspection.underlying_cli == "gemini"
    assert inspection.audit_safe_config_proven is True
    assert inspection.mutation_flags == []


def test_reject_mutation_flag_in_config_args(tmp_path: Path) -> None:
    config_dir = tmp_path / "clink_configs"
    config_dir.mkdir()
    config = safe_claude_config()
    config["additional_args"] = ["--permission-mode", "bypassPermissions"]
    path = config_dir / "claude-audit.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    inspection = inspect_clink_client_config(path)

    assert inspection.status == "TOOLING_UNSAFE"
    assert "--permission-mode bypassPermissions" in inspection.mutation_flags


def test_reject_permission_mode_equals_mutation_flag(tmp_path: Path) -> None:
    config = safe_claude_config()
    config["additional_args"] = ["--permission-mode=bypassPermissions"]
    path = tmp_path / "claude-audit.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    inspection = inspect_clink_client_config(path)

    assert inspection.status == "TOOLING_UNSAFE"
    assert "--permission-mode=bypassPermissions" in inspection.mutation_flags


def test_reject_approval_mode_equals_yolo_mutation_flag(tmp_path: Path) -> None:
    config = safe_claude_config()
    config["additional_args"] = ["--approval-mode=yolo"]
    path = tmp_path / "claude-audit.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    inspection = inspect_clink_client_config(path)

    assert inspection.status == "TOOLING_UNSAFE"
    assert "--approval-mode=yolo" in inspection.mutation_flags


def test_reject_mode_equals_autopilot_mutation_flag(tmp_path: Path) -> None:
    config = safe_claude_config()
    config["additional_args"] = ["--mode=autopilot"]
    path = tmp_path / "claude-audit.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    inspection = inspect_clink_client_config(path)

    assert inspection.status == "TOOLING_UNSAFE"
    assert "--mode=autopilot" in inspection.mutation_flags


def test_reject_allow_all_equals_true_mutation_flag(tmp_path: Path) -> None:
    config = safe_claude_config()
    config["additional_args"] = ["--allow-all=true"]
    path = tmp_path / "claude-audit.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    inspection = inspect_clink_client_config(path)

    assert inspection.status == "TOOLING_UNSAFE"
    assert "--allow-all=true" in inspection.mutation_flags


def test_reject_mutation_flag_in_role_args() -> None:
    path = (
        fixture_config_dir("pal_clink_mutation_flag_in_role_args")
        / "claude-audit.json"
    )
    inspection = inspect_clink_client_config(path)

    assert inspection.status == "TOOLING_UNSAFE"
    assert "--allow-all-tools" in inspection.mutation_flags


def test_scan_effective_args_includes_internal_args() -> None:
    config = load_clink_client_config(
        fixture_config_dir("pal_clink_audit_safe_gemini_available")
        / "gemini-audit.json"
    )

    args = effective_args_for_config(
        config, internal_args=["--mode", "autopilot", "--approval-mode", "plan"]
    )

    assert "--mode" in args
    assert "autopilot" in args
    assert "--mode autopilot" in detect_mutation_flags(args)


def test_roles_must_be_default_and_codereviewer(tmp_path: Path) -> None:
    config = safe_claude_config()
    config["roles"]["planner"] = {
        "prompt_path": "systemprompts/clink/default_planner.txt",
        "role_args": [],
    }
    path = tmp_path / "claude-audit.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    inspection = inspect_clink_client_config(path)

    assert inspection.status == "TOOLING_UNSAFE"
    assert "roles must be exactly default,codereviewer" in inspection.reason


def test_roles_must_share_codereviewer_prompt(tmp_path: Path) -> None:
    config = safe_claude_config()
    config["roles"]["default"]["prompt_path"] = "systemprompts/clink/default.txt"
    path = tmp_path / "claude-audit.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    inspection = inspect_clink_client_config(path)

    assert inspection.status == "TOOLING_UNSAFE"
    assert "default_codereviewer.txt" in inspection.reason


def test_roles_reject_same_basename_outside_trusted_prompt_root(
    tmp_path: Path,
) -> None:
    config = safe_claude_config()
    config["roles"]["default"]["prompt_path"] = "../../evil/default_codereviewer.txt"
    path = tmp_path / "claude-audit.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    inspection = inspect_clink_client_config(path)

    assert inspection.status == "TOOLING_UNSAFE"
    assert CANONICAL_CLINK_PROMPT in inspection.reason


def test_roles_accept_canonical_codereviewer_prompt_path(tmp_path: Path) -> None:
    config = safe_claude_config()
    config["roles"]["default"]["prompt_path"] = CANONICAL_CLINK_PROMPT
    config["roles"]["codereviewer"]["prompt_path"] = CANONICAL_CLINK_PROMPT
    path = tmp_path / "claude-audit.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    inspection = inspect_clink_client_config(path)

    assert inspection.status == "AVAILABLE"
    assert inspection.audit_safe_config_proven is True


def test_classify_no_configs_as_tooling_unsafe() -> None:
    route = classify_pal_clink_route(
        config_roots=[fixture_config_dir("pal_clink_no_configs_found")]
    )

    assert route["status"] == "TOOLING_UNSAFE"
    assert route["installed"] is False
    assert route["requires_operator_approval"] is True


def test_classify_safe_claude_route_available() -> None:
    route = classify_pal_clink_route(
        config_roots=[fixture_config_dir("pal_clink_audit_safe_claude_available")]
    )

    assert route["tool"] == "pal-mcp-clink"
    assert route["status"] == "AVAILABLE"
    assert route["underlying_cli"] == "claude"
    assert route["clink_client_name"] == "claude-audit"
    assert route["clink_role"] == "codereviewer"
    assert route["repo_context_sent"] is False
    assert route["tools_disabled"] is True
    assert route["requires_operator_approval"] is True
    assert "pal-clink" in route["invocation_template"]


def test_select_tier1_when_direct_available() -> None:
    probes = fixtures.load_fixture_probes(
        FIXTURES / "pal_clink_not_chosen_when_direct_available"
    )
    pal_route = classify_pal_clink_route(
        config_roots=[
            FIXTURES / "pal_clink_not_chosen_when_direct_available" / "clink_configs"
        ]
    )

    selected = select_preferred_route(
        direct_routes=probes["direct_routes"],
        pal_routes=[pal_route],
        fallback_routes=probes.get("fallback_routes", []),
        allow_fallback=False,
    )

    assert selected["tool"] == "claude-code-cli"
    assert selected["status"] == "AVAILABLE"


def test_select_clink_when_direct_auth_required() -> None:
    probes = fixtures.load_fixture_probes(
        FIXTURES / "pal_clink_chosen_when_direct_auth_required"
    )
    pal_route = classify_pal_clink_route(
        config_roots=[
            FIXTURES / "pal_clink_chosen_when_direct_auth_required" / "clink_configs"
        ]
    )

    selected = select_preferred_route(
        direct_routes=probes["direct_routes"],
        pal_routes=[pal_route],
        fallback_routes=probes.get("fallback_routes", []),
        allow_fallback=False,
    )

    assert selected["tool"] == "pal-mcp-clink"
    assert selected["status"] == "AVAILABLE"


def test_select_clink_when_all_tier1_not_installed() -> None:
    probes = fixtures.load_fixture_probes(
        FIXTURES / "pal_clink_selected_when_all_tier1_not_installed"
    )
    pal_route = classify_pal_clink_route(
        config_roots=[
            FIXTURES
            / "pal_clink_selected_when_all_tier1_not_installed"
            / "clink_configs"
        ]
    )

    selected = select_preferred_route(
        direct_routes=probes["direct_routes"],
        pal_routes=[pal_route],
        fallback_routes=probes.get("fallback_routes", []),
        allow_fallback=False,
    )

    assert selected["tool"] == "pal-mcp-clink"


def test_select_copilot_fallback_only_when_allow_fallback_and_no_clink() -> None:
    probes = fixtures.load_fixture_probes(
        FIXTURES / "pal_clink_no_configs_found"
    )
    pal_route = classify_pal_clink_route(
        config_roots=[FIXTURES / "pal_clink_no_configs_found" / "clink_configs"]
    )

    blocked = select_preferred_route(
        direct_routes=probes["direct_routes"],
        pal_routes=[pal_route],
        fallback_routes=probes.get("fallback_routes", []),
        allow_fallback=False,
    )
    selected = select_preferred_route(
        direct_routes=probes["direct_routes"],
        pal_routes=[pal_route],
        fallback_routes=probes.get("fallback_routes", []),
        allow_fallback=True,
    )

    assert blocked["status"] == "NEEDS_SUPERVISOR"
    assert selected["tool"] == "copilot-cli"
    assert selected["status"] == "FALLBACK_ONLY"


def test_route_schema_valid_with_pal_clink() -> None:
    route = classify_pal_clink_route(
        config_roots=[fixture_config_dir("pal_clink_audit_safe_gemini_available")]
    )

    assert_schema_valid(route, ROOT / "schemas" / "proof" / "auditor_route.schema.json")


def test_normalize_pal_clink_pass() -> None:
    route = classify_pal_clink_route(
        config_roots=[fixture_config_dir("pal_clink_audit_safe_claude_available")]
    )

    audit = normalize_pal_clink_audit_output(
        {"status": "success", "verdict": "PASS", "findings": [], "risks": []},
        route=route,
        report_path="proof/TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002/AUDITOR_REPORT.md",
    )

    assert audit["status"] == "PASS"
    assert audit["auditor_tool"] == "pal-mcp-clink"
    assert audit["auditor_model"] == "sonnet"


def test_normalize_pal_clink_pass_with_risks() -> None:
    route = classify_pal_clink_route(
        config_roots=[fixture_config_dir("pal_clink_audit_safe_gemini_available")]
    )

    audit = normalize_pal_clink_audit_output(
        {
            "status": "success",
            "verdict": "PASS_WITH_RISKS",
            "findings": [],
            "risks": ["Host-side auth state not inspected by router."],
        },
        route=route,
        report_path="proof/TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002/AUDITOR_REPORT.md",
    )

    assert audit["status"] == "PASS_WITH_RISKS"
    assert audit["remaining_risks"] == ["Host-side auth state not inspected by router."]
    assert audit["auditor_model"] == "gemini"


def test_normalize_pal_clink_fail() -> None:
    route = classify_pal_clink_route(
        config_roots=[fixture_config_dir("pal_clink_audit_safe_claude_available")]
    )

    audit = normalize_pal_clink_audit_output(
        {
            "status": "success",
            "verdict": "PASS",
            "findings": [
                {
                    "id": "F-1",
                    "severity": "BLOCKING",
                    "title": "Unsafe config selected",
                    "body": "A mutation-capable config was selected.",
                }
            ],
            "risks": [],
        },
        route=route,
        report_path="proof/TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002/AUDITOR_REPORT.md",
    )

    assert audit["status"] == "FAIL"
    assert audit["findings"][0]["status"] == "OPEN"


def test_normalize_pal_clink_no_verdict_needs_supervisor() -> None:
    route = classify_pal_clink_route(
        config_roots=[fixture_config_dir("pal_clink_audit_safe_claude_available")]
    )

    audit = normalize_pal_clink_audit_output(
        {"status": "success", "content": "No explicit verdict here."},
        route=route,
        report_path="proof/TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002/AUDITOR_REPORT.md",
    )

    assert audit["status"] == "NEEDS_SUPERVISOR"
    assert audit["remaining_risks"] == ["PAL clink output did not include an explicit verdict."]


def test_normalize_pal_clink_truncated_needs_supervisor() -> None:
    route = classify_pal_clink_route(
        config_roots=[fixture_config_dir("pal_clink_audit_safe_gemini_available")]
    )

    audit = normalize_pal_clink_audit_output(
        {"status": "success", "verdict": "PASS", "truncated": True},
        route=route,
        report_path="proof/TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002/AUDITOR_REPORT.md",
    )

    assert audit["status"] == "NEEDS_SUPERVISOR"
    assert audit["remaining_risks"] == ["PAL clink output was truncated."]


def test_preflight_fixture_writes_route_artifacts(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.auditor_router.preflight",
            "--fixture-dir",
            str(FIXTURES / "pal_clink_chosen_when_direct_auth_required"),
            "--out",
            str(tmp_path),
            "--packet-id",
            "TP-DMX-AUDITOR-ROUTER-PAL-CLINK-002",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    route = load_json(tmp_path / "AUDITOR_ROUTE.json")
    probes = load_json(tmp_path / "ROUTE_PROBE_OUTPUTS.json")
    assert route["tool"] == "pal-mcp-clink"
    assert route["repo_context_sent"] is False
    assert probes["pal_mcp_called"] is False
    assert probes["external_cli_called_for_pal_clink"] is False
