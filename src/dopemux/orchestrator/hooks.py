"""Read-only orchestrator plugin and hook registry validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

import yaml

from dopemux.orchestrator.policy import (
    REQUIRED_TIERS,
    T4_PLUS,
    WRITE_MODES,
    load_approval_policy,
)
from dopemux.orchestrator.validation.report import (
    ValidationIssue,
    ValidationReport,
    issue,
    path_text,
    sort_issues,
)


SUPPORTED_SCHEMA_VERSION = "1"
DEFAULT_HOOK_REGISTRY_PATH = Path("config/orchestrator/plugin_hooks.yaml")
HOOK_REGISTRY_AUTHORITY = "task-orchestrator-operator-integration-authority"
REQUIRED_HOOK_IDS = [
    "on_startup",
    "on_repo_scan",
    "on_context_refresh",
    "on_packet_created",
    "on_packet_started",
    "on_packet_completed",
    "on_proof_received",
    "on_audit_requested",
    "on_pr_opened",
    "on_pr_updated",
    "on_merge_candidate",
    "on_blocker_detected",
    "on_daily_plan_requested",
    "on_memory_write_requested",
    "on_authority_violation",
]
REQUIRED_ROOT_FIELDS = ["schema_version", "id", "authority", "plugins", "hooks"]
REQUIRED_PLUGIN_FIELDS = ["title", "enabled", "tier", "capabilities"]
REQUIRED_HOOK_FIELDS = [
    "id",
    "trigger",
    "tier",
    "automatic_allowed",
    "approval_required",
    "receipt_required",
    "allowed_actions",
    "forbidden_actions",
    "failure_behavior",
    "plugins",
]


@dataclass(frozen=True)
class PluginDefinition:
    plugin_id: str
    title: str
    enabled: bool
    tier: str
    capabilities: List[str]
    description: str = ""

    @classmethod
    def from_mapping(
        cls,
        plugin_id: str,
        payload: Mapping[str, Any],
    ) -> "PluginDefinition":
        return cls(
            plugin_id=plugin_id,
            title=str(payload.get("title") or plugin_id),
            enabled=bool(payload.get("enabled", False)),
            tier=str(payload.get("tier") or "TU"),
            capabilities=[str(item) for item in payload.get("capabilities", [])],
            description=str(payload.get("description") or ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "title": self.title,
            "enabled": self.enabled,
            "tier": self.tier,
            "capabilities": list(self.capabilities),
        }
        if self.description:
            data["description"] = self.description
        return data


@dataclass(frozen=True)
class HookDefinition:
    hook_id: str
    trigger: str
    tier: str
    automatic_allowed: bool
    approval_required: bool
    receipt_required: bool
    allowed_actions: List[str]
    forbidden_actions: List[str]
    failure_behavior: str
    plugins: List[str]
    description: str = ""

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "HookDefinition":
        return cls(
            hook_id=str(payload["id"]),
            trigger=str(payload["trigger"]),
            tier=str(payload["tier"]),
            automatic_allowed=bool(payload.get("automatic_allowed", False)),
            approval_required=bool(payload.get("approval_required", False)),
            receipt_required=bool(payload.get("receipt_required", False)),
            allowed_actions=[
                str(item) for item in payload.get("allowed_actions", [])
            ],
            forbidden_actions=[
                str(item) for item in payload.get("forbidden_actions", [])
            ],
            failure_behavior=str(payload["failure_behavior"]),
            plugins=[str(item) for item in payload.get("plugins", [])],
            description=str(payload.get("description") or ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "id": self.hook_id,
            "trigger": self.trigger,
            "tier": self.tier,
            "automatic_allowed": self.automatic_allowed,
            "approval_required": self.approval_required,
            "receipt_required": self.receipt_required,
            "allowed_actions": list(self.allowed_actions),
            "forbidden_actions": list(self.forbidden_actions),
            "failure_behavior": self.failure_behavior,
            "plugins": list(self.plugins),
        }
        if self.description:
            data["description"] = self.description
        return data


@dataclass(frozen=True)
class HookRegistry:
    schema_version: str
    registry_id: str
    authority: str
    updated: str
    mode: str
    plugins: Dict[str, PluginDefinition]
    hooks: List[HookDefinition]
    source_path: str

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any],
        *,
        source_path: str,
    ) -> "HookRegistry":
        plugin_payload = payload.get("plugins") or {}
        return cls(
            schema_version=str(payload.get("schema_version") or ""),
            registry_id=str(payload.get("id") or ""),
            authority=str(payload.get("authority") or ""),
            updated=str(payload.get("updated") or ""),
            mode=str(payload.get("mode") or "read_only_registry"),
            plugins={
                str(plugin_id): PluginDefinition.from_mapping(
                    str(plugin_id),
                    plugin_data,
                )
                for plugin_id, plugin_data in plugin_payload.items()
                if isinstance(plugin_data, Mapping)
            },
            hooks=[
                HookDefinition.from_mapping(hook_data)
                for hook_data in payload.get("hooks", [])
                if isinstance(hook_data, Mapping)
            ],
            source_path=source_path,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "id": self.registry_id,
            "authority": self.authority,
            "updated": self.updated,
            "mode": self.mode,
            "plugins": {
                plugin_id: plugin.to_dict()
                for plugin_id, plugin in self.plugins.items()
            },
            "hooks": [hook.to_dict() for hook in self.hooks],
        }


def default_hook_registry_path() -> Path:
    cwd_candidate = Path.cwd() / DEFAULT_HOOK_REGISTRY_PATH
    if cwd_candidate.exists():
        return DEFAULT_HOOK_REGISTRY_PATH

    repo_candidate = Path(__file__).resolve().parents[3] / DEFAULT_HOOK_REGISTRY_PATH
    if repo_candidate.exists():
        return repo_candidate
    return DEFAULT_HOOK_REGISTRY_PATH


def load_hook_registry(path: str | Path | None = None) -> HookRegistry:
    registry_path = Path(path) if path is not None else default_hook_registry_path()
    payload, errors = _load_mapping(registry_path)
    if errors:
        raise ValueError(errors[0]["message"])
    validation_errors = list(_validate_registry_payload(payload or {}))
    if validation_errors:
        raise ValueError(validation_errors[0]["message"])
    return HookRegistry.from_mapping(
        payload or {},
        source_path=path_text(registry_path),
    )


def hook_registry_list_payload(path: str | Path | None = None) -> Dict[str, Any]:
    registry = load_hook_registry(path)
    return {
        "path": registry.source_path,
        "authority": registry.authority,
        "registry_id": registry.registry_id,
        "read_only": True,
        "hook_count": len(registry.hooks),
        "plugin_count": len(registry.plugins),
        "plugins": {
            plugin_id: plugin.to_dict()
            for plugin_id, plugin in registry.plugins.items()
        },
        "hooks": [hook.to_dict() for hook in registry.hooks],
    }


def validate_hook_registry_file(
    path: str | Path | None = None,
) -> ValidationReport:
    return _build_report(path, kind="plugin_hook_registry")


def audit_hook_registry_file(
    path: str | Path | None = None,
) -> ValidationReport:
    return _build_report(path, kind="plugin_hook_doctor")


def _build_report(path: str | Path | None, *, kind: str) -> ValidationReport:
    registry_path = Path(path) if path is not None else default_hook_registry_path()
    payload, load_errors = _load_mapping(registry_path)
    errors: List[ValidationIssue] = [*load_errors]
    details: Dict[str, Any] = {
        "authority_boundary": "read_only_plugin_hook_registry_validation_only",
        "schema_version": SUPPORTED_SCHEMA_VERSION,
        "required_hooks": list(REQUIRED_HOOK_IDS),
        "read_only": True,
    }
    if payload is not None:
        errors.extend(_validate_registry_payload(payload))
        hooks = payload.get("hooks") if isinstance(payload, Mapping) else []
        plugins = payload.get("plugins") if isinstance(payload, Mapping) else {}
        hook_ids = _hook_ids(hooks)
        missing_hooks = [
            hook_id for hook_id in REQUIRED_HOOK_IDS if hook_id not in hook_ids
        ]
        extra_hooks = [
            hook_id for hook_id in hook_ids if hook_id not in REQUIRED_HOOK_IDS
        ]
        details.update(
            {
                "registry_id": payload.get("id"),
                "hook_count": len(hooks) if isinstance(hooks, list) else 0,
                "plugin_count": len(plugins) if isinstance(plugins, Mapping) else 0,
                "missing_hooks": missing_hooks,
                "extra_hooks": extra_hooks,
            }
        )

    sorted_errors = sort_issues(errors)
    status = "PASS" if not sorted_errors else "FAIL"
    return ValidationReport(
        kind=kind,
        path=path_text(registry_path),
        authority=HOOK_REGISTRY_AUTHORITY,
        status=status,
        valid=status == "PASS",
        errors=sorted_errors,
        details=details,
        exit_code=0 if status == "PASS" else 2,
    )


def _load_mapping(path: Path) -> tuple[Dict[str, Any] | None, List[ValidationIssue]]:
    if not path.exists():
        return None, [
            issue(
                "HOOK_REGISTRY_PATH_MISSING",
                f"Hook registry path is missing: {path_text(path)}",
            )
        ]

    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return None, [
            issue("HOOK_REGISTRY_YAML_INVALID", f"Hook registry YAML is invalid: {exc}")
        ]

    if not isinstance(payload, dict):
        return None, [
            issue(
                "HOOK_REGISTRY_INVALID_ROOT",
                "Hook registry root must be a mapping.",
            )
        ]
    return payload, []


def _validate_registry_payload(payload: Mapping[str, Any]) -> Iterable[ValidationIssue]:
    errors: List[ValidationIssue] = []
    _validate_root(errors, payload)
    plugin_ids = _validate_plugins(errors, payload.get("plugins"))
    _validate_hooks(errors, payload.get("hooks"), plugin_ids)
    return errors


def _validate_root(errors: List[ValidationIssue], payload: Mapping[str, Any]) -> None:
    for field_name in REQUIRED_ROOT_FIELDS:
        if field_name not in payload:
            errors.append(
                issue(
                    "HOOK_REGISTRY_ROOT_FIELD_MISSING",
                    f"Hook registry must include {field_name}.",
                    path=f"/{field_name}",
                )
            )
    if str(payload.get("schema_version") or "") != SUPPORTED_SCHEMA_VERSION:
        errors.append(
            issue(
                "HOOK_REGISTRY_SCHEMA_VERSION_UNSUPPORTED",
                f"schema_version must be {SUPPORTED_SCHEMA_VERSION}.",
                path="/schema_version",
            )
        )
    for field_name in ("id", "authority"):
        if not _non_empty_string(payload.get(field_name)):
            errors.append(
                issue(
                    "HOOK_REGISTRY_TEXT_FIELD_MISSING",
                    f"Hook registry must include non-empty {field_name}.",
                    path=f"/{field_name}",
                )
            )
    if payload.get("mode") not in (None, "read_only_registry"):
        errors.append(
            issue(
                "HOOK_REGISTRY_MODE_INVALID",
                "Hook registry mode must remain read_only_registry.",
                path="/mode",
            )
        )


def _validate_plugins(errors: List[ValidationIssue], plugins: Any) -> set[str]:
    if not isinstance(plugins, Mapping) or not plugins:
        errors.append(
            issue(
                "HOOK_REGISTRY_PLUGINS_MISSING",
                "Hook registry plugins must be a non-empty mapping.",
                path="/plugins",
            )
        )
        return set()

    policy = load_approval_policy()
    plugin_ids: set[str] = set()
    for plugin_id, plugin in plugins.items():
        plugin_id_text = str(plugin_id)
        plugin_path = f"/plugins/{plugin_id_text}"
        plugin_ids.add(plugin_id_text)
        if not isinstance(plugin, Mapping):
            errors.append(
                issue(
                    "HOOK_REGISTRY_PLUGIN_INVALID",
                    "Plugin entry must be a mapping.",
                    path=plugin_path,
                )
            )
            continue
        for field_name in REQUIRED_PLUGIN_FIELDS:
            if field_name not in plugin:
                errors.append(
                    issue(
                        "HOOK_REGISTRY_PLUGIN_FIELD_MISSING",
                        f"Plugin must include {field_name}.",
                        path=f"{plugin_path}/{field_name}",
                    )
                )
        _validate_tier(
            errors,
            str(plugin.get("tier") or ""),
            path=f"{plugin_path}/tier",
        )
        if not isinstance(plugin.get("enabled"), bool):
            errors.append(
                issue(
                    "HOOK_REGISTRY_PLUGIN_ENABLED_INVALID",
                    "Plugin enabled must be a boolean.",
                    path=f"{plugin_path}/enabled",
                )
            )
        capabilities = plugin.get("capabilities")
        if not _string_list(capabilities):
            errors.append(
                issue(
                    "HOOK_REGISTRY_PLUGIN_CAPABILITIES_INVALID",
                    "Plugin capabilities must be a non-empty list of strings.",
                    path=f"{plugin_path}/capabilities",
                )
            )
            continue
        for index, capability_id in enumerate(capabilities):
            _validate_registered_capability(
                errors,
                str(capability_id),
                policy=policy,
                path=f"{plugin_path}/capabilities/{index}",
                approval_required=bool(plugin.get("approval_required", False)),
                receipt_required=bool(plugin.get("receipt_required", False)),
                automatic_allowed=False,
                plugin_scope=True,
            )
    return plugin_ids


def _validate_hooks(
    errors: List[ValidationIssue],
    hooks: Any,
    plugin_ids: set[str],
) -> None:
    if not isinstance(hooks, list) or not hooks:
        errors.append(
            issue(
                "HOOK_REGISTRY_HOOKS_MISSING",
                "Hook registry hooks must be a non-empty list.",
                path="/hooks",
            )
        )
        return

    hook_ids = _hook_ids(hooks)
    for hook_id in REQUIRED_HOOK_IDS:
        if hook_id not in hook_ids:
            errors.append(
                issue(
                    "HOOK_REGISTRY_REQUIRED_HOOK_MISSING",
                    f"Required hook is missing: {hook_id}",
                    path="/hooks",
                )
            )
    if hook_ids[: len(REQUIRED_HOOK_IDS)] != REQUIRED_HOOK_IDS:
        errors.append(
            issue(
                "HOOK_REGISTRY_HOOK_ORDER_MISMATCH",
                "Authority hooks must be declared in deterministic authority order.",
                path="/hooks",
            )
        )

    seen: set[str] = set()
    policy = load_approval_policy()
    for index, hook in enumerate(hooks):
        path = f"/hooks/{index}"
        if not isinstance(hook, Mapping):
            errors.append(
                issue(
                    "HOOK_REGISTRY_HOOK_INVALID",
                    "Hook entry must be a mapping.",
                    path=path,
                )
            )
            continue
        for field_name in REQUIRED_HOOK_FIELDS:
            if field_name not in hook:
                errors.append(
                    issue(
                        "HOOK_REGISTRY_HOOK_FIELD_MISSING",
                        f"Hook must include {field_name}.",
                        path=f"{path}/{field_name}",
                    )
                )
        hook_id = str(hook.get("id") or "")
        if hook_id:
            if hook_id in seen:
                errors.append(
                    issue(
                        "HOOK_REGISTRY_DUPLICATE_HOOK",
                        f"Duplicate hook id: {hook_id}",
                        path=f"{path}/id",
                    )
                )
            seen.add(hook_id)
        for field_name in ("id", "trigger", "failure_behavior"):
            if not _non_empty_string(hook.get(field_name)):
                errors.append(
                    issue(
                        "HOOK_REGISTRY_HOOK_TEXT_FIELD_MISSING",
                        f"Hook must include non-empty {field_name}.",
                        path=f"{path}/{field_name}",
                    )
                )

        tier = str(hook.get("tier") or "")
        _validate_tier(errors, tier, path=f"{path}/tier")
        automatic_allowed = hook.get("automatic_allowed")
        approval_required = hook.get("approval_required")
        receipt_required = hook.get("receipt_required")
        for field_name in (
            "automatic_allowed",
            "approval_required",
            "receipt_required",
        ):
            if not isinstance(hook.get(field_name), bool):
                errors.append(
                    issue(
                        "HOOK_REGISTRY_HOOK_BOOL_FIELD_INVALID",
                        f"Hook {field_name} must be a boolean.",
                        path=f"{path}/{field_name}",
                    )
                )
        if automatic_allowed is True and tier not in {"T0", "T1"}:
            errors.append(
                issue(
                    "HOOK_REGISTRY_AUTOMATION_SCOPE_VIOLATION",
                    "Only T0/T1 hooks may allow automatic invocation.",
                    path=f"{path}/automatic_allowed",
                )
            )
        if tier in T4_PLUS:
            if approval_required is not True:
                errors.append(
                    issue(
                        "HOOK_REGISTRY_T4_APPROVAL_REQUIRED",
                        "T4 and higher hooks must require approval.",
                        path=f"{path}/approval_required",
                    )
                )
            if receipt_required is not True:
                errors.append(
                    issue(
                        "HOOK_REGISTRY_T4_RECEIPT_REQUIRED",
                        "T4 and higher hooks must require receipts.",
                        path=f"{path}/receipt_required",
                    )
                )

        allowed_actions = hook.get("allowed_actions")
        forbidden_actions = hook.get("forbidden_actions")
        if not _string_list(allowed_actions):
            errors.append(
                issue(
                    "HOOK_REGISTRY_ALLOWED_ACTIONS_INVALID",
                    "Hook allowed_actions must be a non-empty list of strings.",
                    path=f"{path}/allowed_actions",
                )
            )
            allowed_actions = []
        if not _string_list(forbidden_actions):
            errors.append(
                issue(
                    "HOOK_REGISTRY_FORBIDDEN_ACTIONS_INVALID",
                    "Hook forbidden_actions must be a non-empty list of strings.",
                    path=f"{path}/forbidden_actions",
                )
            )
            forbidden_actions = []
        _validate_action_conflicts(errors, path, allowed_actions, forbidden_actions)

        for action_index, action in enumerate(allowed_actions):
            _validate_registered_capability(
                errors,
                str(action),
                policy=policy,
                path=f"{path}/allowed_actions/{action_index}",
                approval_required=approval_required is True,
                receipt_required=receipt_required is True,
                automatic_allowed=automatic_allowed is True,
                plugin_scope=False,
            )

        hook_plugins = hook.get("plugins")
        if not _string_list(hook_plugins):
            errors.append(
                issue(
                    "HOOK_REGISTRY_HOOK_PLUGINS_INVALID",
                    "Hook plugins must be a non-empty list of strings.",
                    path=f"{path}/plugins",
                )
            )
        else:
            for plugin_index, plugin_id in enumerate(hook_plugins):
                if str(plugin_id) not in plugin_ids:
                    errors.append(
                        issue(
                            "HOOK_REGISTRY_UNKNOWN_PLUGIN",
                            f"Hook references unknown plugin: {plugin_id}",
                            path=f"{path}/plugins/{plugin_index}",
                        )
                    )


def _validate_tier(
    errors: List[ValidationIssue],
    tier: str,
    *,
    path: str,
) -> None:
    if tier not in REQUIRED_TIERS:
        errors.append(
            issue(
                "HOOK_REGISTRY_UNKNOWN_TIER",
                f"tier must be one of {', '.join(REQUIRED_TIERS)}.",
                path=path,
            )
        )


def _validate_action_conflicts(
    errors: List[ValidationIssue],
    path: str,
    allowed_actions: Any,
    forbidden_actions: Any,
) -> None:
    if not isinstance(allowed_actions, list) or not isinstance(forbidden_actions, list):
        return
    allowed = {_normalize_action(action) for action in allowed_actions}
    forbidden = {_normalize_action(action) for action in forbidden_actions}
    conflict = sorted(item for item in allowed & forbidden if item)
    if conflict:
        errors.append(
            issue(
                "HOOK_REGISTRY_ACTION_CONFLICT",
                f"Allowed and forbidden actions conflict: {', '.join(conflict)}.",
                path=path,
            )
        )


def _validate_registered_capability(
    errors: List[ValidationIssue],
    capability_id: str,
    *,
    policy: Any,
    path: str,
    approval_required: bool,
    receipt_required: bool,
    automatic_allowed: bool,
    plugin_scope: bool,
) -> None:
    if not capability_id.startswith("orchestrator."):
        return
    capability = policy.capabilities.get(capability_id)
    if capability is None:
        errors.append(
            issue(
                "HOOK_REGISTRY_UNKNOWN_CAPABILITY",
                f"Capability is not registered in approval policy: {capability_id}",
                path=path,
            )
        )
        return
    write_like = capability.mode in WRITE_MODES or capability.tier in T4_PLUS
    if plugin_scope and write_like:
        errors.append(
            issue(
                "HOOK_REGISTRY_PLUGIN_WRITE_CAPABILITY_FORBIDDEN",
                "Plugin registry capabilities must remain read-only or analysis.",
                path=path,
            )
        )
        return
    if write_like:
        if approval_required is not True:
            errors.append(
                issue(
                    "HOOK_REGISTRY_WRITE_CAPABILITY_REQUIRES_APPROVAL",
                    "Write/destructive hook capabilities must require approval.",
                    path=path,
                )
            )
        if receipt_required is not True:
            errors.append(
                issue(
                    "HOOK_REGISTRY_WRITE_CAPABILITY_REQUIRES_RECEIPT",
                    "Write/destructive hook capabilities must require receipts.",
                    path=path,
                )
            )
        if automatic_allowed is True:
            errors.append(
                issue(
                    "HOOK_REGISTRY_WRITE_CAPABILITY_AUTOMATION_FORBIDDEN",
                    "Write/destructive hook capabilities must not be automatic.",
                    path=path,
                )
            )


def _hook_ids(hooks: Any) -> List[str]:
    if not isinstance(hooks, list):
        return []
    ids: List[str] = []
    for hook in hooks:
        if isinstance(hook, Mapping) and hook.get("id"):
            ids.append(str(hook["id"]))
    return ids


def _normalize_action(value: Any) -> str:
    return " ".join(str(value).strip().lower().split())


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        _non_empty_string(item) for item in value
    )
