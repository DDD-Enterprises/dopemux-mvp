"""
Extract Commands

Document extraction with ADHD-optimized patterns.
"""

import importlib.util
import os
import sys
import time
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional, Dict, List, Sequence

import click
import yaml
from dopemux.ui.progress import branded_progress
from dopemux.ui.progress import branded_progress
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.text import Text

from ..console import console
from ..ui.theme import styled_panel, styled_table, error_panel, Glyphs, StatusChip

@click.group()
@click.pass_context
def extract(ctx):
    """📄 Ritual Daemon: Document extraction with ADHD-optimized patterns.

    Engage the cockpit for high-precision entity extraction, configuration harvesting,
    and pattern recognition. This subsystem synchronizes through markdown, YAML,
    and ADHD-specific content streams to build a high-fidelity model of your
    documentation corpus.
    """
    pass


@extract.command("docs")
@click.argument("directory", default=".")
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["basic", "detailed", "adhd"]),
    default="basic",
    help="📊 Calibration mode for the extraction ritual: basic (key-value), detailed (all patterns), or adhd (ADHD-specific patterns).",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "csv", "markdown", "yaml"]),
    default="json",
    help="🛠️  Output format for the extracted payload: json, csv, markdown, or yaml.",
)
@click.option(
    "--output",
    "-o",
    help="📂 Target file path for the extraction payload (default: telemetry stream to stdout).",
)
@click.option(
    "--confidence",
    "-c",
    type=float,
    default=0.5,
    help="🎯 Minimum confidence threshold for entity validation (0.0 to 1.0).",
)
@click.option(
    "--extensions",
    help="🧪 Specific file extensions to be analyzed by the ritual sensors (default: .md,.yaml,.yml).",
)
@click.option(
    "--adhd-profile",
    "-p",
    is_flag=True,
    help="🧠 Enable extraction of specialized ADHD accommodation profiles and cognitive load assessments.",
)
@click.pass_context
def extract_docs(
    ctx,
    directory: str,
    mode: str,
    format: str,
    output: Optional[str],
    confidence: float,
    extensions: Optional[str],
    adhd_profile: bool,
):
    """📄 Flight-Deck: Execute a targeted document extraction ritual.

    Process markdown and YAML assets to synthesize structured intelligence
    using ADHD-optimized patterns and adaptive confidence scoring.
    This command calibrates the extraction engines for specific document
    clusters to ensure high-fidelity harvesting of entities and metadata.
    """
    with mobile_task_notification(
        ctx,
        "Documentation extraction",
        success_message="✅ Documentation extraction complete",
        failure_message="❌ Documentation extraction failed",
    ):
        _run_extract_docs(
            ctx,
            directory,
            mode,
            format,
            output,
            confidence,
            extensions,
            adhd_profile,
        )


def _run_extract_docs(
    ctx,
    directory: str,
    mode: str,
    format: str,
    output: Optional[str],
    confidence: float,
    extensions: Optional[str],
    adhd_profile: bool,
) -> None:
    import json
    import csv
    from io import StringIO

    # Add extraction package to path
    sys.path.append(str(Path(__file__).parent.parent.parent / "extraction"))

    try:
        from document_classifier import DocumentClassifier, extract_from_directory
    except ImportError as e:
        console.logger.info(f"[error]❌ Could not import extraction modules: {e}[/error]")
        console.logger.info("[warning]💡 Make sure you're in the dopemux-mvp directory[/warning]")
        sys.exit(1)

    source_path = Path(directory).resolve()
    if not source_path.exists():
        console.logger.info(f"[error]❌ Directory does not exist: {source_path}[/error]")
        sys.exit(1)

    if not extensions:
        extensions = ".md,.yaml,.yml,.json"

    with branded_progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Extracting entities in {mode} mode...", total=None)

        try:
            results = extract_from_directory(str(source_path))

            progress.update(task, description="Processing results...", total=None)

            filtered_entities = {}
            total_entities = 0
            filtered_count = 0

            for entity_type, entity_list in results.get('all_entities', {}).items():
                filtered_list = []
                for entity in entity_list:
                    total_entities += 1
                    entity_confidence = entity.get('confidence', 0.0)
                    if entity_confidence >= confidence:
                        filtered_list.append(entity)
                        filtered_count += 1

                if filtered_list:
                    filtered_entities[entity_type] = filtered_list

            if mode == "basic":
                basic_types = ['section_header', 'project_metadata', 'yaml_properties', 'markdown_headers']
                filtered_entities = {k: v for k, v in filtered_entities.items() if k in basic_types}
            elif mode == "adhd":
                adhd_keywords = ['adhd', 'focus', 'break', 'attention', 'cognitive', 'accommodation']
                adhd_types = [
                    k
                    for k in filtered_entities.keys()
                    if any(keyword in k.lower() for keyword in adhd_keywords)
                ]
                filtered_entities = {k: v for k, v in filtered_entities.items() if k in adhd_types}

            progress.update(task, description="Formatting output...", total=None)

            output_data = {
                'extraction_summary': {
                    'mode': mode,
                    'source_directory': str(source_path),
                    'documents_processed': results.get('documents_processed', 0),
                    'total_entities_found': total_entities,
                    'entities_above_threshold': filtered_count,
                    'confidence_threshold': confidence,
                    'entity_types': list(filtered_entities.keys()),
                },
                'entities': filtered_entities,
            }

            if adhd_profile and results.get('metadata', {}).get('adhd_documents'):
                sys.path.append(str(Path(__file__).parent.parent.parent / "extraction"))
                from adhd_entities import ADHDEntityExtractor

                extractor = ADHDEntityExtractor()
                for doc_info in results.get('document_types', {}).get('markdown', []):
                    if doc_info['filename'] in results['metadata']['adhd_documents']:
                        output_data['adhd_profile'] = {
                            'accommodation_categories': ['attention_management', 'energy_management'],
                            'confidence_note': 'Profile extraction requires document content access',
                        }
                        break

            progress.update(task, description="Complete! ✅", completed=True)

        except Exception as e:
            progress.update(task, description="Error occurred", completed=True)
            console.logger.error(f"[error]❌ Extraction failed: {e}[/error]")
            if ctx.obj.get("verbose"):
                import traceback
                traceback.print_exc()
            sys.exit(1)

    if format == "json":
        output_text = json.dumps(output_data, indent=2, ensure_ascii=False)
    elif format == "yaml":
        try:
            import yaml

            output_text = yaml.dump(output_data, default_flow_style=False, allow_unicode=True)
        except ImportError:
            console.logger.info("[warning]⚠️ PyYAML not available, falling back to JSON[/warning]")
            output_text = json.dumps(output_data, indent=2, ensure_ascii=False)
    elif format == "csv":
        output_buffer = StringIO()
        writer = csv.writer(output_buffer)
        writer.writerow(['entity_type', 'content', 'value', 'confidence', 'source_file'])

        for entity_type, entity_list in filtered_entities.items():
            for entity in entity_list:
                writer.writerow(
                    [
                        entity_type,
                        entity.get('content', ''),
                        entity.get('value', ''),
                        entity.get('confidence', 0.0),
                        entity.get('source_file', ''),
                    ]
                )
        output_text = output_buffer.getvalue()
    elif format == "markdown":
        lines = [f"# Extraction Results - {mode.title()} Mode\n"]
        lines.append(f"**Source**: {source_path}")
        lines.append(f"**Documents**: {output_data['extraction_summary']['documents_processed']}")
        lines.append(f"**Entities**: {filtered_count}/{total_entities} (confidence ≥ {confidence})\n")

        for entity_type, entity_list in filtered_entities.items():
            lines.append(f"## {entity_type.replace('_', ' ').title()}\n")
            for entity in entity_list:
                lines.append(f"- **{entity.get('content', 'N/A')}**")
                if entity.get('value'):
                    lines.append(f": {entity['value']}")
                lines.append(f" _(confidence: {entity.get('confidence', 0.0):.2f})_")
                lines.append("")

        output_text = "\n".join(lines)
    else:
        output_text = json.dumps(output_data, indent=2, ensure_ascii=False)

    if output:
        output_path = Path(output)
        output_path.write_text(output_text, encoding='utf-8')
        console.logger.info(f"[success]✅ Results written to {output_path}[/success]")
    else:
        console.logger.info(output_text)

    console.print(
        styled_panel(
            f"🎯 Extraction Summary:\n\n"
            f"• Mode: {mode}\n"
            f"• Documents: {results.get('documents_processed', 0)}\n"
            f"• Entities: {filtered_count}/{total_entities}\n"
            f"• Entity types: {len(filtered_entities)}\n"
            f"• Format: {format}",
            title="📊 Results",
            border_style="success",
        )
    )


@extract.command("pipeline")
@click.argument("directory", default=".")
@click.option(
    "--output",
    "-o",
    help="📂 Target directory for the complete pipeline payload and generated artifacts.",
    default="./output",
)
@click.option(
    "--adhd/--no-adhd",
    default=True,
    help="🧠 Toggle synchronization of specialized ADHD-specific extraction patterns.",
)
@click.option(
    "--multi-angle/--no-multi-angle",
    default=True,
    help="📐 Enable multi-angle entity extraction for higher fidelity across diverse structures.",
)
@click.option(
    "--embeddings/--no-embeddings",
    default=True,
    help="🔍 Generate vector embeddings for the extracted corpus to enable semantic HUD search.",
)
@click.option(
    "--tsv/--no-tsv",
    default=True,
    help="📊 Generate atomic TSV registries for rapid metadata indexing and cross-referencing.",
)
@click.option(
    "--confidence",
    "-c",
    type=float,
    default=0.5,
    help="🎯 Minimum confidence threshold for entity validation throughout the pipeline ritual.",
)
@click.option(
    "--embedding-model",
    "-m",
    default="voyage-context-3",
    help="🧪 Specify the high-fidelity embedding model for vector synthesis.",
)
@click.option(
    "--milvus-uri",
    help="🗄️  Milvus database URI for long-term vector storage and retrieval telemetry.",
)
@click.option(
    "--extensions",
    help="🧪 Specific file extensions to be ingested by the pipeline sensors (default: .md,.yaml,.yml,.json,.txt).",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "csv", "markdown"]),
    default="json",
    help="🛠️  Primary output format for the extraction metadata: json, csv, or markdown.",
)
@click.option(
    "--synthesis/--no-synthesis",
    default=True,
    help="⚡ Enable LLM-powered document synthesis and executive summaries for the flight-deck.",
)
@click.option(
    "--synthesis-types",
    multiple=True,
    type=click.Choice(["executive", "adhd", "technical", "all"]),
    default=["executive", "adhd"],
    help="📊 Calibration types for document synthesis: executive, adhd, or technical.",
)
@click.option(
    "--synthesis-format",
    type=click.Choice(["markdown", "json", "both"]),
    default="markdown",
    help="🛠️  Output format for the synthesized reports: markdown, json, or both.",
)
@click.pass_context
def extract_pipeline(
    ctx,
    directory: str,
    output: str,
    adhd: bool,
    multi_angle: bool,
    embeddings: bool,
    tsv: bool,
    confidence: float,
    embedding_model: str,
    milvus_uri: Optional[str],
    extensions: Optional[str],
    format: str,
    synthesis: bool,
    synthesis_types: tuple,
    synthesis_format: str,
):
    """🚀 Ritual Daemon: Engage the full unified document processing pipeline.

    This command ignites the complete multi-layer extraction sequence:
    atomic unit normalization, TSV registry generation, and vector
    embedding synthesis. It integrates all cockpit extraction systems
    into a single, high-fidelity workflow for corpus-level intelligence.
    """
    with mobile_task_notification(
        ctx,
        "Extraction pipeline",
        success_message="✅ Extraction pipeline complete",
        failure_message="❌ Extraction pipeline failed",
    ):
        _run_extract_pipeline(
            ctx,
            directory,
            output,
            adhd,
            multi_angle,
            embeddings,
            tsv,
            confidence,
            embedding_model,
            milvus_uri,
            extensions,
            format,
            synthesis,
            synthesis_types,
            synthesis_format,
        )


def _run_extract_pipeline(
    ctx,
    directory: str,
    output: str,
    adhd: bool,
    multi_angle: bool,
    embeddings: bool,
    tsv: bool,
    confidence: float,
    embedding_model: str,
    milvus_uri: Optional[str],
    extensions: Optional[str],
    format: str,
    synthesis: bool,
    synthesis_types: tuple,
    synthesis_format: str,
) -> None:

    try:
        from ..extraction import UnifiedDocumentPipeline, PipelineConfig
    except ImportError as e:
        console.logger.info(f"[error]❌ Could not import pipeline modules: {e}[/error]")
        console.logger.info("[warning]💡 Make sure the extraction package is properly installed[/warning]")
        sys.exit(1)

    source_path = Path(directory).resolve()
    output_path = Path(output).resolve()

    if not source_path.exists():
        console.logger.info(f"[error]❌ Source directory does not exist: {source_path}[/error]")
        sys.exit(1)

    file_extensions = None
    if extensions:
        file_extensions = [ext.strip() for ext in extensions.split(',')]
        if not all(ext.startswith('.') for ext in file_extensions):
            file_extensions = ['.' + ext.lstrip('.') for ext in file_extensions]

    synthesis_types_list = list(synthesis_types)
    if "all" in synthesis_types_list:
        synthesis_types_list = ["executive", "adhd", "technical"]

    config = PipelineConfig(
        source_directory=source_path,
        output_directory=output_path,
        enable_adhd_extraction=adhd,
        enable_multi_angle=multi_angle,
        file_extensions=file_extensions,
        confidence_threshold=confidence,
        generate_tsv_registries=tsv,
        generate_embeddings=embeddings,
        embedding_model=embedding_model,
        milvus_uri=milvus_uri,
        export_json=(format == "json"),
        export_csv=(format == "csv"),
        export_markdown=(format == "markdown"),
        enable_synthesis=synthesis,
        synthesis_types=synthesis_types_list,
        synthesis_format=synthesis_format,
    )

    console.logger.info(f"[info]🚀 Starting unified document pipeline...[/info]")
    console.logger.info(f"[info]📁 Source: {source_path}[/info]")
    console.logger.info(f"[info]📤 Output: {output_path}[/info]")

    with branded_progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing pipeline...", total=None)

        try:
            pipeline = UnifiedDocumentPipeline(config)
            result = pipeline.process_documents()

            if result.success:
                progress.update(task, description="Pipeline completed successfully! ✅", completed=True)

                console.print(
                    styled_panel(
                        f"🎯 Pipeline Results:\n\n"
                        f"• Processing time: {result.processing_time:.2f}s\n"
                        f"• Documents processed: {result.document_count}\n"
                        f"• Total entities extracted: {result.total_entities}\n"
                        f"• TSV registries: {len(result.registry_files or {})}\n"
                        f"• Vector embeddings: {result.vector_count}\n"
                        f"• Output files: {len(result.output_files or [])}\n\n"
                        f"📊 Configuration:\n"
                        f"• ADHD extraction: {'✅' if adhd else '❌'}\n"
                        f"• Multi-angle extraction: {'✅' if multi_angle else '❌'}\n"
                        f"• TSV registries: {'✅' if tsv else '❌'}\n"
                        f"• Vector embeddings: {'✅' if embeddings else '❌'}\n"
                        f"• Confidence threshold: {confidence}",
                        title="🚀 Pipeline Complete",
                        border_style="success",
                    )
                )

                if result.output_files:
                    console.logger.info("\n[success]📤 Generated files:[/success]")
                    for file_path in result.output_files:
                        console.logger.info(f"  • {file_path}")

                if result.registry_files:
                    console.logger.info("\n[success]📊 TSV registries:[/success]")
                    for name, path in result.registry_files.items():
                        count = result.registry_counts.get(name, 0) if result.registry_counts else 0
                        console.logger.info(f"  • {name}: {path} ({count} entries)")

                if result.embedding_summary:
                    console.logger.info("\n[success]🔍 Embeddings:[/success]")
                    console.logger.info(f"  • Model: {result.embedding_summary.get('model', 'N/A')}")
                    console.logger.info(f"  • Vectors: {result.vector_count}")

            else:
                progress.update(task, description="Pipeline failed ❌", completed=True)
                console.logger.error(f"[error]❌ Pipeline failed: {result.error_message}[/error]")
                sys.exit(1)

        except Exception as e:
            progress.update(task, description="Error occurred", completed=True)
            console.logger.error(f"[error]❌ Pipeline execution failed: {e}[/error]")
            if ctx.obj.get("verbose"):
                import traceback
                traceback.print_exc()
            sys.exit(1)


@extract.command("cleanup")
@click.argument("directory", default=".")
@click.option(
    "--dry-run/--execute",
    default=True,
    help="🛡️  Preview the cleanup ritual without purging any assets (default: dry-run).",
)
@click.option(
    "--cleanup-types",
    multiple=True,
    type=click.Choice(["temporary", "cache", "outputs", "interim", "all"]),
    default=["temporary", "cache", "interim"],
    help="📊 Categorization of files to be purged: temporary, cache, outputs, or interim.",
)
@click.option(
    "--include-outputs/--preserve-outputs",
    default=False,
    help="🔥 Force the inclusion of final output files in the cleanup purge.",
)
@click.option(
    "--report-format",
    type=click.Choice(["table", "json", "detailed"]),
    default="detailed",
    help="🛠️  Output format for the cleanup diagnostic report: table, json, or detailed.",
)
@click.option(
    "--report-file", help="📂 Target file path for saving the cleanup diagnostic report."
)
@click.pass_context
def extract_cleanup(
    ctx,
    directory: str,
    dry_run: bool,
    cleanup_types: tuple,
    include_outputs: bool,
    report_format: str,
    report_file: Optional[str],
):
    """🧹 Flight-Deck: Execute pipeline cleanup ritual and generate activity report.

    Purge temporary assets, cache files, and interim artifacts generated
    during the pipeline processing. This command ensures the cockpit remains
    clear of stale data and provides a detailed audit of the cleanup operation.
    Default behavior preserves output files and runs in dry-run mode for safety.
    """
    with mobile_task_notification(
        ctx,
        "Pipeline cleanup",
        success_message="✅ Pipeline cleanup complete",
        failure_message="❌ Pipeline cleanup failed",
    ):
        _run_extract_cleanup(
            ctx,
            directory,
            dry_run,
            cleanup_types,
            include_outputs,
            report_format,
            report_file,
        )


def _run_extract_cleanup(
    ctx,
    directory: str,
    dry_run: bool,
    cleanup_types: tuple,
    include_outputs: bool,
    report_format: str,
    report_file: Optional[str],
) -> None:
    import json
    from datetime import datetime

    # Import cleanup modules
    try:
        from ..extraction.cleanup import PipelineCleanup, CleanupConfig
    except ImportError as e:
        console.logger.info(f"[error]❌ Could not import cleanup modules: {e}[/error]")
        console.logger.info("[warning]💡 Make sure the extraction package is properly installed[/warning]")
        sys.exit(1)

    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.logger.info(f"[error]❌ Target directory does not exist: {target_path}[/error]")
        sys.exit(1)

    # Configure cleanup
    cleanup_types_list = list(cleanup_types)
    if "all" in cleanup_types_list:
        cleanup_types_list = ["temporary", "cache", "outputs", "interim"]
    elif include_outputs and "outputs" not in cleanup_types_list:
        cleanup_types_list.append("outputs")

    config = CleanupConfig(
        cleanup_types=cleanup_types_list,
        dry_run=dry_run,
        preserve_recent_hours=0,  # Clean all matching files
        include_hidden=False,
        backup_before_delete=False  # For safety in dry-run mode
    )

    console.logger.info(f"[info]🧹 {'Previewing' if dry_run else 'Executing'} pipeline cleanup...[/info]")
    console.logger.info(f"[info]📁 Target: {target_path}[/info]")
    console.logger.info(f"[info]🎯 Cleanup types: {', '.join(cleanup_types_list)}[/info]")

    if dry_run:
        console.logger.info("[warning]⚠️  DRY RUN: No files will actually be removed[/warning]")

    with branded_progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning for cleanup candidates...", total=None)

        try:
            # Create cleanup system and generate mock activity report
            cleanup = PipelineCleanup(config)

            # For cleanup command, we simulate an activity report for the target directory
            mock_activity_report = {
                "operation_summary": {
                    "start_time": datetime.now().isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "total_operations": 0,
                    "directories_scanned": [str(target_path)]
                },
                "file_operations": {
                    "created": [],
                    "modified": [],
                    "deleted": [],
                    "moved": []
                },
                "size_tracking": {
                    "total_bytes_created": 0,
                    "total_bytes_modified": 0,
                    "total_bytes_deleted": 0
                },
                "categorization": {
                    "by_extension": {},
                    "by_operation": {},
                    "by_directory": {}
                }
            }

            progress.update(task, description="Performing cleanup analysis...")

            # Perform cleanup
            result = cleanup.cleanup_pipeline_files(mock_activity_report, target_path)

            if result.success:
                progress.update(task, description=f"Cleanup {'preview' if dry_run else 'execution'} completed! ✅", completed=True)

                # Generate detailed report
                if report_format == "detailed":
                    console.print(
                        styled_panel(
                            f"🧹 Cleanup Results:\n\n"
                            f"• Files removed: {result.files_removed}\n"
                            f"• Space freed: {result.space_freed / (1024*1024):.2f} MB\n"
                            f"• Processing time: {result.processing_time:.2f}s\n"
                            f"• Errors: {len(result.errors)}\n\n"
                            f"📊 File Types Cleaned:\n"
                            + "\n".join([f"• {category}: {count} files"
                                       for category, count in result.files_by_category.items()]),
                            title=f"🧹 Cleanup {'Preview' if dry_run else 'Complete'}",
                            border_style="success" if result.success else "red",
                        )
                    )

                    # Show detailed file lists
                    if result.removed_files:
                        console.logger.info(f"\n[success]{'📋 Files to be removed:' if dry_run else '🗑️  Files removed:'}[/success]")
                        for file_path in result.removed_files[:20]:  # Show first 20
                            file_size = file_path.stat().st_size if file_path.exists() else 0
                            size_str = f"({file_size / 1024:.1f} KB)" if file_size > 0 else ""
                            console.logger.info(f"  • {file_path.relative_to(target_path)} {size_str}")

                        if len(result.removed_files) > 20:
                            console.logger.info(f"  ... and {len(result.removed_files) - 20} more files")

                    # Show errors if any
                    if result.errors:
                        console.logger.error(f"\n[error]⚠️  Errors encountered:[/error]")
                        for error in result.errors[:5]:  # Show first 5 errors
                            console.logger.error(f"  • {error}")
                        if len(result.errors) > 5:
                            console.logger.error(f"  ... and {len(result.errors) - 5} more errors")

                elif report_format == "table":
                    # Create a summary table
                    table = styled_table(
                        f"Cleanup {'Preview' if dry_run else 'Results'}",
                        ("Category", {"style": "info"}),
                        ("Files", {"justify": "right", "style": "magenta"}),
                        ("Size", {"justify": "right", "style": "success"}),
                    )

                    for category, count in result.files_by_category.items():
                        # Calculate size for this category
                        category_size = sum(
                            f.stat().st_size if f.exists() else 0
                            for f in result.removed_files
                            if category.lower() in str(f).lower()
                        )
                        size_mb = category_size / (1024 * 1024)
                        table.add_row(category, str(count), f"{size_mb:.2f} MB")

                    console.logger.info(table)

                elif report_format == "json":
                    # JSON summary
                    json_result = {
                        "cleanup_summary": {
                            "dry_run": dry_run,
                            "success": result.success,
                            "files_removed": result.files_removed,
                            "space_freed_mb": result.space_freed / (1024*1024),
                            "processing_time": result.processing_time,
                            "target_directory": str(target_path),
                            "cleanup_types": cleanup_types_list
                        },
                        "file_categories": result.files_by_category,
                        "removed_files": [str(f) for f in result.removed_files],
                        "errors": result.errors,
                        "timestamp": datetime.now().isoformat()
                    }
                    console.logger.info(json.dumps(json_result, indent=2))

                # Save report to file if requested
                if report_file:
                    report_path = Path(report_file)
                    report_data = {
                        "cleanup_summary": {
                            "dry_run": dry_run,
                            "success": result.success,
                            "files_removed": result.files_removed,
                            "space_freed_mb": result.space_freed / (1024*1024),
                            "processing_time": result.processing_time,
                            "target_directory": str(target_path),
                            "cleanup_types": cleanup_types_list,
                            "timestamp": datetime.now().isoformat()
                        },
                        "detailed_results": {
                            "file_categories": result.files_by_category,
                            "removed_files": [str(f) for f in result.removed_files],
                            "errors": result.errors
                        }
                    }

                    with open(report_path, 'w') as f:
                        json.dump(report_data, f, indent=2)

                    console.logger.info(f"\n[success]📄 Report saved to: {report_path}[/success]")

            else:
                progress.update(task, description="Cleanup failed ❌", completed=True)
                console.logger.error(f"[error]❌ Cleanup failed: {result.error_message}[/error]")
                sys.exit(1)

        except Exception as e:
            progress.update(task, description="Error occurred", completed=True)
            console.logger.error(f"[error]❌ Cleanup execution failed: {e}[/error]")
            if ctx.obj.get("verbose"):
                import traceback
                traceback.print_exc()
            sys.exit(1)


# ---------------------------------------------------------------------------
# Helper: load extraction_hygiene module dynamically
# ---------------------------------------------------------------------------

def _load_hygiene_module():
    """Load extraction_hygiene.py without requiring it to be on sys.path."""
    repo_root = Path(__file__).resolve().parents[3]
    mod_path = repo_root / "services" / "repo-truth-extractor" / "extraction_hygiene.py"
    if not mod_path.exists():
        return None, None
    spec = importlib.util.spec_from_file_location("extraction_hygiene", mod_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["extraction_hygiene"] = mod
    spec.loader.exec_module(mod)
    return mod, repo_root


def _hygiene_severity_color(level: str) -> str:
    return {"error": "bold red", "warning": "bold yellow", "info": "cyan"}.get(level, "white")


# ---------------------------------------------------------------------------
# truth-run command
# ---------------------------------------------------------------------------

@extract.command("truth-run")
@click.option(
    "--run-id",
    default=None,
    help="🆔 Unique session identifier for the ritual run (defaults to auto-generated timestamp).",
)
@click.option(
    "--phase",
    default="ALL",
    show_default=True,
    help="📊 Specific extraction phase(s) to engage (e.g. A, A,B, ALL).",
)
@click.option(
    "--workers",
    "-w",
    default=10,
    show_default=True,
    help="⚡ Number of concurrent ritual workers allocated for the partitioning phase.",
)
@click.option(
    "--routing-policy",
    default="balanced_openrouter",
    show_default=True,
    help="📊 LLM routing policy for the extraction ritual (e.g., balanced_openrouter, high_fidelity).",
)
@click.option(
    "--doctor",
    is_flag=True,
    help="🩺 Execute provider preflight doctor diagnostics before starting the ritual.",
)
@click.option(
    "--resume",
    is_flag=True,
    help="⏯️  Resume a suspended ritual run, skipping already-validated partitions.",
)
@click.option(
    "--import-v3",
    "import_v3_run_id",
    default=None,
    metavar="RUN_ID",
    help="📦 Migrate a legacy v3 ritual run into the v5 runs directory before resuming. Copies artifacts, sets --resume, and pins the session ID.",
)
@click.option(
    "--skip-hygiene",
    is_flag=True,
    help="⏩ Skip the pre-flight hygiene scan and proceed directly to extraction (use with caution).",
)
@click.option(
    "--apply-cleanup",
    is_flag=True,
    help="🧹 Apply quarantine cleanup and purge hazards identified during the hygiene scan.",
)
@click.option(
    "--force",
    is_flag=True,
    help="🚀 Force the extraction ritual to proceed even if hygiene diagnostics report critical errors.",
)
@click.option(
    "--skip-prescan",
    is_flag=True,
    help="⏩ Skip the integrated Stage 0 prescan.",
)
@click.option(
    "--prescan-import-dir",
    type=str,
    help="📥 Import precomputed prescan artifacts from an external directory.",
)
@click.option(
    "--prescan-online",
    is_flag=True,
    help="📡 Authorize online LLM passes during the integrated prescan stage.",
)
@click.option(
    "--prescan-allow-scope-reduction",
    is_flag=True,
    help="⚖️  Allow prescan intelligence to reduce the extraction scope based on duplicate/noise hints.",
)
@click.option(
    "--allow-online-llm",
    is_flag=True,
    help="💸 Authorize online LLM spend for the entire ritual run (including prescan).",
)
@click.pass_context
def truth_run(
    ctx,
    run_id: Optional[str],
    phase: str,
    workers: int,
    routing_policy: str,
    doctor: bool,
    resume: bool,
    import_v3_run_id: Optional[str],
    skip_hygiene: bool,
    apply_cleanup: bool,
    force: bool,
    skip_prescan: bool,
    prescan_import_dir: Optional[str],
    prescan_online: bool,
    prescan_allow_scope_reduction: bool,
    allow_online_llm: bool,
):
    """🔬 Ritual Daemon: Full extraction workflow — Hygiene scan → Optional cleanup → v5 Extraction execution.

    Engage the ultimate repo-truth-extractor sequence. This ritual synchronizes
    pre-flight hygiene checks to catch stale artifacts, noisy paths, and
    version/path mismatches before they contaminate extraction output.
    The cockpit monitors and streams live telemetry during the v5 extraction.

    \b
    Ritual Phases:
      0. (Optional) Migrate legacy v3 session into v5 cockpit (--import-v3 RUN_ID)
      1. Pre-flight hygiene diagnostic scan (read-only sensors)
      2. Optional quarantine cleanup and hazard purging (requires --apply-cleanup)
      3. Ignite v5 extraction engines with live telemetry streaming output

    \b
    To resume a legacy v3 session in the v5 cockpit:
      dopemux extract truth-run --import-v3 FULL_RUN --resume
    """
    import shutil

    # ------------------------------------------------------------------
    # Phase 0: Migrate v3 run into v5 directory
    # ------------------------------------------------------------------
    _v3_root = Path("extraction/repo-truth-extractor/v3")
    _v5_root = Path("extraction/repo-truth-extractor/v5")

    if import_v3_run_id:
        # --import-v3 implies --resume and pins the run_id
        resume = True
        if run_id is None:
            run_id = import_v3_run_id

        console.print()
        console.print(styled_panel(
            f"[magenta]Phase 0 · Migrate v3 → v5[/magenta]\n"
            f"[text.dim]Importing run[/text.dim] [bold]{import_v3_run_id}[/bold] "
            f"[text.dim]from v3 into v5 runs directory[/text.dim]",
            title="Phase 0",
            border_style="magenta",
        ))

        v3_run_src = _v3_root / "runs" / import_v3_run_id
        v5_runs_dir = _v5_root / "runs"
        v5_run_dst = v5_runs_dir / import_v3_run_id
        v5_latest = _v5_root / "latest_run_id.txt"

        if not v3_run_src.exists():
            console.print(f"[error]❌ v3 run not found:[/error] {v3_run_src}")
            console.print(f"[dim]Available v3 runs:[/dim]")
            if (_v3_root / "runs").exists():
                for d in sorted((_v3_root / "runs").iterdir()):
                    if d.is_dir():
                        console.print(f"  [dim]• {d.name}[/dim]")
            sys.exit(1)

        if v5_run_dst.exists():
            console.print(
                f"[warning]⚠️  v5 run already exists:[/warning] [text.dim]{v5_run_dst}[/text.dim]\n"
                f"[text.dim]Skipping copy — will resume using existing v5 artifacts.[/text.dim]"
            )
        else:
            # Count what we're copying for the progress display
            v3_files = list(v3_run_src.rglob("*"))
            n_files = sum(1 for f in v3_files if f.is_file())
            n_phases = sum(1 for d in v3_run_src.iterdir() if d.is_dir() and not d.name.startswith("."))

            console.print(
                f"[info]📦 Copying[/info] [bold]{n_files}[/bold] files across "
                f"[bold]{n_phases}[/bold] phase dirs…"
            )

            with branded_progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task(
                    f"[magenta]Copying {import_v3_run_id} → v5/runs/{import_v3_run_id}…",
                    total=None,
                )
                v5_runs_dir.mkdir(parents=True, exist_ok=True)
                shutil.copytree(str(v3_run_src), str(v5_run_dst))
                progress.update(task, completed=True)

            console.print(f"[success]✅ Copied:[/success] {v3_run_src} → {v5_run_dst}")

        # Show phase summary table
        _display_v3_migration_summary(v5_run_dst, import_v3_run_id, console)

        # Update v5 latest_run_id.txt
        _v5_root.mkdir(parents=True, exist_ok=True)
        v5_latest.write_text(import_v3_run_id + "\n", encoding="utf-8")
        console.print(f"[dim]📝 Updated v5/latest_run_id.txt → {import_v3_run_id}[/dim]")

    auto_run_id, display_run_id, cmd = _build_truth_run_command(
        runner_path=None,
        run_id=run_id,
        phase=phase,
        workers=workers,
        routing_policy=routing_policy,
        doctor=doctor,
        resume=resume,
        skip_prescan=skip_prescan,
        prescan_import_dir=prescan_import_dir,
        prescan_online=prescan_online,
        prescan_allow_scope_reduction=prescan_allow_scope_reduction,
        allow_online_llm=allow_online_llm,
    )

    resume_indicator = " [success]+resume[/success]" if resume else ""
    console.print(styled_panel(
        f"[mint]🔬 dopemux extract truth-run[/mint]\n"
        f"[text.dim]run_id=[/text.dim][bold]{display_run_id}[/bold]  "
        f"[text.dim]phase=[/text.dim][bold]{phase}[/bold]  "
        f"[text.dim]workers=[/text.dim][bold]{workers}[/bold]  "
        f"[text.dim]routing=[/text.dim][magenta]{routing_policy}[/magenta]"
        f"{resume_indicator}",
        title="🔬 Truth Run",
        border_style="panel.border",
    ))

    # ------------------------------------------------------------------
    # Phase 1: Hygiene scan
    # ------------------------------------------------------------------
    if skip_hygiene:
        console.print("[dim]⏩ Pre-flight hygiene scan skipped (--skip-hygiene)[/dim]")
        scan = None
        mod = None
        repo_root = Path.cwd()
    else:
        console.print()
        console.print(styled_panel("[mint]Phase 1 · Pre-flight Hygiene Scan[/mint]", title="Phase 1"))

        with branded_progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("[info]Scanning repo surfaces…", total=None)
            mod, repo_root = _load_hygiene_module()
            if mod is None:
                console.print("[error]❌ extraction_hygiene.py not found — cannot run pre-flight scan.[/error]")
                console.print("[dim]Hint: expected at services/repo-truth-extractor/extraction_hygiene.py[/dim]")
                if not force:
                    sys.exit(1)
                scan = None
            else:
                scan = mod.run_scan(repo_root=repo_root)
            progress.update(task, completed=True)

        if scan is not None:
            _display_scan_results(scan, console)

            error_count = len(scan.errors)
            warn_count = len(scan.warnings)

            if error_count > 0 and not force:
                console.print(
                    f"\n[error]🚫 Hygiene scan found {error_count} error(s). "
                    "Aborting. Use --force to override.[/error]"
                )
                sys.exit(1)
            elif error_count > 0:
                console.print(f"\n[warning]⚠️  {error_count} error(s) found — proceeding anyway (--force)[/warning]")
            elif warn_count > 0:
                console.print(f"\n[warning]⚠️  {warn_count} warning(s) found.[/warning]")
            else:
                console.print("\n[success]✅ Hygiene scan clean — no issues found.[/success]")

    # ------------------------------------------------------------------
    # Phase 2: Optional cleanup
    # ------------------------------------------------------------------
    if apply_cleanup and mod is not None and scan is not None:
        console.print()
        console.print(styled_panel("[warning]Phase 2 · Quarantine Cleanup[/warning]", title="Phase 2"))

        with branded_progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("[warning]Applying cleanup…", total=None)
            plan = mod.run_apply(repo_root=repo_root, dry_run=False)
            progress.update(task, completed=True)

        moved = [a for a in plan.applied_actions if a.action == "move_to_quarantine"]
        if moved:
            tbl = styled_table("Quarantine Actions", "Action", ("Path", {"style": "text.dim"}), ("Reason", {"style": "info"}), compact=True)
            for a in moved:
                tbl.add_row("→ quarantined", str(a.source.relative_to(repo_root)), a.reason)
            console.print(tbl)
            if plan.manifest_path:
                console.print(f"[dim]📄 Manifest: {plan.manifest_path}[/dim]")
        else:
            console.print("[success]✅ Nothing to quarantine.[/success]")
    elif apply_cleanup and (mod is None or scan is None):
        console.print("[dim]⏩ Cleanup skipped (hygiene module unavailable).[/dim]")

    # ------------------------------------------------------------------
    # Phase 3: Launch extraction
    # ------------------------------------------------------------------
    console.print()
    console.print(styled_panel(
        f"[success]Phase 3 · Running v5 Extraction[/success]\n"
        f"[text.dim]Launching run_extraction_v5.py — output streams below[/text.dim]",
        title="Phase 3",
        border_style="success",
    ))

    runner_path = _find_runner(repo_root if not skip_hygiene else Path.cwd())
    if runner_path is None:
        console.print("[error]❌ run_extraction_v5.py not found. Check services/repo-truth-extractor/.[/error]")
        sys.exit(1)

    auto_run_id, _, cmd = _build_truth_run_command(
        runner_path=runner_path,
        run_id=run_id,
        phase=phase,
        workers=workers,
        routing_policy=routing_policy,
        doctor=doctor,
        resume=resume,
    )

    console.print(f"[dim]$ {' '.join(cmd)}[/dim]")
    console.print()

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, bufsize=1, cwd=str(repo_root if not skip_hygiene else Path.cwd()))
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="", flush=True)
        proc.wait()
        if proc.returncode != 0:
            console.print(f"\n[error]❌ Extraction exited with code {proc.returncode}[/error]")
            sys.exit(proc.returncode)
        else:
            console.print("\n[success]✅ Extraction complete.[/success]")
    except KeyboardInterrupt:
        console.print("\n[warning]⚠️  Interrupted.[/warning]")
        sys.exit(130)


def _build_truth_run_command(
    *,
    runner_path: Optional[Path],
    run_id: Optional[str],
    phase: str,
    workers: int,
    routing_policy: str,
    doctor: bool,
    resume: bool,
    skip_prescan: bool = False,
    prescan_import_dir: Optional[str] = None,
    prescan_online: bool = False,
    prescan_allow_scope_reduction: bool = False,
    allow_online_llm: bool = False,
) -> tuple[Optional[str], str, list[str]]:
    """Build the v5 runner command while preserving latest-run resume semantics."""
    effective_run_id: Optional[str]
    if run_id:
        effective_run_id = run_id
    elif resume:
        effective_run_id = None
    else:
        effective_run_id = datetime.now().strftime("RUN-%Y%m%dT%H%M%S")

    display_run_id = effective_run_id or "latest_run_id.txt"
    cmd = [
        sys.executable,
        str(runner_path) if runner_path is not None else "<runner>",
        "--phase",
        phase,
        "--partition-workers",
        str(workers),
        "--routing-policy",
        routing_policy,
    ]
    if effective_run_id is not None:
        cmd.extend(["--run-id", effective_run_id])
    if doctor:
        cmd.append("--doctor")
    if resume:
        cmd.append("--resume")
    
    # ── Integrated Prescan Flags ──
    if skip_prescan:
        cmd.append("--skip-prescan")
    if prescan_import_dir:
        cmd.extend(["--prescan-import-dir", prescan_import_dir])
    if prescan_online:
        cmd.append("--prescan-online")
    if prescan_allow_scope_reduction:
        cmd.append("--prescan-allow-scope-reduction")
    if allow_online_llm:
        cmd.append("--allow-online-llm")
        
    return effective_run_id, display_run_id, cmd


def _find_runner(repo_root: Path) -> Optional[Path]:
    """Locate run_extraction_v5.py relative to repo_root."""
    candidate = repo_root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    if candidate.exists():
        return candidate
    # Fallback: search upward
    for parent in [Path.cwd()] + list(Path.cwd().parents):
        c = parent / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
        if c.exists():
            return c
    return None


def _display_scan_results(scan, console) -> None:
    """Render hygiene scan results to the console."""
    # Version path
    if scan.version_path_issues:
        for issue in scan.version_path_issues:
            console.print(f"[error]🔗 VERSION_PATH_MISMATCH:[/error] {issue.message}")
    else:
        console.print("[success]🔗 Version/path wiring:[/success] [success]v5 code → v5 output ✅[/success]")

    # Noise paths
    if scan.noise_paths:
        tbl = styled_table("⚠️  Noisy Paths Detected", "Path", ("Category", {"style": "warning"}), compact=True)
        for np in scan.noise_paths[:20]:
            tbl.add_row(np.path, np.category)
        if len(scan.noise_paths) > 20:
            tbl.add_row(f"… and {len(scan.noise_paths) - 20} more", "")
        console.print(tbl)
    else:
        console.print("[success]📁 Noise paths:[/success] [success]none found ✅[/success]")

    # Resume hazards
    if scan.resume_state_issues:
        tbl = styled_table("⚠️  Resume-State Hazards", ("Severity", {"style": "error"}), ("Type", {"style": "error"}), ("Path", {"style": "text.dim"}), compact=True)
        shown = scan.resume_state_issues[:15]
        for ri in shown:
            tbl.add_row(ri.severity, ri.issue_type, str(ri.path))
        if len(scan.resume_state_issues) > 15:
            tbl.add_row("", f"… and {len(scan.resume_state_issues) - 15} more", "")
        console.print(tbl)

    # Authority summary
    if scan.authority_summary:
        tbl = styled_table("📚 Authority Classification Summary", ("Tier", {"style": "mint"}), ("Count", {"justify": "right"}), compact=True)
        for tier, count in sorted(scan.authority_summary.items()):
            tbl.add_row(tier, str(count))
        console.print(tbl)


def _display_v3_migration_summary(v5_run_dir: "Path", run_id: str, console: "Console") -> None:
    """Show a table summarising phases found in the migrated run directory."""
    if not v5_run_dir.exists():
        return

    phase_dirs = sorted(
        [d for d in v5_run_dir.iterdir() if d.is_dir() and not d.name.startswith(".")],
        key=lambda d: d.name,
    )
    if not phase_dirs:
        return

    tbl = styled_table(
        f"📊 Migrated run: {run_id}",
        ("Phase dir", {"style": "bold"}),
        ("Raw outputs", {"justify": "right", "style": "success"}),
        ("FAILED markers", {"justify": "right", "style": "error"}),
        ("Norm outputs", {"justify": "right", "style": "info"}),
        ("QA outputs", {"justify": "right", "style": "info"}),
    )

    for phase_dir in phase_dirs:
        raw_dir = phase_dir / "raw"
        norm_dir = phase_dir / "norm"
        qa_dir = phase_dir / "qa"

        def _count(d: "Path", pattern: str) -> str:
            if not d.exists():
                return "[dim]—[/dim]"
            return str(sum(1 for _ in d.glob(pattern)))

        raw_ok = _count(raw_dir, "*.json")
        raw_fail = _count(raw_dir, "*.FAILED.*")
        norm_ok = _count(norm_dir, "*.json")
        qa_ok = _count(qa_dir, "*.json")

        tbl.add_row(phase_dir.name, raw_ok, raw_fail, norm_ok, qa_ok)

    console.print(tbl)
    console.print(
        f"[text.dim]Phases with existing raw/*.json will be [success]skipped[/success] "
        f"by v5 resume. Failed partitions will be [warning]retried[/warning].[/text.dim]"
    )
