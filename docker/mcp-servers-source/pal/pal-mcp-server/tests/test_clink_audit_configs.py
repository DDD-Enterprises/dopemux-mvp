import json
from pathlib import Path

import clink.registry as clink_registry
from clink.models import CLIClientConfig
from clink.registry import ClinkRegistry


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "conf" / "cli_clients"
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


def _registry_with_empty_user_overrides(monkeypatch, tmp_path: Path) -> ClinkRegistry:
    empty_user_config_dir = tmp_path / "empty_user_cli_clients"
    empty_user_config_dir.mkdir()
    monkeypatch.delenv(clink_registry.CONFIG_ENV_VAR, raising=False)
    monkeypatch.setattr(clink_registry, "USER_CONFIG_DIR", empty_user_config_dir)
    return ClinkRegistry()


def _effective_args(client) -> list[str]:
    args = list(client.internal_args)
    args.extend(client.config_args)
    for role in client.roles.values():
        args.extend(role.role_args)
    return args


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


def test_audit_configs_load_validate_and_resolve_via_public_registry(monkeypatch, tmp_path):
    registry = _registry_with_empty_user_overrides(monkeypatch, tmp_path)

    for name, path in AUDIT_CONFIGS.items():
        raw_payload, config = _load_config(path)
        assert raw_payload["name"] == name

        resolved = registry.get_client(name)
        assert set(resolved.roles) == {"default", "codereviewer"}

        for role_name in ("default", "codereviewer"):
            raw_role = config.roles[role_name]
            resolved_role = resolved.roles[role_name]
            assert raw_role.prompt_path == CODEREVIEWER_PROMPT_REF
            assert raw_role.role_args == []
            assert resolved_role.prompt_path == CODEREVIEWER_PROMPT
            assert resolved_role.role_args == []

        _assert_no_forbidden_flags(_effective_args(resolved))


def test_audit_configs_use_safe_runner_plan_modes(monkeypatch, tmp_path):
    registry = _registry_with_empty_user_overrides(monkeypatch, tmp_path)

    _, claude = _load_config(AUDIT_CONFIGS["claude-audit"])
    claude_client = registry.get_client("claude-audit")
    assert claude.runner == "claude"
    _assert_plan_pair(claude_client.config_args, "--permission-mode")

    _, gemini = _load_config(AUDIT_CONFIGS["gemini-audit"])
    gemini_client = registry.get_client("gemini-audit")
    assert gemini.runner == "gemini"
    _assert_plan_pair(gemini_client.config_args, "--approval-mode")


def test_copilot_audit_config_is_deferred():
    assert not (CONFIG_DIR / "copilot-audit.json").exists()
