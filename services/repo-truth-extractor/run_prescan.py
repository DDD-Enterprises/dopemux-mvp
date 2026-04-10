#!/usr/bin/env python
"""Standalone prescan CLI - runs pre-extraction intelligence audit.

This script provides direct access to the prescan pipeline without requiring
dopemux installation. Use this for CI/CD integration or standalone testing.

Example:
    python run_prescan.py \\
        --repo-root /path/to/repo \\
        --output-dir extraction/prescan_output \\
        --passes dedup,discover,feasibility,optimize \\
        --code --git --incremental
"""

import argparse
import json
import logging
import sys
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parent
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Flight-Deck: Execute a pre-extraction intelligence audit.",
        epilog="For more info, see docs/02-how-to/extraction/run-prescan.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Core arguments
    parser.add_argument(
        "--repo-root",
        type=str,
        required=True,
        help="Path to repository root to scan",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory to write prescan artifacts",
    )

    # Passes
    parser.add_argument(
        "--passes",
        type=str,
        default="dedup,discover,feasibility,optimize",
        help=(
            "Comma-separated grok passes to run (default: all). "
            "Use 'none' to skip all passes, or 'all' to run every pass."
        ),
    )

    # Enrichment
    parser.add_argument(
        "--code",
        action="store_true",
        default=True,
        help="Enable code intelligence (AST analysis) [default: enabled]",
    )
    parser.add_argument(
        "--no-code",
        action="store_true",
        help="Disable code intelligence",
    )
    parser.add_argument(
        "--git",
        action="store_true",
        default=True,
        help="Enable git enrichment [default: enabled]",
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Disable git enrichment",
    )

    # Modes
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Run in incremental mode (reuse cached code analysis)",
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help="Enable deep mode (include archived/historical files)",
    )

    # Cost estimation
    parser.add_argument(
        "--cost-estimate",
        action="store_true",
        default=True,
        help="Estimate extraction costs [default: enabled]",
    )
    parser.add_argument(
        "--no-cost-estimate",
        action="store_true",
        help="Skip cost estimation",
    )

    # Batch mode
    parser.add_argument(
        "--batch-mode",
        action="store_true",
        default=True,
        help="Use token-aware batching [default: enabled]",
    )
    parser.add_argument(
        "--no-batch-mode",
        action="store_true",
        help="Disable batching",
    )
    parser.add_argument(
        "--max-tokens-per-batch",
        type=int,
        default=1_500_000,
        help="Max tokens per batch (default: 1,500,000)",
    )

    # Dry run / verbosity
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip expensive operations (no grok passes, no git enrichment)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Import after arg parsing to allow early --help
    try:
        from lib.prescan import PrescanEngine, PrescanConfig
    except ImportError:
        logger.error(
            "Failed to import prescan library from %s.",
            SERVICE_DIR,
        )
        sys.exit(1)

    # Build config
    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not repo_root.is_dir():
        logger.error(f"Repo root not found: {repo_root}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    config = PrescanConfig(
        repo_root=repo_root,
        output_dir=output_dir,
        enable_code_prescan=args.code and not args.no_code,
        enable_git_enrichment=args.git and not args.no_git,
        incremental=args.incremental,
        deep_mode=args.deep,
        cost_estimate=args.cost_estimate and not args.no_cost_estimate,
        batch_mode=args.batch_mode and not args.no_batch_mode,
        max_tokens_per_batch=args.max_tokens_per_batch,
        verbose=args.verbose,
    )

    # Parse passes — special-case 'none' and 'all' before CSV split
    _ALL_PASSES = ["dedup", "discover", "feasibility", "optimize"]
    _passes_raw = (args.passes or "").strip().lower()
    if _passes_raw in ("none", ""):
        passes: list[str] = []
    elif _passes_raw == "all":
        passes = list(_ALL_PASSES)
    else:
        passes = [p.strip() for p in args.passes.split(",") if p.strip()]

    # Dry run: skip expensive operations
    if args.dry_run:
        config.enable_code_prescan = False
        config.enable_git_enrichment = False
        passes = []
        logger.info("🏜️  DRY RUN: Skipping code, git, and grok passes")

    logger.info(f"🚀 Prescan starting: {repo_root.name}")
    logger.info(f"   Output: {output_dir}")
    logger.info(f"   Passes: {', '.join(passes) if passes else 'none'}")
    logger.info(f"   Code prescan: {config.enable_code_prescan}")
    logger.info(f"   Git enrichment: {config.enable_git_enrichment}")

    # Run prescan
    engine = PrescanEngine(config)
    result = engine.run(passes=passes, incremental=args.incremental)

    # Report results
    if result.success:
        logger.info(f"✅ Prescan complete: {result.file_count} files, {result.code_files_analyzed} analyzed ({result.duration_seconds:.1f}s)")

        if result.intelligence_path:
            logger.info(f"   Intelligence: {result.intelligence_path.relative_to(output_dir)}")
        if result.manifest_path:
            logger.info(f"   Manifest: {result.manifest_path.relative_to(output_dir)}")
        if result.code_graph_path:
            logger.info(f"   Code graph: {result.code_graph_path.relative_to(output_dir)}")

        if result.warnings:
            for warning in result.warnings:
                logger.warning(f"   ⚠️  {warning}")

        # Print intelligence schema (for validation)
        if result.intelligence_path:
            try:
                intel = json.loads(result.intelligence_path.read_text())
                keys = list(intel.keys())
                logger.info(f"   Schema keys: {', '.join(keys)}")
            except Exception as e:
                logger.debug(f"Could not read intelligence schema: {e}")

        return 0
    else:
        logger.error(f"❌ Prescan failed: {result.duration_seconds:.1f}s")
        for error in result.errors:
            logger.error(f"   {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
