---
id: PROFILE_SYSTEM_ARCHITECTURE
title: Profile_System_Architecture
type: explanation
owner: '@hu3mann'
last_review: '2025-10-17'
next_review: '2026-01-15'
---
# Profile System Architecture

**Developer documentation for extending and maintaining the Dopemux profile system.**

## Overview

The profile system provides context-aware MCP server selection with ADHD optimizations:
- **Profiles**: YAML-defined MCP server sets with metadata
- **Detection**: Weighted 5-signal scoring for auto-suggestions
- **Analytics**: ConPort-based metrics tracking and visualization
- **Migration**: Git-based onboarding wizard

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   Profile System                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────┐    ┌──────────────┐                │
│  │ ProfileParser │───▶│ ProfileModel │                │
│  │ (YAML→Object) │    │  (Pydantic)  │                │
│  └───────────────┘    └──────────────┘                │
│         │                     │                         │
│         ▼                     ▼                         │
│  ┌───────────────┐    ┌──────────────┐                │
│  │ProfileDetector│◀───│DetectionCtx  │                │
│  │ (100pt score) │    │ (5 signals)  │                │
│  └───────────────┘    └──────────────┘                │
│         │                     │                         │
│         ▼                     ▼                         │
│  ┌───────────────┐    ┌──────────────┐                │
│  │ AutoDetection │───▶│ ConPort API  │                │
│  │   Service     │    │  (metrics)   │                │
│  └───────────────┘    └──────────────┘                │
│         │                     │                         │
│         ▼                     ▼                         │
│  ┌───────────────┐    ┌──────────────┐                │
│  │   CLI Commands│◀───│  Analytics   │                │
│  │  (init/stats) │    │ (dashboard)  │                │
│  └───────────────┘    └──────────────┘                │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. ProfileParser (`profile_parser.py`)

**Purpose**: Parse and validate profile YAML files

**Key Methods:**
- `parse_file(path)` - Parse single YAML file
- `parse_directory(dir, pattern)` - Parse all profiles in directory
- `parse_string(yaml)` - Parse from string (testing)

**Validation:**
- Pydantic model validation
- MCP server name validation (optional)
- Profile name uniqueness across collection

### 2. ProfileDetector (`profile_detector.py`)

**Purpose**: Score profiles based on context signals

**Scoring Algorithm** (100 points total):
```python
git_branch:    30 points  # Exact pattern match
directory:     25 points  # Directory contains pattern
adhd_state:    20 points  # Energy + attention match
time_window:   15 points  # Within time window
file_patterns: 10 points  # Recent files match patterns
```

**Confidence Levels:**
```python
>= 0.85: Auto-suggest (high confidence)
>= 0.65: Prompt user (moderate confidence)
<  0.65: No suggestion (low confidence)
```

**Key Methods:**
- `detect(context)` - Find best profile for context
- `_score_git_branch()` - Pattern matching with fnmatch
- `_score_directory()` - Substring and parent matching
- `_score_adhd_state()` - Energy/attention compatibility
- `_gather_context()` - Auto-detect from environment

### 3. AutoDetectionService (`auto_detection_service.py`)

**Purpose**: Background detection with debouncing and quiet hours

**Features:**
- 5-minute detection intervals (configurable)
- 30-minute debouncing (don't re-suggest same profile)
- Quiet hours (default: 22:00-08:00)
- Never-list (user can block profiles permanently)
- YAML config persistence (`.dopemux/profile-settings.yaml`)

**Key Methods:**
- `run_detection_cycle()` - Single detection pass
- `should_suggest()` - Check debounce/quiet/confidence
- `suggest_profile_switch()` - Show [y/N/never] prompt
- `run_loop()` - Continuous background operation

**Integration Point**: Designed for daemon mode (future)

### 4. ProfileAnalytics (`profile_analytics.py`)

**Purpose**: Track and analyze profile usage patterns

**Metrics Tracked:**
```python
ProfileSwitch:
  - timestamp
  - from_profile / to_profile
  - trigger (manual/auto/suggestion_accepted/declined)
  - confidence (if auto-triggered)

ProfileStats (aggregated):
  - total_switches, manual/auto counts
  - most_used_profile
  - avg_switches_per_day
  - switch_accuracy (% lasting >30 min)
  - usage_by_hour (time-of-day patterns)
  - usage_by_profile (frequency distribution)
```

**Storage**: ConPort `custom_data` API (category: `profile_metrics`)

**Key Methods:**
- `log_switch()` - Record switch event (async)
- `get_stats()` - Aggregate metrics (async)
- `display_stats()` - Rich visual dashboard

### 5. ProfileWizard (`profile_wizard.py`)

**Purpose**: Interactive onboarding with git analysis

**Workflow:**
1. `GitHistoryAnalyzer` - Extract patterns from commits
2. Display analysis with suggestions
3. 3-question interactive flow
4. Generate Profile object
5. Save as YAML to `profiles/`

**Git Analysis:**
- Branch prefixes (feature/, fix/, docs/)
- Directory patterns (services/, src/, docs/)
- Commit times (infer peak work hours)
- Commit intensity (files per commit → energy level)
- MCP suggestions (directory types → relevant MCPs)

## Extension Points

### Adding New Detection Signals

To add a new signal (e.g., "language detection"):

1. **Add to DetectionContext:**
```python
# profile_detector.py
@dataclass
class DetectionContext:
    # ... existing fields ...
    primary_language: Optional[str] = None
```

2. **Add scoring method:**
```python
def _score_language(self, patterns: List[str], current_lang: str) -> float:
    """Score language match (0-X points)"""
    # Your logic here
    return score
```

3. **Integrate in detect():**
```python
signal_scores['language'] = self._score_language(
    profile.auto_detection.languages,
    context.primary_language
)
```

4. **Update Profile model:**
```python
# profile_models.py
class AutoDetection(BaseModel):
    # ... existing fields ...
    languages: Optional[List[str]] = None
```

### Adding Analytics Metrics

To track new metrics (e.g., "switch duration"):

1. **Add to ProfileSwitch:**
```python
@dataclass
class ProfileSwitch:
    # ... existing fields ...
    duration_minutes: Optional[int] = None
```

2. **Update logging:**
```python
# profile_analytics.py
async def log_switch(..., duration: Optional[int] = None):
    switch_data['duration_minutes'] = duration
```

3. **Compute in stats:**
```python
# _analyze_switches()
avg_duration = sum(s.duration_minutes for s in switches if s.duration_minutes) / len(switches)
```

### Custom Suggestion Logic

Override `should_suggest()` for custom logic:

```python
class CustomDetectionService(AutoDetectionService):
    def should_suggest(self, profile_name: str, confidence: float) -> bool:
        # Your custom logic
        if self.user_is_in_meeting():
            return False

        return super().should_suggest(profile_name, confidence)
```

## Data Flow

### Profile Application Flow

```
User: dopemux profile apply developer
  │
  ├─▶ ProfileParser.parse_file("developer.yaml")
  │     └─▶ Profile object (validated)
  │
  ├─▶ ClaudeConfig.validate_profile()
  │     └─▶ Check MCPs exist in ~/.claude.json
  │
  ├─▶ ClaudeConfig.apply_profile()
  │     └─▶ Update ~/.claude.json mcpServers
  │
  └─▶ ProfileAnalytics.log_switch()
        └─▶ ConPort custom_data (metrics)
```

### Auto-Detection Flow

```
AutoDetectionService (every 5 min)
  │
  ├─▶ ProfileDetector.detect()
  │     ├─▶ _gather_context() → DetectionContext
  │     ├─▶ Score all profiles (5 signals each)
  │     └─▶ Return best match with confidence
  │
  ├─▶ should_suggest()?
  │     ├─▶ Check confidence >= 0.85
  │     ├─▶ Check not in quiet hours
  │     ├─▶ Check debounced (last suggestion >30 min ago)
  │     └─▶ Check not in never_suggest list
  │
  ├─▶ suggest_profile_switch()
  │     ├─▶ Display match summary with scores
  │     ├─▶ Prompt [y/N/never]
  │     └─▶ Handle response
  │
  └─▶ If accepted: apply_profile() + log_switch()
```

## Database Schema

### ConPort Storage

**Profile Metrics** (`custom_data` category: `profile_metrics`):
```json
{
  "workspace_id": "/Users/hue/code/dopemux-mvp",
  "category": "profile_metrics",
  "key": "switch_1729090123.456",
  "value": {
    "timestamp": "2025-10-16T12:48:43",
    "from_profile": "minimal",
    "to_profile": "developer",
    "trigger": "manual",
    "confidence": null
  }
}
```

**Auto-Detection Config** (`.dopemux/profile-settings.yaml`):
```yaml
enabled: true
check_interval_seconds: 300
confidence_threshold: 0.85
debounce_minutes: 30
quiet_hours_start: '22:00'
quiet_hours_end: '08:00'
never_suggest: []
```

## Performance

**Targets** (ADHD optimization):
- Profile parsing: <100ms
- Detection scoring: <200ms
- Analytics query: <500ms
- Stats display: <1s

**Actual** (measured):
- Profile parsing: ~50ms (5 profiles)
- Detection: ~80ms (5 profiles, 5 signals each)
- Analytics: Depends on data size (O(n) switches)

## Testing

### Unit Tests

```bash
# Test profile parsing
pytest tests/test_profile_parser.py

# Test detection
pytest tests/test_profile_detector.py

# Test analytics
pytest tests/test_profile_analytics.py
```

### Manual Testing

```bash
# Test wizard
dopemux profile init test-profile

# Test detection
python -m dopemux.profile_detector

# Test analytics
python -m dopemux.profile_analytics
```

## Future Enhancements

**Planned** (not yet implemented):
1. Machine learning: Learn from user corrections
2. Multi-signal fusion: Bayesian confidence adjustment
3. Profile recommendations: "Users like you prefer..."
4. A/B testing: Compare profile effectiveness
5. Integration with ADHD Engine: Real-time energy/attention

**Extension Ideas:**
- Editor integration: VSCode extension for profile switching
- Git hooks: Auto-suggest on branch checkout
- Calendar integration: Time-based auto-switching
- Team profiles: Shared profile templates

## API Reference

### ProfileParser

```python
from dopemux.profile_parser import ProfileParser

parser = ProfileParser(validate_mcps=True)
collection = parser.parse_directory(Path("profiles"), pattern="*.yaml")

for profile in collection.profiles:
    print(f"{profile.name}: {len(profile.mcps)} MCPs")
```

### ProfileDetector

```python
from dopemux.profile_detector import ProfileDetector, DetectionContext

detector = ProfileDetector(Path("profiles"))

# Auto-detect
match = detector.detect()
print(f"Best: {match.profile_name} ({match.confidence:.0%})")

# Custom context
context = DetectionContext(
    current_dir=Path.cwd() / "src",
    git_branch="feature/auth"
)
match = detector.detect(context)
```

### ProfileAnalytics

```python
from dopemux.profile_analytics import log_switch_sync, get_stats_sync

# Log a switch
log_switch_sync(
    workspace_id="/path/to/project",
    to_profile="developer",
    trigger="manual"
)

# Get statistics
stats = get_stats_sync(
    workspace_id="/path/to/project",
    days_back=30
)

print(f"Total switches: {stats.total_switches}")
print(f"Most used: {stats.most_used_profile}")
```

## Contributing

When adding features to the profile system:

1. **Maintain ADHD optimizations**: Max 3 choices, clear visuals, gentle guidance
2. **Test with real profiles**: Use the 5 existing profiles for validation
3. **Update documentation**: Keep user and developer docs in sync
4. **Log metrics**: Use ConPort for persistence
5. **Follow patterns**: Match existing code style and structure

## Support

- 📖 User Guide: `docs/guides/PROFILE_USER_GUIDE.md`
- 📖 Migration Guide: `docs/guides/PROFILE_MIGRATION_GUIDE.md`
- 🔧 YAML Schema: `docs/PROFILE-YAML-SCHEMA.md`
- 🐛 Issues: GitHub issue tracker

---

**Status**: Production-ready (6 commits, 3,087 lines)
**Version**: Epic 4 implementation (Tasks 4.2, 4.4, 4.5, 4.6)
