"""
Unified Document Pipeline Orchestrator

Coordinates the complete document processing pipeline:
1. Multi-layer extraction (basic, ADHD, multi-angle)
2. Atomic unit normalization
3. TSV registry generation
4. Vector embedding generation
5. Multiple output format support
"""

import sys
import asyncio
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time
import json

# Import from doc_processor for TSV and atomic units
doc_processor_path = Path(__file__).parent.parent.parent.parent / "doc_processor"
sys.path.insert(0, str(doc_processor_path))

try:
    from normalizer import AtomicUnit, AtomicUnitsNormalizer
    from registries import RegistryBuilder
    from embedder import DocumentEmbedder
except ImportError as e:
    print(f"⚠️ Could not import doc_processor modules: {e}")
    AtomicUnit = None
    AtomicUnitsNormalizer = None
    RegistryBuilder = None
    DocumentEmbedder = None

from .unified_extractor import UnifiedDocumentExtractor, ExtractionResult
from .synthesizer import DocumentSynthesizer, SynthesisConfig
# Updated imports for modular embedding system
from ..embeddings import (
    AdvancedEmbeddingConfig,
    EmbeddingHealthMetrics,
    create_production_config,
    HybridVectorStore,
    ConsensusValidator,
    create_consensus_config
)


@dataclass
class PipelineConfig:
    """Configuration for the unified document pipeline."""
    source_directory: Path
    output_directory: Path

    # Extraction settings
    enable_adhd_extraction: bool = True
    enable_multi_angle: bool = True
    file_extensions: Optional[List[str]] = None
    confidence_threshold: float = 0.5

    # Pipeline components
    generate_tsv_registries: bool = True
    generate_embeddings: bool = True
    generate_summaries: bool = True

    # Synthesis settings
    enable_synthesis: bool = True
    synthesis_types: List[str] = None
    synthesis_format: str = "markdown"

    # Advanced Embedding settings
    embedding_model: str = "voyage-context-3"
    embedding_provider: str = "auto"
    require_embeddings: bool = False
    rerank_model: str = "voyage-rerank-2.5"
    embedding_dimension: int = 2048

    # Hybrid search configuration
    bm25_weight: float = 0.3
    vector_weight: float = 0.7
    enable_learning_to_rank: bool = False

    # Vector index settings
    enable_quantization: bool = True
    enable_consensus_validation: bool = False  # Expensive, use selectively

    # Legacy settings (for compatibility)
    milvus_uri: Optional[str] = None
    similarity_threshold: float = 0.92

    # Output formats
    export_json: bool = True
    export_csv: bool = False
    export_markdown: bool = False


@dataclass
class PipelineResult:
    """Results from complete pipeline execution."""
    config: PipelineConfig
    success: bool
    processing_time: float

    # Extraction results
    extraction_summary: Dict[str, Any]
    total_entities: int
    document_count: int

    # TSV registry results
    registry_files: Dict[str, str] = None
    registry_counts: Dict[str, int] = None

    # Advanced Embedding results
    embedding_summary: Dict[str, Any] = None
    vector_count: int = 0
    embedding_health_metrics: EmbeddingHealthMetrics = None
    consensus_summary: Dict[str, Any] = None

    # Output files
    output_files: List[str] = None
    error_message: Optional[str] = None


class UnifiedDocumentPipeline:
    """
    Complete document processing pipeline orchestrator.

    Integrates extraction, normalization, registry building, and embedding
    generation into a single, comprehensive workflow.
    """

    def __init__(self, config: PipelineConfig):
        """Initialize pipeline with configuration."""
        self.config = config

        # Ensure output directory exists
        self.config.output_directory.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.unified_extractor = UnifiedDocumentExtractor()

        # Initialize MultiAngleExtractor with output directory if needed
        if self.config.enable_multi_angle:
            try:
                from ..analysis.extractor import MultiAngleExtractor
                self.unified_extractor.multi_angle_extractor = MultiAngleExtractor(self.config.output_directory)
            except ImportError:
                print("⚠️ MultiAngleExtractor not available - multi-angle extraction disabled")
                self.config.enable_multi_angle = False

        # Initialize doc_processor components if available
        self.normalizer = AtomicUnitsNormalizer() if AtomicUnitsNormalizer else None
        self.registry_builder = (RegistryBuilder(self.config.output_directory)
                               if RegistryBuilder else None)

        # Initialize advanced embedding system
        self.advanced_embedding_config = self._create_advanced_embedding_config()
        self.hybrid_vector_store = None
        self.consensus_validator = None
        self.embedding_health_metrics = EmbeddingHealthMetrics()

        # Legacy embedder for backward compatibility
        self.embedder = (DocumentEmbedder(
            model_name=self.config.embedding_model,
            milvus_uri=self.config.milvus_uri,
            similarity_threshold=self.config.similarity_threshold
        ) if DocumentEmbedder else None)

        # Processing stats
        self.start_time = None
        self.extraction_results = []
        self.atomic_units = []

    def _create_advanced_embedding_config(self) -> AdvancedEmbeddingConfig:
        """Create advanced embedding configuration from pipeline config."""
        # Start with production defaults
        config = create_production_config()

        # Override with pipeline-specific settings
        config.embedding_model = self.config.embedding_model
        config.rerank_model = self.config.rerank_model
        config.embedding_dimension = self.config.embedding_dimension
        config.bm25_weight = self.config.bm25_weight
        config.vector_weight = self.config.vector_weight
        config.enable_learning_to_rank = self.config.enable_learning_to_rank
        config.enable_quantization = self.config.enable_quantization
        config.enable_consensus = self.config.enable_consensus_validation

        # Set output directory for persistence
        config.persist_directory = str(self.config.output_directory / ".advanced_vectors")

        provider_status = self._resolve_embedding_provider()
        if provider_status["resolved_provider"] == "voyage":
            config.voyage_api_key = os.environ.get("VOYAGE_API_KEY")
            config.use_on_premise = False
        else:
            config.voyage_api_key = None
            config.use_on_premise = True

        return config

    def _resolve_embedding_provider(self) -> Dict[str, Any]:
        requested = (self.config.embedding_provider or "auto").lower()
        if requested not in {"auto", "voyage", "none"}:
            raise ValueError(f"Unsupported embedding provider: {self.config.embedding_provider}")

        api_key_present = bool(os.environ.get("VOYAGE_API_KEY"))
        if not self.config.generate_embeddings:
            resolved = "none"
            status = "disabled"
            reason = "embeddings_disabled"
        elif requested == "none":
            resolved = "none"
            status = "skipped_provider_none"
            reason = "provider_none"
        elif requested == "voyage":
            resolved = "voyage" if api_key_present else "none"
            status = "ready" if api_key_present else "skipped_no_credentials"
            reason = None if api_key_present else "voyage_api_key_missing"
        elif api_key_present:
            resolved = "voyage"
            status = "ready"
            reason = None
        else:
            resolved = "none"
            status = "skipped_no_credentials"
            reason = "voyage_api_key_missing"

        return {
            "requested_provider": requested,
            "resolved_provider": resolved,
            "api_key_present": api_key_present,
            "status": status,
            "skipped_reason": reason,
        }

    def _embedding_manifest_path(self) -> Path:
        return self.config.output_directory / "embedding_manifest.json"

    def _write_embedding_manifest(self, manifest: Dict[str, Any]) -> Path:
        manifest_path = self._embedding_manifest_path()
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True, default=str)
        return manifest_path

    def _build_embedding_documents(self) -> List[Dict[str, Any]]:
        documents: List[Dict[str, Any]] = []
        if self.atomic_units:
            for unit in self.atomic_units:
                doc_content = f"{unit.title}\n\n{unit.content}"
                documents.append({
                    'id': unit.id,
                    'content': doc_content,
                    'metadata': {
                        'source_file': unit.source_file,
                        'doc_type': unit.doc_type,
                        'tags': unit.tags,
                        'title': unit.title
                    }
                })
            return documents

        for result_index, result in enumerate(self.extraction_results):
            if not result.success:
                continue

            entity_texts: List[str] = []
            for layer_entities in [
                result.basic_entities,
                result.adhd_entities,
                result.multi_angle_entities,
            ]:
                for entity_list in layer_entities.values():
                    for entity in entity_list:
                        if not isinstance(entity, dict):
                            continue
                        parts = [
                            str(entity.get("content", "")).strip(),
                            str(entity.get("value", "")).strip(),
                        ]
                        text = ": ".join(part for part in parts if part)
                        if text:
                            entity_texts.append(text)

            if entity_texts:
                content = "\n".join(entity_texts)
            else:
                try:
                    content = result.document_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    content = ""

            if not content.strip():
                continue

            documents.append({
                'id': f"document:{result.document_path.stem}:{result_index}",
                'content': content,
                'metadata': {
                    'source_file': str(result.document_path),
                    'doc_type': result.document_type,
                    'title': result.document_path.name,
                    'fallback_from_extraction_results': True,
                }
            })

        return documents

    async def process_documents(self) -> PipelineResult:
        """Execute the complete document processing pipeline."""
        self.start_time = time.time()

        try:
            print("🚀 Starting unified document processing pipeline...")

            # Step 1: Multi-layer extraction
            print("📄 Step 1: Multi-layer document extraction...")
            extraction_summary = self._run_extraction()

            # Step 2: Convert to atomic units
            print("⚛️  Step 2: Converting to atomic units...")
            atomic_units_count = self._convert_to_atomic_units()

            # Step 3: Generate TSV registries
            registry_files = {}
            registry_counts = {}
            if self.config.generate_tsv_registries and self.registry_builder:
                print("📊 Step 3: Building TSV registries...")
                registry_files, registry_counts = self._build_registries()
            else:
                print("⏭️  Step 3: Skipping TSV registries (disabled or unavailable)")

            # Step 4: Generate embeddings
            embedding_summary = {}
            vector_count = 0
            if self.config.generate_embeddings:
                print("🔍 Step 4: Generating advanced embeddings...")
                import asyncio
                embedding_summary, vector_count = await self._generate_embeddings()
            else:
                print("⏭️  Step 4: Skipping embeddings (disabled)")

            # Step 5: Generate document synthesis
            synthesis_files = []
            if self.config.enable_synthesis:
                print("📝 Step 5: Generating document synthesis...")
                synthesis_files = self._generate_synthesis(extraction_summary)
            else:
                print("⏭️  Step 5: Skipping synthesis (disabled)")

            # Step 6: Export in multiple formats
            print("📤 Step 6: Exporting results...")
            output_files = self._export_results(extraction_summary)
            output_files.extend(synthesis_files)
            if embedding_summary.get("manifest_path"):
                output_files.append(embedding_summary["manifest_path"])

            processing_time = time.time() - self.start_time
            print(f"✅ Pipeline complete! ({processing_time:.2f}s)")

            return PipelineResult(
                config=self.config,
                success=True,
                processing_time=processing_time,
                extraction_summary=extraction_summary,
                total_entities=extraction_summary.get('summary', {}).get('total_entities', 0),
                document_count=len(self.extraction_results),
                registry_files=registry_files,
                registry_counts=registry_counts,
                embedding_summary=embedding_summary,
                vector_count=vector_count,
                embedding_health_metrics=self.embedding_health_metrics,
                consensus_summary=embedding_summary.get('consensus_summary') if embedding_summary else None,
                output_files=output_files
            )

        except Exception as e:
            processing_time = time.time() - self.start_time if self.start_time else 0
            print(f"❌ Pipeline failed: {e}")

            return PipelineResult(
                config=self.config,
                success=False,
                processing_time=processing_time,
                extraction_summary={},
                total_entities=0,
                document_count=0,
                error_message=str(e)
            )

    def _run_extraction(self) -> Dict[str, Any]:
        """Run multi-layer extraction on all documents."""
        self.extraction_results = self.unified_extractor.extract_from_directory(
            self.config.source_directory,
            enable_adhd=self.config.enable_adhd_extraction,
            enable_multi_angle=self.config.enable_multi_angle,
            file_extensions=self.config.file_extensions
        )

        # Merge results
        extraction_summary = self.unified_extractor.merge_extraction_results(
            self.extraction_results
        )

        # Add total entity count
        total_entities = 0
        for layer in ['basic', 'adhd', 'multi_angle']:
            for entity_list in extraction_summary['all_entities'][layer].values():
                total_entities += len(entity_list)

        extraction_summary['summary']['total_entities'] = total_entities

        print(f"✅ Extracted {total_entities} entities from {len(self.extraction_results)} documents")
        return extraction_summary

    def _convert_to_atomic_units(self) -> int:
        """Convert extraction results to atomic units format."""
        if not self.normalizer or not AtomicUnit:
            print("⚠️ Atomic unit conversion unavailable - skipping")
            return 0

        self.atomic_units = []

        for result in self.extraction_results:
            if not result.success:
                continue

            # Create atomic units from each entity
            unit_id_counter = 0

            # Process basic entities
            for entity_type, entity_list in result.basic_entities.items():
                for entity in entity_list:
                    if self._meets_confidence_threshold(entity):
                        unit = self._create_atomic_unit(
                            result, entity_type, entity, unit_id_counter
                        )
                        if unit:
                            self.atomic_units.append(unit)
                            unit_id_counter += 1

            # Process ADHD entities
            for entity_type, entity_list in result.adhd_entities.items():
                for entity in entity_list:
                    if self._meets_confidence_threshold(entity):
                        unit = self._create_atomic_unit(
                            result, f"adhd_{entity_type}", entity, unit_id_counter
                        )
                        if unit:
                            # Add ADHD-specific tags
                            unit.tags.extend(['adhd', 'accommodation'])
                            self.atomic_units.append(unit)
                            unit_id_counter += 1

        print(f"✅ Created {len(self.atomic_units)} atomic units")
        return len(self.atomic_units)

    def _meets_confidence_threshold(self, entity: Dict[str, Any]) -> bool:
        """Check if entity meets confidence threshold."""
        confidence = entity.get('confidence', 1.0)
        return confidence >= self.config.confidence_threshold

    def _create_atomic_unit(self, result: ExtractionResult,
                           entity_type: str, entity: Dict[str, Any],
                           unit_id: int) -> Optional[AtomicUnit]:
        """Create an AtomicUnit from an extraction entity."""
        try:
            content = entity.get('content', '')
            value = entity.get('value', '')

            # Combine content and value for the unit content
            unit_content = f"{content}: {value}" if value else content

            if not unit_content.strip():
                return None

            return AtomicUnit(
                id=f"{result.document_path.stem}-{entity_type}-{unit_id}",
                content=unit_content.strip(),
                title=entity.get('title', content[:50] + "..." if len(content) > 50 else content),
                source_file=str(result.document_path),
                line_start=1,  # Simplified - would need line tracking
                line_end=1,
                doc_type=result.document_type,
                tags=[entity_type, result.document_type.lower()]
            )
        except Exception as e:
            print(f"⚠️ Error creating atomic unit: {e}")
            return None

    def _build_registries(self) -> tuple[Dict[str, str], Dict[str, int]]:
        """Build TSV registries from atomic units."""
        if not self.registry_builder or not self.atomic_units:
            return {}, {}

        try:
            registry_counts = self.registry_builder.build_registries(self.atomic_units)

            # Map registry names to file paths
            registry_files = {
                'features': str(self.config.output_directory / "features.tsv"),
                'components': str(self.config.output_directory / "components.tsv"),
                'subsystems': str(self.config.output_directory / "subsystems.tsv"),
                'research': str(self.config.output_directory / "research.tsv"),
                'evidence_links': str(self.config.output_directory / "evidence_links.tsv")
            }

            # Only include files that exist
            existing_files = {}
            for name, path in registry_files.items():
                if Path(path).exists():
                    existing_files[name] = path

            print(f"✅ Generated {len(existing_files)} TSV registries")
            return existing_files, registry_counts

        except Exception as e:
            print(f"⚠️ Registry building failed: {e}")
            return {}, {}

    async def _generate_embeddings(self) -> tuple[Dict[str, Any], int]:
        """Generate advanced vector embeddings with hybrid search capability."""
        provider_status = self._resolve_embedding_provider()

        documents = self._build_embedding_documents()

        if (
            self.config.require_embeddings
            and provider_status["resolved_provider"] != "voyage"
        ):
            manifest = {
                **provider_status,
                "model": self.advanced_embedding_config.embedding_model,
                "total_units": len(documents),
                "embedded_count": 0,
                "indexed_count": 0,
                "embedding_status": "failed_required_embeddings",
                "cost_estimate_usd": None,
                "output_paths": {
                    "manifest": str(self._embedding_manifest_path()),
                    "index_directory": self.advanced_embedding_config.persist_directory,
                },
            }
            self._write_embedding_manifest(manifest)
            raise RuntimeError("Embeddings were required, but VOYAGE_API_KEY is not configured")

        if not documents:
            print("⚠️ No documents available for embedding")
            manifest = {
                **provider_status,
                "model": self.advanced_embedding_config.embedding_model,
                "total_units": 0,
                "embedded_count": 0,
                "indexed_count": 0,
                "embedding_status": "skipped_no_documents",
                "cost_estimate_usd": None,
                "output_paths": {
                    "manifest": str(self._embedding_manifest_path()),
                    "index_directory": self.advanced_embedding_config.persist_directory,
                },
            }
            self._write_embedding_manifest(manifest)
            return manifest, 0

        try:
            from datetime import datetime
            self.embedding_health_metrics.processing_start_time = datetime.now()
            self.embedding_health_metrics.documents_processed = len(self.atomic_units)

            print(f"🔍 Initializing advanced embedding system for {len(documents)} units...")

            # Initialize hybrid vector store
            self.hybrid_vector_store = HybridVectorStore(
                self.advanced_embedding_config,
                persist_directory=Path(self.advanced_embedding_config.persist_directory)
            )

            # Initialize consensus validator if enabled
            if self.config.enable_consensus_validation:
                consensus_config = create_consensus_config()
                self.consensus_validator = ConsensusValidator(consensus_config)
                print("🤝 Consensus validation enabled")

            print(f"📝 Prepared {len(documents)} local extraction units for embedding/indexing")

            # Add documents to hybrid vector store
            await self.hybrid_vector_store.add_documents(documents)
            indexed_count = self.hybrid_vector_store.get_stats().get("documents", {}).get("document_count", 0)
            embedded_count = self.hybrid_vector_store.metrics.documents_embedded

            # Update health metrics
            self.embedding_health_metrics.documents_embedded = embedded_count
            self.embedding_health_metrics.vector_index_size_mb = self.hybrid_vector_store.get_index_size_mb()

            # Run consensus validation on sample documents if enabled
            consensus_summary = {}
            if self.consensus_validator and len(documents) > 0:
                print("🤝 Running consensus validation on sample documents...")
                # Validate first 5 documents as sample
                sample_docs = documents[:5]
                for doc in sample_docs:
                    # Get primary embedding from hybrid store
                    query_vector = await self.hybrid_vector_store._get_query_vector(doc['content'])
                    await self.consensus_validator.validate_embedding(
                        doc['id'], doc['content'], query_vector
                    )

                consensus_summary = self.consensus_validator.get_consensus_summary()
                print(f"✅ Consensus validation complete: {consensus_summary.get('avg_consensus_score', 0):.3f} avg score")

            # Create comprehensive embedding summary
            embedding_status = (
                "completed"
                if provider_status["resolved_provider"] == "voyage" and embedded_count > 0
                else provider_status["status"]
            )
            embedding_summary = {
                'model': self.advanced_embedding_config.embedding_model,
                'rerank_model': self.advanced_embedding_config.rerank_model,
                'dimension': self.advanced_embedding_config.embedding_dimension,
                'requested_provider': provider_status["requested_provider"],
                'resolved_provider': provider_status["resolved_provider"],
                'credential_source_present': provider_status["api_key_present"],
                'total_units': len(documents),
                'embedded_documents': embedded_count,
                'embedded_count': embedded_count,
                'indexed_count': indexed_count,
                'skipped_reason': provider_status["skipped_reason"],
                'embedding_status': embedding_status,
                'hybrid_search_enabled': True,
                'bm25_weight': self.advanced_embedding_config.bm25_weight,
                'vector_weight': self.advanced_embedding_config.vector_weight,
                'quantization_enabled': self.advanced_embedding_config.enable_quantization,
                'consensus_validation_enabled': self.config.enable_consensus_validation,
                'index_size_mb': self.embedding_health_metrics.vector_index_size_mb,
                'persist_directory': self.advanced_embedding_config.persist_directory,
                'status': embedding_status,
                'cost_estimate_usd': None,
                'output_paths': {
                    'manifest': str(self._embedding_manifest_path()),
                    'index_directory': self.advanced_embedding_config.persist_directory,
                },
                'processing_time_ms': self.embedding_health_metrics.avg_embedding_time_ms,
                'consensus_summary': consensus_summary if consensus_summary else None
            }
            manifest_path = self._write_embedding_manifest(embedding_summary)
            embedding_summary['manifest_path'] = str(manifest_path)

            # Display ADHD-friendly progress summary
            if self.advanced_embedding_config.visual_progress_indicators:
                self.embedding_health_metrics.display_progress(gentle_mode=True)

            print(f"✅ Advanced embedding indexing complete! {indexed_count} documents indexed")
            print(f"   📊 Model: {self.advanced_embedding_config.embedding_model} ({self.advanced_embedding_config.embedding_dimension}D)")
            print(f"   🔍 Hybrid search: BM25({self.advanced_embedding_config.bm25_weight}) + Vector({self.advanced_embedding_config.vector_weight})")
            print(f"   💾 Index size: {self.embedding_health_metrics.vector_index_size_mb:.1f}MB")

            return embedding_summary, embedded_count

        except Exception as e:
            print(f"❌ Advanced embedding generation failed: {e}")
            self.embedding_health_metrics.documents_failed += 1
            failure_summary = {
                **provider_status,
                'model': self.advanced_embedding_config.embedding_model,
                'total_units': len(documents),
                'embedded_count': 0,
                'indexed_count': 0,
                'embedding_status': 'failed',
                'status': 'failed',
                'skipped_reason': provider_status.get('skipped_reason'),
                'cost_estimate_usd': None,
                'output_paths': {
                    'manifest': str(self._embedding_manifest_path()),
                    'index_directory': self.advanced_embedding_config.persist_directory,
                },
                'error': str(e),
            }
            self._write_embedding_manifest(failure_summary)
            return failure_summary, 0

    def _generate_synthesis(self, extraction_summary: Dict[str, Any]) -> List[str]:
        """Generate document synthesis using DocumentSynthesizer."""
        synthesis_files = []

        try:
            # Configure synthesis
            synthesis_types = self.config.synthesis_types or ["executive", "adhd"]

            # Determine primary synthesis type (use first one specified)
            primary_synthesis_type = synthesis_types[0] if synthesis_types else "executive"

            synthesis_config = SynthesisConfig(
                synthesis_type=primary_synthesis_type,
                output_format=self.config.synthesis_format,
                confidence_threshold=self.config.confidence_threshold,
                max_length=1000,  # Reasonable limit for synthesis
                enable_topic_clustering=True,
                enable_knowledge_graph=True if "technical" in synthesis_types else False
            )

            # Create synthesizer and generate reports
            synthesizer = DocumentSynthesizer(synthesis_config)
            synthesis_result = synthesizer.synthesize_documents(extraction_summary)

            if synthesis_result.success:
                # Save synthesis reports
                base_output_dir = self.config.output_directory / "synthesis"
                base_output_dir.mkdir(exist_ok=True)

                # Executive summary
                if synthesis_result.executive_summary:
                    exec_file = base_output_dir / f"executive_summary.{self.config.synthesis_format}"
                    exec_file.write_text(synthesis_result.executive_summary, encoding='utf-8')
                    synthesis_files.append(str(exec_file))
                    print(f"  ✅ Executive summary: {exec_file}")

                # ADHD-optimized summary
                if synthesis_result.adhd_summary:
                    adhd_file = base_output_dir / f"adhd_summary.{self.config.synthesis_format}"
                    adhd_file.write_text(synthesis_result.adhd_summary, encoding='utf-8')
                    synthesis_files.append(str(adhd_file))
                    print(f"  ✅ ADHD summary: {adhd_file}")

                # Technical report
                if synthesis_result.technical_report:
                    tech_file = base_output_dir / f"technical_report.{self.config.synthesis_format}"
                    tech_file.write_text(synthesis_result.technical_report, encoding='utf-8')
                    synthesis_files.append(str(tech_file))
                    print(f"  ✅ Technical report: {tech_file}")

                # Topic clusters (JSON format)
                if synthesis_result.topic_clusters:
                    clusters_file = base_output_dir / "topic_clusters.json"
                    with clusters_file.open('w', encoding='utf-8') as f:
                        json.dump(synthesis_result.topic_clusters, f, indent=2, ensure_ascii=False, default=str)
                    synthesis_files.append(str(clusters_file))
                    print(f"  ✅ Topic clusters: {clusters_file}")

                # Knowledge graph (JSON format)
                if synthesis_result.knowledge_graph:
                    graph_file = base_output_dir / "knowledge_graph.json"
                    with graph_file.open('w', encoding='utf-8') as f:
                        json.dump(synthesis_result.knowledge_graph, f, indent=2, ensure_ascii=False, default=str)
                    synthesis_files.append(str(graph_file))
                    print(f"  ✅ Knowledge graph: {graph_file}")

                # Synthesis metadata
                metadata_file = base_output_dir / "synthesis_metadata.json"
                metadata = {
                    "synthesis_config": {
                        "types": synthesis_types,
                        "format": self.config.synthesis_format,
                        "confidence_threshold": self.config.confidence_threshold
                    },
                    "processing_time": synthesis_result.processing_time,
                    "entities_processed": synthesis_result.entities_processed,
                    "topic_count": len(synthesis_result.topic_clusters) if synthesis_result.topic_clusters else 0,
                    "files_generated": len(synthesis_files),
                    "timestamp": synthesis_result.timestamp
                }
                with metadata_file.open('w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                synthesis_files.append(str(metadata_file))

                print(f"✅ Generated {len(synthesis_files)} synthesis files ({synthesis_result.processing_time:.2f}s)")
            else:
                print(f"⚠️ Synthesis generation failed: {synthesis_result.error_message}")

        except Exception as e:
            print(f"⚠️ Synthesis generation failed: {e}")

        return synthesis_files

    def _export_results(self, extraction_summary: Dict[str, Any]) -> List[str]:
        """Export results in requested formats."""
        output_files = []

        # JSON export
        if self.config.export_json:
            json_file = self.config.output_directory / "extraction_results.json"
            with json_file.open('w', encoding='utf-8') as f:
                json.dump(extraction_summary, f, indent=2, ensure_ascii=False, default=str)
            output_files.append(str(json_file))

        # CSV export
        if self.config.export_csv:
            csv_file = self.config.output_directory / "extraction_results.csv"
            self._export_csv(extraction_summary, csv_file)
            output_files.append(str(csv_file))

        # Markdown export
        if self.config.export_markdown:
            md_file = self.config.output_directory / "extraction_results.md"
            self._export_markdown(extraction_summary, md_file)
            output_files.append(str(md_file))

        return output_files

    def _export_csv(self, data: Dict[str, Any], output_file: Path):
        """Export extraction data to CSV format."""
        import csv

        with output_file.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['layer', 'entity_type', 'content', 'value', 'confidence', 'source_file'])

            for layer in ['basic', 'adhd', 'multi_angle']:
                for entity_type, entity_list in data['all_entities'][layer].items():
                    for entity in entity_list:
                        writer.writerow([
                            layer,
                            entity_type,
                            entity.get('content', ''),
                            entity.get('value', ''),
                            entity.get('confidence', ''),
                            entity.get('source_file', '')
                        ])

    def _export_markdown(self, data: Dict[str, Any], output_file: Path):
        """Export extraction data to Markdown format."""
        lines = ["# Document Extraction Results\n"]

        # Summary
        summary = data.get('summary', {})
        lines.append(f"**Documents processed**: {summary.get('total_documents', 0)}")
        lines.append(f"**Successful extractions**: {summary.get('successful_extractions', 0)}")
        lines.append(f"**Total entities**: {summary.get('total_entities', 0)}")
        lines.append(f"**Processing time**: {summary.get('total_processing_time', 0):.2f}s\n")

        # Entities by layer
        for layer in ['basic', 'adhd', 'multi_angle']:
            layer_entities = data['all_entities'][layer]
            if layer_entities:
                lines.append(f"## {layer.title()} Entities\n")

                for entity_type, entity_list in layer_entities.items():
                    if entity_list:
                        lines.append(f"### {entity_type.replace('_', ' ').title()}\n")
                        for entity in entity_list[:10]:  # Limit to first 10
                            content = entity.get('content', 'N/A')
                            confidence = entity.get('confidence', 0)
                            lines.append(f"- {content} _(confidence: {confidence:.2f})_")

                        if len(entity_list) > 10:
                            lines.append(f"- ... and {len(entity_list) - 10} more\n")
                        else:
                            lines.append("")

        output_file.write_text('\n'.join(lines), encoding='utf-8')


async def run_unified_pipeline(source_directory: str,
                              output_directory: str,
                              **kwargs) -> PipelineResult:
    """
    Convenience function to run the complete unified pipeline.

    Args:
        source_directory: Path to documents to process
        output_directory: Path for output files
        **kwargs: Additional configuration options

    Returns:
        Pipeline execution results
    """
    config = PipelineConfig(
        source_directory=Path(source_directory),
        output_directory=Path(output_directory),
        **kwargs
    )

    pipeline = UnifiedDocumentPipeline(config)
    return await pipeline.process_documents()
