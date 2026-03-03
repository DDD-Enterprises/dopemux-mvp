# DocuXtractor Current TODO - Phase 2 Ready

**Last Updated**: 2025-01-24
**Status**: Phase 1 Complete → Phase 2 Implementation Ready
**Priority**: Document Discovery Engine

## 🎯 **Immediate Next Tasks (Phase 2)**

### HIGH PRIORITY - Document Discovery Engine
- [ ] **Create DocumentDiscovery class** in `src/docuxtractor/core/discovery.py`
  - File walking with recursive directory traversal
  - Exclude patterns: node_modules, .git, __pycache__, venv, build, dist
  - Extension filtering: md, py, js, ts, html, css, json, yaml, yml, toml
  - Size limits: Skip >10MB, warn >1MB files
  - Progress tracking with ADHD-friendly feedback

- [ ] **Implement encoding detection** using chardet
  - UTF-8 with fallback handling for problematic files
  - Error recovery for corrupted/binary files
  - Charset normalization for consistent processing

- [ ] **Add file fingerprinting** (from technical specs)
  - Store path, SHA256, size, mtime, detected format
  - Build manifest.tsv with one row per file
  - Change detection for resume capability

### MEDIUM PRIORITY - Basic Processing Pipeline
- [ ] **Create AtomicUnitProcessor** in `src/docuxtractor/core/processor.py`
  - Document chunking by structure (not just tokens)
  - Atomic unit creation with metadata preservation
  - Section path tracking (H1 › H2 › H3)
  - Content normalization and formatting

- [ ] **Implement pattern application**
  - Apply 11 regex patterns to atomic units
  - Extract context windows (±100 characters)
  - Calculate confidence scores using existing algorithm
  - Generate ExtractedEntity objects

- [ ] **Add progress tracking**
  - File-level progress with batch processing (25 files per chunk)
  - Real-time entity count updates
  - ADHD break reminders every 25 minutes
  - Visual progress bars with Rich console

### LOW PRIORITY - State Management
- [ ] **Create ProcessingStateManager** in `src/docuxtractor/core/state.py`
  - JSON state persistence in output directory
  - Checkpoint system after each batch
  - Resume logic for interrupted processing
  - Error recovery and retry tracking

- [ ] **Implement cost tracking stub**
  - Placeholder cost calculation (actual costs come in Phase 3)
  - Budget monitoring with warning thresholds
  - Usage analytics per file/entity/operation

## 🛠️ **Implementation Guidelines**

### File Structure to Create
```
src/docuxtractor/
├── core/
│   ├── discovery.py      # ← START HERE
│   ├── processor.py      # ← Then this
│   └── state.py          # ← Finally this
├── cli/
│   └── commands.py       # ← Enhanced process command
└── tests/
    └── unit/
        ├── test_discovery.py
        └── test_processor.py
```

### ADHD Accommodations to Maintain
- **Progress Chunking**: Process 25 files per batch maximum
- **Visual Feedback**: Rich progress bars with encouraging messages
- **Break Reminders**: Suggest pause after 25 minutes processing
- **Clear Status**: Show exactly what's happening at each step
- **Error Recovery**: Gentle error messages with clear next steps

### Integration Points
- **CLI Command**: Enhance `docuxtractor process` to use new discovery engine
- **Pattern System**: Use existing `EXTRACTION_PATTERNS` from `patterns.py`
- **Data Models**: Use existing `AtomicUnit` and `ExtractedEntity` models
- **Testing**: Add unit tests for each new component

## 📋 **Success Criteria for Phase 2**

### Minimum Viable Implementation
- [ ] `docuxtractor process .` discovers and lists files correctly
- [ ] Basic file filtering by extension works
- [ ] Can create atomic units from markdown files
- [ ] Pattern extraction produces entities with confidence scores
- [ ] Progress tracking shows file-by-file updates

### Full Phase 2 Complete
- [ ] Handles all supported file types (md, py, js, ts, html, css, json, yaml)
- [ ] Proper encoding detection and error handling
- [ ] Resume capability from processing state
- [ ] ADHD break reminders and progress chunking
- [ ] Comprehensive unit tests for discovery and processing

## 🎮 **Getting Started Commands**

```bash
# Verify current setup
cd /Users/hue/code/dopemux-mvp/dopemux-docuXtractor
docuxtractor --help

# Check current CLI output
docuxtractor process . --max-files 5

# Run existing tests
python -m pytest tests/unit/test_patterns.py -v

# Start implementation
# Create src/docuxtractor/core/discovery.py
```

## 🧠 **Context from Phase 1**

### What Works Now
- CLI framework with all commands (setup, process, status, config, cost)
- 11-pattern regex extraction with confidence scoring
- Rich console output with ADHD accommodations
- Pydantic data models for all entities
- Unit tests for pattern recognition (11/11 passing)

### What's Still Stubbed
- Actual file discovery and processing (shows "implementation in progress")
- Cloud service integration (Voyage AI, Zilliz Cloud)
- State persistence and resume capability
- Cost tracking and budget monitoring
- TSV registry generation

### Next Logical Step
Implement `DocumentDiscovery` class to start actually processing files through our sophisticated pattern system. This bridges the gap between our working CLI and the powerful extraction engine we've built.

**Ready to code!** 🚀