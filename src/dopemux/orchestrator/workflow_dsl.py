"""Read-only workflow DSL parsing and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

import yaml

from dopemux.orchestrator.policy import (
    REQUIRED_TIERS,
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


WORKFLOW_DSL_AUTHORITY = "workflow-dsl-governance"
SUPPORTED_SCHEMA_VERSION = "1"
REQUIRED_ROOT_FIELDS = [
    "schema_version",
    "id",
    "title",
    "owner",
    "authority",
    "automation_tier",
    "triggers",
    "inputs",
    "steps",
    "outputs",
    "approval",
]
REQUIRED_STEP_FIELDS = ["id", "tool", "mode", "validation", "on_failure"]
VALID_STEP_MODES = {"read", "analysis", "draft", "write", "destructive"}
WRITE_TIERS = {"T4", "T5", "T6"}
REFUSAL_TIERS = {"TX", "TU"}
FORBIDDEN_TRUE_FIELDS = {
    "auto_approve": "WORKFLOW_DSL_FORBIDDEN_AUTO_APPROVE",
    "bridge_as_authority": "WORKFLOW_DSL_FORBIDDEN_BRIDGE_AUTHORITY",
    "destructive": "WORKFLOW_DSL_FORBIDDEN_DESTRUCTIVE",
    "god_mode": "WORKFLOW_DSL_FORBIDDEN_GOD_MODE",
    "silent_write": "WORKFLOW_DSL_FORBIDDEN_SILENT_WRITE",
}


@dataclass(frozen=True)
class WorkflowDslStep:
    step_id: str
    tool: str
    mode: str
    validation: List[str]
    on_failure: str
    canonical_writer: str = ""
    upstream_canonical_writer: str = ""
    bridge_mediated: bool = False
    schema_path: str = ""
    approval_required: bool = False
    receipt_required: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "WorkflowDslStep":
        return cls(
            step_id=str(payload["id"]),
            tool=str(payload["tool"]),
            mode=str(payload["mode"]),
            validation=[str(item) for item in payload.get("validation", [])],
            on_failure=str(payload["on_failure"]),
            canonical_writer=str(payload.get("canonical_writer") or ""),
            upstream_canonical_writer=str(
                payload.get("upstream_canonical_writer") or ""
            ),
            bridge_mediated=bool(payload.get("bridge_mediated", False)),
            schema_path=str(payload.get("schema_path") or ""),
            approval_required=bool(payload.get("approval_required", False)),
            receipt_required=bool(payload.get("receipt_required", False)),
            metadata=dict(payload.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "id": self.step_id,
            "tool": self.tool,
            "mode": self.mode,
            "validation": list(self.validation),
            "on_failure": self.on_failure,
        }
        for key, value in (
            ("canonical_writer", self.canonical_writer),
            ("upstream_canonical_writer", self.upstream_canonical_writer),
            ("schema_path", self.schema_path),
        ):
            if value:
                data[key] = value
        if self.bridge_mediated:
            data["bridge_mediated"] = True
        if self.approval_required:
            data["approval_required"] = True
        if self.receipt_required:
            data["receipt_required"] = True
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        return data


@dataclass(frozen=True)
class WorkflowDsl:
    schema_version: str
    workflow_id: str
    title: str
    owner: str
    authority_primary_owner: str
    automation_tier: str
    triggers: List[str]
    inputs: List[str]
    steps: List[WorkflowDslStep]
    outputs: List[str]
    approval_required: bool
    decision: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "WorkflowDsl":
        authority = payload.get("authority") or {}
        approval = payload.get("approval") or {}
        return cls(
            schema_version=str(payload["schema_version"]),
            workflow_id=str(payload["id"]),
            title=str(payload["title"]),
            owner=str(payload["owner"]),
            authority_primary_owner=str(authority["primary_owner"]),
            automation_tier=str(payload["automation_tier"]),
            triggers=[str(item) for item in payload.get("triggers", [])],
            inputs=[str(item) for item in payload.get("inputs", [])],
            steps=[
                WorkflowDslStep.from_mapping(item)
                for item in payload.get("steps", [])
            ],
            outputs=[str(item) for item in payload.get("outputs", [])],
            approval_required=bool(approval.get("required", False)),
            decision=str(payload.get("decision") or ""),
            metadata=dict(payload.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "id": self.workflow_id,
            "title": self.title,
            "owner": self.owner,
            "authority": {"primary_owner": self.authority_primary_owner},
            "automation_tier": self.automation_tier,
            "triggers": list(self.triggers),
            "inputs": list(self.inputs),
            "steps": [step.to_dict() for step in self.steps],
            "outputs": list(self.outputs),
            "approval": {"required": self.approval_required},
        }
        if self.decision:
            data["decision"] = self.decision
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        return data


def load_workflow_dsl_file(path: str | Path) -> WorkflowDsl:
    """Load a workflow DSL file after validating its local shape."""
    dsl_path = Path(path)
    payload, errors = _load_mapping(dsl_path)
    if errors:
        raise ValueError(errors[0]["message"])
    validation_errors = list(_validate_payload(payload or {}))
    if validation_errors:
        raise ValueError(validation_errors[0]["message"])
    return WorkflowDsl.from_mapping(payload or {})


def validate_workflow_dsl_file(path: str | Path) -> ValidationReport:
    dsl_path = Path(path)
    payload, load_errors = _load_mapping(dsl_path)
    errors: List[ValidationIssue] = [*load_errors]
    details: Dict[str, Any] = {
        "authority_boundary": "read_only_workflow_dsl_validation_only",
        "schema_version": SUPPORTED_SCHEMA_VERSION,
        "required_root_fields": REQUIRED_ROOT_FIELDS,
    }

    if payload is not None:
        errors.extend(_validate_payload(payload))
        steps = payload.get("steps") if isinstance(payload, Mapping) else []
        details.update(
            {
                "workflow_id": payload.get("id"),
                "automation_tier": payload.get("automation_tier"),
                "step_count": len(steps) if isinstance(steps, list) else 0,
            }
        )

    sorted_errors = sort_issues(errors)
    status = "PASS" if not sorted_errors else "FAIL"
    return ValidationReport(
        kind="workflow_dsl",
        path=path_text(dsl_path),
        authority=WORKFLOW_DSL_AUTHORITY,
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
                "WORKFLOW_DSL_PATH_MISSING",
                f"Workflow DSL path is missing: {path_text(path)}",
            )
        ]

    try:
        raw_text = path.read_text(encoding="utf-8")
        payload = (
            json.loads(raw_text)
            if path.suffix.lower() == ".json"
            else yaml.safe_load(raw_text)
        )
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        return None, [
            issue("WORKFLOW_DSL_PARSE_ERROR", f"Workflow DSL parse failed: {exc}")
        ]

    if not isinstance(payload, dict):
        return None, [
            issue(
                "WORKFLOW_DSL_INVALID_ROOT",
                "Workflow DSL root must be a mapping.",
            )
        ]
    return payload, []


def _validate_payload(payload: Mapping[str, Any]) -> Iterable[ValidationIssue]:
    errors: List[ValidationIssue] = []
    _validate_required_root_fields(errors, payload)
    _validate_forbidden_semantics(errors, payload)
    _validate_tier_and_approval(errors, payload)
    _validate_authority(errors, payload)
    _validate_io_lists(errors, payload)
    _validate_steps(errors, payload.get("steps"))
    return errors


def _validate_required_root_fields(
    errors: List[ValidationIssue],
    payload: Mapping[str, Any],
) -> None:
    for field_name in REQUIRED_ROOT_FIELDS:
        if field_name not in payload:
            errors.append(
                issue(
                    "WORKFLOW_DSL_ROOT_FIELD_MISSING",
                    f"Workflow DSL must include {field_name}.",
                    path=f"/{field_name}",
                )
            )

    if str(payload.get("schema_version") or "") != SUPPORTED_SCHEMA_VERSION:
        errors.append(
            issue(
                "WORKFLOW_DSL_SCHEMA_VERSION_UNSUPPORTED",
                f"schema_version must be {SUPPORTED_SCHEMA_VERSION}.",
                path="/schema_version",
            )
        )
    for field_name in ("id", "title", "owner"):
        if not _non_empty_string(payload.get(field_name)):
            errors.append(
                issue(
                    "WORKFLOW_DSL_TEXT_FIELD_MISSING",
                    f"Workflow DSL must include non-empty {field_name}.",
                    path=f"/{field_name}",
                )
            )


def _validate_forbidden_semantics(
    errors: List[ValidationIssue],
    payload: Mapping[str, Any],
) -> None:
    for field_name, code in FORBIDDEN_TRUE_FIELDS.items():
        if payload.get(field_name) is True:
            errors.append(
                issue(
                    code,
                    f"{field_name}: true is forbidden in workflow DSL.",
                    path=f"/{field_name}",
                )
            )
    if payload.get("canonical_writer") == "task-orchestrator":
        errors.append(
            issue(
                "WORKFLOW_DSL_ROOT_CANONICAL_WRITER_FORBIDDEN",
                "Root canonical_writer must not make task-orchestrator general authority.",
                path="/canonical_writer",
            )
        )


def _validate_tier_and_approval(
    errors: List[ValidationIssue],
    payload: Mapping[str, Any],
) -> None:
    tier = str(payload.get("automation_tier") or "")
    approval = payload.get("approval")
    approval_required = (
        isinstance(approval, Mapping) and approval.get("required") is True
    )

    if tier not in REQUIRED_TIERS:
        errors.append(
            issue(
                "WORKFLOW_DSL_UNKNOWN_TIER",
                f"automation_tier must be one of {', '.join(REQUIRED_TIERS)}.",
                path="/automation_tier",
            )
        )
    if tier in WRITE_TIERS and not approval_required:
        errors.append(
            issue(
                "WORKFLOW_DSL_T4_APPROVAL_REQUIRED",
                "T4 and higher workflows must require approval.",
                path="/approval/required",
            )
        )
    if tier in REFUSAL_TIERS and payload.get("decision") != "refuse":
        errors.append(
            issue(
                "WORKFLOW_DSL_UNRESOLVED_REFUSE_REQUIRED",
                "TX/TU workflows must refuse by default.",
                path="/decision",
            )
        )
    if not isinstance(approval, Mapping) or not isinstance(
        approval.get("required"), bool
    ):
        errors.append(
            issue(
                "WORKFLOW_DSL_APPROVAL_REQUIRED_INVALID",
                "approval.required must be a boolean.",
                path="/approval/required",
            )
        )


def _validate_authority(
    errors: List[ValidationIssue],
    payload: Mapping[str, Any],
) -> None:
    authority = payload.get("authority")
    if not isinstance(authority, Mapping):
        errors.append(
            issue(
                "WORKFLOW_DSL_AUTHORITY_INVALID",
                "authority must be a mapping.",
                path="/authority",
            )
        )
        return
    if not _non_empty_string(authority.get("primary_owner")):
        errors.append(
            issue(
                "WORKFLOW_DSL_AUTHORITY_OWNER_MISSING",
                "authority.primary_owner must be non-empty.",
                path="/authority/primary_owner",
            )
        )


def _validate_io_lists(
    errors: List[ValidationIssue],
    payload: Mapping[str, Any],
) -> None:
    for field_name in ("triggers", "inputs", "outputs"):
        value = payload.get(field_name)
        if not _string_list(value):
            errors.append(
                issue(
                    "WORKFLOW_DSL_LIST_FIELD_INVALID",
                    f"{field_name} must be a non-empty list of strings.",
                    path=f"/{field_name}",
                )
            )
    outputs = payload.get("outputs")
    if isinstance(outputs, list) and "items" in outputs:
        missing = {"more_count", "next_token"} - set(outputs)
        if missing:
            errors.append(
                issue(
                    "WORKFLOW_DSL_PAGING_OUTPUTS_INCOMPLETE",
                    "Paged outputs with items must include more_count and next_token.",
                    path="/outputs",
                )
            )


def _validate_steps(errors: List[ValidationIssue], steps: Any) -> None:
    if not isinstance(steps, list) or not steps:
        errors.append(
            issue(
                "WORKFLOW_DSL_STEPS_MISSING",
                "Workflow DSL must include a non-empty steps list.",
                path="/steps",
            )
        )
        return

    policy = load_approval_policy()
    seen: set[str] = set()
    for index, step in enumerate(steps):
        path = f"/steps/{index}"
        if not isinstance(step, Mapping):
            errors.append(
                issue(
                    "WORKFLOW_DSL_STEP_INVALID",
                    "Step entry must be a mapping.",
                    path=path,
                )
            )
            continue
        _validate_step_required_fields(errors, path, step)
        step_id = str(step.get("id") or "")
        if step_id:
            if step_id in seen:
                errors.append(
                    issue(
                        "WORKFLOW_DSL_DUPLICATE_STEP",
                        f"Duplicate step id: {step_id}",
                        path=f"{path}/id",
                    )
                )
            seen.add(step_id)
        _validate_step_mode(errors, path, step)
        _validate_step_tool(errors, path, step, policy)


def _validate_step_required_fields(
    errors: List[ValidationIssue],
    path: str,
    step: Mapping[str, Any],
) -> None:
    for field_name in REQUIRED_STEP_FIELDS:
        if field_name not in step:
            errors.append(
                issue(
                    "WORKFLOW_DSL_STEP_FIELD_MISSING",
                    f"Step must include {field_name}.",
                    path=f"{path}/{field_name}",
                )
            )
    for field_name in ("id", "tool", "mode", "on_failure"):
        if not _non_empty_string(step.get(field_name)):
            errors.append(
                issue(
                    "WORKFLOW_DSL_STEP_TEXT_FIELD_MISSING",
                    f"Step must include non-empty {field_name}.",
                    path=f"{path}/{field_name}",
                )
            )
    if not _string_list(step.get("validation")):
        errors.append(
            issue(
                "WORKFLOW_DSL_STEP_VALIDATION_INVALID",
                "Step validation must be a non-empty list of strings.",
                path=f"{path}/validation",
            )
        )


def _validate_step_mode(
    errors: List[ValidationIssue],
    path: str,
    step: Mapping[str, Any],
) -> None:
    mode = str(step.get("mode") or "")
    if mode not in VALID_STEP_MODES:
        errors.append(
            issue(
                "WORKFLOW_DSL_STEP_MODE_INVALID",
                f"Step mode must be one of {', '.join(sorted(VALID_STEP_MODES))}.",
                path=f"{path}/mode",
            )
        )
        return

    if mode in WRITE_MODES:
        if not _non_empty_string(step.get("canonical_writer")):
            errors.append(
                issue(
                    "WORKFLOW_DSL_WRITE_CANONICAL_WRITER_REQUIRED",
                    "Any write/destructive step must name canonical_writer.",
                    path=f"{path}/canonical_writer",
                )
            )
        if step.get("bridge_mediated") is True and not _non_empty_string(
            step.get("upstream_canonical_writer")
        ):
            errors.append(
                issue(
                    "WORKFLOW_DSL_BRIDGE_UPSTREAM_WRITER_REQUIRED",
                    "Bridge-mediated writes must name upstream_canonical_writer.",
                    path=f"{path}/upstream_canonical_writer",
                )
            )


def _validate_step_tool(
    errors: List[ValidationIssue],
    path: str,
    step: Mapping[str, Any],
    policy: Any,
) -> None:
    tool = str(step.get("tool") or "")
    capability = (
        policy.capabilities.get(tool) if tool.startswith("orchestrator.") else None
    )
    if tool.startswith("orchestrator.") and capability is None:
        errors.append(
            issue(
                "WORKFLOW_DSL_UNKNOWN_CAPABILITY",
                f"Step tool is not registered in approval policy: {tool}",
                path=f"{path}/tool",
            )
        )
    if capability and capability.mode in WRITE_MODES:
        if step.get("approval_required") is not True:
            errors.append(
                issue(
                    "WORKFLOW_DSL_WRITE_APPROVAL_REQUIRED",
                    "Write/destructive policy capabilities must require approval.",
                    path=f"{path}/approval_required",
                )
            )
        if step.get("receipt_required") is not True:
            errors.append(
                issue(
                    "WORKFLOW_DSL_WRITE_RECEIPT_REQUIRED",
                    "Write/destructive policy capabilities must require receipts.",
                    path=f"{path}/receipt_required",
                )
            )
    if _requires_schema_path(tool) and not _non_empty_string(step.get("schema_path")):
        errors.append(
            issue(
                "WORKFLOW_DSL_SCHEMA_PATH_REQUIRED",
                "Proof and packet workflow steps must reference a schema_path.",
                path=f"{path}/schema_path",
            )
        )


def _requires_schema_path(tool: str) -> bool:
    return (
        ".proof." in tool
        or ".packet." in tool
        or "proof" in tool
        or "packet" in tool
    )


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        _non_empty_string(item) for item in value
    )
