"""
Document Type Classifier and Unified Extraction Pipeline

Routes different document types to appropriate extractors and merges
results into a unified format suitable for the knowledge graph.
"""

import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

# Import our extractors
try:
    # Try relative imports first (when used as module)
    from .markdown_patterns import MarkdownPatternExtractor
    from .yaml_extractor import YamlExtractor
except ImportError:
    # Fall back to direct imports (when run as script)
    from markdown_patterns import MarkdownPatternExtractor
    from yaml_extractor import YamlExtractor


@dataclass
class DocumentInfo:
    """Information about a document to be processed."""
    filepath: Path
    filename: str
    extension: str
    content: str
    doc_type: str
    size_bytes: int


@dataclass
class ExtractionResult:
    """Unified result from document extraction."""
    document: DocumentInfo
    entities: Dict[str, List[Dict[str, Any]]]
    metadata: Dict[str, Any]
    extraction_method: str
    success: bool
    error_message: Optional[str] = None


class DocumentClassifier:
    """Classify documents and route to appropriate extractors."""

    def __init__(self):
        """Initialize classifier with extractors."""
        self.markdown_extractor = MarkdownPatternExtractor()
        self.yaml_extractor = YamlExtractor()

        # Define file type mappings
        self.file_type_mapping = {
            '.md': 'markdown',
            '.mdx': 'markdown',
            '.txt': 'text',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.db': 'sqlite',
            '.sqlite': 'sqlite',
            '.sqlite3': 'sqlite'
        }

        # Define processing priorities (higher = more important)
        self.type_priorities = {
            'markdown': 10,
            'yaml': 9,
            'json': 8,
            'text': 7,
            'sqlite': 6,
            'unknown': 1
        }

    def classify_document(self, filepath: Path) -> DocumentInfo:
        """Classify a document and prepare it for extraction."""
        try:
            # Basic file information
            extension = filepath.suffix.lower()
            doc_type = self.file_type_mapping.get(extension, 'unknown')
            size_bytes = filepath.stat().st_size

            # Read content based on file type
            content = ""
            if doc_type in ['markdown', 'yaml', 'json', 'text']:
                try:
                    content = filepath.read_text(encoding='utf-8', errors='replace')
                except Exception as e:
                    print(f"Warning: Could not read {filepath}: {e}")

            elif doc_type == 'sqlite':
                content = f"SQLite database: {filepath.name} ({size_bytes} bytes)"

            return DocumentInfo(
                filepath=filepath,
                filename=filepath.name,
                extension=extension,
                content=content,
                doc_type=doc_type,
                size_bytes=size_bytes
            )

        except Exception as e:
            # Return error document info
            return DocumentInfo(
                filepath=filepath,
                filename=filepath.name if filepath else "unknown",
                extension="",
                content="",
                doc_type="error",
                size_bytes=0
            )

    def extract_entities(self, doc_info: DocumentInfo) -> ExtractionResult:
        """Extract entities from a document using appropriate extractor."""

        try:
            if doc_info.doc_type == 'markdown':
                return self._extract_markdown(doc_info)
            elif doc_info.doc_type == 'yaml':
                return self._extract_yaml(doc_info)
            elif doc_info.doc_type == 'json':
                return self._extract_json(doc_info)
            elif doc_info.doc_type == 'text':
                return self._extract_text(doc_info)
            elif doc_info.doc_type == 'sqlite':
                return self._extract_sqlite(doc_info)
            else:
                return ExtractionResult(
                    document=doc_info,
                    entities={},
                    metadata={'doc_type': doc_info.doc_type},
                    extraction_method='none',
                    success=False,
                    error_message=f"Unsupported document type: {doc_info.doc_type}"
                )

        except Exception as e:
            return ExtractionResult(
                document=doc_info,
                entities={},
                metadata={'error': str(e)},
                extraction_method='error',
                success=False,
                error_message=str(e)
            )

    def _extract_markdown(self, doc_info: DocumentInfo) -> ExtractionResult:
        """Extract entities from markdown document."""
        entities = self.markdown_extractor.extract_to_dict(doc_info.content, doc_info.filename)

        metadata = {
            'doc_type': 'markdown',
            'lines': len(doc_info.content.splitlines()),
            'words': len(doc_info.content.split()),
            'has_headers': any(etype.startswith('section_') for etype in entities.keys()),
            'has_adhd_content': any('adhd' in etype for etype in entities.keys())
        }

        return ExtractionResult(
            document=doc_info,
            entities=entities,
            metadata=metadata,
            extraction_method='markdown_patterns',
            success=True
        )

    def _extract_yaml(self, doc_info: DocumentInfo) -> ExtractionResult:
        """Extract entities from YAML document."""
        entities = self.yaml_extractor.extract_to_dict(doc_info.content, doc_info.filename)

        # Get ADHD profile if available
        adhd_profile = self.yaml_extractor.extract_adhd_profile(doc_info.content)

        metadata = {
            'doc_type': 'yaml',
            'config_sections': len([e for e in entities if 'section' in e]),
            'has_adhd_profile': bool(adhd_profile),
            'adhd_profile': adhd_profile
        }

        return ExtractionResult(
            document=doc_info,
            entities=entities,
            metadata=metadata,
            extraction_method='yaml_parser',
            success=True
        )

    def _extract_json(self, doc_info: DocumentInfo) -> ExtractionResult:
        """Extract entities from JSON document."""
        try:
            import json
            data = json.loads(doc_info.content)

            # Simple JSON extraction - treat as key-value pairs
            entities = {'json_properties': []}

            def extract_json_recursive(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        if isinstance(value, (dict, list)):
                            extract_json_recursive(value, current_path)
                        else:
                            entities['json_properties'].append({
                                'key_path': current_path,
                                'value': value,
                                'type': type(value).__name__,
                                'confidence': 0.8
                            })

            extract_json_recursive(data)

            metadata = {
                'doc_type': 'json',
                'properties_count': len(entities['json_properties'])
            }

            return ExtractionResult(
                document=doc_info,
                entities=entities,
                metadata=metadata,
                extraction_method='json_parser',
                success=True
            )

        except json.JSONDecodeError as e:
            return ExtractionResult(
                document=doc_info,
                entities={},
                metadata={'error': 'Invalid JSON'},
                extraction_method='json_parser',
                success=False,
                error_message=f"JSON parsing error: {e}"
            )

    def _extract_text(self, doc_info: DocumentInfo) -> ExtractionResult:
        """Extract entities from plain text document."""
        # For plain text, try markdown patterns but with lower confidence
        entities = self.markdown_extractor.extract_to_dict(doc_info.content, doc_info.filename)

        # Reduce confidence for all entities since this is plain text
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                if 'confidence' in entity:
                    entity['confidence'] *= 0.7  # Reduce confidence

        metadata = {
            'doc_type': 'text',
            'lines': len(doc_info.content.splitlines()),
            'words': len(doc_info.content.split()),
            'note': 'Plain text processed with markdown patterns'
        }

        return ExtractionResult(
            document=doc_info,
            entities=entities,
            metadata=metadata,
            extraction_method='markdown_patterns_text',
            success=True
        )

    def _extract_sqlite(self, doc_info: DocumentInfo) -> ExtractionResult:
        """Extract metadata from SQLite database."""
        entities = {'database_info': []}

        try:
            # Connect and get table information
            conn = sqlite3.connect(str(doc_info.filepath))
            cursor = conn.cursor()

            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            for table_name in tables:
                table_name = table_name[0]

                # Get table info
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()

                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                row_count = cursor.fetchone()[0]

                entities['database_info'].append({
                    'table_name': table_name,
                    'columns': [col[1] for col in columns],  # Column names
                    'row_count': row_count,
                    'type': 'database_table',
                    'confidence': 0.9
                })

            conn.close()

            metadata = {
                'doc_type': 'sqlite',
                'table_count': len(tables),
                'total_size_bytes': doc_info.size_bytes
            }

            return ExtractionResult(
                document=doc_info,
                entities=entities,
                metadata=metadata,
                extraction_method='sqlite_inspector',
                success=True
            )

        except Exception as e:
            return ExtractionResult(
                document=doc_info,
                entities={'database_info': [{'error': str(e), 'confidence': 0.1}]},
                metadata={'error': 'SQLite access failed'},
                extraction_method='sqlite_inspector',
                success=False,
                error_message=f"SQLite error: {e}"
            )

    def process_directory(self, directory_path: Path) -> List[ExtractionResult]:
        """Process all documents in a directory."""
        results = []

        if not directory_path.exists():
            return results

        # Find all files
        for file_path in directory_path.rglob('*'):
            if file_path.is_file():
                # Skip hidden files and common excludes
                if file_path.name.startswith('.') and file_path.name not in ['.gitignore']:
                    # Allow some dotfiles like config files
                    if not any(ext in file_path.name for ext in ['.yaml', '.yml', '.json', '.md']):
                        continue

                doc_info = self.classify_document(file_path)
                if doc_info.doc_type != 'error':
                    result = self.extract_entities(doc_info)
                    results.append(result)

        # Sort by priority and filename
        results.sort(key=lambda r: (
            -self.type_priorities.get(r.document.doc_type, 0),
            r.document.filename
        ))

        return results

    def merge_results(self, results: List[ExtractionResult]) -> Dict[str, Any]:
        """Merge multiple extraction results into unified format."""
        merged = {
            'documents_processed': len(results),
            'successful_extractions': len([r for r in results if r.success]),
            'failed_extractions': len([r for r in results if not r.success]),
            'document_types': {},
            'all_entities': {},
            'metadata': {
                'extraction_methods': set(),
                'total_confidence_scores': [],
                'adhd_documents': []
            }
        }

        # Process each result
        for result in results:
            doc_type = result.document.doc_type

            # Track document types
            if doc_type not in merged['document_types']:
                merged['document_types'][doc_type] = []
            merged['document_types'][doc_type].append({
                'filename': result.document.filename,
                'success': result.success,
                'entity_count': sum(len(entities) for entities in result.entities.values())
            })

            # Merge entities
            for entity_type, entity_list in result.entities.items():
                if entity_type not in merged['all_entities']:
                    merged['all_entities'][entity_type] = []

                # Add source information to each entity
                for entity in entity_list:
                    entity_with_source = entity.copy()
                    entity_with_source['source_file'] = result.document.filename
                    entity_with_source['source_type'] = doc_type
                    merged['all_entities'][entity_type].append(entity_with_source)

                    # Collect confidence scores
                    if 'confidence' in entity:
                        merged['metadata']['total_confidence_scores'].append(entity['confidence'])

            # Track extraction methods
            merged['metadata']['extraction_methods'].add(result.extraction_method)

            # Track ADHD-related documents
            if any('adhd' in str(v).lower() for v in result.entities.values()):
                merged['metadata']['adhd_documents'].append(result.document.filename)

        # Convert set to list for JSON serialization
        merged['metadata']['extraction_methods'] = list(merged['metadata']['extraction_methods'])

        # Calculate average confidence
        confidence_scores = merged['metadata']['total_confidence_scores']
        if confidence_scores:
            merged['metadata']['average_confidence'] = sum(confidence_scores) / len(confidence_scores)
        else:
            merged['metadata']['average_confidence'] = 0.0

        return merged


def extract_from_directory(directory_path: str) -> Dict[str, Any]:
    """Convenience function to extract entities from all documents in a directory."""
    classifier = DocumentClassifier()
    results = classifier.process_directory(Path(directory_path))
    return classifier.merge_results(results)


# Test function
def test_with_docs_to_process():
    """Test the classifier with test_docs directory."""
    docs_dir = Path("test_docs")

    if not docs_dir.exists():
        print("test_docs directory not found")
        return

    classifier = DocumentClassifier()
    results = classifier.process_directory(docs_dir)

    print(f"Processed {len(results)} documents:")
    for result in results:
        status = "✅" if result.success else "❌"
        entity_count = sum(len(entities) for entities in result.entities.values())
        print(f"  {status} {result.document.filename} ({result.document.doc_type}) - {entity_count} entities")

        if not result.success:
            print(f"    Error: {result.error_message}")

    # Show merged results summary
    merged = classifier.merge_results(results)
    print(f"\nSummary:")
    print(f"  Documents processed: {merged['documents_processed']}")
    print(f"  Successful: {merged['successful_extractions']}")
    print(f"  Failed: {merged['failed_extractions']}")
    print(f"  Document types: {list(merged['document_types'].keys())}")
    print(f"  Entity types found: {list(merged['all_entities'].keys())}")
    print(f"  Average confidence: {merged['metadata']['average_confidence']:.2f}")
    print(f"  ADHD documents: {merged['metadata']['adhd_documents']}")

    return results


if __name__ == "__main__":
    test_with_docs_to_process()