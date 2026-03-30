# DocuXtractor Standalone CLI Planning Log

**Project**: Extract 11-pattern document processing from Dopemux into standalone CLI
**Date**: 2025-09-23
**Status**: Deep Planning Phase

## Project Overview

### Goal
Transform the Dopemux 11-pattern document processing system into a completely standalone CLI tool called "DocuXtractor" that requires only Python + Claude Code as prerequisites.

### Current State
- Partial implementation exists in `dopemux-docuXtractor/` directory
- System currently depends on Dopemux infrastructure (local Milvus, Claude Code integrations)
- Complex pipeline with Voyage AI embeddings, vector search, and 11-pattern extraction

### Target Requirements
- Completely standalone CLI program
- API key configuration for: Voyage AI, Zilliz Cloud, OpenAI
- User onboarding with account creation guides
- Replace local Milvus with Zilliz Cloud
- Self-contained LLM processing
- Maximum logging and progressive feedback
- One-level-at-a-time processing with detailed metrics
- Semantic search enrichment of final outputs

## Deep Analysis Completed

### 1. Full Scope Assessment
**What needs to be accomplished:**
- Extract 11-pattern processing from Dopemux into standalone CLI
- Replace all Dopemux dependencies with self-contained equivalents
- Create professional user onboarding for multiple cloud APIs
- Implement progressive processing with maximum transparency
- Ensure semantic search enhances output quality
- Package as distributable CLI requiring only Python + Claude Code

### 2. Approach Analysis
**Selected: Full Cloud Migration (Approach A)**
- Replace Milvus with Zilliz Cloud completely
- Use OpenAI/Claude for all LLM processing
- Cloud-first architecture with local CLI interface
- Pros: Scalable, professional, no local dependencies
- Cons: Higher costs, internet dependency, API complexity

### 3. Constraints & Dependencies
**Technical Constraints:**
- User has only Python + Claude Code initially
- Must be completely self-contained after setup
- Multiple cloud APIs with different authentication patterns
- Zilliz requires schema/collection setup
- Processing must be interruptible and resumable

**Dependency Chain:**
1. Python environment setup
2. API key acquisition (Voyage, Zilliz, OpenAI)
3. Cloud service configuration (collections, schemas)
4. Local CLI tool installation
5. Project-specific processing setup

### 4. Success Criteria
**Technical Success:**
- ✅ Processes 446+ files with 11-pattern extraction
- ✅ Generates comprehensive TSV registries with full traceability
- ✅ Semantic search enhances output quality measurably
- ✅ Zero dependency on Dopemux infrastructure
- ✅ Professional installation experience

**User Experience Success:**
- ✅ Clear setup instructions with account creation guides
- ✅ Progressive feedback showing exactly what's happening
- ✅ Detailed metrics at each processing level
- ✅ Intuitive CLI interface
- ✅ Comprehensive logging for troubleshooting

### 5. Risk Assessment
**Early Risks:**
- API Key Management: Complex multi-service authentication
- Zilliz Setup: Users struggling with cloud database configuration
- Dependency Hell: Package conflicts in user environments
- Cost Surprises: Unexpected API charges during processing

**Late Risks:**
- Performance Issues: Large document sets overwhelming cloud APIs
- Quality Degradation: Semantic search not improving outputs
- Maintenance Burden: Multiple API integrations requiring updates

## Architecture Decisions (Step 2)

### Core Architecture: Progressive Cloud-First Approach
1. **Vector Database**: Zilliz Cloud (managed Milvus) for production-grade vector search
2. **LLM Processing**: OpenAI GPT-4 for document analysis, with Voyage AI for embeddings
3. **Configuration Management**: Professional CLI setup wizard with validation
4. **Processing Pipeline**: One-level-at-a-time with comprehensive logging and metrics
5. **Installation**: Python package with setup command handling all dependencies

### Key Components to Build

#### 1. Setup Wizard (`docuxtractor setup`)
- Guided API key collection and validation
- Zilliz collection creation and schema setup
- Configuration file generation with encryption
- Test processing to validate entire pipeline

#### 2. Processing Engine (`docuxtractor process <directory>`)
- Progressive file discovery and analysis
- 11-pattern extraction with semantic enrichment
- Real-time metrics and file-level feedback
- Resumable processing with state persistence

#### 3. Configuration Management
- Secure API key storage (encrypted config files)
- Service health checking and validation
- Usage monitoring and cost estimation
- Debug mode with extensive logging

## Refined Analysis (Step 3 Preparation)

### Approach Validation
- **Cloud-First Confirmed**: Professional experience, scalability, no local infrastructure
- **Refinement**: Hybrid model where Claude Code handles LLM tasks, cloud handles vectors
- **Decision**: Stick with cloud-first but leverage Claude Code to reduce OpenAI dependency

### Major Phases Identified
1. **Foundation & Setup** (Critical) - Package structure, config, wizard
2. **Cloud Service Integration** (Complex) - Zilliz, Voyage AI, monitoring
3. **Processing Engine** (Core Value) - Discovery, extraction, state management
4. **Output & UX** (Differentiation) - TSV generation, progress, enrichment
5. **Distribution & Maintenance** (Sustainability) - Packaging, docs, updates

### Critical Dependencies
**Sequential**: Config System → Zilliz Setup → Document Processing → Registry Generation
**Parallel Opportunities**: CLI framework + config system, documentation during development

### Resource Requirements
- Python packaging and CLI development expertise
- Cloud API integration across multiple services
- Vector database schema design knowledge
- Rich console interface development
- Error handling and recovery patterns

### Critical Path Analysis
**Highest Risk**: Zilliz integration complexity, multi-API orchestration, cost transparency
**Most Time-Sensitive**: Configuration system, Zilliz schema design, Claude Code integration

## Step 3: Implementation Sequence & Component Breakdown

### Refined Architecture: Hybrid Cloud + Claude Code
Minimize costs and leverage existing capabilities by using Claude Code for LLM tasks.

### Phase 1: Foundation & Setup (Week 1-2)

#### Component 1.1: Project Structure & CLI Framework
- Create `docuxtractor/` package with proper entry points
- Implement Click-based CLI with `setup`, `process`, `status`, `config` commands
- Rich console interface for professional output
- Logging framework with debug/info/error levels

#### Component 1.2: Configuration Management System
- Encrypted config file storage (`~/.docuxtractor/config.json`)
- API key validation and health checking
- Service status monitoring (Voyage, Zilliz availability)
- Cost estimation and usage tracking

#### Component 1.3: Setup Wizard
```bash
docuxtractor setup
```
- Interactive API key collection with validation
- Zilliz Cloud project creation guidance
- Collection schema setup automation
- End-to-end pipeline test

### Phase 2: Cloud Service Integration (Week 2-3)

#### Component 2.1: Zilliz Cloud Integration
- Collection creation with hybrid search schema
- Embedding insertion and retrieval
- Health monitoring and connection management
- Error recovery and retry logic

#### Component 2.2: Voyage AI Integration
- Batch embedding generation for documents
- Rate limiting and quota management
- Fallback strategies for API failures
- Cost tracking per processing run

#### Component 2.3: Claude Code Bridge
- Replace OpenAI calls with Claude Code tool invocations
- Document analysis and pattern extraction
- Atomic unit normalization and quality assessment
- Integration with existing Dopemux patterns

## Final Strategic Validation (Step 3 Reflection)

### Completeness Check ✅
- All original requirements covered in implementation plan
- Technical requirements properly addressed
- ADHD accommodations maintained

### Critical Gaps Identified
1. **Claude Code Integration Pattern**: Need specific invocation method
2. **Zilliz Schema Complexity**: Require detailed hybrid search schema
3. **Cost Estimation Accuracy**: Upfront transparency essential
4. **Error Recovery**: Mid-processing failure handling

### Key Assumptions Requiring Validation
- Claude Code programmatic invocation feasibility
- Zilliz Cloud performance equivalence to local Milvus
- User capability for multi-service API setup
- Voyage AI rate limit accommodation

### First Concrete Steps
**Immediate (This Week):**
1. Examine existing `dopemux-docuXtractor/` code
2. Design CLI structure and commands
3. Create proper Python package skeleton

**Next (Week 2):**
1. Implement encrypted config system
2. Build interactive setup wizard
3. Zilliz integration and testing

## Step 4: Processing Engine Detailed Design (Completed)

### Processing Engine Architecture: Hybrid Cloud + Local CLI Design

#### Core Engine Components

##### 1. Document Discovery & Filtering System
**Class: `DocumentDiscovery`**
- **File Walker**: Recursive directory traversal with exclude patterns (node_modules, .git, __pycache__)
- **Extension Filter**: Support for 16+ file types (.md, .py, .js, .ts, .html, .json, etc.)
- **Size Limits**: Skip files >10MB, warn on >1MB files
- **Encoding Detection**: UTF-8 with fallback handling for problematic files
- **Progress Tracking**: Real-time file count with estimated processing time

##### 2. 11-Pattern Extraction Engine with Claude Code Integration
**Class: `PatternExtractor`**
- **Pattern Definitions**: Migrate existing regex patterns from Dopemux extractor.py
- **Claude Code Bridge**: Replace OpenAI calls with subprocess calls to `claude code --prompt`
- **Atomic Unit Processing**: Break documents into sections (paragraph/function level)
- **Confidence Scoring**: Maintain existing confidence calculation (0.1-1.0 range)
- **Context Extraction**: 100-character windows around matches
- **Batch Processing**: Process 10 files per batch for progress feedback

##### 3. Semantic Embedding & Enrichment Pipeline
**Class: `EmbeddingEnricher`**
- **Voyage AI Integration**: voyage-context-3 model (1024-dim vectors)
- **Zilliz Cloud Storage**: Hybrid search collections with metadata
- **Specificity Scoring**: Port existing scoring logic (IDs: 0.3, Numbers: 0.2, Code: 0.3, Depth: 0.2)
- **Similarity Thresholds**: Cosine ≥0.92, Jaccard ≥0.82 for duplicate detection
- **Enrichment Process**: Semantic search against existing vectors to enhance extraction results

##### 4. State Management & Resume Capability
**Class: `ProcessingState`**
- **State File**: JSON state in output directory (.docuxtractor_state.json)
- **Checkpoint System**: Save state after each file/batch
- **Resume Logic**: Detect incomplete runs and offer resume option
- **Progress Persistence**: Track files processed, entities extracted, embeddings created
- **Error Recovery**: Log failed files for retry attempts

#### Processing Workflow: One-Level-at-a-Time Approach

##### Level 1: Document Discovery
```
docuxtractor process /path/to/docs --output ./analysis
├── Scanning directory tree...
├── Found 446 processable files
├── Estimated processing time: 45 minutes
└── Continue? [Y/n]
```

##### Level 2: Document Processing (25-minute chunks)
```
Processing Batch 1/18 (25 files)
[████████░░] 8/25 complete
✅ file1.py: 5 atomic units, 12 entities
✅ file2.md: 3 atomic units, 8 entities
⚠️ file3.js: encoding issues, using fallback
```

##### Level 3: Entity Extraction & Classification
```
Extracting entities from 446 atomic units...
Features: 23 ✅    Components: 45 ✅    Subsystems: 12 ✅
Requirements: 34 ✅    Decisions: 18 ✅    Constraints: 7 ✅
Patterns: 29 ✅    Technologies: 56 ✅    Interfaces: 41 ✅
Processes: 15 ✅    Metrics: 9 ✅
```

##### Level 4: Semantic Embedding
```
Creating embeddings for 289 entities...
Batch 1/15: ████████░░ 67% (Cost: $0.12)
├── Uploading to Zilliz Cloud...
├── Similarity analysis...
└── 15 potential duplicates found
```

##### Level 5: Registry Generation & Enrichment
```
Generating TSV registries...
✅ features_registry.tsv (23 entries)
✅ components_registry.tsv (45 entries)
✅ subsystems_registry.tsv (12 entries)
✅ research_registry.tsv (34 entries)
✅ evidence_links.tsv (156 entries)

Semantic enrichment complete!
🎯 Final output: ./analysis/ (5 TSV files, 289 total entities)
```

#### Error Recovery & Retry Logic

##### Service Health Monitoring
- **Voyage AI**: Rate limit detection (1000 requests/minute)
- **Zilliz Cloud**: Connection health checks
- **Claude Code**: Process availability verification
- **Fallback Strategies**: Local pattern extraction if cloud services fail

##### Retry Patterns
- **Exponential Backoff**: 1s, 2s, 4s, 8s delays
- **Partial Recovery**: Resume from last successful checkpoint
- **User Choice**: Continue with available services or abort

##### Error Categories
- **Network Issues**: Retry with backoff
- **API Limits**: Wait and retry with rate limiting
- **File Issues**: Skip and log for manual review
- **Critical Failures**: Save state and exit gracefully

#### Cost Transparency & Monitoring

##### Real-Time Cost Tracking
```
Current Session Costs:
├── Voyage AI: $0.45 (1,250 requests)
├── Zilliz Cloud: $0.08 (storage + queries)
├── Estimated Total: $0.53
└── Projected Final Cost: $2.15
```

##### Budget Controls
- **Cost Warnings**: Alert at 50%, 75%, 90% of user-defined budget
- **Pause Options**: Stop processing and save state when limits reached
- **Usage Analytics**: Track cost per file, per entity, per embedding

## Next Steps
- Step 5: Output & UX specifications
- Step 6: Distribution & packaging strategy
- Step 7: Testing & validation approach
- Step 8: Documentation & maintenance plan

---

## Step 5: Output & UX Specifications (Completed)

### CLI Interface & Command Design

#### Core Commands Structure
```bash
docuxtractor --help                    # Global help and overview
docuxtractor setup                     # Interactive setup wizard
docuxtractor process <directory>       # Main processing command
docuxtractor status [project]          # Check processing status
docuxtractor config                    # Configuration management
docuxtractor cost [project]            # Cost analysis and budgeting
docuxtractor resume [project]          # Resume interrupted processing
```

#### Progressive Onboarding Flow (Setup Command)
- **Step 1/4**: Environment verification (Python, Claude Code, connectivity)
- **Step 2/4**: Voyage AI API key setup with validation
- **Step 3/4**: Zilliz Cloud configuration and schema creation
- **Step 4/4**: End-to-end validation test

#### One-Level-at-a-Time Processing Interface
**Level 1**: Document discovery with cost/time estimates
**Level 2**: File processing in ADHD-friendly 25-file batches
**Level 3**: Entity extraction with live progress for all 11 patterns
**Level 4**: Semantic embedding with cost tracking
**Level 5**: Registry generation and enrichment

### Progress Visualization System

#### Visual Progress Indicators
- Multi-level progress bars showing overall and phase-specific progress
- Real-time file-by-file feedback with entity counts
- Cost tracking with budget warnings at 50%, 75%, 90% thresholds
- Time estimates with break suggestions every 25 minutes

#### ADHD Accommodations
- Break reminders with pause/continue options
- Gentle error messages with clear recovery paths
- Visual status indicators (✅ ⚠️ 🔄 ⏳) for cognitive load reduction
- Progressive disclosure: essential info first, details on request

### Output Format Specifications

#### TSV Registry Schemas
**Features Registry**: id, name, description, source_file, confidence, context, metadata
**Components Registry**: id, name, description, component_type, dependencies, interfaces
**Evidence Links Registry**: entity_type, entity_id, source_type, link_type, confidence

#### Error Classification & Recovery
- **INFO/WARNING/ERROR/FATAL** severity levels
- Automated recovery suggestions for common issues
- Resume capability from any checkpoint
- Partial results export for interrupted processing

### Cost Management Interface
- Real-time cost dashboard with service breakdown
- Budget alerts with overrun projections
- Cost per entity metrics and efficiency tracking
- Multiple budget adjustment options during processing

## Step 6: Distribution & Packaging Strategy (Completed)

### Python Packaging Architecture
- **Modern Standards**: pyproject.toml (PEP 518/621), semantic versioning, MIT license
- **Package Structure**: src/ layout with clear module separation (cli/, core/, services/, config/, utils/)
- **Multi-Channel Distribution**: PyPI (primary), GitHub releases (secondary), Conda-Forge (future)
- **Installation Methods**: pip, pipx (recommended for isolation), direct from GitHub

### Dependency Management
- **Minimal Philosophy**: Core dependencies only (click, rich, pydantic, httpx, pymilvus, voyageai, cryptography)
- **Version Pinning**: Major version constraints to prevent breaking changes
- **Cross-Platform**: Python 3.8+ support on macOS, Linux, Windows
- **Isolation Support**: pipx compatibility for clean installations

### Configuration System
- **Standards Compliant**: XDG config directories on Unix, AppData on Windows
- **Encrypted Storage**: API keys encrypted using cryptography library
- **Layered Config**: Global defaults, project-specific overrides
- **Schema Validation**: Pydantic models for type safety

### Quality Assurance
- **Comprehensive Testing**: Unit, integration, e2e, performance test suites
- **CI/CD Pipeline**: GitHub Actions with matrix testing across Python versions and platforms
- **Release Process**: Alpha → Beta → RC → Stable with community feedback loops

### Documentation & Support
- **Multi-Format Docs**: README, CLI help, online docs (ReadTheDocs), in-app guidance
- **Support Channels**: GitHub Issues/Discussions, comprehensive troubleshooting guides
- **Update Mechanism**: Version checking with future self-update capability

## Step 7: Testing & Validation Approach (Completed)

### Multi-Tier Testing Architecture
- **Tier 1 - Unit Testing**: Core algorithms, pattern extraction, cost calculation, state management
- **Tier 2 - Integration Testing**: External service mocking (Voyage AI, Zilliz, Claude Code)
- **Tier 3 - End-to-End Testing**: Complete workflows with real API validation
- **Tier 4 - Performance Testing**: Large codebase processing, memory usage, scalability

### Specialized Testing Areas
- **ADHD Accommodation Validation**: Break reminders, progress clarity, cognitive load limits
- **Security Testing**: API key encryption, config file permissions, secure storage
- **Cross-Platform Testing**: Windows, macOS, Linux compatibility and path handling
- **Cost Accuracy Testing**: Budget tracking within 1% precision for large datasets

### CI/CD Pipeline Strategy
- **Matrix Testing**: Python 3.8-3.11 across ubuntu/macos/windows
- **Conditional E2E**: Real API tests only on main branch pushes
- **Performance Gates**: Memory <1GB, processing time <1hr for 500+ files
- **Quality Thresholds**: >95% code coverage, all security validations pass

### Test Data Management
- **Synthetic Codebase Generation**: Realistic multi-language codebases for testing
- **Pattern-Rich Content**: Files designed to test all 11 extraction patterns
- **Edge Case Coverage**: Large files, encoding issues, malformed content
- **Performance Datasets**: 500+ file codebases for load testing

### Release Validation Checklist
9 critical quality gates including unit tests, security validation, ADHD UX testing, and cost accuracy verification before any release.

## Step 8: Documentation & Maintenance Plan (Completed)

### Documentation Architecture

#### Multi-Tier Documentation Strategy
- **Tier 1 - Quick Start**: 5-minute setup to first results for immediate value
- **Tier 2 - User Guide**: Complete workflows, cost management, ADHD accommodations
- **Tier 3 - Technical Guide**: API setup, troubleshooting, advanced configuration
- **Tier 4 - Developer Docs**: Contributing, architecture, maintenance procedures

#### Platform-Specific Documentation
- **README.md**: Installation overview and quick start
- **docs/ Directory**: Comprehensive Sphinx documentation with ReadTheDocs hosting
- **CLI Help**: Built-in contextual help for all commands and options
- **Setup Wizard**: Interactive documentation during configuration process

### Long-Term Maintenance Strategy

#### Service Integration Monitoring
- **API Compatibility**: Automated testing against Voyage AI and Zilliz Cloud API changes
- **Cost Model Updates**: Quarterly review of pricing and budget calculation accuracy
- **Claude Code Evolution**: Compatibility testing with new Claude Code releases
- **Dependency Security**: Regular security audits and dependency updates

#### Community & Support Framework
- **GitHub Issues**: Bug tracking with templates for clear issue reporting
- **GitHub Discussions**: Community support, use cases, feature requests
- **Documentation Updates**: User feedback integration and accuracy maintenance
- **Release Communication**: Clear changelogs and migration guides

#### Quality Assurance Pipeline
- **Automated Monitoring**: Service health checks and performance regression detection
- **User Feedback**: Collection and analysis for improvement prioritization
- **Performance Optimization**: Continuous improvement for large codebase processing
- **Cross-Platform Validation**: Regular testing across operating systems and Python versions

---

**Planning Status**: COMPLETE (8/8 steps finished)
**Next Actions**: Ready for implementation or detailed technical design

## Planning Summary

This comprehensive 8-step planning process has designed DocuXtractor as a standalone CLI tool that successfully extracts the Dopemux 11-pattern document processing system with the following key innovations:

**Core Achievements:**
- Cloud-first architecture replacing local Milvus with Zilliz Cloud
- ADHD-optimized UX with one-level-at-a-time processing
- Professional CLI with comprehensive cost transparency
- Robust testing framework covering all integration points
- Modern Python packaging with multi-channel distribution

**Technical Foundation:**
- Hybrid processing: Claude Code for LLM tasks, cloud services for vectors
- State persistence and resumable processing
- Encrypted API key management
- 11-pattern extraction with semantic search enrichment
- Real-time cost tracking with budget controls

**Implementation Ready:**
All architectural decisions, component designs, and quality frameworks are now defined and ready for development execution.