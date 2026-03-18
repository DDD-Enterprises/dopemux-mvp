import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

class IntelligenceRouter:
    def __init__(self, prescan_intelligence: Dict[str, Any]):
        self.intel = prescan_intelligence
        self.code_intel = prescan_intelligence.get("code_intelligence", {})
        self.hints = prescan_intelligence.get("extraction_hints", {})

        # Pre-processed lookups
        self.skip_list = set(self.hints.get("skip_duplicates", []))
        self.compress_map = {c["chain_id"]: c for c in self.hints.get("compress_candidates", [])}

        # Load topological order if available
        self.topological_order = self.code_intel.get("topological_order", [])
        self.topo_index = {path: i for i, path in enumerate(self.topological_order)}

        # Code intelligence report data
        self.code_report: Dict[str, Any] = {}
        self.processing_order: Dict[str, float] = {}
        self.orphan_set: Set[str] = set()
        self.partition_briefs: Dict[str, List[str]] = {}

        # Grok optimize pass data
        self._phase_routing: Dict[str, str] = {}
        self._model_routing: List[Dict[str, Any]] = []
        self._grok_skip_list: Set[str] = set()

        # Batch plan data
        self.batch_plan: Dict[str, Any] = {}
        self.archaeology_report: Dict[str, Any] = {}

        # Load grok optimize pass results if available
        grok_passes = prescan_intelligence.get("grok_passes", {})
        optimize = grok_passes.get("optimize", {})
        if optimize:
            self._grok_skip_list = set(optimize.get("skip_list", []))
            self.skip_list |= self._grok_skip_list
            for cc in optimize.get("compress_chains", []):
                if cc.get("send_summary_instead"):
                    self.compress_map[cc.get("chain_id", "")] = cc
            for pr in optimize.get("phase_routing_overrides", []):
                self._phase_routing[pr.get("path", "")] = pr.get("recommended_phase", "")
            self._model_routing = optimize.get("model_routing_hints", [])

            # Populate compress_candidates in hints
            if optimize.get("compress_chains"):
                self.hints.setdefault("compress_candidates", []).extend(
                    optimize["compress_chains"]
                )

    @classmethod
    def from_dir(cls, prescan_dir: Path) -> Optional["IntelligenceRouter"]:
        intel_path = prescan_dir / "prescan_intelligence.json"
        if not intel_path.exists():
            return None

        try:
            with open(intel_path) as f:
                data = json.load(f)
            router = cls(data)

            # Load code intelligence report
            code_report_path = prescan_dir / "code_intelligence_report.json"
            if code_report_path.exists():
                with open(code_report_path) as f:
                    router.code_report = json.load(f)
                # Build processing order lookup
                for entry in router.code_report.get("processing_order", []):
                    router.processing_order[entry["rel_path"]] = entry["score"]
                # Build orphan set (confidence >= 0.7)
                for orphan in router.code_report.get("orphans", []):
                    if orphan.get("confidence", 0) >= 0.7:
                        router.orphan_set.add(orphan["rel_path"])

            # Load batch plan
            batch_plan_path = prescan_dir / "batch_plan.json"
            if batch_plan_path.exists():
                with open(batch_plan_path) as f:
                    router.batch_plan = json.load(f)

            # Load archaeology report
            arch_path = prescan_dir / "archaeology_report.json"
            if arch_path.exists():
                with open(arch_path) as f:
                    router.archaeology_report = json.load(f)

            return router
        except Exception as e:
            logger.error(f"Failed to load intelligence router: {e}")
            return None

    def should_skip(self, rel_path: str) -> bool:
        """Check if a file should be skipped based on prescan."""
        return rel_path in self.skip_list

    def get_compression_hint(self, rel_path: str) -> Optional[str]:
        """Return a summary hint if this file is part of a compressed version chain."""
        for chain_id, members in self.intel.get("version_chains", {}).items():
            paths = [m["path"] for m in members]
            if rel_path in paths:
                for cc in self.hints.get("compress_candidates", []):
                    if cc.get("chain_id") == chain_id and cc.get("send_summary_instead"):
                        return cc.get("summary_hint", "Superseded by newer version.")
        return None

    def get_routing_priority(self, rel_path: str) -> int:
        """Return priority score (higher = extract earlier/more detail)."""
        priority = 50
        if rel_path in self.topo_index:
            priority += (100 - min(self.topo_index[rel_path], 50))
        return priority

    def get_composite_priority(self, rel_path: str) -> float:
        """Returns composite priority score (0-1). Higher = extract first."""
        return self.processing_order.get(rel_path, 0.5)

    def should_skip_code(self, rel_path: str) -> bool:
        """Dead code deprioritization (advisory only, never auto-skip).

        Returns True if confidence >= 0.7 (unreachable + zero importers).
        Never returns True for entry points, test files, or config files.
        """
        return rel_path in self.orphan_set

    def get_model_tier(self, rel_path: str) -> str:
        """Route complex/important files to better models.

        Returns 'premium', 'standard', or 'economy'.
        """
        # Check grok optimize model routing hints
        import fnmatch as _fnmatch
        for hint in self._model_routing:
            pattern = hint.get("partition_pattern", "")
            if _fnmatch.fnmatch(rel_path, pattern):
                return hint.get("recommended_model", "standard")

        # Check code intelligence
        if self.code_report:
            hotspots = self.code_report.get("hotspots", [])
            for h in hotspots[:10]:  # Top 10 hotspots
                if h.get("rel_path") == rel_path and h.get("hotspot_score", 0) > 0.7:
                    return "premium"

            pagerank = self.code_report.get("pagerank_scores", {})
            if pagerank:
                scores = sorted(pagerank.values(), reverse=True)
                top_10_pct = scores[max(0, len(scores) // 10)] if scores else 0
                if pagerank.get(rel_path, 0) >= top_10_pct and top_10_pct > 0:
                    return "premium"

        return "standard"

    def get_partition_brief(self, phase_key: str, partition_idx: int) -> Optional[str]:
        """Retrieve pre-generated context brief for a specific partition."""
        briefs = self.partition_briefs.get(phase_key, [])
        if partition_idx < len(briefs):
            return briefs[partition_idx]
        return None

    def get_phase_routing_override(self, rel_path: str) -> Optional[str]:
        """Return phase override from optimize pass, or None."""
        return self._phase_routing.get(rel_path)

    def get_model_routing_hint(self, rel_path: str) -> Optional[str]:
        """Return model routing hint from optimize pass, or None."""
        import fnmatch as _fnmatch
        for hint in self._model_routing:
            if _fnmatch.fnmatch(rel_path, hint.get("partition_pattern", "")):
                return hint.get("recommended_model")
        return None

    def get_test_file(self, rel_path: str) -> Optional[str]:
        """Return mapped test file path, or None."""
        for mapping in self.code_report.get("test_mappings", []):
            if mapping.get("source_path") == rel_path:
                return mapping.get("test_path")
        return None

    def get_bundling_group(self, rel_path: str) -> Optional[str]:
        """Suggest a bundling group (e.g. dependency cluster)."""
        for i, cluster in enumerate(self.code_intel.get("dependency_clusters", [])):
            if rel_path in cluster:
                return f"cluster_{i}"
        return None

    def estimate_token_savings(self, manifest: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Estimate token savings based on skip/compress rules."""
        stats = self.intel.get("corpus_summary", {})
        total_size = stats.get("total_included_size_bytes", 0)

        skipped_size = 0
        if manifest:
            for m in manifest:
                if m.get("rel_path") in self.skip_list:
                    skipped_size += m.get("size_bytes", 0)

        reduction_pct = round((skipped_size / total_size * 100), 1) if total_size > 0 else 0

        return {
            "skipped_files_count": len(self.skip_list),
            "skipped_bytes": skipped_size,
            "total_bytes": total_size,
            "estimated_reduction_pct": reduction_pct,
        }

    def reorder_partition(self, partition_files: List[str]) -> List[str]:
        """Reorder files within a partition by composite priority (descending)."""
        return sorted(
            partition_files,
            key=lambda f: self.get_composite_priority(f),
            reverse=True,
        )
