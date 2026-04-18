import datetime as dt
import json
import logging
import time
from pathlib import Path
from typing import Any

from .models import PrescanConfig, PrescanResult, FileEntry
from .corpus_walker import CorpusWalker
from .classifier import Classifier
from .git_enricher import GitEnricher
from .duplicate_detector import DuplicateDetector
from .grok_passes import GrokPassRunner
from .code_prescan import CodePrescan
from .dependency_graph import DependencyGraph
from .batch_planner import BatchPlanner
from .cost_estimator import CostEstimator
from .incremental_cache import IncrementalCodeCache
from .provider_catalog import (
    NO_LIVE_LANE,
    build_provider_model_catalog,
    build_prescan_routing_plan,
    build_provider_readiness_matrix,
    write_live_lane_success_artifact,
    write_no_live_lane_artifact,
    write_provider_catalog,
    write_provider_readiness,
    write_routing_plan,
)

logger = logging.getLogger(__name__)

class PrescanEngine:
    def __init__(self, config: PrescanConfig):
        self.config = config
        self.walker = CorpusWalker(config)
        self.classifier = Classifier(config)
        self.git_enricher = GitEnricher(config)
        self.duplicate_detector = DuplicateDetector(config)
        self.grok_runner = GrokPassRunner(config)
        self.code_prescan = CodePrescan(config)
        self.dep_graph = DependencyGraph()
        self.cost_estimator = CostEstimator(config)

    def run(self, passes: list[str] | None = None, incremental: bool = False) -> PrescanResult:
        """Run full or incremental prescan pipeline."""
        start_time = time.time()
        warnings = []
        errors = []
        incremental_cache = IncrementalCodeCache(self.config)
        changed_files: set[str] | None = None
        cache_payload: dict[str, Any] | None = None
        cache_fallback_reason: str | None = None
        cached_reuse_count = 0
        reanalyzed_count = 0
        removed_cache_entries = 0

        try:
            # 1. Walk corpus
            logger.info(f"Walking corpus in {self.config.repo_root}...")
            entries = self.walker.walk()
            
            # 2. Incremental logic: Filter unchanged files if requested
            if incremental:
                changed_files = self._get_changed_files()
                if changed_files is None:
                    warning = (
                        "Incremental change detection unavailable; running explicit full recompute and regenerating cache."
                    )
                    warnings.append(warning)
                    logger.warning(warning)
                else:
                    logger.info(f"Incremental mode: {len(changed_files)} files changed since last run.")
                    cache_payload, cache_warning = incremental_cache.load()
                    if cache_warning:
                        cache_fallback_reason = cache_warning
                        warnings.append(cache_warning)
                        logger.warning(cache_warning)
            
            # 3. Classify files
            logger.info("Classifying files...")
            self.classifier.classify_all(entries)
            
            # 3. Git enrichment
            if self.config.enable_git_enrichment:
                logger.info("Enriching with git metadata...")
                self.git_enricher.enrich(entries)
                
                logger.info("Recovering ghost files...")
                existing_paths = {e.rel_path for e in entries}
                ghosts = self.git_enricher.recover_ghost_files(existing_paths)
                entries.extend(ghosts)
            
            # 4. Duplicate detection
            logger.info("Detecting duplicates and version chains...")
            self.duplicate_detector.detect_duplicates(entries)
            self.duplicate_detector.detect_version_chains(entries)

            # 5. Code Intelligence (AST)
            code_intel = []
            if self.config.enable_code_prescan:
                logger.info("Running code intelligence (AST analysis)...")
                current_paths = {entry.rel_path for entry in entries}
                removed_cache_entries = incremental_cache.removed_entry_count(cache_payload, current_paths)
                for entry in entries:
                    cached = incremental_cache.reusable_analysis(cache_payload, entry, changed_files)
                    if cached is not None:
                        cached_reuse_count += 1
                        code_intel.append(incremental_cache.apply_cached_metrics(entry, cached))
                        continue
                    intel = self.code_prescan.analyze_file(entry, self.config.repo_root)
                    if intel:
                        reanalyzed_count += 1
                        code_intel.append(intel)

                if incremental:
                    logger.info(
                        "Incremental code analysis: reused=%d reanalyzed=%d removed=%d",
                        cached_reuse_count,
                        reanalyzed_count,
                        removed_cache_entries,
                    )
                
                logger.info("Building dependency graph...")
                manifest_simple = [e.to_dict() for e in entries]
                self.dep_graph.build_from_code_intelligence(code_intel, manifest_simple)
            
            # 6. Build intelligence report (base)
            intelligence = self._build_intelligence_base(entries, code_intel)
            manifest = [e.to_dict() for e in entries]
            
            # 6a. Cost Estimation (Only if explicitly requested, though we don't have a flag for it in config yet, let's assume we do it if batch_mode or explicitly requested, or we can just keep it fast. Let's wrap in a try block)
            if self.config.cost_estimate:
                logger.info("Estimating extraction costs...")
                intelligence["cost_estimate"] = self.cost_estimator.estimate(entries)
            
            # 6b. Code Intelligence Report (if code prescan ran)
            code_report = None
            code_report_path = None
            if self.config.enable_code_prescan and code_intel:
                try:
                    from .code_intelligence_report import CodeIntelligenceBuilder

                    builder = CodeIntelligenceBuilder(
                        code_prescan=self.code_prescan,
                        dep_graph=self.dep_graph,
                        entries=entries,
                        manifest=manifest,
                    )
                    code_report = builder.build(self.config.repo_root)
                    code_report_path = self.config.output_dir / "code_intelligence_report.json"
                    self.config.output_dir.mkdir(parents=True, exist_ok=True)
                    code_report_path.write_text(
                        json.dumps(code_report, indent=2, default=str) + "\n"
                    )
                    # Inject summary into intelligence
                    intelligence.setdefault("code_intelligence", {})
                    intelligence["code_intelligence"]["report_summary"] = code_report.get("summary", {})
                    intelligence["code_intelligence"]["processing_order"] = code_report.get("processing_order", [])[:50]
                    intelligence["code_intelligence"]["hotspots"] = code_report.get("hotspots", [])
                    intelligence["code_intelligence"]["orphans"] = code_report.get("orphans", [])
                    logger.info(f"Code intelligence report saved: {code_report_path}")
                except Exception as e:
                    logger.warning(f"Code intelligence report failed (non-fatal): {e}")

            # 6c. Batch planning (if batch_mode enabled)
            batch_plans = {}
            batch_plan_path = None
            if self.config.batch_mode and passes:
                logger.info("Planning token-aware batches...")
                planner = BatchPlanner(self.config, entries, manifest)
                for pid in passes:
                    batch_plans[pid] = planner.plan_batches(pid, intelligence)
                    bp = batch_plans[pid]
                    logger.info(
                        f"  {pid}: {len(bp.batches)} batches, "
                        f"~{bp.total_estimated_tokens:,} tokens, "
                        f"{bp.total_files} files"
                    )
                    if bp.oversized_files:
                        logger.info(f"  {pid}: {len(bp.oversized_files)} oversized files excluded")

                # Save batch plan
                self.config.output_dir.mkdir(parents=True, exist_ok=True)
                batch_plan_path = self.config.output_dir / "batch_plan.json"
                plan_data = {pid: bp.to_dict() for pid, bp in batch_plans.items()}
                batch_plan_path.write_text(
                    json.dumps(plan_data, indent=2, sort_keys=True) + "\n"
                )

            # 7. Build provider routing plan for grok passes
            routing_plan = None
            routing_plan_path = None
            provider_readiness = None
            live_lane_success_path = None
            if passes:
                try:
                    logger.info("Building provider model catalog for routing...")
                    self.config.output_dir.mkdir(parents=True, exist_ok=True)
                    catalog = build_provider_model_catalog(self.config)
                    catalog_path = write_provider_catalog(self.config.output_dir, catalog)
                    logger.info(f"Provider catalog saved: {catalog_path}")

                    provider_readiness = build_provider_readiness_matrix(self.config, catalog)
                    readiness_path = write_provider_readiness(self.config.output_dir, provider_readiness)
                    logger.info(f"Provider readiness saved: {readiness_path}")

                    routing_plan = build_prescan_routing_plan(self.config, catalog, provider_readiness, passes)
                    routing_plan_path = write_routing_plan(self.config.output_dir, routing_plan)
                    logger.info(f"Routing plan saved: {routing_plan_path}")
                    if routing_plan.get("status") == "PASS":
                        live_lane_success_path = write_live_lane_success_artifact(
                            self.config.output_dir,
                            routing_plan,
                        )
                        logger.info(f"Live lane success artifact saved: {live_lane_success_path}")
                except Exception as e:
                    logger.exception("Provider routing failed during Stage 0 readiness gating")
                    return PrescanResult(
                        success=False,
                        intelligence_path=None,
                        manifest_path=None,
                        code_graph_path=None,
                        file_count=len(entries),
                        included_count=sum(1 for e in entries if e.include),
                        code_files_analyzed=len(code_intel),
                        duration_seconds=round(time.time() - start_time, 2),
                        warnings=warnings,
                        errors=[f"Stage 0 routing/readiness failed: {e}"],
                        metadata={
                            "git_sha": self._get_git_sha(),
                            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                            "stage0": {
                                "provider_readiness_status": "UNKNOWN",
                                "routing_plan_status": "ERROR",
                                "routing_error": str(e),
                                "routing_plan_path": None,
                                "live_lane_success_artifact": None,
                            },
                            "incremental": {
                                "enabled": incremental,
                                "changed_files_count": len(changed_files) if changed_files is not None else None,
                                "cached_code_analysis_reused": cached_reuse_count,
                                "reanalyzed_code_files": reanalyzed_count,
                                "removed_cache_entries": removed_cache_entries,
                                "fallback_reason": cache_fallback_reason,
                            },
                        },
                        batch_plan_path=batch_plan_path,
                        batch_count=sum(len(bp.batches) for bp in batch_plans.values()) if batch_plans else 0,
                        code_report_path=code_report_path,
                    )

                if routing_plan and routing_plan.get("status") == NO_LIVE_LANE:
                    no_live_lane_path = write_no_live_lane_artifact(self.config.output_dir, routing_plan)
                    logger.error(f"No executable prescan route survived Stage 0: {no_live_lane_path}")
                    return PrescanResult(
                        success=False,
                        intelligence_path=None,
                        manifest_path=None,
                        code_graph_path=None,
                        file_count=len(entries),
                        included_count=sum(1 for e in entries if e.include),
                        code_files_analyzed=len(code_intel),
                        duration_seconds=round(time.time() - start_time, 2),
                        warnings=warnings,
                        errors=["No executable live prescan lane survived Stage 0 readiness gating."],
                        metadata={
                            "git_sha": self._get_git_sha(),
                            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                            "stage0": {
                                "provider_readiness_status": (
                                    provider_readiness or {}
                                ).get("status", "UNKNOWN"),
                                "routing_plan_status": routing_plan.get("status"),
                                "routing_plan_path": str(routing_plan_path) if routing_plan_path else None,
                                "no_live_lane_artifact": str(no_live_lane_path),
                                "live_lane_success_artifact": None,
                            },
                            "incremental": {
                                "enabled": incremental,
                                "changed_files_count": len(changed_files) if changed_files is not None else None,
                                "cached_code_analysis_reused": cached_reuse_count,
                                "reanalyzed_code_files": reanalyzed_count,
                                "removed_cache_entries": removed_cache_entries,
                                "fallback_reason": cache_fallback_reason,
                            },
                        },
                        batch_plan_path=batch_plan_path,
                        batch_count=sum(len(bp.batches) for bp in batch_plans.values()) if batch_plans else 0,
                        code_report_path=code_report_path,
                    )

            # 7a. Grok passes (optional)
            grok_results = {}
            if passes:
                logger.info(f"Running Grok passes: {', '.join(passes)}...")
                if self.config.batch_mode and batch_plans:
                    grok_results = self.grok_runner.run_passes_batched(
                        passes, intelligence, manifest, batch_plans, routing_plan=routing_plan
                    )
                else:
                    grok_results = self.grok_runner.run_passes(passes, intelligence, manifest, routing_plan=routing_plan)
                intelligence["grok_passes"] = grok_results

            # 7b. Archaeology report (deep mode only)
            archaeology_report_path = None
            if self.config.deep_mode and grok_results:
                try:
                    from .archaeology_report import ArchaeologyReporter

                    reporter = ArchaeologyReporter(entries, intelligence, grok_results)
                    arch_report = reporter.generate()
                    archaeology_report_path = self.config.output_dir / "archaeology_report.json"
                    archaeology_report_path.write_text(
                        json.dumps(arch_report, indent=2, default=str) + "\n"
                    )
                    logger.info(f"Archaeology report saved: {archaeology_report_path}")
                except Exception as e:
                    logger.warning(f"Archaeology report failed (non-fatal): {e}")
            
            # 8. Save artifacts
            self.config.output_dir.mkdir(parents=True, exist_ok=True)
            
            intel_path = self.config.output_dir / "prescan_intelligence.json"
            manifest_path = self.config.output_dir / "corpus_manifest.json"
            graph_path = self.config.output_dir / "code_graph.json"
            
            intel_path.write_text(json.dumps(intelligence, indent=2, sort_keys=True) + "\n")
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            
            if self.config.enable_code_prescan:
                graph_path.write_text(self.dep_graph.to_json() + "\n")

            if self.config.enable_code_prescan:
                incremental_cache.write(entries, code_intel, self._get_git_sha())
            
            duration = time.time() - start_time
            
            total_batches = sum(len(bp.batches) for bp in batch_plans.values()) if batch_plans else 0

            return PrescanResult(
                success=True,
                intelligence_path=intel_path,
                manifest_path=manifest_path,
                code_graph_path=graph_path if self.config.enable_code_prescan else None,
                file_count=len(entries),
                included_count=sum(1 for e in entries if e.include),
                code_files_analyzed=len(code_intel),
                duration_seconds=round(duration, 2),
                warnings=warnings,
                errors=errors,
                metadata={
                    "git_sha": self._get_git_sha(),
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "stage0": {
                        "provider_readiness_status": (
                            provider_readiness or {}
                        ).get("status", "UNKNOWN") if passes else None,
                        "routing_plan_status": (
                            routing_plan or {}
                        ).get("status", "NOT_REQUESTED") if passes else "NOT_REQUESTED",
                        "routing_plan_path": str(routing_plan_path) if routing_plan_path else None,
                        "live_lane_success_artifact": (
                            str(live_lane_success_path) if live_lane_success_path else None
                        ),
                    },
                    "incremental": {
                        "enabled": incremental,
                        "changed_files_count": len(changed_files) if changed_files is not None else None,
                        "cached_code_analysis_reused": cached_reuse_count,
                        "reanalyzed_code_files": reanalyzed_count,
                        "removed_cache_entries": removed_cache_entries,
                        "fallback_reason": cache_fallback_reason,
                    },
                },
                batch_plan_path=batch_plan_path,
                batch_count=total_batches,
                archaeology_report_path=archaeology_report_path,
                code_report_path=code_report_path,
            )

        except Exception as e:
            logger.error(f"Prescan failed: {e}", exc_info=True)
            return PrescanResult(
                success=False,
                errors=[str(e)],
                duration_seconds=round(time.time() - start_time, 2)
            )

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

        # Duplicate groups
        dup_groups = {}
        for e in included:
            if e.duplicate_group_id:
                dup_groups.setdefault(e.duplicate_group_id, []).append(e.rel_path)

        # Version chains
        chains = {}
        for e in entries:
            if e.version_chain_id:
                chains.setdefault(e.version_chain_id, []).append({
                    "path": e.rel_path,
                    "ordinal": e.version_ordinal,
                    "is_latest": e.is_latest_version
                })

        lifecycle_distribution: dict[str, int] = {}
        for e in entries:
            stage = e.lifecycle_stage or "unknown"
            lifecycle_distribution[stage] = lifecycle_distribution.get(stage, 0) + 1

        planned_features = {
            "proposed_adrs": sorted(e.rel_path for e in included if e.is_proposed_adr),
            "stub_files": sorted(e.rel_path for e in included if e.has_stub_methods),
            "todo_files": sorted(e.rel_path for e in included if e.has_todo_markers),
            "draft_docs": sorted(e.rel_path for e in included if e.is_draft_doc),
        }
        compression_potential_files = sum(
            1 for e in included if e.version_chain_id and not e.is_latest_version
        )
        high_churn_files = sorted(
            e.rel_path for e in included if e.churn_score >= 2.0
        )
        excluded_files = sum(1 for e in entries if not e.include and not e.is_ghost)

        # API surfaces summary
        api_surfaces = set()
        if code_intel:
            for ci in code_intel:
                api_surfaces.update(ci.get("api_surfaces", []))

        corpus_health_score = 100
        if entries:
            coverage_ratio = len(included) / len(entries)
            corpus_health_score = int(round(coverage_ratio * 100))
            corpus_health_score -= min(compression_potential_files * 5, 20)
            corpus_health_score -= min(len(ghosts) * 2, 10)
            corpus_health_score = max(0, min(100, corpus_health_score))

        intelligence = {
            "version": "2.0.0",
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "repo_root": str(self.config.repo_root),
            "corpus_summary": {
                "total_files_scanned": len(entries),
                "included_files": len(included),
                "excluded_files": excluded_files,
                "ghost_files": len(ghosts),
                "total_included_size_bytes": sum(e.size_bytes for e in included),
                "by_authority_class": by_class,
                "by_extension": by_ext,
                "corpus_health_score": corpus_health_score,
            },
            "lifecycle_distribution": lifecycle_distribution,
            "duplicate_groups": dup_groups,
            "version_chains": chains,
            "version_chain_count": len(chains),
            "compression_potential_files": compression_potential_files,
            "ghost_files": [
                {
                    "path": e.rel_path,
                    "deleted_at_sha": e.deleted_at_sha,
                    "deleted_date": e.deleted_date,
                    "recovery_source": e.recovery_source,
                }
                for e in ghosts
            ],
            "planned_features": planned_features,
            "extraction_hints": {
                "skip_duplicates": [e.rel_path for e in included if e.is_duplicate],
                "high_churn_files": high_churn_files,
                "compress_candidates": [],
            },
        }

        if code_intel:
            intelligence["code_intelligence"] = {
                "analyzed_files": len(code_intel),
                "api_surfaces": sorted(list(api_surfaces)),
                "dependency_clusters": [list(c) for c in self.dep_graph.find_clusters()],
                "topological_order": self.dep_graph.get_topological_order()[:100] # Limit for report
            }

        return intelligence

    def _get_changed_files(self) -> set[str] | None:
        """Get set of files changed since the last git commit or specified baseline."""
        import subprocess
        try:
            baseline = self.config.incremental_baseline or "HEAD~1"
            cmd = ["git", "diff", "--name-only", "--diff-filter=ACMR", baseline, "HEAD"]
            output = subprocess.check_output(
                cmd, 
                cwd=self.config.repo_root, 
                stderr=subprocess.DEVNULL
            ).decode().splitlines()
            return set(output)
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            return None

    def _get_git_sha(self) -> str:
        import subprocess
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "HEAD"], 
                cwd=self.config.repo_root, 
                stderr=subprocess.DEVNULL
            ).decode().strip()
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            return "unknown"
