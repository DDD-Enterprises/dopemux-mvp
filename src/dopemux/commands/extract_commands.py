"""
Extract Commands

Document extraction with ADHD-optimized patterns.
"""

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
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

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
