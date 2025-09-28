# ChatX Psychology Analysis Guide
*Status: Master | Owner: Team | Last Updated: 2025-09-04*

## Overview

ChatX's **Psychology-Graph Integration Architecture** (ADR-008) provides sophisticated forensic chat analysis by combining psychology-specialized embeddings with temporal relationship modeling. This system supports complex forensic queries while maintaining strict privacy boundaries through local-first processing and optional cloud enhancement.

`★ Insight ─────────────────────────────────────`
The psychology analysis system transforms ChatX from a simple chat extraction tool into a world-class forensic psychology platform capable of analyzing complex relationship dynamics, temporal patterns, and behavioral evolution while preserving complete privacy and data traceability.
`─────────────────────────────────────────────────`

## Architecture Components

### 1. Psychology Label Taxonomy

ChatX uses a sophisticated **two-tier label system** defined in `config/labels.yml`:

- **53 Coarse Labels**: Cloud-safe psychological constructs (e.g., `attention_availability`, `boundary_consent`)
- **100+ Fine Labels**: Local-only detailed analysis (e.g., `attention_availability_assertion_direct`)

**Privacy Boundaries:**
- **Coarse labels**: MAY be shared with cloud services after Policy Shield validation
- **Fine labels**: MUST NEVER leave the device under any circumstances

### 2. Psychology-Specialized Embeddings

**Model Selection:**
```python
PSYCHOLOGY_MODELS = {
    "mental/mental-bert-base-uncased": {
        "dimension": 768,
        "description": "BERT trained on mental health texts"
    }
}
```

**Automatic Content Detection:**
- 60+ psychology keywords for content classification
- Automatic switching between psychology and generic models
- Hardware optimization (CPU/MPS/CUDA) integration

### 3. Temporal Graph Relationships

**12 Relationship Types:**
- **Temporal**: `RESPONDS_TO`, `FOLLOWS`, `REFERENCES_BACK`
- **Emotional**: `ESCALATES_FROM`, `REPAIRS_AFTER`, `TRIGGERS`
- **Content**: `PARALLELS`, `CONTRADICTS`, `ELABORATES`
- **Psychology-Specific**: `BOUNDARY_TESTS`, `GASLIGHTS`, `VALIDATES`

**6 Pattern Types:**
- `escalation_cycle`: Escalation→Peak→Resolution patterns
- `repair_cycle`: Harm→Repair→Reconciliation sequences
- `boundary_testing`: Repeated boundary violation attempts
- `gaslighting_sequence`: Systematic gaslighting pattern detection
- `avoidance_pattern`: Conflict avoidance behaviors
- `validation_seeking`: Validation request patterns

## Forensic Query Capabilities

### Complex Multi-Dimensional Queries

**Example 1: Escalation Pattern Analysis**
```python
results = await hybrid_engine.forensic_query(
    "Find escalation patterns triggered by boundary violations",
    psychology_filters=["boundary_consent"],
    relationship_patterns=["escalation_cycle"],
    temporal_analysis=True
)
```

**Example 2: Substance Impact Analysis**
```python
results = await hybrid_engine.forensic_query(
    "Analyze substance influence on communication patterns",
    psychology_filters=["substance_influence_*"],
    relationship_patterns=["TRIGGERS", "ESCALATES_FROM"],
    temporal_window="last_30_days"
)
```

**Example 3: Evidence Chain Reconstruction**
```python
evidence_chain = await hybrid_engine.build_evidence_chain(
    trigger_message="msg_123",
    relationship_path=["ESCALATES_FROM", "REPAIRS_AFTER"],
    include_psychology_context=True,
    preserve_traceability=True
)
```

### Query Result Structure

**Unified Results with Evidence Chains:**
```python
{
    "original_messages": [
        {
            "msg_id": "msg_123",
            "text": "I feel like you never listen to me",
            "timestamp": "2025-09-04T10:30:00Z",
            "psychology_labels_coarse": ["attention_availability"],
            "psychology_labels_fine": ["attention_availability_assertion_direct"]
        }
    ],
    "relationship_context": {
        "pattern_detected": "escalation_cycle",
        "confidence": 0.87,
        "temporal_span": "2 minutes",
        "psychology_transitions": ["attention_to_boundary_pushback"]
    },
    "evidence_chain": [
        {"step": 1, "trigger": "attention_availability", "message": "msg_123"},
        {"step": 2, "escalation": "boundary_pushback", "message": "msg_124"},
        {"step": 3, "resolution": "repair_attempt", "message": "msg_125"}
    ]
}
```

## Cloud Reconstruction Strategy

### Token-Preserving Privacy Architecture

**Safe Cloud Processing Flow:**
```python
# 1. Local redaction with token preservation
original: "I feel like John never listens to me"
redacted: "I feel like ⟦TKN:PERSON_A⟧ never listens to me"

# 2. Cloud analysis on redacted content
cloud_result = {
    "psychology_labels": ["attention_availability"],
    "relationship_context": "⟦TKN:PERSON_A⟧ shows dismissive pattern",
    "confidence": 0.85
}

# 3. Local reconstruction with original context
final_result = {
    "psychology_labels": ["attention_availability"],
    "relationship_context": "John shows dismissive pattern",
    "confidence": 0.85,
    "privacy_preserved": True
}
```

### Privacy Boundary Enforcement

**What Gets Reconstructed (SAFE):**
- ✅ Entity references: `⟦TKN:PERSON_A⟧` → `John`
- ✅ Psychology patterns with token placeholders
- ✅ Relationship analysis with local context
- ✅ Confidence scores enhanced with local data

**What Never Leaves Device (PROTECTED):**
- ❌ Fine psychology labels (remain local-only)
- ❌ Explicit content details
- ❌ Attachment content
- ❌ Raw message text reconstruction beyond tokens

## Implementation Phases

### Phase 1: Foundation (Current)
- ✅ Psychology embedding provider implementation
- ✅ Neo4j graph store with relationship types
- ✅ Base data structures and interfaces
- ✅ Comprehensive test coverage

### Phase 2: Core Integration (In Development)
- 🔄 Label mapping system (470+ constructs → relationships)
- 🔄 Psychology-informed graph construction
- 🔄 Conversation analysis pipeline enhancement

### Phase 3: Advanced Features (Planned)
- ⏳ Token-preserving cloud reconstruction
- ⏳ Hybrid query engine (ChromaDB + Neo4j)
- ⏳ Privacy boundary validation system

### Phase 4: System Integration (Planned)
- ⏳ CLI command extensions
- ⏳ Performance optimization and caching
- ⏳ End-to-end forensic workflow testing

## Performance Characteristics

### Target Metrics
- **Hybrid Queries**: <5s response time for typical forensic analysis
- **Psychology Detection**: Real-time content classification
- **Graph Construction**: Efficient relationship detection at scale
- **Cloud Reconstruction**: <2s overhead for token-preserving analysis

### Optimization Strategies
- **Caching**: Frequent psychology query results cached locally
- **Batch Processing**: Efficient large-scale conversation analysis
- **Async Operations**: Non-blocking hybrid query execution
- **Memory Management**: Optimized graph structure handling

## Privacy & Security

### Local-First Guarantees
- **Complete Local Analysis**: Full functionality without cloud services
- **Fine Label Protection**: Detailed psychology analysis never leaves device
- **Source Preservation**: Original message content always accessible
- **Audit Trails**: Complete provenance tracking for all analysis

### Cloud Enhancement (Optional)
- **Explicit Consent**: Cloud processing requires `--allow-cloud` flag
- **Token Preservation**: Entity anonymization with local reconstruction
- **Boundary Validation**: Automated privacy violation detection
- **Fallback Capability**: Seamless degradation to local-only analysis

## Clinical and Forensic Applications

### Relationship Pattern Analysis
- **Escalation Cycle Detection**: Identify triggers, peaks, and resolution patterns
- **Repair Attempt Effectiveness**: Analyze reconciliation success rates
- **Boundary Violation Patterns**: Track consent and boundary dynamics
- **Communication Style Evolution**: Monitor relationship communication changes

### Forensic Evidence Construction
- **Timeline Reconstruction**: Build accurate temporal sequences
- **Pattern Correlation**: Link psychological states to behavioral outcomes  
- **Context Preservation**: Maintain original message context throughout analysis
- **Expert Testimony Support**: Provide data-driven insights for forensic analysis

### Research Applications
- **Longitudinal Studies**: Track relationship dynamics over extended periods
- **Pattern Recognition**: Identify recurring psychological and behavioral patterns
- **Privacy-Safe Analytics**: Conduct research while protecting individual privacy
- **Cross-Platform Analysis**: Unified analysis across multiple communication platforms

---

This psychology analysis system transforms ChatX into a sophisticated forensic psychology platform while maintaining its core privacy-first architecture and local-first processing principles.