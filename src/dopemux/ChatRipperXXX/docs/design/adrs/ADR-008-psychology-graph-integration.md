# ADR-008: Psychology-Graph Integration Architecture

**Status:** Accepted  
**Date:** 2025-09-04  
**Authors:** Claude Code + Team  
**Supersedes:** N/A  
**Related:** ADR-001 (Local-First Architecture), ADR-003 (Privacy Shield)

## Context

ChatX's forensic chat analysis requires sophisticated understanding of psychological patterns and relationship dynamics over time. Our initial implementation created isolated systems:

- **Psychology Embeddings**: mental/mental-bert-base-uncased model for psychology-aware semantic analysis
- **Neo4j Graph Store**: Temporal relationship modeling with 12 relationship types and 6 pattern types  
- **Label Taxonomy**: 470+ psychology constructs (53 coarse + 100+ fine) from labels.yml

**Critical Gap Identified**: These systems operate independently, preventing sophisticated forensic queries that require integrated psychology-relationship-temporal analysis.

### Forensic Query Requirements Not Supported
- "Show escalation patterns triggered by boundary_consent issues"
- "Find substance_influence correlation with relationship dynamics over time"
- "Cross-reference attention_availability with repair attempt success rates"
- "Build evidence chains: psychological trigger → escalation → resolution patterns"

## Decision

We will implement a **Psychology-Graph Integration Architecture** that unifies psychology embeddings, graph relationships, and temporal analysis into a cohesive forensic analysis system.

### Core Components

#### 1. Psychology Label Mapping System
```python
class PsychologyLabelMapper:
    """Maps 470+ labels.yml constructs to graph relationship types."""
    
    def map_labels_to_relationships(self, psychology_labels: List[str]) -> List[RelationshipType]:
        # Example mappings:
        # "boundary_consent" + escalation context → BOUNDARY_TESTS relationship
        # "attention_availability" + response patterns → RESPONDS_TO relationship
        # "substance_influence_*" + behavioral changes → TRIGGERS relationship
```

#### 2. Psychology-Informed Graph Construction
```python
class PsychologyInformedGraphStore(Neo4jGraphStore):
    """Graph construction weighted by psychology analysis confidence."""
    
    def create_graph(self, chunks: List[ConversationChunk], psychology_analysis: List[PsychologyResult]):
        # Use psychology embeddings to inform relationship detection
        # Include psychology labels as node properties
        # Weight relationship confidence by psychology analysis scores
```

#### 3. Token-Preserving Cloud Reconstruction
```python
class CloudAnalysisReconstructor:
    """Safe cloud analysis with local privacy-preserving reconstruction."""
    
    async def analyze_with_reconstruction(self, chunks: List[ConversationChunk]):
        # 1. Policy Shield redaction with ⟦TKN:PERSON_A⟧ token preservation
        # 2. Cloud LLM analysis on redacted content only
        # 3. Local reconstruction using salt-based token mapping
        # 4. Privacy boundary validation (fine labels remain local)
```

#### 4. Hybrid Query Engine
```python
class HybridPsychologyQueryEngine:
    """Unified queries across ChromaDB + Neo4j with evidence chains."""
    
    async def forensic_query(self, query: str, psychology_context: bool = True):
        # Combine semantic similarity + relationship traversal + temporal patterns
        # Return evidence chains with complete message traceability
```

### Architecture Benefits

1. **Unified Psychology Analysis**: Psychology embeddings inform graph relationship detection
2. **Cloud Enhancement with Privacy**: Cloud LLM expertise while preserving local boundaries
3. **Forensic Evidence Chains**: Complete traceability from trigger → pattern → resolution
4. **Complex Query Support**: Multi-dimensional analysis across semantics + relationships + time

## Implementation Strategy

### Phase 1: Foundation Components
- Psychology Label Mapping System (labels.yml → relationships)
- Psychology-Informed Graph Construction
- Enhanced conversation analysis pipeline

### Phase 2: Advanced Features  
- Token-Preserving Cloud Reconstruction
- Hybrid Query Engine (ChromaDB + Neo4j)
- Privacy boundary validation

### Phase 3: System Integration
- CLI command extensions (`chatx analyze psychology`, `chatx graph`)
- Performance optimization and caching
- Comprehensive testing and validation

## Consequences

### Positive
- **Sophisticated Forensic Capabilities**: Support complex psychology-relationship-temporal queries
- **Privacy-Safe Cloud Processing**: Enhanced analysis while maintaining Policy Shield guarantees
- **Complete Data Traceability**: Evidence chains preserve original message context
- **Scalable Architecture**: Unified system supporting all 470+ psychology constructs

### Negative  
- **Implementation Complexity**: Significant integration work across multiple systems
- **Performance Implications**: Hybrid queries more expensive than single-system queries
- **Testing Complexity**: Privacy boundary validation across integrated components

### Neutral
- **Backward Compatibility**: All existing ChatX interfaces preserved
- **Local-First Principle**: Architecture maintains local processing with optional cloud enhancement

## Privacy Implications

### Enhanced Privacy Controls
- **Token-Preserving Reconstruction**: Cloud analysis without exposing original entities
- **Strict Boundary Enforcement**: Fine psychology labels never leave device
- **Validated Reconstruction**: Automatic privacy boundary checking on all reconstructed results

### Risk Mitigation
- **Comprehensive Testing**: Privacy boundary violation detection throughout system
- **Audit Trails**: Complete provenance tracking for all cloud reconstruction operations
- **Fallback Capability**: Full local-only operation when cloud disabled

## Performance Considerations

### Optimization Strategies
- **Caching Layer**: Frequent psychology queries cached for performance
- **Async Processing**: Non-blocking hybrid query execution
- **Batch Analysis**: Efficient processing of large conversation corpora
- **Memory Management**: Optimized graph structure handling

### Expected Performance
- **Hybrid Queries**: Target <5s response time for typical forensic analysis
- **Psychology Mapping**: Real-time label-to-relationship mapping
- **Cloud Reconstruction**: <2s overhead for token-preserving analysis

## Alternatives Considered

### Alternative 1: Separate Query Systems
**Rejected**: Would not support integrated forensic analysis queries requiring psychology + relationship + temporal context

### Alternative 2: Full Cloud Processing  
**Rejected**: Violates ChatX local-first privacy architecture and Policy Shield requirements

### Alternative 3: Local-Only Analysis
**Rejected**: Limits psychology analysis accuracy compared to cloud LLM capabilities

## Implementation Timeline

- **Phase 1**: 2-3 weeks (Foundation components)
- **Phase 2**: 3-4 weeks (Advanced features) 
- **Phase 3**: 2-3 weeks (System integration)
- **Total**: 7-10 weeks for complete implementation

## Success Metrics

1. **Psychology Integration**: Support all 470+ constructs from labels.yml in graph relationships
2. **Query Capabilities**: Complex multi-dimensional forensic queries functional
3. **Privacy Compliance**: Zero privacy boundary violations in cloud reconstruction
4. **Performance**: Hybrid queries meet <5s response time target
5. **Compatibility**: 100% backward compatibility with existing ChatX interfaces

## Related Decisions

- **ADR-001**: Maintains local-first processing principle
- **ADR-003**: Extends Policy Shield with token-preserving cloud reconstruction
- **Future ADR**: May require decisions on specific cloud provider integrations

---

This ADR establishes the foundation for ChatX's transformation into a world-class forensic psychology analysis platform while preserving its core privacy-first architectural principles.