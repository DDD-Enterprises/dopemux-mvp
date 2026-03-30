# TODO - Next Session Priorities

**Status**: Phase 2 COMPLETE → Starting Phase 3 Cloud Integration
**Priority**: HIGH - Cloud services for production-ready document analysis

## 🎯 **Immediate Next Tasks (Phase 3 Start)**

### HIGH PRIORITY - Cloud Service Setup
- [ ] **Create API key management** in `src/docuxtractor/config/api_keys.py`
  - Secure storage with cryptography library
  - Environment variable loading (.env support)
  - Validation and health check methods
  - Encrypted local storage for persistence

- [ ] **Implement Voyage AI client** in `src/docuxtractor/services/voyage.py`
  - Context-3 embedding generation
  - Batch processing (100 entities per request)
  - Rate limiting and error retry
  - Cost calculation per request

- [ ] **Create Zilliz Cloud client** in `src/docuxtractor/services/zilliz.py`
  - Collection management for entity types
  - Batch vector insertion
  - Semantic search capabilities
  - Connection health monitoring

### MEDIUM PRIORITY - Processing Pipeline
- [ ] **Build embedding orchestrator** in `src/docuxtractor/core/embedder.py`
  - Take ExtractedEntity objects from Phase 2
  - Generate optimized text chunks for Context-3
  - Coordinate with Voyage AI and Zilliz Cloud
  - ADHD-friendly progress tracking

- [ ] **Implement semantic enrichment** in `src/docuxtractor/core/enricher.py`
  - Calculate entity similarity scores
  - Detect duplicate/related entities
  - Generate relationship recommendations
  - Quality scoring and validation

### LOW PRIORITY - Output Generation
- [ ] **Create TSV registry generator** in `src/docuxtractor/exporters/tsv.py`
  - Features.tsv with full provenance
  - Components.tsv with technical details
  - Subsystems.tsv with domain mapping
  - Evidence_Links.tsv for relationships
  - Research.tsv for insights

- [ ] **Add state management** in `src/docuxtractor/core/state.py`
  - ProcessingStateManager from models.py
  - JSON persistence in output directory
  - Resume capability from checkpoints
  - Cost tracking across sessions

## 🛠️ **Implementation Guidelines**

### Cloud Service Integration
- **Start with Voyage AI**: Embedding generation is the foundation
- **Use environment variables**: Keep API keys out of code
- **Implement cost tracking**: Essential for budget management
- **Add health checks**: Validate connections before processing

### ADHD Accommodations for Phase 3
- **25-entity batches**: Process in ADHD-friendly chunks
- **Cost alerts**: Warn at 50%, 80%, 90% of budget
- **Break reminders**: Suggest pauses every 10 minutes
- **Visual progress**: Real-time embedding progress bars
- **Interrupt-friendly**: Save state after each batch

### Error Handling Priorities
- **API failures**: Retry logic with exponential backoff
- **Network issues**: Graceful degradation and recovery
- **Rate limits**: Respect API quotas automatically
- **Budget limits**: Hard stops when budget reached

## 📊 **Success Metrics for Next Session**

### Minimum Viable Implementation
- [ ] Voyage AI embeddings working for sample entities
- [ ] Zilliz Cloud storing and retrieving vectors
- [ ] Basic cost tracking operational
- [ ] CLI integration with cloud commands

### Full Phase 3 Complete
- [ ] All entity types embedded and stored
- [ ] 5 TSV registries generated with relationships
- [ ] Resume capability tested and working
- [ ] ADHD accommodations fully integrated
- [ ] Budget management preventing overruns

## 🎮 **Getting Started Commands for Next Session**

### 1. Context Restoration (2 minutes)
```bash
cd /Users/hue/code/dopemux-mvp/dopemux-docuXtractor
cat SESSION_RESTORE_FINAL.md    # Full context
cat PHASE_3_ROADMAP.md          # Technical plan
cat TODO_NEXT_SESSION.md        # This file

# Verify Phase 2 still working
docuxtractor process . --max-files 2
```

### 2. Phase 3 Setup (5 minutes)
```bash
# Create cloud service directories
mkdir -p src/docuxtractor/config
mkdir -p src/docuxtractor/services
mkdir -p src/docuxtractor/exporters

# Install additional dependencies
pip install voyageai pymilvus python-dotenv

# Start with API key management
touch src/docuxtractor/config/api_keys.py
```

### 3. Development Focus
1. **Start here**: API key management (secure foundation)
2. **Then**: Voyage AI client (embedding generation)
3. **Next**: Zilliz Cloud client (vector storage)
4. **Finally**: CLI integration (user interface)

## 🧠 **Context Bridges**

### From Phase 2
- **Working system**: 5 files → 172 units → 8 entities
- **Data models**: AtomicUnit, ExtractedEntity fully compliant
- **Pattern system**: 11-pattern extraction with 0.681 avg confidence
- **CLI framework**: 4-phase pipeline ready for cloud integration

### To Phase 3
- **Cloud-native**: Voyage AI + Zilliz Cloud integration
- **Production-ready**: Cost management + state persistence
- **Enterprise features**: TSV registries + relationship mapping
- **Scale-ready**: Batch processing + resume capability

## 📁 **File Structure to Create**

```
src/docuxtractor/
├── config/
│   ├── __init__.py
│   └── api_keys.py          # ← START HERE
├── services/
│   ├── __init__.py
│   ├── voyage.py            # ← THEN THIS
│   └── zilliz.py            # ← THEN THIS
├── exporters/
│   ├── __init__.py
│   └── tsv.py               # ← LATER
└── tests/
    ├── integration/
    │   ├── test_voyage.py
    │   └── test_zilliz.py
    └── unit/
        └── test_embedder.py
```

## 🚀 **Ready State Verification**

Before starting Phase 3, confirm Phase 2 is solid:
```bash
# All should pass/work
python -m pytest tests/unit/test_patterns.py -v  # ✅ 11/11 tests
docuxtractor --help                              # ✅ CLI working
docuxtractor process . --max-files 1            # ✅ End-to-end pipeline

# If any fail, fix Phase 2 first
# If all pass, proceed with Phase 3 implementation
```

**Next session goal**: Working cloud integration with cost management! 🌟