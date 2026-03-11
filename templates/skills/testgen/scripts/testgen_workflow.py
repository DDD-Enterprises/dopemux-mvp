#!/usr/bin/env python3
"""Deterministic helpers for the testgen skill."""

from __future__ import annotations

import json
import re
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

VALID_MODES = {"tdd-driver", "post-impl-generator"}
VALID_SOURCES = {"feature-list", "task-packet"}
VALID_PREFERRED_CLIS = {"auto", "gemini", "copilot", "claude"}
VALID_PAL_OPTIONS = {"auto", "on", "off"}


class ScopeResolutionError(RuntimeError):
    """Raised when touched-file scope cannot be resolved deterministically."""


class CoverageResolutionError(RuntimeError):
    """Raised when coverage evaluation cannot be completed safely."""


class ToolingResolutionError(RuntimeError):
    """Raised when tool strategy cannot satisfy request constraints."""


@dataclass(frozen=True)
class Requirement:
    req_id: str
    text: str
    source: str


@dataclass(frozen=True)
class LayerDecision:
    layer: str
    applicable: bool
    rationale: str
    evidence_required: str


@dataclass(frozen=True)
class ToolAvailability:
    thinkdeep: bool = True
    planner: bool = True
    consensus: bool = True
    clink: bool = True
    pal_testgen: bool = False

    @classmethod
    def from_dict(cls, raw: Optional[Dict[str, Any]]) -> "ToolAvailability":
        if raw is None:
            return cls()
        allowed = {field: bool(raw.get(field, getattr(cls(), field))) for field in cls.__dataclass_fields__}
        return cls(**allowed)


@dataclass(frozen=True)
class TestgenRequest:
    mode: str
    source: str
    payload: str
    coverage_target: int = 90
    preferred_cli: str = "auto"
    use_pal_testgen: str = "auto"


def _normalize_lines(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _strip_bullet_prefix(line: str) -> str:
    return re.sub(r"^\s*(?:[-*+]|\d+[.)])\s*", "", line).strip()


def parse_feature_list_payload(payload: str) -> List[Requirement]:
    """Parse feature-list payload into stable requirements."""
    candidates: List[str] = []
    stripped = payload.strip()
    if not stripped:
        raise ValueError("Feature list payload is empty")

    if stripped.startswith("["):
        try:
            data = json.loads(stripped)
            if isinstance(data, list):
                candidates = [str(item).strip() for item in data if str(item).strip()]
        except json.JSONDecodeError:
            candidates = []

    if not candidates:
        for raw_line in _normalize_lines(payload):
            cleaned = _strip_bullet_prefix(raw_line)
            if cleaned:
                candidates.append(cleaned)

    if not candidates:
        raise ValueError("No valid feature entries found")

    return [Requirement(req_id=f"F{idx:03d}", text=item, source="feature-list") for idx, item in enumerate(candidates, 1)]


def _extract_markdown_section(markdown: str, header: str) -> str:
    pattern = re.compile(
        rf"^\s*##\s+{re.escape(header)}\s*$([\s\S]*?)(?=^\s*##\s+|\Z)",
        re.MULTILINE,
    )
    match = pattern.search(markdown)
    return match.group(1).strip() if match else ""


def _extract_bullets(section_text: str) -> List[str]:
    bullets: List[str] = []
    for raw_line in section_text.splitlines():
        line = raw_line.rstrip()
        if re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", line):
            bullets.append(_strip_bullet_prefix(line))
    return [bullet for bullet in bullets if bullet]


def _extract_scope_in_items(scope_section: str) -> List[str]:
    if not scope_section:
        return []
    in_pattern = re.compile(r"IN:\s*([\s\S]*?)(?:\n\s*OUT:|\Z)", re.IGNORECASE)
    match = in_pattern.search(scope_section)
    if not match:
        return []
    return _extract_bullets(match.group(1))


def parse_task_packet_payload(payload: str) -> List[Requirement]:
    """Extract requirements from a task packet body."""
    requirements: List[Requirement] = []

    objective_section = _extract_markdown_section(payload, "Objective")
    objective_lines = _normalize_lines(objective_section)
    if objective_lines:
        requirements.append(Requirement(req_id="TP001", text=objective_lines[0], source="objective"))

    scope_items = _extract_scope_in_items(_extract_markdown_section(payload, "Scope"))
    for idx, item in enumerate(scope_items, 1):
        requirements.append(Requirement(req_id=f"TP1{idx:02d}", text=item, source="scope-in"))

    invariant_items = _extract_bullets(_extract_markdown_section(payload, "Invariants (Must Remain True)"))
    for idx, item in enumerate(invariant_items, 1):
        requirements.append(Requirement(req_id=f"TP2{idx:02d}", text=item, source="invariant"))

    acceptance_items = _extract_bullets(_extract_markdown_section(payload, "Acceptance Criteria"))
    for idx, item in enumerate(acceptance_items, 1):
        requirements.append(Requirement(req_id=f"TP3{idx:02d}", text=item, source="acceptance"))

    if not requirements:
        raise ValueError("Task packet parsing yielded zero requirements")

    return requirements


def _normalize_repo_path(path: str) -> str:
    return Path(path).as_posix().lstrip("./")


def _run_git(repo_root: Path, args: Sequence[str]) -> List[str]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _parse_status_paths(lines: Iterable[str]) -> List[str]:
    paths: List[str] = []
    for line in lines:
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        normalized = _normalize_repo_path(path)
        if normalized:
            paths.append(normalized)
    return paths


def resolve_touched_files(
    repo_root: Path,
    explicit_touched: Optional[Sequence[str]] = None,
    base_ref: Optional[str] = None,
    feature_file_map: Optional[Sequence[str]] = None,
) -> List[str]:
    """Resolve touched files deterministically with fail-closed semantics."""
    if explicit_touched:
        touched = sorted({_normalize_repo_path(path) for path in explicit_touched if path.strip()})
        if touched:
            return touched

    status_lines = _run_git(repo_root, ["status", "--porcelain"])
    status_paths = sorted(set(_parse_status_paths(status_lines)))
    if status_paths:
        return status_paths

    if base_ref:
        diff_lines = _run_git(repo_root, ["diff", "--name-only", f"{base_ref}...HEAD"])
    else:
        diff_lines = _run_git(repo_root, ["diff", "--name-only", "HEAD"])
    diff_paths = sorted({_normalize_repo_path(path) for path in diff_lines if path.strip()})
    if diff_paths:
        return diff_paths

    if feature_file_map:
        mapped = sorted({_normalize_repo_path(path) for path in feature_file_map if path.strip()})
        if mapped:
            return mapped

    raise ScopeResolutionError(
        "Unable to resolve touched files from git diff/status or feature mapping; provide explicit scope"
    )


def build_specialist_strategy(
    tool_availability: ToolAvailability,
    preferred_cli: str,
    use_pal_testgen: str,
) -> Dict[str, Any]:
    if preferred_cli not in VALID_PREFERRED_CLIS:
        raise ValueError(f"Unsupported preferred_cli: {preferred_cli}")
    if use_pal_testgen not in VALID_PAL_OPTIONS:
        raise ValueError(f"Unsupported use_pal_testgen: {use_pal_testgen}")

    reasoning = {
        "thinkdeep": "thinkdeep" if tool_availability.thinkdeep else "local-reasoning-fallback",
        "planner": "planner" if tool_availability.planner else "local-reasoning-fallback",
        "consensus": "consensus" if tool_availability.consensus else "local-reasoning-fallback",
    }

    cli_resolution = {
        "auto": "gemini",
        "gemini": "gemini",
        "claude": "claude",
        "copilot": "codex",
    }
    selected_cli = cli_resolution[preferred_cli]

    if tool_availability.clink:
        specialist = {
            "primary": f"clink:{selected_cli}:test-specialist",
            "fallback": "builtin-test-specialist",
        }
    else:
        specialist = {
            "primary": "builtin-test-specialist",
            "fallback": "builtin-test-specialist",
        }

    if use_pal_testgen == "on" and not tool_availability.pal_testgen:
        raise ToolingResolutionError("PAL testgen was forced on but is unavailable")

    if use_pal_testgen == "on":
        pal_mode = "enabled"
    elif use_pal_testgen == "off":
        pal_mode = "disabled"
    else:
        pal_mode = "enabled" if tool_availability.pal_testgen else "disabled"

    return {
        "reasoning": reasoning,
        "specialist": specialist,
        "pal_testgen": pal_mode,
    }


def determine_test_layers(
    requirements: Sequence[Requirement],
    touched_files: Sequence[str],
    mode: str,
) -> List[LayerDecision]:
    text_blob = " ".join(req.text.lower() for req in requirements)
    files_blob = " ".join(path.lower() for path in touched_files)

    smoke_signals = ("health", "compose", "service", "startup", "smoke", "deploy")
    integration_signals = ("integration", "bridge", "pipeline", "workflow", "api", "database")
    e2e_signals = ("end-to-end", "user flow", "journey", "browser", "ui", "cli")
    regression_signals = ("regression", "bug", "incident", "fix")

    smoke_applicable = any(sig in text_blob or sig in files_blob for sig in smoke_signals)
    integration_applicable = any(sig in text_blob or sig in files_blob for sig in integration_signals)
    e2e_applicable = any(sig in text_blob or sig in files_blob for sig in e2e_signals)
    regression_applicable = mode == "post-impl-generator" or any(
        sig in text_blob for sig in regression_signals
    )

    decisions = [
        LayerDecision(
            layer="unit",
            applicable=True,
            rationale="Unit coverage is mandatory for all requests.",
            evidence_required="At least one passing unit test mapped to every requirement.",
        ),
        LayerDecision(
            layer="smoke",
            applicable=smoke_applicable,
            rationale="Smoke tests validate startup and health-critical paths.",
            evidence_required="Service boot/health assertions or explicit N/A rationale with evidence.",
        ),
        LayerDecision(
            layer="integration",
            applicable=integration_applicable,
            rationale="Integration tests cover cross-component boundaries.",
            evidence_required="Boundary assertions (API, DB, event, bridge) or explicit N/A rationale.",
        ),
        LayerDecision(
            layer="e2e",
            applicable=e2e_applicable,
            rationale="E2E tests validate user-observable flows.",
            evidence_required="Flow-level assertions (CLI/UI/API journey) or explicit N/A rationale.",
        ),
        LayerDecision(
            layer="regression",
            applicable=regression_applicable,
            rationale="Regression tests guard against issue recurrence.",
            evidence_required="Historical-failure reproduction test or explicit N/A rationale.",
        ),
    ]

    return decisions


def _coverage_for_file(class_nodes: Sequence[ET.Element]) -> Dict[str, Dict[str, int]]:
    stats: Dict[str, Dict[str, int]] = {}
    for node in class_nodes:
        filename = node.attrib.get("filename", "").strip()
        if not filename:
            continue
        normalized = _normalize_repo_path(filename)
        covered = 0
        total = 0
        for line_node in node.findall("./lines/line"):
            total += 1
            if int(line_node.attrib.get("hits", "0")) > 0:
                covered += 1
        if total == 0:
            line_rate = node.attrib.get("line-rate")
            if line_rate is not None:
                total = 1
                covered = 1 if float(line_rate) >= 1.0 else 0
        current = stats.setdefault(normalized, {"covered": 0, "total": 0})
        current["covered"] += covered
        current["total"] += total
    return stats


def evaluate_touched_coverage(
    coverage_xml: Path,
    touched_files: Sequence[str],
    coverage_target: int,
) -> Dict[str, Any]:
    if not coverage_xml.exists():
        raise CoverageResolutionError(f"Coverage XML not found: {coverage_xml}")

    tree = ET.parse(coverage_xml)
    root = tree.getroot()
    class_nodes = root.findall(".//class")
    if not class_nodes:
        raise CoverageResolutionError("Coverage XML has no class entries")

    stats = _coverage_for_file(class_nodes)
    matched: List[str] = []
    missing: List[str] = []
    covered_total = 0
    line_total = 0

    for path in touched_files:
        normalized = _normalize_repo_path(path)
        match_key: Optional[str] = None
        if normalized in stats:
            match_key = normalized
        else:
            # Collect all candidate coverage entries that could plausibly
            # correspond to this touched path, then resolve deterministically.
            candidates = [
                candidate
                for candidate in stats
                if candidate.endswith(normalized) or normalized.endswith(candidate)
            ]
            if candidates:
                min_len = min(len(candidate) for candidate in candidates)
                shortest = sorted(
                    [candidate for candidate in candidates if len(candidate) == min_len]
                )
                if len(shortest) == 1:
                    match_key = shortest[0]
                else:
                    raise CoverageResolutionError(
                        "Ambiguous coverage entries for touched path "
                        f"'{normalized}': " + ", ".join(shortest)
                    )
        if match_key is None:
            missing.append(normalized)
            continue
        matched.append(normalized)
        covered_total += stats[match_key]["covered"]
        line_total += stats[match_key]["total"]

    if missing:
        raise CoverageResolutionError(
            "Coverage data missing for touched files: " + ", ".join(sorted(missing))
        )

    if line_total == 0:
        raise CoverageResolutionError("Touched files have zero measurable coverage lines")

    percent = round((covered_total / line_total) * 100.0, 2)
    status = "pass" if percent >= coverage_target else "fail"
    return {
        "status": status,
        "target": coverage_target,
        "percent": percent,
        "matched_files": sorted(matched),
        "covered_lines": covered_total,
        "total_lines": line_total,
    }


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower())
    slug = slug.strip("_")
    return slug[:48] if slug else "requirement"


def build_traceability_matrix(
    requirements: Sequence[Requirement],
    layer_decisions: Sequence[LayerDecision],
) -> List[Dict[str, Any]]:
    applicable_layers = [decision.layer for decision in layer_decisions if decision.applicable]
    matrix: List[Dict[str, Any]] = []
    for requirement in requirements:
        base_slug = _slugify(requirement.text)
        test_ids = [f"test_{base_slug}_{layer}" for layer in applicable_layers]
        matrix.append(
            {
                "requirement_id": requirement.req_id,
                "requirement_text": requirement.text,
                "source": requirement.source,
                "test_ids": test_ids,
            }
        )
    return matrix


def generate_testgen_plan(
    request: TestgenRequest,
    repo_root: Path,
    tool_availability: Optional[ToolAvailability] = None,
    coverage_xml: Optional[Path] = None,
    explicit_touched: Optional[Sequence[str]] = None,
    base_ref: Optional[str] = None,
    feature_file_map: Optional[Sequence[str]] = None,
    allow_local_reasoning_fallback: bool = True,
) -> Dict[str, Any]:
    if request.mode not in VALID_MODES:
        raise ValueError(f"Unsupported mode: {request.mode}")
    if request.source not in VALID_SOURCES:
        raise ValueError(f"Unsupported source: {request.source}")
    if request.preferred_cli not in VALID_PREFERRED_CLIS:
        raise ValueError(f"Unsupported preferred_cli: {request.preferred_cli}")
    if request.use_pal_testgen not in VALID_PAL_OPTIONS:
        raise ValueError(f"Unsupported use_pal_testgen: {request.use_pal_testgen}")

    if request.source == "feature-list":
        requirements = parse_feature_list_payload(request.payload)
    else:
        requirements = parse_task_packet_payload(request.payload)

    touched_files = resolve_touched_files(
        repo_root=repo_root,
        explicit_touched=explicit_touched,
        base_ref=base_ref,
        feature_file_map=feature_file_map,
    )

    availability = tool_availability or ToolAvailability()
    strategy = build_specialist_strategy(
        tool_availability=availability,
        preferred_cli=request.preferred_cli,
        use_pal_testgen=request.use_pal_testgen,
    )

    if not allow_local_reasoning_fallback:
        missing = [
            tool for tool in ("thinkdeep", "planner", "consensus") if strategy["reasoning"][tool] == "local-reasoning-fallback"
        ]
        if missing:
            raise ToolingResolutionError(
                "Local reasoning fallback disabled and required tools are unavailable: " + ", ".join(missing)
            )

    layer_decisions = determine_test_layers(requirements, touched_files, request.mode)
    traceability_matrix = build_traceability_matrix(requirements, layer_decisions)

    if coverage_xml is None:
        coverage_gate = {
            "status": "pending",
            "target": request.coverage_target,
            "percent": None,
            "reason": "Coverage XML not provided",
        }
    else:
        coverage_gate = evaluate_touched_coverage(
            coverage_xml=coverage_xml,
            touched_files=touched_files,
            coverage_target=request.coverage_target,
        )

    na_layers = [
        {
            "layer": decision.layer,
            "rationale": decision.rationale,
            "evidence_required": decision.evidence_required,
        }
        for decision in layer_decisions
        if not decision.applicable
    ]

    next_actions = [
        "Generate unit tests mapped from traceability_matrix.",
        "Generate all applicable non-unit layers and document explicit N/A evidence for skipped layers.",
        "Run tests and collect coverage for touched files.",
        "Enforce coverage gate and fail closed on missing evidence.",
    ]

    return {
        "request": {
            "mode": request.mode,
            "source": request.source,
            "coverage_target": request.coverage_target,
            "preferred_cli": request.preferred_cli,
            "use_pal_testgen": request.use_pal_testgen,
        },
        "requirements": [req.__dict__ for req in requirements],
        "touched_files": touched_files,
        "tool_strategy": strategy,
        "layer_plan": [decision.__dict__ for decision in layer_decisions],
        "na_layers": na_layers,
        "traceability_matrix": traceability_matrix,
        "coverage_gate": coverage_gate,
        "next_actions": next_actions,
    }
