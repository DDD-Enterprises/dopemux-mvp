---
description: "Comprehensive session save with ConPort context and file state preservation"
allowed-tools: [
  "Bash", "Read", "Write", "Grep",
  "mcp__conport__update_active_context",
  "mcp__conport__log_decision",
  "mcp__conport__log_progress",
  "mcp__conport__batch_log_items"
]
model: "claude-sonnet-4-5-20250929"
---

# /dx:save - Comprehensive Session Save

Save complete development session: work context, git state, open files, decisions, and ADHD metrics.

**Purpose**: ADHD-friendly session preservation that captures EVERYTHING so you can restore exactly where you left off.

---

## Step 1: Auto-Capture Current State

**Capture Git State** (automatically):
```bash
Use Bash:
git branch --show-current > /tmp/dx_save_branch
git status --porcelain > /tmp/dx_save_status
git log --oneline -5 > /tmp/dx_save_commits
git diff --stat > /tmp/dx_save_diff
```

**Count Recent Activity**:
- Changed files: Count from git status
- Recent commits: Last 5 commits
- Current branch: For restoration

**Capture Open File Context** (from user):
Ask: "Which files are you currently working on? (comma-separated or just hit enter to skip)"
Store list of active files.

---

## Step 2: Gather Work Context

Ask user (with smart prompting):
```
Session Save - Quick Context Capture
═══════════════════════════════════════════

What were you working on? (one sentence)
> [If empty, suggest from git commits or ConPort focus]

What did you accomplish this session?
> [If empty, offer to generate from git diff]

What's next when you return?
> [If empty, suggest continuing current file]

Any blockers or issues? (optional)
>
```

**Smart Suggestions**:
- If recent commits: Suggest "Working on [commit messages]"
- If ConPort focus exists: Pre-fill with current_focus
- If git diff shows files: "Modified [file names]"

---

## Step 3: Check for Decisions

**Automatically detect decision-worthy work**:
```bash
Use Grep to check recent commits and changes:
- Architecture changes (new services, major refactors)
- Configuration changes (docker-compose, .env)
- ADR creation or updates
```

If detected:
- Show: "Looks like you made architectural decisions. Log to ConPort? (y/n)"
- If yes: Guide through decision logging with mcp__conport__log_decision

If no architectural changes:
- Skip decision logging (don't ask if not needed)

---

## Step 4: Capture ADHD Metrics

**Query ADHD Engine** (if running):
```bash
Use Bash:
curl -s http://localhost:8095/api/v1/energy-level/current_user
curl -s http://localhost:8095/api/v1/attention-state/current_user
```

Extract:
- Final energy level
- Final attention state
- Session quality indicators

**Calculate Session Stats**:
- Session duration (from active_context.session_start)
- 25-minute chunks completed
- Break compliance (did user take breaks?)

---

## Step 5: Save to ConPort

**Update Active Context** with comprehensive state:
```
mcp__conport__update_active_context with:
  workspace_id: "/Users/hue/code/dopemux-mvp"
  patch_content: {
    "current_focus": "USER_SUMMARY",
    "completed_tasks": ["USER_ACCOMPLISHMENTS"],
    "next_steps": ["USER_NEXT_STEPS"],
    "blockers": ["USER_BLOCKERS"],
    "session_saved": "CURRENT_TIMESTAMP",
    "session_end": "CURRENT_TIMESTAMP",
    "git_state": {
      "branch": "CURRENT_BRANCH",
      "changed_files": CHANGED_COUNT,
      "recent_commits": ["COMMIT_LIST"]
    },
    "open_files": ["USER_FILE_LIST"],
    "adhd_metrics": {
      "final_energy": "ENERGY_LEVEL",
      "final_attention": "ATTENTION_STATE",
      "session_duration": "DURATION",
      "chunks_completed": CHUNKS,
      "break_compliance": "COMPLIANCE"
    }
  }
```

**If tasks were completed**, create progress entries:
```
For each completed item mentioned:
  mcp__conport__log_progress with status="DONE" and description
```

---

## Step 6: Create Session Backup File

**Write session snapshot** (for extra safety):
```bash
Use Write to create: .dopemux/sessions/session-TIMESTAMP.json
Content: {
  "timestamp": "CURRENT_TIMESTAMP",
  "focus": "USER_SUMMARY",
  "accomplished": ["LIST"],
  "next_steps": ["LIST"],
  "git_branch": "BRANCH",
  "git_status": "STATUS_OUTPUT",
  "open_files": ["LIST"],
  "adhd_metrics": {...},
  "conport_synced": true
}
```

---

## Step 7: Success Summary

Show comprehensive save confirmation:
```
✅ Session Saved - Complete State Preserved
═══════════════════════════════════════════

Session Summary:
📋 Focus: [USER_SUMMARY]
✅ Accomplished: [COUNT] items
⏭️  Next: [NEXT_STEPS]
🌳 Git: [BRANCH] with [COUNT] changes

ADHD Metrics:
⚡ Final Energy: [ENERGY]
👁️  Final Attention: [ATTENTION]
⏱️  Session: [DURATION] ([CHUNKS] × 25min)
☕ Break Compliance: [COMPLIANCE]

Saved To:
• ConPort active_context (synced)
• Session file: .dopemux/sessions/session-TIMESTAMP.json
• [If decisions]: ConPort decision #XXX

Next Session:
• /dx:load - Restore this complete state
• All context preserved (files, git, focus, metrics)

Safe to close! Everything is saved. 💙
═══════════════════════════════════════════
```

---

## Step 8: Cleanup & Recommendations

**Check session length**:
- If > 90 minutes: "Great long session! Consider taking a longer break."
- If < 25 minutes: "Short session - that's okay! Progress is progress."
- If 25-50 minutes: "Perfect ADHD-friendly session length!"

**Remind about break** (if needed):
- Calculate time since last break
- If > 60 minutes: "Remember to take a break! Your brain needs it."

---

## Error Handling

**If ConPort unavailable**:
- Still create session file in .dopemux/sessions/
- Show: "⚠️ ConPort unavailable - saved locally only"
- Show: "Sync to ConPort next session with /dx:load"

**If ADHD Engine unavailable**:
- Skip ADHD metrics
- Continue with context save
- Note in save file: "adhd_metrics": "unavailable"

**If git not initialized**:
- Skip git state capture
- Still save work context
- Note: "Not a git repository"

---

## Success Criteria

- ✅ ConPort active_context updated with full state
- ✅ Session backup file created
- ✅ Git state captured
- ✅ ADHD metrics recorded (if available)
- ✅ User feels confident context is preserved
- ✅ Clear next steps for restoration

---

## Notes for Claude

**Be comprehensive**: Capture more rather than less
**Be quick**: Don't make user answer 10 questions (3-4 max)
**Be reassuring**: Emphasize that everything is safe
**Be ADHD-friendly**: Celebrate saving as good habit
**Suggest rest**: If long session, encourage break

