from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

from .models import FileEntry, PrescanConfig


CACHE_VERSION = "PRESCAN_INCREMENTAL_CACHE_V1"
ANALYZER_FILES = (
    "engine.py",
    "code_prescan.py",
    "dependency_graph.py",
    "code_intelligence_report.py",
)


class IncrementalCodeCache:
    def __init__(self, config: PrescanConfig):
        self.config = config
        self.cache_path = self.config.output_dir / ".cache" / "prescan_incremental_cache.json"

    def load(self) -> tuple[dict[str, Any] | None, str | None]:
        if not self.cache_path.exists():
            return None, "Incremental cache missing; running explicit full recompute and regenerating cache."

        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            return None, (
                f"Incremental cache unreadable ({exc}); running explicit full recompute and regenerating cache."
            )

        if payload.get("version") != CACHE_VERSION:
            return None, "Incremental cache version mismatch; running explicit full recompute and regenerating cache."
        if payload.get("config_fingerprint") != self.config_fingerprint():
            return None, "Incremental cache config fingerprint mismatch; running explicit full recompute and regenerating cache."
        if payload.get("analyzer_fingerprint") != self.analyzer_fingerprint():
            return None, "Incremental cache analyzer fingerprint mismatch; running explicit full recompute and regenerating cache."

        files = payload.get("files")
        if not isinstance(files, dict):
            return None, "Incremental cache file payload invalid; running explicit full recompute and regenerating cache."

        return payload, None

    def write(self, entries: list[FileEntry], code_intel: list[dict[str, Any]], git_sha: str) -> None:
        intel_by_path = {item["rel_path"]: item for item in code_intel if item.get("rel_path")}
        files: dict[str, Any] = {}
        for entry in sorted(entries, key=lambda item: item.rel_path):
            if entry.rel_path not in intel_by_path:
                continue
            files[entry.rel_path] = {
                "content_hash": entry.content_hash,
                "code_analysis": intel_by_path[entry.rel_path],
                "entry_metrics": {
                    "function_count": entry.function_count,
                    "class_count": entry.class_count,
                    "import_count": entry.import_count,
                    "docstring_coverage": entry.docstring_coverage,
                    "complexity_score": entry.complexity_score,
                },
            }

        payload = {
            "version": CACHE_VERSION,
            "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "repo_root": str(self.config.repo_root),
            "baseline_git_sha": git_sha,
            "config_fingerprint": self.config_fingerprint(),
            "analyzer_fingerprint": self.analyzer_fingerprint(),
            "files": files,
        }

        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def reusable_analysis(
        self,
        payload: dict[str, Any] | None,
        entry: FileEntry,
        changed_files: set[str] | None,
    ) -> dict[str, Any] | None:
        if payload is None or changed_files is None:
            return None
        if entry.rel_path in changed_files:
            return None
        cached = payload.get("files", {}).get(entry.rel_path)
        if not isinstance(cached, dict):
            return None
        if cached.get("content_hash") != entry.content_hash:
            return None
        code_analysis = cached.get("code_analysis")
        entry_metrics = cached.get("entry_metrics")
        if not isinstance(code_analysis, dict) or not isinstance(entry_metrics, dict):
            return None
        return cached

    def apply_cached_metrics(self, entry: FileEntry, cached: dict[str, Any]) -> dict[str, Any]:
        metrics = cached.get("entry_metrics", {})
        entry.function_count = int(metrics.get("function_count", 0))
        entry.class_count = int(metrics.get("class_count", 0))
        entry.import_count = int(metrics.get("import_count", 0))
        entry.docstring_coverage = float(metrics.get("docstring_coverage", 0.0))
        entry.complexity_score = float(metrics.get("complexity_score", 0.0))
        return cached["code_analysis"]

    def config_fingerprint(self) -> str:
        payload = {
            "batch_mode": self.config.batch_mode,
            "chars_per_token": self.config.chars_per_token,
            "code_languages": list(self.config.code_languages),
            "deep_mode": self.config.deep_mode,
            "enable_code_prescan": self.config.enable_code_prescan,
            "enable_git_enrichment": self.config.enable_git_enrichment,
            "exclude_globs": list(self.config.exclude_globs),
            "include_globs": list(self.config.include_globs),
            "large_json_threshold": self.config.large_json_threshold,
            "max_corpus_size": self.config.max_corpus_size,
            "max_file_size": self.config.max_file_size,
        }
        return self._stable_hash(payload)

    def analyzer_fingerprint(self) -> str:
        root = Path(__file__).resolve().parent
        hasher = hashlib.sha256()
        for name in ANALYZER_FILES:
            path = root / name
            hasher.update(name.encode("utf-8"))
            hasher.update(path.read_bytes())
        return hasher.hexdigest()

    def _stable_hash(self, payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
