"""
Document Synthesizer - Advanced document synthesis and knowledge extraction

Transforms extracted entities into coherent summaries, reports, and knowledge graphs
optimized for ADHD-friendly consumption and strategic decision making.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter
from datetime import datetime
import re


@dataclass
class SynthesisConfig:
    """Configuration for document synthesis."""
    synthesis_type: str = "executive"  # executive, adhd, technical, comprehensive
    max_length: int = 1000
    confidence_threshold: float = 0.6
    enable_topic_clustering: bool = True
    enable_knowledge_graph: bool = True
    output_format: str = "markdown"  # markdown, json, html


@dataclass
class SynthesisResult:
    """Results from document synthesis."""
    config: SynthesisConfig
    success: bool
    processing_time: float

    # Synthesis outputs
    executive_summary: str = ""
    adhd_summary: str = ""
    technical_report: str = ""
    topic_clusters: Dict[str, List[Dict[str, Any]]] = None
    knowledge_graph: Dict[str, Any] = None

    # Metadata
    entity_count: int = 0
    document_count: int = 0
    confidence_stats: Dict[str, float] = None
    error_message: Optional[str] = None


class DocumentSynthesizer:
    """
    Advanced document synthesis engine.

    Transforms raw extraction results into coherent, actionable reports
    with ADHD accommodations and strategic insights.
    """

    def __init__(self, config: SynthesisConfig):
        """Initialize synthesizer with configuration."""
        self.config = config

        # Entity processing
        self.high_confidence_entities = []
        self.entity_clusters = defaultdict(list)
        self.topic_map = {}

        # Processing stats
        self.processing_start = None

    def synthesize_documents(self, extraction_results: Dict[str, Any]) -> SynthesisResult:
        """
        Synthesize documents from extraction results.

        Args:
            extraction_results: Merged extraction results from UnifiedDocumentExtractor

        Returns:
            Comprehensive synthesis results
        """
        import time
        self.processing_start = time.time()

        try:
            print("🧠 Starting document synthesis...")

            # Step 1: Filter and prepare entities
            self._prepare_entities(extraction_results)

            # Step 2: Generate topic clusters
            topic_clusters = {}
            if self.config.enable_topic_clustering:
                topic_clusters = self._generate_topic_clusters()

            # Step 3: Build knowledge graph
            knowledge_graph = {}
            if self.config.enable_knowledge_graph:
                knowledge_graph = self._build_knowledge_graph()

            # Step 4: Generate synthesis outputs
            executive_summary = ""
            adhd_summary = ""
            technical_report = ""

            if self.config.synthesis_type in ["executive", "comprehensive"]:
                executive_summary = self._generate_executive_summary(topic_clusters)

            if self.config.synthesis_type in ["adhd", "comprehensive"]:
                adhd_summary = self._generate_adhd_summary(topic_clusters)

            if self.config.synthesis_type in ["technical", "comprehensive"]:
                technical_report = self._generate_technical_report(extraction_results)

            # Step 5: Calculate statistics
            confidence_stats = self._calculate_confidence_stats()

            processing_time = time.time() - self.processing_start
            print(f"✅ Synthesis complete! ({processing_time:.2f}s)")

            return SynthesisResult(
                config=self.config,
                success=True,
                processing_time=processing_time,
                executive_summary=executive_summary,
                adhd_summary=adhd_summary,
                technical_report=technical_report,
                topic_clusters=topic_clusters,
                knowledge_graph=knowledge_graph,
                entity_count=len(self.high_confidence_entities),
                document_count=extraction_results.get('summary', {}).get('total_documents', 0),
                confidence_stats=confidence_stats
            )

        except Exception as e:
            processing_time = time.time() - self.processing_start if self.processing_start else 0
            print(f"❌ Synthesis failed: {e}")

            return SynthesisResult(
                config=self.config,
                success=False,
                processing_time=processing_time,
                error_message=str(e)
            )

    def _prepare_entities(self, extraction_results: Dict[str, Any]):
        """Filter entities by confidence and prepare for synthesis."""
        self.high_confidence_entities = []

        # Process all entity layers
        all_entities = extraction_results.get('all_entities', {})

        for layer in ['basic', 'adhd', 'multi_angle']:
            layer_entities = all_entities.get(layer, {})

            for entity_type, entity_list in layer_entities.items():
                for entity in entity_list:
                    confidence = entity.get('confidence', 0.0)

                    if confidence >= self.config.confidence_threshold:
                        # Enhance entity with metadata
                        enhanced_entity = {
                            **entity,
                            'layer': layer,
                            'entity_type': entity_type,
                            'synthesis_score': self._calculate_synthesis_score(entity)
                        }
                        self.high_confidence_entities.append(enhanced_entity)

        print(f"📊 Prepared {len(self.high_confidence_entities)} high-confidence entities")

    def _calculate_synthesis_score(self, entity: Dict[str, Any]) -> float:
        """Calculate synthesis importance score for entity."""
        score = entity.get('confidence', 0.0)

        # Boost score for ADHD-related entities
        content = entity.get('content', '').lower()
        if any(keyword in content for keyword in ['adhd', 'focus', 'attention', 'break']):
            score += 0.2

        # Boost for configuration entities
        if entity.get('type') in ['configuration_section', 'configuration_value']:
            score += 0.1

        # Boost for entities with values
        if entity.get('value'):
            score += 0.1

        return min(score, 1.0)

    def _generate_topic_clusters(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group entities into topic clusters for better organization."""
        clusters = defaultdict(list)

        # Define topic keywords
        topic_keywords = {
            'ADHD Configuration': ['adhd', 'focus', 'attention', 'break', 'cognitive'],
            'System Settings': ['config', 'setting', 'parameter', 'option'],
            'Project Metadata': ['project', 'name', 'description', 'version'],
            'Documentation': ['doc', 'readme', 'guide', 'manual'],
            'Development': ['dev', 'develop', 'code', 'build', 'test'],
            'Architecture': ['architecture', 'system', 'component', 'module'],
            'User Interface': ['ui', 'interface', 'screen', 'view', 'layout']
        }

        # Classify entities into topics
        for entity in self.high_confidence_entities:
            content = entity.get('content', '').lower()
            entity_type = entity.get('entity_type', '').lower()
            combined_text = f"{content} {entity_type}"

            assigned = False
            for topic, keywords in topic_keywords.items():
                if any(keyword in combined_text for keyword in keywords):
                    clusters[topic].append(entity)
                    assigned = True
                    break

            # Default cluster for unclassified entities
            if not assigned:
                clusters['Other'].append(entity)

        # Sort clusters by entity count and synthesis scores
        sorted_clusters = {}
        for topic, entities in clusters.items():
            if entities:  # Only include non-empty clusters
                # Sort entities by synthesis score
                sorted_entities = sorted(entities, key=lambda e: e.get('synthesis_score', 0), reverse=True)
                sorted_clusters[topic] = sorted_entities

        print(f"🏷️ Generated {len(sorted_clusters)} topic clusters")
        return dict(sorted_clusters)

    def _build_knowledge_graph(self) -> Dict[str, Any]:
        """Build knowledge graph from entity relationships."""
        graph = {
            'nodes': [],
            'edges': [],
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'entity_count': len(self.high_confidence_entities),
                'relationship_count': 0
            }
        }

        # Create nodes
        for i, entity in enumerate(self.high_confidence_entities):
            node = {
                'id': f"entity_{i}",
                'label': entity.get('content', 'Unknown'),
                'type': entity.get('entity_type', 'unknown'),
                'layer': entity.get('layer', 'unknown'),
                'confidence': entity.get('confidence', 0.0),
                'synthesis_score': entity.get('synthesis_score', 0.0),
                'source_file': entity.get('source_file', '')
            }
            graph['nodes'].append(node)

        # Create edges based on relationships
        relationship_count = 0

        # File-based relationships
        file_entities = defaultdict(list)
        for i, entity in enumerate(self.high_confidence_entities):
            source_file = entity.get('source_file', '')
            if source_file:
                file_entities[source_file].append(f"entity_{i}")

        # Connect entities from same file
        for source_file, entity_ids in file_entities.items():
            for i in range(len(entity_ids)):
                for j in range(i + 1, len(entity_ids)):
                    edge = {
                        'source': entity_ids[i],
                        'target': entity_ids[j],
                        'type': 'same_document',
                        'strength': 0.5
                    }
                    graph['edges'].append(edge)
                    relationship_count += 1

        # ADHD-focused relationships
        adhd_entities = [f"entity_{i}" for i, entity in enumerate(self.high_confidence_entities)
                        if 'adhd' in entity.get('content', '').lower()]

        # Connect ADHD entities with higher strength
        for i in range(len(adhd_entities)):
            for j in range(i + 1, len(adhd_entities)):
                edge = {
                    'source': adhd_entities[i],
                    'target': adhd_entities[j],
                    'type': 'adhd_related',
                    'strength': 0.8
                }
                graph['edges'].append(edge)
                relationship_count += 1

        graph['metadata']['relationship_count'] = relationship_count
        print(f"🕸️ Built knowledge graph with {len(graph['nodes'])} nodes and {relationship_count} edges")

        return graph

    def _generate_executive_summary(self, topic_clusters: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate executive summary from clustered entities."""
        lines = ["# Executive Summary\n"]

        # Overview
        lines.append(f"**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**Documents Analyzed**: {len(set(e.get('source_file', '') for e in self.high_confidence_entities))}")
        lines.append(f"**High-Confidence Entities**: {len(self.high_confidence_entities)}\n")

        # Key findings by topic
        lines.append("## Key Findings\n")

        for topic, entities in list(topic_clusters.items())[:5]:  # Top 5 topics
            if not entities:
                continue

            lines.append(f"### {topic}")

            # Get top entities by synthesis score
            top_entities = sorted(entities, key=lambda e: e.get('synthesis_score', 0), reverse=True)[:3]

            for entity in top_entities:
                content = entity.get('content', 'N/A')
                value = entity.get('value', '')
                confidence = entity.get('confidence', 0.0)

                if value:
                    lines.append(f"- **{content}**: {value} _(confidence: {confidence:.2f})_")
                else:
                    lines.append(f"- **{content}** _(confidence: {confidence:.2f})_")

            lines.append("")

        # ADHD-specific insights
        adhd_entities = [e for e in self.high_confidence_entities
                        if 'adhd' in e.get('content', '').lower() or 'adhd' in e.get('entity_type', '').lower()]

        if adhd_entities:
            lines.append("## ADHD Accommodations Detected\n")

            for entity in adhd_entities[:5]:  # Top 5 ADHD entities
                content = entity.get('content', 'N/A')
                value = entity.get('value', '')

                if value:
                    lines.append(f"- {content}: {value}")
                else:
                    lines.append(f"- {content}")

            lines.append("")

        # Summary statistics
        lines.append("## Analysis Statistics\n")
        lines.append(f"- **Topic Clusters**: {len(topic_clusters)}")
        lines.append(f"- **ADHD Entities**: {len(adhd_entities)}")

        avg_confidence = sum(e.get('confidence', 0) for e in self.high_confidence_entities) / len(self.high_confidence_entities)
        lines.append(f"- **Average Confidence**: {avg_confidence:.2f}")

        return "\n".join(lines)

    def _generate_adhd_summary(self, topic_clusters: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate ADHD-optimized summary with chunked, visual format."""
        lines = ["# 🧠 ADHD-Optimized Summary\n"]

        # Quick stats at top
        lines.append("## 📊 Quick Stats")
        lines.append(f"- 📄 **Documents**: {len(set(e.get('source_file', '') for e in self.high_confidence_entities))}")
        lines.append(f"- 🎯 **Key Items**: {len(self.high_confidence_entities)}")
        lines.append(f"- 🏷️ **Topics**: {len(topic_clusters)}\n")

        # Visual progress indicators
        total_clusters = len(topic_clusters)
        if total_clusters > 0:
            lines.append("## 🎯 Key Areas")

            for i, (topic, entities) in enumerate(topic_clusters.items()):
                if i >= 5:  # Limit to top 5 for ADHD focus
                    break

                progress = "█" * min(len(entities), 5) + "░" * (5 - min(len(entities), 5))
                lines.append(f"### {topic} [{progress}] {len(entities)} items")

                # Show top 2 items per topic (chunked information)
                for entity in entities[:2]:
                    content = entity.get('content', 'N/A')
                    value = entity.get('value', '')
                    confidence = entity.get('confidence', 0.0)

                    # Use emojis and clear formatting
                    confidence_emoji = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"

                    if value:
                        lines.append(f"  {confidence_emoji} **{content}**: `{value}`")
                    else:
                        lines.append(f"  {confidence_emoji} **{content}**")

                lines.append("")

        # ADHD-specific accommodations
        adhd_entities = [e for e in self.high_confidence_entities
                        if any(keyword in e.get('content', '').lower()
                              for keyword in ['adhd', 'focus', 'attention', 'break', 'cognitive'])]

        if adhd_entities:
            lines.append("## 🎯 ADHD Accommodations")

            for entity in adhd_entities[:3]:  # Limit for focus
                content = entity.get('content', 'N/A')
                value = entity.get('value', '')
                confidence = entity.get('confidence', 0.0)

                confidence_emoji = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"

                if value:
                    lines.append(f"{confidence_emoji} **{content}**: `{value}`")
                else:
                    lines.append(f"{confidence_emoji} **{content}**")

            lines.append("")

        # Next actions (chunked decision support)
        lines.append("## ✅ Next Actions")
        lines.append("Based on the analysis, consider:")
        lines.append("1. 🔍 Review high-confidence findings")
        lines.append("2. ⚙️ Implement identified ADHD accommodations")
        lines.append("3. 📝 Update documentation with extracted insights")

        return "\n".join(lines)

    def _generate_technical_report(self, extraction_results: Dict[str, Any]) -> str:
        """Generate detailed technical report with confidence analysis."""
        lines = ["# Technical Analysis Report\n"]

        # Processing metadata
        summary = extraction_results.get('summary', {})
        lines.append("## Processing Summary")
        lines.append(f"- **Total Documents**: {summary.get('total_documents', 0)}")
        lines.append(f"- **Successful Extractions**: {summary.get('successful_extractions', 0)}")
        lines.append(f"- **Failed Extractions**: {summary.get('failed_extractions', 0)}")
        lines.append(f"- **Processing Time**: {summary.get('total_processing_time', 0):.2f}s")
        lines.append(f"- **Total Entities**: {summary.get('total_entities', 0)}")
        lines.append(f"- **High-Confidence Entities**: {len(self.high_confidence_entities)}\n")

        # Confidence analysis
        confidence_stats = self._calculate_confidence_stats()
        lines.append("## Confidence Analysis")
        lines.append(f"- **Average Confidence**: {confidence_stats.get('average', 0.0):.3f}")
        lines.append(f"- **Maximum Confidence**: {confidence_stats.get('max', 0.0):.3f}")
        lines.append(f"- **Minimum Confidence**: {confidence_stats.get('min', 0.0):.3f}")
        lines.append(f"- **Standard Deviation**: {confidence_stats.get('std_dev', 0.0):.3f}\n")

        # Entity breakdown by layer
        layer_breakdown = defaultdict(int)
        type_breakdown = defaultdict(int)

        for entity in self.high_confidence_entities:
            layer_breakdown[entity.get('layer', 'unknown')] += 1
            type_breakdown[entity.get('entity_type', 'unknown')] += 1

        lines.append("## Entity Distribution")
        lines.append("### By Extraction Layer")
        for layer, count in sorted(layer_breakdown.items()):
            percentage = (count / len(self.high_confidence_entities)) * 100
            lines.append(f"- **{layer}**: {count} entities ({percentage:.1f}%)")

        lines.append("\n### By Entity Type")
        for entity_type, count in sorted(type_breakdown.items(), key=lambda x: x[1], reverse=True)[:10]:
            percentage = (count / len(self.high_confidence_entities)) * 100
            lines.append(f"- **{entity_type}**: {count} entities ({percentage:.1f}%)")

        lines.append("")

        # Document analysis
        doc_types = extraction_results.get('document_types', {})
        if doc_types:
            lines.append("## Document Type Analysis")
            for doc_type, count in doc_types.items():
                lines.append(f"- **{doc_type}**: {count} documents")
            lines.append("")

        # Error analysis
        errors = extraction_results.get('errors', [])
        if errors:
            lines.append("## Error Analysis")
            lines.append(f"**Total Errors**: {len(errors)}\n")

            for i, error in enumerate(errors[:5]):  # Show first 5 errors
                lines.append(f"### Error {i+1}")
                lines.append(f"- **File**: {error.get('file', 'Unknown')}")
                lines.append(f"- **Error**: {error.get('error', 'Unknown')}")
                lines.append("")

        return "\n".join(lines)

    def _calculate_confidence_stats(self) -> Dict[str, float]:
        """Calculate confidence statistics for entities."""
        if not self.high_confidence_entities:
            return {}

        confidences = [entity.get('confidence', 0.0) for entity in self.high_confidence_entities]

        # Calculate basic stats
        avg_confidence = sum(confidences) / len(confidences)
        max_confidence = max(confidences)
        min_confidence = min(confidences)

        # Calculate standard deviation
        variance = sum((x - avg_confidence) ** 2 for x in confidences) / len(confidences)
        std_dev = variance ** 0.5

        return {
            'average': avg_confidence,
            'max': max_confidence,
            'min': min_confidence,
            'std_dev': std_dev,
            'count': len(confidences)
        }


def synthesize_documents(extraction_results: Dict[str, Any],
                        synthesis_type: str = "executive",
                        max_length: int = 1000,
                        confidence_threshold: float = 0.6) -> SynthesisResult:
    """
    Convenience function for document synthesis.

    Args:
        extraction_results: Results from UnifiedDocumentExtractor
        synthesis_type: Type of synthesis to generate
        max_length: Maximum length of synthesis outputs
        confidence_threshold: Minimum confidence for entity inclusion

    Returns:
        Synthesis results with generated summaries and insights
    """
    config = SynthesisConfig(
        synthesis_type=synthesis_type,
        max_length=max_length,
        confidence_threshold=confidence_threshold
    )

    synthesizer = DocumentSynthesizer(config)
    return synthesizer.synthesize_documents(extraction_results)