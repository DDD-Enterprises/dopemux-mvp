import json
from pathlib import Path

from clink.models import CLIClientConfig
from clink.registry import ClinkRegistry


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "conf" / "cli_clients"
PROOF_ROOT = PROJECT_ROOT.parents[3] / "proof" / "TP-DMX-PAL-CLINK-AUDIT-CONFIGS-001"
DOC_PATH = PROJECT_ROOT / "docs" / "tools" / "clink.md"
CODEREVIEWER_PROMPT = PROJECT_ROOT / "systemprompts" / "clink" / "default_codereviewer.txt"
CODEREVIEWER_PROMPT_REF = "systemprompts/clink/default_codereviewer.txt"
AUDIT_CONFIGS = {
    "claude-audit": CONFIG_DIR / "claude-audit.json",
    "gemini-audit": CONFIG_DIR / "gemini-audit.json",
}
FORBIDDEN_FLAGS = {
    "--yolo",
    "-y",
    "acceptEdits",
    "bypassPermissions",
    "dontAsk",
    "--dangerously-bypass-approvals-and-sandbox",
    "--dangerously-skip-permissions",
    "--allow-all",
    "--allow-all-tools",
    "--allow-all-paths",
    "--allow-all-urls",
    "--autopilot",
    "--add-dir",
}


def _load_config(path: Path) -> tuple[dict, CLIClientConfig]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload, CLIClientConfig.model_validate(payload)


def _resolve_config(config: CLIClientConfig, source_path: Path):
    registry = ClinkRegistry.__new__(ClinkRegistry)
    return registry._resolve_config(config, source_path=source_path)


def _assert_no_forbidden_flags(args: list[str]) -> None:
    for arg in args:
        for forbidden in FORBIDDEN_FLAGS:
            if arg == forbidden or (not forbidden.startswith("-") and forbidden in arg):
                raise AssertionError(f"Forbidden audit config flag {forbidden!r} found in {arg!r}")


def _assert_plan_pair(args: list[str], flag: str) -> None:
    assert flag in args
    flag_index = args.index(flag)
    assert len(args) > flag_index + 1
    assert args[flag_index + 1] == "plan"


def test_audit_configs_load_validate_and_resolve():
    for name, path in AUDIT_CONFIGS.items():
        raw_payload, config = _load_config(path)
        assert raw_payload["name"] == name

        resolved = _resolve_config(config, path)
        assert set(resolved.roles) == {"default", "codereviewer"}

        for role_name in ("default", "codereviewer"):
            raw_role = config.roles[role_name]
            resolved_role = resolved.roles[role_name]
            assert raw_role.prompt_path == CODEREVIEWER_PROMPT_REF
            assert raw_role.role_args == []
            assert resolved_role.prompt_path == CODEREVIEWER_PROMPT
            assert resolved_role.role_args == []

        _assert_no_forbidden_flags(config.additional_args)
        for role in config.roles.values():
            _assert_no_forbidden_flags(role.role_args)


def test_audit_configs_use_safe_runner_plan_modes():
    _, claude = _load_config(AUDIT_CONFIGS["claude-audit"])
    assert claude.runner == "claude"
    _assert_plan_pair(claude.additional_args, "--permission-mode")

    _, gemini = _load_config(AUDIT_CONFIGS["gemini-audit"])
    assert gemini.runner == "gemini"
    _assert_plan_pair(gemini.additional_args, "--approval-mode")


def test_copilot_audit_config_is_deferred():
    assert not (CONFIG_DIR / "copilot-audit.json").exists()

    proof_text = (PROOF_ROOT / "PROOF.json").read_text(encoding="utf-8")
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    expected = "DEFERRED_COPILOT_RUNNER_UNSUPPORTED"
    assert expected in proof_text
    assert expected in doc_text


def test_docs_and_proof_record_default_role_mapping():
    proof_text = (PROOF_ROOT / "PROOF.json").read_text(encoding="utf-8")
    doc_text = DOC_PATH.read_text(encoding="utf-8")

    assert "ACCEPTED_DEFAULT_ROLE_INJECTION" in proof_text
    assert "default and codereviewer" in proof_text
    assert CODEREVIEWER_PROMPT_REF in proof_text
    assert "`default` and `codereviewer`" in doc_text
    assert CODEREVIEWER_PROMPT_REF in doc_text
