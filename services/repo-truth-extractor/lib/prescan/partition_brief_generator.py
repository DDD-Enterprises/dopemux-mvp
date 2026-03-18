"""Aider-style structural context briefs for extraction partitions.

Each brief is a compact map showing dependency flow, ranked signatures,
and API surfaces — prepended to the LLM extraction prompt to give the
model structural awareness of the code it's about to process.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Set

from .token_counter import estimate_tokens

logger = logging.getLogger(__name__)


class PartitionBriefGenerator:
    """Generates per-partition context briefs from code intelligence.

    Each brief stays within a token budget (default 2000 tokens ≈ 8KB).
    """

    def __init__(self, code_report: Dict[str, Any], token_budget: int = 2000):
        self.report = code_report
        self.token_budget = token_budget
        self._pagerank = code_report.get("pagerank_scores", {})
        self._signatures = code_report.get("signature_index", {})
        self._entry_points = set(code_report.get("entry_points", []))
        self._hub_files = {
            h["rel_path"]: h
            for h in code_report.get("hub_files", [])
        }

    def generate_brief(self, phase_key: str, partition_files: List[str]) -> str:
        """Build context brief for one partition."""
        if not partition_files:
            return ""

        lines: List[str] = []
        file_set = set(partition_files)

        # Header
        hub = self._find_hub(partition_files)
        hub_label = f" | Hub: {hub}" if hub else ""
        lines.append("=== Partition Context ===")
        lines.append(
            f"Phase: {phase_key} | {len(partition_files)} files{hub_label}"
        )
        lines.append("")

        # Dependency flow (compact)
        flow = self._build_dependency_flow(partition_files)
        if flow:
            lines.append("Dependency Flow:")
            for line in flow:
                lines.append(f"  {line}")
            lines.append("")

        # Key signatures (ranked by PageRank)
        sig_lines = self._build_ranked_signatures(partition_files)
        if sig_lines:
            lines.append("Key Signatures (by importance):")
            lines.extend(sig_lines)
            lines.append("")

        # API surfaces
        api_summary = self._build_api_summary(partition_files)
        if api_summary:
            lines.append("API Surfaces:")
            for line in api_summary:
                lines.append(f"  {line}")

        brief = "\n".join(lines)

        # Trim to budget
        tokens = estimate_tokens(brief)
        if tokens > self.token_budget:
            # Truncate signatures section to fit
            while tokens > self.token_budget and sig_lines:
                sig_lines.pop()
                brief = "\n".join(lines[:lines.index("Key Signatures (by importance):") + 1] + sig_lines + [""])
                tokens = estimate_tokens(brief)

        return brief

    def generate_all_briefs(
        self, phase_partitions: Dict[str, List[List[str]]]
    ) -> Dict[str, List[str]]:
        """Generate briefs for all partitions across all phases."""
        result: Dict[str, List[str]] = {}
        for phase_key, partitions in phase_partitions.items():
            result[phase_key] = [
                self.generate_brief(phase_key, partition_files)
                for partition_files in partitions
            ]
        return result

    def _find_hub(self, files: List[str]) -> str | None:
        """Find the most important file in the partition."""
        best_rank = -1.0
        best_file = None
        for f in files:
            rank = self._pagerank.get(f, 0.0)
            if rank > best_rank:
                best_rank = rank
                best_file = f
        return best_file

    def _build_dependency_flow(self, files: List[str]) -> List[str]:
        """Build compact dependency flow lines."""
        # Simple: show entry points → their direct deps within partition
        flows: List[str] = []
        file_set = set(files)

        for f in files:
            if f in self._entry_points or f in self._hub_files:
                sigs = self._signatures.get(f, [])
                imported_names = [
                    s["name"] for s in sigs
                    if s.get("kind") == "function" and s.get("decorators")
                ]
                if imported_names:
                    name = Path(f).name
                    flows.append(f"{name} → {', '.join(imported_names[:5])}")

        return flows[:5]  # Limit flow lines

    def _build_ranked_signatures(self, files: List[str]) -> List[str]:
        """Build signature lines ranked by PageRank."""
        ranked = sorted(files, key=lambda f: self._pagerank.get(f, 0.0), reverse=True)
        lines: List[str] = []

        for f in ranked[:8]:  # Top 8 files
            pr = self._pagerank.get(f, 0.0)
            sigs = self._signatures.get(f, [])
            if not sigs:
                continue

            lines.append(f"  {f} [PageRank: {pr:.4f}]")
            for sig in sigs[:6]:  # Top 6 signatures per file
                prefix = "    "
                if sig.get("parent"):
                    prefix = "      "
                sig_text = sig.get("signature", sig.get("name", ""))
                lines.append(f"{prefix}{sig_text}")

        return lines

    def _build_api_summary(self, files: List[str]) -> List[str]:
        """Summarize API surfaces in the partition."""
        # Count surface types from signatures
        surface_counts: Dict[str, int] = {}
        for f in files:
            sigs = self._signatures.get(f, [])
            for sig in sigs:
                for dec in sig.get("decorators", []):
                    if "@click" in dec or "@typer" in dec:
                        surface_counts["cli"] = surface_counts.get("cli", 0) + 1
                    elif "@app." in dec or "@router." in dec:
                        surface_counts["http"] = surface_counts.get("http", 0) + 1
                    elif "@mcp" in dec or "@tool" in dec:
                        surface_counts["mcp"] = surface_counts.get("mcp", 0) + 1

        lines: List[str] = []
        for surface_type, count in sorted(surface_counts.items()):
            lines.append(f"@{surface_type}: {count} endpoints")
        return lines
