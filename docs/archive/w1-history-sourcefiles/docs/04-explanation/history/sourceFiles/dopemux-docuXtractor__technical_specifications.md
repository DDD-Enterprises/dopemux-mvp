# DocuXtractor Technical Specifications

**Source**: Deep analysis of Dopemux 11-pattern document processing system
**Date**: 2025-09-23
**Status**: Implementation-ready technical specifications

## Complete 8-Stage Processing Pipeline

### End-to-End Document Architecture System
```
Input Files → Inventory → Multi-Pass → AtomicUnits → Embed/Index → Registries → Doc Fusion → Validation → Reports
     ↓           ↓          ↓            ↓            ↓             ↓            ↓           ↓          ↓
  Multi-type  Fingerprint  Structure   Normalize    Vector DB    5 TSV Files  Gap Fill   Quality    9 Output
  Sources     + Convert    Detection   + Metadata   + Dedupe     + Evidence   + Merge    Gates      Types
```

### Stage 0: Inventory and Fingerprinting
**File Crawling**: Store path, SHA256, size, mtime, detected format, charset
**Format Conversion**: pdf/docx → md, normalize headings and line endings
**Manifest Generation**: build/manifest.tsv with one row per file

### Stage 1-3: Multi-Pass Extraction → AtomicUnits
**Pass A**: Document type detection (ADR, RFC, arc42 §1-12, C4, Diátaxis)
**Pass B**: Entity extraction with exact source line ranges
**Pass C**: Cross-document relation linking with IDs and near-title matches

### Stage 4-5: Vector Processing → Registry Generation
**Embedding Strategy**: Chunk by structure (not tokens), contextualized with Voyage
**Deduplication**: Cosine ≥0.92, keep newest + most specific
**5 Specialized Registries**: Features, Components, Subsystems, Research, Evidence_Links

### Stage 6-8: Document Fusion → Quality Validation → Report Generation
**Gap Fill Algorithm**: Query vector index → re-rank → dedupe → select winners
**Conflict Resolution**: Newer + specific wins, formal conflict register
**9 Output Types**: Updated docs + 8 analysis reports with full provenance

### Phase 1: Document Discovery
**Entry Point**: `DocumentProcessor.analyze_directory()`
**File Types**: `.md`, `.txt`, `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.html`, `.css`, `.yml`, `.yaml`, `.json`, `.toml`, `.rst`, `.adoc`, `.org`, `.tex`
**Exclusions**: `node_modules`, `.git`, `__pycache__`, `venv`, `env`, `build`, `dist`, `.next`, `.nuxt`, `target`
**ADHD Optimization**: Process 25 files per chunk with progress feedback

### Phase 2: Precision Chunking Strategy (Content-Type Aware)

**Token-Based Sizing** (tokens, not characters):
- **General docs/specs**: 300–500 tokens
- **Technical/code/config blocks & logs**: 120–250 tokens
- **Long narrative/background sections**: 400–700 tokens
- **Coalesced target range**: 260–720 tokens (typical outcome: 250–450)

**Voyage Token Estimation**:
- ~5 characters per token (Voyage-specific)
- ~1.1–1.2× tiktoken estimates
- Use Voyage tokenizer for precise budgeting

**Document Type-Specific Processing**:

#### A) Markdown Docs (RFCs, ADRs, specs, overviews, roadmaps)
- **Splitter**: Heading-aware (H1→H3 boundaries)
- **Preserve**: Fenced blocks and lists as atomic units
- **Size**: ~800–1,200 tokens; min 200; max 1,600
- **Overlap**: 80–120 tokens (only across prose, not through code/table fences)
- **Metadata**: doc_type, id (RFC-001, ADR-005), status, created, updated, section_path

#### B) Tables & Checklists (roadmaps, ADHD matrices)
- **As-table chunk**: Embed whole table once
- **Row cards**: Generate normalized row strings ("State=Scattered | Interface=Simplified | Info=Essential only")
- **Metadata**: table_headers, row_index
- **Benefit**: Huge recall boost for pinpoint queries

#### C) Code Blocks & Fenced Configs (YAML/JSON/Mermaid)
- **Keep intact**: Each fenced block as own chunk
- **Add paraphrase**: Short textual description for natural-language queries
- **Configs**: Flatten to path.to.key: value lines, chunk by top-level key
- **Size**: 120–250 tokens for function/block-level precision

#### D) Session-State & Continuity Files
- **Don't embed raw logs**: Use state snapshots and diff summaries instead
- **Metadata**: session_id, ts, layer, repo, instance
- **Focus**: Immediate/Working/Session layers as documented
**Enhanced Chunk Structure**:
```python
{
    "id": f"{file_path.stem}_chunk_{i}",
    "content": coalesced_chunk_text,
    "token_count": estimated_tokens,
    "title": file_path.name,
    "source_file": str(file_path),
    "doc_type": inferred_type,  # markdown, python, javascript, etc.
    "section_path": "H1 › H2 › H3",  # Hierarchical heading path
    "chunk_type": "literal",  # literal | summary | table | code | config
    "metadata": {
        "chunk_index": i,
        "file_size": file_path.stat().st_size,
        "modified_time": file_path.stat().st_mtime,
        "original_sections": [section_ids],  # Before coalescing
        "heading_level": max_heading_depth,
        "contains_code": boolean,
        "contains_table": boolean
    }
}
```

## 11-Pattern Extraction System

### Exact Regex Patterns (Extracted from Dopemux)
```python
EXTRACTION_PATTERNS = {
    "features": r"(?:feature|capability|functionality):\s*([^.\n]+)",
    "components": r"(?:component|module|class|service):\s*([^.\n]+)",
    "subsystems": r"(?:subsystem|system|domain|layer):\s*([^.\n]+)",
    "requirements": r"(?:requirement|must|should|shall):\s*([^.\n]+)",
    "decisions": r"(?:decision|chosen|selected|opted):\s*([^.\n]+)",
    "constraints": r"(?:constraint|limitation|restriction):\s*([^.\n]+)",
    "patterns": r"(?:pattern|approach|strategy|method):\s*([^.\n]+)",
    "technologies": r"(?:using|with|technology|framework|library):\s*([A-Za-z0-9.-]+)",
    "interfaces": r"(?:interface|API|endpoint):\s*([^.\n]+)",
    "processes": r"(?:process|workflow|procedure|steps):\s*([^.\n]+)",
    "metrics": r"(?:metric|measure|KPI|target):\s*([^.\n]+)"
}
```

### Confidence Scoring Algorithm
```python
def calculate_confidence(entity_text: str, content: str) -> float:
    base_confidence = 0.7

    # Boost for important context keywords
    important_keywords = ["important", "critical", "key", "main"]
    if any(keyword in content.lower() for keyword in important_keywords):
        base_confidence += 0.1

    # Boost for multiple occurrences
    occurrence_count = content.lower().count(entity_text.lower())
    if occurrence_count > 1:
        base_confidence += min(0.2, occurrence_count * 0.05)

    # Penalize short or generic terms
    generic_terms = ["test", "data", "info", "item"]
    if len(entity_text) < 5 or entity_text.lower() in generic_terms:
        base_confidence -= 0.2

    return max(0.1, min(1.0, base_confidence))
```

### Entity Structure
```python
{
    "id": f"{pattern_name}_entity_{index}",
    "name": extracted_text.strip(),
    "description": context_description,  # Generated from surrounding text
    "source_file": atomic_unit.source_file,
    "source_unit": atomic_unit.id,
    "doc_type": atomic_unit.doc_type,
    "confidence": calculated_score,
    "context": surrounding_text_window,  # ±100 characters
    "metadata": {
        "pattern_type": pattern_name,
        "extraction_method": "regex",
        "file_path": atomic_unit.source_file,
        "unit_title": atomic_unit.title
    }
}
```

## Embedding & Vector Operations

### Voyage AI Contextualized Integration
**Model**: `voyage-context-3` with contextualized embeddings
**Dimensions**: 1024 (512 for cost-saving, 2048 for max recall)
**Context Length**: 32,000 tokens per model call
**Batch Limits**: ≤1,000 inputs, ≤120k total tokens, ≤16k chunks per call

**Contextualized Embedding Strategy**:
- **Document Mode**: Group chunks by document in nested lists
- **Query Mode**: Single query in single-item list
- **Zero Overlap**: Context-3 adds global document context automatically
- **Order Preservation**: Pass chunks in document order for context

**API Usage Pattern**:
```python
# For indexing documents (contextualized)
# Group chunks by document in nested structure
documents = {}
for chunk in processed_chunks:
    doc_id = chunk['source_file']
    documents.setdefault(doc_id, []).append(chunk['content'])

# Create nested input structure: [[doc1_chunks], [doc2_chunks], ...]
inputs = [chunks for doc_id, chunks in sorted(documents.items())]

response = client.contextualized_embed(
    inputs=inputs,  # List of lists (per-document chunk groups)
    model="voyage-context-3",
    input_type="document",
    dimensions=1024,
    output_dtype="float"  # int8/uint8 for compression, binary for extreme scale
)

# For search queries (contextualized)
query_embedding = client.contextualized_embed(
    inputs=[[query_text]],  # Single query in single-item list
    model="voyage-context-3",
    input_type="query",
    dimensions=1024
).embeddings[0][0]
```

**API Batching Constraints**:
- **Per request limits**: ≤1,000 inputs, ≤120k total tokens, ≤16k chunks total
- **Model context**: 32k tokens per call
- **Order preservation**: Pass chunks in document order within each inner list
- **Token estimation**: ~5 chars/token (Voyage-specific), ~1.1-1.2× tiktoken

**Production-Ready Code Pattern**:
```python
from voyageai import Client
import json

client = Client(api_key="YOUR_VOYAGE_API_KEY")

# Group chunks by document in nested structure for contextualized embedding
documents = {}
for chunk in processed_chunks:
    doc_id = chunk['source_file']
    documents.setdefault(doc_id, []).append(chunk['content'])

# Create nested input: [[doc1_chunks], [doc2_chunks], ...]
inputs = [chunks for doc_id, chunks in sorted(documents.items())]

# Batch processing under limits
batch_size = min(1000, 120000 // max_tokens_per_chunk)
for batch in batch_inputs(inputs, batch_size):
    emb = client.contextualized_embed(
        inputs=batch,
        model="voyage-context-3",
        input_type="document",
        dimensions=1024,
        output_dtype="float"  # int8/uint8 for compression
    )
    # emb.embeddings is list of lists (per-doc, per-chunk vectors)
```

### Vector Database Schema (for Zilliz Cloud)
**Collection Name**: `document_units`
**Enhanced Schema**:
```python
{
    "fields": [
        {"name": "id", "type": "VarChar", "max_length": 255, "is_primary": True},
        {"name": "vector", "type": "FloatVector", "dim": 1024},
        {"name": "doc_id", "type": "VarChar", "max_length": 255},        # RFC-001, ADR-005
        {"name": "doc_type", "type": "VarChar", "max_length": 100},      # RFC|ADR|spec|overview|roadmap|guide
        {"name": "section_path", "type": "VarChar", "max_length": 500},  # "Summary > Motivation > Architecture"
        {"name": "title", "type": "VarChar", "max_length": 500},
        {"name": "content", "type": "VarChar", "max_length": 65535},
        {"name": "hash", "type": "VarChar", "max_length": 64},           # SHA256 for dedup
        {"name": "chunk_index", "type": "Int64"},
        {"name": "status", "type": "VarChar", "max_length": 50},         # Proposed|Accepted|Deprecated
        {"name": "created", "type": "VarChar", "max_length": 50},        # ISO8601 timestamp
        {"name": "updated", "type": "VarChar", "max_length": 50},        # ISO8601 timestamp
        {"name": "kind", "type": "VarChar", "max_length": 50},           # literal|summary|table|row-card|diagram|config
        {"name": "file_path", "type": "VarChar", "max_length": 1000},
        {"name": "tags", "type": "VarChar", "max_length": 2000},         # JSON array as string
        {"name": "ts_range", "type": "VarChar", "max_length": 100},      # For session states
    ]
}
```

**Metadata Filtering Fields** (optimized for fast narrowing):
- `doc_type`, `doc_id`, `status`, `created`, `updated`
- `section_path`, `kind`, `tags`
- `chunk_index`, `hash` (for deduplication)

**Optimized Index Configuration**:
```python
{
    "index_type": "HNSW",
    "metric_type": "COSINE",  # or IP (equivalent for unit-normalized vectors)
    "params": {
        "M": 24,                  # Graph degree (16-32 range)
        "efConstruction": 320,    # Build-time search width
        "ef": 128                 # Query-time search width
    }
}
```

**Search Pipeline**:
- **Stage 1**: ANN top-K (200) with Zilliz Cloud HNSW
- **Stage 2**: voyage-rerank-2.5 reranking of candidates
- **Stage 3**: Return top 8-12 to LLM (ADHD-optimized count)
- **Similarity Metric**: Cosine (vectors are unit-normalized)
- **efSearch**: 64-200 for speed/recall tradeoff

**Reranking Integration**:
```python
# Stage 1: Vector similarity search
vector_results = collection.search(
    data=[query_embedding],
    anns_field="vector",
    param={"metric_type": "COSINE", "ef": 128},
    limit=200
)

# Stage 2: Rerank with voyage-rerank-2.5
rerank_response = client.rerank(
    query=query_text,
    documents=[result.entity.get('content') for result in vector_results[0]],
    model="rerank-2.5",
    top_k=12  # ADHD-friendly result count
)

# Stage 3: Return reranked results
final_results = rerank_response.results[:12]
```

**Storage Optimization**:
- Default: float (highest accuracy)
- Storage-optimized: int8/uint8 (~75% memory reduction)
- Extreme scale: binary (~97% memory reduction)

### Advanced Document Processing Patterns

**Multi-Pass Extraction Strategy**:

#### Pass A: Advanced Document Type Detection
```python
DOCUMENT_TYPE_PATTERNS = {
    "ADR": ["Status", "Context", "Decision", "Consequences", "Date", r"ADR-\d+"],
    "RFC": ["Abstract", "Motivation", "Specification", "Rationale", "Security Considerations"],
    "arc42": {
        "1": ["Introduction", "Requirements", "Context"],
        "2": ["Architecture Constraints", "Constraints"],
        "3": ["Solution Strategy", "Strategy"],
        "4": ["Building Block", "Whitebox", "Blackbox"],
        "5": ["Runtime", "Behavior", "Scenarios"],
        "6": ["Deployment", "Infrastructure"],
        "7": ["Cross-cutting", "Concepts"],
        "8": ["Architecture Decision", "Decisions"],
        "9": ["Quality", "Requirements"],
        "10": ["Risk", "Technical Debt"],
        "11": ["Technical Debt"],
        "12": ["Glossary"]
    },
    "C4": {
        "code_fence_tokens": ["System", "Container", "Component", "Person", "Rel"],
        "plantuml_markers": ["@startuml", "@enduml"],
        "mermaid_markers": ["```mermaid", "```"]
    },
    "Diátaxis": ["Tutorial", "How-to", "Reference", "Explanation"],
    "Feature": ["Feature", "Epic", "Capability", "User Story", "Acceptance Criteria"]
}
```

#### Pass B: Sophisticated Entity Extraction
```python
ENTITY_TYPES = {
    "Decision": r"(?:decision|chosen|selected|opted|concluded):\s*([^.\n]+)",
    "Requirement": r"(?:requirement|must|should|shall|will):\s*([^.\n]+)",
    "Interface": r"(?:interface|API|endpoint|contract):\s*([^.\n]+)",
    "Risk": r"(?:risk|threat|vulnerability|concern):\s*([^.\n]+)",
    "QualityScenario": r"(?:performance|scalability|availability|security):\s*([^.\n]+)",
    "SLI": r"(?:SLI|indicator|metric|measurement):\s*([^.\n]+)",
    "SLO": r"(?:SLO|objective|target|threshold):\s*([^.\n]+)",
    "Code": r"```[\w]*\n(.*?)\n```",
    "Diagram": r"(?:diagram|chart|visualization):\s*([^.\n]+)",
    "Table": r"\|.*\|\n\|[-\s\|]+\|\n(?:\|.*\|\n)+",
    "Para": r"^[A-Z][^.\n]*\."  # Paragraph starting with capital letter
}
```

#### Pass C: Relation Detection and Cross-Linking
```python
RELATION_PATTERNS = {
    "supersedes": [r"supersedes?\s+([A-Z]{3}-\d+)", r"replaces?\s+([A-Z]{3}-\d+)"],
    "duplicates": [r"duplicate\s+of\s+([A-Z]{3}-\d+)", r"same\s+as\s+([A-Z]{3}-\d+)"],
    "depends_on": [r"depends?\s+on\s+([A-Z]{3}-\d+)", r"requires?\s+([A-Z]{3}-\d+)"],
    "supports": [r"supports?\s+([A-Z]{3}-\d+)", r"enables?\s+([A-Z]{3}-\d+)"],
    "contradicts": [r"conflicts?\s+with\s+([A-Z]{3}-\d+)", r"contradicts?\s+([A-Z]{3}-\d+)"]
}
```

**Complete AtomicUnit Data Structure**:
```python
{
    "unit_id": "sha256:...",                    # SHA256 hash for unique identification
    "doc_uri": "repo/path/file.md",             # Full repository path
    "doc_type": "ADR|RFC|Feature|arc42|C4|Dia", # Document classification
    "section_path": ["5 Building Blocks", "5.1 Ledger"], # Hierarchical section path
    "entity_type": "Decision|Interface|Risk|QualityScenario|SLI|SLO|Code|Diagram|Table|Para",
    "title": "...",                            # Section or entity title
    "text": "normalized text or fenced code",    # Content with preserved formatting
    "created_at": "ISO8601 or mtime",          # Creation timestamp
    "effective_date": "ISO8601|null",          # When decision/requirement takes effect
    "status": "Proposed|Accepted|Deprecated|Superseded|null", # Lifecycle status
    "related_ids": ["ADR-001", "RFC-002"],     # Cross-references to other units
    "source_lines": [start, end],             # Exact line ranges for traceability
    "checksum": "sha256",                      # Content hash for change detection
    "glossary_expansions": ["SLI=Service Level Indicator"], # Expanded acronyms
    "tags": ["arc42:5", "c4:component", "adr:0102"] # Classification tags
}
```

**Normalization Rules**:
- **Acronym expansion**: Use glossary for first occurrence expansions
- **Content preservation**: Keep code, tables, diagrams intact (no wrapping)
- **Formatting**: Strip trailing spaces, preserve list/code indentation
- **Line tracking**: Maintain exact source line ranges for provenance

**Hybrid Search Architecture**:
- **Dense Vector Search**: voyage-context-3 embeddings for semantic similarity
- **Sparse BM25 Search**: Full-text search for exact field names and terminology
- **Combined Scoring**: Hybrid dense + sparse ranking in Milvus 2.5+
- **Deduplication**: Cosine ≥ 0.92 threshold for duplicate detection

### Provenance Tracking and Conflict Resolution

**Inline Provenance Markers**:
```html
<!-- provenance: {"source":"docs/rfcs/0031-ledger-export.md", "lines":"120-210", "date":"2025-09-22", "confidence":0.86, "reason":"fills arc42 §5.2 responsibilities"} -->
```

**TODO Stub Format** (for gaps):
```markdown
TODO[C4-L1-Context]:
scope: external systems A, B, C
must include: actors, primary data flows, trust boundaries
owner: Platform team
due_by: 2025-10-05
```

**Conflict Resolution Policy**:
1. **Newer and Specific Wins**: Prefer recent, detailed sources over old/generic
2. **Template Alignment**: Prefer arc42/ADR structured documents
3. **Conflict Register**: Record unresolved conflicts with alternatives
```python
{
    "conflict_id": "interface_definition_mismatch",
    "area": "Component API specification",
    "options_chosen": "winner_source_id",
    "rationale": "More recent and includes security considerations",
    "alternatives": ["older_source_id"],
    "disposition": "resolved|escalated|deferred",
    "owner": "platform_team"
}
```

**Quality Gates & Guardrails**:
- **Coverage**: ≥95% of section needs satisfied or TODO-stubbed with concrete acceptance criteria
- **Consistency**: Zero unresolved contradictions across interfaces and decisions
- **Citations**: 100% of claims have file/line provenance with confidence scores
- **SRE Compliance**: Each component has SLI/SLO pair and error budget reference
- **Security**: Threat model summary for security-relevant components
- **Style**: No orphan acronyms, active voice, normalized headings

**Deduplication & Near-Duplicate Detection**:
- **Cosine similarity threshold**: ≥0.92 for duplicate detection
- **SimHash/MinHash**: Jaccard threshold ≥0.82 for near-duplicates
- **Specificity scoring**: Weights on presence of IDs (0.3), numbers (0.2), code/tables (0.3), section depth (0.2)
- **Winner selection**: Keep newer and most specific version
- **Cross-document dedup**: Drop or merge repeated status blocks

**Type-Aware Query Boosting**:
- **Query contains "why/decision/consequence"** → boost ADR Decision/Consequences sections
- **"roadmap/milestone" queries** → boost roadmap checklists and project planning docs
- **"how to search/API/technical" queries** → boost reference documentation and implementation guides
- **Section pinning**: Prepend ADR/RFC Summary/Decision chunks for relevant query types

**Document Fusion Algorithm** (6 Steps per Target Section):
1. **Build "Needs" checklist** for each arc42 section:
   - §1 Context: goals, stakeholders, scope, constraints
   - §5 Building blocks: subsystem map, components, responsibilities
   - §8 Cross-cutting: security, performance, observability, configuration
   - §9 Quality requirements: SLIs, SLOs, error budgets, test scenarios
   - §10 Risks: risk list with mitigations and owners

2. **Query vector index** with structured prompts: [section] + [entity types] + [domain terms]
3. **Re-rank top-k** by recency and specificity scores
4. **Deduplicate and select winners** using conflict resolution policy
5. **Insert with provenance markers**:
   ```html
   <!-- provenance: {source:"docs/rfcs/0031.md", lines:"120-210", date:"2025-09-22", confidence:0.86} -->
   ```
6. **Create TODO stubs** for gaps:
   ```markdown
   TODO[C4-L1-Context]:
   scope: external systems A, B, C
   must_include: actors, primary data flows, trust boundaries
   owner: Platform team
   due_by: 2025-10-05
   ```

**Evaluation & Testing Framework**:
- **Build ~40 targeted test prompts** for quality validation:
  - "Why [technology] over alternatives?" → must hit RFC Summary/Goals quickly
  - "What is [ADR-ID]'s decision/consequences?" → must retrieve specific ADR sections
  - "How does [component] work?" → hit implementation docs + architecture decisions

## Complete Output System (9 Output Types)

### Repository Layout Structure
```
/docs
  /arc42/{01-context,...,12-glossary}.md     # Normalized architecture documentation
  /diataxis/{tutorials,how-to,reference,explanation}/...  # Documentation framework
  /adr/ADR-0001.md                           # Architecture Decision Records
  /rfcs/RFC-0001.md                          # Request for Comments
  /c4/{context.puml,containers.puml,components/*.puml}   # C4 diagrams
  /research/spikes/*.md                      # Research and experiments

/build
  atomic_units.jsonl                         # All extracted units
  catalog/{features.tsv,components.tsv,subsystems.tsv,research.tsv,evidence_links.tsv}
  reports/{gap_map.tsv,traceability.tsv,change_log.md,conflicts.tsv,open_questions.tsv,quality.md}
```

### 9 Complete Output Types

1. **UPDATED_DOCS**: Normalized documents with provenance markers
2. **GAP_MAP**: Missing requirements and ownership assignments
3. **TRACEABILITY_LEDGER**: Full audit trail of content sources
4. **CHANGE_LOG**: PR-style changelog with evidence
5. **CONFLICT_REGISTER**: Unresolved conflicts with alternatives
6. **OPEN_QUESTIONS**: Action items requiring decisions
7. **QUALITY_REPORT**: Coverage metrics and compliance scores
8. **5 TSV Registries**: Features, Components, Subsystems, Research, Evidence_Links
9. **SQLite Catalog**: Optional queryable database

### Advanced Registry System (5 Specialized TSV Files)

#### 1. Features Registry (`features.tsv`)
```tsv
feature_id	title	type	status	priority	owner	subsystem_ids	component_ids	description	acceptance_criteria	non_goals	risk	level_of_effort	story_points	target_release	rfc_ids	adr_ids	source_uri	source_lines	created_at	updated_at	tags
```
**Detection**: Feature|Epic|Capability headings, Gherkin, Acceptance Criteria, Non-Goals blocks
**Enrichment**: Link to ADRs/RFCs, extract owner from PRD/CODEOWNERS

#### 2. Components Registry (`components.tsv`)
```tsv
component_id	name	subsystem_id	container_name	purpose	public_interfaces	data_owned	dependencies	tech_stack	repo	owner	slo_availability	slo_latency	sli_metrics	alerts	security_notes	threat_model_refs	adr_ids	rfc_ids	source_uri	source_lines	created_at	updated_at	tags
```
**Detection**: C4 code blocks, ADR text for "Service|Module|Adapter|Gateway"
**Enrichment**: Extract interfaces from OpenAPI/gRPC, data schemas, SLO metrics

#### 3. Subsystems Registry (`subsystems.tsv`)
```tsv
subsystem_id	name	domain	description	containers	owning_team	upstream	dependent_on	data_stores	events	rto	rpo	sla	external_interfaces	security_posture	owner	adr_ids	rfc_ids	source_uri	source_lines	created_at	updated_at	tags
```
**Detection**: arc42 §5 headings, diagram groupings, bounded context phrases

#### 4. Research Registry (`research.tsv`)
```tsv
research_id	title	research_type	status	author	date_collected	recency_days	source_quality	sample_size	method	claim_summary	key_findings	key_metrics	limitations	risks	recommendation	confidence	score_breakdown	sources	source_uri	source_lines	tags	use_by
```
**Detection**: Hypothesis, Method, Dataset, Findings, Limitations, Recommendation blocks
**Enrichment**: Parse metrics (throughput, latency, error rate), create support/contradiction links

#### 5. Evidence Links Registry (`evidence_links.tsv`)
```tsv
from_id	from_type	to_id	to_type	relation	rationale	confidence	source_uri	source_lines	created_at	tags
```
**Relation Types**: supports|informs|contradicts|risks|mitigates|requires|supersedes|duplicates

**Column Definitions**:
- `id`: Unique identifier (e.g., "feature_1", "component_15")
- `name`: Extracted entity name/text
- `description`: Context-aware description generated from surrounding text
- `source_file`: Full path to originating file
- `source_unit`: Atomic unit identifier
- `doc_type`: File type (python, markdown, javascript, etc.)
- `confidence`: Confidence score (0.1 to 1.0)
- `context`: Surrounding text (±100 character window)
- `entity_type`: Pattern type (features, components, etc.)
- `extraction_method`: "regex" for pattern-based extraction
- `metadata`: JSON object with additional extraction details

### Evidence Links Schema
```tsv
id	entity_type	entity_id	entity_name	source_type	source_id	source_file	link_type	confidence	metadata
```

**Link Types**:
- `extraction_source`: Entity extracted from atomic unit
- `co_occurrence`: Entities found in same file/unit
- `semantic_similarity`: Entities with similar embeddings

## ADHD-Optimized UX Patterns

### Progress Visualization
- **Rich Console**: Colorized output with progress bars
- **Visual Indicators**: ✅ ⚠️ 🔄 ⏳ for status
- **Gentle Feedback**: Encouraging messages every 10 files
- **Break Suggestions**: After 25-minute processing chunks

### Batch Processing Sizes
- **File Processing**: 25 files per batch (Pomodoro-aligned)
- **Entity Extraction**: All patterns per atomic unit
- **Embedding Generation**: 50 units per Voyage AI batch
- **Vector Storage**: Batch inserts to Zilliz Cloud

### State Persistence
**Checkpoint Data**:
```python
{
    "session_id": unique_identifier,
    "start_time": timestamp,
    "current_phase": "discovery|processing|extraction|embedding|output",
    "files_processed": count,
    "entities_extracted": count,
    "current_batch": index,
    "cost_tracking": {
        "voyage_ai": dollars_spent,
        "zilliz_cloud": dollars_spent,
        "total": dollars_spent
    },
    "processing_stats": {
        "files_discovered": count,
        "atomic_units_created": count,
        "features_extracted": count,
        "components_identified": count,
        # ... other pattern counts
    }
}
```

## Configuration Management

### Config File Structure (`config.yaml`)
```yaml
version: "1.0"

api_keys:
  voyage_ai: "encrypted:AAAAABh..."
  zilliz_cloud: "encrypted:AAAAABh..."

services:
  voyage:
    model: "voyage-context-3"
    batch_size: 50
    rate_limit: 1000
  zilliz:
    uri: "https://xxx.vectordb.zilliz.com"
    collection: "docuxtractor_vectors"

preferences:
  default_budget: 5.00
  batch_size: 25
  adhd_mode: true
  break_intervals: 1500  # 25 minutes in seconds

processing:
  file_extensions: [".py", ".md", ".js", ".ts", ".html"]
  exclude_patterns: ["*/node_modules/*", "*/.git/*", "*/__pycache__/*"]
  output_format: "tsv"
  max_content_length: 2000
```

### Cross-Platform Config Paths
- **Unix/macOS**: `~/.config/docuxtractor/config.yaml`
- **Windows**: `%APPDATA%/docuxtractor/config.yaml`
- **Project Override**: `.docuxtractor/config.yaml`

## Implementation Priority Order

### Phase 1: Core Extraction Engine
1. **Pattern Definitions**: Implement all 11 regex patterns
2. **Confidence Scoring**: Port exact algorithm from Dopemux
3. **Atomic Unit Processing**: Document → sections → units
4. **Entity Extraction**: Apply patterns to atomic units

### Phase 2: Cloud Service Integration
1. **API Key Management**: Encrypted storage and validation
2. **Voyage AI Client**: Embedding generation with batch processing
3. **Zilliz Cloud Setup**: Collection creation and schema management
4. **Cost Tracking**: Real-time monitoring and budget alerts

### Phase 3: CLI Interface
1. **Click Framework**: Command structure and argument parsing
2. **Rich Console**: Progress visualization and ADHD-friendly output
3. **Setup Wizard**: Interactive API key collection and validation
4. **Processing Commands**: Main workflow with state persistence

### Phase 4: Quality & Testing
1. **Unit Tests**: Core algorithms and data structures
2. **Integration Tests**: API mocking and service interactions
3. **End-to-End Tests**: Complete workflows with real services
4. **ADHD UX Validation**: Break reminders and progress clarity

## LLM Runbook Prompts (Production-Ready)

### A) Section and Type Detection
```
You are a deterministic extractor. Input is a single Markdown document.
Task: Emit JSONL of AtomicUnits with doc_type, entity_type, title, section_path, text, and exact source line ranges.
Rules:
- Detect ADR, RFC, arc42 sections 1–12, C4 code blocks, Diátaxis buckets.
- Entities include Decision, Requirement, Interface, Risk, QualityScenario, SLI, SLO, Code, Diagram, Table, Para.
- Keep code and tables intact.
- Expand acronyms on first use using this glossary: <paste glossary>.
- Output only valid JSONL, one unit per minimal complete block.
```

### B) Relation Linking
```
Input: AtomicUnits JSONL. Task: link related units across files.
Emit JSON lines: {from_unit_id, relation, to_unit_id, rationale}.
Relations: supersedes, duplicates, depends_on, supports, contradicts.
Use titles, IDs (ADR-###, RFC-###), and near-string matches.
```

### C) Research Registry Builder
```
Input: AtomicUnits likely to be research (spike, benchmark, interview, market).
Task: Emit rows for research.tsv and evidence_links.tsv.
Extract claim_summary, method, key_findings, key_metrics, limitations, recommendation.
Infer research_type and confidence. Link to ADRs, Components, Features by tokens and proximity.
Never overwrite specs. Suggest addenda patches instead.
```

### D) Gap Fill for Target Section
```
Input: target section name and Needs checklist.
Task: Query the vector index with combined keywords and entity hints. Re-rank by recency and specificity.
Select winners, dedupe, and produce a merged block. Provide provenance for each kept block and list discards with reasons.
Emit:
- merged_markdown
- kept_sources[]
- discarded_sources[] with reasons
- remaining_todos[] with acceptance criteria
```

### E) Conflict Resolution
```
Input: two or more conflicting passages for the same fact.
Task: Choose a winner using policy: newer and more specific wins. Prefer template-aligned docs.
Emit: winner_id, loser_ids[], rationale, alternatives_summary, recommended_default, add CONFLICT_REGISTER row.
```

## arc42, C4, Diátaxis Mapping Framework

### arc42 Architecture Documentation (§1-12)
- **§1–3**: System context, stakeholders, constraints
- **§4**: Solution strategy and key architectural approaches
- **§5**: Building blocks (align with C4 L1/L2 containers/components)
- **§6**: Runtime scenarios and behavioral views
- **§7**: Cross-cutting concerns (logging, security, performance)
- **§8–9**: Architecture decisions, quality requirements, SLIs/SLOs, error budgets
- **§10–12**: Risks, technical debt, glossary

### C4 Model Integration
- **L0 Context**: System landscape and external actors
- **L1 Containers**: Major deployable/runnable units
- **L2 Components**: Internal structure within containers
- **L3 Code**: Implementation details (classes, functions)
- **Extraction**: Parse PlantUML/Mermaid blocks with System|Container|Component|Person|Rel tokens

### Diátaxis Documentation Framework
- **Tutorials**: Learning-oriented beginner walkthroughs
- **How-to**: Problem-oriented crisp procedures
- **Reference**: Information-oriented specs, APIs, SLOs, schemas
- **Explanation**: Understanding-oriented rationale and trade-offs

## Quality Gate Implementation Checklist
- **Coverage**: ≥95% of section needs satisfied or TODO-stubbed with concrete acceptance criteria
- **Consistency**: Zero unresolved contradictions across interfaces and decisions
- **Citations**: 100% of claims traced to file and line provenance
- **SRE**: Each component has SLI/SLO pair and error budget reference
- **Security**: Threat model summary present for security-relevant components
- **Research**: Performance claims and risky decisions linked to evidence
- **Style**: No orphan acronyms, active voice, normalized headings, no secrets/PII

This specification provides complete implementation details for building a comprehensive document architecture system that rivals enterprise knowledge management platforms.