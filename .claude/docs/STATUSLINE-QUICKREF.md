# Statusline Quick Reference

**One-page cheat sheet for the Dopemux ADHD-optimized statusline**

---

## Symbol Legend

### Connection Status
| Symbol | Meaning |
|--------|---------|
| 📊 | ConPort connected - context preserved |
| 📴 | ConPort disconnected - context at risk |

### Energy Levels
| Symbol | State | Best For |
|--------|-------|----------|
| ⚡ | Hyperfocus | Complex architecture, deep debugging |
| ↑ | High | New features, challenging problems |
| • | Medium | Regular development, bug fixes |
| ↓ | Low | Documentation, simple edits |
| ⇣ | Very Low | **Take a break!** |

### Attention States
| Symbol | State | Action |
|--------|-------|--------|
| ·👁️✨ | Hyperfocused | Celebrate! Protect this state |
| ·👁️ | Focused | Keep going, you're productive |
| ·👁️~ | Transitioning | Be gentle with yourself |
| ·👁️🌀 | Scattered | Simplify current task |
| ·👁️💥 | Overwhelmed | **Stop. Break time.** |

### Break Warnings
| Symbol | Urgency | Action |
|--------|---------|--------|
| ☕ (yellow) | Soon | Finish task (5-10min), then break |
| ☕! (red) | **NOW** | Stop immediately, 10-15min break |

### Accommodations
| Symbol | Meaning |
|--------|---------|
| ·🛡️ | Hyperfocus protection active |

### Token Usage Colors
| Color | Range | Meaning | Action |
|-------|-------|---------|--------|
| 🟢 Green | 0-60% | Plenty of context | Work freely |
| 🟡 Yellow | 60-80% | Filling up | Wrap up soon, log decisions |
| 🔴 Red | 80-100% | Near limit | **Save now!** Autocompact coming |

---

## Common Commands

### Start Session
```bash
mcp__conport__update_active_context \
  --workspace_id $(pwd) \
  --patch_content "{
    \"current_focus\": \"Your task here\",
    \"session_start\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"
  }"
```

### Change Focus (Keep Timer)
```bash
mcp__conport__update_active_context \
  --workspace_id $(pwd) \
  --patch_content "{\"current_focus\": \"New task\"}"
```

### Log Decision
```bash
mcp__conport__log_decision \
  --workspace_id $(pwd) \
  --summary "Decision summary" \
  --rationale "Why you decided this" \
  --tags "tag1,tag2"
```

### Reset Session Timer
```bash
mcp__conport__update_active_context \
  --workspace_id $(pwd) \
  --patch_content "{\"session_start\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}"
```

---

## Troubleshooting Quick Fixes

### 📴 ConPort Disconnected
```bash
# Check database exists
ls -la context_portal/context.db

# Initialize if missing
mcp__conport__get_active_context --workspace_id $(pwd)
```

### 0K/200K Token Usage
```bash
# Enable debug
# Edit .claude/statusline.sh, uncomment lines 9-11

# Check logs
cat /tmp/statusline_debug.json | jq .
```

### No Session Time
```bash
# Reset to current time
mcp__conport__update_active_context \
  --workspace_id $(pwd) \
  --patch_content "{\"session_start\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}"
```

### 💤 ADHD Engine Sleeping
```bash
# Start service
cd services/adhd-engine
uvicorn main:app --port 8095 --reload
```

---

## Energy-Task Matching

| Energy | Task Complexity | Examples |
|--------|-----------------|----------|
| ⚡ Hyperfocus | **Maximum** | System architecture, complex algorithms, deep refactoring |
| ↑ High | **High** | New features, challenging bugs, learning new tech |
| • Medium | **Moderate** | Regular development, testing, code review |
| ↓ Low | **Light** | Documentation, simple fixes, formatting |
| ⇣ Very Low | **None** | **BREAK TIME** - Don't push through |

---

## Context Window Management

### 🟢 Green Zone (0-60%)
- ✅ Work freely
- ✅ Log decisions as you go
- ✅ No urgency

### 🟡 Yellow Zone (60-80%)
- ⚠️ Finish current subtask
- ⚠️ Log important decisions NOW
- ⚠️ Prepare for potential session end

**Action:**
```bash
mcp__conport__log_decision \
  --workspace_id $(pwd) \
  --summary "Current progress checkpoint" \
  --implementation_details "What you've done" \
  --tags "checkpoint"
```

### 🔴 Red Zone (80-100%)
- 🚨 **SAVE IMMEDIATELY**
- 🚨 Log ALL critical context
- 🚨 Consider new session

**Emergency Save:**
```bash
# Log everything important RIGHT NOW
mcp__conport__log_decision \
  --workspace_id $(pwd) \
  --summary "Emergency context save at 85%" \
  --rationale "$(cat current_thinking.txt)" \
  --tags "emergency,context-save"
```

---

## Break Protocol

### When You See ☕ (Yellow)
1. Check timer: How long have you been working?
2. Finish current small task (< 10 minutes)
3. Log progress to ConPort
4. 5-minute break:
   - Stand up
   - Look away from screen
   - Walk around
   - Hydrate

### When You See ☕! (Red)
1. **STOP IMMEDIATELY** - Don't finish "just one more thing"
2. Save all work
3. Log critical context
4. 10-15 minute break:
   - Leave your desk
   - Physical movement
   - No screens
   - Complete mental reset

**Trust the system** - It's protecting you from burnout

---

## Focus Tag Patterns

Prefix your focus with categories for better organization:

| Prefix | Example | Purpose |
|--------|---------|---------|
| `[FEAT]` | `[FEAT] User authentication` | New feature development |
| `[BUG]` | `[BUG] Login redirect loop` | Bug fixing |
| `[REFACTOR]` | `[REFACTOR] Auth middleware` | Code improvement |
| `[LEARN]` | `[LEARN] OAuth2 flow` | Learning/research |
| `[DOC]` | `[DOC] API documentation` | Documentation |
| `[TEST]` | `[TEST] Auth test coverage` | Testing |

---

## Terminal Width Optimization

| Width | Display Level | What You See |
|-------|---------------|--------------|
| < 90 cols | **Minimal** | Essential only: dir, branch, tokens, model |
| 90-120 cols | **Standard** | + Focus, time, energy, attention |
| > 120 cols | **Full** | + Extended states, accommodations, warnings |

**Recommendation:** Use at least 100 columns for optimal ADHD experience

---

## Files to Know

| File | Purpose |
|------|---------|
| `.claude/statusline.sh` | Main statusline script |
| `.claude/docs/STATUSLINE.md` | Full documentation |
| `context_portal/context.db` | ConPort SQLite database |
| `/tmp/statusline_debug.json` | Debug: latest input |
| `/tmp/statusline_debug.log` | Debug: token extraction log |

---

## Emergency Checklist

**When statusline shows problems:**

- [ ] ConPort 📴? → Check `context_portal/context.db` exists
- [ ] 0K tokens? → Enable debug, check transcript path
- [ ] No session time? → Reset session_start timestamp
- [ ] ADHD Engine 💤? → Start service on port 8095
- [ ] Wrong focus? → Update active_context
- [ ] Break warning ignored? → **TAKE THE BREAK NOW**

---

## Resources

- **Full Docs:** `.claude/docs/STATUSLINE.md`
- **Main README:** `README.md`
- **ConPort:** `docker/mcp-servers/conport/`
- **ADHD Engine:** `services/adhd-engine/`

---

**Remember:** The statusline is here to support you, not stress you. Trust its signals. 💚
