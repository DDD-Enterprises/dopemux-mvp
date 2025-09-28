"""
Serena Integration Adapter

Integrates the embedding system with Serena (enhanced code navigation)
for semantic code search, documentation embedding, and ADHD-optimized
development workflow integration.
"""

import asyncio
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from datetime import datetime

from ..core import SearchResult, AdvancedEmbeddingConfig, EmbeddingError
from .base import BaseIntegration

logger = logging.getLogger(__name__)


class SerenaAdapter(BaseIntegration):
    """
    Serena integration adapter for code-aware embedding management.

    Synchronizes code files, documentation, and development artifacts
    with the embedding system for enhanced semantic code search and
    ADHD-optimized development workflows.
    """

    def __init__(self, config: AdvancedEmbeddingConfig, project_root: str):
        """
        Initialize Serena adapter.

        Args:
            config: Embedding configuration
            project_root: Root directory of the project
        """
        super().__init__(config)
        self.project_root = Path(project_root)
        self.connection_status = "unknown"
        self.last_sync_time: Optional[datetime] = None

        # File patterns to include/exclude
        self.include_patterns = {
            "code": ["*.py", "*.js", "*.ts", "*.go", "*.rs", "*.java", "*.cpp", "*.h"],
            "docs": ["*.md", "*.rst", "*.txt", "*.adoc"],
            "config": ["*.json", "*.yaml", "*.yml", "*.toml", "*.ini"],
            "scripts": ["*.sh", "*.bash", "*.zsh", "*.fish", "Makefile", "Dockerfile"]
        }

        self.exclude_patterns = {
            "__pycache__", "node_modules", ".git", ".pytest_cache",
            "venv", "env", ".env", "dist", "build", "target"
        }

        # Code analysis patterns
        self.function_patterns = {
            "python": r"^def\s+(\w+)",
            "javascript": r"^function\s+(\w+)|^const\s+(\w+)\s*=\s*\(",
            "typescript": r"^function\s+(\w+)|^const\s+(\w+)\s*=\s*\(",
            "go": r"^func\s+(\w+)",
            "rust": r"^fn\s+(\w+)",
            "java": r"^\s*public\s+\w+\s+(\w+)\s*\("
        }

        self.class_patterns = {
            "python": r"^class\s+(\w+)",
            "javascript": r"^class\s+(\w+)",
            "typescript": r"^class\s+(\w+)",
            "java": r"^\s*public\s+class\s+(\w+)",
            "go": r"^type\s+(\w+)\s+struct"
        }

        logger.info(f"🔌 Serena adapter initialized for project: {project_root}")

    async def validate_connection(self) -> bool:
        """
        Validate connection to Serena and project files.

        Returns:
            True if project root exists and is accessible
        """
        try:
            if not self.project_root.exists():
                self.connection_status = f"error: project root not found at {self.project_root}"
                return False

            if not self.project_root.is_dir():
                self.connection_status = f"error: project root is not a directory: {self.project_root}"
                return False

            # Check if we can list files
            list(self.project_root.iterdir())

            self.connection_status = "healthy"
            logger.info("✅ Serena project connection validated")
            return True

        except Exception as e:
            self.connection_status = f"error: {str(e)}"
            logger.error(f"❌ Serena connection failed: {e}")
            return False

    async def sync_documents(self, workspace_id: str) -> Dict[str, Any]:
        """
        Synchronize code files and documentation from project.

        Scans the project directory for code files, documentation,
        configuration files, and extracts semantic content for embedding.

        Args:
            workspace_id: Project workspace identifier

        Returns:
            Sync statistics and document collection
        """
        try:
            if not await self.validate_connection():
                raise EmbeddingError("Serena project connection not available")

            sync_start = datetime.now()
            documents_synced = 0
            sync_results = {
                "documents": [],
                "file_types": {},
                "errors": []
            }

            if self.config.enable_progress_tracking:
                print(f"🔄 Scanning project files from {self.project_root}...")

            # Sync different file types
            file_processors = [
                ("code", self._sync_code_files),
                ("docs", self._sync_documentation),
                ("config", self._sync_config_files),
                ("scripts", self._sync_scripts)
            ]

            for file_type, processor in file_processors:
                try:
                    if self.config.enable_progress_tracking:
                        print(f"📁 Processing {file_type} files...")

                    type_docs = await processor()
                    sync_results["documents"].extend(type_docs)
                    sync_results["file_types"][file_type] = len(type_docs)
                    documents_synced += len(type_docs)

                except Exception as e:
                    error_msg = f"Failed to process {file_type} files: {str(e)}"
                    sync_results["errors"].append(error_msg)
                    logger.warning(f"⚠️ {error_msg}")

            # Update sync metadata
            self.last_sync_time = sync_start
            sync_duration = (datetime.now() - sync_start).total_seconds()

            # ADHD-friendly completion feedback
            if self.config.enable_progress_tracking:
                print(f"✅ Serena sync complete: {documents_synced} files in {sync_duration:.1f}s")

            return {
                "documents_synced": documents_synced,
                "sync_duration_seconds": sync_duration,
                "file_types": sync_results["file_types"],
                "errors": sync_results["errors"],
                "documents": sync_results["documents"]
            }

        except Exception as e:
            logger.error(f"❌ Serena sync failed: {e}")
            raise EmbeddingError(f"Serena sync failed: {e}") from e

    async def _sync_code_files(self) -> List[Dict[str, Any]]:
        """Sync source code files for semantic analysis."""
        documents = []

        for pattern in self.include_patterns["code"]:
            for file_path in self.project_root.rglob(pattern):
                if self._should_exclude_file(file_path):
                    continue

                try:
                    content = await self._read_file_content(file_path)
                    if not content.strip():
                        continue

                    # Extract code metadata
                    file_ext = file_path.suffix.lower()
                    language = self._detect_language(file_ext)
                    functions = self._extract_functions(content, language)
                    classes = self._extract_classes(content, language)

                    # Create document for file
                    doc = {
                        "id": f"code_{self._get_relative_path(file_path)}",
                        "content": content,
                        "metadata": {
                            "type": "code",
                            "source": "serena",
                            "file_path": str(self._get_relative_path(file_path)),
                            "language": language,
                            "extension": file_ext,
                            "functions": functions,
                            "classes": classes,
                            "line_count": len(content.splitlines()),
                            "char_count": len(content),
                            "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime)
                        }
                    }
                    documents.append(doc)

                    # Create separate documents for functions/classes
                    for func_name, func_content in functions.items():
                        func_doc = {
                            "id": f"function_{self._get_relative_path(file_path)}_{func_name}",
                            "content": func_content,
                            "metadata": {
                                "type": "function",
                                "source": "serena",
                                "file_path": str(self._get_relative_path(file_path)),
                                "function_name": func_name,
                                "language": language,
                                "parent_file": str(self._get_relative_path(file_path))
                            }
                        }
                        documents.append(func_doc)

                except Exception as e:
                    logger.warning(f"⚠️ Failed to process {file_path}: {e}")

        return documents

    async def _sync_documentation(self) -> List[Dict[str, Any]]:
        """Sync documentation files."""
        documents = []

        for pattern in self.include_patterns["docs"]:
            for file_path in self.project_root.rglob(pattern):
                if self._should_exclude_file(file_path):
                    continue

                try:
                    content = await self._read_file_content(file_path)
                    if not content.strip():
                        continue

                    # Extract documentation metadata
                    headers = self._extract_markdown_headers(content)
                    word_count = len(content.split())

                    doc = {
                        "id": f"doc_{self._get_relative_path(file_path)}",
                        "content": content,
                        "metadata": {
                            "type": "documentation",
                            "source": "serena",
                            "file_path": str(self._get_relative_path(file_path)),
                            "format": self._detect_doc_format(file_path),
                            "headers": headers,
                            "word_count": word_count,
                            "reading_time_minutes": max(1, word_count // 200),
                            "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime)
                        }
                    }
                    documents.append(doc)

                except Exception as e:
                    logger.warning(f"⚠️ Failed to process doc {file_path}: {e}")

        return documents

    async def _sync_config_files(self) -> List[Dict[str, Any]]:
        """Sync configuration files."""
        documents = []

        for pattern in self.include_patterns["config"]:
            for file_path in self.project_root.rglob(pattern):
                if self._should_exclude_file(file_path):
                    continue

                try:
                    content = await self._read_file_content(file_path)
                    if not content.strip():
                        continue

                    doc = {
                        "id": f"config_{self._get_relative_path(file_path)}",
                        "content": content,
                        "metadata": {
                            "type": "configuration",
                            "source": "serena",
                            "file_path": str(self._get_relative_path(file_path)),
                            "config_type": self._detect_config_type(file_path),
                            "line_count": len(content.splitlines()),
                            "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime)
                        }
                    }
                    documents.append(doc)

                except Exception as e:
                    logger.warning(f"⚠️ Failed to process config {file_path}: {e}")

        return documents

    async def _sync_scripts(self) -> List[Dict[str, Any]]:
        """Sync script files."""
        documents = []

        for pattern in self.include_patterns["scripts"]:
            for file_path in self.project_root.rglob(pattern):
                if self._should_exclude_file(file_path):
                    continue

                try:
                    content = await self._read_file_content(file_path)
                    if not content.strip():
                        continue

                    doc = {
                        "id": f"script_{self._get_relative_path(file_path)}",
                        "content": content,
                        "metadata": {
                            "type": "script",
                            "source": "serena",
                            "file_path": str(self._get_relative_path(file_path)),
                            "script_type": self._detect_script_type(file_path),
                            "line_count": len(content.splitlines()),
                            "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime)
                        }
                    }
                    documents.append(doc)

                except Exception as e:
                    logger.warning(f"⚠️ Failed to process script {file_path}: {e}")

        return documents

    async def _read_file_content(self, file_path: Path) -> str:
        """Safely read file content with encoding detection."""
        try:
            # Try UTF-8 first
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                # Fallback to latin-1
                return file_path.read_text(encoding='latin-1')
            except Exception:
                # Skip binary files
                return ""

    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from processing."""
        path_parts = file_path.parts
        return any(exclude in path_parts for exclude in self.exclude_patterns)

    def _get_relative_path(self, file_path: Path) -> Path:
        """Get relative path from project root."""
        return file_path.relative_to(self.project_root)

    def _detect_language(self, file_ext: str) -> str:
        """Detect programming language from file extension."""
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp"
        }
        return language_map.get(file_ext, "unknown")

    def _extract_functions(self, content: str, language: str) -> Dict[str, str]:
        """Extract function definitions from code."""
        functions = {}

        if language not in self.function_patterns:
            return functions

        pattern = self.function_patterns[language]
        lines = content.splitlines()

        for i, line in enumerate(lines):
            match = re.search(pattern, line.strip())
            if match:
                func_name = match.group(1) or match.group(2)
                if func_name:
                    # Extract function body (simplified)
                    func_lines = [line]
                    for j in range(i + 1, min(i + 20, len(lines))):
                        func_lines.append(lines[j])
                        if language == "python" and lines[j].strip() and not lines[j].startswith(" "):
                            break

                    functions[func_name] = "\n".join(func_lines)

        return functions

    def _extract_classes(self, content: str, language: str) -> Dict[str, str]:
        """Extract class definitions from code."""
        classes = {}

        if language not in self.class_patterns:
            return classes

        pattern = self.class_patterns[language]
        lines = content.splitlines()

        for i, line in enumerate(lines):
            match = re.search(pattern, line.strip())
            if match:
                class_name = match.group(1)
                if class_name:
                    # Extract class definition (simplified)
                    class_lines = [line]
                    for j in range(i + 1, min(i + 50, len(lines))):
                        class_lines.append(lines[j])

                    classes[class_name] = "\n".join(class_lines)

        return classes

    def _extract_markdown_headers(self, content: str) -> List[str]:
        """Extract headers from markdown content."""
        headers = []
        for line in content.splitlines():
            if line.startswith("#"):
                headers.append(line.strip())
        return headers

    def _detect_doc_format(self, file_path: Path) -> str:
        """Detect documentation format."""
        format_map = {
            ".md": "markdown",
            ".rst": "restructuredtext",
            ".txt": "plaintext",
            ".adoc": "asciidoc"
        }
        return format_map.get(file_path.suffix.lower(), "unknown")

    def _detect_config_type(self, file_path: Path) -> str:
        """Detect configuration file type."""
        config_map = {
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".ini": "ini"
        }
        return config_map.get(file_path.suffix.lower(), "unknown")

    def _detect_script_type(self, file_path: Path) -> str:
        """Detect script type."""
        if file_path.name == "Makefile":
            return "makefile"
        elif file_path.name == "Dockerfile":
            return "dockerfile"
        else:
            script_map = {
                ".sh": "shell",
                ".bash": "bash",
                ".zsh": "zsh",
                ".fish": "fish"
            }
            return script_map.get(file_path.suffix.lower(), "script")

    async def store_embeddings(self, documents: List[Dict[str, Any]],
                              embeddings: List[List[float]]) -> None:
        """
        Store embeddings for code navigation enhancement.

        Args:
            documents: Document metadata
            embeddings: Generated embeddings
        """
        try:
            if len(documents) != len(embeddings):
                raise ValueError("Documents and embeddings count mismatch")

            # Mock storage - in practice would integrate with Serena's index
            stored_count = 0

            for doc, embedding in zip(documents, embeddings):
                try:
                    # Store embedding with file metadata for code navigation
                    stored_count += 1

                except Exception as e:
                    logger.warning(f"⚠️ Failed to store embedding for {doc['id']}: {e}")

            if self.config.enable_progress_tracking:
                print(f"💾 Stored {stored_count} code embeddings")

        except Exception as e:
            logger.error(f"❌ Failed to store embeddings for Serena: {e}")
            raise EmbeddingError(f"Serena embedding storage failed: {e}") from e

    async def enhance_search_results(self, results: List[SearchResult],
                                   context: Dict[str, Any]) -> List[SearchResult]:
        """
        Enhance search results with code navigation metadata.

        Args:
            results: Raw search results
            context: Additional search context

        Returns:
            Enhanced search results with navigation info
        """
        try:
            enhanced_results = []

            for result in results:
                enhanced_result = result  # Copy original result

                # Add code-specific enhancements
                if result.metadata.get("type") == "code":
                    enhanced_result.metadata.update({
                        "serena_navigation": {
                            "file_type": result.metadata.get("language", "unknown"),
                            "complexity": self._assess_code_complexity(result.content),
                            "entry_points": result.metadata.get("functions", {}),
                            "related_files": await self._find_related_files(result.metadata.get("file_path"))
                        }
                    })

                elif result.metadata.get("type") == "function":
                    enhanced_result.metadata.update({
                        "serena_navigation": {
                            "function_complexity": self._assess_function_complexity(result.content),
                            "estimated_read_time": self._estimate_code_read_time(result.content),
                            "parent_file": result.metadata.get("parent_file")
                        }
                    })

                elif result.metadata.get("type") == "documentation":
                    enhanced_result.metadata.update({
                        "serena_navigation": {
                            "reading_time": result.metadata.get("reading_time_minutes", 0),
                            "headers": result.metadata.get("headers", []),
                            "related_code": await self._find_related_code(result.content)
                        }
                    })

                enhanced_results.append(enhanced_result)

            return enhanced_results

        except Exception as e:
            logger.warning(f"⚠️ Failed to enhance results with Serena data: {e}")
            return results

    def _assess_code_complexity(self, content: str) -> str:
        """Assess code complexity for ADHD time management."""
        lines = len(content.splitlines())
        if lines > 200:
            return "high"
        elif lines > 50:
            return "medium"
        else:
            return "low"

    def _assess_function_complexity(self, content: str) -> str:
        """Assess function complexity."""
        lines = len(content.splitlines())
        if lines > 30:
            return "high"
        elif lines > 10:
            return "medium"
        else:
            return "low"

    def _estimate_code_read_time(self, content: str) -> str:
        """Estimate time needed to understand code."""
        complexity = self._assess_function_complexity(content)
        time_map = {
            "low": "2-5 minutes",
            "medium": "5-15 minutes",
            "high": "15-30 minutes"
        }
        return time_map.get(complexity, "unknown")

    async def _find_related_files(self, file_path: Optional[str]) -> List[str]:
        """Find files related to the current file."""
        # Mock implementation - would use actual analysis
        return []

    async def _find_related_code(self, doc_content: str) -> List[str]:
        """Find code files related to documentation."""
        # Mock implementation - would analyze mentions and links
        return []

    def get_integration_status(self) -> Dict[str, Any]:
        """
        Get Serena integration health and status.

        Returns:
            Status dictionary with project and sync information
        """
        return {
            "integration_type": "serena",
            "project_root": str(self.project_root),
            "connection_status": self.connection_status,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "include_patterns": self.include_patterns,
            "exclude_patterns": list(self.exclude_patterns),
            "features": {
                "code_analysis": True,
                "documentation_sync": True,
                "semantic_navigation": True,
                "function_extraction": True,
                "complexity_assessment": True
            }
        }