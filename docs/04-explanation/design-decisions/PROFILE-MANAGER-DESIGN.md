---
id: PROFILE-MANAGER-DESIGN
title: Profile Manager Design
type: explanation
owner: '@hu3mann'
last_review: '2025-10-17'
next_review: '2026-01-15'
---
# Dopemux Profile Manager - Design Specification

**Date**: 2025-10-05
**Status**: Design Complete, Ready for Implementation
**Decision**: ConPort Decision #10
**Planner Session**: f7884a69-21c8-41ff-9461-95bb8ae73a16

---

## Executive Summary

**Problem**: 8 MCP servers exposing 50+ tools causes context window overload (15-20K tokens overhead per conversation)

**Solution**: Profile-based MCP selection reducing to 10-15 tools per use case (70% reduction)

**Approach**: Lightweight YAML profiles + smart auto-detection, replacing MetaMCP broker complexity

**Architecture Decision**: Replace MetaMCP broker with profile-based config generation. MetaMCP solved the right problem (context overload) but with over-engineered broker architecture. Profile manager achieves same goal with 500-700 LOC vs 2000+ LOC.

---

## Background: MetaMCP Context

### Original Problem
- 8 MCP servers (serena-v2, conport, zen, gpt-researcher, context7, mas-sequential-thinking, dope-context, exa)
- 50+ tools exposed to Claude Code in every conversation
- 15-20K tokens of overhead just for tool schemas
- LLM decision paralysis and token waste

### MetaMCP's Approach (Deprecated)
- Central broker service on port 8090
- Role-based tool mounting (developer, researcher, planner, reviewer, ops, architect, debugger)
- Dynamic escalation rules and token budgets
- Complex runtime orchestration

### Why MetaMCP Was Abandoned
1. **MCP Protocol Limitation**: Can't change tools without restarting Claude (no lazy loading)
2. **Over-Engineering**: Complexity should be in config generation, not runtime
3. **Never Deployed**: Built but never actually used - profiles are simpler
4. **ADHD Friction**: Managing broker + roles adds cognitive overhead

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DOPEMUX PROFILE MANAGER                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  User Command                                                │
│  └─> dopemux start --profile developer                      │
│                                                               │
│  Detection Layer                                             │
│  ├─> Git Branch Scanner (30% weight)                        │
│  ├─> Directory Pattern Matcher (25% weight)                 │
│  ├─> ADHD Engine Query [optional] (20% weight)              │
│  ├─> Time Window Checker (15% weight)                       │
│  └─> File Pattern Analyzer (10% weight)                     │
│         │                                                     │
│         v                                                     │
│  Profile Selector                                            │
│  └─> Score profiles → Select best match                     │
│         │                                                     │
│         v                                                     │
│  Config Generator                                            │
│  └─> profile.yaml → Claude config.json                      │
│         │                                                     │
│         v                                                     │
│  Session Manager                                             │
│  ├─> ConPort: save_active_context()                         │
│  ├─> Stop Claude (SIGTERM)                                  │
│  ├─> Write new config.json                                  │
│  ├─> Start Claude with new config                           │
│  └─> ConPort: restore_active_context()                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Profile Definition Format

### YAML Structure

```yaml
# .dopemux/profiles/developer.yaml

name: developer
display_name: "Developer"
description: "Code implementation and debugging"

# MCP Server Selection (ConPort required in all profiles)
mcps:
  - serena-v2        # Code navigation, LSP
  - conport          # Memory (MANDATORY)
  - dope-context     # Semantic code search

# ADHD Optimization
adhd_config:
  energy_preference: medium-high  # Best when energy >= medium
  attention_mode: focused         # Needs sustained focus
  session_duration: 50            # Pomodoro-friendly (minutes)

# Auto-Detection Rules
auto_detection:
  git_branches:
    - "feature/*"
    - "fix/*"
    - "refactor/*"

  directories:
    - "src/"
    - "tests/"
    - "lib/"

  file_patterns:
    - "*.py"
    - "*.ts"
    - "*.js"
    - "*.go"

  time_windows:
    - "09:00-12:00"  # Morning focus
    - "14:00-17:00"  # Afternoon focus
```

### Core Profiles

| Profile | MCPs | Tool Count | Use Case |
|---------|------|------------|----------|
| developer | serena-v2, conport, dope-context | ~10-12 | Implementation |
| researcher | zen, gpt-researcher, context7, conport | ~12-15 | Investigation |
| architect | zen, serena-v2, conport, dope-context | ~15-18 | Design/planning |
| full | all 8 MCPs | ~50+ | Complex tasks |

---

## Auto-Detection Algorithm

### Scoring System

```python
def detect_profile(context: ProfileContext) -> ProfileMatch:
    """
    Weighted scoring system for profile detection
    Total score: 100 points distributed across 5 signals
    """

    scores = {}
    for profile in load_profiles():
        score = 0.0

        # SIGNAL 1: Git Branch (30 points)
        if matches_branch_pattern(profile.git_branches, context.current_branch):
            score += 30

        # SIGNAL 2: Directory Context (25 points)
        if current_dir_matches(profile.directories, context.pwd):
            score += 25

        # SIGNAL 3: ADHD State (20 points) - OPTIONAL
        if adhd_engine_available():
            energy = get_current_energy()
            if energy_matches(profile.energy_preference, energy):
                score += 20

        # SIGNAL 4: Time of Day (15 points)
        if in_time_window(profile.time_windows, now()):
            score += 15

        # SIGNAL 5: Recent Files (10 points)
        if recent_files_match(profile.file_patterns):
            score += 10

        scores[profile.name] = score

    best_match = max(scores, key=scores.get)
    confidence = scores[best_match] / 100.0

    return ProfileMatch(
        profile=best_match,
        confidence=confidence,
        scores=scores
    )
```

### Suggestion Strategy (ADHD-Friendly)

| Confidence | Action |
|------------|--------|
| > 0.85 | Show suggestion in statusline (gentle) |
| 0.65 - 0.85 | Prompt with explanation + scores |
| < 0.65 | Don't suggest (avoid false positives) |

### Fallback Hierarchy

1. ADHD Engine available? → Use energy + attention state
2. Git branch detected? → Use branch patterns
3. Directory patterns match? → Use pwd matching
4. Time of day match? → Use time windows
5. Manual override → User knows best (always respected)

---

## Profile Switching Workflow

```
USER TRIGGERS SWITCH
  │
  v
┌────────────────────────────────────┐
│ 1. Detect Current Profile          │
│    Parse active Claude config.json │
└────────────────────────────────────┘
  │
  v
┌────────────────────────────────────┐
│ 2. ConPort: Save Session           │
│    - Open files list               │
│    - Cursor positions              │
│    - Recent decisions              │
│    Returns: session_id             │
└────────────────────────────────────┘
  │
  v
┌────────────────────────────────────┐
│ 3. Generate New Config              │
│    Load: .dopemux/profiles/X.yaml  │
│    Transform: profile -> config    │
│    Write: ~/.claude/config.json    │
└────────────────────────────────────┘
  │
  v
┌────────────────────────────────────┐
│ 4. Graceful Claude Restart          │
│    - Send SIGTERM (3s timeout)     │
│    - Start Claude with new config  │
└────────────────────────────────────┘
  │
  v
┌────────────────────────────────────┐
│ 5. ConPort: Restore Session        │
│    - Reopen files                  │
│    - Restore cursor positions      │
│    - Load recent decisions         │
└────────────────────────────────────┘
  │
  v
PROFILE SWITCH COMPLETE
(Total: 7-10 seconds)
```

### ConPort Integration

```python
# New ConPort category: "profile_sessions"

{
  "session_id": "sess_20251005_123456",
  "profile_from": "developer",
  "profile_to": "researcher",
  "timestamp": "2025-10-05T12:34:56",
  "context_snapshot": {
    "open_files": ["src/main.py", "tests/test_main.py"],
    "active_file": "src/main.py",
    "cursor_line": 42,
    "recent_decisions": [143, 9, 10]
  }
}
```

---

## Migration Strategy

### Phase 1: Backward Compatible (Week 1)

**Objective**: Zero disruption to current workflow

```yaml
# Create default profile matching current setup
# .dopemux/profiles/full.yaml

name: full
display_name: "Full Stack"
mcps:
  - serena-v2
  - conport
  - zen
  - gpt-researcher
  - context7
  - mas-sequential-thinking
  - dope-context

adhd_config:
  energy_preference: any
  attention_mode: any

# Set as system default
default_profile: full
```

**Result**: Existing `dopemux start` continues working identically

### Phase 2: Introduce Profiles (Week 2)

**Objective**: Enable opt-in testing of reduced context

```bash
# Create specialized profiles
.dopemux/profiles/
  ├── developer.yaml     # 3 MCPs
  ├── researcher.yaml    # 4 MCPs
  ├── architect.yaml     # 4 MCPs
  └── full.yaml          # 7 MCPs (default)

# User can test manually
dopemux start --profile developer

# Migration assistant
dopemux profile suggest
# Analyzes git history, file patterns, suggests optimal profile
```

### Phase 3: Smart Defaults (Week 3)

**Objective**: Enable auto-detection with user confirmation

```bash
# Auto-detection with gentle prompts
dopemux start
# Output: "Detected feature/auth branch -> Developer profile? [Y/n]"

# Statusline shows suggestions
# "DEV | MED | FOCUS | [!] Switch to RESEARCH?"
```

---

## Implementation Roadmap

### Priority 0: MVP (2 days)

**Components**:
1. Profile YAML parser
2. Config generator (profile.yaml → Claude config.json)
3. Manual profile selection (`dopemux start --profile <name>`)

**Deliverables**:
- `src/dopemux/profile_manager.py` (100-150 LOC)
- `src/dopemux/config_generator.py` (100-150 LOC)
- 4 YAML profile templates in `.dopemux/profiles/`

### Priority 1: Intelligence Layer (1 week)

**Components**:
1. Auto-detection algorithm (git, directory, ADHD, time, files)
2. ConPort session management (save/restore)
3. Profile switching command (`dopemux switch <profile>`)

**Deliverables**:
- `src/dopemux/detection.py` (200-250 LOC)
- ConPort custom_data schema update
- Enhanced CLI commands

### Priority 2: UX Integration (2 weeks)

**Components**:
1. Statusline profile indicator
2. Gentle suggestion UI
3. Usage analytics and optimization

**Deliverables**:
- Updated statusline script
- Suggestion prompt system
- Analytics dashboard

---

## Technical Specifications

### File Structure

```
.dopemux/
├── profiles/
│   ├── developer.yaml
│   ├── researcher.yaml
│   ├── architect.yaml
│   └── full.yaml
└── config/
    └── profile-settings.yaml

src/dopemux/
├── profile_manager.py      # Core profile operations (100-150 LOC)
├── config_generator.py     # Claude config transformation (100-150 LOC)
├── detection.py            # Auto-detection algorithms (200-250 LOC)
└── session_manager.py      # ConPort integration (100-150 LOC)

Total: ~500-700 LOC vs MetaMCP's 2000+ LOC
```

### Key Interfaces

```python
# profile_manager.py

@dataclass
class Profile:
    name: str
    display_name: str
    description: str
    mcps: List[str]
    adhd_config: ADHDConfig
    auto_detection: AutoDetectionRules

class ProfileManager:
    def load_profiles() -> Dict[str, Profile]
    def get_profile(name: str) -> Optional[Profile]
    def validate_profile(profile: Profile) -> ValidationResult

# config_generator.py

class ConfigGenerator:
    def generate_claude_config(profile: Profile) -> Dict
    def write_config(config: Dict, path: Path) -> None
    def backup_current_config() -> Path

# detection.py

@dataclass
class ProfileMatch:
    profile: str
    confidence: float
    scores: Dict[str, float]

class ProfileDetector:
    def detect_profile(context: ProfileContext) -> ProfileMatch
    def calculate_scores(profile: Profile, context: ProfileContext) -> float
    def suggest_profile(confidence: float) -> SuggestionStrategy
```

---

## Success Metrics

### Quantitative

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Tools per session | 50+ | 10-15 | 70% reduction |
| Context overhead | 15-20K | 5-7K | 65% reduction |
| Auto-detect accuracy | N/A | >85% | New capability |
| Switch time | N/A | <10s | New capability |

### Qualitative

- Profile visible in statusline (clear mental model)
- Gentle suggestions, not forced switches (ADHD-friendly)
- Session continuity via ConPort (zero data loss)
- One command to start everything (`dopemux start`)

---

## Related Documentation

- **Architecture Consolidation**: `docs/ARCHITECTURE-CONSOLIDATION-SYNTHESIS.md`
- **ConPort Memory**: `.claude/modules/cognitive-plane/conport-memory.md`
- **Dopemux Context**: `docs/DOPEMUX-CONTEXT-DEEP-DIVE.md`
- **ADHD Engine**: `services/task-orchestrator/adhd_engine.py`
- **MCP Overview**: Research on context window management (see web search results)

---

## Next Steps

1. Create 4 YAML profile templates in `.dopemux/profiles/`
2. Implement `profile_manager.py` and `config_generator.py` (P0)
3. Test token reduction with developer profile
4. Validate backward compatibility with full profile
5. Implement auto-detection algorithm (P1)
6. Add ConPort session save/restore (P1)
7. Integrate with statusline (P2)

---

**Document Status**: Complete, Ready for Implementation
**Owner**: Architecture Team
**Tags**: profile-manager, context-management, adhd-optimization, mcp-selection, architecture-decision
