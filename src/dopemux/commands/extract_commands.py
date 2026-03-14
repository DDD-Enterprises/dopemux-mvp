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
from rich import box
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text

from ..console import console

@click.group()
@click.pass_context
def extract(ctx):
    """
    📄 Document extraction with ADHD-optimized patterns

    Extract entities, configurations, and patterns from documentation
    using specialized extractors for markdown, YAML, and ADHD content.
    """
    pass


@extract.command("docs")
@click.argument("directory", default=".")
@click.option(
    "--mode", "-m",
    type=click.Choice(["basic", "detailed", "adhd"]),
    default="basic",
    help="Extraction mode: basic (key-value), detailed (all patterns), adhd (ADHD-specific)"
)
@click.option(
    "--format", "-f",
    type=click.Choice(["json", "csv", "markdown", "yaml"]),
    default="json",
    help="Output format for extracted entities"
)
@click.option("--output", "-o", help="Output file path (default: print to stdout)")
@click.option("--confidence", "-c", type=float, default=0.5, help="Minimum confidence threshold (0.0-1.0)")
@click.option("--extensions", help="File extensions to process (default: .md,.yaml,.yml)")
@click.option("--adhd-profile", "-p", is_flag=True, help="Extract ADHD accommodation profile")
@click.pass_context
def extract_docs(
    ctx,
    directory: str,
    mode: str,
    format: str,
    output: Optional[str],
    confidence: float,
    extensions: Optional[str],
    adhd_profile: bool
):
    """
    📄 Extract entities from documentation files

    Process markdown and YAML files to extract structured information
    using ADHD-optimized patterns and confidence scoring.
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
        console.logger.info(f"[red]❌ Could not import extraction modules: {e}[/red]")
        console.logger.info("[yellow]💡 Make sure you're in the dopemux-mvp directory[/yellow]")
        sys.exit(1)

    source_path = Path(directory).resolve()
    if not source_path.exists():
        console.logger.info(f"[red]❌ Directory does not exist: {source_path}[/red]")
        sys.exit(1)

    if not extensions:
        extensions = ".md,.yaml,.yml,.json"

    with Progress(
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
            console.logger.error(f"[red]❌ Extraction failed: {e}[/red]")
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
            console.logger.info("[yellow]⚠️ PyYAML not available, falling back to JSON[/yellow]")
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
        console.logger.info(f"[green]✅ Results written to {output_path}[/green]")
    else:
        console.logger.info(output_text)

    console.print(
        Panel(
            f"🎯 Extraction Summary:\n\n"
            f"• Mode: {mode}\n"
            f"• Documents: {results.get('documents_processed', 0)}\n"
            f"• Entities: {filtered_count}/{total_entities}\n"
            f"• Entity types: {len(filtered_entities)}\n"
            f"• Format: {format}",
            title="📊 Results",
            border_style="green",
        )
    )


@extract.command("pipeline")
@click.argument("directory", default=".")
@click.option("--output", "-o", help="Output directory for pipeline results", default="./output")
@click.option(
    "--adhd/--no-adhd",
    default=True,
    help="Enable/disable ADHD-specific extraction patterns"
)
@click.option(
    "--multi-angle/--no-multi-angle",
    default=True,
    help="Enable/disable multi-angle entity extraction"
)
@click.option(
    "--embeddings/--no-embeddings",
    default=True,
    help="Enable/disable vector embedding generation"
)
@click.option(
    "--tsv/--no-tsv",
    default=True,
    help="Enable/disable TSV registry generation"
)
@click.option(
    "--confidence", "-c",
    type=float,
    default=0.5,
    help="Minimum confidence threshold for entities (0.0-1.0)"
)
@click.option(
    "--embedding-model", "-m",
    default="voyage-context-3",
    help="Embedding model to use"
)
@click.option("--milvus-uri", help="Milvus database URI for vector storage")
@click.option("--extensions", help="File extensions to process (default: .md,.yaml,.yml,.json,.txt)")
@click.option(
    "--format", "-f",
    type=click.Choice(["json", "csv", "markdown"]),
    default="json",
    help="Output format for extraction results"
)
@click.option(
    "--synthesis/--no-synthesis",
    default=True,
    help="Enable/disable document synthesis generation"
)
@click.option(
    "--synthesis-types",
    multiple=True,
    type=click.Choice(["executive", "adhd", "technical", "all"]),
    default=["executive", "adhd"],
    help="Types of synthesis to generate (can specify multiple)"
)
@click.option(
    "--synthesis-format",
    type=click.Choice(["markdown", "json", "both"]),
    default="markdown",
    help="Output format for synthesis results"
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
    synthesis_format: str
):
    """
    🚀 Complete document processing pipeline

    Run the full unified pipeline including multi-layer extraction,
    atomic unit normalization, TSV registry generation, and vector
    embeddings. Integrates all extraction systems into a single workflow.
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
        console.logger.info(f"[red]❌ Could not import pipeline modules: {e}[/red]")
        console.logger.info("[yellow]💡 Make sure the extraction package is properly installed[/yellow]")
        sys.exit(1)

    source_path = Path(directory).resolve()
    output_path = Path(output).resolve()

    if not source_path.exists():
        console.logger.info(f"[red]❌ Source directory does not exist: {source_path}[/red]")
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

    console.logger.info(f"[blue]🚀 Starting unified document pipeline...[/blue]")
    console.logger.info(f"[blue]📁 Source: {source_path}[/blue]")
    console.logger.info(f"[blue]📤 Output: {output_path}[/blue]")

    with Progress(
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
                    Panel(
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
                        border_style="green",
                    )
                )

                if result.output_files:
                    console.logger.info("\n[green]📤 Generated files:[/green]")
                    for file_path in result.output_files:
                        console.logger.info(f"  • {file_path}")

                if result.registry_files:
                    console.logger.info("\n[green]📊 TSV registries:[/green]")
                    for name, path in result.registry_files.items():
                        count = result.registry_counts.get(name, 0) if result.registry_counts else 0
                        console.logger.info(f"  • {name}: {path} ({count} entries)")

                if result.embedding_summary:
                    console.logger.info("\n[green]🔍 Embeddings:[/green]")
                    console.logger.info(f"  • Model: {result.embedding_summary.get('model', 'N/A')}")
                    console.logger.info(f"  • Vectors: {result.vector_count}")

            else:
                progress.update(task, description="Pipeline failed ❌", completed=True)
                console.logger.error(f"[red]❌ Pipeline failed: {result.error_message}[/red]")
                sys.exit(1)

        except Exception as e:
            progress.update(task, description="Error occurred", completed=True)
            console.logger.error(f"[red]❌ Pipeline execution failed: {e}[/red]")
            if ctx.obj.get("verbose"):
                import traceback
                traceback.print_exc()
            sys.exit(1)


@extract.command("cleanup")
@click.argument("directory", default=".")
@click.option(
    "--dry-run/--execute",
    default=True,
    help="Preview cleanup without removing files (default: dry-run)"
)
@click.option(
    "--cleanup-types",
    multiple=True,
    type=click.Choice(["temporary", "cache", "outputs", "interim", "all"]),
    default=["temporary", "cache", "interim"],
    help="Types of files to clean (can specify multiple)"
)
@click.option(
    "--include-outputs/--preserve-outputs",
    default=False,
    help="Include output files in cleanup (default: preserve)"
)
@click.option(
    "--report-format",
    type=click.Choice(["table", "json", "detailed"]),
    default="detailed",
    help="Format for cleanup report"
)
@click.option("--report-file", help="Save cleanup report to file")
@click.pass_context
def extract_cleanup(
    ctx,
    directory: str,
    dry_run: bool,
    cleanup_types: tuple,
    include_outputs: bool,
    report_format: str,
    report_file: Optional[str]
):
    """
    🧹 Clean pipeline files and generate activity report

    Remove temporary, cache, and interim files created during pipeline processing.
    Provides detailed reporting on files removed, created, changed, and output.

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
        console.logger.info(f"[red]❌ Could not import cleanup modules: {e}[/red]")
        console.logger.info("[yellow]💡 Make sure the extraction package is properly installed[/yellow]")
        sys.exit(1)

    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.logger.info(f"[red]❌ Target directory does not exist: {target_path}[/red]")
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

    console.logger.info(f"[blue]🧹 {'Previewing' if dry_run else 'Executing'} pipeline cleanup...[/blue]")
    console.logger.info(f"[blue]📁 Target: {target_path}[/blue]")
    console.logger.info(f"[blue]🎯 Cleanup types: {', '.join(cleanup_types_list)}[/blue]")

    if dry_run:
        console.logger.info("[yellow]⚠️  DRY RUN: No files will actually be removed[/yellow]")

    with Progress(
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
                        Panel(
                            f"🧹 Cleanup Results:\n\n"
                            f"• Files removed: {result.files_removed}\n"
                            f"• Space freed: {result.space_freed / (1024*1024):.2f} MB\n"
                            f"• Processing time: {result.processing_time:.2f}s\n"
                            f"• Errors: {len(result.errors)}\n\n"
                            f"📊 File Types Cleaned:\n"
                            + "\n".join([f"• {category}: {count} files"
                                       for category, count in result.files_by_category.items()]),
                            title=f"🧹 Cleanup {'Preview' if dry_run else 'Complete'}",
                            border_style="green" if result.success else "red",
                        )
                    )

                    # Show detailed file lists
                    if result.removed_files:
                        console.logger.info(f"\n[green]{'📋 Files to be removed:' if dry_run else '🗑️  Files removed:'}[/green]")
                        for file_path in result.removed_files[:20]:  # Show first 20
                            file_size = file_path.stat().st_size if file_path.exists() else 0
                            size_str = f"({file_size / 1024:.1f} KB)" if file_size > 0 else ""
                            console.logger.info(f"  • {file_path.relative_to(target_path)} {size_str}")

                        if len(result.removed_files) > 20:
                            console.logger.info(f"  ... and {len(result.removed_files) - 20} more files")

                    # Show errors if any
                    if result.errors:
                        console.logger.error(f"\n[red]⚠️  Errors encountered:[/red]")
                        for error in result.errors[:5]:  # Show first 5 errors
                            console.logger.error(f"  • {error}")
                        if len(result.errors) > 5:
                            console.logger.error(f"  ... and {len(result.errors) - 5} more errors")

                elif report_format == "table":
                    # Create a summary table
                    from rich.table import Table

                    table = Table(title=f"Cleanup {'Preview' if dry_run else 'Results'}")
                    table.add_column("Category", style="cyan")
                    table.add_column("Files", justify="right", style="magenta")
                    table.add_column("Size", justify="right", style="green")

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

                    console.logger.info(f"\n[green]📄 Report saved to: {report_path}[/green]")

            else:
                progress.update(task, description="Cleanup failed ❌", completed=True)
                console.logger.error(f"[red]❌ Cleanup failed: {result.error_message}[/red]")
                sys.exit(1)

        except Exception as e:
            progress.update(task, description="Error occurred", completed=True)
            console.logger.error(f"[red]❌ Cleanup execution failed: {e}[/red]")
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
@click.option("--run-id", default=None, help="Extraction run ID (default: auto timestamp)")
@click.option("--phase", default="ALL", show_default=True, help="Extraction phase(s) to run (e.g. A, A,B, ALL)")
@click.option("--workers", "-w", default=10, show_default=True, help="Partition worker count")
@click.option("--routing-policy", default="balanced_openrouter", show_default=True, help="LLM routing policy")
@click.option("--doctor", is_flag=True, help="Run provider preflight doctor checks")
@click.option("--skip-hygiene", is_flag=True, help="Skip pre-flight hygiene scan")
@click.option("--apply-cleanup", is_flag=True, help="Apply quarantine cleanup if hygiene scan finds hazards")
@click.option("--force", is_flag=True, help="Run extraction even if hygiene scan reports errors")
@click.pass_context
def truth_run(
    ctx,
    run_id: Optional[str],
    phase: str,
    workers: int,
    routing_policy: str,
    doctor: bool,
    skip_hygiene: bool,
    apply_cleanup: bool,
    force: bool,
):
    """
    🔬 Full extraction workflow: hygiene scan → optional cleanup → v5 extraction run.

    Runs the complete repo-truth-extractor pipeline with a pre-flight hygiene
    check to catch stale artifacts, noisy paths, and version/path mismatches
    before they contaminate extraction output.

    \b
    Steps:
      1. Pre-flight hygiene scan (read-only, skippable with --skip-hygiene)
      2. Optional cleanup / quarantine (requires --apply-cleanup)
      3. Launch run_extraction_v5.py with live streaming output
    """
    auto_run_id = run_id or datetime.now().strftime("RUN-%Y%m%dT%H%M%S")

    console.print(Panel(
        Text.from_markup(
            f"[bold cyan]🔬 dopemux extract truth-run[/bold cyan]\n"
            f"[dim]run_id=[/dim][bold]{auto_run_id}[/bold]  "
            f"[dim]phase=[/dim][bold]{phase}[/bold]  "
            f"[dim]workers=[/dim][bold]{workers}[/bold]  "
            f"[dim]routing=[/dim][bold magenta]{routing_policy}[/bold magenta]"
        ),
        box=box.DOUBLE_EDGE,
        border_style="bright_cyan",
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
        console.print(Panel("[bold blue]Phase 1 · Pre-flight Hygiene Scan[/bold blue]", border_style="blue"))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("[cyan]Scanning repo surfaces…", total=None)
            mod, repo_root = _load_hygiene_module()
            if mod is None:
                console.print("[bold red]❌ extraction_hygiene.py not found — cannot run pre-flight scan.[/bold red]")
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
                    f"\n[bold red]🚫 Hygiene scan found {error_count} error(s). "
                    "Aborting. Use --force to override.[/bold red]"
                )
                sys.exit(1)
            elif error_count > 0:
                console.print(f"\n[bold yellow]⚠️  {error_count} error(s) found — proceeding anyway (--force)[/bold yellow]")
            elif warn_count > 0:
                console.print(f"\n[yellow]⚠️  {warn_count} warning(s) found.[/yellow]")
            else:
                console.print("\n[bold green]✅ Hygiene scan clean — no issues found.[/bold green]")

    # ------------------------------------------------------------------
    # Phase 2: Optional cleanup
    # ------------------------------------------------------------------
    if apply_cleanup and mod is not None and scan is not None:
        console.print()
        console.print(Panel("[bold yellow]Phase 2 · Quarantine Cleanup[/bold yellow]", border_style="yellow"))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("[yellow]Applying cleanup…", total=None)
            plan = mod.run_apply(repo_root=repo_root, dry_run=False)
            progress.update(task, completed=True)

        moved = [a for a in plan.applied_actions if a.action == "move_to_quarantine"]
        if moved:
            tbl = Table(box=box.SIMPLE, border_style="yellow")
            tbl.add_column("Action", style="yellow")
            tbl.add_column("Path", style="dim")
            tbl.add_column("Reason", style="cyan")
            for a in moved:
                tbl.add_row("→ quarantined", str(a.source.relative_to(repo_root)), a.reason)
            console.print(tbl)
            if plan.manifest_path:
                console.print(f"[dim]📄 Manifest: {plan.manifest_path}[/dim]")
        else:
            console.print("[green]✅ Nothing to quarantine.[/green]")
    elif apply_cleanup and (mod is None or scan is None):
        console.print("[dim]⏩ Cleanup skipped (hygiene module unavailable).[/dim]")

    # ------------------------------------------------------------------
    # Phase 3: Launch extraction
    # ------------------------------------------------------------------
    console.print()
    console.print(Panel(
        Text.from_markup(
            f"[bold green]Phase 3 · Running v5 Extraction[/bold green]\n"
            f"[dim]Launching run_extraction_v5.py — output streams below[/dim]"
        ),
        border_style="green",
    ))

    runner_path = _find_runner(repo_root if not skip_hygiene else Path.cwd())
    if runner_path is None:
        console.print("[bold red]❌ run_extraction_v5.py not found. Check services/repo-truth-extractor/.[/bold red]")
        sys.exit(1)

    cmd = [sys.executable, str(runner_path), "--phase", phase, "--partition-workers", str(workers),
           "--routing-policy", routing_policy, "--run-id", auto_run_id]
    if doctor:
        cmd.append("--doctor")

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
            console.print(f"\n[bold red]❌ Extraction exited with code {proc.returncode}[/bold red]")
            sys.exit(proc.returncode)
        else:
            console.print("\n[bold green]✅ Extraction complete.[/bold green]")
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Interrupted.[/yellow]")
        sys.exit(130)


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
    from rich.table import Table
    from rich import box as rbox

    # Version path
    if scan.version_path_issues:
        for issue in scan.version_path_issues:
            console.print(f"[bold red]🔗 VERSION_PATH_MISMATCH:[/bold red] {issue.message}")
    else:
        console.print("[green]🔗 Version/path wiring:[/green] [bold green]v5 code → v5 output ✅[/bold green]")

    # Noise paths
    if scan.noise_paths:
        tbl = Table(title="⚠️  Noisy Paths Detected", box=rbox.SIMPLE, border_style="yellow")
        tbl.add_column("Path", style="dim")
        tbl.add_column("Category", style="yellow")
        for np in scan.noise_paths[:20]:
            tbl.add_row(np.path, np.category)
        if len(scan.noise_paths) > 20:
            tbl.add_row(f"… and {len(scan.noise_paths) - 20} more", "")
        console.print(tbl)
    else:
        console.print("[green]📁 Noise paths:[/green] [bold green]none found ✅[/bold green]")

    # Resume hazards
    if scan.resume_state_issues:
        tbl = Table(title="⚠️  Resume-State Hazards", box=rbox.SIMPLE, border_style="red")
        tbl.add_column("Run dir", style="dim")
        tbl.add_column("Issue", style="red")
        for ri in scan.resume_state_issues[:15]:
            tbl.add_row(ri.run_dir, ri.issue_type)
        console.print(tbl)

    # Authority summary
    if scan.authority_summary:
        tbl = Table(title="📚 Authority Classification Summary", box=rbox.SIMPLE, border_style="cyan")
        tbl.add_column("Tier", style="bold cyan")
        tbl.add_column("Count", justify="right")
        for tier, count in sorted(scan.authority_summary.items()):
            tbl.add_row(tier, str(count))
        console.print(tbl)
