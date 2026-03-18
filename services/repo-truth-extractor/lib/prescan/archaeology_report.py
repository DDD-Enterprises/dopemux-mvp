"""Feature archaeology report for deep mode prescan.

Synthesizes Grok discover-pass results with file metadata to surface
hidden features, ghost files worth restoring, and abandoned work.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from .models import FileEntry

logger = logging.getLogger(__name__)


class ArchaeologyReporter:
    """Generates a structured archaeology report from prescan data."""

    def __init__(
        self,
        entries: list[FileEntry],
        intelligence: dict,
        grok_results: dict,
    ):
        self.entries = entries
        self.intelligence = intelligence
        self.grok_results = grok_results
        self._entry_map = {e.rel_path: e for e in entries}

    def generate(self) -> dict:
        """Produce the archaeology report combining all sources."""
        discover = self.grok_results.get("discover", {})

        discovered_features = self._build_discovered_features(discover)
        ghost_worth = self._assess_ghosts(discover)

        worth_restoring = sum(1 for g in ghost_worth if g.get("worth_restoring"))
        abandoned = sum(
            1 for f in discovered_features if f.get("status") == "abandoned"
        )

        return {
            "discovered_features": discovered_features,
            "ghost_files_worth_restoring": ghost_worth,
            "summary": {
                "total_discovered": len(discovered_features),
                "worth_restoring": worth_restoring,
                "abandoned": abandoned,
            },
        }

    def _build_discovered_features(self, discover: dict) -> list[dict]:
        """Build feature list from hidden_features + rediscovery_candidates."""
        features: list[dict] = []
        seen_paths: set[str] = set()

        # Hidden features from Grok discover pass
        for hf in discover.get("hidden_features", []):
            path = hf.get("path", "")
            if path in seen_paths:
                continue
            seen_paths.add(path)

            entry = self._entry_map.get(path)
            status = self._infer_status(entry, hf)

            features.append({
                "name": hf.get("feature_name", path),
                "status": status,
                "source_paths": [path],
                "last_modified": entry.last_commit_date if entry else None,
                "recommendation": self._recommend(status, hf),
                "confidence": hf.get("confidence", 0.5),
                "extraction_phase": hf.get("extraction_phase", "X"),
            })

        # Rediscovery candidates
        for rc in discover.get("rediscovery_candidates", []):
            path = rc.get("path", "")
            if path in seen_paths:
                continue
            seen_paths.add(path)

            entry = self._entry_map.get(path)
            features.append({
                "name": path,
                "status": "documented_only",
                "source_paths": [path],
                "last_modified": entry.last_commit_date if entry else None,
                "recommendation": "reference",
                "confidence": 0.4,
                "insight": rc.get("insight", ""),
            })

        return features

    def _assess_ghosts(self, discover: dict) -> list[dict]:
        """Consolidate ghost file assessments."""
        results: list[dict] = []
        for ga in discover.get("ghost_assessments", []):
            results.append({
                "path": ga.get("path", ""),
                "worth_restoring": ga.get("worth_restoring", False),
                "reason": ga.get("reason", ""),
            })
        return results

    def _infer_status(self, entry: FileEntry | None, hf: dict) -> str:
        """Infer feature status from metadata."""
        if entry is None:
            return "abandoned"
        if entry.lifecycle_stage == "frozen":
            return "abandoned" if entry.days_since_modified and entry.days_since_modified > 365 else "partial"
        if entry.has_stub_methods:
            return "partial"
        if entry.is_draft_doc:
            return "documented_only"
        return "completed"

    def _recommend(self, status: str, hf: dict) -> str:
        """Recommend action based on status."""
        if status == "completed":
            return "reference"
        if status == "abandoned":
            return "archive"
        if status == "partial":
            return "restore"
        return "reference"
