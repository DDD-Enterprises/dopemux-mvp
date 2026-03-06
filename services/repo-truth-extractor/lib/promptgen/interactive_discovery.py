"""Interactive feature discovery for universal repo-truth-extractor.

CLI-driven developer-in-the-loop feature confirmation that extends
auto-detection with human knowledge about the codebase.

Uses Questionary for ADHD-friendly progressive disclosure prompts.

Output: FEATURE_MAP.json + SCOPE_OVERRIDES.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .fingerprint import deterministic_generated_at

logger = logging.getLogger(__name__)

FEATURE_MAP_FILENAME = "FEATURE_MAP.json"
SCOPE_OVERRIDES_FILENAME = "SCOPE_OVERRIDES.json"


def _try_import_questionary():
    """Import questionary with fallback for environments without it."""
    try:
        import questionary
        return questionary
    except ImportError:
        return None


def _try_import_rich():
    """Import rich with fallback."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        return Console, Panel, Table
    except ImportError:
        return None, None, None


def run_interactive_discovery(
    *,
    auto_features: Dict[str, Any],
    phase_plan: Dict[str, Any],
    repo_root: Path,
    run_id: str,
    non_interactive: bool = False,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Run the interactive feature discovery flow.

    Args:
        auto_features: Output from feature_detector.detect_features().
        phase_plan: Output from phase_applicability.determine_phase_plan().
        repo_root: Path to the target repository.
        run_id: Unique run identifier.
        non_interactive: If True, skip all prompts and accept auto-detection as-is.

    Returns:
        Tuple of (FEATURE_MAP.json payload, SCOPE_OVERRIDES.json payload).
    """
    if non_interactive:
        return _build_auto_only_outputs(auto_features, phase_plan, run_id)

    questionary = _try_import_questionary()
    Console, Panel, Table = _try_import_rich()

    if questionary is None:
        logger.warning("questionary not installed — falling back to non-interactive mode")
        return _build_auto_only_outputs(auto_features, phase_plan, run_id)

    console = Console() if Console else None

    # --- Stage 1a: Present auto-detected features ---
    if console and Panel:
        console.print(Panel(
            "[bold cyan]Feature Discovery[/bold cyan]\n"
            "Review auto-detected features. Confirm, correct, or add missing ones.",
            title="[bold]DØPEMÜX Extractor — Stage 1[/bold]",
            border_style="cyan",
        ))

    confirmed_features: List[Dict[str, Any]] = []
    rejected_features: List[str] = []
    added_features: List[Dict[str, Any]] = []

    detected = auto_features.get("detected_features", [])
    if detected:
        if console:
            console.print(f"\n[bold]Auto-detected {len(detected)} features:[/bold]\n")

        for feat in detected:
            label = feat.get("label", feat["feature_id"])
            confidence = feat.get("confidence", "unknown")
            evidence = feat.get("evidence", [])[:3]
            evidence_str = ", ".join(evidence) if evidence else "no evidence"

            try:
                confirmed = questionary.confirm(
                    f"  ✓ {label} ({confidence} confidence) — {evidence_str}",
                    default=True,
                ).ask()
            except (KeyboardInterrupt, EOFError):
                logger.info("Interactive discovery cancelled by user")
                return _build_auto_only_outputs(auto_features, phase_plan, run_id)

            if confirmed is None:
                return _build_auto_only_outputs(auto_features, phase_plan, run_id)

            if confirmed:
                confirmed_features.append(feat)
            else:
                rejected_features.append(feat["feature_id"])
    else:
        if console:
            console.print("[yellow]No features auto-detected.[/yellow]")

    # --- Stage 1b: Ask about missing features ---
    missing_feature_prompts = [
        ("event_bus", "Event bus or message queue (Redis Streams, Kafka, RabbitMQ, NATS)"),
        ("grpc_api", "gRPC API definitions"),
        ("graphql_api", "GraphQL schema and resolvers"),
        ("database_graph", "Graph database (Neo4j, AGE, ArangoDB)"),
        ("database_vector", "Vector/embedding database (Qdrant, Pinecone, ChromaDB)"),
        ("kubernetes", "Kubernetes manifests or Helm charts"),
        ("terraform", "Terraform or other IaC"),
        ("agent_orchestration", "AI agent or bot orchestration"),
        ("plugin_system", "Plugin or extension system"),
        ("monitoring", "Monitoring/observability (Prometheus, Grafana, OpenTelemetry)"),
    ]

    already_detected = set(auto_features.get("feature_ids", []))
    missing_to_ask = [
        (fid, desc) for fid, desc in missing_feature_prompts
        if fid not in already_detected
    ]

    if missing_to_ask:
        if console:
            console.print("\n[bold]Check for features we might have missed:[/bold]\n")

        for fid, desc in missing_to_ask[:5]:  # ADHD: max 5 questions
            try:
                has_it = questionary.confirm(
                    f"  ? {desc}",
                    default=False,
                ).ask()
            except (KeyboardInterrupt, EOFError):
                break

            if has_it is None:
                break

            if has_it:
                # Ask for scan root
                try:
                    root_path = questionary.text(
                        f"    Where is it? (directory path, e.g., 'pkg/events/')",
                        default="",
                    ).ask()
                except (KeyboardInterrupt, EOFError):
                    root_path = ""

                added_features.append({
                    "feature_id": fid,
                    "label": desc,
                    "description": f"Developer-added: {desc}",
                    "confidence": "developer_confirmed",
                    "evidence": [],
                    "scan_roots": [root_path] if root_path else [],
                    "maps_to_steps": [],
                    "maps_to_phases": [],
                })

    # --- Stage 1c: Domain vocabulary ---
    if console:
        console.print("\n[bold]Domain vocabulary mapping:[/bold]\n")

    domain_vocab: Dict[str, str] = {}

    vocab_questions = [
        ("service_term", "What do you call 'services'?", "services"),
        ("config_format", "Primary config format?", "yaml"),
    ]

    for key, question, default in vocab_questions:
        try:
            answer = questionary.text(
                f"  {question}",
                default=default,
            ).ask()
        except (KeyboardInterrupt, EOFError):
            answer = default

        if answer is None:
            answer = default
        domain_vocab[key] = answer

    # Ask for custom patterns (free-form, optional)
    try:
        custom_patterns = questionary.text(
            "  Any architectural patterns to note? (e.g., 'CQRS', 'event sourcing')",
            default="",
        ).ask()
    except (KeyboardInterrupt, EOFError):
        custom_patterns = ""

    if custom_patterns:
        domain_vocab["custom_patterns"] = custom_patterns

    # --- Stage 1d: Scan boundary overrides ---
    scope_overrides: Dict[str, List[str]] = {}

    try:
        wants_overrides = questionary.confirm(
            "\n  Override any scan paths? (default auto-detected paths)",
            default=False,
        ).ask()
    except (KeyboardInterrupt, EOFError):
        wants_overrides = False

    if wants_overrides:
        if console:
            console.print("  [dim]Enter step_id=path1,path2 (e.g., C1=src/api/,services/)[/dim]")
        try:
            override_input = questionary.text(
                "  Overrides (one per line, empty to finish):",
                default="",
            ).ask()
        except (KeyboardInterrupt, EOFError):
            override_input = ""

        if override_input:
            for line in override_input.strip().split("\n"):
                if "=" in line:
                    step_id, paths = line.split("=", 1)
                    scope_overrides[step_id.strip()] = [
                        p.strip() for p in paths.split(",") if p.strip()
                    ]

    # --- Stage 1e: Phase skipping ---
    skippable_phases = []
    for phase_entry in phase_plan.get("phases", []):
        if phase_entry.get("status") == "conditional":
            skippable_phases.append(phase_entry)

    skip_phases: List[str] = []
    if skippable_phases:
        if console:
            console.print("\n[bold]These phases are conditionally included:[/bold]\n")
        for entry in skippable_phases:
            try:
                skip = questionary.confirm(
                    f"  Skip phase {entry['phase']} ({entry['label']})?",
                    default=False,
                ).ask()
            except (KeyboardInterrupt, EOFError):
                break
            if skip:
                skip_phases.append(entry["phase"])

    # --- Build outputs ---
    return _build_outputs(
        auto_features=auto_features,
        confirmed_features=confirmed_features,
        rejected_features=rejected_features,
        added_features=added_features,
        domain_vocab=domain_vocab,
        scope_overrides=scope_overrides,
        skip_phases=skip_phases,
        run_id=run_id,
    )


def _build_auto_only_outputs(
    auto_features: Dict[str, Any],
    phase_plan: Dict[str, Any],
    run_id: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Build outputs when no interactive discovery is performed."""
    feature_map = {
        "version": "FEATURE_MAP_V1",
        "generated_at": deterministic_generated_at(run_id),
        "run_id": run_id,
        "discovery_mode": "auto_only",
        "confirmed_features": auto_features.get("detected_features", []),
        "rejected_features": [],
        "added_features": [],
        "domain_vocabulary": {},
        "skip_phases": [],
        "is_dopemux_repo": auto_features.get("is_dopemux_repo", False),
        "feature_ids": auto_features.get("feature_ids", []),
    }
    scope_overrides = {
        "version": "SCOPE_OVERRIDES_V1",
        "generated_at": deterministic_generated_at(run_id),
        "run_id": run_id,
        "overrides": {},
    }
    return feature_map, scope_overrides


def _build_outputs(
    *,
    auto_features: Dict[str, Any],
    confirmed_features: List[Dict[str, Any]],
    rejected_features: List[str],
    added_features: List[Dict[str, Any]],
    domain_vocab: Dict[str, str],
    scope_overrides: Dict[str, List[str]],
    skip_phases: List[str],
    run_id: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Build the FEATURE_MAP.json and SCOPE_OVERRIDES.json payloads."""
    all_features = confirmed_features + added_features
    all_feature_ids = sorted(set(
        f["feature_id"] for f in all_features
    ))

    feature_map = {
        "version": "FEATURE_MAP_V1",
        "generated_at": deterministic_generated_at(run_id),
        "run_id": run_id,
        "discovery_mode": "interactive",
        "confirmed_features": confirmed_features,
        "rejected_features": rejected_features,
        "added_features": added_features,
        "domain_vocabulary": domain_vocab,
        "skip_phases": skip_phases,
        "is_dopemux_repo": auto_features.get("is_dopemux_repo", False),
        "feature_ids": all_feature_ids,
    }

    scope_overrides_payload = {
        "version": "SCOPE_OVERRIDES_V1",
        "generated_at": deterministic_generated_at(run_id),
        "run_id": run_id,
        "overrides": scope_overrides,
    }

    return feature_map, scope_overrides_payload
