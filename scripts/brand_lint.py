#!/usr/bin/env python3
"""Production-oriented brand and operator UX lint for audited Dopemux surfaces."""

from __future__ import annotations

import ast
import re
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

AUDITED_PYTHON_FILES = [
    "services/activity-capture/main.py",
    "src/dopemux/cli.py",
    "src/dopemux/commands/extract_commands.py",
    "src/dopemux/commands/extractor_commands.py",
    "src/dopemux/commands/extractor_validation_ui.py",
    "src/dopemux/config/manager.py",
    "src/dopemux/extractor/runner.py",
    "src/dopemux/ui/dashboard.py",
    "src/dopemux/ui/dashboard_detail.py",
    "src/dopemux/ui/service_endpoints.py",
    "src/dopemux/ui/theme.py",
    "src/dopemux/ui/voice.py",
    "src/dopemux/ux/interactive_prompts.py",
    "src/dopemux/ux/launcher_wizard.py",
    "src/dopemux/ux/questionary_support.py",
    "src/dopemux/ux/wizard/cost_profiles.py",
    "src/dopemux/ux/wizard/extraction.py",
    "src/dopemux/ux/wizard/prompts.py",
    "src/dopemux/voice/core.py",
    "services/shared/brand_voice.py",
]

AUTHORITATIVE_BRAND_DOCS = [
    "docs/04-explanation/branding/cli-ux-design-spec.md",
    "docs/03-reference/brand-compliance-checklist.md",
    "docs/04-explanation/branding/dopemux-brand-system.md",
    "docs/04-explanation/ux/ux-style-guide.md",
    "docs/ux/ux-style-guide.md",
]

OPERATIONAL_UI_FILES = [
    "src/dopemux/commands/extractor_validation_ui.py",
    "src/dopemux/ui/dashboard.py",
    "src/dopemux/ui/dashboard_detail.py",
    "src/dopemux/ui/voice.py",
    "src/dopemux/ux/interactive_prompts.py",
    "src/dopemux/ux/launcher_wizard.py",
    "src/dopemux/ux/questionary_support.py",
    "src/dopemux/ux/wizard/cost_profiles.py",
    "src/dopemux/ux/wizard/extraction.py",
    "src/dopemux/ux/wizard/prompts.py",
]

APPROVED_THEME_FILES = {
    "src/dopemux/ui/theme.py",
    "src/dopemux/ui/dopemux.tcss",
}

PROHIBITED_UI_PHRASES = [
    "public shame",
    "roast escalation",
    "shame you",
]

PROHIBITED_UI_MODE_TOKENS = [
    "VoiceMode.UX_SCOLD",
    "VoiceMode.FILTH_DAEMON",
]

HEX_COLOR_RE = re.compile(r"#[0-9A-Fa-f]{6}\b")
MERGE_MARKER_RE = re.compile(r"^(<<<<<<<|=======|>>>>>>>)", re.MULTILINE)


def _rel_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _attr_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _attr_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _is_call_to(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Call) and _attr_name(node.func) == name


def _existing_path(rel_path: str, errors: list[str]) -> Path | None:
    path = REPO_ROOT / rel_path
    if not path.exists():
        errors.append(f"{path}: file missing")
        return None
    return path


def _iter_syntax_violations(path: Path) -> list[str]:
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return [f"{path}:{exc.lineno} syntax error: {exc.msg}"]
    return []


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


def _iter_merge_marker_violations(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if MERGE_MARKER_RE.search(text):
        return [f"{path}: merge conflict markers detected in authoritative brand doc"]
    return []


def _iter_theme_default_violations() -> list[str]:
    errors: list[str] = []
    theme_path = REPO_ROOT / "src/dopemux/ui/theme.py"
    config_path = REPO_ROOT / "src/dopemux/config/manager.py"
    theme_text = theme_path.read_text(encoding="utf-8")
    config_text = config_path.read_text(encoding="utf-8")
    if 'return "mint-mojo"' not in theme_text:
        errors.append(f"{theme_path}: default theme fallback must be mint-mojo")
    if 'theme: str = "mint-mojo"' not in config_text:
        errors.append(f"{config_path}: config default theme must be mint-mojo")
    return errors


def _iter_operational_ui_tone_violations(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    lowered = text.lower()
    for phrase in PROHIBITED_UI_PHRASES:
        if phrase in lowered:
            errors.append(f"{path}: prohibited public-shame phrase '{phrase}' in operational UI surface")
    for token in PROHIBITED_UI_MODE_TOKENS:
        if token in text:
            errors.append(f"{path}: prohibited non-production voice mode '{token}' in operational UI surface")
    return errors


def _iter_palette_violations(path: Path) -> list[str]:
    rel_path = _rel_path(path)
    if rel_path in APPROVED_THEME_FILES:
        return []
    text = path.read_text(encoding="utf-8")
    matches = sorted(set(HEX_COLOR_RE.findall(text)))
    return [
        f"{path}: raw hex color {match} is not allowed outside approved theme files"
        for match in matches
    ]


def main() -> int:
    errors: list[str] = []

    for rel_path in AUDITED_PYTHON_FILES:
        path = _existing_path(rel_path, errors)
        if path is None:
            continue
        errors.extend(_iter_syntax_violations(path))

    for rel_path in STRICT_LOG_FILES:
        path = _existing_path(rel_path, errors)
        if path is None:
            continue
        errors.extend(_iter_logger_violations(path))

    for rel_path in HTTP_DETAIL_FILES:
        path = _existing_path(rel_path, errors)
        if path is None:
            continue
        errors.extend(_iter_http_detail_violations(path))

    for rel_path, snippets in REQUIRED_SNIPPETS.items():
        path = _existing_path(rel_path, errors)
        if path is None:
            continue
        errors.extend(_iter_required_snippet_violations(path, snippets))

    for rel_path in AUTHORITATIVE_BRAND_DOCS:
        path = _existing_path(rel_path, errors)
        if path is None:
            continue
        errors.extend(_iter_merge_marker_violations(path))

    errors.extend(_iter_theme_default_violations())

    for rel_path in OPERATIONAL_UI_FILES:
        path = _existing_path(rel_path, errors)
        if path is None:
            continue
        errors.extend(_iter_operational_ui_tone_violations(path))
        errors.extend(_iter_palette_violations(path))

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
