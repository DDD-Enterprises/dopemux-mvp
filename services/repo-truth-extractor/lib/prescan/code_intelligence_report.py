"""Central code intelligence orchestrator.

Runs all code analysis passes and produces a unified
``code_intelligence_report.json`` artifact.
"""

from __future__ import annotations

import datetime as dt
import logging
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .code_prescan import CodePrescan
from .dependency_graph import DependencyGraph
from .models import FileEntry

logger = logging.getLogger(__name__)

# Files exempt from dead-code detection
KNOWN_DYNAMIC_PATTERNS = {
    "management/commands/",
    "migrations/",
    "conftest.py",
    "plugins/",
    "templatetags/",
    "fixtures/",
}


@dataclass
class HotspotEntry:
    rel_path: str
    churn_score: float
    complexity_score: float
    hotspot_score: float
    contributors: int
    last_modified: str


@dataclass
class TestMapping:
    source_path: str
    test_path: Optional[str]
    confidence: float
    method: str  # "import_analysis" | "naming_convention" | "git_cochange"


@dataclass
class OrphanEntry:
    rel_path: str
    reason: str  # "unreachable" | "no_importers" | "no_tests"
    confidence: float
    recommendation: str  # "investigate" | "deprioritize" | "needs_test"


class CodeIntelligenceBuilder:
    """Orchestrates all code analysis into a single report artifact."""

    def __init__(
        self,
        code_prescan: CodePrescan,
        dep_graph: DependencyGraph,
        entries: List[FileEntry],
        manifest: List[dict],
    ):
        self.code_prescan = code_prescan
        self.dep_graph = dep_graph
        self.entries = entries
        self.manifest = manifest
        self._entry_map = {e.rel_path: e for e in entries}
        self._code_entries = [
            e for e in entries
            if e.include and not e.is_ghost
            and e.extension.lstrip(".") in ("py", "js", "ts", "tsx", "jsx")
        ]

    def build(self, repo_root: Path) -> Dict[str, Any]:
        """Run all passes and produce the report."""
        git_depth = _detect_git_depth(repo_root)
        use_churn = git_depth == "full"

        # 1. Extract signatures
        signature_index: Dict[str, list] = {}
        for entry in self._code_entries:
            sigs = self.code_prescan.extract_signatures(entry, repo_root)
            if sigs:
                signature_index[entry.rel_path] = sigs

        # 2. PageRank
        pagerank = {}
        if len(self.dep_graph.nodes) >= 5:
            pagerank = self.dep_graph.compute_pagerank()

        # 3. Entry points
        entry_points = self.dep_graph.find_entry_points(self.manifest)

        # 4. Reachability
        reachability: Dict[str, int] = {}
        if entry_points and len(self.dep_graph.nodes) >= 5:
            reachability = self.dep_graph.compute_reachability(entry_points)
        else:
            logger.warning(
                "Fewer than 5 graph nodes or no entry points — "
                "skipping dead code analysis"
            )

        # 5. Orphans (advisory only, never auto-skip)
        orphans = self._identify_orphans(reachability, entry_points) if reachability else []

        # 6. Hotspot matrix
        hotspots = self._build_hotspot_matrix(use_churn)

        # 7. Test mappings
        test_mappings = self._map_tests()

        # 8. Hub files
        hub_files = self.dep_graph.find_hub_files(top_n=15)
        # Add pagerank to hub entries
        for h in hub_files:
            h["pagerank"] = round(pagerank.get(h["rel_path"], 0.0), 6)

        # 9. Composite priority
        processing_order = self._compute_composite_priority(
            pagerank, reachability, hotspots, entry_points, use_churn
        )

        # Summary
        total_code = len(self._code_entries)
        mapped_tests = sum(1 for t in test_mappings if t.test_path)
        avg_complexity = 0.0
        if self._code_entries:
            avg_complexity = round(
                sum(e.complexity_score for e in self._code_entries) / total_code, 2
            )

        return {
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "repo_root": str(repo_root),
            "git_depth": git_depth,
            "summary": {
                "total_code_files": total_code,
                "entry_points": len(entry_points),
                "hub_files": len(hub_files),
                "hotspots": len([h for h in hotspots if h.hotspot_score >= 0.5]),
                "orphan_candidates": len(orphans),
                "test_coverage_mapped": mapped_tests,
                "avg_complexity": avg_complexity,
            },
            "signature_index": {
                k: v for k, v in list(signature_index.items())[:200]
            },
            "pagerank_scores": {
                k: round(v, 6) for k, v in sorted(
                    pagerank.items(), key=lambda x: x[1], reverse=True
                )[:100]
            },
            "entry_points": sorted(entry_points),
            "hotspots": [asdict(h) for h in hotspots[:50]],
            "orphans": [asdict(o) for o in orphans[:100]],
            "test_mappings": [asdict(t) for t in test_mappings[:200]],
            "hub_files": hub_files,
            "processing_order": processing_order[:100],
        }

    def _build_hotspot_matrix(self, use_churn: bool) -> List[HotspotEntry]:
        """churn × cognitive_complexity for each code file."""
        hotspots: List[HotspotEntry] = []

        for entry in self._code_entries:
            churn = entry.churn_score if use_churn else 0.0
            complexity = entry.complexity_score

            if use_churn:
                raw_score = churn * complexity
            else:
                raw_score = complexity  # complexity-only fallback

            hotspots.append(HotspotEntry(
                rel_path=entry.rel_path,
                churn_score=round(churn, 3),
                complexity_score=round(complexity, 3),
                hotspot_score=round(raw_score, 3),
                contributors=entry.contributor_count,
                last_modified=entry.last_commit_date or "",
            ))

        # Normalize: top 5% get ≥ 0.8
        hotspots.sort(key=lambda h: h.hotspot_score, reverse=True)
        if hotspots:
            max_score = hotspots[0].hotspot_score
            if max_score > 0:
                for h in hotspots:
                    h.hotspot_score = round(h.hotspot_score / max_score, 3)

        return hotspots

    def _map_tests(self) -> List[TestMapping]:
        """Multi-signal test mapping."""
        mappings: List[TestMapping] = []
        test_files = {
            e.rel_path for e in self._code_entries
            if _is_test_file(e.rel_path)
        }
        source_files = {
            e.rel_path for e in self._code_entries
            if not _is_test_file(e.rel_path)
        }

        for source in sorted(source_files):
            best_test: Optional[str] = None
            best_confidence = 0.0
            best_method = "naming_convention"

            # Signal 1: Naming convention (weight 0.5)
            p = Path(source)
            candidates = [
                str(p.parent / f"test_{p.name}"),
                str(Path("tests") / f"test_{p.name}"),
                str(Path("tests") / p.parent / f"test_{p.name}"),
            ]
            for cand in candidates:
                if cand in test_files:
                    conf = 0.5
                    if conf > best_confidence:
                        best_test = cand
                        best_confidence = conf
                        best_method = "naming_convention"

            # Signal 2: Import analysis (weight 0.4)
            source_module = str(Path(source).with_suffix("")).replace("/", ".")
            for tf in test_files:
                # Check if the test file imports the source module
                entry = self._entry_map.get(tf)
                if entry and entry.import_count > 0:
                    # Heuristic: if test file name contains source module name
                    source_stem = Path(source).stem
                    test_stem = Path(tf).stem
                    if source_stem in test_stem:
                        conf = 0.4
                        if conf > best_confidence:
                            best_test = tf
                            best_confidence = conf
                            best_method = "import_analysis"

            mappings.append(TestMapping(
                source_path=source,
                test_path=best_test,
                confidence=round(best_confidence, 2),
                method=best_method,
            ))

        return mappings

    def _compute_composite_priority(
        self,
        pagerank: Dict[str, float],
        reachability: Dict[str, int],
        hotspots: List[HotspotEntry],
        entry_points: Set[str],
        use_churn: bool,
    ) -> List[Dict[str, Any]]:
        """Composite extraction priority.

        score = pagerank * 0.4 + entry_proximity * 0.3 + hotspot_score * 0.3
        When churn unavailable: pagerank * 0.55 + entry_proximity * 0.45
        """
        hotspot_map = {h.rel_path: h.hotspot_score for h in hotspots}
        max_distance = max(reachability.values()) if reachability else 1

        results: List[Dict[str, Any]] = []
        for entry in self._code_entries:
            rp = entry.rel_path
            pr = pagerank.get(rp, 0.0)
            # Normalize pagerank to 0-1
            max_pr = max(pagerank.values()) if pagerank else 1.0
            pr_norm = pr / max_pr if max_pr > 0 else 0.0

            # Entry proximity: 1.0 for entry points, decreasing by distance
            if rp in entry_points:
                proximity = 1.0
            elif rp in reachability:
                proximity = max(0.0, 1.0 - (reachability[rp] / (max_distance + 1)))
            else:
                proximity = 0.5 if not reachability else 0.0

            hs = hotspot_map.get(rp, 0.0)

            if use_churn:
                score = pr_norm * 0.4 + proximity * 0.3 + hs * 0.3
            else:
                score = pr_norm * 0.55 + proximity * 0.45

            results.append({
                "rel_path": rp,
                "score": round(score, 4),
                "pagerank": round(pr_norm, 4),
                "proximity": round(proximity, 4),
                "hotspot": round(hs, 4),
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def _identify_orphans(
        self,
        reachability: Dict[str, int],
        entry_points: Set[str],
    ) -> List[OrphanEntry]:
        """Dead code candidates with confidence gating.

        Advisory only — never auto-skip.
        """
        orphans: List[OrphanEntry] = []

        for entry in self._code_entries:
            rp = entry.rel_path

            # Skip known dynamic patterns
            if any(pat in rp for pat in KNOWN_DYNAMIC_PATTERNS):
                continue
            # Skip test files, config files, __init__.py
            if _is_test_file(rp):
                continue
            if Path(rp).name in ("__init__.py", "conftest.py"):
                continue
            if rp in entry_points:
                continue

            in_degree = self.dep_graph.get_in_degree(rp)
            is_reachable = rp in reachability

            if not is_reachable and in_degree == 0:
                orphans.append(OrphanEntry(
                    rel_path=rp,
                    reason="unreachable",
                    confidence=0.9,
                    recommendation="deprioritize",
                ))
            elif not is_reachable and in_degree > 0:
                orphans.append(OrphanEntry(
                    rel_path=rp,
                    reason="unreachable",
                    confidence=0.5,
                    recommendation="investigate",
                ))
            elif is_reachable and entry.complexity_score > 0.6 and not entry.tested_by:
                orphans.append(OrphanEntry(
                    rel_path=rp,
                    reason="no_tests",
                    confidence=0.3,
                    recommendation="needs_test",
                ))

        return orphans


def _is_test_file(rel_path: str) -> bool:
    """Check if a file is a test file by naming convention."""
    name = Path(rel_path).name
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith(".test.ts")
        or name.endswith(".test.js")
        or name.endswith(".spec.ts")
        or name.endswith(".spec.js")
        or "/tests/" in rel_path
        or "/__tests__/" in rel_path
    )


def _detect_git_depth(repo_root: Path) -> str:
    """Returns 'full' | 'shallow' | 'minimal' | 'none'."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-shallow-repository"],
            capture_output=True, text=True, cwd=repo_root,
            timeout=5,
        )
        if result.returncode != 0:
            return "none"
        if result.stdout.strip() == "true":
            return "shallow"

        # Count commits
        count_result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            capture_output=True, text=True, cwd=repo_root,
            timeout=10,
        )
        if count_result.returncode == 0:
            count = int(count_result.stdout.strip())
            if count < 50:
                return "minimal"
        return "full"
    except Exception:
        return "none"
