import datetime as dt
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any

from .batch_planner import BatchPlanner
from .classifier import Classifier
from .code_prescan import CodePrescan
from .cost_estimator import CostEstimator
from .corpus_walker import CorpusWalker
from .dependency_graph import DependencyGraph
from .duplicate_detector import DuplicateDetector
from .git_enricher import GitEnricher
from .grok_passes import GrokPassRunner
from .models import FileEntry, PrescanConfig, PrescanResult
from .provider_catalog import (
    build_prescan_routing_plan,
    build_provider_model_catalog,
    write_provider_catalog,
    write_routing_plan,
)

logger = logging.getLogger(__name__)


class PrescanEngine:
    def __init__(self, config: PrescanConfig, limiter: Any | None = None):
        self.config = config
        self.walker = CorpusWalker(config)
        self.classifier = Classifier(config)
        self.enricher = GitEnricher(config)
        self.detector = DuplicateDetector(config)
        self.code_scanner = CodePrescan(config)
        self.dep_graph = DependencyGraph()
        self.cost_estimator = CostEstimator(config)
        self.grok_runner = GrokPassRunner(config, limiter=limiter)

    def run(self, passes: list[str] | None = None, incremental: bool = False) -> PrescanResult:
        """Run full prescan pipeline."""
        start_time = time.time()
        warnings: list[str] = []

        try:
            logger.info("Walking corpus in %s...", self.config.repo_root)
            entries = self.walker.walk()

            logger.info("Classifying files...")
            self.classifier.classify_all(entries)

            if self.config.enable_git_enrichment:
                logger.info("Enriching with git metadata...")
                try:
                    self.enricher.enrich(entries)
                except Exception as exc:  # pragma: no cover - non-fatal guard
                    logger.warning("Git enrichment failed: %s", exc)
                    warnings.append(f"Git enrichment failed: {exc}")

            logger.info("Detecting duplicates and version chains...")
            self.detector.detect_duplicates(entries)
            self.detector.detect_version_chains(entries)
            duplicates = self._collect_duplicate_summaries(entries)

            logger.info("Running code intelligence...")
            manifest = [e.to_dict() for e in entries]
            code_intel: list[dict[str, Any]] = []
            if self.config.enable_code_prescan:
                try:
                    for entry in entries:
                        intel = self.code_scanner.analyze_file(entry, self.config.repo_root)
                        if intel:
                            code_intel.append(intel)
                    self.dep_graph.build_from_code_intelligence(code_intel, manifest)
                except Exception as exc:  # pragma: no cover - non-fatal guard
                    logger.warning("Code intelligence failed: %s", exc)
                    warnings.append(f"Code intelligence failed: {exc}")

            intelligence = self._build_intelligence_base(entries, code_intel)
            intelligence["duplicate_groups"] = duplicates["groups"]
            intelligence["version_chains"] = duplicates["chains"]
            intelligence["version_chain_count"] = len(duplicates["chains"])

            batch_plans: dict[str, Any] = {}
            batch_plan_path: Path | None = None
            routing_plan: dict[str, Any] | None = None

            if passes:
                if self.config.batch_mode:
                    logger.info("Planning token-aware batches...")
                    planner = BatchPlanner(self.config, entries, manifest)
                    for pass_id in passes:
                        batch_plans[pass_id] = planner.plan_batches(pass_id, intelligence)

                    batch_plan_path = self.config.output_dir / "batch_plan.json"
                    batch_plan_path.write_text(
                        json.dumps(
                            {pid: bp.to_dict() for pid, bp in batch_plans.items()},
                            indent=2,
                            sort_keys=True,
                        )
                        + "\n"
                    )

                logger.info("Building provider model catalog for routing...")
                try:
                    catalog_data = build_provider_model_catalog(self.config)
                    routing_plan = build_prescan_routing_plan(self.config, catalog_data, passes)
                    write_routing_plan(self.config.output_dir, routing_plan)
                    write_provider_catalog(self.config.output_dir, catalog_data)
                except Exception as exc:  # pragma: no cover - non-fatal guard
                    logger.warning("Provider routing failed (using defaults): %s", exc)
                    warnings.append(f"Provider routing failed: {exc}")

                logger.info("Running Grok passes: %s", ", ".join(passes))
                if self.config.batch_mode and batch_plans:
                    grok_results = self.grok_runner.run_passes_batched(
                        passes,
                        intelligence,
                        manifest,
                        batch_plans,
                        routing_plan=routing_plan,
                    )
                else:
                    grok_results = self.grok_runner.run_passes(
                        passes,
                        intelligence,
                        manifest,
                        routing_plan=routing_plan,
                    )
                intelligence["grok_passes"] = grok_results

            self.config.output_dir.mkdir(parents=True, exist_ok=True)
            intel_path = self.config.output_dir / "prescan_intelligence.json"
            manifest_path = self.config.output_dir / "corpus_manifest.json"

            intel_path.write_text(json.dumps(intelligence, indent=2, sort_keys=True) + "\n")
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

            duration = round(time.time() - start_time, 2)
            total_batches = sum(len(bp.batches) for bp in batch_plans.values()) if batch_plans else 0

            return PrescanResult(
                success=True,
                duration_seconds=duration,
                file_count=len(entries),
                code_files_analyzed=len(code_intel),
                intelligence_path=intel_path,
                manifest_path=manifest_path,
                warnings=warnings,
                batch_plan_path=batch_plan_path,
                batch_count=total_batches,
            )

        except Exception as exc:
            logger.error("Prescan failed: %s", exc, exc_info=True)
            return PrescanResult(
                success=False,
                duration_seconds=round(time.time() - start_time, 2),
                file_count=0,
                code_files_analyzed=0,
                errors=[str(exc)],
            )

        finally:
            try:
                self.config.output_dir.mkdir(parents=True, exist_ok=True)
                self.grok_runner.save_attempts()
            except Exception as exc:  # pragma: no cover - non-fatal guard
                logger.warning("Failed to save LLM attempts evidence (finally): %s", exc)

    def _collect_duplicate_summaries(self, entries: list[FileEntry]) -> dict[str, dict[str, Any]]:
        groups: dict[str, list[str]] = {}
        chains: dict[str, list[dict[str, Any]]] = {}

        for entry in entries:
            if entry.duplicate_group_id:
                groups.setdefault(entry.duplicate_group_id, []).append(entry.rel_path)
            if entry.version_chain_id:
                chains.setdefault(entry.version_chain_id, []).append(
                    {
                        "path": entry.rel_path,
                        "ordinal": entry.version_ordinal,
                        "is_latest": entry.is_latest_version,
                    }
                )

        return {"groups": groups, "chains": chains}

    def _build_intelligence_base(
        self,
        entries: list[FileEntry],
        code_intel: list[dict] | None = None,
    ) -> dict[str, Any]:
        included = [e for e in entries if e.include and not e.is_ghost]
        ghosts = [e for e in entries if e.is_ghost]

        by_class: dict[str, int] = {}
        for entry in entries:
            by_class[entry.authority_class] = by_class.get(entry.authority_class, 0) + 1

        by_ext: dict[str, int] = {}
        for entry in included:
            by_ext[entry.extension] = by_ext.get(entry.extension, 0) + 1

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
            },
        }

    def _get_lifecycle_dist(self, entries: list[FileEntry]) -> dict[str, int]:
        dist: dict[str, int] = {}
        for entry in entries:
            dist[entry.lifecycle_stage] = dist.get(entry.lifecycle_stage, 0) + 1
        return dist

    def _find_planned_features(self, entries: list[FileEntry]) -> dict[str, list[str]]:
        return {
            "proposed_adrs": [
                e.rel_path for e in entries if "ADR" in e.rel_path and e.lifecycle_stage == "stub"
            ],
            "stub_files": [e.rel_path for e in entries if e.lifecycle_stage == "stub"],
            "todo_files": [e.rel_path for e in entries if e.lifecycle_stage == "stale"],
            "draft_docs": [
                e.rel_path for e in entries if e.authority_class == "historical"
            ],
        }

    def _get_git_sha(self) -> str:
        try:
            return (
                subprocess.check_output(
                    ["git", "rev-parse", "HEAD"],
                    cwd=self.config.repo_root,
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )
        except Exception:
            return "unknown"
