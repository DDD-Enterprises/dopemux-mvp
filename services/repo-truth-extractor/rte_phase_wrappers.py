from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


HOME_PHASE_BASE_EXCLUDES = [
    "Downloads",
    "Library",
    "Documents",
    "Pictures",
    "Music",
    "Public",
    "Desktop",
    ".cache",
    ".npm",
    ".pip",
]

HOME_PHASE_SENSITIVE_EXCLUDES = [
    ".ssh",
    ".ssh/*",
    ".SSH",
    ".SSH/*",
    ".aws",
    ".aws/*",
    ".AWS",
    ".AWS/*",
    ".config",
    ".CONFIG",
    ".local",
    ".local/*",
    ".LOCAL",
    ".LOCAL/*",
    ".gnupg",
    ".gnupg/*",
    ".GNUPG",
    ".GNUPG/*",
    ".kube",
    ".kube/*",
    ".KUBE",
    ".KUBE/*",
    ".kube/config",
    ".KUBE/config",
    ".KUBE/CONFIG",
    "Containers",
    "Containers/*",
    "containers",
    "containers/*",
    "CONTAINERS",
    "CONTAINERS/*",
    ".netrc",
    ".NETRC",
    ".aws_credentials",
    ".AWS_CREDENTIALS",
    "Library/Keychains",
    "Library/Keychains/*",
    "Library/keychains",
    "Library/keychains/*",
    "library/Keychains",
    "library/Keychains/*",
    "library/keychains",
    "library/keychains/*",
]


@dataclass(frozen=True)
class PhaseWrapperPlan:
    collector: Any
    targets: Optional[List[str]]
    precollected_items: Optional[List[Dict[str, Any]]]


def plan_home_phase(
    *,
    home: Path,
    collector_factory: Callable[[Path, List[str]], Any],
    home_safe_roots: Sequence[str],
    home_scan_mode: str,
    home_safe_filter: Callable[[List[Dict[str, Any]], Path], List[Dict[str, Any]]],
) -> PhaseWrapperPlan:
    excludes = list(HOME_PHASE_BASE_EXCLUDES) + list(HOME_PHASE_SENSITIVE_EXCLUDES)
    collector = collector_factory(home, excludes)
    items = collector.collect(subdirs=list(home_safe_roots))
    if home_scan_mode == "safe":
        items = home_safe_filter(items, home)
    return PhaseWrapperPlan(collector=None, targets=None, precollected_items=items)


def plan_repo_scan_phase(
    *,
    cwd: Path,
    collector_factory: Callable[[Path, List[str]], Any],
    merge_scan_excludes: Callable[[Sequence[str], Sequence[str]], List[str]],
    repo_scan_excludes: Sequence[str],
    base_excludes: Sequence[str],
    targets: Sequence[str],
) -> PhaseWrapperPlan:
    collector = collector_factory(
        cwd,
        merge_scan_excludes(list(base_excludes), repo_scan_excludes),
    )
    return PhaseWrapperPlan(
        collector=collector,
        targets=list(targets),
        precollected_items=None,
    )


def plan_q_phase(
    dirs: Dict[str, Path],
    *,
    aggregated_phases: Sequence[str],
    collect_phase_artifacts: Callable[
        [Dict[str, Path], Sequence[str], Sequence[str]], List[Dict[str, Any]]
    ],
    write_q_promptpack_declared_outputs_manifest: Callable[[Dict[str, Path]], Path],
    to_items: Callable[[Sequence[Path]], List[Dict[str, Any]]],
) -> PhaseWrapperPlan:
    items = collect_phase_artifacts(
        dirs, aggregated_phases, ["raw", "norm", "qa"]
    )
    promptpack_manifest = write_q_promptpack_declared_outputs_manifest(dirs)
    items.extend(to_items([promptpack_manifest]))
    items.sort(key=lambda item: str(item.get("path", "")))
    return PhaseWrapperPlan(collector=None, targets=None, precollected_items=items)


def collect_r_phase_inputs(
    dirs: Dict[str, Path],
    *,
    required_input_phases: Sequence[str],
    optional_input_phases: Sequence[str],
) -> Dict[str, Any]:
    input_files: List[Path] = []
    for phase in required_input_phases:
        phase_norm = dirs[phase] / "norm"
        if phase_norm.exists():
            input_files.extend(sorted(phase_norm.glob("*.json")))
            input_files.extend(sorted(phase_norm.glob("*.md")))

    optional_contributed: List[Tuple[str, int]] = []
    optional_skipped: List[Tuple[str, str]] = []
    for opt_phase in optional_input_phases:
        opt_dir = dirs.get(opt_phase)
        if opt_dir is None:
            optional_skipped.append((opt_phase, "missing_phase_dir"))
            continue
        opt_norm = opt_dir / "norm"
        if not opt_norm.exists():
            optional_skipped.append((opt_phase, "no_norm_dir"))
            continue
        opt_files = sorted(opt_norm.glob("*.json")) + sorted(opt_norm.glob("*.md"))
        if opt_files:
            input_files.extend(opt_files)
            optional_contributed.append((opt_phase, len(opt_files)))
        else:
            optional_skipped.append((opt_phase, "empty_norm_dir"))

    deduped_inputs = sorted(set(input_files), key=str)
    return {
        "deduped_inputs": deduped_inputs,
        "optional_contributed": optional_contributed,
        "optional_skipped": optional_skipped,
    }


def plan_r_phase(
    dirs: Dict[str, Path],
    *,
    required_input_phases: Sequence[str],
    optional_input_phases: Sequence[str],
    to_items: Callable[[Sequence[Path]], List[Dict[str, Any]]],
) -> Dict[str, Any]:
    summary = collect_r_phase_inputs(
        dirs,
        required_input_phases=required_input_phases,
        optional_input_phases=optional_input_phases,
    )
    return {
        **summary,
        "plan": PhaseWrapperPlan(
            collector=None,
            targets=None,
            precollected_items=to_items(summary["deduped_inputs"]),
        ),
    }


def plan_x_phase(
    *,
    cwd: Path,
    collector_factory: Callable[[Path, List[str]], Any],
    merge_scan_excludes: Callable[[Sequence[str], Sequence[str]], List[str]],
    repo_scan_excludes: Sequence[str],
) -> PhaseWrapperPlan:
    return plan_repo_scan_phase(
        cwd=cwd,
        collector_factory=collector_factory,
        merge_scan_excludes=merge_scan_excludes,
        repo_scan_excludes=repo_scan_excludes,
        base_excludes=[".git", "node_modules"],
        targets=[
            "services",
            "src",
            "docs",
            "config",
            "scripts",
            "Makefile",
            "docker",
            "compose.yml",
        ],
    )


def plan_t_phase(
    dirs: Dict[str, Path],
    *,
    repo_root: Path,
    governance_paths: Sequence[str],
    to_items: Callable[[Sequence[Path]], List[Dict[str, Any]]],
) -> PhaseWrapperPlan:
    input_files: List[Path] = []
    for phase in ["R", "X"]:
        norm_dir = dirs[phase] / "norm"
        if norm_dir.exists():
            input_files.extend(sorted(norm_dir.glob("*.json")))
            input_files.extend(sorted(norm_dir.glob("*.md")))
    for rel_path in governance_paths:
        candidate = repo_root / rel_path
        if candidate.exists():
            input_files.append(candidate)
    return PhaseWrapperPlan(
        collector=None,
        targets=None,
        precollected_items=to_items(input_files),
    )


def collect_s_input_sources(
    dirs: Dict[str, Path],
    *,
    safe_read: Callable[[Path], str],
) -> Dict[str, Any]:
    r_norm = dirs["R"] / "norm"
    input_sources: Dict[Path, str] = {}
    if r_norm.exists():
        for path in sorted(r_norm.glob("*.json")) + sorted(r_norm.glob("*.md")):
            input_sources[path.resolve()] = "R"

    r_quality_issues: List[str] = []
    if not input_sources:
        r_quality_issues.append(f"missing_norm_outputs:{r_norm}")
    else:
        non_empty_outputs = 0
        for path in sorted(input_sources.keys(), key=str):
            content = safe_read(path)
            if not content.strip():
                r_quality_issues.append(f"empty_output:{path.name}")
                continue
            if path.suffix.lower() == ".json":
                try:
                    json.loads(content)
                except json.JSONDecodeError:
                    r_quality_issues.append(f"invalid_json:{path.name}")
                    continue
            non_empty_outputs += 1
        if non_empty_outputs == 0:
            r_quality_issues.append("no_nonempty_r_outputs")
    return {"input_sources": input_sources, "r_quality_issues": r_quality_issues}


def extend_input_sources_with_phase_norms(
    input_sources: Dict[Path, str],
    dirs: Dict[str, Path],
    *,
    phases: Sequence[str],
) -> None:
    for phase in phases:
        norm_dir = dirs[phase] / "norm"
        if norm_dir.exists():
            for path in sorted(norm_dir.glob("*.json")) + sorted(norm_dir.glob("*.md")):
                input_sources.setdefault(path.resolve(), phase)


def add_manual_rulings_sources(input_sources: Dict[Path, str], run_root: Path) -> None:
    manual_rulings_dir = run_root / "manual_rulings"
    if not manual_rulings_dir.exists():
        return
    for path in sorted(manual_rulings_dir.glob("PRO_*.json")):
        input_sources.setdefault(path.resolve(), "MANUAL")


def plan_s_phase(
    dirs: Dict[str, Path],
    *,
    safe_read: Callable[[Path], str],
    write_truth_pack_manifest: Callable[[Dict[str, Path], Dict[Path, str]], Path],
    to_items: Callable[[Sequence[Path]], List[Dict[str, Any]]],
) -> Dict[str, Any]:
    summary = collect_s_input_sources(dirs, safe_read=safe_read)
    input_sources = summary["input_sources"]
    extend_input_sources_with_phase_norms(input_sources, dirs, phases=["X", "T", "Z"])
    add_manual_rulings_sources(input_sources, dirs["root"])
    deduped_inputs = sorted(input_sources.keys(), key=str)
    truth_pack_manifest = write_truth_pack_manifest(dirs, input_sources)
    precollected_files = deduped_inputs + [truth_pack_manifest]
    return {
        **summary,
        "input_sources": input_sources,
        "deduped_inputs": deduped_inputs,
        "truth_pack_manifest": truth_pack_manifest,
        "plan": PhaseWrapperPlan(
            collector=None,
            targets=None,
            precollected_items=to_items(precollected_files),
        ),
    }


def plan_sp_phase(
    dirs: Dict[str, Path],
    *,
    to_items: Callable[[Sequence[Path]], List[Dict[str, Any]]],
) -> Dict[str, Any]:
    r_norm = dirs["R"] / "norm"
    input_sources: Dict[Path, str] = {}
    r_input_count = 0
    if r_norm.exists():
        for path in sorted(r_norm.glob("*.json")) + sorted(r_norm.glob("*.md")):
            input_sources[path.resolve()] = "R"
            r_input_count += 1
    extend_input_sources_with_phase_norms(input_sources, dirs, phases=["X", "T", "Z"])
    deduped_inputs = sorted(input_sources.keys(), key=str)
    return {
        "input_sources": input_sources,
        "r_input_count": r_input_count,
        "deduped_inputs": deduped_inputs,
        "plan": PhaseWrapperPlan(
            collector=None,
            targets=None,
            precollected_items=to_items(deduped_inputs),
        ),
    }
