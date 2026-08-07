#!/usr/bin/env python3
"""Build the normalized agent/persona catalog from Dopemux source files.

Deterministic, idempotent, schema-validating. Reads source files from the
worktree, resolves roles through src/dopemux/roles/catalog.py, and emits a
strict model-free advisory catalog.

Usage:
  python scripts/commandcode_router/build_normalized_catalog.py [--check]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Repo-relative constants — never emit absolute machine paths into the catalog.
SOURCE_MANIFEST_REL = "proof/CCAR-002/SOURCE_MANIFEST.json"
SCHEMA_REL = "schemas/commandcode/normalized_agent_persona_catalog.schema.json"
CATALOG_REL = "config/commandcode/normalized_agent_persona_catalog.yaml"
REPO_MARKERS = (".dopetaskroot", "pyproject.toml")
ROOT_REQUIRED_REL_PATHS = (
    SOURCE_MANIFEST_REL,
    SCHEMA_REL,
    "src/dopemux/roles/catalog.py",
)

GENERATOR_VERSION = "1.0.1"


def _validate_repo_root(root: Path) -> Path:
    """Fail closed if candidate is not a usable dopemux-mvp repository root."""
    root = root.resolve()
    if not root.is_dir():
        raise SystemExit(f"Repository root is not a directory: {root}")
    if not any((root / marker).exists() for marker in REPO_MARKERS):
        raise SystemExit(
            f"Repository root missing markers {REPO_MARKERS}: {root}"
        )
    missing = [rel for rel in ROOT_REQUIRED_REL_PATHS if not (root / rel).exists()]
    if missing:
        raise SystemExit(
            f"Repository root missing required paths {missing}: {root}"
        )
    return root


def resolve_repo_root(
    explicit: Optional[Path] = None,
    start: Optional[Path] = None,
) -> Path:
    """Resolve repository root via explicit path, git toplevel, or marker walk.

    Does not rely solely on a fixed ``Path(__file__).parent×N`` depth, so the
    builder remains portable across differently located worktrees and checkouts.
    """
    if explicit is not None:
        return _validate_repo_root(Path(explicit))

    start_path = (start or Path.cwd()).resolve()

    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(start_path),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if out:
            return _validate_repo_root(Path(out))
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass

    cur = start_path
    for _ in range(32):
        if any((cur / marker).exists() for marker in REPO_MARKERS):
            return _validate_repo_root(cur)
        if cur.parent == cur:
            break
        cur = cur.parent

    # Last resort: script location (validated). Prefer git/markers above.
    script_candidate = Path(__file__).resolve().parent.parent.parent
    try:
        return _validate_repo_root(script_candidate)
    except SystemExit:
        raise SystemExit(
            f"Cannot resolve repository root from start={start_path} "
            f"or script candidate={script_candidate}"
        ) from None


def _paths_for_root(root: Path) -> Dict[str, Path]:
    root = root.resolve()
    personas_dir = root / ".claude" / "personas"
    agents_dir = root / ".claude" / "agents"
    return {
        "root": root,
        "agents_dir": agents_dir,
        "personas_dir": personas_dir,
        "personas_archive": personas_dir / "archive",
        "ref_agents_dir": root / ".github" / "agents",
        "src_personas_dir": root / "src" / "dopemux" / "personas",
        "schema_path": root / SCHEMA_REL,
        "catalog_path": root / CATALOG_REL,
        "proof_dir": root / "proof" / "CCAR-002",
        "source_manifest_path": root / SOURCE_MANIFEST_REL,
        "persona_index_path": personas_dir / "PERSONA_INDEX.md",
        "agents_index_path": agents_dir / "_index.md",
    }


# Module-level paths bound at import for compatibility; re-bound in main().
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_PATHS = _paths_for_root(PROJECT_ROOT)
AGENTS_DIR = _PATHS["agents_dir"]
PERSONAS_DIR = _PATHS["personas_dir"]
PERSONAS_ARCHIVE = _PATHS["personas_archive"]
REF_AGENTS_DIR = _PATHS["ref_agents_dir"]
SRC_PERSONAS_DIR = _PATHS["src_personas_dir"]
SCHEMA_PATH = _PATHS["schema_path"]
CATALOG_PATH = _PATHS["catalog_path"]
PROOF_DIR = _PATHS["proof_dir"]
SOURCE_MANIFEST_PATH = _PATHS["source_manifest_path"]
PERSONA_INDEX_PATH = _PATHS["persona_index_path"]
AGENTS_INDEX_PATH = _PATHS["agents_index_path"]


def bind_repo_root(root: Path) -> Path:
    """Bind module path globals to a validated repository root."""
    global PROJECT_ROOT, AGENTS_DIR, PERSONAS_DIR, PERSONAS_ARCHIVE
    global REF_AGENTS_DIR, SRC_PERSONAS_DIR, SCHEMA_PATH, CATALOG_PATH
    global PROOF_DIR, SOURCE_MANIFEST_PATH, PERSONA_INDEX_PATH, AGENTS_INDEX_PATH
    global _PATHS

    root = _validate_repo_root(root)
    _PATHS = _paths_for_root(root)
    PROJECT_ROOT = _PATHS["root"]
    AGENTS_DIR = _PATHS["agents_dir"]
    PERSONAS_DIR = _PATHS["personas_dir"]
    PERSONAS_ARCHIVE = _PATHS["personas_archive"]
    REF_AGENTS_DIR = _PATHS["ref_agents_dir"]
    SRC_PERSONAS_DIR = _PATHS["src_personas_dir"]
    SCHEMA_PATH = _PATHS["schema_path"]
    CATALOG_PATH = _PATHS["catalog_path"]
    PROOF_DIR = _PATHS["proof_dir"]
    SOURCE_MANIFEST_PATH = _PATHS["source_manifest_path"]
    PERSONA_INDEX_PATH = _PATHS["persona_index_path"]
    AGENTS_INDEX_PATH = _PATHS["agents_index_path"]
    return PROJECT_ROOT

# 9 base agents — resolved through src/dopemux/roles/catalog.py
# Each is an executable lane. Personas map to one or more of these.
BASE_AGENTS: Dict[str, Dict[str, Any]] = {
    "architect": {
        "id": "architect",
        "source_file": ".claude/agents/architect.md",
        "canonical_role": "architect",
        "label": "Architect",
        "description": "Strategic design for system architecture, ADRs, and trade-off analysis.",
        "attention_state": "focused",
        "tools": ["read", "search", "web_search", "web_fetch", "glob", "grep"],
        "mode": "PLAN",
        "may_edit": False,
        "route_eligible": True,
        "stage_lane": "strong",
    },
    "developer": {
        "id": "developer",
        "source_file": ".claude/agents/developer.md",
        "canonical_role": "developer",
        "label": "Developer",
        "description": "Core implementation, debugging, testing, and task-packet execution.",
        "attention_state": "focused",
        "tools": ["read", "edit", "write", "search", "execute", "glob", "grep"],
        "mode": "ACT",
        "may_edit": True,
        "route_eligible": True,
        "stage_lane": "standard",
    },
    "researcher": {
        "id": "researcher",
        "source_file": ".claude/agents/researcher.md",
        "canonical_role": "research",
        "label": "Researcher",
        "description": "Information gathering, technology evaluation, and knowledge synthesis.",
        "attention_state": "focused",
        "tools": ["read", "search", "web_search", "web_fetch", "glob", "grep"],
        "mode": "Both",
        "may_edit": False,
        "route_eligible": True,
        "stage_lane": "cheap_read",
    },
    "reviewer": {
        "id": "reviewer",
        "source_file": None,
        "canonical_role": "reviewer",
        "label": "Reviewer",
        "description": "Code review and decision verification.",
        "attention_state": "focused",
        "tools": ["read", "search", "glob", "grep"],
        "mode": "PLAN",
        "may_edit": False,
        "route_eligible": True,
        "stage_lane": "standard",
    },
    "quickfix": {
        "id": "quickfix",
        "source_file": None,
        "canonical_role": "quickfix",
        "label": "Quickfix",
        "description": "5-15 minute wins, minimal cognitive load.",
        "attention_state": "scattered",
        "tools": ["read", "edit", "write", "search", "execute", "glob", "grep"],
        "mode": "ACT",
        "may_edit": True,
        "route_eligible": True,
        "stage_lane": "standard",
    },
    "debugger": {
        "id": "debugger",
        "source_file": None,
        "canonical_role": "debugger",
        "label": "Debugger",
        "description": "Targeted debugging and incident reproduction.",
        "attention_state": "focused",
        "tools": ["read", "edit", "search", "execute", "glob", "grep"],
        "mode": "ACT",
        "may_edit": True,
        "route_eligible": True,
        "stage_lane": "standard",
    },
    "ops": {
        "id": "ops",
        "source_file": None,
        "canonical_role": "ops",
        "label": "Ops",
        "description": "Operations, deployment, and runbook execution.",
        "attention_state": "focused",
        "tools": ["read", "edit", "search", "execute", "glob"],
        "mode": "ACT",
        "may_edit": True,
        "route_eligible": True,
        "stage_lane": "standard",
    },
    "plan": {
        "id": "plan",
        "source_file": None,
        "canonical_role": "plan",
        "label": "Plan",
        "description": "Strategic planning, architecture, coordination.",
        "attention_state": "focused",
        "tools": ["read", "search", "web_search", "web_fetch", "glob", "grep"],
        "mode": "PLAN",
        "may_edit": False,
        "route_eligible": True,
        "stage_lane": "strong",
    },
    "act": {
        "id": "act",
        "source_file": None,
        "canonical_role": "act",
        "label": "Act",
        "description": "Generic implementation and refactoring workflows.",
        "attention_state": "focused",
        "tools": ["read", "edit", "write", "search", "execute", "glob", "grep"],
        "mode": "ACT",
        "may_edit": True,
        "route_eligible": True,
        "stage_lane": "standard",
    },
}

# Persona -> base agent mapping. Each active persona maps to 1+ base agents.
# Route_eligible is false for all advisory personas per invariant.
PERSONA_DEFINITIONS: Dict[str, Dict[str, Any]] = {}

def _register(
    persona_id: str,
    label: str,
    description: str,
    base_agents: List[str],
    source_file: str,
    naming_convention: str,
    domain: str = "",
    alias_group: Optional[str] = None,
    route_eligible: bool = False,
    warnings: Optional[List[str]] = None,
):
    PERSONA_DEFINITIONS[persona_id] = {
        "id": persona_id,
        "alias_group": alias_group,
        "base_agents": base_agents,
        "label": label,
        "description": description,
        "route_eligible": route_eligible,
        "may_change_tools": False,
        "may_select_model": False,
        "may_grant_write_authority": False,
        "source_file": source_file,
        "domain": domain,
        "naming_convention": naming_convention,
        "warnings": warnings or [],
    }


# --- Persona registrations ---

# Curated agent personas (from agents/_index.md)
_register("project-manager", "Project Manager",
    "Coordination, sprint tracking, task-packet flow, cross-surface progress visibility.",
    ["plan"], ".claude/agents/project-manager.md", "agent.md",
    domain="coordination")

# Architecture domain
_register("system-architect-dopemux", "System Architect",
    "High-level system design with Dopemux integration.",
    ["architect"], ".claude/personas/system-architect-dopemux.md", "dopemux.md",
    domain="architecture")
_register("se-system-architecture-reviewer", "SE: Architect (Review)",
    "System architecture review with Well-Architected frameworks.",
    ["architect", "reviewer"], ".claude/personas/se-system-architecture-reviewer.agent.md", "agent.md",
    domain="architecture")
_register("backend-architect-dopemux", "Backend Architect",
    "APIs, databases, scalability, reliability with Dopemux integration.",
    ["architect", "developer"], ".claude/personas/backend-architect-dopemux.md", "dopemux.md",
    domain="architecture")
_register("frontend-architect-dopemux", "Frontend Architect",
    "UI/UX, React, accessibility, performance with Dopemux integration.",
    ["architect", "developer"], ".claude/personas/frontend-architect-dopemux.md", "dopemux.md",
    domain="architecture")

# DevOps domain
_register("devops-architect-dopemux", "DevOps Architect",
    "Infrastructure, CI/CD, deployment, monitoring with Dopemux integration.",
    ["architect", "ops"], ".claude/personas/devops-architect-dopemux.md", "dopemux.md",
    domain="devops")
_register("devops-expert", "DevOps Expert",
    "Hands-on infrastructure and deployment work.",
    ["ops", "developer"], ".claude/personas/devops-expert.agent.md", "agent.md",
    domain="devops")
_register("se-gitops-ci-specialist", "SE: GitOps CI Specialist",
    "CI/CD pipeline design and GitHub Actions expertise.",
    ["ops", "developer"], ".claude/personas/se-gitops-ci-specialist.agent.md", "agent.md",
    domain="devops")
_register("github-actions-expert", "GitHub Actions Expert",
    "GitHub Actions workflow authoring and debugging.",
    ["ops", "developer"], ".claude/personas/github-actions-expert.agent.md", "agent.md",
    domain="devops")

# Security domain
_register("security-engineer-dopemux", "Security Engineer",
    "Security design and implementation with Dopemux integration.",
    ["architect", "developer", "reviewer"], ".claude/personas/security-engineer-dopemux.md", "dopemux.md",
    domain="security")
_register("se-security-reviewer", "SE: Security (Review)",
    "Security-focused code review with OWASP, Zero Trust, LLM security.",
    ["reviewer", "architect"], ".claude/personas/se-security-reviewer.agent.md", "agent.md",
    domain="security")
_register("wg-code-sentinel", "WG Code Sentinel",
    "Security review identifying vulnerabilities and attack vectors.",
    ["reviewer"], ".claude/personas/wg-code-sentinel.agent.md", "agent.md",
    domain="security")

# Quality / performance domain
_register("performance-engineer-dopemux", "Performance Engineer",
    "Performance optimization with Dopemux integration.",
    ["architect", "developer"], ".claude/personas/performance-engineer-dopemux.md", "dopemux.md",
    domain="performance")
_register("quality-engineer-dopemux", "Quality Engineer",
    "QA and test strategy with Dopemux integration.",
    ["reviewer", "developer"], ".claude/personas/quality-engineer-dopemux.md", "dopemux.md",
    domain="quality")

# Implementation / engineering domain
_register("principal-software-engineer", "Principal Software Engineer",
    "Senior engineering judgment, clean code, design patterns.",
    ["architect", "developer", "reviewer"], ".claude/personas/principal-software-engineer.agent.md", "agent.md",
    domain="engineering")
_register("janitor", "Universal Janitor",
    "Code cleanup, simplification, tech debt remediation.",
    ["developer", "quickfix"], ".claude/personas/janitor.agent.md", "agent.md",
    domain="engineering")
_register("wg-code-alchemist", "WG Code Alchemist",
    "Clean Code transformation with SOLID principles.",
    ["developer"], ".claude/personas/wg-code-alchemist.agent.md", "agent.md",
    domain="engineering")
_register("modernization", "Modernization",
    "Code modernization and migration strategies.",
    ["architect", "developer"], ".claude/personas/modernization.agent.md", "agent.md",
    domain="engineering")
_register("tech-debt-remediation-plan", "Tech Debt Remediation Plan",
    "Technical debt analysis and remediation planning.",
    ["architect", "developer"], ".claude/personas/tech-debt-remediation-plan.agent.md", "agent.md",
    domain="engineering")
_register("python-expert-dopemux", "Python Expert",
    "Python development with Dopemux integration.",
    ["developer"], ".claude/personas/python-expert-dopemux.md", "dopemux.md",
    domain="engineering")
_register("python-mcp-expert", "Python MCP Server Expert",
    "MCP server development in Python with FastMCP.",
    ["developer"], ".claude/personas/python-mcp-expert.agent.md", "agent.md",
    domain="engineering")
_register("refine-issue", "Refine Issue",
    "Issue triage and refinement.",
    ["plan", "developer"], ".claude/personas/refine-issue.agent.md", "agent.md",
    domain="engineering")

# Documentation domain
_register("adr-generator", "ADR Generator",
    "Architectural Decision Record creation.",
    ["architect", "plan"], ".claude/personas/adr-generator.agent.md", "agent.md",
    domain="documentation")
_register("specification", "Specification",
    "Specification document generation and updates.",
    ["plan", "architect"], ".claude/personas/specification.agent.md", "agent.md",
    domain="documentation")
_register("prd", "PRD Author",
    "Product Requirements Document authoring.",
    ["plan"], ".claude/personas/prd.agent.md", "agent.md",
    domain="documentation")
_register("technical-writer-dopemux", "Technical Writer",
    "Technical documentation with Dopemux integration.",
    ["researcher"], ".claude/personas/technical-writer-dopemux.md", "dopemux.md",
    domain="documentation")
_register("se-technical-writer", "SE: Technical Writer",
    "Technical writing and documentation standards.",
    ["researcher"], ".claude/personas/se-technical-writer.agent.md", "agent.md",
    domain="documentation")
_register("implementation-plan", "Implementation Plan",
    "Feature implementation planning.",
    ["plan", "architect"], ".claude/personas/implementation-plan.agent.md", "agent.md",
    domain="documentation")

# Workflow / orchestration domain
_register("workflow-manager", "Workflow Manager",
    "Phase-gated workflow orchestration and validation.",
    ["plan", "reviewer"], ".claude/personas/workflow-manager.agent.md", "agent.md",
    domain="workflow")
_register("workflow-executor", "Workflow Executor",
    "Isolated workflow task implementation.",
    ["developer", "act"], ".claude/personas/workflow-executor.agent.md", "agent.md",
    domain="workflow")
_register("task-planner", "Task Planner",
    "Task breakdown and planning.",
    ["plan"], ".claude/personas/task-planner.agent.md", "agent.md",
    domain="workflow")
_register("task-researcher", "Task Researcher",
    "Focused task research and investigation.",
    ["researcher"], ".claude/personas/task-researcher.agent.md", "agent.md",
    domain="workflow")

# Advisory / mentoring domain
_register("critical-thinking", "Critical Thinking",
    "Red-team analysis and critical evaluation.",
    ["architect", "reviewer"], ".claude/personas/critical-thinking.agent.md", "agent.md",
    domain="advisory")
_register("devils-advocate", "Devil's Advocate",
    "Challenge assumptions and stress-test proposals.",
    ["architect", "reviewer"], ".claude/personas/devils-advocate.agent.md", "agent.md",
    domain="advisory")
_register("socratic-mentor-dopemux", "Socratic Mentor",
    "Teaching through strategic questioning with Dopemux integration.",
    ["architect"], ".claude/personas/socratic-mentor-dopemux.md", "dopemux.md",
    domain="advisory")
_register("learning-guide-dopemux", "Learning Guide",
    "Walk-through teaching with Dopemux integration.",
    ["researcher"], ".claude/personas/learning-guide-dopemux.md", "dopemux.md",
    domain="advisory")
_register("prompt-builder", "Prompt Builder",
    "Prompt template construction and optimization.",
    ["plan"], ".claude/personas/prompt-builder.agent.md", "agent.md",
    domain="advisory")
_register("prompt-engineer", "Prompt Engineer",
    "Prompt refinement and evaluation.",
    ["plan", "researcher"], ".claude/personas/prompt-engineer.agent.md", "agent.md",
    domain="advisory")
_register("search-ai-optimization-expert", "Search AI Optimization Expert",
    "Web/SEO research and optimization.",
    ["researcher"], ".claude/personas/search-ai-optimization-expert.agent.md", "agent.md",
    domain="advisory")

# Product / UX domain
_register("se-product-manager-advisor", "SE: Product Manager Advisor",
    "Product strategy and roadmap guidance.",
    ["plan", "architect"], ".claude/personas/se-product-manager-advisor.agent.md", "agent.md",
    domain="product")
_register("se-ux-ui-designer", "SE: UX/UI Designer",
    "UX/UI design review and guidance.",
    ["architect"], ".claude/personas/se-ux-ui-designer.agent.md", "agent.md",
    domain="product")

# General / fallback
_register("general-purpose-dopemux", "General Purpose",
    "Multi-domain tasks with Dopemux integration. NOT an automatic write fallback.",
    ["architect", "developer", "researcher"],
    ".claude/personas/general-purpose-dopemux.md", "dopemux.md",
    domain="general",
    warnings=["general-purpose-dopemux is never an automatic write fallback per invariant."])
_register("statusline-setup-dopemux", "Statusline Setup",
    "Statusline configuration with Dopemux integration.",
    ["ops"], ".claude/personas/statusline-setup-dopemux.md", "dopemux.md",
    domain="general")


def _validate_role_resolution() -> None:
    """Verify every base agent resolves through src/dopemux/roles/catalog.py."""
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    try:
        from dopemux.roles.catalog import resolve_role, RoleNotFoundError
    except ImportError as e:
        print(f"WARNING: Cannot import role catalog: {e}", file=sys.stderr)
        print("Role resolution validation SKIPPED.", file=sys.stderr)
        return

    for agent_id, agent in BASE_AGENTS.items():
        role = agent["canonical_role"]
        try:
            spec = resolve_role(role)
            assert spec.key == role, f"Role {role} resolved to {spec.key}"
        except RoleNotFoundError as e:
            print(f"ERROR: Base agent {agent_id} role {role} not found: {e}", file=sys.stderr)
            sys.exit(1)
    print(
        f"PASS: All {len(BASE_AGENTS)} base agents resolve through roles/catalog.py",
        file=sys.stderr,
    )


def _verify_persona_coverage() -> List[str]:
    """Check every active persona is represented exactly once."""
    active_sources = set()
    for p in PERSONA_DEFINITIONS.values():
        active_sources.add(p["source_file"])

    # List all active persona files (non-archive)
    actual_files = set()
    for fpath in PERSONAS_DIR.glob("*.md"):
        if fpath.name == "PERSONA_INDEX.md":
            continue
        actual_files.add(f".claude/personas/{fpath.name}")
    for fpath in PERSONAS_DIR.glob("*.agent.md"):
        actual_files.add(f".claude/personas/{fpath.name}")

    # Also count curated agents
    actual_files.add(".claude/agents/project-manager.md")

    missing = actual_files - active_sources
    extra = active_sources - actual_files

    warnings = []
    if missing:
        warnings.append(f"UNCOVERED_PERSONAS: {sorted(missing)}")
    if extra:
        warnings.append(f"EXTRA_PERSONAS: {sorted(extra)}")
    return warnings


def _load_source_manifest() -> Dict[str, Any]:
    """Load the immutable source manifest."""
    with open(SOURCE_MANIFEST_PATH, "r") as f:
        return json.load(f)


def _verify_source_hashes(manifest: Dict[str, Any]) -> List[str]:
    """Verify every source SHA-256 in the manifest matches current bytes."""
    warnings = []
    for section in ["active_agents", "active_personas"]:
        for key, info in manifest.get(section, {}).items():
            fpath = PROJECT_ROOT / info["path"]
            if not fpath.exists():
                warnings.append(f"MISSING_SOURCE: {info['path']}")
                continue
            current_hash = hashlib.sha256(fpath.read_bytes()).hexdigest()
            if current_hash != info["sha256"]:
                warnings.append(
                    f"HASH_MISMATCH: {info['path']} "
                    f"expected={info['sha256'][:8]} actual={current_hash[:8]}"
                )
    return warnings


def build_catalog(generated_at: Optional[str] = None) -> Dict[str, Any]:
    """Build the complete normalized catalog.

    ``meta.source_manifest`` is always the stable repo-relative path
    ``proof/CCAR-002/SOURCE_MANIFEST.json`` — never an absolute worktree path.
    """
    manifest = _load_source_manifest()
    ts = generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    catalog: Dict[str, Any] = {
        "meta": {
            "packet_id": "CCAR-002",
            "generated_at": ts,
            "source_manifest": SOURCE_MANIFEST_REL,
            "source_commit": manifest["base_commit"],
            "base_agent_count": len(BASE_AGENTS),
            "persona_count": len(PERSONA_DEFINITIONS),
            "model_free": True,
            "generator_version": GENERATOR_VERSION,
        },
        "base_agents": BASE_AGENTS,
        "personas": PERSONA_DEFINITIONS,
    }

    return catalog


def validate_catalog(catalog: Dict[str, Any]) -> List[str]:
    """Validate catalog invariants. Returns list of violations."""
    violations = []

    # Check base agent count
    if len(catalog["base_agents"]) != 9:
        violations.append(f"Expected 9 base agents, got {len(catalog['base_agents'])}")

    # No model IDs in catalog
    catalog_str = json.dumps(catalog, sort_keys=True)
    model_patterns = [
        r'claude[\s-]?(sonnet|opus|haiku)',
        r'gpt[\s-]?\d',
        r'gemini[\s-]?\d',
        r'grok[\s-]?\d',
    ]
    for pattern in model_patterns:
        if re.search(pattern, catalog_str, re.IGNORECASE):
            violations.append(f"Model ID pattern found: {pattern}")

    # Authority prohibitions
    for persona_id, persona in catalog["personas"].items():
        if persona["may_change_tools"]:
            violations.append(f"Persona {persona_id}: may_change_tools must be false")
        if persona["may_select_model"]:
            violations.append(f"Persona {persona_id}: may_select_model must be false")
        if persona["may_grant_write_authority"]:
            violations.append(f"Persona {persona_id}: may_grant_write_authority must be false")

    # No duplicate IDs
    persona_ids = list(catalog["personas"].keys())
    if len(persona_ids) != len(set(persona_ids)):
        violations.append("Duplicate persona IDs found")

    # general-purpose-dopemux routing check
    gp = catalog["personas"].get("general-purpose-dopemux", {})
    if gp.get("route_eligible"):
        violations.append("general-purpose-dopemux must not be route_eligible")

    return violations


def _scan_model_ids(text: str) -> List[str]:
    """Scan for model ID patterns in source text. Used for warnings only."""
    patterns = [
        r'claude[\s-]?(?:sonnet|opus|haiku)[\s-]?\d[\d.]*',
        r'gpt[\s-]?\d[\d.]*[-\w]*',
        r'gemini[\s-]?\d[\d.]*[-\w]*',
        r'grok[\s-]?\d[\d.]*[-\w]*',
    ]
    found = []
    for pattern in patterns:
        found.extend(m.group(0) for m in re.finditer(pattern, text, re.IGNORECASE))
    return found


def _generate_warnings(catalog: Dict[str, Any]) -> List[str]:
    """Generate advisory warnings about source content."""
    warnings = []

    # Scan source files for model references (advisory only, catalog is model-free)
    for persona_id, persona in catalog["personas"].items():
        src = persona.get("source_file", "")
        if src and PROJECT_ROOT.joinpath(src).exists():
            text = PROJECT_ROOT.joinpath(src).read_text(errors="replace")
            model_refs = _scan_model_ids(text[:500])  # check frontmatter area
            if model_refs:
                warnings.append(
                    f"Source {src} contains model references: {model_refs}. "
                    f"Catalog record for {persona_id} is model-free."
                )

    # Coverage warnings
    coverage_warnings = _verify_persona_coverage()
    warnings.extend(coverage_warnings)

    return warnings


def catalog_to_yaml(catalog: Dict[str, Any]) -> str:
    """Serialize catalog to deterministic YAML text."""
    return yaml.dump(catalog, sort_keys=False, allow_unicode=True, width=200)


def normalize_generated_at(yaml_text: str) -> str:
    """Normalize generated_at timestamps for cross-run / cross-worktree compare."""
    return re.sub(
        r'generated_at:\s*["\']?\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z["\']?',
        "generated_at: NORMALIZED",
        yaml_text,
    )


def assert_no_absolute_source_manifest(catalog: Dict[str, Any]) -> None:
    """Fail closed if meta.source_manifest is not the stable repo-relative path."""
    sm = catalog.get("meta", {}).get("source_manifest", "")
    if sm != SOURCE_MANIFEST_REL:
        raise SystemExit(
            f"INVARIANT_VIOLATION: source_manifest must be "
            f"{SOURCE_MANIFEST_REL!r}, got {sm!r}"
        )
    if sm.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", sm):
        raise SystemExit(
            f"INVARIANT_VIOLATION: absolute source_manifest forbidden: {sm!r}"
        )


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Build normalized agent/persona catalog")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit nonzero if catalog differs from committed version",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Explicit repository root (validated). Overrides git/marker discovery.",
    )
    parser.add_argument(
        "--generated-at",
        default=None,
        help="Optional fixed UTC timestamp (YYYY-MM-DDTHH:MM:SSZ) for deterministic builds",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Write catalog YAML to stdout instead of the catalog file",
    )
    args = parser.parse_args(argv)

    root = resolve_repo_root(explicit=args.repo_root, start=Path.cwd())
    bind_repo_root(root)
    os.chdir(PROJECT_ROOT)

    # Status noise always goes to stderr so --stdout stays pure YAML.
    def status(msg: str) -> None:
        print(msg, file=sys.stderr)

    # Verify role resolution
    _validate_role_resolution()

    # Verify source hashes
    manifest = _load_source_manifest()
    hash_warnings = _verify_source_hashes(manifest)
    if hash_warnings:
        for w in hash_warnings:
            print(f"HASH_VIOLATION: {w}", file=sys.stderr)
        sys.exit(1)
    status(f"PASS: Source hash verification ({len(manifest['source_counts'])} categories)")

    # Build catalog
    catalog = build_catalog(generated_at=args.generated_at)
    assert_no_absolute_source_manifest(catalog)

    # Validate catalog
    violations = validate_catalog(catalog)
    if violations:
        for v in violations:
            print(f"INVARIANT_VIOLATION: {v}", file=sys.stderr)
        sys.exit(1)
    status("PASS: Catalog invariant validation")

    # Generate warnings
    warnings = _generate_warnings(catalog)
    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)

    # Schema validation
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)

    try:
        import jsonschema
        jsonschema.validate(catalog, schema)
        status("PASS: Schema validation")
    except ImportError:
        print("WARNING: jsonschema not installed, skipping schema validation", file=sys.stderr)
    except jsonschema.ValidationError as e:
        print(f"SCHEMA_VIOLATION: {e.message}", file=sys.stderr)
        sys.exit(1)

    # Serialize to YAML
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    yaml_str = catalog_to_yaml(catalog)

    if args.check:
        if not CATALOG_PATH.exists():
            print("CHECK_FAILED: Catalog file does not exist", file=sys.stderr)
            sys.exit(1)
        current = CATALOG_PATH.read_text()
        norm_current = normalize_generated_at(current)
        norm_new = normalize_generated_at(yaml_str)
        if norm_current != norm_new:
            print("CHECK_FAILED: Catalog differs from committed version", file=sys.stderr)
            sys.exit(1)
        status("CHECK_PASS: Catalog matches committed version")
    elif args.stdout:
        sys.stdout.write(yaml_str)
    else:
        CATALOG_PATH.write_text(yaml_str)
        status(f"Catalog written to {CATALOG_PATH.relative_to(PROJECT_ROOT)}")

    status(
        f"Summary: {len(catalog['base_agents'])} base agents, "
        f"{len(catalog['personas'])} personas; root={PROJECT_ROOT}"
    )


if __name__ == "__main__":
    main()
