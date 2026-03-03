# HISTORICAL Docs Refactoring Plan

## Context
This document captures the plan for refactoring 97+ files in `/docs/HISTORICAL/` into a structured documentation system using Diátaxis + ADRs + Feature Hubs + MCP integration.

## Framework Overview
- **Diátaxis Structure**: 4-part documentation taxonomy (tutorials/how-to/reference/explanation)
- **Feature Hub Pattern**: Central index pages linking all related docs per feature
- **ADR-Driven Decisions**: Formal Architecture Decision Records for ALL system decisions
- **MCP Integration**: Claude Code slash commands for intelligent context retrieval
- **Owner**: @hu3mann (Dopemux)

## Current State Analysis
- **Location**: `/docs/HISTORICAL/`
- **Files**: 97+ markdown files
- **Structure**: Two main subfolders need merging:
  - `preliminary-docs-normalized/`
  - `diagrams/`
- **ADR Sources**: 20+ files contain embedded architectural decisions

## Target Structure
```
docs/
├── 01-tutorials/         # Learning paths
├── 02-how-to/           # Task-oriented guides
├── 03-reference/        # Information reference
├── 04-explanation/      # Feature Hubs + concepts
├── 90-adr/             # Architecture Decision Records
├── 91-rfc/             # Request for Comments
├── 92-runbooks/        # Operational procedures
├── 94-architecture/    # arc42 + C4 diagrams
├── _manifest.yaml      # Document registry
└── features.yaml       # Feature registry
```

## ADR Categories to Extract
ADRs are relevant to ALL Dopemux categories and subsystems:

### 1. Core Architecture
- Orchestration Pattern Selection (Hub-and-Spoke with Mesh Fallback)
- Agent Framework Decision (Custom with LangGraph patterns)
- Memory System Architecture (Letta + Custom Tiers)
- Communication Protocol Selection
- System Integration Patterns

### 2. ADHD Optimization Systems
- Cognitive Load Reduction Strategies
- Attention Management Architecture
- Context Preservation Methods
- Notification and Feedback Systems
- Executive Function Support Patterns
- Time Perception and Management

### 3. Integration Architecture
- Claude Code Integration Strategy
- MCP Server Implementation Approach
- Leantime Integration Architecture
- Task-Master AI Integration
- Multi-Agent Communication Protocols

### 4. Development Workflow
- Development Environment Setup
- Testing Strategy Architecture
- Deployment and Distribution
- Configuration Management
- Code Organization Patterns

### 5. User Experience Design
- Interface Design Patterns
- Accessibility Requirements
- User Flow Optimizations
- ADHD-Friendly UI Patterns

### 6. Data & Memory Architecture
- Context Storage Patterns
- Session Management
- Memory Tiering Strategy
- Data Persistence Approaches

### 7. Security & Privacy
- Authentication Systems
- Data Protection Strategies
- User Privacy Frameworks
- Secure Communication Patterns

### 8. Performance & Scalability
- Resource Management
- Optimization Strategies
- Scalability Patterns
- Performance Monitoring

## Implementation Phases

### Phase 1: Setup Framework (Ready to implement)
1. Install drop-in docs starter pack for dopemux-mvp
2. Setup pre-commit hooks and automation
3. Configure Claude Code slash commands
4. Initialize MCP integration

### Phase 2: ADR Extraction
1. Scan all 20+ identified files with ADR content
2. Extract architectural decisions into formal ADR format
3. Categorize by system/feature area
4. Create cross-references and links

### Phase 3: Content Migration
1. Categorize existing content by Diátaxis type
2. Create Feature Hubs for major systems
3. Move content to appropriate directories
4. Generate tombstone files for merged content

### Phase 4: Architecture Documentation
1. Extract diagrams and create C4 structure
2. Build arc42 architecture documentation
3. Document system interfaces and relationships
4. Create navigation and cross-references

### Phase 5: Integration & Validation
1. Update manifest and feature registries
2. Test MCP context retrieval
3. Validate cross-references and links
4. Run quality checks (linting, link validation)

## Files Requiring ADR Extraction
Key files identified with embedded architectural decisions:
- `DOPEMUX_CUSTOM_AGENT_RND.md`
- `DOPEMUX_TECHNICAL_ARCHITECTURE_v3.md`
- `DOPEMUX_IMPLEMENTATION_BLUEPRINT.md`
- `dopemux-feature-analysis.md`
- `DOPEMUX_RESEARCH_FINDINGS.md`
- And 15+ additional files

## Automation Tools Ready
- Front-matter guard scripts
- Manifest generation
- Tombstone creation
- Pre-commit quality checks
- MCP context integration

## Next Actions After Context Clear
1. Deploy starter pack to dopemux-mvp
2. Begin systematic ADR extraction
3. Create Feature Hubs for core systems
4. Migrate and organize existing content
5. Validate and test complete system

## Success Criteria
- All architectural decisions captured in formal ADRs
- Content properly categorized by Diátaxis structure
- Feature Hubs provide clear navigation
- MCP integration enables intelligent context retrieval
- Quality automation prevents documentation drift
- All content linked and cross-referenced properly

## Owner & Timeline
- **Owner**: @hu3mann
- **Status**: Ready for implementation
- **Next Review**: After Phase 1 completion

---
Generated: 2025-09-20 via HISTORICAL docs refactoring analysis