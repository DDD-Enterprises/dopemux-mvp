"""Stage 6: Partition preview — map corpus files to extraction phases."""

from __future__ import annotations

import math
from pathlib import PurePosixPath
from typing import Any, Dict, List, Optional

from dopemux.console import console

from .display import render_educational_panel, render_phase_table
from .stages import PHASE_INFO, PHASES, StageResult, StageStatus, WizardState

# ── Phase-to-path mapping rules ────────────────────────────────────────────
# These are heuristic mappings based on typical repo structure.
# The actual v5 extractor has its own routing but this gives a useful preview.

PHASE_PATH_PATTERNS: Dict[str, List[str]] = {
    "A": [
        "pyproject.toml", "Makefile", "setup.py", "setup.cfg",
        "package.json", "compose.yml", "compose.yaml", "docker-compose.yml",
        "Dockerfile", "Dockerfile.*", ".env.example", "dopemux.toml",
        "litellm.config.yaml", "requirements.txt", "requirements-*.txt",
    ],
    "H": [".dopemux/", ".dopetask/"],
    "D": ["docs/", "*.md", "README*", "CHANGELOG*", "INSTALL*", "QUICK_START*", "AGENTS.md"],
    "C": ["src/", "services/"],
    "E": ["scripts/", "tools/", "ops/"],
    "W": [".github/", ".gitlab-ci*", "compose*.yml"],
    "B": ["contracts/", "openapi*", "swagger*", "*.graphql", "*.proto"],
    "G": [".claude/", ".pre-commit*", "AGENTS.md", ".dopetaskroot"],
    "Q": ["tests/", "test_*", "*_test.py"],
    "T": ["task-packets/"],
}

# Phases without direct file mapping (meta/cross-referencing phases)
META_PHASES = {"R", "X", "Z", "S"}


def _classify_file_to_phase(rel_path: str) -> Optional[str]:
    """Assign a file to its primary extraction phase based on path patterns."""
    path = PurePosixPath(rel_path)
    parts = path.parts

    for phase_key, patterns in PHASE_PATH_PATTERNS.items():
        for pattern in patterns:
            # Directory match (pattern ends with /)
            if pattern.endswith("/"):
                dir_name = pattern.rstrip("/")
                if parts and parts[0] == dir_name:
                    return phase_key
            # Exact filename match
            elif "*" not in pattern:
                if path.name == pattern or rel_path == pattern:
                    return phase_key
            # Glob-like match on filename
            elif pattern.startswith("*."):
                ext = pattern[1:]  # e.g. ".md"
                if path.suffix == ext:
                    return phase_key
            # Prefix match (e.g. "README*")
            elif pattern.endswith("*"):
                prefix = pattern[:-1]
                if path.name.startswith(prefix):
                    return phase_key

    return None


def map_corpus_to_phases(manifest: Optional[List[Dict[str, Any]]]) -> Dict[str, int]:
    """Map included corpus files to phases and return per-phase file counts."""
    counts: Dict[str, int] = {p: 0 for p in PHASES if p not in META_PHASES}

    if not manifest:
        return counts

    for entry in manifest:
        if not entry.get("include", False):
            continue
        rel_path = entry.get("rel_path", "")
        phase = _classify_file_to_phase(rel_path)
        if phase and phase in counts:
            counts[phase] += 1

    return counts


def run_partition_preview(state: WizardState) -> StageResult:
    """Stage 6 — Map corpus files to phases and show partition estimates."""

    file_counts = map_corpus_to_phases(state.corpus_manifest)

    # Display the phase table
    render_phase_table(file_counts)

    # Summary stats
    total_files = sum(file_counts.values())
    total_partitions = sum(
        max(1, math.ceil(c / 50)) for c in file_counts.values() if c > 0
    )
    unmapped = (state.corpus_included_count or 0) - total_files

    console.print(
        f"\n  [bold]Mapped:[/bold] {total_files:,} files → {total_partitions} partitions"
    )
    if unmapped > 0:
        console.print(
            f"  [dim]{unmapped:,} files not mapped to a primary phase "
            f"(may be processed in multiple phases)[/dim]"
        )

    # Educational content
    if state.educate_mode:
        render_educational_panel(
            "How partitioning works",
            "The extractor splits each phase's files into partitions of ~50 files each.\n"
            "Each partition is processed as a single LLM request with the phase's prompt.\n\n"
            "Partition workers (default: 10) run in parallel for each phase.\n"
            "More partitions = more parallelism but more API calls.\n\n"
            "Meta phases (R, X, Z, S) don't have direct file inputs —\n"
            "they cross-reference outputs from earlier phases.",
        )

    console.print()
    return StageResult(
        status=StageStatus.COMPLETED,
        message=f"{total_files:,} files, {total_partitions} partitions",
        data={"file_counts": file_counts, "total_partitions": total_partitions},
    )
