# dope-context Optimization Roadmap

**Status**: Performance improvements for large-scale production usage

## Current State

dope-context works correctly with good performance for typical usage:
- Code search: < 200ms ADHD target ✅
- Workspace detection: 0.37ms (134x better than target) ✅
- Multi-project isolation: Perfect ✅
- Incremental sync: SHA256-based change detection ✅

## Future Optimizations

### 1. Incremental Chunk Updates (Performance)

**Location**: `src/mcp/server.py:708`

**Current Behavior**:
```python
# Detects changed files with SHA256
changes = sync.check_changes()

# But requires full reindex
# "Run index_workspace to update" (reindexes entire changed files)
```

**Optimization**:
```python
# Only update affected chunks within changed files
# 1. Identify changed regions via diff
# 2. Rechunk only modified sections
# 3. Update/delete/insert specific vectors
# 4. Preserve unchanged chunks
```

**Impact**:
- **Before**: Modify 1 line → reindex entire 500-line file → 10 chunks re-embedded
- **After**: Modify 1 line → reindex 1 function → 1 chunk re-embedded
- **Speedup**: 10x faster reindexing for small edits
- **Cost Savings**: 10x fewer embedding API calls

**Complexity**: Medium
- Requires diff analysis
- Chunk boundary detection
- Vector ID tracking

**Priority**: Low (current full-file reindex is fast enough for ADHD targets)

---

### 2. DocumentProcessor Integration (Quality)

**Location**: `src/pipeline/docs_pipeline.py:76, :151`

**Current Behavior**:
```python
# Simple text extraction for MVP
text = file_path.read_text(encoding="utf-8")
chunks = self._simple_chunk(text, chunk_size=1000)
```

**Limitations**:
- PDF: No support (falls back to text extraction)
- DOCX: No support (falls back to text extraction)
- HTML: No structure preservation (treats as plain text)
- Markdown: No heading hierarchy (treats as plain text)

**Optimization**:
```python
# Use DocumentProcessor for smart extraction
processor = DocumentProcessor()
document = processor.process(file_path)  # Handles PDF/DOCX/HTML/MD

# Smart chunking with structure preservation
chunks = processor.chunk_by_structure(
    document,
    strategy="semantic",  # Preserve headings, sections
    max_chunk_size=1000
)
```

**Impact**:
- **PDF Support**: Extract text, tables, images from PDFs
- **DOCX Support**: Preserve formatting, styles, structure
- **HTML Quality**: Extract main content, ignore navigation/ads
- **Markdown Quality**: Preserve heading hierarchy for better context

**Complexity**: Medium
- Requires `DocumentProcessor` class implementation
- Libraries: pypdf2, python-docx, beautifulsoup4, markdown
- Testing across multiple formats

**Priority**: Medium (would improve docs search quality significantly)

---

## Implementation Plan

### Phase 1: Current State (✅ Complete)
- [x] Hybrid search (dense + sparse)
- [x] Multi-project isolation
- [x] Incremental sync detection
- [x] ADHD optimizations
- [x] Metrics tracking

### Phase 2: Quality Improvements (Recommended Next)
- [ ] DocumentProcessor integration
- [ ] PDF/DOCX support
- [ ] HTML smart extraction
- [ ] Markdown hierarchy preservation

### Phase 3: Performance Optimization (Optional)
- [ ] Incremental chunk updates
- [ ] Chunk boundary caching
- [ ] Vector ID tracking system

---

## Performance Targets

### Current Performance (✅ Sufficient for ADHD)
| Operation | ADHD Target | Current | Status |
|-----------|-------------|---------|--------|
| Search | < 200ms | ~78ms | ✅ 2.5x better |
| Workspace detect | < 50ms | 0.37ms | ✅ 135x better |
| Reindex (full) | N/A | ~30s for 1000 files | ✅ Acceptable |

### Post-Optimization Targets (Phase 3)
| Operation | Target | Expected | Improvement |
|-----------|--------|----------|-------------|
| Reindex (incremental) | < 5s | ~3s | 10x faster |
| Small edits | < 1s | ~500ms | 60x faster |
| Large file edits | < 10s | ~5s | 6x faster |

---

## Decision Rationale

**Why defer these optimizations?**

1. **ADHD Targets Met**: Current performance exceeds all attention-span requirements
2. **Correctness First**: Working implementation > premature optimization
3. **Usage Data Needed**: Need real-world metrics to guide optimization priorities
4. **Incremental Value**: Phase 2 (quality) delivers more user value than Phase 3 (speed)

**When to implement?**

- **Phase 2**: When users report poor docs search quality or missing PDF support
- **Phase 3**: When reindexing takes >1 minute or costs become significant

---

**Current Status**: Production-ready with room for future enhancement
**Next Steps**: Monitor usage, collect feedback, prioritize based on real needs
