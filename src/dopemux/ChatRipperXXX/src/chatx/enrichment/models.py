"""Pydantic models for LLM-based message enrichment."""

from typing import Optional, Literal, Any
from enum import Enum
from datetime import datetime
import uuid

from pydantic import BaseModel, Field, validator, root_validator


class EmotionEnum(str, Enum):
    """Primary emotion categories for message analysis."""
    JOY = "joy"
    ANGER = "anger"
    FEAR = "fear"
    SADNESS = "sadness"
    DISGUST = "disgust"
    SURPRISE = "surprise"
    NEUTRAL = "neutral"


class SpeechActEnum(str, Enum):
    """Speech act categories for message classification."""
    ASK = "ask"
    INFORM = "inform"
    PROMISE = "promise"
    REFUSE = "refuse"
    APOLOGIZE = "apologize"
    PROPOSE = "propose"
    META = "meta"


class StanceEnum(str, Enum):
    """Stance categories for relationship dynamics."""
    SUPPORTIVE = "supportive"
    NEUTRAL = "neutral"
    CHALLENGING = "challenging"


class BoundarySignalEnum(str, Enum):
    """Boundary signal categories for relationship analysis."""
    NONE = "none"
    SET = "set"
    TEST = "test"
    VIOLATE = "violate"
    REINFORCE = "reinforce"


class SourceEnum(str, Enum):
    """Source of enrichment analysis."""
    LOCAL = "local"
    CLOUD = "cloud"


class ConfidenceValue(BaseModel):
    """Confidence value with validation."""
    val: float = Field(ge=0.0, le=1.0, description="Confidence value between 0.0 and 1.0")


class MessageEnrichment(BaseModel):
    """Schema for message-level enrichment metadata."""
    
    msg_id: str = Field(description="Message identifier")
    speech_act: SpeechActEnum = Field(description="Speech act classification")
    intent: str = Field(max_length=200, description="Inferred intent")
    stance: StanceEnum = Field(description="Stance toward the other person")
    tone: str = Field(max_length=50, description="Communication tone")
    emotion_primary: EmotionEnum = Field(description="Primary emotion detected")
    certainty: ConfidenceValue = Field(description="Certainty level of speaker")
    directness: ConfidenceValue = Field(description="Directness of communication")
    boundary_signal: BoundarySignalEnum = Field(description="Boundary-related signal")
    repair_attempt: bool = Field(description="Whether this is a repair attempt")
    inferred_meaning: str = Field(max_length=200, description="Concise meaning summary")
    map_refs: list[str] = Field(default_factory=list, description="References to other messages")
    
    # Labels - coarse are cloud-safe, fine are local-only
    coarse_labels: list[str] = Field(default_factory=list, description="Cloud-safe labels")
    fine_labels_local: list[str] = Field(
        default_factory=list, 
        description="LOCAL-ONLY; MUST NOT be sent to cloud"
    )
    
    # Optional influence and relationship fields
    influence_class: Optional[str] = Field(None, description="Influence class from taxonomy")
    influence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Influence strength")
    relationship_structure: list[str] = Field(default_factory=list, description="Relationship structure elements")
    relationship_dynamic: list[str] = Field(default_factory=list, description="Dynamic patterns")
    
    # Metadata
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    confidence_llm: float = Field(ge=0.0, le=1.0, description="LLM confidence in analysis")
    source: SourceEnum = Field(description="Source of analysis")
    
    # Provenance
    provenance: dict[str, Any] = Field(default_factory=dict, description="Analysis provenance")
    shield: Optional[dict[str, Any]] = Field(None, description="Policy shield context")
    
    @validator('confidence_llm')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('confidence_llm must be between 0.0 and 1.0')
        return v
    
    @root_validator(skip_on_failure=True)
    def validate_influence_consistency(cls, values):
        influence_class = values.get('influence_class')
        influence_score = values.get('influence_score')
        
        if (influence_class is None) != (influence_score is None):
            raise ValueError('influence_class and influence_score must both be present or both be None')
        
        return values
    
    def set_provenance(self, run_id: str, model_id: str, prompt_hash: str) -> None:
        """Set provenance metadata."""
        self.provenance = {
            "schema_v": "0.1.0",
            "run_id": run_id,
            "model_id": model_id,
            "prompt_hash": prompt_hash,
            "timestamp": datetime.now().isoformat(),
        }
    
    class Config:
        use_enum_values = True


class ConversationUnitEnrichment(BaseModel):
    """Schema for conversation unit enrichment metadata."""
    
    cu_id: str = Field(description="Conversation unit identifier")
    topic_label: str = Field(max_length=50, description="Topic label (≤6 words)")
    vibe_trajectory: list[str] = Field(description="Emotional trajectory through unit")
    escalation_curve: Literal["low", "spike", "high", "resolve"] = Field(
        description="Escalation pattern"
    )
    
    # Relationship ledgers
    ledgers: dict[str, list[dict[str, Any]]] = Field(
        default_factory=lambda: {
            "boundary": [],
            "consent": [],
            "decisions": [],
            "commitments": []
        },
        description="Tracked relationship elements"
    )
    
    # Issue and episode references
    issue_refs: list[str] = Field(default_factory=list, description="Referenced issues")
    episode_ids: list[str] = Field(default_factory=list, description="Episode identifiers")
    
    # Labels - same privacy model as MessageEnrichment
    coarse_labels: list[str] = Field(default_factory=list, description="Cloud-safe labels")
    fine_labels_local: list[str] = Field(
        default_factory=list,
        description="LOCAL-ONLY; MUST NOT be sent to cloud"
    )
    
    # Evidence and confidence
    evidence_index: list[str] = Field(description="Message IDs used as evidence")
    confidence_llm: float = Field(ge=0.0, le=1.0, description="LLM confidence in analysis")
    source: SourceEnum = Field(description="Source of analysis")
    
    # Provenance
    provenance: dict[str, Any] = Field(default_factory=dict, description="Analysis provenance")
    
    @validator('topic_label')
    def validate_topic_length(cls, v):
        word_count = len(v.split())
        if word_count > 6:
            raise ValueError('topic_label must be ≤6 words')
        return v
    
    def set_provenance(self, run_id: str, model_id: str, prompt_hash: str) -> None:
        """Set provenance metadata."""
        self.provenance = {
            "schema_v": "0.1.0",
            "run_id": run_id,
            "model_id": model_id,
            "prompt_hash": prompt_hash,
            "timestamp": datetime.now().isoformat(),
        }
    
    class Config:
        use_enum_values = True


class EnrichmentRequest(BaseModel):
    """Request for message enrichment."""
    
    msg_id: str = Field(description="Message identifier")
    text: str = Field(description="Message text to analyze")
    context: Optional[list[dict[str, Any]]] = Field(
        None, 
        description="Optional context messages (±2 turns)"
    )
    contact: str = Field(description="Contact identifier")
    platform: str = Field(description="Platform (imessage, instagram, etc.)")
    timestamp: datetime = Field(description="Message timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EnrichmentResponse(BaseModel):
    """Response from enrichment processing."""
    
    msg_id: str = Field(description="Message identifier")
    enrichment: Optional[MessageEnrichment] = Field(None, description="Enrichment result")
    error: Optional[str] = Field(None, description="Error message if processing failed")
    processing_time_ms: float = Field(description="Processing time in milliseconds")
    
    @validator('enrichment', 'error')
    def validate_result_xor_error(cls, v, values):
        enrichment = values.get('enrichment')
        error = values.get('error')
        
        # Exactly one of enrichment or error should be set
        if (enrichment is None) == (error is None):
            raise ValueError('Exactly one of enrichment or error must be set')
        
        return v


class BatchEnrichmentRequest(BaseModel):
    """Request for batch message enrichment."""
    
    requests: list[EnrichmentRequest] = Field(description="List of enrichment requests")
    
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Batch identifier")
    
    @validator('requests')
    def validate_non_empty_requests(cls, v):
        if not v:
            raise ValueError('requests cannot be empty')
        return v


class BatchEnrichmentResponse(BaseModel):
    """Response from batch enrichment processing."""
    
    batch_id: str = Field(description="Batch identifier")
    responses: list[EnrichmentResponse] = Field(description="Individual responses")
    total_processing_time_ms: float = Field(description="Total batch processing time")
    success_count: int = Field(description="Number of successful enrichments")
    error_count: int = Field(description="Number of failed enrichments")
    
    @validator('responses')
    def validate_response_consistency(cls, v, values):
        success_count = sum(1 for r in v if r.enrichment is not None)
        error_count = sum(1 for r in v if r.error is not None)
        
        # Update counts based on actual responses
        values['success_count'] = success_count
        values['error_count'] = error_count
        
        return v
