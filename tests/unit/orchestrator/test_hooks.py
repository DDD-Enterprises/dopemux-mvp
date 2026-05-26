import ast
from pathlib import Path

import yaml

from dopemux.orchestrator.hooks import (
    REQUIRED_HOOK_IDS,
    audit_hook_registry_file,
    load_hook_registry,
    validate_hook_registry_file,
)


def _write_yaml(path: Path, payload: dict) -> Path:
    path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    return path


def test_default_hook_registry_declares_authority_hooks_in_order() -> None:
    registry = load_hook_registry()

    assert [hook.hook_id for hook in registry.hooks] == REQUIRED_HOOK_IDS
    assert registry.hooks[0].hook_id == "on_startup"
    assert registry.hooks[0].tier == "T0"
    assert "orchestrator.status.queue" in registry.hooks[0].allowed_actions
    assert registry.plugins["orchestrator-operator-hooks"].enabled is True


def test_default_hook_registry_validates_successfully() -> None:
    report = validate_hook_registry_file()

    assert report.valid is True
    assert report.status == "PASS"
    assert report.errors == []
    assert report.details["hook_count"] == len(REQUIRED_HOOK_IDS)
    assert report.details["plugin_count"] >= 1


def test_plugin_doctor_reports_pass_for_default_registry() -> None:
    report = audit_hook_registry_file()

    assert report.valid is True
    assert report.kind == "plugin_hook_doctor"
    assert report.status == "PASS"
    assert report.details["missing_hooks"] == []
    assert report.details["read_only"] is True


def test_hook_registry_rejects_missing_required_hook(tmp_path: Path) -> None:
    payload = load_hook_registry().to_dict()
    payload["hooks"] = payload["hooks"][:-1]
    path = _write_yaml(tmp_path / "plugin_hooks.yaml", payload)

    report = validate_hook_registry_file(path)

    assert report.valid is False
    assert any(
        error["code"] == "HOOK_REGISTRY_REQUIRED_HOOK_MISSING"
        for error in report.errors
    )


def test_hook_registry_rejects_unknown_tier(tmp_path: Path) -> None:
    payload = load_hook_registry().to_dict()
    payload["hooks"][0]["tier"] = "T9000"
    path = _write_yaml(tmp_path / "plugin_hooks.yaml", payload)

    report = validate_hook_registry_file(path)

    assert report.valid is False
    assert any(
        error["code"] == "HOOK_REGISTRY_UNKNOWN_TIER" for error in report.errors
    )


def test_hook_registry_rejects_allowed_forbidden_action_conflict(
    tmp_path: Path,
) -> None:
    payload = load_hook_registry().to_dict()
    payload["hooks"][0]["forbidden_actions"].append(
        payload["hooks"][0]["allowed_actions"][0]
    )
    path = _write_yaml(tmp_path / "plugin_hooks.yaml", payload)

    report = validate_hook_registry_file(path)

    assert report.valid is False
    assert any(
        error["code"] == "HOOK_REGISTRY_ACTION_CONFLICT"
        for error in report.errors
    )


def test_hook_registry_rejects_unknown_orchestrator_action(
    tmp_path: Path,
) -> None:
    payload = load_hook_registry().to_dict()
    payload["hooks"][0]["allowed_actions"].append("orchestrator.future.unknown")
    path = _write_yaml(tmp_path / "plugin_hooks.yaml", payload)

    report = validate_hook_registry_file(path)

    assert report.valid is False
    assert any(
        error["code"] == "HOOK_REGISTRY_UNKNOWN_CAPABILITY"
        for error in report.errors
    )


def test_hook_registry_requires_approval_for_write_capability(
    tmp_path: Path,
) -> None:
    payload = load_hook_registry().to_dict()
    payload["hooks"][0]["allowed_actions"].append("orchestrator.github.comment")
    payload["hooks"][0]["approval_required"] = False
    payload["hooks"][0]["receipt_required"] = False
    path = _write_yaml(tmp_path / "plugin_hooks.yaml", payload)

    report = validate_hook_registry_file(path)

    assert report.valid is False
    assert {
        error["code"] for error in report.errors
    } >= {
        "HOOK_REGISTRY_WRITE_CAPABILITY_REQUIRES_APPROVAL",
        "HOOK_REGISTRY_WRITE_CAPABILITY_REQUIRES_RECEIPT",
    }


def test_hook_registry_module_does_not_import_runtime_hook_managers() -> None:
    module_path = Path("src/dopemux/orchestrator/hooks.py")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    forbidden_modules = {
        "dopemux.hooks",
        "dopemux.hooks.hook_manager",
        "dopemux.mcp.hooks",
    }
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)

    assert forbidden_modules.isdisjoint(imports)
