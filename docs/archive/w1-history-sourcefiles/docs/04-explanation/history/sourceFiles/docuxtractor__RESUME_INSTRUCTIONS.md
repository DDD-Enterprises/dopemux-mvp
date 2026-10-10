# DocuXtractor Session Resume Instructions

## Context Restoration Command

When resuming, start with:
```
I'm continuing the DocuXtractor implementation. We're building a standalone CLI tool that transforms any text (chat histories, meeting notes, scattered docs) into professional software documentation using NLP-based extraction and Zilliz Cloud vector storage.

Current Status: Foundation complete (repo structure, pyproject.toml, AtomicUnit models), now implementing the embedding pipeline by porting from doc_processor/embedder.py with Zilliz Cloud integration.

Key requirement: Use "think harder" approach - deeper analysis at each implementation step.
```

## What's Been Built (Resume State)

### ✅ Complete
- **Repository Structure**: docuxtractor/ with proper src/ layout
- **Package Config**: pyproject.toml with all dependencies
- **Data Models**: Enhanced AtomicUnit with NLP support in `src/docuxtractor/core/atomic_units.py`
- **Key Features**: Enum types, chat detection, concept extraction, confidence scoring

### 🔄 Current Task: Embedding Pipeline
**Goal**: Port from `doc_processor/embedder.py` but adapt for:
- Zilliz Cloud instead of local Milvus (community-friendly)
- Keep Voyage AI integration
- Maintain ChromaDB fallback
- Add sentence-transformers for local NLP

**File Location**: `src/docuxtractor/storage/`

### ⏳ Next Tasks (In Order)
1. **NLP ConceptExtractor**: Semantic matching vs rigid regex
2. **Content Analyzer**: Parse chat/docs/notes formats
3. **Zilliz Cloud**: Auto-provisioning and setup
4. **Templates**: Arc42, C4, ADR generators
5. **CLI**: Rich progress with ADHD accommodations

## Key Design Decisions Made

### 1. Input Strategy: Any Text Format
- **Chat Histories**: Discord, Slack, generic chat logs
- **Documents**: Markdown, text, code files
- **Meeting Notes**: Agenda-style unstructured content
- **Auto-Detection**: File extension + content analysis patterns

### 2. Processing Strategy: Hybrid NLP
```python
# Replace rigid regex with semantic similarity
OLD: r"feature:\s*([^.\n]+)"
NEW: cosine_similarity(sentence_embed, "users can") > 0.7
```

### 3. Output Strategy: Professional Templates
- Arc42 architecture (12 sections)
- C4 model diagrams (Context, Container, Component)
- ADRs with full decision context
- PRDs from feature discussions

## Critical Code Locations

### Source Material to Extract From
- `doc_processor/embedder.py` - Voyage AI + vector storage logic
- `src/dopemux/analysis/processor.py` - ADHD progress displays
- `src/dopemux/analysis/extractor.py` - Pattern extraction concepts

### Target Implementation Files
```
src/docuxtractor/
├── storage/
│   ├── embeddings.py    🔄 Next: Port embedder logic
│   ├── zilliz.py        ⏳ Zilliz Cloud client
│   └── local.py         ⏳ ChromaDB fallback
├── nlp/
│   ├── concepts.py      ⏳ Semantic extraction
│   └── patterns.py      ⏳ NLP pattern matching
└── synthesis/
    └── templates/       ⏳ Arc42, C4, ADR
```

## Technical Specifications

### Dependencies (Already in pyproject.toml)
```toml
# NLP and embeddings
"sentence-transformers>=2.2.0"
"voyageai>=0.2.0"
"pymilvus[zillizcloud]>=2.3.0"

# CLI and display
"click>=8.0.0"
"rich>=13.0.0"

# Fallback storage
"chromadb>=0.4.0"
```

### Key Parameters
- **Similarity Thresholds**: 0.92 cosine, 0.82 Jaccard (from existing)
- **Embedding Model**: voyage-context-3 for docs, voyage-code-3 for code
- **Batch Size**: 50 for Voyage AI, adjust for rate limits
- **Confidence Range**: 0.0-1.0 for all extractions

## Success Criteria
- **Setup Time**: < 5 minutes from pip install to first analysis
- **Input Flexibility**: Works on Discord exports, meeting notes, any text
- **Output Quality**: Professional Arc42/C4/ADR documentation
- **Extraction Accuracy**: > 80% relevant concepts captured

## Next Implementation Step

**Immediate Task**: Create `src/docuxtractor/storage/embeddings.py`

Port the embedding logic from `doc_processor/embedder.py` but:
1. **Think harder** about Zilliz Cloud integration vs local Milvus
2. Keep the Voyage AI client pattern but improve error handling
3. Add sentence-transformers for local NLP preprocessing
4. Maintain the duplicate detection and confidence scoring
5. Design for batch processing (chat logs can be huge)

**Key Files to Reference**:
- `doc_processor/embedder.py` (lines 1-100+ analyzed in session)
- `docuxtractor/src/docuxtractor/core/atomic_units.py` (our enhanced models)

## Context Continuation

The user emphasized "think harder" throughout implementation - this means:
- Deeper analysis of each technical decision
- Consider edge cases and failure modes
- Think about user experience and community adoption
- Anticipate performance and scaling issues
- Design for flexibility and extensibility

Resume by continuing the embedding pipeline implementation with this thoughtful approach.