from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from .fingerprint import deterministic_generated_at

ARCHETYPES_FILENAME = "ARCHETYPES.json"


@dataclass(frozen=True)
class ArchetypeThresholds:
    monorepo_score: float = 2.0
    event_score: float = 1.5
    db_score: float = 1.5
    plugin_score: float = 1.0


def _glob_count(root: Path, pattern: str, max_hits: int = 10_000) -> int:
    count = 0
    for _ in root.glob(pattern):
        count += 1
        if count >= max_hits:
            break
    return count


def _has_any(root: Path, patterns: List[str]) -> bool:
    return any(_glob_count(root, pattern, max_hits=1) > 0 for pattern in patterns)


def classify_archetypes(
    *,
    root: Path,
    run_id: str,
    repo_fingerprint: Dict[str, Any],
    build_surface: Dict[str, Any],
    dependency_hints: Dict[str, Any],
    thresholds: ArchetypeThresholds | None = None,
) -> Dict[str, Any]:
    t = thresholds or ArchetypeThresholds()
    top_clusters = repo_fingerprint.get("path_clusters")
    if not isinstance(top_clusters, list):
        top_clusters = []

    cluster_names = {str(row.get("path", "")) for row in top_clusters if isinstance(row, dict)}
    total_files = int(((repo_fingerprint.get("totals") or {}).get("total_files", 0)) or 0)
    build_systems = set(str(x) for x in build_surface.get("build_systems", []) if isinstance(x, str))

    services_dir_count = _glob_count(root, "services/*")
    dockerfile_count = _glob_count(root, "**/Dockerfile*")
    compose_count = len(build_surface.get("dockerfiles", [])) if isinstance(build_surface.get("dockerfiles"), list) else 0

    monorepo_score = 0.0
    monorepo_reasons: List[str] = []
    if services_dir_count >= 3:
        monorepo_score += 1.0
        monorepo_reasons.append("services_root_count>=3")
    if len(build_systems) >= 2:
        monorepo_score += 1.0
        monorepo_reasons.append("multiple_build_systems")
    if dockerfile_count >= 3 or compose_count >= 3:
        monorepo_score += 0.5
        monorepo_reasons.append("many_container_surfaces")
    if total_files >= 1200:
        monorepo_score += 0.5
        monorepo_reasons.append("large_file_count")

    event_taxonomy_present = _has_any(
        root,
        [
            "**/*event*taxonomy*.json",
            "**/*event*schema*.json",
            "**/*event*catalog*.md",
            "**/*eventbus*.py",
            "**/*event_bus*.py",
            "**/*producer*.py",
            "**/*consumer*.py",
        ],
    )
    event_score = 1.0 if event_taxonomy_present else 0.0
    if _has_any(root, ["**/*eventbus*", "**/*event_bus*"]):
        event_score += 0.5

    db_score = 0.0
    if _has_any(root, ["**/migrations/**", "**/*schema*.sql", "**/alembic/**"]):
        db_score += 1.0
    if _has_any(root, ["**/*orm*.py", "**/*repository*.py", "**/*dao*.py"]):
        db_score += 0.5

    plugin_score = 0.0
    if _has_any(root, ["plugins/**", "**/*plugin*.py", "**/*plugin*.ts"]):
        plugin_score += 1.0

    docs_count = _glob_count(root, "docs/**/*.md")
    code_count = 0
    filetype_counts = repo_fingerprint.get("filetype_counts") if isinstance(repo_fingerprint.get("filetype_counts"), dict) else {}
    for ext in [".py", ".ts", ".js", ".go", ".rs", ".java", ".kt"]:
        code_count += int(filetype_counts.get(ext, 0))

    docs_first = docs_count > 0 and code_count > 0 and docs_count >= max(200, code_count * 2)
    single_service = not (monorepo_score >= t.monorepo_score) and services_dir_count <= 2 and total_files < 1500

    node_workspaces = ((dependency_hints.get("workspace_hints") or {}).get("node_workspaces"))
    if not isinstance(node_workspaces, list):
        node_workspaces = []

    payload = {
        "version": "ARCHETYPES_V1",
        "generated_at": deterministic_generated_at(run_id),
        "run_id": run_id,
        "repo_root": str(root.resolve()),
        "archetypes": {
            "monorepo": {
                "value": monorepo_score >= t.monorepo_score,
                "score": round(monorepo_score, 3),
                "reasons": sorted(monorepo_reasons),
            },
            "microservices": {
                "value": services_dir_count >= 3,
                "score": float(services_dir_count),
            },
            "single_service_app": {
                "value": single_service,
                "score": 1.0 if single_service else 0.0,
            },
            "event_driven_likely": {
                "value": event_score >= t.event_score,
                "score": round(event_score, 3),
            },
            "db_heavy": {
                "value": db_score >= t.db_score,
                "score": round(db_score, 3),
            },
            "plugin_system_likely": {
                "value": plugin_score >= t.plugin_score,
                "score": round(plugin_score, 3),
            },
            "node_typescript_monorepo": {
                "value": len(node_workspaces) > 1 and ("node_package_json" in build_systems),
                "score": float(len(node_workspaces)),
            },
            "docs_first_spec_driven": {
                "value": docs_first,
                "score": float(docs_count),
            },
        },
        "surface_areas": {
            "cluster_names": sorted(cluster_names),
            "services_root_count": services_dir_count,
            "dockerfile_count": dockerfile_count,
            "compose_surface_count": compose_count,
            "docs_file_count": docs_count,
            "code_file_count": code_count,
        },
        "contracts_present": {
            "event_taxonomy": bool(event_taxonomy_present),
            "db_schema": bool(_has_any(root, ["**/*schema*.sql", "**/migrations/**", "**/alembic/**"])),
            "api_specs": bool(_has_any(root, ["**/*openapi*.yml", "**/*openapi*.yaml", "**/*swagger*.json"])),
            "adrs": bool(_has_any(root, ["docs/90-adr/*.md", "docs/**/ADR-*.md"])),
        },
    }

    return payload
