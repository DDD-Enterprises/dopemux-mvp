"""Stage 2: Corpus audit — run canonical v5 integrated prescan and visualize results."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, Dict, List, Tuple

from dopemux.console import console

from .display import render_corpus_table, render_educational_panel, render_prescan_hud
from .stages import AUTHORITY_CLASSES, StageResult, StageStatus, WizardState


def _load_v5_runner_module(repo_root: Path) -> ModuleType:
    runner_path = repo_root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    if not runner_path.exists():
        raise FileNotFoundError(f"Canonical v5 runner not found: {runner_path}")

    spec = importlib.util.spec_from_file_location("dopemux_wizard_rte_v5", runner_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {runner_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _build_corpus_stats(manifest: List[Dict[str, Any]]) -> Dict[str, Any]:
    included = [entry for entry in manifest if entry.get("include", False)]
    by_class: Dict[str, Dict[str, int]] = {}
    by_extension: Dict[str, int] = {}
    by_directory: Dict[str, int] = {}

    for entry in included:
        authority_class = str(entry.get("authority_class", "unknown") or "unknown")
        size_bytes = int(entry.get("size_bytes", 0) or 0)
        rel_path = str(entry.get("rel_path", "") or "")
        extension = str(entry.get("extension", "") or "")
        top_dir = rel_path.split("/", 1)[0] if "/" in rel_path else "root"

        cls_row = by_class.setdefault(authority_class, {"count": 0, "total_size": 0})
        cls_row["count"] += 1
        cls_row["total_size"] += size_bytes
        by_extension[extension] = by_extension.get(extension, 0) + 1
        by_directory[top_dir] = by_directory.get(top_dir, 0) + 1

    return {
        "total_files_scanned": len(manifest),
        "included_count": len(included),
        "excluded_count": len(manifest) - len(included),
        "total_included_size": sum(int(entry.get("size_bytes", 0) or 0) for entry in included),
        "by_class": by_class,
        "by_extension": dict(sorted(by_extension.items())),
        "by_directory": dict(sorted(by_directory.items())),
    }


def _run_integrated_v5_prescan(state: WizardState) -> Tuple[Path, Any]:
    module = _load_v5_runner_module(state.repo_root)
    run_root = (
        state.repo_root
        / "extraction"
        / "repo-truth-extractor"
        / "v5"
        / "runs"
        / state.run_id
    )
    run_root.mkdir(parents=True, exist_ok=True)
    cfg = SimpleNamespace(
        prescan_skip=False,
        prescan_import_dir=None,
        prescan_online=False,
        allow_online_llm=False,
        prescan_allow_scope_reduction=False,
    )
    router = module.run_integrated_prescan_stage(state.repo_root, run_root, cfg)
    return run_root / "prescan", router


def _load_optional_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def run_corpus_audit(state: WizardState) -> StageResult:
    """Stage 2 — Run canonical Stage 0 prescan and parse its manifest/intelligence."""
    if not state.run_id:
        return StageResult(status=StageStatus.FAILED, message="Wizard run_id is missing")

    console.print(
        "[bold cyan]Running canonical v5 integrated Phase 0 prescan "
        "(local analysis only — no live provider spend)…[/bold cyan]\n"
    )

    try:
        prescan_dir, router = _run_integrated_v5_prescan(state)
    except Exception as exc:
        console.print(f"[bold red]Integrated prescan failed: {exc}[/bold red]")
        return StageResult(status=StageStatus.FAILED, message="Integrated prescan failed")

    # Parse canonical v5 outputs
    manifest_path = prescan_dir / "corpus_manifest.json"
    intelligence_path = prescan_dir / "prescan_intelligence.json"

    if not manifest_path.exists():
        console.print("[bold red]❌  corpus_manifest.json not found after integrated prescan[/bold red]")
        return StageResult(status=StageStatus.FAILED, message="Prescan output missing")

    try:
        with open(manifest_path, encoding="utf-8") as f:
            state.corpus_manifest = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        console.print(f"[bold red]Failed to parse corpus_manifest.json: {exc}[/bold red]")
        return StageResult(status=StageStatus.FAILED, message="Manifest JSON parse error")

    intelligence = _load_optional_json(intelligence_path)

    state.corpus_stats = _build_corpus_stats(state.corpus_manifest or [])
    state.corpus_included_count = state.corpus_stats.get("included_count", 0)
    state.corpus_total_size = state.corpus_stats.get("total_included_size", 0)
    state.intelligence_router = router
    state.prescan_dir = str(prescan_dir)
    state.code_intelligence = intelligence.get("code_intelligence")

    # Display integrated prescan results
    console.print()
    render_prescan_hud(
        state.corpus_stats,
        intelligence,
        {
            "receipt": _load_optional_json(prescan_dir / "prescan_stage_receipt.json"),
            "batch_plan": _load_optional_json(prescan_dir / "batch_plan.json"),
            "routing_plan": _load_optional_json(prescan_dir / "prescan_routing_plan.json"),
        },
    )
    render_corpus_table(state.corpus_stats)

    excluded = state.corpus_stats.get("excluded_count", 0)
    total_scanned = state.corpus_stats.get("total_files_scanned", 0)
    console.print(
        f"\n  [dim]Scanned {total_scanned:,} total files  •  "
        f"{excluded:,} excluded (noise/binaries/vendor/caches)[/dim]"
    )

    # Educational content
    if state.educate_mode:
        class_descriptions = "\n".join(
            f"  {meta['icon']}  {cls.capitalize()}: {meta['desc']}"
            for cls, meta in AUTHORITY_CLASSES.items()
        )
        render_educational_panel(
            "Integrated Phase 0 prescan",
            "The wizard now uses the same integrated Stage 0 prescan as the canonical v5 extractor.\n\n"
            "This pass runs local dedup, discovery, feasibility, and optimization analysis,\n"
            "writes canonical prescan artifacts under the current v5 run root, and prepares\n"
            "routing intelligence that later wizard phases can reuse.\n\n"
            "Authority classes still describe each file's role in the repository:\n\n"
            f"{class_descriptions}\n\n"
            f"Prescan artifacts for this wizard run live at:\n  {prescan_dir}",
        )

    return StageResult(
        status=StageStatus.COMPLETED,
        message=f"{state.corpus_included_count:,} files, {state.corpus_total_size / (1024*1024):.1f} MB",
        data={
            "included": state.corpus_included_count,
            "size": state.corpus_total_size,
            "prescan_dir": state.prescan_dir,
            "router_loaded": bool(state.intelligence_router),
        },
    )
