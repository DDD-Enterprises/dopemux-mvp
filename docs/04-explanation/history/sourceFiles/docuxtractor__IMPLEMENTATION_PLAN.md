# DocuXtractor Implementation Plan

## Vision: Transform ANY text into professional software documentation

Transform unstructured text (chat histories, meeting notes, scattered docs) into professional software documentation using NLP-based extraction and Zilliz Cloud vector storage.

## Core Value Proposition
- **Input**: Discord exports, Slack dumps, meeting notes, scattered markdown
- **Process**: NLP-based semantic extraction + professional templates
- **Output**: Arc42 architecture, C4 diagrams, ADRs, PRDs
- **Setup**: `pip install docuxtractor && docux setup` (5 minutes max)

## Technical Architecture

### 1. Core Data Flow
```
Raw Text → AtomicUnits → NLP Extraction → Concepts → Templates → Professional Docs
    ↓           ↓             ↓            ↓          ↓            ↓
Chat logs   Chunking    Semantic      Features   Arc42      Architecture
Docs        Content     Analysis      Decisions  C4         Documents
Notes       Metadata    Confidence    Problems   ADRs       Diagrams
```

### 2. Component Architecture
```python
# Core Processing Pipeline
AtomicUnit          # Enhanced data model with NLP support
ContentAnalyzer     # Parse any format (chat, docs, notes)
ConceptExtractor    # NLP-based semantic extraction
EmbeddingPipeline   # Voyage AI + Zilliz Cloud
DocumentSynthesizer # Template-based generation

# Key Differentiators
- Semantic matching (not rigid regex)
- Chat history understanding
- Professional template output
- Zero infrastructure setup
```

### 3. Key Innovation: NLP-Based Extraction
```python
# OLD: Rigid regex patterns
FEATURE_PATTERN = r"feature:\s*([^.\n]+)"

# NEW: Semantic similarity
FEATURE_SIGNALS = ["users can", "ability to", "supports", "enables"]
feature_embeddings = embed(FEATURE_SIGNALS)
sentence_embedding = embed(sentence)
if cosine_similarity > 0.7:
    extract_feature(sentence, confidence=similarity_score)
```

## Implementation Phases

### Phase 1: Foundation (Days 1-3) ✅ PARTIALLY COMPLETE
- [x] Repository structure and pyproject.toml
- [x] Enhanced AtomicUnit data models
- [ ] Embedding pipeline (Zilliz Cloud migration)
- [ ] Basic content analyzer

### Phase 2: Intelligence (Days 4-6)
- [ ] NLP ConceptExtractor with semantic matching
- [ ] Chat format parsers (Discord, Slack, generic)
- [ ] Confidence scoring and validation
- [ ] Fallback keyword matching

### Phase 3: Storage (Days 7-9)
- [ ] Zilliz Cloud auto-provisioning
- [ ] Voyage AI integration (context-3, rerank-2.5)
- [ ] ChromaDB local fallback
- [ ] Hybrid search (dense + sparse)

### Phase 4: Synthesis (Days 10-12)
- [ ] Arc42 template generator
- [ ] C4 model diagram creation
- [ ] ADR and PRD builders
- [ ] PlantUML/Mermaid diagram output

### Phase 5: CLI & Polish (Days 13-15)
- [ ] Rich CLI with progress displays
- [ ] Interactive setup wizard
- [ ] Quality gates and validation
- [ ] PyPI packaging and examples

## Critical Technical Decisions

### 1. Zilliz Cloud vs Local Infrastructure
**Decision**: Zilliz Cloud primary, ChromaDB fallback
**Rationale**: Community adoption requires zero-setup experience
**Implementation**:
```python
# Auto-provision Zilliz collections
client = MilvusClient(uri=zilliz_cloud_url, token=user_token)
if not client.has_collection("docux_concepts"):
    client.create_collection("docux_concepts", dimension=1024)
```

### 2. NLP Strategy: Hybrid Approach
**Decision**: Sentence transformers + Voyage AI + keyword fallback
**Rationale**: Balance accuracy, cost, and reliability
**Implementation**:
```python
# Primary: Semantic similarity
similarity = cosine_similarity(sentence_embed, pattern_embed)
if similarity > 0.7:
    return extract_concept(sentence, confidence=similarity)

# Fallback: Keyword matching
elif any(keyword in sentence.lower() for keyword in fallback_keywords):
    return extract_concept(sentence, confidence=0.5)
```

### 3. Template Strategy: Professional Standards
**Decision**: Arc42, C4, Diátaxis frameworks
**Rationale**: Industry-standard formats increase adoption
**Templates**:
- Arc42: 12-section architecture documentation
- C4: Context → Container → Component → Code
- ADR: Context → Decision → Consequences
- PRD: Problem → Solution → Success Metrics

## File Structure (Target)
```
docuxtractor/
├── src/docuxtractor/
│   ├── __init__.py              ✅ Done
│   ├── cli.py                   ⏳ Phase 5
│   ├── core/
│   │   ├── atomic_units.py      ✅ Done
│   │   ├── analyzer.py          ⏳ Phase 1
│   │   └── extractor.py         ⏳ Phase 2
│   ├── nlp/
│   │   ├── concepts.py          ⏳ Phase 2
│   │   ├── patterns.py          ⏳ Phase 2
│   │   └── chat_parser.py       ⏳ Phase 2
│   ├── storage/
│   │   ├── zilliz.py           ⏳ Phase 3
│   │   ├── voyage.py           ⏳ Phase 3
│   │   └── local.py            ⏳ Phase 3
│   └── synthesis/
│       ├── templates/          ⏳ Phase 4
│       ├── generator.py        ⏳ Phase 4
│       └── diagrams.py         ⏳ Phase 4
├── tests/
├── examples/
│   ├── discord_export.json
│   ├── slack_dump.zip
│   └── meeting_notes.md
├── pyproject.toml              ✅ Done
└── README.md
```

## Success Metrics
1. **Setup Time**: < 5 minutes from install to first analysis
2. **Accuracy**: > 80% relevant concept extraction
3. **Speed**: Process 1000 pages in < 5 minutes
4. **Formats**: Discord, Slack, Markdown, plain text, meeting notes
5. **Output Quality**: Professional Arc42/C4/ADR documentation

## Next Session Priorities

### Immediate (Resume First)
1. **Complete embedding pipeline**: Port from doc_processor/embedder.py
   - Keep Voyage AI integration
   - Replace local Milvus with Zilliz Cloud
   - Maintain ChromaDB fallback

2. **Build content analyzer**: Parse different input formats
   - Chat parsers for Discord/Slack
   - Document structure detection
   - AtomicUnit creation with metadata

3. **Create NLP concept extractor**: Semantic pattern matching
   - Replace regex with embeddings
   - Confidence scoring
   - Support for conversational text

### Critical Code to Extract
From existing codebase:
- `doc_processor/embedder.py`: Voyage AI + vector storage
- `src/dopemux/analysis/processor.py`: ADHD progress displays
- `src/dopemux/analysis/extractor.py`: Pattern concepts (adapt for NLP)

## User Experience Target
```bash
# Install
pip install docuxtractor

# Setup (interactive wizard)
docux setup

# Analyze any text
docux analyze discord_export.json -o architecture_docs/
docux analyze ./meeting_notes/ --format notes -o requirements/
docux analyze ./scattered_docs/ --format auto -o complete_docs/

# Output: Professional documentation ready for teams
```

This plan transforms the vision into actionable implementation steps with clear technical decisions and success criteria.