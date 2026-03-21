#!/usr/bin/env python3
"""Audit targeted backend/runtime branding invariants."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

STRICT_LOG_FILES = [
    "services/activity-capture/main.py",
    "services/activity-capture/activity_tracker.py",
    "services/activity-capture/event_subscriber.py",
    "services/activity-capture/adhd_client.py",
    "services/workspace-watcher/main.py",
    "services/workspace-watcher/event_emitter.py",
    "services/workspace-watcher/app_detector.py",
    "services/workspace-watcher/workspace_mapper.py",
    "services/adhd-dashboard/backend.py",
    "services/adhd-dashboard/task_recommender.py",
    "services/adhd_engine/core/output_dispatcher.py",
    "services/adhd_engine/domains/break-suggester/engine.py",
    "services/adhd_engine/domains/attention/overwhelm_detector.py",
    "services/adhd_engine/domains/task_enablement/decomposition_coordinator.py",
    "services/adhd_engine/ml/energy_predictor.py",
    "services/adhd_engine/integration_bridge_connector.py",
    "services/adhd_engine/workspace_watcher.py",
    "services/adhd_engine/api/routes.py",
    "src/dopemux/workflow/service.py",
    "src/dopemux/workflow/orchestration.py",
    "src/conport/memory_server.py",
]

HTTP_DETAIL_FILES = [
    "services/adhd-dashboard/backend.py",
    "services/adhd_engine/api/routes.py",
]

REQUIRED_SNIPPETS = {
    "services/workspace-watcher/event_emitter.py": [
        "switch_summary",
        "status_chip",
        "tone",
        "voice_header",
    ],
    "services/adhd-dashboard/task_recommender.py": [
        "status_chip",
        "tone",
        "voice_header",
    ],
    "src/dopemux/workflow/models.py": [
        "status_chip",
        "tone",
        "voice_header",
    ],
}


def _attr_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _attr_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _is_call_to(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Call) and _attr_name(node.func) == name


def _iter_logger_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    errors: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func_name = _attr_name(node.func)
        if func_name not in {"logger.info", "logger.warning", "logger.error"}:
            continue
        if not node.args:
            errors.append(f"{path}:{node.lineno} logger call missing message")
            continue
        first_arg = node.args[0]
        if _is_call_to(first_arg, "brand_log"):
            continue
        errors.append(f"{path}:{node.lineno} logger call must wrap message with brand_log()")
    return errors


def _iter_http_detail_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    errors: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or _attr_name(node.func) != "HTTPException":
            continue
        for keyword in node.keywords:
            if keyword.arg != "detail":
                continue
            if _is_call_to(keyword.value, "brand_error"):
                break
            errors.append(f"{path}:{node.lineno} HTTPException detail must use brand_error()")
    return errors


def _iter_required_snippet_violations(path: Path, snippets: list[str]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [
        f"{path}: missing required snippet '{snippet}'"
        for snippet in snippets
        if snippet not in text
    ]


def main() -> int:
    errors: list[str] = []

    for rel_path in STRICT_LOG_FILES:
        path = REPO_ROOT / rel_path
        if not path.exists():
            errors.append(f"{path}: file missing")
            continue
        errors.extend(_iter_logger_violations(path))

    for rel_path in HTTP_DETAIL_FILES:
        path = REPO_ROOT / rel_path
        if not path.exists():
            errors.append(f"{path}: file missing")
            continue
        errors.extend(_iter_http_detail_violations(path))

    for rel_path, snippets in REQUIRED_SNIPPETS.items():
        path = REPO_ROOT / rel_path
        if not path.exists():
            errors.append(f"{path}: file missing")
            continue
        errors.extend(_iter_required_snippet_violations(path, snippets))

    if errors:
        print("Brand lint failed:")
        for error in errors:
            print(f"- {error}")
        print(f"{len(errors)} errors, 0 warnings")
        return 1

    print("0 errors, 0 warnings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
