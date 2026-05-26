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
WRITE_TIERS = {"T4", "T5", "T6"}


@dataclass(frozen=True)
class WorkflowDslState:
    state_id: str
    title: str = ""
    terminal: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "WorkflowDslState":
        return cls(
            state_id=str(payload["id"]),
            title=str(payload.get("title") or payload["id"]),
            terminal=bool(payload.get("terminal", False)),
            metadata=dict(payload.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "id": self.state_id,
            "title": self.title,
            "terminal": self.terminal,
        }
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        return data


@dataclass(frozen=True)
class WorkflowDslTransition:
    transition_id: str
    from_state: str
    to_state: str
    capability: str
    approval_required: bool = False
    receipt_required: bool = False
    automatic: bool = False
    guards: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "WorkflowDslTransition":
        return cls(
            transition_id=str(payload["id"]),
            from_state=str(payload["from"]),
            to_state=str(payload["to"]),
            capability=str(payload["capability"]),
            approval_required=bool(payload.get("approval_required", False)),
            receipt_required=bool(payload.get("receipt_required", False)),
            automatic=bool(payload.get("automatic", False)),
            guards=[str(item) for item in payload.get("guards", [])],
            metadata=dict(payload.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "id": self.transition_id,
            "from": self.from_state,
            "to": self.to_state,
            "capability": self.capability,
            "approval_required": self.approval_required,
            "receipt_required": self.receipt_required,
            "automatic": self.automatic,
        }
        if self.guards:
            data["guards"] = list(self.guards)
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        return data


@dataclass(frozen=True)
class WorkflowDsl:
    schema_version: str
    workflow_id: str
    title: str
    initial_state: str
    states: List[WorkflowDslState]
    transitions: List[WorkflowDslTransition]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "WorkflowDsl":
        return cls(
            schema_version=str(payload["schema_version"]),
            workflow_id=str(payload["id"]),
            title=str(payload.get("title") or payload["id"]),
            initial_state=str(payload["initial_state"]),
            states=[
                WorkflowDslState.from_mapping(item)
                for item in payload.get("states", [])
            ],
            transitions=[
                WorkflowDslTransition.from_mapping(item)
                for item in payload.get("transitions", [])
            ],
            metadata=dict(payload.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "id": self.workflow_id,
            "title": self.title,
            "initial_state": self.initial_state,
            "states": [state.to_dict() for state in self.states],
            "transitions": [
                transition.to_dict() for transition in self.transitions
            ],
        }
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
    }

    if payload is not None:
        errors.extend(_validate_payload(payload))
        states = payload.get("states") if isinstance(payload, Mapping) else []
        transitions = payload.get("transitions") if isinstance(payload, Mapping) else []
        details.update(
            {
                "workflow_id": payload.get("id"),
                "state_count": len(states) if isinstance(states, list) else 0,
                "transition_count": (
                    len(transitions) if isinstance(transitions, list) else 0
                ),
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
        if path.suffix.lower() == ".json":
            payload = json.loads(raw_text)
        else:
            payload = yaml.safe_load(raw_text)
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
    _validate_header(errors, payload)

    states = payload.get("states")
    transitions = payload.get("transitions")
    state_ids, terminal_states = _validate_states(errors, states)
    _validate_transitions(errors, transitions, state_ids, terminal_states)

    initial_state = payload.get("initial_state")
    if _non_empty_string(initial_state) and str(initial_state) not in state_ids:
        errors.append(
            issue(
                "WORKFLOW_DSL_INITIAL_STATE_UNKNOWN",
                f"Initial state is not declared: {initial_state}",
                path="/initial_state",
            )
        )
    return errors


def _validate_header(
    errors: List[ValidationIssue],
    payload: Mapping[str, Any],
) -> None:
    if str(payload.get("schema_version") or "") != SUPPORTED_SCHEMA_VERSION:
        errors.append(
            issue(
                "WORKFLOW_DSL_SCHEMA_VERSION_UNSUPPORTED",
                f"schema_version must be {SUPPORTED_SCHEMA_VERSION}.",
                path="/schema_version",
            )
        )
    if not _non_empty_string(payload.get("id")):
        errors.append(
            issue(
                "WORKFLOW_DSL_ID_MISSING",
                "Workflow DSL must include a non-empty id.",
                path="/id",
            )
        )
    if not _non_empty_string(payload.get("initial_state")):
        errors.append(
            issue(
                "WORKFLOW_DSL_INITIAL_STATE_MISSING",
                "Workflow DSL must include a non-empty initial_state.",
                path="/initial_state",
            )
        )


def _validate_states(
    errors: List[ValidationIssue],
    states: Any,
) -> tuple[set[str], set[str]]:
    if not isinstance(states, list) or not states:
        errors.append(
            issue(
                "WORKFLOW_DSL_STATES_MISSING",
                "Workflow DSL must include a non-empty states list.",
                path="/states",
            )
        )
        return set(), set()

    seen: set[str] = set()
    terminal: set[str] = set()
    for index, state_payload in enumerate(states):
        path = f"/states/{index}"
        if not isinstance(state_payload, Mapping):
            errors.append(
                issue(
                    "WORKFLOW_DSL_STATE_INVALID",
                    "State entry must be a mapping.",
                    path=path,
                )
            )
            continue
        state_id = state_payload.get("id")
        if not _non_empty_string(state_id):
            errors.append(
                issue(
                    "WORKFLOW_DSL_STATE_ID_MISSING",
                    "State entry must include a non-empty id.",
                    path=f"{path}/id",
                )
            )
            continue
        state_id_text = str(state_id)
        if state_id_text in seen:
            errors.append(
                issue(
                    "WORKFLOW_DSL_DUPLICATE_STATE",
                    f"Duplicate state id: {state_id_text}",
                    path=f"{path}/id",
                )
            )
        seen.add(state_id_text)
        if bool(state_payload.get("terminal", False)):
            terminal.add(state_id_text)
    return seen, terminal


def _validate_transitions(
    errors: List[ValidationIssue],
    transitions: Any,
    state_ids: set[str],
    terminal_states: set[str],
) -> None:
    if not isinstance(transitions, list) or not transitions:
        errors.append(
            issue(
                "WORKFLOW_DSL_TRANSITIONS_MISSING",
                "Workflow DSL must include a non-empty transitions list.",
                path="/transitions",
            )
        )
        return

    policy = load_approval_policy()
    seen: set[str] = set()
    for index, transition_payload in enumerate(transitions):
        path = f"/transitions/{index}"
        if not isinstance(transition_payload, Mapping):
            errors.append(
                issue(
                    "WORKFLOW_DSL_TRANSITION_INVALID",
                    "Transition entry must be a mapping.",
                    path=path,
                )
            )
            continue

        transition_id = _text_value(transition_payload.get("id"))
        from_state = _text_value(transition_payload.get("from"))
        to_state = _text_value(transition_payload.get("to"))
        capability_id = _text_value(transition_payload.get("capability"))
        _validate_transition_required_fields(
            errors,
            path,
            transition_id,
            from_state,
            to_state,
            capability_id,
        )
        if not transition_id or not from_state or not to_state or not capability_id:
            continue

        if transition_id in seen:
            errors.append(
                issue(
                    "WORKFLOW_DSL_DUPLICATE_TRANSITION",
                    f"Duplicate transition id: {transition_id}",
                    path=f"{path}/id",
                )
            )
        seen.add(transition_id)

        if from_state not in state_ids:
            errors.append(
                issue(
                    "WORKFLOW_DSL_UNKNOWN_FROM_STATE",
                    f"Transition source state is not declared: {from_state}",
                    path=f"{path}/from",
                )
            )
        elif from_state in terminal_states:
            errors.append(
                issue(
                    "WORKFLOW_DSL_TERMINAL_SOURCE",
                    f"Transition source state is terminal: {from_state}",
                    path=f"{path}/from",
                )
            )

        if to_state not in state_ids:
            errors.append(
                issue(
                    "WORKFLOW_DSL_UNKNOWN_TO_STATE",
                    f"Transition target state is not declared: {to_state}",
                    path=f"{path}/to",
                )
            )

        capability = policy.capabilities.get(capability_id)
        if capability is None or capability.tier not in REQUIRED_TIERS:
            errors.append(
                issue(
                    "WORKFLOW_DSL_UNKNOWN_CAPABILITY",
                    f"Transition capability is not registered: {capability_id}",
                    path=f"{path}/capability",
                )
            )
            continue
        _validate_capability_gates(errors, path, transition_payload, capability)


def _validate_transition_required_fields(
    errors: List[ValidationIssue],
    path: str,
    transition_id: str,
    from_state: str,
    to_state: str,
    capability_id: str,
) -> None:
    required = {
        "id": transition_id,
        "from": from_state,
        "to": to_state,
        "capability": capability_id,
    }
    for key, value in required.items():
        if not value:
            errors.append(
                issue(
                    "WORKFLOW_DSL_TRANSITION_FIELD_MISSING",
                    f"Transition must include non-empty {key}.",
                    path=f"{path}/{key}",
                )
            )


def _validate_capability_gates(
    errors: List[ValidationIssue],
    path: str,
    transition_payload: Mapping[str, Any],
    capability: Any,
) -> None:
    write_like = capability.mode in WRITE_MODES or capability.tier in WRITE_TIERS
    if write_like:
        if transition_payload.get("approval_required") is not True:
            errors.append(
                issue(
                    "WORKFLOW_DSL_WRITE_APPROVAL_REQUIRED",
                    "Write/destructive capabilities must require approval.",
                    path=f"{path}/approval_required",
                )
            )
        if transition_payload.get("receipt_required") is not True:
            errors.append(
                issue(
                    "WORKFLOW_DSL_WRITE_RECEIPT_REQUIRED",
                    "Write/destructive capabilities must require receipts.",
                    path=f"{path}/receipt_required",
                )
            )

    if transition_payload.get("automatic") is True and not (
        capability.automatic_allowed
        and capability.tier in {"T0", "T1"}
        and not capability.approval_required
    ):
        errors.append(
            issue(
                "WORKFLOW_DSL_AUTOMATIC_CAPABILITY_FORBIDDEN",
                "Only automatic T0/T1 capabilities may be marked automatic.",
                path=f"{path}/automatic",
            )
        )


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _text_value(value: Any) -> str:
    return str(value).strip() if _non_empty_string(value) else ""
