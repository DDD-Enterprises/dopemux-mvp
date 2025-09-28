"""Multi-pass enrichment pipeline using the sophisticated labels.yml taxonomy."""

import logging
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import time

from chatx.enrichment.ollama_client import OllamaClient
from chatx.redaction.policy_shield import PrivacyGate

logger = logging.getLogger(__name__)


class PassType(Enum):
    """Four enrichment passes for comprehensive labeling."""
    ENTITIES = "entities"        # Pass 1: Named entities, PII, basic patterns
    STRUCTURE = "structure"      # Pass 2: Speech acts, communication patterns
    PSYCHOLOGY = "psychology"    # Pass 3: Emotional/psychological analysis
    RELATIONSHIPS = "relationships"  # Pass 4: Interpersonal dynamics, temporal patterns


@dataclass
class PassConfig:
    """Configuration for each enrichment pass."""
    name: str
    enabled: bool = True
    local_model: str = "gemma2:9b-instruct-q4_K_M"
    cloud_model: str = "claude-3-sonnet-20240229"
    max_tokens: int = 800
    temperature: float = 0.1
    privacy_tier: str = "both"  # "local_only", "cloud_safe", or "both"
    batch_size: int = 20
    retry_attempts: int = 3
    
    # Pass-specific configurations
    entity_patterns: List[str] = field(default_factory=list)
    label_categories: List[str] = field(default_factory=list)
    dependency_passes: List[PassType] = field(default_factory=list)


@dataclass
class EnrichmentContext:
    """Context information for enrichment passes."""
    contact: str
    conversation_id: str
    chunk_window_size: int
    total_chunks: int
    privacy_tier: str
    
    # Cumulative context from previous passes
    entities_found: Set[str] = field(default_factory=set)
    labels_applied: Dict[str, int] = field(default_factory=dict)
    patterns_detected: List[str] = field(default_factory=list)
    relationship_insights: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PassResult:
    """Result from a single enrichment pass."""
    pass_type: PassType
    chunk_id: str
    labels_added: List[str]
    confidence: float
    processing_time_ms: int
    metadata: Dict[str, Any]
    privacy_violations: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)


class LabelTaxonomy:
    """Sophisticated label taxonomy loader and validator."""
    
    def __init__(self, taxonomy_file: Optional[Path] = None):
        """Initialize with labels.yml taxonomy."""
        if taxonomy_file is None:
            taxonomy_file = Path(__file__).parent.parent.parent / "config" / "labels.yml"
        
        self.taxonomy_file = taxonomy_file
        self.taxonomy = {}
        self.coarse_labels = set()
        self.fine_labels = set()
        self.synonyms = {}
        self.co_occurrence_rules = {}
        self.polarity_scores = {}
        self.load_taxonomy()
    
    def load_taxonomy(self) -> None:
        """Load the comprehensive labels taxonomy."""
        try:
            with open(self.taxonomy_file, 'r') as f:
                data = yaml.safe_load(f)
            
            self.taxonomy = data
            
            # Extract coarse and fine labels
            for category, category_data in data.get('categories', {}).items():
                if isinstance(category_data, dict):
                    # Coarse labels (cloud-safe)
                    coarse = category_data.get('coarse', [])
                    if isinstance(coarse, list):
                        self.coarse_labels.update(coarse)
                    
                    # Fine labels (local-only)
                    fine = category_data.get('fine', [])
                    if isinstance(fine, list):
                        self.fine_labels.update(fine)
            
            # Load synonyms
            synonyms_data = data.get('synonyms', {})
            for canonical, synonym_list in synonyms_data.items():
                for synonym in synonym_list:
                    self.synonyms[synonym] = canonical
            
            # Load co-occurrence rules
            self.co_occurrence_rules = data.get('co_occurrence_rules', {})
            
            # Load polarity scores
            self.polarity_scores = data.get('polarity_scores', {})
            
            logger.info(f"Loaded taxonomy: {len(self.coarse_labels)} coarse + {len(self.fine_labels)} fine labels")
            
        except Exception as e:
            logger.error(f"Failed to load taxonomy from {self.taxonomy_file}: {e}")
            # Fallback to basic labels
            self._load_fallback_taxonomy()
    
    def _load_fallback_taxonomy(self) -> None:
        """Load basic fallback taxonomy if main file fails."""
        self.coarse_labels = {
            "stress", "intimacy", "conflict", "support", "planning", "social",
            "work", "family", "health", "emotion", "communication", "time",
            "attention", "boundaries", "trust", "respect", "care", "growth"
        }
        
        self.fine_labels = {
            "sexuality", "substances", "mental_health_specific", "financial_details",
            "location_specific", "family_conflict", "relationship_issues",
            "personal_secrets", "vulnerability_specific", "trauma_indicators"
        }
        
        logger.warning("Using fallback taxonomy due to loading error")
    
    def normalize_label(self, label: str) -> str:
        """Normalize label using synonyms."""
        return self.synonyms.get(label.lower(), label.lower())
    
    def is_coarse_label(self, label: str) -> bool:
        """Check if label is coarse (cloud-safe)."""
        normalized = self.normalize_label(label)
        return normalized in self.coarse_labels
    
    def is_fine_label(self, label: str) -> bool:
        """Check if label is fine (local-only)."""
        normalized = self.normalize_label(label)
        return normalized in self.fine_labels
    
    def get_polarity_score(self, label: str) -> float:
        """Get polarity score for label (-1.0 to 1.0)."""
        normalized = self.normalize_label(label)
        return self.polarity_scores.get(normalized, 0.0)
    
    def apply_co_occurrence_rules(self, labels: List[str]) -> List[str]:
        """Apply co-occurrence rules to enhance labels."""
        enhanced_labels = set(labels)
        
        for rule_name, rule_config in self.co_occurrence_rules.items():
            required = set(rule_config.get('requires', []))
            implies = set(rule_config.get('implies', []))
            
            # Check if all required labels are present
            if required.issubset(set([self.normalize_label(label) for label in labels])):
                enhanced_labels.update(implies)
        
        return list(enhanced_labels)
    
    def validate_labels(self, labels: List[str]) -> Tuple[List[str], List[str]]:
        """Validate and separate coarse/fine labels."""
        coarse_valid = []
        fine_valid = []
        
        for label in labels:
            normalized = self.normalize_label(label)
            if self.is_coarse_label(normalized):
                coarse_valid.append(normalized)
            elif self.is_fine_label(normalized):
                fine_valid.append(normalized)
            else:
                logger.debug(f"Unknown label: {label}")
        
        return coarse_valid, fine_valid


class EntityExtractor:
    """Pass 1: Extract entities, patterns, and basic classifications."""
    
    def __init__(self, taxonomy: LabelTaxonomy):
        self.taxonomy = taxonomy
        
        # Basic entity patterns
        self.patterns = {
            'temporal': [
                r'\b(?:yesterday|today|tomorrow|weekend|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
                r'\b(?:morning|afternoon|evening|night|dawn|dusk)\b',
                r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b',
                r'\b\d{1,2}[:/]\d{1,2}(?:[:/]\d{2,4})?\b',  # dates
                r'\b\d{1,2}:\d{2}(?:\s?[ap]m)?\b'  # times
            ],
            'emotional': [
                r'\b(?:love|hate|angry|sad|happy|excited|worried|stressed|anxious|calm|peaceful)\b',
                r'\b(?:feeling|felt|emotions?|mood)\b',
                r'\b(?:cry|crying|laugh|laughing|smile|smiling|frown|frowning)\b'
            ],
            'relationship': [
                r'\b(?:we|us|our|together|relationship|partner|couple|dating|married)\b',
                r'\b(?:family|parents?|mother|father|mom|dad|sister|brother|sibling)\b',
                r'\b(?:friend|friendship|buddy|pal|bestie|bff)\b'
            ],
            'conflict': [
                r'\b(?:fight|fighting|argue|argument|disagree|conflict|issue|problem)\b',
                r'\b(?:upset|frustrated|annoyed|irritated|bothered|mad)\b',
                r'\b(?:sorry|apologize|mistake|wrong|fault|blame)\b'
            ],
            'support': [
                r'\b(?:help|helping|support|care|caring|comfort|reassure)\b',
                r'\b(?:understanding|listen|hear|acknowledge|validate)\b',
                r'\b(?:there for|here for|count on|rely on|depend on)\b'
            ]
        }
    
    def extract_entities(self, text: str, context: EnrichmentContext) -> PassResult:
        """Extract entities and apply basic pattern-based labels."""
        start_time = time.time()
        labels_added = []
        metadata = {}
        
        # Pattern matching for quick classification
        for category, patterns in self.patterns.items():
            category_matches = 0
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                category_matches += len(matches)
                if matches:
                    context.entities_found.update(matches)
            
            if category_matches > 0:
                labels_added.append(category)
                metadata[f"{category}_count"] = category_matches
        
        # Apply taxonomy normalization
        normalized_labels = []
        for label in labels_added:
            normalized = self.taxonomy.normalize_label(label)
            if normalized:
                normalized_labels.append(normalized)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return PassResult(
            pass_type=PassType.ENTITIES,
            chunk_id="",  # Will be set by caller
            labels_added=normalized_labels,
            confidence=0.8,  # High confidence for pattern matching
            processing_time_ms=processing_time,
            metadata=metadata
        )


class StructuralAnalyzer:
    """Pass 2: Analyze communication structure and speech acts."""
    
    def __init__(self, taxonomy: LabelTaxonomy, llm_client: OllamaClient):
        self.taxonomy = taxonomy
        self.llm_client = llm_client
    
    def analyze_structure(self, text: str, context: EnrichmentContext, entities_result: PassResult) -> PassResult:
        """Analyze communication patterns and speech acts."""
        start_time = time.time()
        
        # Build prompt with entity context
        entities_context = ", ".join(entities_result.labels_added) if entities_result.labels_added else "none"
        
        prompt = f"""Analyze the communication structure and speech acts in this conversation chunk.

Detected entities from Pass 1: {entities_context}

Text to analyze:
"{text}"

Identify speech acts and communication patterns. Choose from these structural labels:
- informing, requesting, questioning, suggesting, agreeing, disagreeing
- apologizing, thanking, complaining, praising, criticizing
- boundary_setting, boundary_testing, boundary_crossing
- turn_taking, interrupting, topic_shifting, topic_maintaining
- direct_communication, indirect_communication, passive_aggressive

Response format:
{{
    "speech_acts": ["label1", "label2"],
    "communication_style": "direct|indirect|mixed",
    "turn_pattern": "initiating|responding|maintaining|closing",
    "boundary_signals": ["none|setting|testing|crossing"],
    "confidence": 0.0-1.0
}}"""

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                max_tokens=300,
                temperature=0.1
            )
            
            # Parse JSON response
            result_data = json.loads(response.strip())
            
            labels_added = []
            labels_added.extend(result_data.get("speech_acts", []))
            
            communication_style = result_data.get("communication_style", "")
            if communication_style:
                labels_added.append(f"communication_{communication_style}")
            
            turn_pattern = result_data.get("turn_pattern", "")
            if turn_pattern:
                labels_added.append(f"turn_{turn_pattern}")
            
            boundary_signals = result_data.get("boundary_signals", [])
            for signal in boundary_signals:
                if signal != "none":
                    labels_added.append(f"boundary_{signal}")
            
            confidence = result_data.get("confidence", 0.7)
            
            # Normalize labels using taxonomy
            normalized_labels = []
            for label in labels_added:
                normalized = self.taxonomy.normalize_label(label)
                if normalized:
                    normalized_labels.append(normalized)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return PassResult(
                pass_type=PassType.STRUCTURE,
                chunk_id="",
                labels_added=normalized_labels,
                confidence=confidence,
                processing_time_ms=processing_time,
                metadata=result_data
            )
            
        except Exception as e:
            logger.error(f"Structural analysis failed: {e}")
            processing_time = int((time.time() - start_time) * 1000)
            
            return PassResult(
                pass_type=PassType.STRUCTURE,
                chunk_id="",
                labels_added=[],
                confidence=0.0,
                processing_time_ms=processing_time,
                metadata={},
                validation_errors=[f"LLM parsing error: {str(e)}"]
            )


class PsychologyAnalyzer:
    """Pass 3: Deep psychological and emotional analysis."""
    
    def __init__(self, taxonomy: LabelTaxonomy, llm_client: OllamaClient):
        self.taxonomy = taxonomy
        self.llm_client = llm_client
    
    def analyze_psychology(
        self, 
        text: str, 
        context: EnrichmentContext, 
        previous_results: List[PassResult]
    ) -> PassResult:
        """Perform deep psychological analysis."""
        start_time = time.time()
        
        # Build context from previous passes
        all_previous_labels = []
        for result in previous_results:
            all_previous_labels.extend(result.labels_added)
        
        previous_context = ", ".join(all_previous_labels) if all_previous_labels else "none"
        
        # Use sophisticated prompt for psychological analysis
        prompt = f"""Perform deep psychological analysis of this conversation chunk using advanced psychological frameworks.

Previous analysis labels: {previous_context}

Text to analyze:
"{text}"

Analyze using these psychological dimensions:

EMOTIONAL STATE:
- Primary emotions: joy, sadness, anger, fear, surprise, disgust, neutral
- Emotional regulation: regulated, dysregulated, suppressed, escalating
- Emotional expression: direct, indirect, masked, amplified

ATTACHMENT & INTIMACY:
- Attachment signals: secure, anxious, avoidant, disorganized
- Intimacy level: surface, moderate, deep, vulnerable
- Connection quality: connected, disconnected, ambivalent, seeking

PSYCHOLOGICAL NEEDS:
- Autonomy: respected, challenged, controlled, supported
- Competence: validated, questioned, supported, undermined  
- Relatedness: fulfilled, starved, ambivalent, satisfied

DEFENSE MECHANISMS:
- Projection, displacement, rationalization, denial, sublimation
- Healthy coping vs. maladaptive patterns

RELATIONAL DYNAMICS:
- Power balance: equal, imbalanced, shifting, contested
- Influence patterns: mutual, one-sided, manipulative, supportive
- Boundary health: clear, blurred, violated, rigid

Choose labels from psychology taxonomy. Separate coarse (cloud-safe) from fine (local-only).

Response format:
{{
    "coarse_labels": ["stress", "intimacy", "conflict", "support", "communication"],
    "fine_labels_local": ["anxiety_specific", "trauma_indicator", "substance_reference"],
    "emotional_state": "primary_emotion:confidence_score",
    "attachment_style": "secure|anxious|avoidant|disorganized",
    "intimacy_level": 1-5,
    "psychological_needs": {{"autonomy": -1_to_1, "competence": -1_to_1, "relatedness": -1_to_1}},
    "defense_mechanisms": ["mechanism1", "mechanism2"],
    "relational_power": -1_to_1,
    "confidence": 0.0-1.0
}}"""

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                max_tokens=500,
                temperature=0.15  # Slightly higher for nuanced psychological analysis
            )
            
            # Parse JSON response
            result_data = json.loads(response.strip())
            
            # Extract labels with privacy awareness
            coarse_labels = result_data.get("coarse_labels", [])
            fine_labels = result_data.get("fine_labels_local", [])
            
            # Validate labels against taxonomy
            coarse_valid, fine_valid = self.taxonomy.validate_labels(coarse_labels + fine_labels)
            
            # Apply co-occurrence rules for label enhancement
            all_labels = coarse_valid + fine_valid
            enhanced_labels = self.taxonomy.apply_co_occurrence_rules(all_labels)
            
            # Separate enhanced labels back into coarse/fine
            coarse_final, fine_final = self.taxonomy.validate_labels(enhanced_labels)
            
            confidence = result_data.get("confidence", 0.75)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Build comprehensive metadata
            metadata = result_data.copy()
            metadata["coarse_labels"] = coarse_final
            metadata["fine_labels_local"] = fine_final
            metadata["labels_enhanced"] = len(enhanced_labels) > len(all_labels)
            
            return PassResult(
                pass_type=PassType.PSYCHOLOGY,
                chunk_id="",
                labels_added=enhanced_labels,
                confidence=confidence,
                processing_time_ms=processing_time,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Psychology analysis failed: {e}")
            processing_time = int((time.time() - start_time) * 1000)
            
            return PassResult(
                pass_type=PassType.PSYCHOLOGY,
                chunk_id="",
                labels_added=[],
                confidence=0.0,
                processing_time_ms=processing_time,
                metadata={},
                validation_errors=[f"LLM parsing error: {str(e)}"]
            )


class RelationshipAnalyzer:
    """Pass 4: Analyze interpersonal dynamics and temporal patterns."""
    
    def __init__(self, taxonomy: LabelTaxonomy, llm_client: OllamaClient):
        self.taxonomy = taxonomy
        self.llm_client = llm_client
    
    def analyze_relationships(
        self,
        text: str,
        context: EnrichmentContext,
        previous_results: List[PassResult],
        chunk_history: Optional[List[Dict[str, Any]]] = None
    ) -> PassResult:
        """Analyze relationship dynamics and temporal patterns."""
        start_time = time.time()
        
        # Aggregate insights from previous passes
        psychology_labels = []
        structural_labels = []
        entity_labels = []
        
        for result in previous_results:
            if result.pass_type == PassType.PSYCHOLOGY:
                psychology_labels.extend(result.labels_added)
            elif result.pass_type == PassType.STRUCTURE:
                structural_labels.extend(result.labels_added)
            elif result.pass_type == PassType.ENTITIES:
                entity_labels.extend(result.labels_added)
        
        # Build temporal context if available
        temporal_context = "No previous chunks available"
        if chunk_history:
            recent_chunks = chunk_history[-3:]  # Last 3 chunks for context
            temporal_context = f"Recent conversation flow: {len(recent_chunks)} previous chunks analyzed"
        
        prompt = f"""Analyze interpersonal relationship dynamics and temporal patterns in this conversation.

CONTEXT FROM PREVIOUS PASSES:
- Entities/Patterns: {', '.join(entity_labels) if entity_labels else 'none'}
- Communication Structure: {', '.join(structural_labels) if structural_labels else 'none'}  
- Psychology: {', '.join(psychology_labels) if psychology_labels else 'none'}

TEMPORAL CONTEXT: {temporal_context}

TEXT TO ANALYZE:
"{text}"

RELATIONSHIP ANALYSIS FRAMEWORK:

INTERPERSONAL DYNAMICS:
- Relationship stage: forming, storming, norming, performing, mourning
- Interaction quality: harmonious, tense, neutral, improving, deteriorating
- Mutual influence: balanced, imbalanced, collaborative, competitive
- Trust indicators: building, stable, eroding, absent
- Conflict style: constructive, destructive, avoidant, accommodating

TEMPORAL PATTERNS:
- Conversation flow: natural, forced, interrupted, resumed
- Response patterns: immediate, delayed, consistent, erratic  
- Topic progression: linear, circular, tangential, focused
- Emotional trajectory: escalating, de-escalating, stable, volatile

LONGITUDINAL INDICATORS:
- Relationship progression: deepening, maintaining, distancing, cycling
- Pattern recognition: recurring themes, behavioral cycles, trigger points
- Growth indicators: learning, adapting, stuck, regressing

ATTACHMENT THEORY INTEGRATION:
- Secure base behaviors: providing/seeking comfort, support, understanding
- Proximity seeking: closeness, distance, ambivalence, approach-avoidance
- Safe haven responses: turning toward/away during stress

Response format:
{{
    "relationship_stage": "forming|storming|norming|performing|mourning",
    "interaction_quality": "harmonious|tense|neutral|improving|deteriorating", 
    "trust_level": 1-5,
    "conflict_style": "constructive|destructive|avoidant|accommodating",
    "temporal_flow": "natural|forced|interrupted|resumed",
    "emotional_trajectory": "escalating|de_escalating|stable|volatile",
    "attachment_behaviors": ["secure_base", "proximity_seeking", "safe_haven"],
    "longitudinal_labels": ["deepening", "pattern_recurring", "growth_indicator"],
    "relationship_labels": ["trust_building", "conflict_constructive", "intimacy_deepening"],
    "confidence": 0.0-1.0
}}"""

        try:
            response = self.llm_client.generate(
                prompt=prompt,
                max_tokens=400,
                temperature=0.2  # Balanced for nuanced relationship analysis
            )
            
            # Parse JSON response
            result_data = json.loads(response.strip())
            
            # Collect relationship-specific labels
            labels_added = []
            
            # Core relationship dynamics
            relationship_stage = result_data.get("relationship_stage", "")
            if relationship_stage:
                labels_added.append(f"relationship_{relationship_stage}")
            
            interaction_quality = result_data.get("interaction_quality", "")
            if interaction_quality:
                labels_added.append(f"interaction_{interaction_quality}")
            
            conflict_style = result_data.get("conflict_style", "")
            if conflict_style:
                labels_added.append(f"conflict_{conflict_style}")
            
            temporal_flow = result_data.get("temporal_flow", "")
            if temporal_flow:
                labels_added.append(f"temporal_{temporal_flow}")
            
            emotional_trajectory = result_data.get("emotional_trajectory", "")
            if emotional_trajectory:
                labels_added.append(f"emotional_{emotional_trajectory}")
            
            # Attachment behaviors
            attachment_behaviors = result_data.get("attachment_behaviors", [])
            for behavior in attachment_behaviors:
                labels_added.append(f"attachment_{behavior}")
            
            # Longitudinal and relationship labels
            labels_added.extend(result_data.get("longitudinal_labels", []))
            labels_added.extend(result_data.get("relationship_labels", []))
            
            confidence = result_data.get("confidence", 0.7)
            
            # Normalize all labels using taxonomy
            normalized_labels = []
            for label in labels_added:
                normalized = self.taxonomy.normalize_label(label)
                if normalized:
                    normalized_labels.append(normalized)
            
            # Apply co-occurrence rules for relationship patterns
            enhanced_labels = self.taxonomy.apply_co_occurrence_rules(normalized_labels)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Build comprehensive relationship metadata
            metadata = result_data.copy()
            metadata["labels_enhanced"] = len(enhanced_labels) > len(normalized_labels)
            metadata["trust_level"] = result_data.get("trust_level", 3)
            metadata["relationship_progression"] = "analyzed"
            
            return PassResult(
                pass_type=PassType.RELATIONSHIPS,
                chunk_id="",
                labels_added=enhanced_labels,
                confidence=confidence,
                processing_time_ms=processing_time,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Relationship analysis failed: {e}")
            processing_time = int((time.time() - start_time) * 1000)
            
            return PassResult(
                pass_type=PassType.RELATIONSHIPS,
                chunk_id="",
                labels_added=[],
                confidence=0.0,
                processing_time_ms=processing_time,
                metadata={},
                validation_errors=[f"LLM parsing error: {str(e)}"]
            )


class MultiPassEnrichmentPipeline:
    """Orchestrates the 4-pass comprehensive enrichment pipeline."""
    
    def __init__(
        self,
        taxonomy_file: Optional[Path] = None,
        local_model: str = "gemma2:9b-instruct-q4_K_M",
        ollama_base_url: str = "http://localhost:11434"
    ):
        """Initialize the multi-pass pipeline."""
        self.taxonomy = LabelTaxonomy(taxonomy_file)
        self.privacy_gate = PrivacyGate()
        
        # Initialize LLM client
        self.llm_client = OllamaClient(
            base_url=ollama_base_url,
            model_name=local_model
        )
        
        # Initialize analyzers
        self.entity_extractor = EntityExtractor(self.taxonomy)
        self.structural_analyzer = StructuralAnalyzer(self.taxonomy, self.llm_client)
        self.psychology_analyzer = PsychologyAnalyzer(self.taxonomy, self.llm_client)
        self.relationship_analyzer = RelationshipAnalyzer(self.taxonomy, self.llm_client)
        
        logger.info("Multi-pass enrichment pipeline initialized")
    
    def enrich_chunk(
        self,
        chunk: Dict[str, Any],
        context: EnrichmentContext,
        chunk_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Run all 4 passes on a single chunk."""
        chunk_id = chunk.get("chunk_id", "unknown")
        text = chunk.get("text", "")
        
        if not text.strip():
            logger.warning(f"Empty text for chunk {chunk_id}")
            return chunk
        
        logger.debug(f"Starting 4-pass enrichment for chunk {chunk_id}")
        start_time = time.time()
        
        # Results storage
        pass_results = []
        all_labels = []
        all_metadata = {}
        privacy_violations = []
        
        try:
            # PASS 1: Entity Extraction
            logger.debug(f"Pass 1 (Entities) for chunk {chunk_id}")
            entities_result = self.entity_extractor.extract_entities(text, context)
            entities_result.chunk_id = chunk_id
            pass_results.append(entities_result)
            all_labels.extend(entities_result.labels_added)
            all_metadata["pass1_entities"] = entities_result.metadata
            
            # PASS 2: Structural Analysis
            logger.debug(f"Pass 2 (Structure) for chunk {chunk_id}")
            structure_result = self.structural_analyzer.analyze_structure(text, context, entities_result)
            structure_result.chunk_id = chunk_id
            pass_results.append(structure_result)
            all_labels.extend(structure_result.labels_added)
            all_metadata["pass2_structure"] = structure_result.metadata
            
            # PASS 3: Psychology Analysis
            logger.debug(f"Pass 3 (Psychology) for chunk {chunk_id}")
            psychology_result = self.psychology_analyzer.analyze_psychology(text, context, pass_results[:2])
            psychology_result.chunk_id = chunk_id
            pass_results.append(psychology_result)
            all_labels.extend(psychology_result.labels_added)
            all_metadata["pass3_psychology"] = psychology_result.metadata
            
            # PASS 4: Relationship Analysis
            logger.debug(f"Pass 4 (Relationships) for chunk {chunk_id}")
            relationship_result = self.relationship_analyzer.analyze_relationships(
                text, context, pass_results[:3], chunk_history
            )
            relationship_result.chunk_id = chunk_id
            pass_results.append(relationship_result)
            all_labels.extend(relationship_result.labels_added)
            all_metadata["pass4_relationships"] = relationship_result.metadata
            
            # Aggregate results and apply final enhancements
            final_labels = list(set(all_labels))  # Remove duplicates
            
            # Apply taxonomy co-occurrence rules one final time
            enhanced_labels = self.taxonomy.apply_co_occurrence_rules(final_labels)
            
            # Separate coarse and fine labels for privacy compliance
            coarse_labels, fine_labels = self.taxonomy.validate_labels(enhanced_labels)
            
            # Privacy validation
            if context.privacy_tier == "cloud_safe" and fine_labels:
                privacy_violations.append(f"Fine labels detected in cloud-safe context: {fine_labels}")
            
            # Update context with labels found
            context.labels_applied.update({label: context.labels_applied.get(label, 0) + 1 for label in enhanced_labels})
            
            # Calculate overall confidence (weighted average)
            total_confidence = sum(result.confidence for result in pass_results)
            avg_confidence = total_confidence / len(pass_results) if pass_results else 0.0
            
            # Build enriched chunk
            enriched_chunk = chunk.copy()
            
            # Update metadata with labels
            if "meta" not in enriched_chunk:
                enriched_chunk["meta"] = {}
            
            enriched_chunk["meta"]["labels_coarse"] = coarse_labels
            if context.privacy_tier != "cloud_safe":
                enriched_chunk["meta"]["labels_fine_local"] = fine_labels
            
            # Add enrichment metadata
            enriched_chunk["enrichment"] = {
                "pipeline_version": "multi_pass_v1",
                "passes_completed": [result.pass_type.value for result in pass_results],
                "overall_confidence": avg_confidence,
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "labels_count": len(enhanced_labels),
                "privacy_tier": context.privacy_tier,
                "privacy_violations": privacy_violations,
                "pass_details": all_metadata,
                "taxonomy_version": getattr(self.taxonomy, 'version', 'unknown'),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add provenance
            if "provenance" not in enriched_chunk:
                enriched_chunk["provenance"] = {}
            
            enriched_chunk["provenance"]["enrichment"] = {
                "method": "multi_pass_pipeline",
                "passes": len(pass_results),
                "model": self.llm_client.model_name,
                "confidence": avg_confidence
            }
            
            total_time = int((time.time() - start_time) * 1000)
            logger.debug(f"Completed 4-pass enrichment for chunk {chunk_id} in {total_time}ms")
            
            return enriched_chunk
            
        except Exception as e:
            logger.error(f"Multi-pass enrichment failed for chunk {chunk_id}: {e}")
            
            # Return original chunk with error metadata
            error_chunk = chunk.copy()
            if "enrichment" not in error_chunk:
                error_chunk["enrichment"] = {}
            
            error_chunk["enrichment"]["error"] = str(e)
            error_chunk["enrichment"]["passes_attempted"] = len(pass_results)
            error_chunk["enrichment"]["timestamp"] = datetime.now().isoformat()
            
            return error_chunk
    
    def enrich_chunks_batch(
        self,
        chunks: List[Dict[str, Any]],
        contact: str,
        batch_size: int = 20
    ) -> List[Dict[str, Any]]:
        """Enrich a batch of chunks with multi-pass pipeline."""
        logger.info(f"Starting multi-pass enrichment of {len(chunks)} chunks for contact {contact}")
        
        enriched_chunks = []
        context = EnrichmentContext(
            contact=contact,
            conversation_id=chunks[0].get("conv_id", "unknown") if chunks else "unknown",
            chunk_window_size=len(chunks),
            total_chunks=len(chunks),
            privacy_tier="local_only"  # Default to local-only for comprehensive labeling
        )
        
        # Process in batches to maintain context
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")
            
            batch_enriched = []
            for j, chunk in enumerate(batch):
                # Build chunk history for relationship analysis
                chunk_history = enriched_chunks[-5:] if enriched_chunks else None
                
                enriched_chunk = self.enrich_chunk(chunk, context, chunk_history)
                batch_enriched.append(enriched_chunk)
            
            enriched_chunks.extend(batch_enriched)
            
            # Update context with batch results
            batch_labels = []
            for enriched_chunk in batch_enriched:
                meta = enriched_chunk.get("meta", {})
                batch_labels.extend(meta.get("labels_coarse", []))
                batch_labels.extend(meta.get("labels_fine_local", []))
            
            # Update pattern detection
            unique_labels = set(batch_labels)
            for label in unique_labels:
                if context.labels_applied.get(label, 0) >= 3:  # Pattern threshold
                    pattern_name = f"recurring_{label}"
                    if pattern_name not in context.patterns_detected:
                        context.patterns_detected.append(pattern_name)
                        logger.debug(f"Detected recurring pattern: {label}")
        
        logger.info(f"Multi-pass enrichment complete: {len(enriched_chunks)} chunks processed")
        logger.info(f"Unique labels applied: {len(context.labels_applied)}")
        logger.info(f"Patterns detected: {len(context.patterns_detected)}")
        
        return enriched_chunks