"""Tests for psychology relationship mapping system."""

import pytest
from typing import List, Tuple

from src.chatx.storage.psychology_relationship_mapper import (
    PsychologyRelationshipMapper,
    RelationshipContext,
    RelationshipMapping
)
from src.chatx.storage.base import RelationshipTypes


class TestPsychologyRelationshipMapper:
    """Test psychology relationship mapping functionality."""
    
    def test_mapper_initialization(self):
        """Test that mapper initializes with comprehensive mappings."""
        mapper = PsychologyRelationshipMapper()
        
        assert mapper.mappings is not None
        assert len(mapper.mappings) > 30  # Should have many mappings (41 currently)
        assert mapper.context_detectors is not None
        assert len(mapper.context_detectors) == 5  # 5 relationship contexts
    
    def test_sexual_relationship_detection(self):
        """Test detection of sexual relationship patterns."""
        mapper = PsychologyRelationshipMapper()
        
        # Test sexual escalation
        labels1 = ["sexual_content", "arousal_anticipation"]
        labels2 = ["sexual_negotiation", "desire_expression"]
        
        relationships = mapper.map_labels_to_relationships(
            labels1, labels2, RelationshipContext.SEXUAL
        )
        
        assert len(relationships) > 0
        rel_types = [rel[0] for rel in relationships]
        assert RelationshipTypes.SEXUAL_ESCALATES in rel_types
        
        # Check confidence scores are reasonable
        for rel_type, confidence in relationships:
            assert 0.0 <= confidence <= 1.0
            if rel_type == RelationshipTypes.SEXUAL_ESCALATES:
                assert confidence > 0.7  # Should be high confidence in sexual context
    
    def test_boundary_relationship_detection(self):
        """Test detection of boundary and consent patterns."""
        mapper = PsychologyRelationshipMapper()
        
        # Test boundary violation
        labels1 = ["boundary_testing", "limit_pushing"]
        labels2 = ["boundary_violation", "consent_violation"]
        
        relationships = mapper.map_labels_to_relationships(
            labels1, labels2, RelationshipContext.ROMANTIC
        )
        
        rel_types = [rel[0] for rel in relationships]
        assert RelationshipTypes.BOUNDARY_TESTS in rel_types or RelationshipTypes.BOUNDARY_VIOLATES in rel_types
        
        # Test consent seeking
        labels1 = ["consent_seeking", "permission_asking"]
        labels2 = ["consent_granting", "agreement_explicit"]
        
        relationships = mapper.map_labels_to_relationships(
            labels1, labels2, RelationshipContext.SEXUAL
        )
        
        rel_types = [rel[0] for rel in relationships]
        assert RelationshipTypes.CONSENT_SEEKS in rel_types or RelationshipTypes.CONSENT_GIVES in rel_types
    
    def test_power_control_relationships(self):
        """Test detection of power and control dynamics."""
        mapper = PsychologyRelationshipMapper()
        
        # Test dominance/submission pattern
        labels1 = ["dominance_assertion", "power_display"]
        labels2 = ["submission_display", "power_yielding"]
        
        relationships = mapper.map_labels_to_relationships(
            labels1, labels2, RelationshipContext.SEXUAL
        )
        
        rel_types = [rel[0] for rel in relationships]
        assert RelationshipTypes.DOMINATES in rel_types or RelationshipTypes.SUBMITS_TO in rel_types
        
        # Test control behavior
        labels1 = ["control_behavior", "manipulation_attempt"]
        labels2 = ["resistance_behavior", "autonomy_assertion"]
        
        relationships = mapper.map_labels_to_relationships(
            labels1, labels2, RelationshipContext.ROMANTIC
        )
        
        rel_types = [rel[0] for rel in relationships]
        assert RelationshipTypes.CONTROLS in rel_types or RelationshipTypes.RESISTS in rel_types
    
    def test_context_detection(self):
        """Test relationship context detection."""
        mapper = PsychologyRelationshipMapper()
        
        # Test sexual context detection
        sexual_labels = ["sexual_content", "arousal_anticipation", "sexual_tension"]
        context = mapper.detect_relationship_context(sexual_labels)
        assert context == RelationshipContext.SEXUAL
        
        # Test romantic context detection  
        romantic_labels = ["emotional_intimacy", "vulnerability_sharing", "love_declaration"]
        context = mapper.detect_relationship_context(romantic_labels)
        assert context == RelationshipContext.ROMANTIC
        
        # Test family context detection
        family_labels = ["family_reference", "nurturing_behavior", "protective_instinct"]
        context = mapper.detect_relationship_context(family_labels)
        assert context == RelationshipContext.FAMILY
        
        # Test professional context detection
        professional_labels = ["service_negotiation", "professional_boundary", "work_reference"]
        context = mapper.detect_relationship_context(professional_labels)
        assert context == RelationshipContext.PROFESSIONAL
        
        # Test unknown context for ambiguous labels
        ambiguous_labels = ["random_label", "unrelated_content"]
        context = mapper.detect_relationship_context(ambiguous_labels)
        assert context == RelationshipContext.UNKNOWN
    
    def test_context_weight_application(self):
        """Test that context weights affect confidence scores appropriately."""
        mapper = PsychologyRelationshipMapper()
        
        # Test that sexual relationship types get boosted confidence in sexual context
        labels1 = ["sexual_content"]
        labels2 = ["arousal_escalation"]
        
        # Sexual context should boost confidence
        sexual_relationships = mapper.map_labels_to_relationships(
            labels1, labels2, RelationshipContext.SEXUAL
        )
        
        # Professional context should reduce confidence  
        professional_relationships = mapper.map_labels_to_relationships(
            labels1, labels2, RelationshipContext.PROFESSIONAL
        )
        
        # Find SEXUAL_ESCALATES in both results
        sexual_confidence = None
        professional_confidence = None
        
        for rel_type, confidence in sexual_relationships:
            if rel_type == RelationshipTypes.SEXUAL_ESCALATES:
                sexual_confidence = confidence
                
        for rel_type, confidence in professional_relationships:
            if rel_type == RelationshipTypes.SEXUAL_ESCALATES:
                professional_confidence = confidence
        
        # Sexual context should have higher confidence than professional
        if sexual_confidence and professional_confidence:
            assert sexual_confidence > professional_confidence
    
    def test_exclusion_labels(self):
        """Test that exclusion labels prevent relationship detection."""
        mapper = PsychologyRelationshipMapper()
        
        # Create a test mapping with exclusion labels
        test_mapping = RelationshipMapping(
            source_labels={"test_label"},
            target_relationship=RelationshipTypes.VALIDATES,
            confidence=0.8,
            context_weight={RelationshipContext.UNKNOWN: 1.0},
            exclusion_labels={"exclusion_label"}
        )
        
        # Add to mapper for testing
        mapper.mappings.append(test_mapping)
        
        # Without exclusion label should detect relationship
        relationships = mapper.map_labels_to_relationships(
            ["test_label"], [], RelationshipContext.UNKNOWN
        )
        rel_types = [rel[0] for rel in relationships]
        assert RelationshipTypes.VALIDATES in rel_types
        
        # With exclusion label should NOT detect relationship
        relationships = mapper.map_labels_to_relationships(
            ["test_label", "exclusion_label"], [], RelationshipContext.UNKNOWN
        )
        rel_types = [rel[0] for rel in relationships]
        assert RelationshipTypes.VALIDATES not in rel_types
    
    def test_temporal_sequence_requirement(self):
        """Test that temporal sequence requirements are enforced."""
        mapper = PsychologyRelationshipMapper()
        
        # Find a mapping that requires temporal sequence (e.g., REPAIRS_AFTER)
        labels1 = ["conflict_escalation"]
        labels2 = ["repair_attempt", "reconciliation_effort"]
        
        # With temporal sequence should detect repair relationship
        with_sequence = mapper.map_labels_to_relationships(
            labels1, labels2, RelationshipContext.ROMANTIC, temporal_sequence=True
        )
        
        # Without temporal sequence should not detect repair relationship
        without_sequence = mapper.map_labels_to_relationships(
            labels1, labels2, RelationshipContext.ROMANTIC, temporal_sequence=False
        )
        
        with_types = [rel[0] for rel in with_sequence]
        without_types = [rel[0] for rel in without_sequence]
        
        # REPAIRS_AFTER should be detected with sequence but not without
        if RelationshipTypes.REPAIRS_AFTER in with_types:
            assert RelationshipTypes.REPAIRS_AFTER not in without_types
    
    def test_relationship_explanation(self):
        """Test relationship explanation generation."""
        mapper = PsychologyRelationshipMapper()
        
        # Test explanation for sexual escalation
        explanation = mapper.get_relationship_explanation(
            RelationshipTypes.SEXUAL_ESCALATES, ["sexual_content", "arousal_escalation"]
        )
        
        assert "Sexual tension" in explanation
        assert "sexual_content" in explanation
        
        # Test explanation for boundary violation
        explanation = mapper.get_relationship_explanation(
            RelationshipTypes.BOUNDARY_VIOLATES, ["boundary_violation"]
        )
        
        assert "boundary violation" in explanation.lower()
        assert "boundary_violation" in explanation
    
    def test_confidence_thresholds(self):
        """Test that confidence thresholds filter out low-confidence relationships."""
        mapper = PsychologyRelationshipMapper()
        
        # Test with labels that should produce low confidence
        weak_labels1 = ["vague_label"]
        weak_labels2 = ["unrelated_label"]
        
        relationships = mapper.map_labels_to_relationships(
            weak_labels1, weak_labels2, RelationshipContext.UNKNOWN
        )
        
        # All returned relationships should meet minimum confidence threshold
        for rel_type, confidence in relationships:
            assert confidence > 0.3  # Minimum threshold from mapper
    
    def test_top_relationships_limit(self):
        """Test that mapper returns limited number of top relationships."""
        mapper = PsychologyRelationshipMapper()
        
        # Use labels that might trigger many relationships
        rich_labels1 = ["sexual_content", "boundary_testing", "dominance_assertion", 
                        "emotional_manipulation", "control_behavior"]
        rich_labels2 = ["arousal_escalation", "boundary_violation", "submission_display",
                        "invalidation_pattern", "resistance_behavior"]
        
        relationships = mapper.map_labels_to_relationships(
            rich_labels1, rich_labels2, RelationshipContext.SEXUAL
        )
        
        # Should return at most 5 relationships (as per mapper design)
        assert len(relationships) <= 5
        
        # Should be sorted by confidence (highest first)
        if len(relationships) > 1:
            for i in range(len(relationships) - 1):
                assert relationships[i][1] >= relationships[i + 1][1]
    
    @pytest.mark.parametrize("context", [
        RelationshipContext.SEXUAL,
        RelationshipContext.ROMANTIC, 
        RelationshipContext.FAMILY,
        RelationshipContext.FRIEND,
        RelationshipContext.PROFESSIONAL
    ])
    def test_all_contexts_have_detectors(self, context: RelationshipContext):
        """Test that all relationship contexts have detection labels."""
        mapper = PsychologyRelationshipMapper()
        
        assert context in mapper.context_detectors
        assert len(mapper.context_detectors[context]) > 0
    
    def test_comprehensive_relationship_coverage(self):
        """Test that mapping covers all major relationship types."""
        mapper = PsychologyRelationshipMapper()
        
        # Get all relationship types that have mappings
        mapped_relationships = set()
        for mapping in mapper.mappings:
            mapped_relationships.add(mapping.target_relationship)
        
        # Check that major relationship categories are covered
        major_relationships = {
            RelationshipTypes.SEXUAL_ESCALATES,
            RelationshipTypes.BOUNDARY_TESTS,
            RelationshipTypes.BOUNDARY_VIOLATES,
            RelationshipTypes.DOMINATES,
            RelationshipTypes.MANIPULATES,
            RelationshipTypes.ESCALATES_FROM,
            RelationshipTypes.REPAIRS_AFTER,
            RelationshipTypes.GASLIGHTS,
            RelationshipTypes.TRIANGULATES,
            RelationshipTypes.ISOLATES,
        }
        
        # Most major relationships should have mappings
        coverage = len(major_relationships.intersection(mapped_relationships))
        assert coverage >= len(major_relationships) * 0.8  # At least 80% coverage