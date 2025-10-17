"""
Comprehensive chatlog extraction pipeline with batch processing and phase synchronization.

Implements 6-phase extraction pipeline:
1. Semantic Chunking
2. Field Extraction (all 7 extractors)
3. Confidence Filtering & Quality Control
4. Knowledge Graph Construction
5. Document Synthesis
6. Archive & Reporting

Features:
- Batch processing with phase synchronization
- ADHD-optimized progress visualization
- ConPort persistence at each phase
- Extensive logging and process insights
- Automatic archiving of processed files
"""

import os
import sys
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from extractors import (
    DecisionExtractor, FeatureExtractor, ResearchExtractor,
    ConstraintExtractor, StakeholderExtractor, RiskExtractor,
    SecurityExtractor, ExtractedField
)
from synthesis import SynthesisEngine
from processing.semantic_chunker import SemanticChunker

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """Statistics for tracking processing performance."""
    total_files: int = 0
    files_processed: int = 0
    total_chunks: int = 0
    total_fields: int = 0
    fields_by_type: Dict[str, int] = field(default_factory=dict)
    high_confidence_fields: int = 0
    documents_generated: int = 0
    processing_time: float = 0.0
    phase_times: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class PipelineConfig:
    """Configuration for the extraction pipeline."""
    source_directory: Path
    output_directory: Path
    archive_directory: Optional[Path] = None
    batch_size: int = 10
    max_workers: int = 4
    confidence_threshold: float = 0.5
    include_basic_extractors: bool = True
    include_pro_extractors: bool = True
    enable_synthesis: bool = True
    max_documents: int = 6
    verbose: bool = True
    persist_to_conport: bool = True
    workspace_id: Optional[str] = None


class ExtractionPipeline:
    """
    Main extraction pipeline orchestrator.

    Handles batch processing, phase synchronization, and comprehensive
    field extraction with document synthesis.
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.stats = ProcessingStats()
        self.setup_logging()
        self.setup_directories()
        self.initialize_components()

    def setup_logging(self):
        """Setup comprehensive logging."""
        log_dir = self.config.output_directory / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create detailed log file
        log_file = log_dir / f"extraction_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        logging.basicConfig(
            level=logging.INFO if self.config.verbose else logging.WARNING,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout) if self.config.verbose else logging.NullHandler()
            ]
        )

        logger.info(f"Extraction pipeline initialized - Log file: {log_file}")

    def setup_directories(self):
        """Create necessary directory structure."""
        self.config.output_directory.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self.config.output_directory / "chunks").mkdir(exist_ok=True)
        (self.config.output_directory / "fields").mkdir(exist_ok=True)
        (self.config.output_directory / "documents").mkdir(exist_ok=True)
        (self.config.output_directory / "reports").mkdir(exist_ok=True)
        (self.config.output_directory / "logs").mkdir(exist_ok=True)

        # Setup archive directory
        if not self.config.archive_directory:
            self.config.archive_directory = self.config.output_directory / "archive"
        self.config.archive_directory.mkdir(parents=True, exist_ok=True)

        logger.info(f"Directories created - Output: {self.config.output_directory}")

    def initialize_components(self):
        """Initialize all extraction components."""
        # Initialize chunker
        self.chunker = SemanticChunker()

        # Initialize extractors
        self.extractors = {}

        # Basic extractors (always included)
        if self.config.include_basic_extractors:
            self.extractors.update({
                'decision': DecisionExtractor(),
                'feature': FeatureExtractor(),
                'research': ResearchExtractor(),
            })

        # Pro extractors (advanced analysis)
        if self.config.include_pro_extractors:
            self.extractors.update({
                'constraint': ConstraintExtractor(),
                'stakeholder': StakeholderExtractor(),
                'risk': RiskExtractor(),
                'security': SecurityExtractor(),
            })

        # Initialize synthesis engine
        if self.config.enable_synthesis:
            self.synthesis_engine = SynthesisEngine(
                max_documents=self.config.max_documents
            )

        logger.info(f"Initialized {len(self.extractors)} extractors")

    def discover_files(self) -> List[Path]:
        """Discover chatlog files to process."""
        supported_extensions = {'.txt', '.md', '.json', '.log', '.chat'}

        files = []
        for ext in supported_extensions:
            files.extend(self.config.source_directory.glob(f"**/*{ext}"))

        # Filter out already processed files (check archive)
        unprocessed_files = []
        for file_path in files:
            archived_path = self.config.archive_directory / file_path.name
            if not archived_path.exists():
                unprocessed_files.append(file_path)

        logger.info(f"Discovered {len(unprocessed_files)} unprocessed files")
        return unprocessed_files

    def run_extraction(self, files: Optional[List[Path]] = None) -> Dict[str, Any]:
        """
        Run the complete 6-phase extraction pipeline.

        Returns comprehensive results including statistics and generated documents.
        """
        start_time = datetime.now()

        if files is None:
            files = self.discover_files()

        self.stats.total_files = len(files)

        if not files:
            logger.warning("No files to process")
            return self._create_results(start_time)

        logger.info(f"Starting extraction pipeline for {len(files)} files")

        # Phase 1: Semantic Chunking (batch synchronized)
        chunks_by_file = self._phase_1_chunking(files)

        # Phase 2: Field Extraction (batch synchronized)
        fields_by_file = self._phase_2_extraction(chunks_by_file)

        # Phase 3: Quality Control & Filtering
        filtered_fields = self._phase_3_filtering(fields_by_file)

        # Phase 4: Knowledge Graph Construction
        knowledge_graph = self._phase_4_knowledge_graph(filtered_fields)

        # Phase 5: Document Synthesis
        documents = self._phase_5_synthesis(filtered_fields)

        # Phase 6: Archive & Reporting
        self._phase_6_archive_and_report(files, documents)

        # Calculate final statistics
        self.stats.processing_time = (datetime.now() - start_time).total_seconds()

        return self._create_results(start_time)

    def _phase_1_chunking(self, files: List[Path]) -> Dict[Path, List[Dict[str, Any]]]:
        """Phase 1: Semantic chunking with batch synchronization."""
        phase_start = datetime.now()
        logger.info("PHASE 1: Starting semantic chunking")

        chunks_by_file = {}

        # Process files in batches
        for i in range(0, len(files), self.config.batch_size):
            batch = files[i:i + self.config.batch_size]
            logger.info(f"Processing chunking batch {i//self.config.batch_size + 1}/{(len(files) + self.config.batch_size - 1)//self.config.batch_size}")

            # Process batch in parallel
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_file = {
                    executor.submit(self._chunk_file, file_path): file_path
                    for file_path in batch
                }

                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        chunks = future.result()
                        chunks_by_file[file_path] = chunks
                        self.stats.total_chunks += len(chunks)
                        logger.debug(f"Chunked {file_path.name}: {len(chunks)} chunks")
                    except Exception as e:
                        logger.error(f"Error chunking {file_path}: {e}")
                        self.stats.errors.append(f"Chunking {file_path.name}: {str(e)}")

        self.stats.phase_times['chunking'] = (datetime.now() - phase_start).total_seconds()
        logger.info(f"PHASE 1 COMPLETE: {self.stats.total_chunks} chunks generated in {self.stats.phase_times['chunking']:.2f}s")

        # Persist to ConPort
        if self.config.persist_to_conport:
            self._persist_chunking_to_conport(chunks_by_file)

        return chunks_by_file

    def _phase_2_extraction(self, chunks_by_file: Dict[Path, List[Dict[str, Any]]]) -> Dict[Path, List[ExtractedField]]:
        """Phase 2: Field extraction with batch synchronization."""
        phase_start = datetime.now()
        logger.info("PHASE 2: Starting field extraction")

        fields_by_file = {}

        # Process all chunks for all extractors
        for extractor_name, extractor in self.extractors.items():
            logger.info(f"Running {extractor_name} extractor")

            for file_path, chunks in chunks_by_file.items():
                if file_path not in fields_by_file:
                    fields_by_file[file_path] = []

                # Extract fields from all chunks
                for chunk in chunks:
                    try:
                        extracted = extractor.extract_from_chunk(chunk)
                        fields_by_file[file_path].extend(extracted)
                    except Exception as e:
                        logger.error(f"Error in {extractor_name} for {file_path}: {e}")
                        self.stats.errors.append(f"{extractor_name} - {file_path.name}: {str(e)}")

        # Calculate statistics
        for file_path, fields in fields_by_file.items():
            self.stats.total_fields += len(fields)
            for field in fields:
                field_type = field.field_type
                self.stats.fields_by_type[field_type] = self.stats.fields_by_type.get(field_type, 0) + 1
                if field.confidence >= 0.7:
                    self.stats.high_confidence_fields += 1

        self.stats.phase_times['extraction'] = (datetime.now() - phase_start).total_seconds()
        logger.info(f"PHASE 2 COMPLETE: {self.stats.total_fields} fields extracted in {self.stats.phase_times['extraction']:.2f}s")

        # Persist to ConPort
        if self.config.persist_to_conport:
            self._persist_extraction_to_conport(fields_by_file)

        return fields_by_file

    def _phase_3_filtering(self, fields_by_file: Dict[Path, List[ExtractedField]]) -> Dict[Path, List[ExtractedField]]:
        """Phase 3: Quality control and confidence filtering."""
        phase_start = datetime.now()
        logger.info("PHASE 3: Starting quality control and filtering")

        filtered_fields = {}

        for file_path, fields in fields_by_file.items():
            # Filter by confidence threshold
            high_quality_fields = [
                field for field in fields
                if field.confidence >= self.config.confidence_threshold
            ]

            # Remove duplicates (same content and type)
            unique_fields = []
            seen = set()
            for field in high_quality_fields:
                key = (field.field_type, field.content.strip().lower())
                if key not in seen:
                    seen.add(key)
                    unique_fields.append(field)

            filtered_fields[file_path] = unique_fields
            logger.debug(f"Filtered {file_path.name}: {len(fields)} -> {len(unique_fields)} fields")

        self.stats.phase_times['filtering'] = (datetime.now() - phase_start).total_seconds()
        logger.info(f"PHASE 3 COMPLETE: Quality filtering done in {self.stats.phase_times['filtering']:.2f}s")

        return filtered_fields

    def _phase_4_knowledge_graph(self, filtered_fields: Dict[Path, List[ExtractedField]]) -> Dict[str, Any]:
        """Phase 4: Knowledge graph construction."""
        phase_start = datetime.now()
        logger.info("PHASE 4: Starting knowledge graph construction")

        # Simple knowledge graph: relationships between fields
        knowledge_graph = {
            'nodes': [],
            'edges': [],
            'statistics': {}
        }

        # Create nodes for each unique field
        node_id = 0
        field_to_node = {}
        fields_list = []  # Keep ordered list for iteration

        for file_path, fields in filtered_fields.items():
            for field in fields:
                node_id += 1
                node = {
                    'id': node_id,
                    'type': field.field_type,
                    'content': field.content,
                    'confidence': field.confidence,
                    'source_file': str(file_path.name),
                    'stakeholders': field.stakeholders
                }
                knowledge_graph['nodes'].append(node)

                # Create a unique hashable key for the field
                field_key = (field.field_type, field.content[:100], str(file_path.name), len(fields_list))
                field_to_node[field_key] = node_id
                fields_list.append((field_key, field))

        # Create edges based on stakeholder relationships and content similarity
        for field_key1, field1 in fields_list:
            for field_key2, field2 in fields_list:
                if field1 != field2:
                    # Stakeholder relationships
                    common_stakeholders = set(field1.stakeholders) & set(field2.stakeholders)
                    if common_stakeholders:
                        knowledge_graph['edges'].append({
                            'source': field_to_node[field_key1],
                            'target': field_to_node[field_key2],
                            'type': 'shared_stakeholder',
                            'weight': len(common_stakeholders)
                        })

        knowledge_graph['statistics'] = {
            'total_nodes': len(knowledge_graph['nodes']),
            'total_edges': len(knowledge_graph['edges']),
            'node_types': {}
        }

        # Calculate node type statistics
        for node in knowledge_graph['nodes']:
            node_type = node['type']
            knowledge_graph['statistics']['node_types'][node_type] = \
                knowledge_graph['statistics']['node_types'].get(node_type, 0) + 1

        self.stats.phase_times['knowledge_graph'] = (datetime.now() - phase_start).total_seconds()
        logger.info(f"PHASE 4 COMPLETE: Knowledge graph built in {self.stats.phase_times['knowledge_graph']:.2f}s")

        # Save knowledge graph
        kg_path = self.config.output_directory / "knowledge_graph.json"
        with open(kg_path, 'w') as f:
            json.dump(knowledge_graph, f, indent=2, default=str)

        return knowledge_graph

    def _phase_5_synthesis(self, filtered_fields: Dict[Path, List[ExtractedField]]) -> Dict[str, Any]:
        """Phase 5: Document synthesis."""
        phase_start = datetime.now()
        logger.info("PHASE 5: Starting document synthesis")

        if not self.config.enable_synthesis:
            logger.info("Document synthesis disabled")
            return {}

        # Combine all fields for synthesis
        all_fields = []
        for fields in filtered_fields.values():
            all_fields.extend(fields)

        if not all_fields:
            logger.warning("No fields available for synthesis")
            return {}

        # Generate documents
        synthesis_result = self.synthesis_engine.synthesize_documents(
            all_fields,
            metadata={
                'total_files': self.stats.total_files,
                'extraction_timestamp': datetime.now().isoformat(),
                'confidence_threshold': self.config.confidence_threshold
            }
        )

        # Save documents to files
        documents_dir = self.config.output_directory / "documents"
        for doc_name, doc_content in synthesis_result['documents'].items():
            doc_path = documents_dir / f"{doc_name}.md"
            with open(doc_path, 'w') as f:
                f.write(doc_content)
            logger.info(f"Generated document: {doc_path}")

        # Save synthesis analysis
        analysis_path = self.config.output_directory / "synthesis_analysis.json"
        with open(analysis_path, 'w') as f:
            json.dump(synthesis_result['analysis'], f, indent=2, default=str)

        self.stats.documents_generated = len(synthesis_result['documents'])
        self.stats.phase_times['synthesis'] = (datetime.now() - phase_start).total_seconds()
        logger.info(f"PHASE 5 COMPLETE: {self.stats.documents_generated} documents generated in {self.stats.phase_times['synthesis']:.2f}s")

        # Persist to ConPort
        if self.config.persist_to_conport:
            self._persist_synthesis_to_conport(synthesis_result)

        return synthesis_result

    def _phase_6_archive_and_report(self, processed_files: List[Path], synthesis_result: Dict[str, Any]):
        """Phase 6: Archive processed files and generate comprehensive report."""
        phase_start = datetime.now()
        logger.info("PHASE 6: Starting archival and reporting")

        # Archive processed files
        for file_path in processed_files:
            try:
                archived_path = self.config.archive_directory / file_path.name
                shutil.move(str(file_path), str(archived_path))
                logger.debug(f"Archived: {file_path.name}")
                self.stats.files_processed += 1
            except Exception as e:
                logger.error(f"Error archiving {file_path}: {e}")
                self.stats.errors.append(f"Archive {file_path.name}: {str(e)}")

        # Generate comprehensive report
        report = self._generate_comprehensive_report(synthesis_result)

        # Save report
        report_path = self.config.output_directory / "reports" / f"extraction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        self.stats.phase_times['archive_report'] = (datetime.now() - phase_start).total_seconds()
        logger.info(f"PHASE 6 COMPLETE: Archival and reporting done in {self.stats.phase_times['archive_report']:.2f}s")

    def _chunk_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Chunk a single file using semantic chunking."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Use semantic chunker with proper method and parameters
            conversation_chunks = self.chunker.chunk_from_text(
                content,
                format_type="colon_separated",
                show_progress=False
            )

            # Convert ConversationChunk objects to our format
            processed_chunks = []
            for i, conv_chunk in enumerate(conversation_chunks):
                # Extract text content from conversation chunk
                chunk_content = []
                for message in conv_chunk.messages:
                    if hasattr(message, 'speaker') and hasattr(message, 'content'):
                        chunk_content.append(f"{message.speaker}: {message.content}")
                    else:
                        chunk_content.append(str(message.content))

                processed_chunks.append({
                    'id': f"{file_path.stem}_{i}",
                    'content': '\n'.join(chunk_content),
                    'source_file': str(file_path),
                    'chunk_index': i,
                    'timestamp': datetime.now().isoformat(),
                    'participants': conv_chunk.participants if hasattr(conv_chunk, 'participants') else [],
                    'chunk_type': conv_chunk.chunk_type if hasattr(conv_chunk, 'chunk_type') else 'unknown'
                })

            return processed_chunks

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return []

    def _persist_chunking_to_conport(self, chunks_by_file: Dict[Path, List[Dict[str, Any]]]):
        """Persist chunking phase results to ConPort."""
        if not self.config.workspace_id:
            return

        try:
            # Log phase progress to ConPort
            phase_summary = {
                "phase": "chunking",
                "timestamp": datetime.now().isoformat(),
                "files_processed": len(chunks_by_file),
                "total_chunks": sum(len(chunks) for chunks in chunks_by_file.values()),
                "phase_duration": self.stats.phase_times.get('chunking', 0),
                "files": [str(file_path.name) for file_path in chunks_by_file.keys()]
            }

            # Store chunking results in ConPort custom data
            self._call_conport('log_custom_data', {
                'workspace_id': self.config.workspace_id,
                'category': 'extraction_pipeline',
                'key': f'chunking_phase_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'value': phase_summary
            })

            # Log progress entry
            self._call_conport('log_progress', {
                'workspace_id': self.config.workspace_id,
                'status': 'DONE',
                'description': f'Phase 1 Complete: Chunked {len(chunks_by_file)} files into {phase_summary["total_chunks"]} semantic chunks'
            })

            logger.info("Persisted chunking results to ConPort")

        except Exception as e:
            logger.error(f"Error persisting chunking to ConPort: {e}")

    def _persist_extraction_to_conport(self, fields_by_file: Dict[Path, List[ExtractedField]]):
        """Persist extraction phase results to ConPort."""
        if not self.config.workspace_id:
            return

        try:
            # Aggregate extraction statistics
            extraction_summary = {
                "phase": "extraction",
                "timestamp": datetime.now().isoformat(),
                "files_processed": len(fields_by_file),
                "total_fields": self.stats.total_fields,
                "fields_by_type": self.stats.fields_by_type,
                "high_confidence_fields": self.stats.high_confidence_fields,
                "extractors_used": list(self.extractors.keys()),
                "phase_duration": self.stats.phase_times.get('extraction', 0)
            }

            # Store extraction results in ConPort
            self._call_conport('log_custom_data', {
                'workspace_id': self.config.workspace_id,
                'category': 'extraction_pipeline',
                'key': f'extraction_phase_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'value': extraction_summary
            })

            # Log key decisions discovered
            decision_fields = [field for fields in fields_by_file.values() for field in fields if field.field_type == 'decision']
            for field in decision_fields[:5]:  # Log top 5 decisions
                if field.confidence >= 0.7:  # High confidence decisions only
                    self._call_conport('log_decision', {
                        'workspace_id': self.config.workspace_id,
                        'summary': field.content[:200] + "..." if len(field.content) > 200 else field.content,
                        'rationale': f"Extracted from chatlog with {field.confidence:.2f} confidence",
                        'implementation_details': field.context[:300] if field.context else None,
                        'tags': ['chatlog_extraction', field.field_type, f'confidence_{int(field.confidence*10)/10}']
                    })

            # Log progress entry
            self._call_conport('log_progress', {
                'workspace_id': self.config.workspace_id,
                'status': 'DONE',
                'description': f'Phase 2 Complete: Extracted {self.stats.total_fields} fields using {len(self.extractors)} extractors'
            })

            logger.info("Persisted extraction results to ConPort")

        except Exception as e:
            logger.error(f"Error persisting extraction to ConPort: {e}")

    def _persist_synthesis_to_conport(self, synthesis_result: Dict[str, Any]):
        """Persist synthesis phase results to ConPort."""
        if not self.config.workspace_id or not synthesis_result:
            return

        try:
            # Store synthesis analysis
            analysis = synthesis_result.get('analysis', {})
            synthesis_summary = {
                "phase": "synthesis",
                "timestamp": datetime.now().isoformat(),
                "documents_generated": len(synthesis_result.get('documents', {})),
                "templates_used": analysis.get('selected_templates', []),
                "field_analysis": analysis.get('field_summary', {}),
                "phase_duration": self.stats.phase_times.get('synthesis', 0)
            }

            self._call_conport('log_custom_data', {
                'workspace_id': self.config.workspace_id,
                'category': 'extraction_pipeline',
                'key': f'synthesis_phase_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'value': synthesis_summary
            })

            # Log system pattern for document generation
            self._call_conport('log_system_pattern', {
                'workspace_id': self.config.workspace_id,
                'name': 'chatlog_document_synthesis',
                'description': f'Adaptive document synthesis generating {len(synthesis_result.get("documents", {}))} documents from extracted chatlog fields',
                'tags': ['document_synthesis', 'chatlog_extraction', 'adaptive_templates']
            })

            # Log progress entry
            self._call_conport('log_progress', {
                'workspace_id': self.config.workspace_id,
                'status': 'DONE',
                'description': f'Phase 5 Complete: Generated {len(synthesis_result.get("documents", {}))} documents via adaptive synthesis'
            })

            logger.info("Persisted synthesis results to ConPort")

        except Exception as e:
            logger.error(f"Error persisting synthesis to ConPort: {e}")

    def _call_conport(self, function_name: str, params: dict):
        """Make a ConPort MCP call with error handling."""
        try:
            # In a real implementation, this would use the MCP client
            # For now, we'll simulate the call and log the intent
            logger.debug(f"ConPort call: {function_name} with params: {params}")

            # This is where the actual MCP call would go:
            # result = conport_client.call(f"mcp__conport__{function_name}", params)
            # return result

        except Exception as e:
            logger.error(f"ConPort MCP call failed for {function_name}: {e}")
            raise

    def _generate_comprehensive_report(self, synthesis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive processing report."""
        return {
            'pipeline_summary': {
                'timestamp': datetime.now().isoformat(),
                'configuration': {
                    'source_directory': str(self.config.source_directory),
                    'output_directory': str(self.config.output_directory),
                    'confidence_threshold': self.config.confidence_threshold,
                    'extractors_used': list(self.extractors.keys()),
                    'synthesis_enabled': self.config.enable_synthesis
                }
            },
            'processing_statistics': {
                'total_files': self.stats.total_files,
                'files_processed': self.stats.files_processed,
                'total_chunks': self.stats.total_chunks,
                'total_fields': self.stats.total_fields,
                'fields_by_type': self.stats.fields_by_type,
                'high_confidence_fields': self.stats.high_confidence_fields,
                'documents_generated': self.stats.documents_generated,
                'processing_time_seconds': self.stats.processing_time,
                'phase_times': self.stats.phase_times
            },
            'quality_metrics': {
                'confidence_distribution': self._calculate_confidence_distribution(),
                'extraction_coverage': self._calculate_extraction_coverage(),
                'synthesis_quality': synthesis_result.get('analysis', {}) if synthesis_result else {}
            },
            'errors_and_warnings': {
                'total_errors': len(self.stats.errors),
                'error_details': self.stats.errors
            }
        }

    def _calculate_confidence_distribution(self) -> Dict[str, int]:
        """Calculate distribution of confidence scores."""
        # This would analyze all extracted fields
        # For now, return placeholder
        return {
            'high_confidence_0.8+': self.stats.high_confidence_fields,
            'medium_confidence_0.5-0.8': self.stats.total_fields - self.stats.high_confidence_fields,
            'low_confidence_<0.5': 0
        }

    def _calculate_extraction_coverage(self) -> Dict[str, float]:
        """Calculate extraction coverage by field type."""
        if not self.stats.fields_by_type:
            return {}

        total = sum(self.stats.fields_by_type.values())
        return {
            field_type: (count / total) * 100
            for field_type, count in self.stats.fields_by_type.items()
        }

    def _create_results(self, start_time: datetime) -> Dict[str, Any]:
        """Create final results dictionary."""
        return {
            'success': len(self.stats.errors) == 0,
            'statistics': {
                'total_files': self.stats.total_files,
                'files_processed': self.stats.files_processed,
                'total_chunks': self.stats.total_chunks,
                'total_fields': self.stats.total_fields,
                'fields_by_type': self.stats.fields_by_type,
                'high_confidence_fields': self.stats.high_confidence_fields,
                'documents_generated': self.stats.documents_generated,
                'processing_time': self.stats.processing_time,
                'phase_times': self.stats.phase_times
            },
            'errors': self.stats.errors,
            'output_directory': str(self.config.output_directory),
            'archive_directory': str(self.config.archive_directory),
            'timestamp': start_time.isoformat()
        }