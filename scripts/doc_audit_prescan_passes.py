#!/usr/bin/env python3
"""
Grok 420 multi-pass pre-extraction intelligence for dopemux docs audit.

Reads prescan_intelligence.json + corpus_manifest.json and runs up to 4
optional Grok passes, each building on the previous:

  Pass 2: DEDUP    — near-duplicate detection + version chain compression
  Pass 3: DISCOVER — hidden features, drift signals, ghost file assessment
  Pass 4: FEASIBILITY — planned feature GSP feasibility analysis
  Pass 5: OPTIMIZE — extraction optimizer (routing, cost, compression plan)

Usage:
  python scripts/doc_audit_prescan_passes.py \\
      --passes dedup,discover,feasibility,optimize \\
      [--prescan-dir extraction/prescan] \\
      [--model grok-4.20-beta-0309-non-reasoning]

Cost guide (approximate, Grok 420):
  dedup:       ~$0.02–0.05  (compressed version chain payloads)
  discover:    ~$0.03–0.08  (historical + canonical files)
  feasibility: ~$0.03–0.07  (ADRs, stubs, TODO files)
  optimize:    ~$0.02–0.04  (intelligence summary only)
  full sweep:  ~$0.10–0.24  total
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

XAI_BASE_URL = "https://api.x.ai/v1"
DEFAULT_MODEL = "grok-4.20-beta-0309-non-reasoning"
MAX_PREVIEW_BYTES = 6144
MAX_PREVIEW_LINES = 150

# ─── Pass Registry ───────────────────────────────────────────────────

PASS_IDS = ("dedup", "discover", "feasibility", "optimize")

PASS_DESCRIPTIONS = {
    "dedup": "Near-duplicate detection + version chain compression summaries",
    "discover": "Hidden feature archaeology, drift signals, ghost assessment",
    "feasibility": "Planned feature GSP feasibility analysis",
    "optimize": "Extraction routing, cost, and compression plan",
}

# ─── System Prompts ──────────────────────────────────────────────────

_DEDUP_SYSTEM_PROMPT = """\
You are a documentation deduplication analyst for a software repository.
You receive groups of files that are exact or near-duplicates (by SHA256 or
filename version pattern). Your job is to:

1. Confirm or reject each duplicate group as a true semantic duplicate.
2. For version chains (e.g., doc.md, doc-v2.md, doc-v3.md), produce a
   compressed evolution summary capturing:
   - What changed between versions (key additions/removals/pivots)
   - The original intent and how it evolved
   - Whether the latest supersedes all prior versions
3. Flag any pairs that appear duplicate but contain divergent intent.

Return valid JSON:
{
  "duplicate_assessments": [
    {
      "group_id": "abc12345",
      "confirmed_duplicate": true,
      "canonical_path": "path/to/canonical.md",
      "superseded_paths": ["path/to/old.md"],
      "confidence": 0.0-1.0,
      "reasoning": "max 60 words"
    }
  ],
  "version_chain_summaries": [
    {
      "chain_id": "xyz98765",
      "base_topic": "brief topic name",
      "evolution_narrative": "max 150 words capturing intent evolution",
      "latest_path": "path/to/latest.md",
      "superseded_paths": ["path/to/v1.md", "path/to/v2.md"],
      "key_changes": ["feature added in v2", "scope narrowed in v3"]
    }
  ],
  "divergent_pairs": [
    {
      "paths": ["a.md", "b.md"],
      "reason": "despite similar title, these cover different systems"
    }
  ]
}
"""

_DISCOVER_SYSTEM_PROMPT = """\
You are a technical archaeology analyst for a software repository.
You receive documentation files with git metadata (lifecycle stage, commit
history, churn score). Your job is to surface:

1. Hidden features: functionality described in docs but not obviously exposed
   in the main README or CLI help.
2. Drift signals: documentation that describes planned/aspirational behavior
   that may not match the current codebase (stale claims, version mismatches,
   future-tense descriptions presented as present-tense).
3. Ghost file assessment: for deleted files recovered from git history, assess
   whether their content is worth restoring or referencing.
4. Rediscovery candidates: frozen docs (>1 year unchanged) that may contain
   valuable ideas worth surfacing in a new context.

Return valid JSON:
{
  "hidden_features": [
    {
      "path": "doc/path.md",
      "feature_name": "brief name",
      "description": "max 80 words",
      "confidence": 0.0-1.0,
      "extraction_phase": "D|X|T"
    }
  ],
  "drift_signals": [
    {
      "path": "doc/path.md",
      "claim": "specific claim that may be stale",
      "drift_type": "version_mismatch|future_as_present|missing_impl",
      "severity": "high|medium|low"
    }
  ],
  "ghost_assessments": [
    {
      "path": "deleted/file.md",
      "worth_restoring": true,
      "reason": "max 50 words"
    }
  ],
  "rediscovery_candidates": [
    {
      "path": "old/frozen/doc.md",
      "insight": "max 80 words on what's worth surfacing"
    }
  ]
}
"""

_FEASIBILITY_SYSTEM_PROMPT = """\
You are a software feasibility analyst. You receive:
- Proposed ADR files (architectural decisions not yet implemented)
- Files with stub methods (raise NotImplementedError)
- Files with TODO/FIXME markers
- Draft documentation for planned features

For each planned feature, assess:
1. Implementation status (stub/planned/partial/blocked)
2. Code foundation score (0.0-1.0): how much infrastructure already exists?
3. Estimated effort (low/medium/high/xlarge)
4. Risk level (low/medium/high)
5. Key dependencies (other features/services it needs)
6. Quick-win potential (can it be done in <1 day with existing scaffolding?)

Return valid JSON:
{
  "planned_features": [
    {
      "path": "docs/90-adr/ADR-XXX.md",
      "feature_name": "brief name",
      "status": "stub|planned|partial|blocked",
      "foundation_score": 0.0-1.0,
      "effort": "low|medium|high|xlarge",
      "risk": "low|medium|high",
      "dependencies": ["service-name", "feature-name"],
      "quick_win": true,
      "reasoning": "max 80 words"
    }
  ],
  "implementation_blockers": [
    {
      "feature": "feature name",
      "blocker": "description of what's missing"
    }
  ],
  "quick_wins": ["list of paths/features that are quick wins"],
  "feasibility_summary": "max 150 word executive summary"
}
"""

_OPTIMIZE_SYSTEM_PROMPT = """\
You are an extraction cost optimizer for a repository knowledge extraction run.
You receive the full intelligence summary from all prior passes. Your job is to
produce an optimal extraction plan that:

1. Routes each file to the most appropriate extraction phase (D/C/X/T/etc.)
2. Identifies files that can be SKIPPED entirely (exact duplicates, pure noise)
3. Identifies version chains that should be COMPRESSED (send summary not files)
4. Prioritizes planned-feature files for Phase X (Feature Index) and T (Tasks)
5. Estimates token savings from your recommendations
6. Assigns model routing hints (fast model vs. premium model per partition)

Return valid JSON:
{
  "skip_list": ["path1.md", "path2.md"],
  "compress_chains": [
    {
      "chain_id": "abc12345",
      "send_summary_instead": true,
      "summary_hint": "brief context about what these files cover"
    }
  ],
  "phase_routing_overrides": [
    {
      "path": "docs/90-adr/ADR-207.md",
      "recommended_phase": "X",
      "reason": "Contains planned feature inventory"
    }
  ],
  "model_routing_hints": [
    {
      "partition_pattern": "docs/90-adr/*",
      "recommended_model": "premium",
      "reason": "Architectural decisions need deep analysis"
    }
  ],
  "estimated_savings": {
    "files_skipped": 0,
    "files_compressed": 0,
    "estimated_token_reduction_pct": 0
  },
  "optimization_summary": "max 200 word executive summary of recommendations"
}
"""

PASS_SYSTEM_PROMPTS = {
    "dedup": _DEDUP_SYSTEM_PROMPT,
    "discover": _DISCOVER_SYSTEM_PROMPT,
    "feasibility": _FEASIBILITY_SYSTEM_PROMPT,
    "optimize": _OPTIMIZE_SYSTEM_PROMPT,
}

# ─── Payload Builders ────────────────────────────────────────────────


def _read_preview(path: Path) -> str:
    """Read first N lines/bytes of a file for payload packaging."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return "[UNREADABLE]"
    lines = text.splitlines(keepends=True)[:MAX_PREVIEW_LINES]
    preview = "".join(lines)
    encoded = preview.encode("utf-8")
    if len(encoded) > MAX_PREVIEW_BYTES:
        preview = encoded[:MAX_PREVIEW_BYTES].decode("utf-8", errors="replace")
    return preview.rstrip()


def _build_dedup_payload(
    intelligence: dict,
    manifest: list[dict],
    repo_root: Path,
) -> str:
    """Build dedup pass payload from duplicate groups + version chains."""
    lines = [
        "# Deduplication Analysis Corpus",
        f"Generated: {dt.datetime.now(dt.timezone.utc).isoformat()}",
        "",
        "## Exact Duplicate Groups",
        "",
    ]

    manifest_index = {e["rel_path"]: e for e in manifest}

    for group_id, paths in list(intelligence.get("duplicate_groups", {}).items())[:30]:
        lines.append(f"### Group {group_id} ({len(paths)} files)")
        for p in paths:
            file_path = repo_root / p
            lines.append(f"#### {p}")
            if file_path.exists():
                lines.append("```")
                lines.append(_read_preview(file_path))
                lines.append("```")
            lines.append("")

    lines += [
        "",
        "## Version Chains (filename pattern duplicates)",
        "",
    ]

    for chain_id, members in list(intelligence.get("version_chains", {}).items())[:20]:
        lines.append(f"### Chain {chain_id} ({len(members)} versions)")
        for m in sorted(members, key=lambda x: x["ordinal"]):
            marker = "📌 LATEST" if m["is_latest"] else f"v{m['ordinal']}"
            file_path = repo_root / m["path"]
            lines.append(f"#### {m['path']} [{marker}]")
            if file_path.exists():
                lines.append("```")
                lines.append(_read_preview(file_path))
                lines.append("```")
            lines.append("")

    return "\n".join(lines)


def _build_discover_payload(
    intelligence: dict,
    manifest: list[dict],
    repo_root: Path,
) -> str:
    """Build discover pass payload from historical + canonical files + ghosts."""
    lines = [
        "# Discovery Analysis Corpus",
        f"Generated: {dt.datetime.now(dt.timezone.utc).isoformat()}",
        "",
        "## Lifecycle Distribution",
        "",
    ]
    for stage, count in intelligence.get("lifecycle_distribution", {}).items():
        lines.append(f"- **{stage}**: {count} files")
    lines.append("")

    # Historical and frozen files (drift candidates)
    lines += ["## Historical / Frozen Files (potential drift + rediscovery)", ""]
    hist_entries = [
        e
        for e in manifest
        if e.get("include")
        and not e.get("is_ghost")
        and (
            e.get("authority_class") in ("historical", "canonical")
            and e.get("lifecycle_stage") in ("frozen", "stale")
        )
    ]
    for e in sorted(
        hist_entries, key=lambda x: x.get("days_since_modified", 0), reverse=True
    )[:40]:
        fp = repo_root / e["rel_path"]
        dsm = e.get("days_since_modified", "?")
        lines.append(
            f"### {e['rel_path']} [frozen {dsm}d ago, "
            f"commits={e.get('commit_count', 0)}]"
        )
        if fp.exists():
            lines.append("```")
            lines.append(_read_preview(fp))
            lines.append("```")
        lines.append("")

    # Ghost files
    ghost_files = intelligence.get("ghost_files", [])
    if ghost_files:
        lines += ["## Ghost Files (deleted, recovered from git history)", ""]
        for g in ghost_files[:20]:
            lines.append(f"### 👻 {g['path']} [deleted {g.get('deleted_date', '?')}]")
            lines.append("*(File deleted from repo — assess restoration value)*")
            lines.append("")

    return "\n".join(lines)


def _build_feasibility_payload(
    intelligence: dict,
    manifest: list[dict],
    repo_root: Path,
) -> str:
    """Build feasibility pass payload from planned feature files."""
    planned = intelligence.get("planned_features", {})
    lines = [
        "# Planned Feature Feasibility Corpus",
        f"Generated: {dt.datetime.now(dt.timezone.utc).isoformat()}",
        "",
        "## Summary",
        f"- Proposed ADRs: {len(planned.get('proposed_adrs', []))}",
        f"- Stub files: {len(planned.get('stub_files', []))}",
        f"- TODO files: {len(planned.get('todo_files', []))}",
        f"- Draft docs: {len(planned.get('draft_docs', []))}",
        "",
    ]

    all_planned_paths = (
        planned.get("proposed_adrs", [])[:15]
        + planned.get("stub_files", [])[:10]
        + planned.get("todo_files", [])[:10]
        + planned.get("draft_docs", [])[:10]
    )
    seen: set[str] = set()

    for p in all_planned_paths:
        if p in seen:
            continue
        seen.add(p)
        fp = repo_root / p
        if not fp.exists():
            continue
        category = (
            "Proposed ADR"
            if p in planned.get("proposed_adrs", [])
            else (
                "Stub Implementation"
                if p in planned.get("stub_files", [])
                else "TODO File" if p in planned.get("todo_files", []) else "Draft Doc"
            )
        )
        lines.append(f"### [{category}] {p}")
        lines.append("```")
        lines.append(_read_preview(fp))
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def _build_optimize_payload(
    intelligence: dict,
    pass_results: dict[str, Any],
) -> str:
    """Build optimize pass payload from all prior intelligence."""
    lines = [
        "# Extraction Optimization Intelligence Summary",
        f"Generated: {dt.datetime.now(dt.timezone.utc).isoformat()}",
        "",
        "## Corpus Stats",
    ]
    summary = intelligence.get("corpus_summary", {})
    lines += [
        f"- Included files: {summary.get('included_files', 0)}",
        f"- Ghost files: {summary.get('ghost_files', 0)}",
        f"- Corpus health score: {summary.get('corpus_health_score', 0)}/100",
        f"- Duplicate skip candidates: "
        f"{len(intelligence.get('extraction_hints', {}).get('skip_duplicates', []))}",
        f"- Version chains: {intelligence.get('version_chain_count', 0)}",
        f"- Compression potential files: "
        f"{intelligence.get('compression_potential_files', 0)}",
        "",
    ]

    if "dedup" in pass_results:
        lines += ["## Dedup Pass Results (summary)", ""]
        result = pass_results["dedup"]
        lines.append(
            f"- Confirmed duplicate groups: "
            f"{len(result.get('duplicate_assessments', []))}"
        )
        lines.append(
            f"- Version chains compressed: "
            f"{len(result.get('version_chain_summaries', []))}"
        )
        for chain in result.get("version_chain_summaries", [])[:5]:
            lines.append(
                f"  - {chain.get('base_topic', '?')}: "
                f"{chain.get('evolution_narrative', '')[:100]}..."
            )
        lines.append("")

    if "discover" in pass_results:
        lines += ["## Discovery Pass Results (summary)", ""]
        result = pass_results["discover"]
        lines.append(f"- Hidden features: {len(result.get('hidden_features', []))}")
        lines.append(f"- Drift signals: {len(result.get('drift_signals', []))}")
        lines.append(f"- Ghost assessments: {len(result.get('ghost_assessments', []))}")
        lines.append("")

    if "feasibility" in pass_results:
        lines += ["## Feasibility Pass Results (summary)", ""]
        result = pass_results["feasibility"]
        planned = result.get("planned_features", [])
        quick_wins = [f for f in planned if f.get("quick_win")]
        lines.append(f"- Features assessed: {len(planned)}")
        lines.append(f"- Quick wins: {len(quick_wins)}")
        if result.get("feasibility_summary"):
            lines.append(f"- Summary: {result['feasibility_summary'][:200]}")
        lines.append("")

    lines += [
        "## Lifecycle Distribution",
        "",
    ]
    for stage, count in intelligence.get("lifecycle_distribution", {}).items():
        lines.append(f"- {stage}: {count} files")
    lines.append("")

    lines += [
        "## High-Churn Files (top 10)",
        "",
    ]
    for p in intelligence.get("extraction_hints", {}).get("high_churn_files", [])[:10]:
        lines.append(f"- {p}")
    lines.append("")

    # ── Code intelligence (if available) ────────────────────────────────
    code_intel = intelligence.get("code_intelligence", {})
    if code_intel:
        lines += ["## Code Intelligence", ""]
        lines.append(f"- Python files: {code_intel.get('total_python_files', 0)}")
        lines.append(f"- Entry points: {code_intel.get('entry_point_count', 0)}")
        lines.append(f"- Orphan files: {code_intel.get('orphan_count', 0)}")
        lines.append(f"- Hub files (≥5 importers): {code_intel.get('hub_count', 0)}")
        lines.append(f"- Circular imports: {len(code_intel.get('circular_imports', []))}")
        lines.append(f"- Avg complexity: {code_intel.get('avg_complexity', 0):.2f}")
        lines.append("")
        for h in code_intel.get("hub_files", [])[:5]:
            lines.append(f"  Hub: {h['path']} (imported by {h['imported_by']})")
        for h in code_intel.get("complexity_hotspots", [])[:5]:
            lines.append(f"  Hotspot: {h['path']} (complexity: {h.get('complexity', 0):.2f})")
        lines.append("")

    # ── Architecture intelligence (if available) ────────────────────────
    arch_data = intelligence.get("architecture", {})
    if arch_data:
        lines += ["## Architecture Intelligence", ""]
        lines.append(f"- Services: {arch_data.get('service_count', 0)}")
        lines.append(f"- API endpoints: {arch_data.get('api_endpoint_count', 0)}")
        lines.append(f"- Event flows: {arch_data.get('event_flow_count', 0)}")
        lines.append(f"- Files mapped to services: {arch_data.get('mapped_file_count', 0)}")
        lines.append("")

    # ── Feature intelligence (if available) ─────────────────────────────
    feat_data = intelligence.get("features", {})
    if feat_data:
        lines += ["## Feature Intelligence", ""]
        lines.append(f"- Feature flags: {feat_data.get('feature_flag_count', 0)}")
        lines.append(f"- CLI commands: {feat_data.get('cli_command_count', 0)}")
        lines.append(f"- MCP tools: {feat_data.get('mcp_tool_count', 0)}")
        lines.append(f"- MCP servers: {feat_data.get('mcp_server_count', 0)}")
        lines.append(f"- Avg completeness: {feat_data.get('avg_completeness', 0):.0%}")
        lines.append("")

    return "\n".join(lines)


PASS_PAYLOAD_BUILDERS = {
    "dedup": _build_dedup_payload,
    "discover": _build_discover_payload,
    "feasibility": _build_feasibility_payload,
}

# ─── Response Parsers ────────────────────────────────────────────────


def _parse_pass_response(pass_id: str, raw: str) -> dict:
    """Parse Grok JSON response for a pass. Returns dict or error dict."""
    try:
        data = json.loads(raw)
        return data
    except json.JSONDecodeError as e:
        logger.warning(f"⚠️  Failed to parse {pass_id} response as JSON: {e}")
        # Attempt to extract JSON block
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                pass
        return {"parse_error": str(e), "raw_response": raw[:500]}


# ─── Grok Caller ─────────────────────────────────────────────────────


def _call_grok(
    pass_id: str,
    payload: str,
    model: str,
    api_key: str,
    temperature: float = 0.1,
) -> dict | None:
    """Call Grok 420 for a single pass. Returns parsed response or None."""
    try:
        import openai
    except ImportError:
        logger.error("❌ 'openai' package not installed: pip install openai>=1.0.0")
        return None

    system_prompt = PASS_SYSTEM_PROMPTS[pass_id]
    client = openai.OpenAI(api_key=api_key, base_url=XAI_BASE_URL)

    payload_size = len(payload.encode("utf-8"))
    logger.info(
        f"   📡 Calling {model} for {pass_id} pass "
        f"({payload_size / 1024:.1f}KB payload)..."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": payload},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        result_text = response.choices[0].message.content or "{}"
        parsed = _parse_pass_response(pass_id, result_text)

        usage = response.usage
        if usage:
            logger.info(
                f"   ✅ {pass_id}: {usage.prompt_tokens} prompt + "
                f"{usage.completion_tokens} completion tokens"
            )

        return parsed

    except Exception as e:
        logger.error(f"❌ {pass_id} pass failed: {e}")
        return None


# ─── Orchestrator ────────────────────────────────────────────────────


def run_passes(
    passes: list[str],
    prescan_dir: Path,
    repo_root: Path,
    model: str,
    api_key: str,
) -> dict[str, Any]:
    """
    Run selected Grok passes sequentially, each building on the previous.
    Returns {pass_id: result_dict, ...}.
    """
    # Load intelligence and manifest
    intel_path = prescan_dir / "prescan_intelligence.json"
    manifest_path = prescan_dir / "corpus_manifest.json"

    if not intel_path.exists():
        raise FileNotFoundError(
            f"prescan_intelligence.json not found at {intel_path}.\n"
            "Run: python scripts/doc_audit_prescan.py dry-run --git-passes"
        )
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"corpus_manifest.json not found at {manifest_path}.\n"
            "Run: python scripts/doc_audit_prescan.py dry-run"
        )

    intelligence = json.loads(intel_path.read_text())
    manifest = json.loads(manifest_path.read_text())

    all_results: dict[str, Any] = {}
    output_dir = prescan_dir

    for pass_id in passes:
        if pass_id not in PASS_IDS:
            logger.warning(f"⚠️  Unknown pass '{pass_id}', skipping")
            continue

        logger.info(f"\n{'─' * 60}")
        logger.info(f"🔬 Pass: {pass_id.upper()} — {PASS_DESCRIPTIONS[pass_id]}")

        # Build payload
        if pass_id == "optimize":
            payload = _build_optimize_payload(intelligence, all_results)
        else:
            builder = PASS_PAYLOAD_BUILDERS[pass_id]
            payload = builder(intelligence, manifest, repo_root)  # type: ignore

        # Save payload for debugging
        (output_dir / f"pass_{pass_id}_payload.md").write_text(
            payload, encoding="utf-8"
        )

        # Call Grok
        result = _call_grok(pass_id, payload, model, api_key)
        if result is None:
            logger.error(f"   ❌ {pass_id} pass failed, stopping")
            break

        all_results[pass_id] = result

        # Save result
        result_path = output_dir / f"pass_{pass_id}_result.json"
        result_path.write_text(
            json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        )
        logger.info(f"   💾 Result saved: {result_path}")

    # Aggregate all pass results into intelligence report
    if all_results:
        intelligence["grok_passes"] = all_results
        intelligence["grok_passes_run"] = passes
        intelligence["grok_passes_timestamp"] = dt.datetime.now(
            dt.timezone.utc
        ).isoformat()
        intel_path.write_text(
            json.dumps(intelligence, indent=2, sort_keys=True, ensure_ascii=False)
            + "\n"
        )
        logger.info(
            f"\n✅ Intelligence report updated with {len(all_results)} pass results"
        )

        # Mirror to extractor inputs if available
        extractor_inputs = repo_root / "services/repo-truth-extractor/runs/00_inputs"
        if extractor_inputs.is_dir():
            dest = extractor_inputs / "PRESCAN_INTELLIGENCE.json"
            dest.write_text(
                json.dumps(intelligence, indent=2, sort_keys=True, ensure_ascii=False)
                + "\n"
            )
            logger.info(f"🔗 Extraction bridge updated: {dest}")

    return all_results


# ─── CLI ─────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="doc_audit_prescan_passes",
        description=("Grok 420 multi-pass pre-extraction intelligence for dopemux."),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Passes (run in order):\n"
            "  dedup       Near-duplicate + version chain compression\n"
            "  discover    Hidden features, drift, ghost assessment\n"
            "  feasibility Planned feature GSP feasibility\n"
            "  optimize    Extraction routing + cost optimization\n\n"
            "Examples:\n"
            "  %(prog)s --passes dedup,discover\n"
            "  %(prog)s --passes all\n"
            "  %(prog)s --passes optimize\n"
        ),
    )
    parser.add_argument(
        "--passes",
        type=str,
        default="all",
        help=(
            "Comma-separated pass IDs to run: "
            "dedup,discover,feasibility,optimize  or  'all'"
        ),
    )
    parser.add_argument(
        "--prescan-dir",
        type=str,
        default=None,
        help="Path to prescan output directory (default: extraction/prescan)",
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help="Repo root path (default: git rev-parse --show-toplevel)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Grok model ID (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--api-key-env",
        type=str,
        default="XAI_API_KEY",
        help="Environment variable containing xAI API key (default: XAI_API_KEY)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Model temperature (default: 0.1)",
    )
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    # Resolve repo root
    if args.repo_root:
        repo_root = Path(args.repo_root).resolve()
    else:
        import subprocess

        try:
            repo_root = Path(
                subprocess.check_output(
                    ["git", "rev-parse", "--show-toplevel"],
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            ).resolve()
        except (subprocess.CalledProcessError, FileNotFoundError):
            repo_root = Path.cwd()

    # Resolve prescan dir
    prescan_dir = (
        Path(args.prescan_dir).resolve()
        if args.prescan_dir
        else repo_root / "extraction/prescan"
    )

    # Resolve passes
    pass_str = args.passes.strip().lower()
    if pass_str == "all":
        passes = list(PASS_IDS)
    else:
        passes = [p.strip() for p in pass_str.split(",") if p.strip()]

    if not passes:
        logger.error("❌ No valid passes specified.")
        return 1

    # Check API key
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        logger.error(
            f"❌ API key not found in ${args.api_key_env}.\n"
            "   Export your xAI API key: export XAI_API_KEY=xai-..."
        )
        return 1

    logger.info(f"🚀 Starting Grok 420 intelligence passes: {', '.join(passes)}")
    logger.info(f"   Model: {args.model}")
    logger.info(f"   Prescan dir: {prescan_dir}")

    try:
        results = run_passes(
            passes=passes,
            prescan_dir=prescan_dir,
            repo_root=repo_root,
            model=args.model,
            api_key=api_key,
        )
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        return 1

    logger.info(f"\n✅ Completed {len(results)}/{len(passes)} passes")
    for pass_id, result in results.items():
        if "parse_error" in result:
            logger.warning(f"   ⚠️  {pass_id}: parse error")
        else:
            logger.info(f"   ✅ {pass_id}: OK")

    return 0


if __name__ == "__main__":
    sys.exit(main())
