#!/usr/bin/env python3
"""
Enhanced Chatlog Extraction Pipeline

Advanced 6-phase pipeline that transforms conversational data into formal documentation
through vector embeddings, semantic analysis, and knowledge synthesis.

Pipeline Phases:
1. Semantic Chunking - Break conversations at natural boundaries
2. Vector Embedding - Create embeddings with voyage-context-3
3. Classification - Multi-label content categorization
4. Entity Extraction - Extract entities, patterns, and relationships
5. Knowledge Graph - Build structured knowledge representation
6. Document Synthesis - Generate formal documentation (PRD, ADR, etc.)

Designed for ADHD-friendly processing with clear checkpoints and progress visibility.
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse
import hashlib

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Confirm, Prompt
from rich.markup import escape

# Import our custom modules
sys.path.append(str(Path(__file__).parent))

from embeddings.voyage_client import VoyageClient, EmbeddingRequest, EmbeddingResult
from processing.semantic_chunker import SemanticChunker, ChatMessage, ConversationChunk

console = Console()

@dataclass
class ExtractionPhase:
    """Represents a single extraction phase."""
    name: str
    description: str
    expected_duration: str
    outputs: List[str]
    dependencies: List[str] = None
    requires_confirmation: bool = True

@dataclass
class ClassificationResult:
    """Results from content classification."""
    chunk_id: str
    content_type: str  # feature, bug, decision, question, implementation
    domain: str       # frontend, backend, database, infrastructure, business
    priority: str     # P0, P1, P2, P3
    status: str       # proposed, approved, in_progress, completed
    confidence: float # 0.0 to 1.0

@dataclass
class ExtractedEntity:
    """Represents an extracted entity."""
    entity_id: str
    entity_type: str  # person, product, component, feature, decision, issue
    text: str
    context: str
    confidence: float
    metadata: Dict[str, Any] = None

@dataclass
class DocumentTemplate:
    """Template for generating structured documents."""
    template_type: str  # PRD, ADR, design_spec, business_plan
    sections: List[str]
    required_entities: List[str]
    output_format: str  # markdown, html, json

class EnhancedChatlogExtractor:
    """
    Advanced 6-phase chatlog extraction system with vector embeddings and synthesis.

    Transforms conversational data into formal documentation through intelligent
    processing phases with ADHD-optimized checkpoints and progress visualization.
    """

    def __init__(
        self,
        chatlog_path: str,
        output_dir: str,
        voyage_api_key: Optional[str] = None,
        enable_vector_embedding: bool = True,
        enable_document_synthesis: bool = True
    ):
        """Initialize the enhanced extractor."""
        self.chatlog_path = Path(chatlog_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.semantic_chunker = SemanticChunker()

        self.voyage_client = None
        if enable_vector_embedding and voyage_api_key:
            try:
                self.voyage_client = VoyageClient(api_key=voyage_api_key)
                console.print("✅ Voyage AI client initialized")
            except Exception as e:
                console.print(f"⚠️ Voyage AI unavailable: {e}")

        # Define enhanced extraction phases
        self.phases = [
            ExtractionPhase(
                name="SemanticChunking",
                description="Break conversations into semantic chunks with context preservation",
                expected_duration="1-2 minutes",
                outputs=["chunks.json", "chunk_analysis.json"],
                dependencies=[]
            ),
            ExtractionPhase(
                name="VectorEmbedding",
                description="Generate vector embeddings for semantic understanding",
                expected_duration="2-5 minutes",
                outputs=["embeddings.json", "similarity_matrix.json"],
                dependencies=["SemanticChunking"]
            ),
            ExtractionPhase(
                name="Classification",
                description="Classify content by type, domain, priority, and status",
                expected_duration="1-3 minutes",
                outputs=["classifications.json", "classification_report.json"],
                dependencies=["VectorEmbedding"]
            ),
            ExtractionPhase(
                name="EntityExtraction",
                description="Extract entities, patterns, decisions, and relationships",
                expected_duration="3-7 minutes",
                outputs=["entities.json", "patterns.json", "decisions.json"],
                dependencies=["Classification"]
            ),
            ExtractionPhase(
                name="KnowledgeGraph",
                description="Build structured knowledge graph with relationships",
                expected_duration="2-4 minutes",
                outputs=["knowledge_graph.json", "relationships.json"],
                dependencies=["EntityExtraction"]
            ),
            ExtractionPhase(
                name="DocumentSynthesis",
                description="Generate formal documentation (PRD, ADR, Design Specs)",
                expected_duration="3-6 minutes",
                outputs=["prd.md", "adr.md", "design_spec.md", "synthesis_report.json"],
                dependencies=["KnowledgeGraph"]
            )
        ]

        # Track processing state
        self.completed_phases = []
        self.phase_results = {}
        self.conversation_chunks = []
        self.embeddings = []
        self.classifications = []
        self.entities = []
        self.knowledge_graph = {}
        self.total_start_time = None

        # Document templates
        self.document_templates = {
            "PRD": DocumentTemplate(
                template_type="PRD",
                sections=["Overview", "Goals", "Requirements", "Success Metrics", "Timeline"],
                required_entities=["feature", "requirement", "goal"],
                output_format="markdown"
            ),
            "ADR": DocumentTemplate(
                template_type="ADR",
                sections=["Context", "Decision", "Consequences", "Alternatives"],
                required_entities=["decision", "alternative", "consequence"],
                output_format="markdown"
            ),
            "DesignSpec": DocumentTemplate(
                template_type="DesignSpec",
                sections=["Architecture", "APIs", "Data Models", "Security", "Performance"],
                required_entities=["component", "api", "database", "security"],
                output_format="markdown"
            ),
            "BusinessPlan": DocumentTemplate(
                template_type="BusinessPlan",
                sections=["Market Analysis", "Revenue Model", "Roadmap", "Resources"],
                required_entities=["market", "revenue", "milestone", "resource"],
                output_format="markdown"
            )
        }

    async def run_extraction(
        self,
        start_phase: str = "SemanticChunking",
        auto_confirm: bool = False
    ) -> Dict[str, Any]:
        """
        Run the complete 6-phase extraction process.

        Args:
            start_phase: Phase to start from
            auto_confirm: Skip user confirmation for automation

        Returns:
            Complete extraction results with all generated artifacts
        """

        console.print(Panel(
            "🤖 [bold blue]Enhanced Chatlog Extraction Pipeline[/bold blue]\n\n"
            f"📁 Input: {self.chatlog_path}\n"
            f"📁 Output: {self.output_dir}\n\n"
            "This advanced pipeline transforms conversations into formal documentation\n"
            "through 6 phases of intelligent processing:\n\n"
            "1. 🧩 Semantic Chunking\n"
            "2. 🚀 Vector Embedding\n"
            "3. 🏷️ Classification\n"
            "4. 🔍 Entity Extraction\n"
            "5. 🕸️ Knowledge Graph\n"
            "6. 📝 Document Synthesis",
            title="🚀 Enhanced Extraction Starting",
            border_style="blue"
        ))

        self.total_start_time = time.time()

        # Find starting phase index
        start_index = 0
        for i, phase in enumerate(self.phases):
            if phase.name == start_phase:
                start_index = i
                break

        # Run phases sequentially
        for i in range(start_index, len(self.phases)):
            phase = self.phases[i]

            # Check dependencies
            if not self._check_dependencies(phase):
                console.print(f"❌ Cannot run {phase.name}: dependencies not met")
                break

            # Display phase information
            self._display_phase_info(phase, i + 1, len(self.phases))

            # Get user confirmation
            if phase.requires_confirmation and not auto_confirm:
                if not Confirm.ask(f"Ready to start {phase.name}?", default=True):
                    console.print("⏸️ Extraction paused. You can resume later.")
                    break

            # Execute phase
            try:
                start_time = time.time()
                result = await self._execute_phase(phase)
                processing_time = time.time() - start_time

                self.phase_results[phase.name] = {
                    "result": result,
                    "processing_time": processing_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.completed_phases.append(phase.name)

                console.print(f"✅ {phase.name} completed in {processing_time:.1f}s")

            except Exception as e:
                console.print(f"❌ {phase.name} failed: {e}")
                break

        # Generate final report
        return self._generate_final_report()

    def _check_dependencies(self, phase: ExtractionPhase) -> bool:
        """Check if phase dependencies are satisfied."""
        if not phase.dependencies:
            return True

        for dep in phase.dependencies:
            if dep not in self.completed_phases:
                return False
        return True

    def _display_phase_info(self, phase: ExtractionPhase, current: int, total: int):
        """Display phase information and progress."""
        console.print(Panel(
            f"[bold cyan]{phase.name}[/bold cyan] ({current}/{total})\n\n"
            f"📋 {phase.description}\n"
            f"⏱️ Expected duration: {phase.expected_duration}\n"
            f"📄 Outputs: {', '.join(phase.outputs)}",
            title=f"Phase {current}: {phase.name}",
            border_style="cyan"
        ))

    async def _execute_phase(self, phase: ExtractionPhase) -> Dict[str, Any]:
        """Execute a specific phase based on its name."""

        if phase.name == "SemanticChunking":
            return await self._phase_semantic_chunking()
        elif phase.name == "VectorEmbedding":
            return await self._phase_vector_embedding()
        elif phase.name == "Classification":
            return await self._phase_classification()
        elif phase.name == "EntityExtraction":
            return await self._phase_entity_extraction()
        elif phase.name == "KnowledgeGraph":
            return await self._phase_knowledge_graph()
        elif phase.name == "DocumentSynthesis":
            return await self._phase_document_synthesis()
        else:
            raise ValueError(f"Unknown phase: {phase.name}")

    async def _phase_semantic_chunking(self) -> Dict[str, Any]:
        """Phase 1: Semantic chunking with context preservation."""

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Reading chatlog file...", total=100)

            # Read chatlog content
            if not self.chatlog_path.exists():
                raise FileNotFoundError(f"Chatlog file not found: {self.chatlog_path}")

            with open(self.chatlog_path, 'r', encoding='utf-8') as f:
                content = f.read()

            progress.update(task, advance=30, description="Detecting format...")

            # Detect format (simplified version)
            format_type = "colon_separated"  # Could be enhanced with format detection
            if '[' in content and ']' in content and ':' in content:
                format_type = "timestamp_separated"

            progress.update(task, advance=30, description="Creating semantic chunks...")

            # Create chunks using our semantic chunker
            self.conversation_chunks = self.semantic_chunker.chunk_from_text(
                content,
                format_type=format_type,
                show_progress=False
            )

            progress.update(task, advance=40, description="Saving chunk data...")

            # Save chunk data
            chunks_file = self.output_dir / "chunks.json"
            chunks_data = [asdict(chunk) for chunk in self.conversation_chunks]
            with open(chunks_file, 'w') as f:
                json.dump(chunks_data, f, indent=2, default=str)

            # Generate analysis
            analysis = {
                "total_chunks": len(self.conversation_chunks),
                "chunk_types": {},
                "avg_tokens": 0,
                "participants": set(),
                "timestamp_range": None
            }

            for chunk in self.conversation_chunks:
                # Count chunk types
                chunk_type = chunk.chunk_type
                analysis["chunk_types"][chunk_type] = analysis["chunk_types"].get(chunk_type, 0) + 1

                # Collect participants
                analysis["participants"].update(chunk.participants)

                # Calculate average tokens
                analysis["avg_tokens"] += chunk.estimated_tokens

            analysis["avg_tokens"] /= len(self.conversation_chunks) if self.conversation_chunks else 1
            analysis["participants"] = list(analysis["participants"])

            # Save analysis
            analysis_file = self.output_dir / "chunk_analysis.json"
            with open(analysis_file, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)

        return {
            "chunks_created": len(self.conversation_chunks),
            "total_tokens": sum(chunk.estimated_tokens for chunk in self.conversation_chunks),
            "chunk_types": analysis["chunk_types"],
            "participants": analysis["participants"]
        }

    async def _phase_vector_embedding(self) -> Dict[str, Any]:
        """Phase 2: Generate vector embeddings using Voyage AI."""

        if not self.voyage_client:
            console.print("⚠️ Skipping vector embedding - Voyage AI not available")
            return {"status": "skipped", "reason": "Voyage AI not available"}

        # Prepare embedding requests
        embedding_requests = []
        for chunk in self.conversation_chunks:
            request = EmbeddingRequest(
                text=chunk.text_content,
                model=None,  # Auto-select based on length
                chunk_id=chunk.chunk_id,
                metadata={
                    "chunk_type": chunk.chunk_type,
                    "participants": chunk.participants,
                    "estimated_tokens": chunk.estimated_tokens
                }
            )
            embedding_requests.append(request)

        console.print(f"🚀 Embedding {len(embedding_requests)} chunks...")

        # Generate embeddings
        self.embeddings = await self.voyage_client.embed_batch(
            embedding_requests,
            show_progress=True
        )

        # Calculate cost
        cost_info = self.voyage_client.calculate_cost(self.embeddings)

        # Save embeddings
        embeddings_file = self.output_dir / "embeddings.json"
        embeddings_data = [asdict(emb) for emb in self.embeddings]
        with open(embeddings_file, 'w') as f:
            json.dump(embeddings_data, f, indent=2)

        # Generate similarity matrix for related chunks
        similarity_matrix = {}
        for i, emb1 in enumerate(self.embeddings):
            similarities = []
            for j, emb2 in enumerate(self.embeddings):
                if i != j:
                    sim = self.voyage_client.similarity(emb1.embedding, emb2.embedding)
                    similarities.append({
                        "chunk_id": emb2.chunk_id,
                        "similarity": sim
                    })

            # Sort by similarity and keep top 5
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            similarity_matrix[emb1.chunk_id] = similarities[:5]

        # Save similarity matrix
        similarity_file = self.output_dir / "similarity_matrix.json"
        with open(similarity_file, 'w') as f:
            json.dump(similarity_matrix, f, indent=2)

        return {
            "embeddings_created": len(self.embeddings),
            "total_cost_usd": cost_info["total_cost_usd"],
            "total_tokens": cost_info["total_tokens"],
            "models_used": list(cost_info["breakdown"].keys())
        }

    async def _phase_classification(self) -> Dict[str, Any]:
        """Phase 3: Multi-label classification of content."""

        console.print("🏷️ Classifying conversation content...")

        # Simple rule-based classification (could be enhanced with ML models)
        self.classifications = []

        for chunk in self.conversation_chunks:
            content = chunk.text_content.lower()

            # Classify content type
            content_type = "discussion"
            if any(word in content for word in ["decided", "conclusion", "agreed"]):
                content_type = "decision"
            elif any(word in content for word in ["user", "feature", "requirement"]):
                content_type = "feature"
            elif any(word in content for word in ["bug", "issue", "problem", "error"]):
                content_type = "bug"
            elif "?" in content:
                content_type = "question"
            elif any(word in content for word in ["implement", "code", "develop"]):
                content_type = "implementation"

            # Classify domain
            domain = "general"
            if any(word in content for word in ["ui", "frontend", "interface", "design"]):
                domain = "frontend"
            elif any(word in content for word in ["api", "server", "backend", "service"]):
                domain = "backend"
            elif any(word in content for word in ["database", "sql", "data", "schema"]):
                domain = "database"
            elif any(word in content for word in ["infrastructure", "deployment", "cloud"]):
                domain = "infrastructure"
            elif any(word in content for word in ["business", "revenue", "customer", "market"]):
                domain = "business"

            # Classify priority based on urgency indicators
            priority = "P2"  # Medium default
            if any(word in content for word in ["urgent", "critical", "asap", "immediately"]):
                priority = "P0"
            elif any(word in content for word in ["important", "high priority", "soon"]):
                priority = "P1"
            elif any(word in content for word in ["later", "nice to have", "future"]):
                priority = "P3"

            # Classify status
            status = "proposed"
            if any(word in content for word in ["approved", "agreed", "decided"]):
                status = "approved"
            elif any(word in content for word in ["working on", "in progress", "implementing"]):
                status = "in_progress"
            elif any(word in content for word in ["completed", "done", "finished"]):
                status = "completed"

            classification = ClassificationResult(
                chunk_id=chunk.chunk_id,
                content_type=content_type,
                domain=domain,
                priority=priority,
                status=status,
                confidence=0.7  # Fixed confidence for rule-based system
            )

            self.classifications.append(classification)

        # Save classifications
        classifications_file = self.output_dir / "classifications.json"
        classifications_data = [asdict(cls) for cls in self.classifications]
        with open(classifications_file, 'w') as f:
            json.dump(classifications_data, f, indent=2)

        # Generate classification report
        report = {
            "content_types": {},
            "domains": {},
            "priorities": {},
            "statuses": {}
        }

        for cls in self.classifications:
            report["content_types"][cls.content_type] = report["content_types"].get(cls.content_type, 0) + 1
            report["domains"][cls.domain] = report["domains"].get(cls.domain, 0) + 1
            report["priorities"][cls.priority] = report["priorities"].get(cls.priority, 0) + 1
            report["statuses"][cls.status] = report["statuses"].get(cls.status, 0) + 1

        report_file = self.output_dir / "classification_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        return {
            "chunks_classified": len(self.classifications),
            "content_type_distribution": report["content_types"],
            "domain_distribution": report["domains"]
        }

    async def _phase_entity_extraction(self) -> Dict[str, Any]:
        """Phase 4: Extract entities, patterns, and relationships."""

        console.print("🔍 Extracting entities and patterns...")

        self.entities = []
        extracted_patterns = []
        extracted_decisions = []

        for chunk in self.conversation_chunks:
            content = chunk.text_content

            # Extract people (speakers are people)
            for participant in chunk.participants:
                entity = ExtractedEntity(
                    entity_id=f"person_{hashlib.sha256(participant.encode()).hexdigest()[:8]}",
                    entity_type="person",
                    text=participant,
                    context=f"Participant in conversation (chunk {chunk.chunk_id})",
                    confidence=1.0,
                    metadata={"role": "participant"}
                )
                self.entities.append(entity)

            # Extract products/components mentioned
            import re
            product_patterns = [
                r'\b([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*)\s+(?:system|service|API|component|platform)\b',
                r'\b(?:the|our|this)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)\s+(?:feature|module|system)\b'
            ]

            for pattern in product_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    product_name = match.group(1).strip()
                    if len(product_name) > 2:  # Filter out short matches
                        entity = ExtractedEntity(
                            entity_id=f"product_{hashlib.sha256(product_name.lower().encode()).hexdigest()[:8]}",
                            entity_type="product",
                            text=product_name,
                            context=f"Mentioned in chunk {chunk.chunk_id}",
                            confidence=0.8
                        )
                        self.entities.append(entity)

            # Extract decisions
            decision_patterns = [
                r'(?:we\s+)?(?:decided|agreed|concluded)\s+(?:to\s+)?([^.!?]+)[.!?]',
                r'(?:the\s+)?(?:decision|conclusion)\s+is\s+([^.!?]+)[.!?]',
                r'(?:let\'s|we should)\s+([^.!?]+)[.!?]'
            ]

            for pattern in decision_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    decision_text = match.group(1).strip()
                    decision = {
                        "decision_id": hashlib.sha256(decision_text.encode()).hexdigest()[:12],
                        "text": decision_text,
                        "context": f"From chunk {chunk.chunk_id}",
                        "participants": chunk.participants,
                        "timestamp": chunk.start_timestamp.isoformat() if chunk.start_timestamp else None
                    }
                    extracted_decisions.append(decision)

        # Remove duplicate entities
        unique_entities = {}
        for entity in self.entities:
            key = f"{entity.entity_type}:{entity.text.lower()}"
            if key not in unique_entities:
                unique_entities[key] = entity

        self.entities = list(unique_entities.values())

        # Save entities
        entities_file = self.output_dir / "entities.json"
        entities_data = [asdict(entity) for entity in self.entities]
        with open(entities_file, 'w') as f:
            json.dump(entities_data, f, indent=2)

        # Save patterns (placeholder for now)
        patterns_file = self.output_dir / "patterns.json"
        with open(patterns_file, 'w') as f:
            json.dump(extracted_patterns, f, indent=2)

        # Save decisions
        decisions_file = self.output_dir / "decisions.json"
        with open(decisions_file, 'w') as f:
            json.dump(extracted_decisions, f, indent=2)

        return {
            "entities_extracted": len(self.entities),
            "entity_types": list(set(e.entity_type for e in self.entities)),
            "decisions_found": len(extracted_decisions)
        }

    async def _phase_knowledge_graph(self) -> Dict[str, Any]:
        """Phase 5: Build knowledge graph with relationships."""

        console.print("🕸️ Building knowledge graph...")

        # Build simple knowledge graph structure
        nodes = []
        edges = []

        # Add entity nodes
        for entity in self.entities:
            nodes.append({
                "id": entity.entity_id,
                "type": entity.entity_type,
                "label": entity.text,
                "confidence": entity.confidence,
                "metadata": entity.metadata or {}
            })

        # Add chunk nodes
        for chunk in self.conversation_chunks:
            nodes.append({
                "id": chunk.chunk_id,
                "type": "conversation_chunk",
                "label": f"Chunk ({chunk.chunk_type})",
                "metadata": {
                    "participants": chunk.participants,
                    "tokens": chunk.estimated_tokens,
                    "timestamp": chunk.start_timestamp.isoformat() if chunk.start_timestamp else None
                }
            })

        # Create relationships
        # Entities mentioned in chunks
        for chunk in self.conversation_chunks:
            chunk_content = chunk.text_content.lower()
            for entity in self.entities:
                if entity.text.lower() in chunk_content:
                    edges.append({
                        "source": chunk.chunk_id,
                        "target": entity.entity_id,
                        "relationship": "mentions",
                        "confidence": 0.8
                    })

        # People participate in chunks
        for chunk in self.conversation_chunks:
            for participant in chunk.participants:
                person_entities = [e for e in self.entities if e.entity_type == "person" and e.text == participant]
                for person_entity in person_entities:
                    edges.append({
                        "source": person_entity.entity_id,
                        "target": chunk.chunk_id,
                        "relationship": "participates_in",
                        "confidence": 1.0
                    })

        self.knowledge_graph = {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
        }

        # Save knowledge graph
        kg_file = self.output_dir / "knowledge_graph.json"
        with open(kg_file, 'w') as f:
            json.dump(self.knowledge_graph, f, indent=2)

        # Save relationships summary
        relationships_file = self.output_dir / "relationships.json"
        relationship_summary = {
            "relationship_types": list(set(edge["relationship"] for edge in edges)),
            "node_types": list(set(node["type"] for node in nodes)),
            "statistics": {
                "nodes_by_type": {},
                "edges_by_type": {}
            }
        }

        # Calculate statistics
        for node in nodes:
            node_type = node["type"]
            relationship_summary["statistics"]["nodes_by_type"][node_type] = \
                relationship_summary["statistics"]["nodes_by_type"].get(node_type, 0) + 1

        for edge in edges:
            edge_type = edge["relationship"]
            relationship_summary["statistics"]["edges_by_type"][edge_type] = \
                relationship_summary["statistics"]["edges_by_type"].get(edge_type, 0) + 1

        with open(relationships_file, 'w') as f:
            json.dump(relationship_summary, f, indent=2)

        return {
            "nodes_created": len(nodes),
            "edges_created": len(edges),
            "relationship_types": relationship_summary["relationship_types"]
        }

    async def _phase_document_synthesis(self) -> Dict[str, Any]:
        """Phase 6: Generate formal documentation."""

        console.print("📝 Synthesizing formal documents...")

        generated_docs = []

        # Generate PRD if we have feature-related content
        feature_content = [c for c in self.classifications if c.content_type == "feature"]
        if feature_content:
            prd = self._generate_prd()
            prd_file = self.output_dir / "prd.md"
            with open(prd_file, 'w') as f:
                f.write(prd)
            generated_docs.append("PRD")

        # Generate ADR if we have decisions
        decision_content = [c for c in self.classifications if c.content_type == "decision"]
        if decision_content:
            adr = self._generate_adr()
            adr_file = self.output_dir / "adr.md"
            with open(adr_file, 'w') as f:
                f.write(adr)
            generated_docs.append("ADR")

        # Generate Design Spec if we have implementation content
        impl_content = [c for c in self.classifications if c.content_type == "implementation"]
        if impl_content:
            design_spec = self._generate_design_spec()
            spec_file = self.output_dir / "design_spec.md"
            with open(spec_file, 'w') as f:
                f.write(design_spec)
            generated_docs.append("Design Spec")

        # Generate synthesis report
        synthesis_report = {
            "documents_generated": generated_docs,
            "content_analysis": {
                "total_chunks": len(self.conversation_chunks),
                "classified_chunks": len(self.classifications),
                "entities_extracted": len(self.entities),
                "knowledge_graph_nodes": len(self.knowledge_graph.get("nodes", []))
            },
            "processing_summary": {
                "phases_completed": self.completed_phases,
                "total_processing_time": time.time() - self.total_start_time if self.total_start_time else 0
            }
        }

        report_file = self.output_dir / "synthesis_report.json"
        with open(report_file, 'w') as f:
            json.dump(synthesis_report, f, indent=2)

        return synthesis_report

    def _generate_prd(self) -> str:
        """Generate Product Requirements Document."""
        feature_chunks = [chunk for chunk, cls in zip(self.conversation_chunks, self.classifications)
                         if cls.content_type == "feature"]

        prd_content = f"""# Product Requirements Document

Generated from conversation analysis on {datetime.utcnow().strftime('%Y-%m-%d')}

## Overview

This document outlines product requirements extracted from team conversations.

## Goals

Based on the analyzed conversations, the following goals were identified:

"""

        for chunk in feature_chunks[:5]:  # Limit to top 5 feature chunks
            prd_content += f"- {chunk.text_content.split(':')[1].strip() if ':' in chunk.text_content else chunk.text_content[:100]}...\n"

        prd_content += """

## Requirements

### Functional Requirements

"""

        # Extract requirement-like statements
        for chunk in feature_chunks:
            content = chunk.text_content
            if "user" in content.lower() and ("can" in content.lower() or "should" in content.lower()):
                prd_content += f"- {content[:200]}...\n"

        prd_content += """

### Non-Functional Requirements

- Performance: Response times under 200ms
- Scalability: Support for concurrent users
- Security: Data protection and access control
- Usability: Intuitive user interface

## Success Metrics

- User engagement metrics
- Feature adoption rates
- Performance benchmarks
- User satisfaction scores

"""

        return prd_content

    def _generate_adr(self) -> str:
        """Generate Architecture Decision Record."""
        decision_chunks = [chunk for chunk, cls in zip(self.conversation_chunks, self.classifications)
                          if cls.content_type == "decision"]

        if not decision_chunks:
            return "# Architecture Decision Record\n\nNo architectural decisions found in the conversation."

        main_decision = decision_chunks[0]  # Take the first decision as main

        adr_content = f"""# Architecture Decision Record

**Status**: Accepted
**Date**: {datetime.utcnow().strftime('%Y-%m-%d')}
**Participants**: {', '.join(main_decision.participants)}

## Context

The following decision was made during team discussions:

{main_decision.text_content}

## Decision

Based on the conversation analysis, the team decided to proceed with the discussed approach.

## Consequences

### Positive
- Addresses the identified requirements
- Aligns with team expertise
- Supports scalability goals

### Negative
- May require additional resources
- Implementation complexity
- Potential maintenance overhead

## Alternatives Considered

Alternative approaches were discussed during the conversation but not selected.

"""

        return adr_content

    def _generate_design_spec(self) -> str:
        """Generate Technical Design Specification."""
        impl_chunks = [chunk for chunk, cls in zip(self.conversation_chunks, self.classifications)
                      if cls.content_type == "implementation"]

        design_spec = f"""# Technical Design Specification

Generated from conversation analysis on {datetime.utcnow().strftime('%Y-%m-%d')}

## Architecture Overview

Based on the analyzed conversations, the following technical design emerges:

"""

        # Add implementation details from chunks
        for chunk in impl_chunks[:3]:  # Limit to top 3 implementation chunks
            design_spec += f"""
### Component: {chunk.chunk_id}

**Participants**: {', '.join(chunk.participants)}

**Details**:
{chunk.text_content}

"""

        design_spec += """

## API Design

RESTful API endpoints for core functionality.

## Data Models

Entity relationships based on extracted knowledge graph.

## Security Considerations

- Authentication and authorization
- Data validation and sanitization
- Secure communication protocols

## Performance Requirements

- Response time targets
- Throughput requirements
- Scalability considerations

"""

        return design_spec

    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final report."""
        total_time = time.time() - self.total_start_time if self.total_start_time else 0

        return {
            "extraction_summary": {
                "total_processing_time": total_time,
                "phases_completed": self.completed_phases,
                "total_chunks": len(self.conversation_chunks),
                "total_entities": len(self.entities),
                "total_classifications": len(self.classifications)
            },
            "phase_results": self.phase_results,
            "output_directory": str(self.output_dir),
            "generated_files": list(self.output_dir.glob("*"))
        }

# CLI interface
async def main():
    """Command-line interface for the enhanced chatlog extractor."""
    parser = argparse.ArgumentParser(description="Enhanced Chatlog Extraction Pipeline")
    parser.add_argument("chatlog_path", help="Path to the chatlog file")
    parser.add_argument("--output-dir", default="./output", help="Output directory")
    parser.add_argument("--voyage-api-key", help="Voyage AI API key")
    parser.add_argument("--start-phase", default="SemanticChunking", help="Phase to start from")
    parser.add_argument("--auto-confirm", action="store_true", help="Skip user confirmations")

    args = parser.parse_args()

    # Initialize extractor
    extractor = EnhancedChatlogExtractor(
        chatlog_path=args.chatlog_path,
        output_dir=args.output_dir,
        voyage_api_key=args.voyage_api_key or os.getenv("VOYAGE_API_KEY")
    )

    # Run extraction
    try:
        results = await extractor.run_extraction(
            start_phase=args.start_phase,
            auto_confirm=args.auto_confirm
        )

        console.print(Panel(
            "✅ [bold green]Extraction Complete![/bold green]\n\n"
            f"📊 Total processing time: {results['extraction_summary']['total_processing_time']:.1f}s\n"
            f"🧩 Chunks created: {results['extraction_summary']['total_chunks']}\n"
            f"🏷️ Classifications: {results['extraction_summary']['total_classifications']}\n"
            f"🔍 Entities extracted: {results['extraction_summary']['total_entities']}\n"
            f"📁 Output directory: {results['output_directory']}",
            title="🎉 Enhanced Extraction Results",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"❌ Extraction failed: {e}")
        return 1

    return 0

if __name__ == "__main__":
    asyncio.run(main())