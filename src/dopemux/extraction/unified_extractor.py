"""
Unified Document Extractor - Comprehensive Multi-Layer Extraction

Combines ADHD patterns, markdown structure, YAML parsing, and multi-angle
entity detection into a single, comprehensive extraction system.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

# Add extraction package to path for imports
extraction_path = Path(__file__).parent.parent.parent.parent / "extraction"
sys.path.insert(0, str(extraction_path))

try:
    # Import from our extraction package
    from document_classifier import DocumentClassifier
    from adhd_entities import ADHDEntityExtractor
    from markdown_patterns import MarkdownPatternExtractor
    from yaml_extractor import YamlExtractor
except ImportError as e:
    print(f"⚠️ Could not import extraction modules: {e}")
    print("Make sure you're running from the dopemux-mvp directory")

# Import from analysis module
try:
    from ..analysis.extractor import MultiAngleExtractor
except ImportError:
    print("⚠️ Could not import MultiAngleExtractor - some features may be limited")
    MultiAngleExtractor = None


@dataclass
class ExtractionResult:
    """Unified result from comprehensive document extraction."""
    document_path: Path
    document_type: str
    success: bool

    # Layer 1: Basic extraction
    basic_entities: Dict[str, List[Dict[str, Any]]]

    # Layer 2: ADHD-specific extraction
    adhd_entities: Dict[str, List[Dict[str, Any]]]
    adhd_profile: Optional[Dict[str, Any]]

    # Layer 3: Multi-angle extraction
    multi_angle_entities: Dict[str, List[Dict[str, Any]]]

    # Metadata
    extraction_metadata: Dict[str, Any]
    confidence_summary: Dict[str, float]
    processing_time: float
    error_message: Optional[str] = None


class UnifiedDocumentExtractor:
    """
    Comprehensive document extractor that combines all extraction layers:

    1. Basic patterns (markdown, YAML, headers)
    2. ADHD-specific accommodations and patterns
    3. Multi-angle entity detection (11 types)
    4. Confidence scoring and deduplication
    """

    def __init__(self):
        """Initialize all extraction components."""
        # Layer 1: Basic extraction
        self.document_classifier = DocumentClassifier()
        self.markdown_extractor = MarkdownPatternExtractor()
        self.yaml_extractor = YamlExtractor()

        # Layer 2: ADHD extraction
        self.adhd_extractor = ADHDEntityExtractor()

        # Layer 3: Multi-angle extraction
        # Note: MultiAngleExtractor requires output_dir, will be initialized per-pipeline
        self.multi_angle_extractor = None

        # Processing stats
        self.total_documents = 0
        self.successful_extractions = 0

    def extract_from_file(self, file_path: Path,
                         enable_adhd: bool = True,
                         enable_multi_angle: bool = True) -> ExtractionResult:
        """
        Extract entities from a single file using all available extraction layers.

        Args:
            file_path: Path to document to process
            enable_adhd: Enable ADHD-specific extraction
            enable_multi_angle: Enable multi-angle entity extraction

        Returns:
            Comprehensive extraction results
        """
        import time
        start_time = time.time()

        try:
            # Classify and read document
            doc_info = self.document_classifier.classify_document(file_path)

            if not doc_info.content:
                return ExtractionResult(
                    document_path=file_path,
                    document_type=doc_info.doc_type,
                    success=False,
                    basic_entities={},
                    adhd_entities={},
                    adhd_profile=None,
                    multi_angle_entities={},
                    extraction_metadata={'error': 'No content to extract'},
                    confidence_summary={},
                    processing_time=time.time() - start_time,
                    error_message="Document has no readable content"
                )

            # Layer 1: Basic extraction via document classifier
            basic_result = self.document_classifier.extract_entities(doc_info)
            basic_entities = basic_result.entities if basic_result.success else {}

            # Layer 2: ADHD-specific extraction
            adhd_entities = {}
            adhd_profile = None
            if enable_adhd:
                try:
                    adhd_entities = self.adhd_extractor.extract_to_dict(
                        doc_info.content, doc_info.filename
                    )
                    adhd_profile = self.adhd_extractor.extract_adhd_profile(doc_info.content)
                except Exception as e:
                    print(f"⚠️ ADHD extraction failed for {file_path}: {e}")

            # Layer 3: Multi-angle extraction
            multi_angle_entities = {}
            if enable_multi_angle and self.multi_angle_extractor:
                try:
                    # MultiAngleExtractor requires atomic units, which we'll create from basic content
                    # Create a simple atomic unit for this document
                    atomic_unit = {
                        'id': f"{file_path.stem}-0",
                        'content': doc_info.content,
                        'title': file_path.name,
                        'source_file': str(file_path),
                        'doc_type': doc_info.doc_type,
                        'metadata': {
                            'line_start': 1,
                            'line_end': len(doc_info.content.split('\n')),
                            'tags': [doc_info.doc_type.lower()]
                        }
                    }

                    # Extract using MultiAngleExtractor
                    analysis_result = self.multi_angle_extractor.extract_all_entities([atomic_unit])
                    if analysis_result:
                        # Convert MultiAngleExtractor results to our entity format
                        multi_angle_entities = self._convert_multi_angle_results(analysis_result)
                except Exception as e:
                    print(f"⚠️ Multi-angle extraction failed for {file_path}: {e}")

            # Calculate confidence summary
            confidence_scores = []
            all_entities = {**basic_entities, **adhd_entities, **multi_angle_entities}

            for entity_list in all_entities.values():
                for entity in entity_list:
                    if isinstance(entity, dict) and 'confidence' in entity:
                        confidence_scores.append(entity['confidence'])

            confidence_summary = {}
            if confidence_scores:
                confidence_summary = {
                    'average': sum(confidence_scores) / len(confidence_scores),
                    'max': max(confidence_scores),
                    'min': min(confidence_scores),
                    'count': len(confidence_scores)
                }

            # Extraction metadata
            extraction_metadata = {
                'document_type': doc_info.doc_type,
                'file_size': doc_info.size_bytes,
                'content_length': len(doc_info.content),
                'layers_enabled': {
                    'basic': True,
                    'adhd': enable_adhd,
                    'multi_angle': enable_multi_angle and self.multi_angle_extractor is not None
                },
                'entity_counts': {
                    'basic': sum(len(entities) for entities in basic_entities.values()),
                    'adhd': sum(len(entities) for entities in adhd_entities.values()),
                    'multi_angle': sum(len(entities) for entities in multi_angle_entities.values())
                }
            }

            self.successful_extractions += 1

            return ExtractionResult(
                document_path=file_path,
                document_type=doc_info.doc_type,
                success=True,
                basic_entities=basic_entities,
                adhd_entities=adhd_entities,
                adhd_profile=adhd_profile,
                multi_angle_entities=multi_angle_entities,
                extraction_metadata=extraction_metadata,
                confidence_summary=confidence_summary,
                processing_time=time.time() - start_time
            )

        except Exception as e:
            return ExtractionResult(
                document_path=file_path,
                document_type="error",
                success=False,
                basic_entities={},
                adhd_entities={},
                adhd_profile=None,
                multi_angle_entities={},
                extraction_metadata={'error': str(e)},
                confidence_summary={},
                processing_time=time.time() - start_time,
                error_message=str(e)
            )
        finally:
            self.total_documents += 1

    def extract_from_directory(self, directory_path: Path,
                              enable_adhd: bool = True,
                              enable_multi_angle: bool = True,
                              file_extensions: Optional[List[str]] = None) -> List[ExtractionResult]:
        """
        Extract entities from all files in a directory.

        Args:
            directory_path: Directory to process
            enable_adhd: Enable ADHD-specific extraction
            enable_multi_angle: Enable multi-angle entity extraction
            file_extensions: File extensions to process (default: .md, .yaml, .yml, .json)

        Returns:
            List of extraction results for all processed files
        """
        if not directory_path.exists():
            raise ValueError(f"Directory does not exist: {directory_path}")

        # Default extensions
        if file_extensions is None:
            file_extensions = ['.md', '.yaml', '.yml', '.json', '.txt']

        results = []

        # Find all files with specified extensions
        for file_path in directory_path.rglob('*'):
            if (file_path.is_file() and
                file_path.suffix.lower() in file_extensions and
                not file_path.name.startswith('.')):

                result = self.extract_from_file(
                    file_path,
                    enable_adhd=enable_adhd,
                    enable_multi_angle=enable_multi_angle
                )
                results.append(result)

        return results

    def merge_extraction_results(self, results: List[ExtractionResult]) -> Dict[str, Any]:
        """
        Merge multiple extraction results into a unified summary.

        Args:
            results: List of extraction results to merge

        Returns:
            Unified summary of all extractions
        """
        merged = {
            'summary': {
                'total_documents': len(results),
                'successful_extractions': len([r for r in results if r.success]),
                'failed_extractions': len([r for r in results if not r.success]),
                'total_processing_time': sum(r.processing_time for r in results)
            },
            'document_types': {},
            'all_entities': {
                'basic': {},
                'adhd': {},
                'multi_angle': {}
            },
            'adhd_profiles': [],
            'confidence_stats': {
                'per_document': [],
                'overall': {}
            },
            'errors': []
        }

        # Process each result
        for result in results:
            # Track document types
            doc_type = result.document_type
            if doc_type not in merged['document_types']:
                merged['document_types'][doc_type] = 0
            merged['document_types'][doc_type] += 1

            # Merge entities by layer
            for layer in ['basic', 'adhd', 'multi_angle']:
                layer_entities = getattr(result, f'{layer}_entities')
                for entity_type, entity_list in layer_entities.items():
                    if entity_type not in merged['all_entities'][layer]:
                        merged['all_entities'][layer][entity_type] = []

                    # Add source file info to each entity
                    for entity in entity_list:
                        if isinstance(entity, dict):
                            entity_with_source = entity.copy()
                            entity_with_source['source_file'] = str(result.document_path)
                            merged['all_entities'][layer][entity_type].append(entity_with_source)

            # Collect ADHD profiles
            if result.adhd_profile:
                profile_with_source = result.adhd_profile.copy()
                profile_with_source['source_file'] = str(result.document_path)
                merged['adhd_profiles'].append(profile_with_source)

            # Collect confidence stats
            if result.confidence_summary:
                conf_with_source = result.confidence_summary.copy()
                conf_with_source['source_file'] = str(result.document_path)
                merged['confidence_stats']['per_document'].append(conf_with_source)

            # Collect errors
            if not result.success:
                merged['errors'].append({
                    'file': str(result.document_path),
                    'error': result.error_message,
                    'metadata': result.extraction_metadata
                })

        # Calculate overall confidence stats
        all_confidences = []
        for doc_conf in merged['confidence_stats']['per_document']:
            if 'average' in doc_conf:
                all_confidences.append(doc_conf['average'])

        if all_confidences:
            merged['confidence_stats']['overall'] = {
                'average': sum(all_confidences) / len(all_confidences),
                'max': max(all_confidences),
                'min': min(all_confidences),
                'documents_with_confidence': len(all_confidences)
            }

        return merged

    def _convert_multi_angle_results(self, analysis_result: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Convert MultiAngleExtractor results to unified entity format."""
        entities = {}

        try:
            # Extract from different analysis categories
            for category, items in analysis_result.items():
                if isinstance(items, list):
                    entity_list = []
                    for item in items:
                        if isinstance(item, dict):
                            # Convert to our entity format
                            entity = {
                                'content': item.get('name', item.get('description', 'N/A')),
                                'value': item.get('value', ''),
                                'confidence': item.get('confidence', 0.8),  # Default confidence for multi-angle
                                'source_type': 'multi_angle',
                                'category': category
                            }
                            entity_list.append(entity)

                    if entity_list:
                        entities[f"multi_angle_{category}"] = entity_list

        except Exception as e:
            print(f"⚠️ Error converting multi-angle results: {e}")

        return entities

    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            'total_documents_processed': self.total_documents,
            'successful_extractions': self.successful_extractions,
            'success_rate': (self.successful_extractions / self.total_documents
                           if self.total_documents > 0 else 0.0)
        }


def extract_comprehensive(directory_path: str,
                         enable_adhd: bool = True,
                         enable_multi_angle: bool = True) -> Dict[str, Any]:
    """
    Convenience function for comprehensive extraction from a directory.

    Args:
        directory_path: Path to directory to process
        enable_adhd: Enable ADHD-specific extraction
        enable_multi_angle: Enable multi-angle extraction

    Returns:
        Merged extraction results
    """
    extractor = UnifiedDocumentExtractor()
    results = extractor.extract_from_directory(
        Path(directory_path),
        enable_adhd=enable_adhd,
        enable_multi_angle=enable_multi_angle
    )
    return extractor.merge_extraction_results(results)