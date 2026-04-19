"""
Extraction Pipelines Commands

The repo-truth extraction, chatlog extraction, and repscan passthrough commands.
Orchestrates LLM-driven extraction rituals across multiple phases and configurations.
"""

import logging
import sys
from pathlib import Path
from typing import Callable, List, Optional

import click

from ..console import console

logger = logging.getLogger(__name__)


@click.command("extract-chatlog")
@click.argument("directory", default=".")
@click.option("--output", "-o", help="📂 Harvest Coordinate: Output directory for extraction results.")
@click.option(
    "--confidence",
    "-c",
    type=float,
    default=0.5,
    help="🎯 Confidence Gate: Minimum threshold for signal extraction (0.0-1.0).",
)
@click.option(
    "--batch-size",
    "-b",
    type=int,
    default=10,
    help="📊 Signal Density: Number of artifacts to process per batch.",
)
@click.option(
    "--max-workers", "-w", type=int, default=4, help="⚡ Extraction Workers: Maximum parallel ritual workers.",
)
@click.option("--archive", "-a", help="📦 Temporal Archive: Directory for processed artifact storage.")
@click.option("--workspace-id", help="🆔 Ritual Chamber: ConPort workspace ID for persistent synchronization.")
@click.pass_context
def extract_chatlog(
    ctx,
    directory: str,
    output: Optional[str],
    confidence: float,
    batch_size: int,
    max_workers: int,
    archive: Optional[str],
    workspace_id: Optional[str],
):
    """
    🔮 Semantic Archaeology: Extract signals from chat logs

    Excavates semantic structure from Claude conversation logs, identifying
    knowledge transfer events, decision context, and learning trajectories.
    """
    _run_extract_chatlog(
        ctx,
        directory,
        output,
        confidence,
        batch_size,
        max_workers,
        archive,
        workspace_id,
    )


def _run_extract_chatlog(
    ctx,
    directory: str,
    output: Optional[str],
    confidence: float,
    batch_size: int,
    max_workers: int,
    archive: Optional[str],
    workspace_id: Optional[str],
):
    """Helper for extract-chatlog command."""
    from ..ux.extractor_runner import run_extractor_runner as _run_extractor_runner

    args: List[str] = [
        "extract-chatlog",
        directory,
    ]
    if output:
        args.extend(["--output", output])
    if confidence:
        args.extend(["--confidence", str(confidence)])
    if batch_size:
        args.extend(["--batch-size", str(batch_size)])
    if max_workers:
        args.extend(["--max-workers", str(max_workers)])
    if archive:
        args.extend(["--archive", archive])
    if workspace_id:
        args.extend(["--workspace-id", workspace_id])
    try:
        _run_extractor_runner(args=args)
    except Exception as e:
        logger.error(f"Extract chatlog failed: {e}")
        sys.exit(1)


@click.command()
@click.argument("directory", default=".")
@click.option("--output", "-o", help="📂 Harvest Coordinate: Output directory for high-fidelity extraction results.")
@click.option(
    "--confidence",
    "-c",
    type=float,
    default=0.4,
    help="🎯 Confidence Gate: Minimum threshold for signal extraction (0.0-1.0).",
)
@click.option(
    "--batch-size",
    "-b",
    type=int,
    default=15,
    help="📊 Signal Density: Number of artifacts to process per batch.",
)
@click.option(
    "--max-workers", "-w", type=int, default=6, help="⚡ Extraction Workers: Maximum parallel ritual workers.",
)
@click.option("--archive", "-a", help="📦 Temporal Archive: Directory for processed artifact storage.")
@click.option("--workspace-id", help="🆔 Ritual Chamber: ConPort workspace ID for persistent synchronization.")
@click.option(
    "--max-documents", "-d", type=int, default=8, help="📜 Materialization Limit: Maximum documents to synthesize during the ritual."
)
@click.pass_context
def extractPro(
    ctx,
    directory: str,
    output: Optional[str],
    confidence: float,
    batch_size: int,
    max_workers: int,
    archive: Optional[str],
    workspace_id: Optional[str],
    max_documents: int,
):
    """
    ⚡ Extraction Pro: High-fidelity signal synthesis

    Premium extraction ritual with adaptive sampling, consensus scoring, and
    multi-document materialization for comprehensive signal semantics.
    """
    _run_extract_pro(
        ctx,
        directory,
        output,
        confidence,
        batch_size,
        max_workers,
        archive,
        workspace_id,
        max_documents,
    )


def _run_extract_pro(
    ctx,
    directory: str,
    output: Optional[str],
    confidence: float,
    batch_size: int,
    max_workers: int,
    archive: Optional[str],
    workspace_id: Optional[str],
    max_documents: int,
):
    """Helper for extractPro command."""
    from ..ux.extractor_runner import run_extractor_runner as _run_extractor_runner

    args: List[str] = [
        "extractPro",
        directory,
    ]
    if output:
        args.extend(["--output", output])
    if confidence:
        args.extend(["--confidence", str(confidence)])
    if batch_size:
        args.extend(["--batch-size", str(batch_size)])
    if max_workers:
        args.extend(["--max-workers", str(max_workers)])
    if archive:
        args.extend(["--archive", archive])
    if workspace_id:
        args.extend(["--workspace-id", workspace_id])
    if max_documents:
        args.extend(["--max-documents", str(max_documents)])
    try:
        _run_extractor_runner(args=args)
    except Exception as e:
        logger.error(f"ExtractPro failed: {e}")
        sys.exit(1)


@click.command(
    "repscan",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.option(
    "--phase",
    type=click.Choice(
        ["ALL", "A", "H", "D", "C", "E", "W", "B", "G", "Q", "R", "X", "T", "Z"]
    ),
    help="📊 Target Phase: Phase code or ALL for the repo scan ritual.",
)
@click.option("--run-id", type=str, help="🆔 Ritual Session: Unique identifier for the scan run.")
@click.option("--promptgen", type=click.Choice(["off", "v1", "v2", "auto"]), help="🧠 Prompt Synthesis: Mode for automated prompt generation.")
@click.option("--promptpack", type=str, help="📦 Prompt Package: Specific promptpack to use for the ritual.")
@click.option("--promptgen-only", is_flag=True, help="⚡ Synthesis Only: Execute only the prompt generation phase.")
@click.option("--prompt-root", type=str, help="🔬 Prompt Source: Root directory for ritual prompts.")
@click.option("--profiles-dir", type=str, help="📂 Profile Registry: Path to the ritual profiles directory.")
@click.option("--legacy-runner", type=str, help="⏪ Legacy Engine: Path to the legacy v3 runner.")
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def repscan_passthrough(
    phase: Optional[str],
    run_id: Optional[str],
    promptgen: Optional[str],
    promptpack: Optional[str],
    promptgen_only: bool,
    prompt_root: Optional[str],
    profiles_dir: Optional[str],
    legacy_runner: Optional[str],
    args: tuple[str, ...],
):
    """
    🔍 Repository Truth Scanner: Comprehensive codebase extraction ritual

    Orchestrates the repo-truth-extractor service across phases A through Z,
    extracting structured semantic knowledge from source code repositories.
    Coordinates with provider ladders for cost-efficient LLM utilization.
    """
    from ..ux.extractor_runner import run_repscan_runner as _run_repscan_runner

    pipeline_version = _resolved_pipeline_version(
        pipeline_version="v5", engine_version_legacy=legacy_runner
    )

    cli_args: List[str] = []
    if phase:
        cli_args.extend(["--phase", phase])
    if run_id:
        cli_args.extend(["--run-id", run_id])
    if promptgen:
        cli_args.extend(["--promptgen", promptgen])
    if promptpack:
        cli_args.extend(["--promptpack", promptpack])
    if promptgen_only:
        cli_args.append("--promptgen-only")
    if prompt_root:
        cli_args.extend(["--prompt-root", prompt_root])
    if profiles_dir:
        cli_args.extend(["--profiles-dir", profiles_dir])

    cli_args.extend(args)

    _run_repscan_runner(pipeline_version=pipeline_version, args=cli_args)


_PIPELINE_VERSION_CHOICES = ["v5", "v4", "v3"]
_ROUTING_POLICY_CHOICES = [
    "cost",
    "speed",
    "quality",
]
_LEGACY_DEFAULT_ROUTING_POLICY = "cost"


def _pipeline_version_options(command_fn: Callable) -> Callable:
    """Add standard pipeline version options to a command."""
    command_fn = click.option(
        "--dry-run",
        is_flag=True,
        default=True,
        show_default=True,
        help="🔬 Ritual Preview: Simulate without persisting artifacts.",
    )(command_fn)
    command_fn = click.option(
        "--resume",
        is_flag=True,
        default=False,
        help="⚡ Resume Ritual: Skip completed phases.",
    )(command_fn)
    command_fn = click.option(
        "--workers",
        type=int,
        default=4,
        show_default=True,
        help="⚙️  Worker Threads: Parallel extraction concurrency.",
    )(command_fn)
    command_fn = click.option(
        "--routing-policy",
        type=click.Choice(_ROUTING_POLICY_CHOICES),
        default=_LEGACY_DEFAULT_ROUTING_POLICY,
        show_default=True,
        help="🧭 Provider Selection: Cost, speed, or quality trade-off.",
    )(command_fn)
    command_fn = click.option(
        "--pipeline-version",
        "pipeline_version",
        type=click.Choice(_PIPELINE_VERSION_CHOICES),
        default="v5",
        show_default=True,
    )(command_fn)
    return command_fn


def _resolved_pipeline_version(
    pipeline_version: str, engine_version_legacy: Optional[str]
) -> str:
    """Resolve final pipeline version, preferring legacy if specified."""
    if engine_version_legacy:
        return engine_version_legacy
    return pipeline_version


def _run_truth_v5_alias(
    *,
    phase: str = "ALL",
    dry_run: bool,
    resume: bool,
    workers: int,
    routing_policy: str,
) -> None:
    """Run truth v5 alias command."""
    from ..ux.extractor_runner import run_extractor_runner as _run_extractor_runner

    args: List[str] = ["--phase", phase or "ALL"]
    if dry_run:
        args.append("--dry-run")
    _run_extractor_runner(pipeline_version="v5", args=args)
