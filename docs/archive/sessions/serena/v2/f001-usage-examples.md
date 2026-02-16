---
id: f001-usage-examples
title: F001 Usage Examples
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: F001 Usage Examples (explanation) for dopemux documentation and developer
  workflows.
---
# F001 Enhanced - Usage Examples

Quick reference for common scenarios with F001 Enhanced.

---

## Scenario 1: Starting New Feature

**Context**: You're about to start a new authentication refactor

```bash
# Call enhanced detection
result = detect_untracked_work_enhanced(session_number=1)
```

**Response**:
```json
{
  "status": "all_clear",
  "message": "✅ All work is tracked or below threshold"
}
```

**Action**: ✅ Safe to start new work!

---

## Scenario 2: First False-Start Alert

**Context**: Working on API refactor, 7 files changed, forgot to track

```bash
result = detect_untracked_work_enhanced(session_number=1)
```

**Response**:
```json
{
  "status": "untracked_work_detected",
  "false_starts_dashboard": {
    "total_unfinished": 3,
    "message": "📊 You have 3 unfinished projects. Let's track this one properly!"
  },
  "design_first_recommendation": {
    "should_create_design": true,
    "document_type": "RFC",
    "message": "📐 7 files + API changes → Create RFC first"
  },
  "suggested_actions": {
    "options": [
      {"action": "design_first", "recommended": true},
      {"action": "track", "recommended": true}
    ]
  }
}
```

**Actions**:
1. ✅ Create RFC for API design
1. ✅ Track in ConPort after design approval

---

## Scenario 3: Overcommitment Warning

**Context**: Already have 3 tasks in progress, starting another

```bash
result = detect_untracked_work_enhanced(session_number=1)
```

**Response**:
```json
{
  "prioritization_context": {
    "in_progress": 3,
    "overcommitment_risk": "medium",
    "recommendation": "⚠️ Several tasks active - is this new work more important?",
    "message": "📋 CURRENT COMMITMENTS\nActive: 8 tasks\n🟡 OVERCOMMITMENT RISK: MEDIUM"
  }
}
```

**Decision Tree**:
- **Truly urgent?** → Track and pause one existing task
- **Can wait?** → Finish one existing task first
- **Not sure?** → Review in-progress tasks, pick one to complete

---

## Scenario 4: Relevant Abandoned Work Found

**Context**: Starting auth work, forgot about abandoned auth refactor

```bash
result = detect_untracked_work_enhanced(session_number=1)
```

**Response**:
```json
{
  "revival_suggestions": {
    "count": 1,
    "suggestions": [{
      "work_name": "Authentication refactor",
      "relevance_score": 0.78,
      "action": "resume",
      "message": "▶️ Highly relevant - consider resuming this instead?"
    }]
  }
}
```

**Actions**:
1. ✅ Review abandoned work files
1. ✅ Resume if context is clear
1. ✅ Or merge ideas into new approach

---

## Scenario 5: Multiple Enhancements Triggered

**Context**: 8 files, 4 dirs, 47 unfinished projects, 5 active tasks

```bash
result = detect_untracked_work_enhanced(session_number=2)  # Second detection
```

**Response**:
```json
{
  "false_starts_dashboard": {
    "total_unfinished": 47,
    "message": "📊 You have 47 unfinished projects. Sure you want to make it 48?"
  },
  "design_first_recommendation": {
    "confidence": 0.75,
    "document_type": "ADR",
    "message": "📐 8 files + 4 directories + architecture keywords → Create ADR"
  },
  "revival_suggestions": {
    "count": 2,
    "message": "🔄 2 abandoned projects might be relevant"
  },
  "prioritization_context": {
    "overcommitment_risk": "medium",
    "message": "📋 5 tasks in progress - is this truly urgent?"
  },
  "suggested_actions": {
    "options": [
      {"action": "resume_abandoned", "recommended": true},
      {"action": "design_first", "recommended": true},
      {"action": "track", "recommended": false}
    ],
    "adhd_guidance": "✨ The most productive choice isn't always starting new work"
  }
}
```

**Recommended Flow**:
1. **Check abandoned work** (E3) - Can you resume instead?
1. **Review active tasks** (E4) - Should you finish one first?
1. **If truly new & urgent** → Create ADR (E2) before implementing
1. **Track in ConPort** after design

---

## Integration Patterns

### Pattern 1: Session Start Hook

```python
# In your development workflow
async def start_development_session():
    # Always check for untracked work at session start
    result = await detect_untracked_work_enhanced(session_number=1)

    if result["status"] == "untracked_work_detected":
        # Show dashboard
        print(result["false_starts_dashboard"]["message"])

        # Handle design-first
        if "design_first_recommendation" in result:
            print(result["design_first_recommendation"]["message"])
            prompt_user("Create design document?")

        # Handle revival
        if "revival_suggestions" in result:
            print(result["revival_suggestions"]["message"])
            prompt_user("Resume abandoned work?")

        # Handle priority
        if "prioritization_context" in result:
            print(result["prioritization_context"]["message"])
            prompt_user("Start new work or finish existing?")
```

### Pattern 2: Pre-Commit Hook

```python
# Before committing, check if work was tracked
async def pre_commit_check():
    result = await detect_untracked_work_enhanced(session_number=3)  # High sensitivity

    if result["status"] == "untracked_work_detected":
        print("⚠️  This work isn't tracked in ConPort")
        print(result["false_starts_dashboard"]["message"])

        choice = prompt_user("Track now before committing?")
        if choice == "yes":
            # Create ConPort task
            track_work(result["work_summary"])
```

### Pattern 3: Daily Standup

```python
# Morning review
async def morning_standup():
    # Check yesterday's untracked work
    result = await detect_untracked_work_enhanced(session_number=2)

    if result.get("revival_suggestions"):
        print("🔄 Abandoned work from yesterday:")
        for suggestion in result["revival_suggestions"]["suggestions"]:
            print(f"  • {suggestion['work_name']} ({suggestion['relevance_score']:.0%} relevant)")

    if result.get("prioritization_context"):
        print("📋 Today's focus:")
        print(result["prioritization_context"]["message"])
```

---

## CLI Examples

### Basic Detection

```bash
# Via MCP client
mcp call serena-v2 detect_untracked_work_enhanced '{
  "session_number": 1,
  "show_details": false
}'
```

### Detailed Detection

```bash
# With confidence breakdown
mcp call serena-v2 detect_untracked_work_enhanced '{
  "session_number": 2,
  "show_details": true
}'
```

### Parsing Results

```bash
# Extract just the dashboard
result=$(mcp call serena-v2 detect_untracked_work_enhanced '{"session_number": 1}')
echo $result | jq '.false_starts_dashboard.message'
```

---

## Workflow Examples

### Workflow 1: ADHD-Optimized Start

```
1. Session Start
   ↓
1. detect_untracked_work_enhanced
   ↓
1. Dashboard shows 47 unfinished
   ↓
1. Revival suggests "Auth refactor" (78% match)
   ↓
1. Review abandoned work → Resume it ✅
   ↓
1. Complete auth refactor (finish existing > start new)
```

### Workflow 2: Design-First Enforcement

```
1. Start new substantial feature
   ↓
1. Write code (8 files, 4 dirs)
   ↓
1. detect_untracked_work_enhanced
   ↓
1. E2 triggers: "Create ADR" (0.75 confidence)
   ↓
1. Stop coding → Create ADR ✅
   ↓
1. Get team feedback
   ↓
1. Resume implementation with clarity
```

### Workflow 3: Overcommitment Prevention

```
1. Excited about new idea
   ↓
1. detect_untracked_work_enhanced
   ↓
1. E4 shows: 5 in-progress tasks (risk: medium)
   ↓
1. E3 suggests: 2 relevant abandoned projects
   ↓
1. Realize: Should finish existing work ✅
   ↓
1. Pick one in-progress task → Complete it
   ↓
1. THEN start new idea
```

---

## Testing Examples

### Unit Test: E2 Heuristics

```python
def test_design_first_with_architecture():
    detector = DesignFirstDetector(workspace)

    git_detection = {
        "files": ["core/orchestrator.py", "core/engine.py"],  # Keywords!
        "new_files_created": ["core/orchestrator.py"]
    }

    result = detector.should_prompt_for_design(git_detection)

    assert result["should_prompt"] == True  # 0.35 > 0.5? Need another heuristic
    assert "architecture_keywords" in result["heuristics_matched"]
```

### Integration Test: Full Flow

```python
async def test_full_enhanced_detection():
    detector = UntrackedWorkDetector(workspace, workspace_id)

    result = await detector.detect_with_enhancements(
        conport_client=mock_conport,
        session_number=2
    )

    assert result["has_untracked_work"] == True
    assert "false_starts" in result["enhancements"]
    assert result["enhancements"]["false_starts"]["summary"]["total_unfinished"] == 47
```

---

## Configuration Examples

### Custom Thresholds

```python
# For highly sensitive team
detector.adaptive_thresholds = {
    1: 0.65,  # Lower threshold (more sensitive)
    2: 0.55,
    3: 0.50
}
```

### Custom Grace Period

```python
# For quick experimental team
detector.grace_period_minutes = 60  # 1 hour instead of 30 min
```

---

**See Also**:
- [User Guide](F001_ENHANCED_USER_GUIDE.md)
- [Test Results](../F001_TEST_RESULTS.md)
- [Build Summary](../F001_ENHANCED_BUILD_SUMMARY.md)
