"""
Document Processing Pipeline for Dopemux

Comprehensive document processing system that transforms scattered docs into
clean arc42/C4/Diátaxis architecture with research evidence integration.
"""

from .normalizer import AtomicUnit, AtomicUnitsNormalizer
from .registries import RegistryBuilder
from .embedder import DocumentEmbedder
from .embedder_v2 import MaxPerformanceEmbedder, upgrade_embeddings_to_max_performance

__all__ = [
    "AtomicUnit",
    "AtomicUnitsNormalizer",
    "RegistryBuilder",
    "DocumentEmbedder",
    "MaxPerformanceEmbedder",
    "upgrade_embeddings_to_max_performance",
    "DocumentProcessor"
]


class DocumentProcessor:
    """
    Main orchestrator for the complete document processing pipeline.

    Processes all files in docs directory following the comprehensive playbook
    to transform scattered docs into normalized arc42/C4/Diátaxis structure.
    """

    def __init__(self, docs_directory="docs", output_directory="build",
                 milvus_host="localhost", milvus_port=19530):
        from pathlib import Path

        self.docs_dir = Path(docs_directory)
        self.output_dir = Path(output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.milvus_host = milvus_host
        self.milvus_port = milvus_port

        # Initialize components
        self.normalizer = AtomicUnitsNormalizer()
        self.registry_builder = RegistryBuilder(self.output_dir)
        # Skip embedder for now - focus on registry generation
        # self.embedder = DocumentEmbedder()

    async def process_all_documents(self):
        """Execute the complete document processing pipeline."""
        print("🚀 Starting complete document processing pipeline...")

        # Step 1: Copy session files to CCDOCS
        self._copy_session_files()

        # Step 2: Simple file inventory
        all_files = self._get_all_files()
        print(f"📁 Found {len(all_files)} files to process")

        # Step 3: Extract and normalize to AtomicUnits
        atomic_units = []
        for file_path in all_files:
            units = self._process_file(file_path)
            atomic_units.extend(units)

        print(f"⚛️  Generated {len(atomic_units)} atomic units")

        # Step 4: Build registries
        registry_counts = self.registry_builder.build_registries(atomic_units)

        # Step 5: Max-performance embeddings with Voyage Context-3 + Milvus + Reranker
        try:
            print("🚀 Upgrading to max-performance embeddings...")
            embedder, embedding_results = await upgrade_embeddings_to_max_performance(
                atomic_units, self.output_dir
            )
            print("✅ Max-performance embeddings complete!")
        except Exception as e:
            print(f"⚠️ Max-performance embeddings failed (continuing without): {e}")
            embedding_results = {"error": str(e)}

        print("✅ Document processing pipeline complete!")
        return {
            'files_processed': len(all_files),
            'atomic_units': len(atomic_units),
            'embedding_results': embedding_results,
            **registry_counts
        }

    def _copy_session_files(self):
        """Copy session shots and build plans to CCDOCS before processing."""
        from pathlib import Path
        import shutil

        ccdocs_dir = Path("CCDOCS")
        ccdocs_dir.mkdir(exist_ok=True)

        # Find session and build plan files
        session_patterns = ["*session*", "*todo*", "*build*", "*plan*"]

        for pattern in session_patterns:
            for file_path in self.docs_dir.glob(f"**/{pattern}"):
                if file_path.is_file():
                    dest_path = ccdocs_dir / file_path.name
                    try:
                        shutil.copy2(file_path, dest_path)
                        print(f"📋 Copied {file_path.name} to CCDOCS/")
                    except Exception as e:
                        print(f"⚠️  Could not copy {file_path}: {e}")

    def _get_all_files(self):
        """Get all files in docs directory and CCDOCS."""
        from pathlib import Path

        all_files = []

        # Get files from docs directory
        for file_path in self.docs_dir.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                all_files.append(file_path)

        # Get files from CCDOCS
        ccdocs_dir = Path("CCDOCS")
        if ccdocs_dir.exists():
            for file_path in ccdocs_dir.glob("*"):
                if file_path.is_file():
                    all_files.append(file_path)

        return all_files

    def _process_file(self, file_path):
        """Process a single file into AtomicUnits."""
        try:
            content = self._read_file_safely(file_path)
            if not content:
                return []

            # Create basic AtomicUnits from file content
            # This is a simplified version - in full implementation would use
            # the comprehensive extractor with 11 entity types
            units = []

            # Split content into sections by headers
            sections = self._split_into_sections(content)

            for i, (title, section_content) in enumerate(sections):
                if section_content.strip():
                    unit = AtomicUnit(
                        id=f"{file_path.stem}-{i}",
                        content=section_content.strip(),
                        title=title,
                        source_file=str(file_path),
                        line_start=1,  # Simplified
                        line_end=len(section_content.split('\n')),
                        doc_type=self._detect_doc_type(file_path, content),
                        tags=self._extract_basic_tags(section_content)
                    )
                    units.append(unit)

            return units

        except Exception as e:
            print(f"⚠️  Error processing {file_path}: {e}")
            return []

    def _read_file_safely(self, file_path):
        """Read file content with encoding detection."""
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # Try with chardet
                import chardet
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding']
                return raw_data.decode(encoding or 'utf-8', errors='ignore')
            except:
                # Fallback to latin-1
                with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
                    return f.read()
        except Exception as e:
            print(f"⚠️  Could not read {file_path}: {e}")
            return ""

    def _split_into_sections(self, content):
        """Split content into sections by markdown headers."""
        import re

        sections = []
        current_title = ""
        current_content = []

        for line in content.split('\n'):
            header_match = re.match(r'^(#{1,6})\s+(.+)', line)
            if header_match:
                # Save previous section
                if current_content:
                    sections.append((current_title, '\n'.join(current_content)))

                # Start new section
                current_title = header_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        # Add final section
        if current_content:
            sections.append((current_title, '\n'.join(current_content)))

        # If no headers found, treat whole content as one section
        if not sections and content.strip():
            sections.append(("", content))

        return sections

    def _detect_doc_type(self, file_path, content):
        """Detect document type from file path and content."""
        import re

        path_str = str(file_path).lower()
        content_lower = content.lower()

        # Detection patterns
        if re.search(r'\badr\b|decision.*record', path_str + content_lower):
            return "ADR"
        elif re.search(r'\brfc\b|request.*comment', path_str + content_lower):
            return "RFC"
        elif re.search(r'component\(|container\(|rel\(', content):
            return "C4"
        elif re.search(r'arc42|architecture.*decision', content_lower):
            return "arc42"
        elif re.search(r'feature|epic|story|acceptance', content_lower):
            return "Feature"
        elif re.search(r'spike|benchmark|research|study', content_lower):
            return "Research"
        elif file_path.suffix.lower() in ['.md', '.markdown']:
            return "Markdown"
        else:
            return "Document"

    def _extract_basic_tags(self, content):
        """Extract basic tags from content."""
        import re

        tags = set()
        content_lower = content.lower()

        # Common tag patterns
        tag_patterns = {
            'api': r'\bapi\b',
            'database': r'\b(database|db|sql|postgres|mysql)\b',
            'security': r'\b(security|auth|jwt|oauth|encryption)\b',
            'performance': r'\b(performance|latency|throughput|benchmark)\b',
            'architecture': r'\b(architecture|design|system)\b',
            'testing': r'\b(test|testing|qa|quality)\b'
        }

        for tag, pattern in tag_patterns.items():
            if re.search(pattern, content_lower):
                tags.add(tag)

        return list(tags)