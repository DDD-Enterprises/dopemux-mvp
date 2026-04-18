"""Token-aware batch planning for Grok prescan passes.

Groups files by authority class first, then splits large classes by
top-level directory.  Each batch stays under ``config.max_tokens_per_batch``
minus the per-pass system-prompt overhead.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from .models import FileEntry, PrescanConfig
from .token_counter import estimate_file_tokens, estimate_payload_overhead

logger = logging.getLogger(__name__)


@dataclass
class Batch:
    batch_id: str  # e.g. "dedup_canonical_0"
    pass_id: str
    file_paths: list[str] = field(default_factory=list)
    estimated_tokens: int = 0
    authority_classes: list[str] = field(default_factory=list)


@dataclass
class BatchPlan:
    pass_id: str
    batches: list[Batch] = field(default_factory=list)
    total_estimated_tokens: int = 0
    total_files: int = 0
    oversized_files: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "pass_id": self.pass_id,
            "batch_count": len(self.batches),
            "total_estimated_tokens": self.total_estimated_tokens,
            "total_files": self.total_files,
            "oversized_files_count": len(self.oversized_files),
            "batches": [
                {
                    "batch_id": b.batch_id,
                    "file_count": len(b.file_paths),
                    "estimated_tokens": b.estimated_tokens,
                    "authority_classes": b.authority_classes,
                }
                for b in self.batches
            ],
            "oversized_files": self.oversized_files,
        }


class BatchPlanner:
    """Plans token-aware batches for each Grok pass.

    Hybrid strategy:
    1. Group files by authority class
    2. Within each class, accumulate into batches up to the token budget
    3. Oversized files (> 90% of batch limit) are excluded from LLM batches
    """

    def __init__(
        self,
        config: PrescanConfig,
        entries: list[FileEntry] | None = None,
        manifest: list[dict] | None = None,
    ):
        self.config = config
        self.entries = entries or []
        self.manifest = manifest or []

        # Pre-index entries by rel_path
        self._entry_map: Dict[str, FileEntry] = {e.rel_path: e for e in self.entries}

        # Pre-index manifest by rel_path
        self._manifest_map: Dict[str, dict] = {
            m["rel_path"]: m for m in self.manifest if "rel_path" in m
        }

    def plan(
        self,
        passes: list[str],
        intelligence: dict,
        manifest: list[dict] | None = None,
    ) -> dict[str, BatchPlan]:
        if manifest is not None:
            self.manifest = manifest
            self._manifest_map = {
                m["rel_path"]: m for m in manifest if "rel_path" in m
            }
        return {
            pass_id: self.plan_batches(pass_id, intelligence)
            for pass_id in passes
        }

    def plan_batches(
        self,
        pass_id: str,
        intelligence: dict,
    ) -> BatchPlan:
        """Create a batch plan for a single pass.

        The plan respects ``config.max_tokens_per_batch`` minus the pass's
        system-prompt overhead.  Files that individually exceed 90% of the
        limit are logged in ``oversized_files`` and excluded from batches.
        """
        overhead = estimate_payload_overhead(pass_id)
        budget = self.config.max_tokens_per_batch - overhead

        # Gather files relevant to this pass
        relevant = self._files_for_pass(pass_id, intelligence)

        plan = BatchPlan(pass_id=pass_id)

        # Group by authority class
        by_class: Dict[str, list[str]] = {}
        for rel_path in relevant:
            entry = self._entry_map.get(rel_path)
            cls_name = entry.authority_class if entry else "unknown"
            by_class.setdefault(cls_name, []).append(rel_path)

        batch_idx = 0
        for cls_name in sorted(by_class.keys()):
            paths = by_class[cls_name]
            current = Batch(
                batch_id=f"{pass_id}_{cls_name}_{batch_idx}",
                pass_id=pass_id,
                authority_classes=[cls_name],
            )

            for rel_path in paths:
                entry = self._entry_map.get(rel_path)
                file_path = self.config.repo_root / rel_path
                tokens = estimate_file_tokens(
                    file_path,
                    chars_per_token=self.config.chars_per_token,
                )

                # Oversized file handling
                if tokens > budget * 0.9:
                    plan.oversized_files.append(
                        {"path": rel_path, "tokens": tokens, "reason": "exceeds_batch_limit"}
                    )
                    continue

                # Would this file push current batch over budget?
                if current.file_paths and (current.estimated_tokens + tokens > budget):
                    # Flush current batch
                    plan.batches.append(current)
                    plan.total_estimated_tokens += current.estimated_tokens
                    plan.total_files += len(current.file_paths)
                    batch_idx += 1
                    current = Batch(
                        batch_id=f"{pass_id}_{cls_name}_{batch_idx}",
                        pass_id=pass_id,
                        authority_classes=[cls_name],
                    )

                current.file_paths.append(rel_path)
                current.estimated_tokens += tokens

            # Flush remaining
            if current.file_paths:
                plan.batches.append(current)
                plan.total_estimated_tokens += current.estimated_tokens
                plan.total_files += len(current.file_paths)
                batch_idx += 1

        return plan

    def _files_for_pass(self, pass_id: str, intelligence: dict) -> list[str]:
        """Return the list of file paths relevant to a given pass."""
        if pass_id == "dedup":
            return self._dedup_files(intelligence)
        elif pass_id == "discover":
            return self._discover_files(intelligence)
        elif pass_id == "feasibility":
            return self._feasibility_files(intelligence)
        elif pass_id == "optimize":
            # Optimize pass uses summaries, not file content
            return []
        return []

    def _dedup_files(self, intelligence: dict) -> list[str]:
        paths: list[str] = []
        for _gid, group_paths in intelligence.get("duplicate_groups", {}).items():
            paths.extend(group_paths)
        for _cid, members in intelligence.get("version_chains", {}).items():
            for m in members:
                if m.get("path"):
                    paths.append(m["path"])
        return list(dict.fromkeys(paths))  # dedupe preserving order

    def _discover_files(self, intelligence: dict) -> list[str]:
        paths: list[str] = []
        for e in self.entries:
            if (
                getattr(e, "include", True)
                and not getattr(e, "is_ghost", False)
                and getattr(e, "authority_class", None) in ("historical", "canonical")
                and getattr(e, "lifecycle_stage", None) in ("frozen", "stale")
            ):
                paths.append(e.rel_path)
        return paths

    def _feasibility_files(self, intelligence: dict) -> list[str]:
        planned = intelligence.get("planned_features", {})
        paths: list[str] = []
        for key in ("proposed_adrs", "stub_files", "todo_files", "draft_docs"):
            paths.extend(planned.get(key, []))
        return list(dict.fromkeys(paths))
