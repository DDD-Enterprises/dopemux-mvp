"""Stage definitions, state management, and phase/authority constants for the wizard."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class StageStatus(Enum):
    """Status of a wizard stage."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class StageResult:
    """Result returned by each wizard stage function."""

    status: StageStatus
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0


@dataclass
class WizardState:
    """Shared mutable state passed between wizard stages."""

    repo_root: Path = field(default_factory=Path.cwd)
    git_branch: str = ""
    git_clean: bool = False
    corpus_stats: Optional[Dict[str, Any]] = None
    corpus_manifest: Optional[List[Dict[str, Any]]] = None
    corpus_included_count: int = 0
    corpus_total_size: int = 0
    grok_response: Optional[Dict[str, Any]] = None
    code_intelligence: Optional[Dict[str, Any]] = None
    intelligence_router: Optional[Any] = None
    prescan_dir: str = ""
    promptset_ready: bool = False
    selected_policy: str = "balanced_openrouter"
    run_id: str = ""
    workers: int = 1
    provider_key_overrides: Dict[str, str] = field(default_factory=dict)
    phase_results: Dict[str, "StageResult"] = field(default_factory=dict)
    execute_mode: bool = False
    educate_mode: bool = True
    max_cost: Optional[float] = 5.0
    validate_live: bool = True
    skip_hygiene: bool = False


# ── 14 extraction phases in pipeline order ──────────────────────────────────

PHASES = ["A", "H", "D", "C", "E", "W", "B", "G", "Q", "R", "X", "T", "Z", "S"]

PHASE_INFO: Dict[str, Dict[str, str]] = {
    "A": {"name": "Repo Control Plane", "icon": "🏗️", "desc": "Analyzes repo structure, entry points, and configuration files"},
    "H": {"name": "Home Control Plane", "icon": "🏠", "desc": "Examines user/home directory configuration and dotfiles"},
    "D": {"name": "Docs Pipeline", "icon": "📚", "desc": "Deep analysis of all documentation files and their relationships"},
    "C": {"name": "Code Surfaces", "icon": "💻", "desc": "Maps code interfaces, APIs, and public surfaces"},
    "E": {"name": "Execution Plane", "icon": "⚡", "desc": "Analyzes runtime behavior, scripts, and execution paths"},
    "W": {"name": "Workflow Plane", "icon": "🔄", "desc": "Maps CI/CD workflows, GitHub Actions, and automation"},
    "B": {"name": "Boundary Contracts", "icon": "🔒", "desc": "Identifies API contracts, schema boundaries, and interfaces"},
    "G": {"name": "Governance Plane", "icon": "📋", "desc": "Reviews governance rules, policies, and compliance"},
    "Q": {"name": "Quality Assurance", "icon": "✅", "desc": "Cross-checks extraction quality and consistency"},
    "R": {"name": "Arbitration", "icon": "⚖️", "desc": "Reconciles conflicts between different extraction phases"},
    "X": {"name": "Feature Index", "icon": "🗂️", "desc": "Builds searchable feature index from all extractions"},
    "T": {"name": "Task Packets", "icon": "📦", "desc": "Generates task-oriented work packets from findings"},
    "Z": {"name": "Handoff Freeze", "icon": "🧊", "desc": "Creates frozen snapshot for handoff to other systems"},
    "S": {"name": "Synthesis", "icon": "🧬", "desc": "Final synthesis combining all phases into coherent truth"},
}


# ── Authority class metadata ────────────────────────────────────────────────

AUTHORITY_CLASSES: Dict[str, Dict[str, str]] = {
    "canonical": {
        "color": "green",
        "icon": "🟢",
        "desc": "Primary source-of-truth documentation and code",
    },
    "historical": {
        "color": "blue",
        "icon": "🔵",
        "desc": "Archived content that provides historical context",
    },
    "operational": {
        "color": "yellow",
        "icon": "🟡",
        "desc": "Scripts, configs, and operational tooling",
    },
    "audit": {
        "color": "dark_orange",
        "icon": "🟠",
        "desc": "Audit reports, analysis artifacts, and review notes",
    },
    "template": {
        "color": "magenta",
        "icon": "🟣",
        "desc": "Templates, examples, and boilerplate",
    },
    "generated": {
        "color": "white",
        "icon": "⚪",
        "desc": "Auto-generated files (lock files, builds, caches)",
    },
}


# ── Provider colour scheme (matches v5 live UI) ────────────────────────────

PROVIDER_COLORS: Dict[str, str] = {
    "openai": "bold green",
    "anthropic": "bold magenta",
    "gemini": "bold blue",
    "xai": "bold yellow",
    "openrouter": "bold cyan",
    "mistral": "bold orange3",
}
