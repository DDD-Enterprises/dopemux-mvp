"""
Main document processing orchestrator for Dopemux analysis.

Coordinates the complete pipeline from document discovery through
semantic embedding and registry generation.
"""

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


@dataclass
class ProcessingConfig:
    """Configuration for document processing pipeline."""

    # Input settings
    source_directory: Path
    output_directory: Path

    # Processing options
    max_files: Optional[int] = None
    file_extensions: List[str] = None
    exclude_patterns: List[str] = None

    # Embedding settings
    embedding_model: str = "voyage-context-3"
    milvus_uri: Optional[str] = None
    batch_size: int = 10

    # ADHD optimizations
    chunk_size: int = 25  # Process in 25-minute chunks
    show_progress: bool = True
    gentle_feedback: bool = True

    def __post_init__(self):
        """Set default values after initialization."""
        if self.file_extensions is None:
            self.file_extensions = [
                ".md",
                ".txt",
                ".py",
                ".js",
                ".ts",
                ".jsx",
                ".tsx",
                ".html",
                ".css",
                ".yml",
                ".yaml",
                ".json",
                ".toml",
                ".rst",
                ".adoc",
                ".org",
                ".tex",
            ]

        if self.exclude_patterns is None:
            self.exclude_patterns = [
                "*/node_modules/*",
                "*/.git/*",
                "*/__pycache__/*",
                "*/venv/*",
                "*/env/*",
                "*/build/*",
                "*/dist/*",
                "*/.next/*",
                "*/.nuxt/*",
                "*/target/*",
            ]


class DocumentProcessor:
    """
    Main document processing orchestrator for Dopemux.

    Handles the complete pipeline from document discovery through
    semantic embedding and knowledge extraction.
    """

    def __init__(self, config: ProcessingConfig):
        """Initialize processor with configuration."""
        self.config = config
        self.stats = {
            "files_processed": 0,
            "atomic_units_created": 0,
            "features_extracted": 0,
            "components_identified": 0,
            "subsystems_mapped": 0,
            "research_entries": 0,
            "evidence_links": 0,
            "start_time": None,
            "end_time": None,
        }

        # Initialize sub-processors
        self._init_processors()

    def _init_processors(self):
        """Initialize sub-processing components."""
        # Import here to avoid circular dependencies
        from .embedder import DocumentEmbedder
        from .extractor import MultiAngleExtractor

        # Initialize document embedder
        milvus_config = {}
        if self.config.milvus_uri:
            milvus_config["milvus_uri"] = self.config.milvus_uri

        self.embedder = DocumentEmbedder(
            model_name=self.config.embedding_model, **milvus_config
        )

        # Initialize multi-angle extractor
        self.extractor = MultiAngleExtractor(output_dir=self.config.output_directory)

    def analyze_directory(self) -> Dict[str, Any]:
        """
        Analyze entire directory with ADHD-optimized processing.

        Returns:
            Dict containing processing results and statistics
        """
        self.stats["start_time"] = time.time()

        with console.status("[bold green]Discovering documents...") as status:
            # Phase 1: Document Discovery
            files = self._discover_documents()

            if not files:
                console.print("[yellow]⚠️ No documents found to process[/yellow]")
                return self._get_results()

            console.print(f"[green]📁 Found {len(files)} documents to process[/green]")

            # Phase 2: Document Processing
            status.update("[bold blue]Processing documents...")
            atomic_units = self._process_documents(files)

            # Phase 3: Registry Generation
            status.update("[bold cyan]Generating registries...")
            self._generate_registries(atomic_units)

            # Phase 4: Embedding Generation
            if self.config.milvus_uri:
                status.update("[bold magenta]Creating embeddings...")
                self._create_embeddings(atomic_units)

        self.stats["end_time"] = time.time()
        self._display_completion_summary()

        return self._get_results()

    def _discover_documents(self) -> List[Path]:
        """Discover processable documents in source directory."""
        files = []
        source_path = Path(self.config.source_directory)

        if not source_path.exists():
            console.print(
                f"[red]❌ Source directory does not exist: {source_path}[/red]"
            )
            return files

        # Walk directory tree
        for root, dirs, filenames in os.walk(source_path):
            root_path = Path(root)

            # Skip excluded directories
            if self._should_exclude_path(root_path):
                continue

            for filename in filenames:
                file_path = root_path / filename

                # Check extension
                if file_path.suffix.lower() in self.config.file_extensions:
                    # Check exclusion patterns
                    if not self._should_exclude_path(file_path):
                        files.append(file_path)

                        # Respect max files limit
                        if (
                            self.config.max_files
                            and len(files) >= self.config.max_files
                        ):
                            break

        return sorted(files)

    def _should_exclude_path(self, path: Path) -> bool:
        """Check if path should be excluded from processing."""
        path_str = str(path)

        for pattern in self.config.exclude_patterns:
            # Simple glob-style pattern matching
            if pattern.replace("*", "").strip("/") in path_str:
                return True

        return False

    def _process_documents(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Process documents into atomic units."""
        atomic_units = []

        # ADHD-friendly progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[bold blue]{task.completed}/{task.total}"),
            console=console,
        ) as progress:

            task = progress.add_task("Processing documents...", total=len(files))

            for i, file_path in enumerate(files):
                try:
                    # Process single file
                    units = self._process_single_file(file_path)
                    atomic_units.extend(units)

                    # Update statistics
                    self.stats["files_processed"] += 1
                    self.stats["atomic_units_created"] += len(units)

                    # ADHD-friendly feedback
                    if self.config.gentle_feedback and i % 10 == 0:
                        progress.update(
                            task,
                            description=f"✅ Processed {self.stats['files_processed']} files, {self.stats['atomic_units_created']} units created",
                            completed=i + 1,
                        )
                    else:
                        progress.update(task, completed=i + 1)

                except Exception as e:
                    console.print(
                        f"[yellow]⚠️ Error processing {file_path}: {e}[/yellow]"
                    )
                    continue

        return atomic_units

    def _process_single_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process a single file into atomic units."""
        # Simple processing - break files into manageable chunks
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return []  # Skip files that can't be read

        # Break content into logical sections
        atomic_units = []

        # Split by double newlines (paragraphs/sections)
        sections = content.split("\n\n")

        for i, section in enumerate(sections):
            section = section.strip()
            if len(section) < 10:  # Skip very short sections
                continue

            # Create atomic unit
            unit = {
                "id": f"{file_path.stem}_section_{i}",
                "content": section[:2000],  # Limit content length
                "title": file_path.name,
                "source_file": str(file_path),
                "doc_type": self._infer_doc_type(file_path),
                "metadata": {
                    "section_index": i,
                    "file_size": file_path.stat().st_size,
                    "modified_time": file_path.stat().st_mtime,
                    "section_length": len(section),
                },
            }
            atomic_units.append(unit)

        # If no sections found, treat entire file as one unit
        if not atomic_units:
            atomic_units.append(
                {
                    "id": f"{file_path.stem}_full",
                    "content": content[:2000],
                    "title": file_path.name,
                    "source_file": str(file_path),
                    "doc_type": self._infer_doc_type(file_path),
                    "metadata": {
                        "section_index": 0,
                        "file_size": file_path.stat().st_size,
                        "modified_time": file_path.stat().st_mtime,
                        "full_file": True,
                    },
                }
            )

        return atomic_units

    def _infer_doc_type(self, file_path: Path) -> str:
        """Infer document type from file extension."""
        extension = file_path.suffix.lower()

        type_mapping = {
            ".md": "markdown",
            ".txt": "text",
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "react",
            ".tsx": "react_typescript",
            ".html": "html",
            ".css": "stylesheet",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".json": "json",
            ".toml": "toml",
        }

        return type_mapping.get(extension, "unknown")

    def _generate_registries(
        self, atomic_units: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate feature, component, and research registries."""
        try:
            registries = self.extractor.extract_all_entities(atomic_units)

            # Update statistics
            self.stats["features_extracted"] = len(registries.get("features", []))
            self.stats["components_identified"] = len(registries.get("components", []))
            self.stats["subsystems_mapped"] = len(registries.get("subsystems", []))
            self.stats["research_entries"] = len(registries.get("research", []))
            self.stats["evidence_links"] = len(registries.get("evidence_links", []))

            return registries

        except Exception as e:
            console.print(f"[yellow]⚠️ Registry generation failed: {e}[/yellow]")
            return {}

    def _create_embeddings(self, atomic_units: List[Dict[str, Any]]):
        """Create semantic embeddings for atomic units."""
        try:
            # Process in batches for ADHD-friendly progress
            batch_size = self.config.batch_size
            total_batches = (len(atomic_units) + batch_size - 1) // batch_size

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[bold magenta]{task.completed}/{task.total}"),
                console=console,
            ) as progress:

                task = progress.add_task("Creating embeddings...", total=total_batches)

                for i in range(0, len(atomic_units), batch_size):
                    batch = atomic_units[i : i + batch_size]

                    # Create embeddings for batch
                    self.embedder.embed_documents(batch)

                    progress.update(task, completed=(i // batch_size) + 1)

        except Exception as e:
            console.print(f"[yellow]⚠️ Embedding creation failed: {e}[/yellow]")

    def _display_completion_summary(self):
        """Display ADHD-friendly completion summary."""
        duration = self.stats["end_time"] - self.stats["start_time"]

        # Create summary table
        table = Table(title="🎉 Processing Complete!")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green", justify="right")
        table.add_column("Status", style="yellow")

        table.add_row("Files Processed", str(self.stats["files_processed"]), "✅")
        table.add_row("Atomic Units", str(self.stats["atomic_units_created"]), "✅")
        table.add_row("Features Extracted", str(self.stats["features_extracted"]), "✅")
        table.add_row(
            "Components Identified", str(self.stats["components_identified"]), "✅"
        )
        table.add_row("Subsystems Mapped", str(self.stats["subsystems_mapped"]), "✅")
        table.add_row("Research Entries", str(self.stats["research_entries"]), "✅")
        table.add_row("Evidence Links", str(self.stats["evidence_links"]), "✅")
        table.add_row("Processing Time", f"{duration:.1f}s", "⏱️")

        console.print(table)

        # Encouraging message
        console.print(
            Panel(
                f"🧠 Great work! Your codebase has been transformed into a structured knowledge base.\n\n"
                f"📊 {self.stats['atomic_units_created']} atomic units created from {self.stats['files_processed']} files\n"
                f"🔗 {self.stats['evidence_links']} evidence links for full traceability\n"
                f"🎯 Ready for semantic search and intelligent navigation!",
                title="🎉 Analysis Complete",
                border_style="green",
            )
        )

    def _get_results(self) -> Dict[str, Any]:
        """Get processing results summary."""
        return {
            "success": True,
            "statistics": self.stats.copy(),
            "output_directory": str(self.config.output_directory),
            "processing_time": (
                self.stats["end_time"] - self.stats["start_time"]
                if self.stats["end_time"] and self.stats["start_time"]
                else 0
            ),
        }
