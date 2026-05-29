from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any

from .batch_planner import BatchPlanner
from .classifier import Classifier
from .code_intelligence_report import CodeIntelligenceBuilder
from .code_prescan import CodePrescan
from .corpus_walker import CorpusWalker
from .cost_estimator import CostEstimator
from .dependency_graph import DependencyGraph
from .duplicate_detector import DuplicateDetector
from .git_enricher import GitEnricher
from .grok_passes import GrokPassRunner
from .incremental_cache import IncrementalCodeCache
from .models import FileEntry, PrescanConfig, PrescanResult
from .provider_catalog import (
    NO_LIVE_LANE,
    build_prescan_routing_plan,
    build_provider_model_catalog,
    build_provider_readiness_matrix,
    write_live_lane_success_artifact,
    write_no_live_lane_artifact,
    write_provider_catalog,
    write_provider_readiness,
    write_routing_plan,
)
from ..intelligence_router import (
    PRESCAN_ARTIFACT_VERSION,
    build_prescan_source_identity,
)

logger = logging.getLogger(__name__)

PRESCAN_ARTIFACT_VERSION = "1.0"


def _stable_json_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class PrescanEngine:
    def __init__(self, config: PrescanConfig, limiter: Any | None = None):
        self.config = config
        self.walker = CorpusWalker(config)
        self.classifier = Classifier(config)
        self.git_enricher = GitEnricher(config)
        self.duplicate_detector = DuplicateDetector(config)
        self.code_prescan = CodePrescan(config)
        self.dep_graph = DependencyGraph()
        self.cost_estimator = CostEstimator(config)
        self.grok_runner = GrokPassRunner(config, limiter=limiter)

        # Backward-compatible aliases used across tests and older callers.
        self.enricher = self.git_enricher
        self.detector = self.duplicate_detector
        self.code_scanner = self.code_prescan

    def _log_progress(self, message: str, **fields: Any) -> None:
        if fields:
            details = " ".join(f"{key}={value}" for key, value in fields.items())
            logger.info("PRESCAN_PROGRESS %s %s", message, details)
            return
        logger.info("PRESCAN_PROGRESS %s", message)

    def _top_file_extensions(self, entries: list[FileEntry], limit: int = 3) -> str:
        counts: dict[str, int] = {}
        for entry in entries:
            if not entry.include:
                continue
            ext = entry.extension or "(no_ext)"
            counts[ext] = counts.get(ext, 0) + 1
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
        return ",".join(f"{ext}:{count}" for ext, count in ranked) if ranked else "none"

    def _count_code_languages(self, entries: list[FileEntry]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entry in entries:
            if entry.include and not entry.is_ghost and self._is_code_entry(entry):
                language = entry.extension.lstrip(".").lower() or "unknown"
                counts[language] = counts.get(language, 0) + 1
        return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))

    def _summarize_batch_plans(self, batch_plans: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for pass_id, plan in sorted(batch_plans.items()):
            oversized = list(getattr(plan, "oversized_files", []) or [])
            rows.append(
                {
                    "pass_id": str(pass_id),
                    "total_files": int(getattr(plan, "total_files", 0) or 0),
                    "batch_count": len(getattr(plan, "batches", []) or []),
                    "estimated_tokens": int(getattr(plan, "total_estimated_tokens", 0) or 0),
                    "oversized_files": len(oversized),
                    "oversized_examples": ",".join(
                        str(item.get("path") or "") for item in oversized[:3] if item.get("path")
                    )
                    or "none",
                }
            )
        return rows

    def _summarize_stage0_routes(self, stage0: dict[str, Any]) -> list[dict[str, Any]]:
        routing_plan = stage0.get("routing_plan") or {}
        selected_routes = routing_plan.get("selected_routes") or {}
        fallback_decisions = routing_plan.get("fallback_decisions") or {}
        rows: list[dict[str, Any]] = []
        for pass_id, route in sorted(selected_routes.items()):
            if not isinstance(route, dict):
                continue
            decisions = list(fallback_decisions.get(pass_id) or [])
            admitted = sum(1 for item in decisions if str(item.get("decision")) == "admitted")
            excluded = sum(1 for item in decisions if str(item.get("decision")) == "excluded")
            exclusion_reasons: dict[str, int] = {}
            for item in decisions:
                if str(item.get("decision")) != "excluded":
                    continue
                reason = str(item.get("reason") or "unknown")
                exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
            reason_summary = ",".join(
                f"{reason}:{count}"
                for reason, count in sorted(
                    exclusion_reasons.items(), key=lambda item: (-item[1], item[0])
                )[:3]
            ) or "none"
            rows.append(
                {
                    "pass_id": str(pass_id),
                    "provider": str(route.get("provider") or ""),
                    "model_id": str(route.get("model_id") or ""),
                    "selected_tier": str(route.get("selected_tier") or ""),
                    "tier_adjustment": str(route.get("tier_adjustment") or "exact"),
                    "admitted_fallbacks": admitted,
                    "excluded_fallbacks": excluded,
                    "exclusion_summary": reason_summary,
                }
            )
        return rows

    def run(self, passes: list[str] | None = None, incremental: bool = False) -> PrescanResult:
        start_time = time.time()
        warnings: list[str] = []
        errors: list[str] = []
        metadata: dict[str, Any] = {}
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        try:
            self._log_progress(
                "start",
                repo=self.config.repo_root,
                output=self.config.output_dir,
                incremental=bool(incremental),
            )
            self._log_progress("walk_corpus")
            entries = self.walker.walk()
            included_count = sum(1 for entry in entries if entry.include)
            self._log_progress(
                "walk_corpus_done",
                files=len(entries),
                included=included_count,
                excluded=len(entries) - included_count,
                top_extensions=self._top_file_extensions(entries),
            )

            self._log_progress("load_incremental_cache")
            cache = IncrementalCodeCache(self.config)
            cache_payload, fallback_reason, changed_files = self._load_incremental_cache(cache, incremental, warnings)
            self._log_progress(
                "incremental_cache_done",
                changed_files=len(changed_files or set()) if incremental else 0,
                fallback=bool(fallback_reason),
                fallback_reason=(fallback_reason or "none").replace(" ", "_"),
            )
            incremental_meta: dict[str, Any] = {
                "enabled": bool(incremental),
                "changed_files_count": len(changed_files or set()) if incremental else 0,
                "fallback_reason": fallback_reason,
            }

            self._log_progress("classify_files", files=len(entries))
            incremental_meta.update(self._classify(entries, cache, cache_payload, changed_files))
            self._log_progress(
                "classify_files_done",
                reused=incremental_meta.get("cached_classifications_reused", 0),
                reclassified=incremental_meta.get("reclassified_files", 0),
            )
            self._log_progress("git_enrichment", enabled=bool(self.config.enable_git_enrichment))
            incremental_meta.update(self._enrich(entries, warnings, cache, cache_payload, changed_files))
            self._log_progress(
                "git_enrichment_done",
                reused=incremental_meta.get("cached_git_enrichment_reused", 0),
                recomputed=incremental_meta.get("git_enrichment_recomputed", 0),
            )
            self._log_progress("duplicate_analysis", files=len(entries))
            duplicates = self._detect_duplicates(entries, cache, cache_payload, changed_files)
            incremental_meta.update(duplicates["metadata"])
            self._log_progress(
                "duplicate_analysis_done",
                groups=len(duplicates["groups"]),
                version_chains=len(duplicates["chains"]),
            )

            manifest = [entry.to_dict() for entry in entries]
            code_entries = sum(
                1
                for entry in entries
                if entry.include and not entry.is_ghost and self._is_code_entry(entry)
            )
            self._log_progress(
                "code_intelligence",
                enabled=bool(self.config.enable_code_prescan),
                files=code_entries,
            )
            code_intel, code_incremental_meta = self._analyze_code(
                entries,
                manifest,
                cache,
                cache_payload,
                changed_files,
            )
            incremental_meta.update(code_incremental_meta)
            self._log_progress(
                "code_intelligence_done",
                analyzed=len(code_intel),
                reused=incremental_meta.get("cached_code_analysis_reused", 0),
                reanalyzed=incremental_meta.get("reanalyzed_code_files", 0),
                languages=",".join(
                    f"{lang}:{count}"
                    for lang, count in self._count_code_languages(entries).items()
                )
                or "none",
            )
            incremental_meta["removed_cache_entries"] = cache.removed_entry_count(
                cache_payload,
                {entry.rel_path for entry in entries},
            )
            metadata["incremental"] = incremental_meta
            current_git_sha = self._get_git_sha()
            self._log_progress("write_incremental_cache")
            cache.write(entries, code_intel, current_git_sha)

            self._log_progress("build_dependency_graph", files=len(code_intel))
            self.dep_graph = DependencyGraph()
            self.dep_graph.build_from_code_intelligence(code_intel, manifest)

            self._log_progress("build_intelligence")
            intelligence = self._build_intelligence_base(entries, code_intel)
            source_identity = build_prescan_source_identity(
                self.config.repo_root,
                self.config.repo_root,
                git_sha=current_git_sha,
                entries=entries,
                artifact_root=self.config.output_dir,
                prescan_mode="local_prescan",
            )
            metadata["source_identity"] = source_identity
            intelligence["prescan_artifact_version"] = PRESCAN_ARTIFACT_VERSION
            intelligence["source_root"] = source_identity["source_root"]
            intelligence["git_sha"] = source_identity["git_sha"]
            intelligence["corpus_manifest_hash"] = source_identity["corpus_manifest_hash"]
            intelligence["source_identity"] = source_identity
            intelligence["duplicate_groups"] = duplicates["groups"]
            intelligence["version_chains"] = duplicates["chains"]
            intelligence["version_chain_count"] = len(duplicates["chains"])

            code_graph_path: Path | None = None
            code_report_path: Path | None = None
            if self.config.enable_code_prescan:
                self._log_progress("write_code_artifacts")
                code_graph_path = self._write_code_graph()
                code_report_path = self._write_code_report(entries, manifest)

            batch_plans: dict[str, Any] = {}
            batch_plan_path: Path | None = None
            if passes:
                self._log_progress("plan_llm_passes", passes=",".join(passes))
                batch_plans, batch_plan_path = self._plan_batches(passes, entries, manifest, intelligence)
                self._log_progress(
                    "plan_llm_passes_done",
                    batches=sum(len(plan.batches) for plan in batch_plans.values()),
                    tokens=sum(int(getattr(plan, "total_estimated_tokens", 0) or 0) for plan in batch_plans.values()),
                )
                for row in self._summarize_batch_plans(batch_plans):
                    self._log_progress(
                        "plan_llm_pass_detail",
                        pass_id=row["pass_id"],
                        files=row["total_files"],
                        batches=row["batch_count"],
                        tokens=row["estimated_tokens"],
                        oversized=row["oversized_files"],
                        oversized_examples=row["oversized_examples"],
                    )
                self._log_progress("provider_readiness", passes=",".join(passes))
                stage0 = self._run_stage0(passes)
                metadata["stage0"] = {
                    "catalog_status": "PASS",
                    "provider_readiness_status": stage0["readiness"]["status"],
                    "routing_plan_status": stage0["routing_plan"]["status"],
                    "selected_live_routes": stage0["routing_plan"].get("selected_routes", {}),
                }
                self._log_progress(
                    "provider_readiness_done",
                    readiness=stage0["readiness"]["status"],
                    routing=stage0["routing_plan"]["status"],
                )
                for row in self._summarize_stage0_routes(stage0):
                    self._log_progress(
                        "provider_readiness_detail",
                        pass_id=row["pass_id"],
                        route=f"{row['provider']}/{row['model_id']}",
                        tier=row["selected_tier"],
                        adjustment=row["tier_adjustment"],
                        admitted_fallbacks=row["admitted_fallbacks"],
                        excluded_fallbacks=row["excluded_fallbacks"],
                        exclusion_summary=row["exclusion_summary"],
                    )
                if stage0["routing_plan"]["status"] == NO_LIVE_LANE:
                    self._log_progress("halt_no_live_lane")
                    write_no_live_lane_artifact(self.config.output_dir, stage0["routing_plan"])
                    errors.append("No executable live prescan lane survived Stage 0 readiness gating.")
                    return PrescanResult(
                        success=False,
                        duration_seconds=round(time.time() - start_time, 2),
                        file_count=len(entries),
                        included_count=sum(1 for entry in entries if entry.include),
                        code_files_analyzed=len(code_intel),
                        intelligence_path=self._write_json("prescan_intelligence.json", intelligence),
                        manifest_path=self._write_json("corpus_manifest.json", manifest),
                        code_graph_path=code_graph_path,
                        code_report_path=code_report_path,
                        batch_plan_path=batch_plan_path,
                        batch_count=sum(len(plan.batches) for plan in batch_plans.values()),
                        warnings=warnings,
                        errors=errors,
                        metadata=metadata,
                    )
                if self.config.allow_online_llm:
                    write_live_lane_success_artifact(self.config.output_dir, stage0["routing_plan"])
                if self.config.allow_online_llm:
                    self._log_progress(
                        "run_online_passes",
                        mode="batch" if self.config.batch_mode and batch_plans else "single",
                    )
                    if self.config.batch_mode and batch_plans:
                        grok_results = self.grok_runner.run_passes_batched(
                            passes,
                            intelligence,
                            manifest,
                            batch_plans,
                            routing_plan=stage0["routing_plan"],
                        )
                    else:
                        grok_results = self.grok_runner.run_passes(
                            passes,
                            intelligence,
                            manifest,
                            routing_plan=stage0["routing_plan"],
                        )
                    intelligence["grok_passes"] = grok_results
                    self._log_progress("run_online_passes_done", results=len(grok_results))
                else:
                    self._log_progress("online_passes_skipped", reason="online_llm_not_authorized")

            self._log_progress("write_prescan_artifacts")
            intelligence_path = self._write_json("prescan_intelligence.json", intelligence)
            manifest_path = self._write_json("corpus_manifest.json", manifest)
            self._log_progress(
                "complete",
                files=len(entries),
                included=sum(1 for entry in entries if entry.include),
                code_files=len(code_intel),
                seconds=round(time.time() - start_time, 2),
            )
            return PrescanResult(
                success=True,
                duration_seconds=round(time.time() - start_time, 2),
                file_count=len(entries),
                included_count=sum(1 for entry in entries if entry.include),
                code_files_analyzed=len(code_intel),
                intelligence_path=intelligence_path,
                manifest_path=manifest_path,
                code_graph_path=code_graph_path,
                code_report_path=code_report_path,
                batch_plan_path=batch_plan_path,
                batch_count=sum(len(plan.batches) for plan in batch_plans.values()),
                warnings=warnings,
                errors=errors,
                metadata=metadata,
            )
        except Exception as exc:
            logger.error("Prescan failed: %s", exc, exc_info=True)
            return PrescanResult(
                success=False,
                duration_seconds=round(time.time() - start_time, 2),
                errors=[str(exc)],
                warnings=warnings,
                metadata=metadata,
            )
        finally:
            try:
                self.grok_runner.save_attempts()
            except Exception as exc:
                logger.warning("Failed to persist prescan LLM attempts: %s", exc)

    def _load_incremental_cache(
        self,
        cache: IncrementalCodeCache,
        incremental: bool,
        warnings: list[str],
    ) -> tuple[dict[str, Any] | None, str | None, set[str] | None]:
        if not incremental:
            return None, None, None

        cache_payload, fallback_reason = cache.load()
        if fallback_reason:
            warnings.append(fallback_reason)
            return None, fallback_reason, None
        return cache_payload, None, set(self._get_changed_files())

    def _classify(
        self,
        entries: list[FileEntry],
        cache: IncrementalCodeCache,
        cache_payload: dict[str, Any] | None,
        changed_files: set[str] | None,
    ) -> dict[str, int]:
        reused = 0
        reclassified = 0
        if hasattr(self.classifier, "classify_file"):
            for entry in entries:
                cached = cache.reusable_entry(cache_payload, entry, changed_files)
                if cached is not None and cache.apply_cached_classification(entry, cached):
                    reused += 1
                    continue
                entry.authority_class = self.classifier.classify_file(entry)
                reclassified += 1
            return {
                "cached_classifications_reused": reused,
                "reclassified_files": reclassified,
            }

        if cache.can_reuse_corpus_wide_outputs(cache_payload, entries, changed_files):
            for entry in entries:
                cached = cache.reusable_entry(cache_payload, entry, changed_files)
                if cached is not None and cache.apply_cached_classification(entry, cached):
                    reused += 1
            if reused == len(entries):
                return {
                    "cached_classifications_reused": reused,
                    "reclassified_files": 0,
                }

        if hasattr(self.classifier, "classify_all"):
            self.classifier.classify_all(entries)
            return {
                "cached_classifications_reused": 0,
                "reclassified_files": len(entries),
            }
        if hasattr(self.classifier, "classify"):
            classified = self.classifier.classify(entries)
            if isinstance(classified, list):
                return {
                    "cached_classifications_reused": 0,
                    "reclassified_files": len(entries),
                }
        raise AttributeError("Prescan classifier does not expose classify_all or classify")

    def _enrich(
        self,
        entries: list[FileEntry],
        warnings: list[str],
        cache: IncrementalCodeCache,
        cache_payload: dict[str, Any] | None,
        changed_files: set[str] | None,
    ) -> dict[str, int]:
        if not self.config.enable_git_enrichment:
            return {
                "cached_git_enrichment_reused": 0,
                "git_enrichment_recomputed": 0,
            }
        if cache.can_reuse_corpus_wide_outputs(cache_payload, entries, changed_files):
            reused = 0
            for entry in entries:
                cached = cache.reusable_entry(cache_payload, entry, changed_files)
                if cached is not None and cache.apply_cached_git_enrichment(entry, cached):
                    reused += 1
            if reused == len(entries):
                return {
                    "cached_git_enrichment_reused": reused,
                    "git_enrichment_recomputed": 0,
                }
        try:
            self.git_enricher.enrich(entries)
            return {
                "cached_git_enrichment_reused": 0,
                "git_enrichment_recomputed": len(entries),
            }
        except Exception as exc:
            warnings.append(f"Git enrichment failed: {exc}")
            return {
                "cached_git_enrichment_reused": 0,
                "git_enrichment_recomputed": 0,
            }

    def _detect_duplicates(
        self,
        entries: list[FileEntry],
        cache: IncrementalCodeCache,
        cache_payload: dict[str, Any] | None,
        changed_files: set[str] | None,
    ) -> dict[str, Any]:
        duplicate_groups: dict[str, list[str]] = {}
        version_chains: dict[str, list[dict[str, Any]]] = {}
        duplicate_detection_recomputed = 0

        if cache.can_reuse_corpus_wide_outputs(cache_payload, entries, changed_files):
            reused = 0
            for entry in entries:
                cached = cache.reusable_entry(cache_payload, entry, changed_files)
                if cached is not None and cache.apply_cached_duplicate_state(entry, cached):
                    reused += 1
            if reused == len(entries):
                return {
                    "groups": self._duplicate_groups_from_entries(entries),
                    "chains": self._version_chains_from_entries(entries),
                    "metadata": {
                        "cached_duplicate_detection_reused": reused,
                        "duplicate_detection_recomputed": 0,
                    },
                }

        duplicate_detector = self.duplicate_detector
        if hasattr(duplicate_detector, "detect_duplicates"):
            duplicate_detector.detect_duplicates(entries)
            duplicate_detector.detect_version_chains(entries)
            duplicate_detection_recomputed = len(entries)
            duplicate_groups = self._duplicate_groups_from_entries(entries)
            version_chains = self._version_chains_from_entries(entries)
        elif hasattr(duplicate_detector, "detect"):
            result = duplicate_detector.detect(entries)
            if isinstance(result, dict):
                duplicate_groups = dict(result.get("groups") or {})
                version_chains = dict(result.get("chains") or {})
            duplicate_detection_recomputed = len(entries)

        ordered_groups = {
            group_id: sorted(paths)
            for group_id, paths in sorted(duplicate_groups.items())
        }
        ordered_chains = {
            chain_id: sorted(
                members,
                key=lambda item: (int(item.get("ordinal") or 0), str(item.get("path") or "")),
            )
            for chain_id, members in sorted(version_chains.items())
        }
        return {
            "groups": ordered_groups,
            "chains": ordered_chains,
            "metadata": {
                "cached_duplicate_detection_reused": 0,
                "duplicate_detection_recomputed": duplicate_detection_recomputed,
            },
        }

    def _duplicate_groups_from_entries(self, entries: list[FileEntry]) -> dict[str, list[str]]:
        duplicate_groups: dict[str, list[str]] = {}
        for entry in entries:
            if entry.duplicate_group_id:
                duplicate_groups.setdefault(entry.duplicate_group_id, []).append(entry.rel_path)
        return duplicate_groups

    def _version_chains_from_entries(self, entries: list[FileEntry]) -> dict[str, list[dict[str, Any]]]:
        version_chains: dict[str, list[dict[str, Any]]] = {}
        for entry in entries:
            if entry.version_chain_id:
                version_chains.setdefault(entry.version_chain_id, []).append(
                    {
                        "path": entry.rel_path,
                        "ordinal": entry.version_ordinal,
                        "is_latest": entry.is_latest_version,
                    }
                )
        return version_chains

    def _is_code_entry(self, entry: FileEntry) -> bool:
        language = entry.extension.lstrip(".").lower()
        if language in {"py", "python"}:
            return "python" in self.config.code_languages or "py" in self.config.code_languages
        if language in {"js", "jsx", "javascript"}:
            return "javascript" in self.config.code_languages or "js" in self.config.code_languages
        if language in {"ts", "tsx", "typescript"}:
            return "typescript" in self.config.code_languages or "ts" in self.config.code_languages
        return False

    def _analyze_code(
        self,
        entries: list[FileEntry],
        manifest: list[dict[str, Any]],
        cache: IncrementalCodeCache,
        cache_payload: dict[str, Any] | None,
        changed_files: set[str] | None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if not self.config.enable_code_prescan:
            return [], {
                "cached_code_analysis_reused": 0,
                "reanalyzed_code_files": 0,
            }

        code_entries = [entry for entry in entries if entry.include and not entry.is_ghost and self._is_code_entry(entry)]
        reused = 0
        reanalyzed = 0
        code_intel: list[dict[str, Any]] = []
        for entry in code_entries:
            cached = cache.reusable_analysis(cache_payload, entry, changed_files)
            if cached is not None:
                reused += 1
                code_intel.append(cache.apply_cached_metrics(entry, cached))
                continue
            analysis = self.code_prescan.analyze_file(entry, self.config.repo_root)
            if analysis:
                code_intel.append(analysis)
            reanalyzed += 1

        code_intel.sort(key=lambda item: str(item.get("rel_path") or ""))
        return code_intel, {
            "cached_code_analysis_reused": reused,
            "reanalyzed_code_files": reanalyzed,
        }

    def _plan_batches(
        self,
        passes: list[str],
        entries: list[FileEntry],
        manifest: list[dict[str, Any]],
        intelligence: dict[str, Any],
    ) -> tuple[dict[str, Any], Path]:
        planner = BatchPlanner(self.config, entries, manifest)
        batch_plans = {
            pass_id: planner.plan_batches(pass_id, intelligence)
            for pass_id in passes
            if pass_id
        }
        path = self.config.output_dir / "batch_plan.json"
        path.write_text(
            json.dumps({pass_id: plan.to_dict() for pass_id, plan in batch_plans.items()}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return batch_plans, path

    def _run_stage0(self, passes: list[str]) -> dict[str, Any]:
        catalog = build_provider_model_catalog(self.config)
        readiness = build_provider_readiness_matrix(self.config, catalog)
        routing_plan = build_prescan_routing_plan(self.config, catalog, readiness, passes)
        write_provider_catalog(self.config.output_dir, catalog)
        write_provider_readiness(self.config.output_dir, readiness)
        write_routing_plan(self.config.output_dir, routing_plan)
        return {
            "catalog": catalog,
            "readiness": readiness,
            "routing_plan": routing_plan,
        }

    def _write_code_graph(self) -> Path:
        payload = {
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "nodes": sorted(self.dep_graph.nodes),
            "edges": [
                {"source": source, "target": target}
                for source, target in sorted(self.dep_graph.edges)
            ],
        }
        return self._write_json("code_graph.json", payload)

    def _write_code_report(self, entries: list[FileEntry], manifest: list[dict[str, Any]]) -> Path:
        builder = CodeIntelligenceBuilder(self.code_prescan, self.dep_graph, entries, manifest)
        report = builder.build(self.config.repo_root)
        return self._write_json("code_intelligence_report.json", report)

    def _write_json(self, filename: str, payload: Any) -> Path:
        path = self.config.output_dir / filename
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def _build_intelligence_base(self, entries: list[FileEntry], code_intel: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        included = [entry for entry in entries if entry.include and not entry.is_ghost]
        ghosts = [entry for entry in entries if entry.is_ghost]
        manifest = [entry.to_dict() for entry in entries]
        by_class: dict[str, int] = {}
        for entry in entries:
            by_class[entry.authority_class] = by_class.get(entry.authority_class, 0) + 1
        by_ext: dict[str, int] = {}
        for entry in included:
            by_ext[entry.extension] = by_ext.get(entry.extension, 0) + 1

        version_chain_count = len({entry.version_chain_id for entry in entries if entry.version_chain_id})
        compression_potential_files = sum(1 for entry in entries if entry.is_duplicate or (entry.version_chain_id and not entry.is_latest_version))
        return {
            "version": "1.0",
            "prescan_artifact_version": PRESCAN_ARTIFACT_VERSION,
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "repo_root": str(self.config.repo_root.resolve()),
            "source_root": str(self.config.repo_root.resolve()),
            "git_sha": self._get_git_sha(),
            "corpus_manifest_hash": _stable_json_hash(manifest),
            "corpus_summary": {
                "total_files": len(entries),
                "included_files": len(included),
                "ghost_files": len(ghosts),
                "by_class": by_class,
                "by_extension": by_ext,
                # S3-06: canonical key is total_included_size_bytes (matches schemas.py
                # and IntelligenceRouter.estimate_token_savings). Emitting total_size_bytes
                # here made the router read 0 and report 0% savings unconditionally.
                "total_included_size_bytes": sum(entry.size_bytes for entry in included),
                "corpus_health_score": 100,
            },
            "lifecycle_distribution": self._get_lifecycle_dist(entries),
            "planned_features": self._find_planned_features(entries),
            "ghost_files": [
                {
                    "path": ghost.rel_path,
                    "deleted_at_sha": ghost.deleted_at_sha,
                    "deleted_date": ghost.deleted_date,
                    "recovery_source": ghost.recovery_source or "unknown",
                }
                for ghost in sorted(ghosts, key=lambda item: item.rel_path)
            ],
            "code_intelligence": {
                "analyzed_files": len(code_intel or []),
                "files": code_intel or [],
            },
            "compression_potential_files": compression_potential_files,
            "version_chain_count": version_chain_count,
            "extraction_hints": {
                "skip_duplicates": sorted(entry.rel_path for entry in entries if entry.is_duplicate),
                "compression_candidates": sorted(
                    entry.rel_path
                    for entry in entries
                    if entry.is_duplicate or (entry.version_chain_id and not entry.is_latest_version)
                ),
            },
        }

    def _get_lifecycle_dist(self, entries: list[FileEntry]) -> dict[str, int]:
        dist: dict[str, int] = {}
        for entry in entries:
            dist[entry.lifecycle_stage] = dist.get(entry.lifecycle_stage, 0) + 1
        return dist

    def _find_planned_features(self, entries: list[FileEntry]) -> dict[str, list[str]]:
        return {
            "proposed_adrs": sorted(entry.rel_path for entry in entries if entry.is_proposed_adr),
            "stub_files": sorted(entry.rel_path for entry in entries if entry.has_stub_methods),
            "todo_files": sorted(entry.rel_path for entry in entries if entry.has_todo_markers),
            "draft_docs": sorted(entry.rel_path for entry in entries if entry.is_draft_doc),
        }

    def _get_changed_files(self) -> set[str]:
        baseline = str(self.config.incremental_baseline or "HEAD")
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", baseline, "--"],
                cwd=self.config.repo_root,
                text=True,
                capture_output=True,
                check=False,
            )
        except OSError:
            return set()
        if result.returncode != 0:
            return set()
        return {line.strip() for line in result.stdout.splitlines() if line.strip()}

    def _get_git_sha(self) -> str:
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=self.config.repo_root,
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except Exception:
            return "unknown"
