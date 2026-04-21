from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

from ..execution_receipts import canonical_json, sha256_hex


DOPECODE_ORCHESTRATION_PLAN_VERSION = "dopecode.orchestration_plan.v1"
DOPECODE_ORCHESTRATION_STATE_VERSION = "dopecode.orchestration_state.v1"

SUPPORTED_STEP_TYPES = frozenset({"apply_patch", "verify_file_sha"})
STEP_STATUSES = frozenset(
    {
        "pending",
        "ready",
        "blocked",
        "running",
        "applied",
        "failed",
        "skipped",
        "verified",
    }
)
SUCCESS_STEP_STATUSES = frozenset({"applied", "skipped", "verified"})
TERMINAL_PLAN_STATUSES = frozenset({"completed", "verified", "failed"})
RESUMABLE_PLAN_STATUSES = frozenset({"blocked", "partial_failure", "running"})


def _sorted_unique(values: Iterable[str]) -> List[str]:
    return sorted({value for value in values if value})


def _normalize_step(step: Dict[str, Any]) -> Dict[str, Any]:
    step_type = str(step.get("step_type", "")).strip()
    if step_type not in SUPPORTED_STEP_TYPES:
        raise ValueError(f"Unsupported orchestration step type: {step_type!r}")

    title = str(step.get("title", "")).strip()
    if not title:
        raise ValueError("Orchestration step title must be provided")

    operation = dict(step.get("operation") or {})
    if step_type == "apply_patch":
        required = ("path", "diff_text", "before_sha256", "after_sha256")
    else:
        required = ("path", "expected_sha256")
    missing = [field for field in required if not str(operation.get(field, "")).strip()]
    if missing:
        raise ValueError(f"Orchestration step {step_type!r} missing required fields: {missing}")

    return {
        "step_type": step_type,
        "title": title,
        "file": str(step.get("file") or operation["path"]),
        "operation": operation,
    }


def build_execution_plan(
    *,
    mutation_id: str,
    operation: str,
    operation_class: str,
    summary: str,
    steps: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    normalized_steps = [_normalize_step(step) for step in steps]
    canonical_steps = [
        {
            "sequence": index,
            "step_type": step["step_type"],
            "title": step["title"],
            "file": step["file"],
            "operation": step["operation"],
        }
        for index, step in enumerate(normalized_steps, start=1)
    ]
    plan_core = {
        "schema_version": DOPECODE_ORCHESTRATION_PLAN_VERSION,
        "mutation_id": mutation_id,
        "operation": operation,
        "operation_class": operation_class,
        "summary": summary,
        "steps": canonical_steps,
    }
    plan_id = sha256_hex(canonical_json(plan_core))

    steps_with_identity: List[Dict[str, Any]] = []
    previous_step_id: Optional[str] = None
    for index, step in enumerate(normalized_steps, start=1):
        step_id = sha256_hex(
            canonical_json(
                {
                    "plan_id": plan_id,
                    "sequence": index,
                    "step_type": step["step_type"],
                    "file": step["file"],
                    "title": step["title"],
                }
            )
        )
        steps_with_identity.append(
            {
                "step_id": step_id,
                "sequence": index,
                "step_type": step["step_type"],
                "title": step["title"],
                "file": step["file"],
                "depends_on": [previous_step_id] if previous_step_id else [],
                "status": "ready" if previous_step_id is None else "pending",
                "operation": step["operation"],
                "error": None,
                "result": None,
            }
        )
        previous_step_id = step_id

    files = _sorted_unique(step["file"] for step in steps_with_identity)
    return {
        "schema_version": DOPECODE_ORCHESTRATION_STATE_VERSION,
        "plan_id": plan_id,
        "mutation_id": mutation_id,
        "operation": operation,
        "operation_class": operation_class,
        "plan_status": "ready" if steps_with_identity else "completed",
        "summary": summary,
        "resume_supported": True,
        "deterministic": True,
        "replay_safe": True,
        "current_step_id": steps_with_identity[0]["step_id"] if steps_with_identity else None,
        "blocked_reason": None,
        "next_action": "apply",
        "affected_files": files,
        "steps": steps_with_identity,
        "status_counts": _status_counts(steps_with_identity),
        "completed_step_count": 0,
        "step_count": len(steps_with_identity),
    }


def extract_latest_orchestration_state(
    events: Sequence[Dict[str, Any]],
    *,
    mutation_id: str,
    operation: str,
) -> Optional[Dict[str, Any]]:
    matching: List[Dict[str, Any]] = []
    for event in events:
        if event.get("mutation_id") != mutation_id:
            continue
        if event.get("operation") != operation:
            continue
        payload = event.get("payload")
        if not isinstance(payload, dict):
            continue
        orchestration = payload.get("orchestration")
        if not isinstance(orchestration, dict):
            continue
        matching.append(orchestration)

    if not matching:
        return None

    latest = deepcopy(matching[-1])
    validate_orchestration_state(latest)
    return latest


def validate_orchestration_state(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("schema_version") != DOPECODE_ORCHESTRATION_STATE_VERSION:
        raise ValueError(f"Unsupported orchestration state schema: {state.get('schema_version')!r}")
    for field in ("plan_id", "mutation_id", "operation", "operation_class", "steps"):
        if field not in state:
            raise ValueError(f"Orchestration state missing required field: {field}")
    if not isinstance(state["steps"], list):
        raise ValueError("Orchestration state steps must be a list")

    seen_step_ids = set()
    for step in state["steps"]:
        for field in ("step_id", "sequence", "step_type", "title", "file", "depends_on", "status", "operation"):
            if field not in step:
                raise ValueError(f"Orchestration step missing required field: {field}")
        if step["step_type"] not in SUPPORTED_STEP_TYPES:
            raise ValueError(f"Unsupported orchestration step type: {step['step_type']!r}")
        if step["status"] not in STEP_STATUSES:
            raise ValueError(f"Unsupported orchestration step status: {step['status']!r}")
        if step["step_id"] in seen_step_ids:
            raise ValueError(f"Duplicate orchestration step_id: {step['step_id']}")
        seen_step_ids.add(step["step_id"])
    return state


def resume_requires_explicit_opt_in(state: Dict[str, Any]) -> bool:
    return state.get("plan_status") in RESUMABLE_PLAN_STATUSES


def is_terminal_plan(state: Dict[str, Any]) -> bool:
    return state.get("plan_status") in TERMINAL_PLAN_STATUSES


def execute_plan(
    state: Dict[str, Any],
    *,
    read_file: Callable[[str], str],
    apply_patch: Callable[[str, str], Dict[str, Any]],
    resume: bool,
) -> Dict[str, Any]:
    current = deepcopy(validate_orchestration_state(deepcopy(state)))

    if is_terminal_plan(current):
        current["next_action"] = "none"
        return _finalize_state(current)

    if resume_requires_explicit_opt_in(current) and not resume:
        current["next_action"] = "resume"
        return _finalize_state(current)

    for step in current["steps"]:
        if step["status"] in SUCCESS_STEP_STATUSES:
            continue

        unmet_dependencies = [
            dependency
            for dependency in step["depends_on"]
            if _step_by_id(current["steps"], dependency).get("status") not in SUCCESS_STEP_STATUSES
        ]
        if unmet_dependencies:
            step["status"] = "blocked"
            step["error"] = {
                "reason": "dependency_not_satisfied",
                "depends_on": unmet_dependencies,
            }
            current["plan_status"] = "blocked"
            current["blocked_reason"] = f"Step {step['sequence']} is waiting for required prior work."
            current["current_step_id"] = step["step_id"]
            current["next_action"] = "resume"
            return _finalize_state(current)

        step["status"] = "running"
        outcome = _execute_step(step, read_file=read_file, apply_patch=apply_patch)
        if outcome["status"] == "applied":
            step["status"] = "applied"
            step["result"] = outcome["result"]
        elif outcome["status"] == "verified":
            step["status"] = "verified"
            step["result"] = outcome["result"]
        elif outcome["status"] == "skipped":
            step["status"] = "skipped"
            step["result"] = outcome["result"]
        elif outcome["status"] == "blocked":
            step["status"] = "blocked"
            step["error"] = outcome["error"]
            current["plan_status"] = "blocked"
            current["blocked_reason"] = outcome["error"]["message"]
            current["current_step_id"] = step["step_id"]
            current["next_action"] = "resume"
            return _finalize_state(current)
        else:
            step["status"] = "failed"
            step["error"] = outcome["error"]
            current["plan_status"] = "partial_failure"
            current["blocked_reason"] = outcome["error"]["message"]
            current["current_step_id"] = step["step_id"]
            current["next_action"] = "resume"
            return _finalize_state(current)

        next_pending = next((candidate for candidate in current["steps"] if candidate["status"] == "pending"), None)
        if next_pending is not None:
            next_pending["status"] = "ready"
            current["current_step_id"] = next_pending["step_id"]
            current["plan_status"] = "running"
            current["blocked_reason"] = None
            current["next_action"] = "apply"

    current["plan_status"] = _terminal_plan_status(current["steps"])
    current["current_step_id"] = None
    current["blocked_reason"] = None
    current["next_action"] = "none"
    return _finalize_state(current)


def _execute_step(
    step: Dict[str, Any],
    *,
    read_file: Callable[[str], str],
    apply_patch: Callable[[str, str], Dict[str, Any]],
) -> Dict[str, Any]:
    operation = dict(step["operation"])
    path = str(operation["path"])
    current_sha = sha256_hex(read_file(path))

    if step["step_type"] == "apply_patch":
        if current_sha == operation["after_sha256"]:
            return {
                "status": "skipped",
                "result": {
                    "path": path,
                    "reason": "expected_after_state_already_present",
                },
            }
        if current_sha != operation["before_sha256"]:
            return {
                "status": "blocked",
                "error": {
                    "reason": "workspace_drift",
                    "message": f"Current content for {path} no longer matches the planned precondition.",
                    "path": path,
                },
            }
        result = apply_patch(path, str(operation["diff_text"]))
        return {
            "status": "applied",
            "result": {
                "path": path,
                "receipt_status": result["status"],
            },
        }

    if step["step_type"] == "verify_file_sha":
        if current_sha != operation["expected_sha256"]:
            return {
                "status": "failed",
                "error": {
                    "reason": "verification_failed",
                    "message": f"Verification failed for {path}; expected content hash was not present.",
                    "path": path,
                },
            }
        return {
            "status": "verified",
            "result": {
                "path": path,
                "expected_sha256": operation["expected_sha256"],
            },
        }

    return {
        "status": "failed",
        "error": {
            "reason": "unsupported_step_type",
            "message": f"Unsupported orchestration step type: {step['step_type']!r}",
        },
    }


def summarize_state_for_payload(state: Dict[str, Any]) -> Dict[str, Any]:
    summary_steps = []
    for step in state["steps"]:
        summary_steps.append(
            {
                "step_id": step["step_id"],
                "sequence": step["sequence"],
                "step_type": step["step_type"],
                "title": step["title"],
                "file": step["file"],
                "depends_on": list(step["depends_on"]),
                "status": step["status"],
                "operation": dict(step["operation"]),
                "error": deepcopy(step.get("error")),
                "result": deepcopy(step.get("result")),
            }
        )
    return {
        "schema_version": state["schema_version"],
        "plan_id": state["plan_id"],
        "mutation_id": state["mutation_id"],
        "operation": state["operation"],
        "operation_class": state["operation_class"],
        "plan_status": state["plan_status"],
        "summary": state["summary"],
        "resume_supported": True,
        "deterministic": True,
        "replay_safe": True,
        "current_step_id": state.get("current_step_id"),
        "blocked_reason": state.get("blocked_reason"),
        "next_action": state.get("next_action"),
        "affected_files": list(state.get("affected_files", [])),
        "status_counts": dict(state.get("status_counts", {})),
        "completed_step_count": int(state.get("completed_step_count", 0)),
        "step_count": int(state.get("step_count", len(summary_steps))),
        "steps": summary_steps,
    }


def describe_next_action(state: Dict[str, Any]) -> str:
    action = state.get("next_action")
    if action == "resume":
        return "Resume is required to continue the existing bounded plan."
    if action == "apply":
        return "Apply may continue the bounded plan from the next ready step."
    return "No further action is required for this plan."


def _status_counts(steps: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    counts = {status: 0 for status in sorted(STEP_STATUSES)}
    for step in steps:
        status = str(step.get("status"))
        if status not in counts:
            counts[status] = 0
        counts[status] += 1
    return counts


def _step_by_id(steps: Sequence[Dict[str, Any]], step_id: str) -> Dict[str, Any]:
    for step in steps:
        if step["step_id"] == step_id:
            return step
    raise ValueError(f"Unknown orchestration dependency step_id: {step_id}")


def _terminal_plan_status(steps: Sequence[Dict[str, Any]]) -> str:
    if any(step["status"] == "failed" for step in steps):
        return "failed"
    if any(step["step_type"] == "verify_file_sha" for step in steps):
        return "verified"
    return "completed"


def _finalize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    state["status_counts"] = _status_counts(state["steps"])
    state["completed_step_count"] = sum(1 for step in state["steps"] if step["status"] in SUCCESS_STEP_STATUSES)
    state["step_count"] = len(state["steps"])
    return state
