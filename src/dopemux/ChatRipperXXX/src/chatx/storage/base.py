"""Base interfaces and data structures for graph storage."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime


@dataclass
class GraphNode:
    """Represents a node in the conversation graph."""
    
    id: str                          # Unique node identifier
    node_type: str                   # Type of node (message, chunk, episode, etc.)
    properties: Dict[str, Any]       # Node properties and attributes
    
    def __post_init__(self):
        """Validate node data."""
        if not self.id or not isinstance(self.id, str):
            raise ValueError("Node ID must be a non-empty string")
        if not self.node_type or not isinstance(self.node_type, str):
            raise ValueError("Node type must be a non-empty string")


@dataclass
class GraphRelationship:
    """Represents a relationship between nodes in the conversation graph."""
    
    from_node: str                   # Source node ID
    to_node: str                     # Target node ID  
    relationship_type: str           # Type of relationship
    properties: Dict[str, Any]       # Relationship properties
    
    def __post_init__(self):
        """Validate relationship data."""
        if not all([self.from_node, self.to_node, self.relationship_type]):
            raise ValueError("From node, to node, and relationship type are required")


@dataclass  
class ConversationGraph:
    """Complete graph representation of a conversation."""
    
    conversation_id: str             # Unique conversation identifier
    nodes: List[GraphNode]           # All nodes in the graph
    relationships: List[GraphRelationship]  # All relationships
    metadata: Dict[str, Any]         # Graph-level metadata
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a specific node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_relationships_for_node(self, node_id: str) -> List[GraphRelationship]:
        """Get all relationships involving a specific node."""
        relationships = []
        for rel in self.relationships:
            if rel.from_node == node_id or rel.to_node == node_id:
                relationships.append(rel)
        return relationships
    
    def get_relationship_types(self) -> set[str]:
        """Get all unique relationship types in the graph."""
        return {rel.relationship_type for rel in self.relationships}


@dataclass
class PatternMatch:
    """Represents a detected pattern in conversation relationships."""
    
    pattern_type: str                # Type of pattern detected
    confidence: float                # Confidence score (0.0-1.0)
    nodes_involved: List[str]        # Node IDs involved in pattern
    relationships_involved: List[str] # Relationship IDs involved
    temporal_span: Dict[str, Any]    # Time span information
    properties: Dict[str, Any]       # Pattern-specific properties
    
    def __post_init__(self):
        """Validate pattern match."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")


@dataclass
class TemporalEvolution:
    """Represents temporal evolution of relationship patterns."""
    
    conversation_id: str             # Conversation being analyzed
    time_window: Dict[str, Any]      # Time window parameters
    evolution_metrics: Dict[str, Any] # Evolution statistics
    pattern_changes: List[Dict[str, Any]] # Pattern change events
    trend_analysis: Dict[str, Any]   # Trend analysis results


class BaseGraphStore(ABC):
    """Abstract base class for graph storage implementations."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the graph database.
        
        Raises:
            ConnectionError: If connection fails
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the graph database."""
        pass
    
    @abstractmethod
    async def create_graph(self, conversation_id: str, 
                          chunks: List[Dict[str, Any]]) -> ConversationGraph:
        """Create a conversation graph from message chunks.
        
        Args:
            conversation_id: Unique conversation identifier
            chunks: List of conversation chunks with metadata
            
        Returns:
            ConversationGraph representing the conversation structure
            
        Raises:
            ValueError: If chunks are invalid
            RuntimeError: If graph creation fails
        """
        pass
    
    @abstractmethod
    async def get_conversation_graph(self, conversation_id: str) -> Optional[ConversationGraph]:
        """Retrieve an existing conversation graph.
        
        Args:
            conversation_id: Conversation to retrieve
            
        Returns:
            ConversationGraph if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def query_relationships(self, conversation_id: str, 
                                relationship_types: Optional[List[str]] = None,
                                node_properties: Optional[Dict[str, Any]] = None) -> List[GraphRelationship]:
        """Query relationships based on criteria.
        
        Args:
            conversation_id: Conversation to search in
            relationship_types: Filter by relationship types
            node_properties: Filter by node properties
            
        Returns:
            List of matching relationships
        """
        pass
    
    @abstractmethod
    async def detect_patterns(self, conversation_id: str,
                            pattern_types: Optional[List[str]] = None) -> List[PatternMatch]:
        """Detect relationship patterns in conversation.
        
        Args:
            conversation_id: Conversation to analyze
            pattern_types: Types of patterns to detect
            
        Returns:
            List of detected patterns with confidence scores
        """
        pass
    
    @abstractmethod
    async def get_temporal_evolution(self, conversation_id: str,
                                   time_window_days: int = 30) -> TemporalEvolution:
        """Analyze temporal evolution of relationship patterns.
        
        Args:
            conversation_id: Conversation to analyze
            time_window_days: Analysis time window
            
        Returns:
            TemporalEvolution with trend analysis
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Check graph database health and connectivity.
        
        Returns:
            Dictionary with health status information
        """
        try:
            await self.connect()
            await self.disconnect()
            return {
                "status": "healthy",
                "message": "Graph database connection successful",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "message": f"Graph database connection failed: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }


# Enhanced psychology-specific relationship types for comprehensive forensic analysis
class RelationshipTypes:
    """Comprehensive relationship types covering romantic, sexual, family, and friend dynamics."""
    
    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 1: TEMPORAL & STRUCTURAL RELATIONSHIPS (Core Patterns)
    # ═══════════════════════════════════════════════════════════════════
    RESPONDS_TO = "RESPONDS_TO"                     # Direct response
    FOLLOWS = "FOLLOWS"                             # Sequential message
    REFERENCES_BACK = "REFERENCES_BACK"             # Historical reference
    INTERRUPTS = "INTERRUPTS"                       # Conversation interruption
    INITIATES = "INITIATES"                         # Topic/conversation initiation
    
    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 2: SEXUAL & INTIMATE RELATIONSHIPS
    # ═══════════════════════════════════════════════════════════════════
    SEXUAL_ESCALATES = "SEXUAL_ESCALATES"           # Sexual escalation pattern
    SEXUAL_WITHDRAWS = "SEXUAL_WITHDRAWS"           # Sexual withdrawal/rejection
    INTIMATE_CONNECTS = "INTIMATE_CONNECTS"         # Deep emotional connection
    INTIMATE_DISTANCES = "INTIMATE_DISTANCES"       # Emotional distancing
    AROUSAL_BUILDS = "AROUSAL_BUILDS"              # Sexual tension building
    AROUSAL_DEFLATES = "AROUSAL_DEFLATES"          # Sexual tension reduction
    SEXUAL_NEGOTIATES = "SEXUAL_NEGOTIATES"        # Sexual activity negotiation
    
    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 3: BOUNDARY & CONSENT DYNAMICS  
    # ═══════════════════════════════════════════════════════════════════
    BOUNDARY_SETS = "BOUNDARY_SETS"                # Clear boundary establishment
    BOUNDARY_TESTS = "BOUNDARY_TESTS"              # Boundary testing/pushing
    BOUNDARY_VIOLATES = "BOUNDARY_VIOLATES"        # Boundary violation
    BOUNDARY_REINFORCES = "BOUNDARY_REINFORCES"    # Boundary reinforcement
    CONSENT_SEEKS = "CONSENT_SEEKS"                # Consent seeking
    CONSENT_GIVES = "CONSENT_GIVES"                # Consent granting
    CONSENT_WITHDRAWS = "CONSENT_WITHDRAWS"        # Consent withdrawal
    CONSENT_VIOLATES = "CONSENT_VIOLATES"          # Consent violation
    
    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 4: EMOTIONAL & PSYCHOLOGICAL PATTERNS
    # ═══════════════════════════════════════════════════════════════════
    ESCALATES_FROM = "ESCALATES_FROM"              # Emotional escalation
    REPAIRS_AFTER = "REPAIRS_AFTER"                # Relationship repair
    TRIGGERS = "TRIGGERS"                          # Emotional triggering
    VALIDATES = "VALIDATES"                        # Emotional validation
    INVALIDATES = "INVALIDATES"                    # Emotional invalidation
    GASLIGHTS = "GASLIGHTS"                        # Gaslighting pattern
    MANIPULATES = "MANIPULATES"                    # Emotional manipulation
    SOOTHES = "SOOTHES"                           # Emotional soothing
    
    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 5: POWER & CONTROL DYNAMICS
    # ═══════════════════════════════════════════════════════════════════
    DOMINATES = "DOMINATES"                        # Power assertion/dominance
    SUBMITS_TO = "SUBMITS_TO"                      # Power submission
    CHALLENGES = "CHALLENGES"                      # Authority/power challenge  
    CONTROLS = "CONTROLS"                          # Control behavior
    RESISTS = "RESISTS"                           # Control resistance
    ENABLES = "ENABLES"                           # Enabling behavior
    CODEPENDS_ON = "CODEPENDS_ON"                 # Codependent pattern
    
    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 6: COMMUNICATION & CONTENT PATTERNS
    # ═══════════════════════════════════════════════════════════════════
    PARALLELS = "PARALLELS"                        # Similar pattern/content
    CONTRADICTS = "CONTRADICTS"                    # Contradiction pattern
    ELABORATES = "ELABORATES"                      # Content elaboration
    CLARIFIES = "CLARIFIES"                        # Clarification seeking
    AVOIDS = "AVOIDS"                             # Topic/issue avoidance
    DEFLECTS = "DEFLECTS"                         # Conversation deflection
    
    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 7: PROFESSIONAL & TRANSACTIONAL (Sex Work Context)
    # ═══════════════════════════════════════════════════════════════════
    NEGOTIATES_SERVICE = "NEGOTIATES_SERVICE"      # Service negotiation
    ESTABLISHES_TERMS = "ESTABLISHES_TERMS"        # Terms/conditions setting
    MAINTAINS_PROFESSIONAL = "MAINTAINS_PROFESSIONAL"  # Professional boundary maintenance
    BLURS_PROFESSIONAL = "BLURS_PROFESSIONAL"      # Professional boundary blurring
    
    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 8: FAMILY & SUPPORT RELATIONSHIPS
    # ═══════════════════════════════════════════════════════════════════
    NURTURES = "NURTURES"                          # Nurturing/caring behavior
    PROTECTS = "PROTECTS"                          # Protective behavior
    DEPENDS_ON = "DEPENDS_ON"                      # Dependency relationship
    SUPPORTS = "SUPPORTS"                          # Emotional/practical support
    BURDENS = "BURDENS"                           # Emotional burdening
    
    # ═══════════════════════════════════════════════════════════════════
    # CATEGORY 9: ADVANCED RELATIONSHIP DYNAMICS
    # ═══════════════════════════════════════════════════════════════════
    TRIANGULATES = "TRIANGULATES"                  # Third-party involvement
    ISOLATES = "ISOLATES"                         # Social isolation pattern
    COMPETES_WITH = "COMPETES_WITH"               # Competition dynamic
    ALLIES_WITH = "ALLIES_WITH"                   # Alliance formation
    BETRAYS = "BETRAYS"                           # Trust betrayal
    RECONCILES = "RECONCILES"                     # Reconciliation attempt
    
    @classmethod
    def get_all_types(cls) -> List[str]:
        """Get all 47 defined relationship types organized by category."""
        return [
            # Temporal & Structural (5)
            cls.RESPONDS_TO, cls.FOLLOWS, cls.REFERENCES_BACK, cls.INTERRUPTS, cls.INITIATES,
            
            # Sexual & Intimate (7)  
            cls.SEXUAL_ESCALATES, cls.SEXUAL_WITHDRAWS, cls.INTIMATE_CONNECTS, cls.INTIMATE_DISTANCES,
            cls.AROUSAL_BUILDS, cls.AROUSAL_DEFLATES, cls.SEXUAL_NEGOTIATES,
            
            # Boundary & Consent (8)
            cls.BOUNDARY_SETS, cls.BOUNDARY_TESTS, cls.BOUNDARY_VIOLATES, cls.BOUNDARY_REINFORCES,
            cls.CONSENT_SEEKS, cls.CONSENT_GIVES, cls.CONSENT_WITHDRAWS, cls.CONSENT_VIOLATES,
            
            # Emotional & Psychological (8)
            cls.ESCALATES_FROM, cls.REPAIRS_AFTER, cls.TRIGGERS, cls.VALIDATES,
            cls.INVALIDATES, cls.GASLIGHTS, cls.MANIPULATES, cls.SOOTHES,
            
            # Power & Control (7)
            cls.DOMINATES, cls.SUBMITS_TO, cls.CHALLENGES, cls.CONTROLS,
            cls.RESISTS, cls.ENABLES, cls.CODEPENDS_ON,
            
            # Communication & Content (6)
            cls.PARALLELS, cls.CONTRADICTS, cls.ELABORATES, cls.CLARIFIES,
            cls.AVOIDS, cls.DEFLECTS,
            
            # Professional & Transactional (4)
            cls.NEGOTIATES_SERVICE, cls.ESTABLISHES_TERMS, cls.MAINTAINS_PROFESSIONAL, cls.BLURS_PROFESSIONAL,
            
            # Family & Support (5)
            cls.NURTURES, cls.PROTECTS, cls.DEPENDS_ON, cls.SUPPORTS, cls.BURDENS,
            
            # Advanced Relationship Dynamics (6)
            cls.TRIANGULATES, cls.ISOLATES, cls.COMPETES_WITH, cls.ALLIES_WITH, cls.BETRAYS, cls.RECONCILES
        ]
        
    @classmethod  
    def get_category_types(cls, category: str) -> List[str]:
        """Get relationship types for a specific category."""
        categories = {
            "temporal_structural": [
                cls.RESPONDS_TO, cls.FOLLOWS, cls.REFERENCES_BACK, cls.INTERRUPTS, cls.INITIATES
            ],
            "sexual_intimate": [
                cls.SEXUAL_ESCALATES, cls.SEXUAL_WITHDRAWS, cls.INTIMATE_CONNECTS, cls.INTIMATE_DISTANCES,
                cls.AROUSAL_BUILDS, cls.AROUSAL_DEFLATES, cls.SEXUAL_NEGOTIATES
            ],
            "boundary_consent": [
                cls.BOUNDARY_SETS, cls.BOUNDARY_TESTS, cls.BOUNDARY_VIOLATES, cls.BOUNDARY_REINFORCES,
                cls.CONSENT_SEEKS, cls.CONSENT_GIVES, cls.CONSENT_WITHDRAWS, cls.CONSENT_VIOLATES
            ],
            "emotional_psychological": [
                cls.ESCALATES_FROM, cls.REPAIRS_AFTER, cls.TRIGGERS, cls.VALIDATES,
                cls.INVALIDATES, cls.GASLIGHTS, cls.MANIPULATES, cls.SOOTHES
            ],
            "power_control": [
                cls.DOMINATES, cls.SUBMITS_TO, cls.CHALLENGES, cls.CONTROLS,
                cls.RESISTS, cls.ENABLES, cls.CODEPENDS_ON
            ],
            "communication_content": [
                cls.PARALLELS, cls.CONTRADICTS, cls.ELABORATES, cls.CLARIFIES,
                cls.AVOIDS, cls.DEFLECTS
            ],
            "professional_transactional": [
                cls.NEGOTIATES_SERVICE, cls.ESTABLISHES_TERMS, cls.MAINTAINS_PROFESSIONAL, cls.BLURS_PROFESSIONAL
            ],
            "family_support": [
                cls.NURTURES, cls.PROTECTS, cls.DEPENDS_ON, cls.SUPPORTS, cls.BURDENS
            ],
            "advanced_dynamics": [
                cls.TRIANGULATES, cls.ISOLATES, cls.COMPETES_WITH, cls.ALLIES_WITH, cls.BETRAYS, cls.RECONCILES
            ]
        }
        return categories.get(category, [])


# Enhanced psychology-specific pattern types for comprehensive relationship analysis
class PatternTypes:
    """Comprehensive pattern types leveraging 47 relationship types for forensic analysis."""
    
    # ═══════════════════════════════════════════════════════════════════
    # CORE RELATIONSHIP PATTERNS (Original + Enhanced)
    # ═══════════════════════════════════════════════════════════════════
    ESCALATION_CYCLE = "escalation_cycle"                    # Escalation->Peak->Resolution
    REPAIR_CYCLE = "repair_cycle"                           # Harm->Repair->Reconciliation  
    BOUNDARY_TESTING = "boundary_testing"                   # Repeated boundary tests/violations
    GASLIGHTING_SEQUENCE = "gaslighting_sequence"           # Systematic gaslighting pattern
    AVOIDANCE_PATTERN = "avoidance_pattern"                 # Conflict/topic avoidance
    VALIDATION_SEEKING = "validation_seeking"               # Validation request pattern
    
    # ═══════════════════════════════════════════════════════════════════
    # SEXUAL & INTIMACY PATTERNS
    # ═══════════════════════════════════════════════════════════════════
    SEXUAL_ESCALATION_CYCLE = "sexual_escalation_cycle"     # Sexual tension build->peak->resolution
    INTIMACY_APPROACH_AVOIDANCE = "intimacy_approach_avoidance"  # Intimacy seeking vs distancing
    AROUSAL_MANIPULATION = "arousal_manipulation"           # Using sexual arousal for control
    SEXUAL_COERCION_SEQUENCE = "sexual_coercion_sequence"   # Coercion->pressure->compliance
    INTIMACY_WITHDRAWAL_PUNISHMENT = "intimacy_withdrawal_punishment"  # Withholding intimacy as punishment
    
    # ═══════════════════════════════════════════════════════════════════
    # CONSENT & BOUNDARY PATTERNS  
    # ═══════════════════════════════════════════════════════════════════
    CONSENT_EROSION = "consent_erosion"                     # Gradual consent boundary erosion
    BOUNDARY_VIOLATION_CYCLE = "boundary_violation_cycle"   # Violate->apologize->repeat pattern
    CONSENT_MANUFACTURING = "consent_manufacturing"         # Creating false consent conditions
    BOUNDARY_REINFORCEMENT = "boundary_reinforcement"       # Healthy boundary maintenance pattern
    CONSENT_CHECK_PATTERN = "consent_check_pattern"         # Consistent consent verification
    
    # ═══════════════════════════════════════════════════════════════════
    # POWER & CONTROL PATTERNS
    # ═══════════════════════════════════════════════════════════════════
    POWER_STRUGGLE_CYCLE = "power_struggle_cycle"           # Dominance->resistance->escalation
    CONTROL_ESCALATION = "control_escalation"               # Increasing control over time
    CODEPENDENT_SPIRAL = "codependent_spiral"               # Mutual codependency reinforcement  
    SUBMISSION_CONDITIONING = "submission_conditioning"      # Gradual submission training
    RESISTANCE_PUNISHMENT = "resistance_punishment"         # Punishment for resistance patterns
    
    # ═══════════════════════════════════════════════════════════════════
    # MANIPULATION & PSYCHOLOGICAL PATTERNS
    # ═══════════════════════════════════════════════════════════════════
    MANIPULATION_SEQUENCE = "manipulation_sequence"         # Systematic emotional manipulation
    INVALIDATION_PATTERN = "invalidation_pattern"          # Consistent emotional invalidation
    TRIANGULATION_PATTERN = "triangulation_pattern"        # Third-party manipulation tactics
    ISOLATION_CAMPAIGN = "isolation_campaign"              # Systematic social isolation
    LOVE_BOMBING_CYCLE = "love_bombing_cycle"               # Excessive affection->withdrawal cycle
    
    # ═══════════════════════════════════════════════════════════════════
    # FAMILY & SUPPORT PATTERNS
    # ═══════════════════════════════════════════════════════════════════
    CARETAKING_OVERLOAD = "caretaking_overload"            # Excessive caretaking burden pattern
    EMOTIONAL_PARENTIFICATION = "emotional_parentification" # Child->parent role reversal
    DEPENDENCY_CULTIVATION = "dependency_cultivation"       # Creating/maintaining dependency
    SUPPORT_WITHDRAWAL = "support_withdrawal"              # Strategic support removal
    NURTURING_MANIPULATION = "nurturing_manipulation"      # Using care/nurturing for control
    
    # ═══════════════════════════════════════════════════════════════════
    # PROFESSIONAL/TRANSACTIONAL PATTERNS
    # ═══════════════════════════════════════════════════════════════════
    BOUNDARY_BLUR_PROGRESSION = "boundary_blur_progression" # Professional->personal boundary erosion
    SERVICE_SCOPE_CREEP = "service_scope_creep"            # Gradual service expansion beyond agreed terms
    PROFESSIONAL_EXPLOITATION = "professional_exploitation" # Exploiting professional relationship
    TERMS_NEGOTIATION_CYCLE = "terms_negotiation_cycle"    # Repeated terms renegotiation pattern
    
    # ═══════════════════════════════════════════════════════════════════
    # COMMUNICATION & BEHAVIORAL PATTERNS
    # ═══════════════════════════════════════════════════════════════════
    DEFLECTION_SEQUENCE = "deflection_sequence"            # Systematic topic deflection
    CONTRADICTION_PATTERN = "contradiction_pattern"        # Consistent self-contradiction
    CLARIFICATION_AVOIDANCE = "clarification_avoidance"    # Avoiding clear communication
    INTERRUPTION_DOMINANCE = "interruption_dominance"      # Using interruption for control
    
    # ═══════════════════════════════════════════════════════════════════
    # COMPLEX MULTI-RELATIONSHIP PATTERNS
    # ═══════════════════════════════════════════════════════════════════
    BETRAYAL_RECONCILIATION_CYCLE = "betrayal_reconciliation_cycle"  # Betray->reconcile->repeat
    COMPETITION_ALLIANCE_FLIP = "competition_alliance_flip"          # Competition->alliance switching
    CRISIS_BONDING = "crisis_bonding"                               # Creating crisis to increase bonding
    REWARD_PUNISHMENT_CONDITIONING = "reward_punishment_conditioning" # Behavioral conditioning pattern
    
    @classmethod
    def get_all_types(cls) -> List[str]:
        """Get all 32 defined pattern types organized by category."""
        return [
            # Core Relationship Patterns (6)
            cls.ESCALATION_CYCLE, cls.REPAIR_CYCLE, cls.BOUNDARY_TESTING,
            cls.GASLIGHTING_SEQUENCE, cls.AVOIDANCE_PATTERN, cls.VALIDATION_SEEKING,
            
            # Sexual & Intimacy Patterns (5)
            cls.SEXUAL_ESCALATION_CYCLE, cls.INTIMACY_APPROACH_AVOIDANCE, cls.AROUSAL_MANIPULATION,
            cls.SEXUAL_COERCION_SEQUENCE, cls.INTIMACY_WITHDRAWAL_PUNISHMENT,
            
            # Consent & Boundary Patterns (5)
            cls.CONSENT_EROSION, cls.BOUNDARY_VIOLATION_CYCLE, cls.CONSENT_MANUFACTURING,
            cls.BOUNDARY_REINFORCEMENT, cls.CONSENT_CHECK_PATTERN,
            
            # Power & Control Patterns (5)
            cls.POWER_STRUGGLE_CYCLE, cls.CONTROL_ESCALATION, cls.CODEPENDENT_SPIRAL,
            cls.SUBMISSION_CONDITIONING, cls.RESISTANCE_PUNISHMENT,
            
            # Manipulation & Psychological Patterns (5)
            cls.MANIPULATION_SEQUENCE, cls.INVALIDATION_PATTERN, cls.TRIANGULATION_PATTERN,
            cls.ISOLATION_CAMPAIGN, cls.LOVE_BOMBING_CYCLE,
            
            # Family & Support Patterns (5)
            cls.CARETAKING_OVERLOAD, cls.EMOTIONAL_PARENTIFICATION, cls.DEPENDENCY_CULTIVATION,
            cls.SUPPORT_WITHDRAWAL, cls.NURTURING_MANIPULATION,
            
            # Professional/Transactional Patterns (4)
            cls.BOUNDARY_BLUR_PROGRESSION, cls.SERVICE_SCOPE_CREEP, cls.PROFESSIONAL_EXPLOITATION,
            cls.TERMS_NEGOTIATION_CYCLE,
            
            # Communication & Behavioral Patterns (4)
            cls.DEFLECTION_SEQUENCE, cls.CONTRADICTION_PATTERN, cls.CLARIFICATION_AVOIDANCE,
            cls.INTERRUPTION_DOMINANCE,
            
            # Complex Multi-Relationship Patterns (4)
            cls.BETRAYAL_RECONCILIATION_CYCLE, cls.COMPETITION_ALLIANCE_FLIP, cls.CRISIS_BONDING,
            cls.REWARD_PUNISHMENT_CONDITIONING
        ]
        
    @classmethod
    def get_category_patterns(cls, category: str) -> List[str]:
        """Get pattern types for a specific category."""
        categories = {
            "core_relationship": [
                cls.ESCALATION_CYCLE, cls.REPAIR_CYCLE, cls.BOUNDARY_TESTING,
                cls.GASLIGHTING_SEQUENCE, cls.AVOIDANCE_PATTERN, cls.VALIDATION_SEEKING
            ],
            "sexual_intimacy": [
                cls.SEXUAL_ESCALATION_CYCLE, cls.INTIMACY_APPROACH_AVOIDANCE, cls.AROUSAL_MANIPULATION,
                cls.SEXUAL_COERCION_SEQUENCE, cls.INTIMACY_WITHDRAWAL_PUNISHMENT
            ],
            "consent_boundary": [
                cls.CONSENT_EROSION, cls.BOUNDARY_VIOLATION_CYCLE, cls.CONSENT_MANUFACTURING,
                cls.BOUNDARY_REINFORCEMENT, cls.CONSENT_CHECK_PATTERN
            ],
            "power_control": [
                cls.POWER_STRUGGLE_CYCLE, cls.CONTROL_ESCALATION, cls.CODEPENDENT_SPIRAL,
                cls.SUBMISSION_CONDITIONING, cls.RESISTANCE_PUNISHMENT
            ],
            "manipulation_psychological": [
                cls.MANIPULATION_SEQUENCE, cls.INVALIDATION_PATTERN, cls.TRIANGULATION_PATTERN,
                cls.ISOLATION_CAMPAIGN, cls.LOVE_BOMBING_CYCLE
            ],
            "family_support": [
                cls.CARETAKING_OVERLOAD, cls.EMOTIONAL_PARENTIFICATION, cls.DEPENDENCY_CULTIVATION,
                cls.SUPPORT_WITHDRAWAL, cls.NURTURING_MANIPULATION
            ],
            "professional_transactional": [
                cls.BOUNDARY_BLUR_PROGRESSION, cls.SERVICE_SCOPE_CREEP, cls.PROFESSIONAL_EXPLOITATION,
                cls.TERMS_NEGOTIATION_CYCLE
            ],
            "communication_behavioral": [
                cls.DEFLECTION_SEQUENCE, cls.CONTRADICTION_PATTERN, cls.CLARIFICATION_AVOIDANCE,
                cls.INTERRUPTION_DOMINANCE
            ],
            "complex_multi_relationship": [
                cls.BETRAYAL_RECONCILIATION_CYCLE, cls.COMPETITION_ALLIANCE_FLIP, cls.CRISIS_BONDING,
                cls.REWARD_PUNISHMENT_CONDITIONING
            ]
        }
        return categories.get(category, [])
        
    @classmethod
    def get_patterns_using_relationships(cls, relationship_types: List[str]) -> List[str]:
        """Get patterns that commonly involve specific relationship types."""
        # This maps relationship types to the patterns they commonly appear in
        relationship_to_patterns = {
            # Sexual & Intimate relationship patterns
            "SEXUAL_ESCALATES": [cls.SEXUAL_ESCALATION_CYCLE, cls.AROUSAL_MANIPULATION],
            "SEXUAL_WITHDRAWS": [cls.INTIMACY_WITHDRAWAL_PUNISHMENT, cls.SEXUAL_COERCION_SEQUENCE],
            "INTIMATE_CONNECTS": [cls.INTIMACY_APPROACH_AVOIDANCE, cls.LOVE_BOMBING_CYCLE],
            "INTIMATE_DISTANCES": [cls.INTIMACY_APPROACH_AVOIDANCE, cls.INTIMACY_WITHDRAWAL_PUNISHMENT],
            
            # Boundary & Consent patterns
            "BOUNDARY_VIOLATES": [cls.BOUNDARY_VIOLATION_CYCLE, cls.CONSENT_EROSION],
            "BOUNDARY_TESTS": [cls.BOUNDARY_TESTING, cls.CONSENT_EROSION],
            "CONSENT_VIOLATES": [cls.SEXUAL_COERCION_SEQUENCE, cls.CONSENT_MANUFACTURING],
            "CONSENT_SEEKS": [cls.CONSENT_CHECK_PATTERN, cls.BOUNDARY_REINFORCEMENT],
            
            # Power & Control patterns
            "DOMINATES": [cls.POWER_STRUGGLE_CYCLE, cls.CONTROL_ESCALATION, cls.SUBMISSION_CONDITIONING],
            "SUBMITS_TO": [cls.SUBMISSION_CONDITIONING, cls.CODEPENDENT_SPIRAL],
            "CONTROLS": [cls.CONTROL_ESCALATION, cls.MANIPULATION_SEQUENCE],
            "RESISTS": [cls.POWER_STRUGGLE_CYCLE, cls.RESISTANCE_PUNISHMENT],
            
            # Manipulation patterns
            "GASLIGHTS": [cls.GASLIGHTING_SEQUENCE, cls.MANIPULATION_SEQUENCE],
            "MANIPULATES": [cls.MANIPULATION_SEQUENCE, cls.TRIANGULATION_PATTERN],
            "TRIANGULATES": [cls.TRIANGULATION_PATTERN, cls.CRISIS_BONDING],
            "ISOLATES": [cls.ISOLATION_CAMPAIGN, cls.CONTROL_ESCALATION],
            
            # Family/Support patterns
            "NURTURES": [cls.NURTURING_MANIPULATION, cls.CARETAKING_OVERLOAD],
            "DEPENDS_ON": [cls.DEPENDENCY_CULTIVATION, cls.CODEPENDENT_SPIRAL],
            "BURDENS": [cls.CARETAKING_OVERLOAD, cls.EMOTIONAL_PARENTIFICATION],
        }
        
        relevant_patterns = set()
        for relationship_type in relationship_types:
            if relationship_type in relationship_to_patterns:
                relevant_patterns.update(relationship_to_patterns[relationship_type])
        
        return list(relevant_patterns)