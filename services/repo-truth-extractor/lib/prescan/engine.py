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

class PrescanEngine:
    def __init__(self, config: PrescanConfig, limiter: Any | None = None):
        self.config = config
        self.walker = CorpusWalker(config)
        self.classifier = FileClassifier(config)
        self.enricher = GitEnricher(config)
        self.git_enricher = self.enricher
        self.detector = DuplicateDetector(config)
        self.duplicate_detector = self.detector
        self.code_scanner = CodePrescan(config)
        self.dep_graph = DependencyGraph()
        self.cost_estimator = CostEstimator(config)
        self.grok_runner = GrokPassRunner(config, limiter=limiter)

    def run(self, passes: list[str] | None = None, incremental: bool = False) -> PrescanResult:
        """Run the full prescan pipeline."""
        start_time = time.time()
        warnings = []
        errors = []
        
        try:
            # 1. Walk corpus
            logger.info(f"Walking corpus in {self.config.repo_root}...")
            files = self.walker.walk()
            
            # 2. Classify files
            logger.info("Classifying files...")
            entries = self.classifier.classify(files)
            
            # 3. Git enrichment
            changed_files = None
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
            if self.config.enable_code_prescan:
                logger.info("Running code intelligence (AST analysis)...")
                try:
                    code_entries = [e for e in entries if e.include and e.extension in self.config.code_languages]
                    code_intel = self.code_scanner.scan([e.rel_path for e in code_entries])
                    self.dep_graph.build_from_code_intelligence(
                        code_intel,
                        [e.to_dict() for e in entries],
                    )
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
                planner = BatchPlanner(self.config, entries, manifest)
                batch_plans = {
                    pass_id: planner.plan_batches(pass_id, intelligence)
                    for pass_id in passes
                }
                
                # Save batch plan
                self.config.output_dir.mkdir(parents=True, exist_ok=True)
                batch_plan_path = self.config.output_dir / "batch_plan.json"
                batch_plan_path.write_text(
                    json.dumps({p: bp.to_dict() for p, bp in batch_plans.items()}, indent=2) + "\n"
                )

                # 7b. Provider routing
                logger.info("Building provider model catalog for routing...")
                routing_plan = None
                try:
                    catalog_data = build_provider_model_catalog(self.config)
                    routing_plan = build_prescan_routing_plan(self.config, catalog_data, passes)
                    
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
            intel_path.write_text(json.dumps(intelligence, indent=2, sort_keys=True) + "\n")
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            
            duration = time.time() - start_time
            total_batches = sum(len(bp.batches) for bp in batch_plans.values()) if batch_plans else 0

            return PrescanResult(
                success=True,
                intelligence_path=intel_path,
                manifest_path=manifest_path,
                file_count=len(entries),
                code_files_analyzed=len(code_intel),
                duration_seconds=round(duration, 2),
                warnings=warnings,
                errors=errors,
                batch_plan_path=batch_plan_path,
                batch_count=total_batches,
            )

        except Exception as e:
            logger.error(f"Prescan failed: {e}", exc_info=True)
            return PrescanResult(
                success=False,
                errors=[str(e)],
                duration_seconds=round(time.time() - start_time, 2),
                file_count=0,
                code_files_analyzed=0,
            )

        finally:
            # 9. Save LLM attempts evidence (always)
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

        version_chain_ids = {e.version_chain_id for e in entries if e.version_chain_id}
        compression_candidates = sum(1 for e in entries if e.version_chain_id and not e.is_latest_version)

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
            "lifecycle_distribution": self._get_lifecycle_dist(entries),
            "planned_features": self._find_planned_features(entries),
            "ghost_files": [
                {
                    "path": g.rel_path,
                    "deleted_at_sha": g.deleted_at_sha,
                    "deleted_date": g.deleted_date,
                    "recovery_source": g.recovery_source,
                }
                for g in ghosts
            ],
            "version_chain_count": len(version_chain_ids),
            "compression_potential_files": compression_candidates,
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
            "proposed_adrs": [e.rel_path for e in entries if e.is_proposed_adr],
            "stub_files": [e.rel_path for e in entries if e.has_stub_methods],
            "todo_files": [e.rel_path for e in entries if e.has_todo_markers],
            "draft_docs": [e.rel_path for e in entries if e.is_draft_doc],
        }

    def _get_git_sha(self) -> str:
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "HEAD"], 
                cwd=self.config.repo_root, 
                stderr=subprocess.DEVNULL
            ).decode().strip()
        except:
            return "unknown"
