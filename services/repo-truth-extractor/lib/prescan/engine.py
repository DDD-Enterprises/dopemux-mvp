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

    def run(self, passes: list[str] | None = None) -> PrescanResult:
        """Run full prescan pipeline."""
        start_time = time.time()
        warnings = []
        errors = []

        try:
            # 1. Walk corpus
            logger.info(f"Walking corpus in {self.config.repo_root}...")
            entries = self.walker.walk()
            
            # 2. Classify files
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
                for entry in entries:
                    intel = self.code_prescan.analyze_file(entry, self.config.repo_root)
                    if intel:
                        code_intel.append(intel)
                
                logger.info("Building dependency graph...")
                manifest_simple = [e.to_dict() for e in entries]
                self.dep_graph.build_from_code_intelligence(code_intel, manifest_simple)
            
            # 6. Build intelligence report (base)
            intelligence = self._build_intelligence_base(entries, code_intel)
            manifest = [e.to_dict() for e in entries]
            
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

            # 7. Grok passes (optional)
            grok_results = {}
            if passes:
                logger.info(f"Running Grok passes: {', '.join(passes)}...")
                if self.config.batch_mode and batch_plans:
                    grok_results = self.grok_runner.run_passes_batched(
                        passes, intelligence, manifest, batch_plans
                    )
                else:
                    grok_results = self.grok_runner.run_passes(passes, intelligence, manifest)
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
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat()
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

        # API surfaces summary
        api_surfaces = set()
        if code_intel:
            for ci in code_intel:
                api_surfaces.update(ci.get("api_surfaces", []))

        intelligence = {
            "version": "2.0.0",
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "repo_root": str(self.config.repo_root),
            "corpus_summary": {
                "total_files_scanned": len(entries),
                "included_files": len(included),
                "total_included_size_bytes": sum(e.size_bytes for e in included),
                "by_authority_class": by_class,
                "by_extension": by_ext
            },
            "duplicate_groups": dup_groups,
            "version_chains": chains,
            "extraction_hints": {
                "skip_duplicates": [e.rel_path for e in included if e.is_duplicate],
                "compress_candidates": [] # Will be populated by passes
            }
        }

        if code_intel:
            intelligence["code_intelligence"] = {
                "analyzed_files": len(code_intel),
                "api_surfaces": sorted(list(api_surfaces)),
                "dependency_clusters": [list(c) for c in self.dep_graph.find_clusters()],
                "topological_order": self.dep_graph.get_topological_order()[:100] # Limit for report
            }

        return intelligence

    def _get_git_sha(self) -> str:
        import subprocess
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "HEAD"], 
                cwd=self.config.repo_root, 
                stderr=subprocess.DEVNULL
            ).decode().strip()
        except:
            return "unknown"
