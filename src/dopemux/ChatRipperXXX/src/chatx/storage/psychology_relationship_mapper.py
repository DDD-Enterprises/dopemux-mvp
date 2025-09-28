"""Psychology label to relationship mapping system for context-aware relationship detection.

This module provides sophisticated mapping between ChatX's 470+ psychology constructs
and the 47 relationship types, enabling context-aware relationship detection across
romantic, sexual, family, and friend relationships.
"""

import logging
from typing import List, Dict, Any, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .base import RelationshipTypes, PatternTypes

logger = logging.getLogger(__name__)


class RelationshipContext(Enum):
    """Relationship context types for context-aware mapping."""
    ROMANTIC = "romantic"
    SEXUAL = "sexual"
    FAMILY = "family"
    FRIEND = "friend"
    PROFESSIONAL = "professional"
    UNKNOWN = "unknown"


@dataclass
class RelationshipMapping:
    """Represents a mapping from psychology labels to relationship types."""
    source_labels: Set[str]          # Psychology labels that trigger this mapping
    target_relationship: str         # RelationshipTypes constant
    confidence: float                # Confidence score (0.0-1.0)
    context_weight: Dict[RelationshipContext, float]  # Context-specific weights
    required_sequence: bool = False  # Whether this requires temporal sequence
    exclusion_labels: Set[str] = None  # Labels that prevent this mapping
    
    def __post_init__(self):
        if self.exclusion_labels is None:
            self.exclusion_labels = set()


class PsychologyRelationshipMapper:
    """Maps psychology labels to relationship types with context awareness."""
    
    def __init__(self):
        """Initialize mapper with comprehensive label-to-relationship mappings."""
        self.mappings = self._build_comprehensive_mappings()
        self.context_detectors = self._build_context_detectors()
    
    def map_labels_to_relationships(self, 
                                  chunk1_labels: List[str], 
                                  chunk2_labels: List[str],
                                  relationship_context: RelationshipContext = RelationshipContext.UNKNOWN,
                                  temporal_sequence: bool = True) -> List[Tuple[str, float]]:
        """Map psychology labels between two chunks to relationship types.
        
        Args:
            chunk1_labels: Psychology labels from first chunk
            chunk2_labels: Psychology labels from second chunk  
            relationship_context: Relationship context (romantic, sexual, etc.)
            temporal_sequence: Whether chunks are in temporal sequence
            
        Returns:
            List of (relationship_type, confidence_score) tuples
        """
        labels1_set = set(chunk1_labels)
        labels2_set = set(chunk2_labels)
        combined_labels = labels1_set.union(labels2_set)
        
        detected_relationships = []
        
        for mapping in self.mappings:
            # Check if required labels are present
            if not mapping.source_labels.intersection(combined_labels):
                continue
                
            # Check exclusion labels
            if mapping.exclusion_labels.intersection(combined_labels):
                continue
                
            # Check sequence requirement
            if mapping.required_sequence and not temporal_sequence:
                continue
            
            # Calculate confidence score
            base_confidence = mapping.confidence
            context_multiplier = mapping.context_weight.get(relationship_context, 1.0)
            
            # Boost confidence if more labels match
            label_overlap_ratio = len(mapping.source_labels.intersection(combined_labels)) / len(mapping.source_labels)
            overlap_bonus = label_overlap_ratio * 0.2
            
            final_confidence = min(1.0, base_confidence * context_multiplier + overlap_bonus)
            
            if final_confidence > 0.3:  # Minimum confidence threshold
                detected_relationships.append((mapping.target_relationship, final_confidence))
        
        # Sort by confidence and return top relationships
        detected_relationships.sort(key=lambda x: x[1], reverse=True)
        return detected_relationships[:5]  # Return top 5 relationships
    
    def detect_relationship_context(self, chunk_labels: List[str]) -> RelationshipContext:
        """Detect the relationship context from psychology labels."""
        labels_set = set(chunk_labels)
        
        context_scores = {}
        for context, detector_labels in self.context_detectors.items():
            overlap = len(labels_set.intersection(detector_labels))
            if overlap > 0:
                context_scores[context] = overlap / len(detector_labels)
        
        if not context_scores:
            return RelationshipContext.UNKNOWN
            
        # Return context with highest score
        return max(context_scores.items(), key=lambda x: x[1])[0]
    
    def _build_comprehensive_mappings(self) -> List[RelationshipMapping]:
        """Build comprehensive mappings from psychology labels to relationships."""
        mappings = []
        
        # ═══════════════════════════════════════════════════════════════════
        # SEXUAL & INTIMATE RELATIONSHIP MAPPINGS
        # ═══════════════════════════════════════════════════════════════════
        
        # Sexual escalation patterns
        mappings.extend([
            RelationshipMapping(
                source_labels={"sexual_content", "arousal_anticipation", "sexual_negotiation"},
                target_relationship=RelationshipTypes.SEXUAL_ESCALATES,
                confidence=0.85,
                context_weight={
                    RelationshipContext.SEXUAL: 1.2,
                    RelationshipContext.ROMANTIC: 1.1,
                    RelationshipContext.PROFESSIONAL: 0.6
                }
            ),
            RelationshipMapping(
                source_labels={"sexual_rejection", "sexual_withdrawal", "intimacy_avoidance"},
                target_relationship=RelationshipTypes.SEXUAL_WITHDRAWS,
                confidence=0.82,
                context_weight={
                    RelationshipContext.SEXUAL: 1.15,
                    RelationshipContext.ROMANTIC: 1.05,
                    RelationshipContext.FAMILY: 0.3
                }
            ),
            RelationshipMapping(
                source_labels={"arousal_escalation", "sexual_tension", "desire_expression"},
                target_relationship=RelationshipTypes.AROUSAL_BUILDS,
                confidence=0.88,
                context_weight={
                    RelationshipContext.SEXUAL: 1.3,
                    RelationshipContext.ROMANTIC: 1.2,
                    RelationshipContext.PROFESSIONAL: 0.4
                }
            ),
            RelationshipMapping(
                source_labels={"arousal_deflation", "sexual_disappointment", "desire_unfulfilled"},
                target_relationship=RelationshipTypes.AROUSAL_DEFLATES,
                confidence=0.78,
                context_weight={
                    RelationshipContext.SEXUAL: 1.1,
                    RelationshipContext.ROMANTIC: 1.0
                }
            ),
        ])
        
        # Intimate connection patterns
        mappings.extend([
            RelationshipMapping(
                source_labels={"emotional_intimacy", "vulnerability_sharing", "deep_connection"},
                target_relationship=RelationshipTypes.INTIMATE_CONNECTS,
                confidence=0.83,
                context_weight={
                    RelationshipContext.ROMANTIC: 1.2,
                    RelationshipContext.SEXUAL: 1.1,
                    RelationshipContext.FRIEND: 0.9,
                    RelationshipContext.FAMILY: 0.8
                }
            ),
            RelationshipMapping(
                source_labels={"emotional_distance", "vulnerability_withdrawal", "intimacy_barriers"},
                target_relationship=RelationshipTypes.INTIMATE_DISTANCES,
                confidence=0.80,
                context_weight={
                    RelationshipContext.ROMANTIC: 1.1,
                    RelationshipContext.SEXUAL: 1.0,
                    RelationshipContext.FAMILY: 0.9
                }
            ),
        ])
        
        # ═══════════════════════════════════════════════════════════════════
        # BOUNDARY & CONSENT RELATIONSHIP MAPPINGS
        # ═══════════════════════════════════════════════════════════════════
        
        mappings.extend([
            RelationshipMapping(
                source_labels={"boundary_establishment", "limit_setting", "consent_clarification"},
                target_relationship=RelationshipTypes.BOUNDARY_SETS,
                confidence=0.90,
                context_weight={context: 1.0 for context in RelationshipContext}
            ),
            RelationshipMapping(
                source_labels={"boundary_testing", "limit_pushing", "consent_pressure"},
                target_relationship=RelationshipTypes.BOUNDARY_TESTS,
                confidence=0.87,
                context_weight={
                    RelationshipContext.SEXUAL: 1.3,
                    RelationshipContext.ROMANTIC: 1.2,
                    RelationshipContext.PROFESSIONAL: 1.1
                }
            ),
            RelationshipMapping(
                source_labels={"boundary_violation", "consent_violation", "limit_crossing"},
                target_relationship=RelationshipTypes.BOUNDARY_VIOLATES,
                confidence=0.95,
                context_weight={context: 1.2 for context in RelationshipContext}
            ),
            RelationshipMapping(
                source_labels={"boundary_reinforcement", "limit_maintenance", "consent_reaffirmation"},
                target_relationship=RelationshipTypes.BOUNDARY_REINFORCES,
                confidence=0.85,
                context_weight={context: 1.0 for context in RelationshipContext}
            ),
            RelationshipMapping(
                source_labels={"consent_seeking", "permission_asking", "consent_check"},
                target_relationship=RelationshipTypes.CONSENT_SEEKS,
                confidence=0.88,
                context_weight={
                    RelationshipContext.SEXUAL: 1.3,
                    RelationshipContext.ROMANTIC: 1.1,
                    RelationshipContext.PROFESSIONAL: 1.2
                }
            ),
            RelationshipMapping(
                source_labels={"consent_granting", "permission_giving", "agreement_explicit"},
                target_relationship=RelationshipTypes.CONSENT_GIVES,
                confidence=0.83,
                context_weight={context: 1.0 for context in RelationshipContext}
            ),
            RelationshipMapping(
                source_labels={"consent_withdrawal", "permission_revocation", "agreement_cancellation"},
                target_relationship=RelationshipTypes.CONSENT_WITHDRAWS,
                confidence=0.92,
                context_weight={context: 1.1 for context in RelationshipContext}
            ),
        ])
        
        # ═══════════════════════════════════════════════════════════════════
        # POWER & CONTROL RELATIONSHIP MAPPINGS
        # ═══════════════════════════════════════════════════════════════════
        
        mappings.extend([
            RelationshipMapping(
                source_labels={"dominance_assertion", "power_display", "control_taking"},
                target_relationship=RelationshipTypes.DOMINATES,
                confidence=0.86,
                context_weight={
                    RelationshipContext.SEXUAL: 1.2,
                    RelationshipContext.PROFESSIONAL: 1.1,
                    RelationshipContext.FAMILY: 0.9
                }
            ),
            RelationshipMapping(
                source_labels={"submission_display", "power_yielding", "control_surrendering"},
                target_relationship=RelationshipTypes.SUBMITS_TO,
                confidence=0.84,
                context_weight={
                    RelationshipContext.SEXUAL: 1.2,
                    RelationshipContext.ROMANTIC: 1.0,
                    RelationshipContext.FAMILY: 0.8
                }
            ),
            RelationshipMapping(
                source_labels={"authority_challenge", "power_resistance", "control_defiance"},
                target_relationship=RelationshipTypes.CHALLENGES,
                confidence=0.88,
                context_weight={
                    RelationshipContext.PROFESSIONAL: 1.2,
                    RelationshipContext.FAMILY: 1.1,
                    RelationshipContext.SEXUAL: 1.0
                }
            ),
            RelationshipMapping(
                source_labels={"control_behavior", "manipulation_attempt", "coercion_pattern"},
                target_relationship=RelationshipTypes.CONTROLS,
                confidence=0.89,
                context_weight={context: 1.1 for context in RelationshipContext}
            ),
            RelationshipMapping(
                source_labels={"resistance_behavior", "control_pushback", "autonomy_assertion"},
                target_relationship=RelationshipTypes.RESISTS,
                confidence=0.82,
                context_weight={context: 1.0 for context in RelationshipContext}
            ),
        ])
        
        # ═══════════════════════════════════════════════════════════════════
        # EMOTIONAL & PSYCHOLOGICAL RELATIONSHIP MAPPINGS
        # ═══════════════════════════════════════════════════════════════════
        
        mappings.extend([
            RelationshipMapping(
                source_labels={"conflict_escalation", "tension_increase", "stress_amplification"},
                target_relationship=RelationshipTypes.ESCALATES_FROM,
                confidence=0.87,
                context_weight={context: 1.0 for context in RelationshipContext},
                required_sequence=True
            ),
            RelationshipMapping(
                source_labels={"repair_attempt", "reconciliation_effort", "relationship_mending"},
                target_relationship=RelationshipTypes.REPAIRS_AFTER,
                confidence=0.90,
                context_weight={context: 1.0 for context in RelationshipContext},
                required_sequence=True
            ),
            RelationshipMapping(
                source_labels={"emotional_trigger", "psychological_trigger", "trauma_activation"},
                target_relationship=RelationshipTypes.TRIGGERS,
                confidence=0.85,
                context_weight={context: 1.0 for context in RelationshipContext}
            ),
            RelationshipMapping(
                source_labels={"validation_giving", "emotional_support", "affirmation_providing"},
                target_relationship=RelationshipTypes.VALIDATES,
                confidence=0.83,
                context_weight={
                    RelationshipContext.ROMANTIC: 1.1,
                    RelationshipContext.FAMILY: 1.2,
                    RelationshipContext.FRIEND: 1.1
                }
            ),
            RelationshipMapping(
                source_labels={"invalidation_pattern", "dismissal_behavior", "emotional_dismissal"},
                target_relationship=RelationshipTypes.INVALIDATES,
                confidence=0.86,
                context_weight={context: 1.1 for context in RelationshipContext}
            ),
            RelationshipMapping(
                source_labels={"gaslighting_pattern", "reality_distortion", "perception_manipulation"},
                target_relationship=RelationshipTypes.GASLIGHTS,
                confidence=0.93,
                context_weight={context: 1.2 for context in RelationshipContext}
            ),
            RelationshipMapping(
                source_labels={"emotional_manipulation", "psychological_manipulation", "guilt_tripping"},
                target_relationship=RelationshipTypes.MANIPULATES,
                confidence=0.88,
                context_weight={context: 1.1 for context in RelationshipContext}
            ),
            RelationshipMapping(
                source_labels={"emotional_soothing", "comfort_providing", "calming_behavior"},
                target_relationship=RelationshipTypes.SOOTHES,
                confidence=0.81,
                context_weight={
                    RelationshipContext.ROMANTIC: 1.1,
                    RelationshipContext.FAMILY: 1.2,
                    RelationshipContext.FRIEND: 1.0
                }
            ),
        ])
        
        # ═══════════════════════════════════════════════════════════════════
        # FAMILY & SUPPORT RELATIONSHIP MAPPINGS
        # ═══════════════════════════════════════════════════════════════════
        
        mappings.extend([
            RelationshipMapping(
                source_labels={"nurturing_behavior", "caretaking_pattern", "protective_instinct"},
                target_relationship=RelationshipTypes.NURTURES,
                confidence=0.84,
                context_weight={
                    RelationshipContext.FAMILY: 1.3,
                    RelationshipContext.ROMANTIC: 1.1,
                    RelationshipContext.FRIEND: 0.9
                }
            ),
            RelationshipMapping(
                source_labels={"protective_behavior", "defense_pattern", "safety_providing"},
                target_relationship=RelationshipTypes.PROTECTS,
                confidence=0.82,
                context_weight={
                    RelationshipContext.FAMILY: 1.2,
                    RelationshipContext.ROMANTIC: 1.1,
                    RelationshipContext.FRIEND: 1.0
                }
            ),
            RelationshipMapping(
                source_labels={"dependency_pattern", "reliance_behavior", "support_seeking"},
                target_relationship=RelationshipTypes.DEPENDS_ON,
                confidence=0.79,
                context_weight={
                    RelationshipContext.FAMILY: 1.1,
                    RelationshipContext.ROMANTIC: 1.0,
                    RelationshipContext.PROFESSIONAL: 0.7
                }
            ),
            RelationshipMapping(
                source_labels={"support_providing", "help_offering", "assistance_pattern"},
                target_relationship=RelationshipTypes.SUPPORTS,
                confidence=0.85,
                context_weight={context: 1.0 for context in RelationshipContext}
            ),
            RelationshipMapping(
                source_labels={"emotional_burden", "caretaking_overload", "responsibility_dumping"},
                target_relationship=RelationshipTypes.BURDENS,
                confidence=0.87,
                context_weight={
                    RelationshipContext.FAMILY: 1.2,
                    RelationshipContext.ROMANTIC: 1.1,
                    RelationshipContext.FRIEND: 0.9
                }
            ),
        ])
        
        # ═══════════════════════════════════════════════════════════════════
        # PROFESSIONAL & TRANSACTIONAL MAPPINGS
        # ═══════════════════════════════════════════════════════════════════
        
        mappings.extend([
            RelationshipMapping(
                source_labels={"service_negotiation", "terms_discussion", "contract_establishing"},
                target_relationship=RelationshipTypes.NEGOTIATES_SERVICE,
                confidence=0.89,
                context_weight={
                    RelationshipContext.PROFESSIONAL: 1.4,
                    RelationshipContext.UNKNOWN: 0.7
                }
            ),
            RelationshipMapping(
                source_labels={"terms_establishment", "conditions_setting", "agreement_formation"},
                target_relationship=RelationshipTypes.ESTABLISHES_TERMS,
                confidence=0.86,
                context_weight={
                    RelationshipContext.PROFESSIONAL: 1.3,
                    RelationshipContext.UNKNOWN: 0.8
                }
            ),
            RelationshipMapping(
                source_labels={"professional_boundary", "work_boundary", "business_maintenance"},
                target_relationship=RelationshipTypes.MAINTAINS_PROFESSIONAL,
                confidence=0.91,
                context_weight={
                    RelationshipContext.PROFESSIONAL: 1.5,
                    RelationshipContext.ROMANTIC: 0.6,
                    RelationshipContext.SEXUAL: 0.5
                }
            ),
            RelationshipMapping(
                source_labels={"boundary_blurring", "professional_crossing", "personal_mixing"},
                target_relationship=RelationshipTypes.BLURS_PROFESSIONAL,
                confidence=0.88,
                context_weight={
                    RelationshipContext.PROFESSIONAL: 1.3,
                    RelationshipContext.ROMANTIC: 1.1
                }
            ),
        ])
        
        # ═══════════════════════════════════════════════════════════════════
        # ADVANCED RELATIONSHIP DYNAMICS
        # ═══════════════════════════════════════════════════════════════════
        
        mappings.extend([
            RelationshipMapping(
                source_labels={"third_party_involvement", "triangle_creation", "others_involving"},
                target_relationship=RelationshipTypes.TRIANGULATES,
                confidence=0.84,
                context_weight={context: 1.1 for context in RelationshipContext}
            ),
            RelationshipMapping(
                source_labels={"isolation_pattern", "social_separation", "support_cutting"},
                target_relationship=RelationshipTypes.ISOLATES,
                confidence=0.89,
                context_weight={context: 1.2 for context in RelationshipContext}
            ),
            RelationshipMapping(
                source_labels={"competition_dynamic", "rivalry_pattern", "competing_behavior"},
                target_relationship=RelationshipTypes.COMPETES_WITH,
                confidence=0.81,
                context_weight={
                    RelationshipContext.PROFESSIONAL: 1.2,
                    RelationshipContext.FAMILY: 1.0,
                    RelationshipContext.FRIEND: 1.1
                }
            ),
            RelationshipMapping(
                source_labels={"alliance_formation", "partnership_building", "coalition_creating"},
                target_relationship=RelationshipTypes.ALLIES_WITH,
                confidence=0.83,
                context_weight={context: 1.0 for context in RelationshipContext}
            ),
            RelationshipMapping(
                source_labels={"trust_betrayal", "loyalty_violation", "confidence_breaking"},
                target_relationship=RelationshipTypes.BETRAYS,
                confidence=0.91,
                context_weight={context: 1.1 for context in RelationshipContext}
            ),
            RelationshipMapping(
                source_labels={"reconciliation_attempt", "peace_making", "relationship_restoration"},
                target_relationship=RelationshipTypes.RECONCILES,
                confidence=0.86,
                context_weight={context: 1.0 for context in RelationshipContext},
                required_sequence=True
            ),
        ])
        
        return mappings
    
    def _build_context_detectors(self) -> Dict[RelationshipContext, Set[str]]:
        """Build context detection mappings from psychology labels."""
        return {
            RelationshipContext.SEXUAL: {
                "sexual_content", "arousal_anticipation", "sexual_negotiation", 
                "sexual_rejection", "sexual_withdrawal", "desire_expression",
                "arousal_escalation", "sexual_tension", "sexual_coercion",
                "orgasm_reference", "sexual_performance", "kink_reference"
            },
            RelationshipContext.ROMANTIC: {
                "emotional_intimacy", "vulnerability_sharing", "deep_connection",
                "romantic_expression", "love_declaration", "relationship_commitment",
                "future_planning", "romantic_gesture", "affection_expression",
                "jealousy_expression", "romantic_disappointment"
            },
            RelationshipContext.FAMILY: {
                "family_reference", "parental_dynamic", "sibling_dynamic",
                "nurturing_behavior", "caretaking_pattern", "protective_instinct",
                "family_obligation", "generational_conflict", "family_loyalty",
                "parent_child_boundary", "family_responsibility"
            },
            RelationshipContext.FRIEND: {
                "friendship_reference", "social_support", "peer_interaction",
                "shared_experience", "social_bonding", "group_dynamic",
                "social_conflict", "friendship_boundary", "peer_pressure",
                "social_validation", "friendship_loyalty"
            },
            RelationshipContext.PROFESSIONAL: {
                "work_reference", "professional_boundary", "service_negotiation",
                "terms_discussion", "contract_establishing", "business_transaction",
                "professional_service", "work_relationship", "client_interaction",
                "service_boundary", "professional_ethics"
            }
        }
    
    def get_relationship_explanation(self, relationship_type: str, 
                                   source_labels: List[str]) -> str:
        """Get human-readable explanation for detected relationship."""
        explanations = {
            RelationshipTypes.SEXUAL_ESCALATES: "Sexual tension and arousal building between messages",
            RelationshipTypes.SEXUAL_WITHDRAWS: "Sexual withdrawal or rejection pattern detected",
            RelationshipTypes.BOUNDARY_TESTS: "Boundary testing or limit pushing behavior",
            RelationshipTypes.BOUNDARY_VIOLATES: "Clear boundary violation detected",
            RelationshipTypes.CONSENT_SEEKS: "Active consent seeking or permission requesting",
            RelationshipTypes.DOMINATES: "Power assertion or dominance behavior",
            RelationshipTypes.MANIPULATES: "Emotional or psychological manipulation pattern",
            RelationshipTypes.GASLIGHTS: "Gaslighting or reality distortion behavior",
            RelationshipTypes.ESCALATES_FROM: "Conflict or tension escalation pattern",
            RelationshipTypes.REPAIRS_AFTER: "Relationship repair or reconciliation attempt",
            RelationshipTypes.TRIANGULATES: "Third-party involvement or triangulation",
            RelationshipTypes.ISOLATES: "Social isolation or support system undermining",
        }
        
        base_explanation = explanations.get(relationship_type, f"Relationship pattern: {relationship_type}")
        if source_labels:
            base_explanation += f" (based on: {', '.join(source_labels[:3])})"
        
        return base_explanation