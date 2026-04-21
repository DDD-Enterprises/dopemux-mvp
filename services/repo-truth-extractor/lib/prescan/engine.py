import datetime as dt
import json
import logging
import time
import subprocess
from pathlib import Path
from typing import Any, Optional

from .models import PrescanConfig, PrescanResult, FileEntry
from .corpus_walker import CorpusWalker
from .classifier import FileClassifier
from .git_enricher import GitEnricher
from .duplicate_detector import DuplicateDetector
from .grok_passes import GrokPassRunner
from .code_prescan import CodePrescan
from .dependency_graph import DependencyGraph
from .batch_planner import BatchPlanner
from .cost_estimator import CostEstimator
from .provider_catalog import (
    build_provider_model_catalog,
    build_prescan_routing_plan,
    write_provider_catalog,
    write_routing_plan,
)

logger = logging.getLogger(__name__)


_LANGUAGE_EXTENSION_ALIASES = {
    "python": {".py"},
    "javascript": {".js", ".jsx"},
    "typescript": {".ts", ".tsx"},
}


def _entry_matches_code_language(entry: FileEntry, code_languages: list[str]) -> bool:
    normalized = {lang.strip().lower() for lang in code_languages}
    aliases: set[str] = set(normalized)
    for language in normalized:
        aliases.update(_LANGUAGE_EXTENSION_ALIASES.get(language, set()))
    return entry.extension in aliases


class PrescanEngine:
    def __init__(self, config: PrescanConfig, limiter: Any | None = None):
        self.config = config
        self.walker = CorpusWalker(config)
        self.classifier = FileClassifier(config)
        self.enricher = GitEnricher(config)
        self.detector = DuplicateDetector(config)
        self.code_scanner = CodePrescan(config)
        self.dep_graph = DependencyGraph()
        self.cost_estimator = CostEstimator(config)
        self.grok_runner = GrokPassRunner(config, limiter=limiter)

    def run(self, passes: list[str] | None = None, incremental: bool = False) -> PrescanResult:
        """Run the full prescan pipeline."""
        start_time = time.time()
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        warnings = []
        errors = []
        
        try:
            # 1. Walk corpus
            logger.info(f"Walking corpus in {self.config.repo_root}...")
            files = self.walker.walk()
            
            # 2. Classify files
            logger.info("Classifying files...")
            entries = files
            self.classifier.classify_all(entries)
            
            # 3. Git enrichment
            if self.config.enable_git_enrichment:
                logger.info("Enriching with git metadata...")
                try:
                    self.enricher.enrich(entries)
                except Exception as e:
                    logger.warning(f"Git enrichment failed: {e}")
                    warnings.append(f"Git enrichment failed: {e}")

            # 4. Duplicate detection
            logger.info("Detecting duplicates and version chains...")
            duplicates = self.detector.detect(entries)
            
            # 5. Code intelligence
            code_intel = []
            code_graph_path = None
            if self.config.enable_code_prescan:
                logger.info("Running code intelligence (AST analysis)...")
                try:
                    code_entries = [
                        e
                        for e in entries
                        if e.include and _entry_matches_code_language(e, self.config.code_languages)
                    ]
                    for entry in code_entries:
                        intel = self.code_scanner.analyze_file(entry, self.config.repo_root)
                        if intel:
                            code_intel.append(intel)
                    self.dep_graph.build_from_code_intelligence(
                        code_intel,
                        [e.to_dict() for e in entries],
                    )
                    code_graph_path = self.config.output_dir / "code_dependency_graph.json"
                    code_graph_path.write_text(self.dep_graph.to_json() + "\n", encoding="utf-8")
                except Exception as e:
                    logger.warning(f"Code intelligence failed: {e}")
                    warnings.append(f"Code intelligence failed: {e}")

            # 6. Build intelligence base
            intelligence = self._build_intelligence_base(entries, code_intel)
            intelligence["duplicate_groups"] = duplicates["groups"]
            intelligence["version_chains"] = duplicates["chains"]
            intelligence["version_chain_count"] = len(duplicates["chains"])
            
            # 7. Optional passes
            batch_plans = {}
            batch_plan_path = None
            
            if passes:
                # 7a. Batch planning
                logger.info("Planning token-aware batches...")
                manifest = [e.to_dict() for e in entries]
                
                # Instantiate planner with live data
                planner = BatchPlanner(self.config, entries, manifest)
                batch_plans = {p: planner.plan_batches(p, intelligence) for p in passes}
                
                # Save batch plan
                batch_plan_path = self.config.output_dir / "batch_plan.json"
                batch_plan_path.write_text(
                    json.dumps({p: bp.to_dict() for p, bp in batch_plans.items()}, indent=2) + "\n",
                    encoding="utf-8"
                )

                # 7b. Provider routing
                logger.info("Building provider model catalog for routing...")
                routing_plan = None
                try:
                    catalog_data = build_provider_model_catalog(self.config)
                    routing_plan = build_prescan_routing_plan(self.config, passes, batch_plans, catalog_data)
                    
                    # Save routing plan
                    write_routing_plan(self.config.output_dir, routing_plan)
                    write_provider_catalog(self.config.output_dir, catalog_data)
                except Exception as e:
                    logger.warning(f"Provider routing failed (using defaults): {e}")
                    warnings.append(f"Provider routing failed: {e}")

                # 7c. Execute Grok passes
                logger.info(f"Running Grok passes: {', '.join(passes)}...")
                grok_results = self.grok_runner.run_passes_batched(
                    passes, intelligence, manifest, batch_plans, routing_plan=routing_plan
                )
                intelligence["grok_passes"] = grok_results

            # 8. Save artifacts
            self.config.output_dir.mkdir(parents=True, exist_ok=True)
            
            intel_path = self.config.output_dir / "prescan_intelligence.json"
            manifest_path = self.config.output_dir / "corpus_manifest.json"
            
            manifest = [e.to_dict() for e in entries]
            intel_path.write_text(json.dumps(intelligence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            
            duration = time.time() - start_time
            total_batches = sum(len(bp.batches) for bp in batch_plans.values()) if batch_plans else 0

            return PrescanResult(
                success=True,
                intelligence_path=intel_path,
                manifest_path=manifest_path,
                file_count=len(entries),
                included_count=sum(1 for e in entries if e.include),
                code_files_analyzed=len(code_intel),
                duration_seconds=round(duration, 2),
                warnings=warnings,
                errors=errors,
                batch_plan_path=batch_plan_path,
                batch_count=total_batches,
                code_graph_path=code_graph_path,
            )

        except Exception as e:
            logger.error(f"Prescan failed: {e}", exc_info=True)
            return PrescanResult(
                success=False,
                errors=errors + [str(e)],
                warnings=warnings,
                duration_seconds=round(time.time() - start_time, 2)
            )

        finally:
            # 10. Save LLM attempts evidence (always)
            try:
                self.config.output_dir.mkdir(parents=True, exist_ok=True)
                self.grok_runner.save_attempts()
            except Exception as e:
                logger.warning(f"Failed to save LLM attempts evidence (finally): {e}")

    def _build_intelligence_base(self, entries: list[FileEntry], code_intel: list[dict] | None = None) -> dict[str, Any]:
        """Build the basic intelligence structure."""
        included = [e for e in entries if e.include and not e.is_ghost]
        ghosts = [e for e in entries if e.is_ghost]

        # Summary stats
        by_class = {}
        for e in entries:
            by_class[e.authority_class] = by_class.get(e.authority_class, 0) + 1
            
        by_ext = {}
        for e in included:
            by_ext[e.extension] = by_ext.get(e.extension, 0) + 1

        return {
            "version": "1.0",
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "repo_root": str(self.config.repo_root),
            "corpus_summary": {
                "total_files": len(entries),
                "included_files": len(included),
                "ghost_files": len(ghosts),
                "by_class": by_class,
                "by_extension": by_ext,
                "total_size_bytes": sum(e.size_bytes for e in included),
                "corpus_health_score": 100,
            },
            "lifecycle_distribution": self._get_lifecycle_dist(included),
            "planned_features": self._find_planned_features(included),
            "ghost_files": [g.to_dict() for g in ghosts],
            "code_intelligence": code_intel or [],
            "extraction_hints": {
                "skip_duplicates": [],
                "compression_candidates": [],
            }
        }

    def _get_lifecycle_dist(self, entries: list[FileEntry]) -> dict[str, int]:
        dist = {}
        for e in entries:
            dist[e.lifecycle_stage] = dist.get(e.lifecycle_stage, 0) + 1
        return dist

    def _find_planned_features(self, entries: list[FileEntry]) -> dict[str, list[str]]:
        return {
            "proposed_adrs": [e.rel_path for e in entries if "ADR" in e.rel_path and e.lifecycle_stage == "stub"],
            "stub_files": [e.rel_path for e in entries if e.lifecycle_stage == "stub"],
            "todo_files": [e.rel_path for e in entries if e.lifecycle_stage == "stale"],
            "draft_docs": [e.rel_path for e in entries if e.authority_class == "historical"],
        }

    def _get_git_sha(self) -> str:
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "HEAD"], 
                cwd=self.config.repo_root, 
                stderr=subprocess.DEVNULL
            ).decode().strip()
        except Exception:
            return "unknown"
