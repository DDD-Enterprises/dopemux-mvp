"""Strict local project mandates. Admission is an explicit trusted-operator action."""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path

VERSION = "dopemux.project_mandate.v1"
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
FIELDS = {
    "schema_version",
    "mandate_id",
    "issuer_ref",
    "project_id",
    "project_root",
    "expires_at",
    "active_seconds",
    "spend_limit_micros",
    "max_parallel",
    "repair_limit",
    "stop_conditions",
    "gates",
    "route",
    "steps",
    "success_steps",
}
STEP_FIELDS = {
    "step_id",
    "kind",
    "argv",
    "effects",
    "write_paths",
    "depends_on",
    "timeout_seconds",
    "heavy",
    "when_failed",
    "resources",
    "capture_bytes",
}
EFFECTS = {"read", "write", "test"}
BYPASSES = {"--dangerously-skip-permissions", "--full-auto", "bypassPermissions"}
FABLE_BASE_URL = "http://127.0.0.1:47821"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def identifier(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError("Invalid stable mandate/project/step identifier")


def finite(value, *, positive=False, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Limit must be finite")
    if value < 0 or (positive and value == 0) or (integer and not isinstance(value, int)):
        raise ValueError("Invalid numeric limit")


def safe_relative(root, value):
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or Path(value).is_absolute()
        or ".." in Path(value).parts
        or any(p.startswith(".git") for p in Path(value).parts)
    ):
        raise ValueError("Write path must be a literal project-relative file")
    current = root
    for part in Path(value).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("Symlink traversal is forbidden")
    if current.exists() and (not current.is_file() or current.stat().st_nlink != 1):
        raise ValueError("Write target is not an ordinary unshared file")
    return current


def validate(raw, authorization_ref):
    if not isinstance(raw, dict) or set(raw) != FIELDS:
        raise ValueError("Mandate has missing or unknown fields")
    if raw["schema_version"] != VERSION or raw["issuer_ref"] != authorization_ref:
        raise ValueError("Explicit issuer authorization reference does not match")
    if not isinstance(authorization_ref, str) or not authorization_ref.strip():
        raise ValueError("Issuer authorization reference required")
    for key in ("mandate_id", "project_id"):
        identifier(raw[key])
    if "REPLACE" in canonical(raw).decode():
        raise ValueError("Template placeholders are not executable authority")
    if not isinstance(raw["project_root"], str):
        raise ValueError("Project root must be a string")
    root = Path(raw["project_root"])
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ValueError("Project root must be an existing absolute ordinary directory")
    if str(root.resolve()) != str(root):
        raise ValueError("Project root must use its canonical resolved path")
    for key in ("expires_at", "active_seconds"):
        finite(raw[key], positive=True)
    for key in ("spend_limit_micros", "max_parallel", "repair_limit"):
        finite(raw[key], integer=True)
    if raw["spend_limit_micros"] != 0:
        raise ValueError("This local-command adapter permits zero paid spend only")
    if not 1 <= raw["max_parallel"] <= 2 or raw["repair_limit"] > 2:
        raise ValueError("Local fleet/repair ceiling exceeded")
    if not isinstance(raw["stop_conditions"], list) or not all(
        isinstance(x, str) and x for x in raw["stop_conditions"]
    ):
        raise ValueError("Stop conditions must be explicit strings")
    gates = raw["gates"]
    if not isinstance(gates, dict) or set(gates) != {
        "security",
        "workflow",
        "spending",
    }:
        raise ValueError("Exact current security/workflow/spending gates required")
    if any(v != "PASS" for v in gates.values()):
        raise ValueError("Unresolved upstream gate")
    route = raw["route"]
    if not isinstance(route, dict) or set(route) != {
        "binding_id",
        "kind",
        "model_class",
        "executable",
        "valid_until",
    }:
        raise ValueError("Route has missing or unknown fields")
    identifier(route["binding_id"])
    if route["kind"] != "local_command" or route["model_class"] != "deterministic":
        raise ValueError("Live model/provider routes require a separate qualified adapter")
    if not isinstance(route["executable"], str):
        raise ValueError("Executable must be a string")
    executable = Path(route["executable"])
    if (
        not executable.is_absolute()
        or not executable.is_file()
        or not os.access(executable, os.X_OK)
    ):
        raise ValueError("Existing absolute executable required; no installation fallback")
    finite(route["valid_until"], positive=True)
    steps = raw["steps"]
    if not isinstance(steps, list) or not 2 <= len(steps) <= 32:
        raise ValueError("A mandate requires bounded implementation and validation steps")
    names = set()
    for step in steps:
        required = STEP_FIELDS - {"when_failed", "resources", "capture_bytes"}
        if not isinstance(step, dict) or not required <= set(step) or set(step) - STEP_FIELDS:
            raise ValueError("Step has missing or unknown fields")
        identifier(step["step_id"])
        if step["step_id"] in names:
            raise ValueError("Duplicate step identity")
        names.add(step["step_id"])
        if not isinstance(step["kind"], str) or step["kind"] not in {
            "implementation",
            "test",
            "validation",
            "repair",
        }:
            raise ValueError("Unknown step kind")
        argv = step["argv"]
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) for x in argv):
            raise ValueError("Explicit argv required; shell interpolation is unsupported")
        if argv[0] != str(executable) or any(
            token in BYPASSES or "bypassPermissions" in token for token in argv
        ):
            raise ValueError("Unbound executable or permission bypass")
        if (
            not isinstance(step["effects"], list)
            or not all(isinstance(x, str) for x in step["effects"])
            or not set(step["effects"]) <= EFFECTS
        ):
            raise ValueError("Unsupported local effect")
        if not isinstance(step["write_paths"], list):
            raise ValueError("Write allowlist required")
        for path in step["write_paths"]:
            safe_relative(root, path)
        if step["write_paths"] and "write" not in step["effects"]:
            raise ValueError("Write paths require the write effect")
        finite(step["timeout_seconds"], positive=True)
        if not isinstance(step["heavy"], bool):
            raise ValueError("Heavy resource declaration must be boolean")
        if "capture_bytes" in step:
            finite(step["capture_bytes"], positive=True, integer=True)
            if step["capture_bytes"] > 1048576:
                raise ValueError("Capture cap exceeded")
        if not isinstance(step["depends_on"], list) or not all(
            isinstance(x, str) for x in step["depends_on"]
        ):
            raise ValueError("Dependencies must be step identities")
        if "resources" in step and (
            not isinstance(step["resources"], list)
            or not all(isinstance(x, str) and x for x in step["resources"])
        ):
            raise ValueError("Resource references must be strings")
        if "when_failed" in step and not isinstance(step["when_failed"], str):
            raise ValueError("Failure dependency must be a step identity")
        if step["kind"] == "repair" and not step.get("when_failed"):
            raise ValueError("Repair requires an explicitly known failed stage")
    graph = {}
    for step in steps:
        deps = list(step["depends_on"])
        if step.get("when_failed"):
            deps.append(step["when_failed"])
        if any(x not in names or x == step["step_id"] for x in deps):
            raise ValueError("Unknown/self dependency")
        graph[step["step_id"]] = deps
    visiting, visited = set(), set()

    def visit(name):
        if name in visiting:
            raise ValueError("Cyclic mandate")
        if name in visited:
            return
        visiting.add(name)
        for dep in graph[name]:
            visit(dep)
        visiting.remove(name)
        visited.add(name)

    for name in graph:
        visit(name)
    if not any(x["kind"] == "implementation" for x in steps):
        raise ValueError("Implementation child required")
    if not any(x["kind"] in {"test", "validation"} for x in steps):
        raise ValueError("Validation child required")
    if (
        not isinstance(raw["success_steps"], list)
        or not raw["success_steps"]
        or not all(isinstance(x, str) for x in raw["success_steps"])
        or not set(raw["success_steps"]) <= names
    ):
        raise ValueError("Exact completion predicates required")
    if any(
        step["kind"] not in {"test", "validation"}
        for step in steps
        if step["step_id"] in raw["success_steps"]
    ):
        raise ValueError("Completion predicates must name validation children")
    if len(canonical(raw)) > 65536:
        raise ValueError("Mandate exceeds compact context ceiling")
    return json.loads(canonical(raw))
