# Statusline Visual Examples

**Real-world statusline outputs and what they mean**

---

## Ideal Development States

### Perfect Flow State 🎯
```
dopemux-mvp main | 📊 Refactoring auth module [1h 12m] | 🧠⚡·👁️✨ 45K/200K (22%) | Sonnet 4.5
```

**What's happening:**
- ✅ ConPort connected and tracking
- ✅ Clear focus: Refactoring auth module
- ✅ Good session length: 1 hour 12 minutes
- ✅ **Hyperfocus state** (⚡ energy + 👁️✨ attention)
- ✅ Plenty of context: only 22% used
- ✅ Sonnet 4.5 active

**Action:** Keep going! You're in the zone. Protected by hyperfocus accommodations (🛡️ may appear).

---

### Productive Regular Work 💪
```
dopemux-mvp feature/login | 📊 Implementing JWT tokens [45m] | 🧠•·👁️ 78K/200K (39%) | Sonnet 4.5
```

**What's happening:**
- ✅ Feature branch active
- ✅ Focused on JWT implementation
- ✅ Medium energy (•), focused attention (👁️)
- ✅ Under 45 minutes - fresh session
- ✅ Good context usage

**Action:** Maintain current pace. Regular productive state.

---

## Warning States

### Approaching Context Limit ⚠️
```
dopemux-mvp main | 📊 Debugging login flow [2h 45m] | 🧠↓·👁️ 162K/200K (81%) | Sonnet 4.5
```

**What's happening:**
- ⚠️ **RED ZONE** - 81% context used
- ⚠️ Long session - 2h 45m
- ⚠️ Low energy (↓)
- ⚠️ Still focused, but resources depleting

**Action:**
1. **SAVE WORK NOW** - Autocompact imminent
2. Log critical decisions:
   ```bash
   mcp__conport__log_decision \
     --workspace_id $(pwd) \
     --summary "Login flow debugging - identified session expiry bug" \
     --implementation_details "Issue in token refresh logic, line 145" \
     --tags "debug,auth,urgent"
   ```
3. Finish current debugging step
4. Take a break
5. Consider starting new session

---

### Break Needed (Soon) ☕
```
dopemux-mvp main | 📊 Code review [1h 35m] | 🧠•·👁️~ ☕ 52K/200K (26%) | Sonnet 4.5
```

**What's happening:**
- ☕ **Yellow break warning** - break suggested soon
- Attention transitioning (👁️~) - focus starting to waver
- Been working for 1h 35m
- Medium energy still okay

**Action:**
1. Finish current code review (< 10 minutes)
2. Log review findings
3. Take 5-minute break
4. Return refreshed

---

### Break Needed (NOW) 🚨
```
dopemux-mvp main | 📊 Bug fixing [2h 15m] | 🧠⇣·👁️🌀 ☕! 145K/200K (72%) | Sonnet 4.5
```

**What's happening:**
- 🚨 **RED break warning** - urgent break needed
- 🚨 Very low energy (⇣)
- 🚨 Scattered attention (👁️🌀)
- Long session approaching context limit

**Action:**
1. **STOP IMMEDIATELY** - Don't "just finish this one thing"
2. Save everything:
   ```bash
   # Emergency context save
   mcp__conport__log_decision \
     --workspace_id $(pwd) \
     --summary "Emergency break at 72% context" \
     --implementation_details "$(git diff HEAD)" \
     --tags "emergency,wip"
   ```
3. Close laptop, leave desk
4. 15-minute break minimum
5. Physical movement, hydrate, no screens

**Why trust it:** System detected cognitive overload before you consciously felt it. Protect your brain.

---

## Problem States

### ConPort Disconnected 📴
```
dopemux-mvp main | 📴 [56m] | 🧠•·👁️ 32K/200K (16%) | Sonnet 4.5
```

**What's happening:**
- ❌ ConPort disconnected - context not being preserved
- ❌ No current focus shown
- ❌ Session tracking limited

**Action:**
```bash
# Check database
ls -la context_portal/context.db

# Initialize if missing
mcp__conport__get_active_context --workspace_id $(pwd)

# Set focus
mcp__conport__update_active_context \
  --workspace_id $(pwd) \
  --patch_content "{
    \"current_focus\": \"Your task\",
    \"session_start\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"
  }"
```

---

### Token Tracking Not Working
```
dopemux-mvp main | 📊 Feature development | 🧠•·👁️ 0K/200K (0%) | Sonnet 4.5
```

**What's happening:**
- ❌ Token usage showing 0K - calculation failed
- Everything else working

**Action:**
```bash
# Enable debug mode
# Edit .claude/statusline.sh
# Uncomment lines 9-11

# Check what Claude Code is sending
cat /tmp/statusline_debug.json | jq .

# Check transcript path
jq -r '.transcript_path' /tmp/statusline_debug.json
```

---

### ADHD Engine Offline 💤
```
dopemux-mvp main | 📊 Code review [1h 15m] | 💤 95K/200K (47%) | Sonnet 4.5
```

**What's happening:**
- 💤 ADHD Engine not responding
- No energy/attention tracking
- No break warnings

**Action:**
```bash
# Start ADHD Engine
cd services/adhd-engine
uvicorn main:app --port 8095 --reload

# Verify running
curl -s http://localhost:8095/health | jq .
```

---

## Special States

### Hyperfocus Protected 🛡️
```
dopemux-mvp main | 📊 System architecture design [3h 45m] | 🧠⚡·👁️✨·🛡️ 125K/200K (62%) | Sonnet 4.5
```

**What's happening:**
- ⚡👁️✨ Deep hyperfocus state
- 🛡️ Protection active - suppressing interruptions
- Long session (3h 45m) but productive
- Context at 62% - monitoring but not alarming

**System behavior:**
- Break warnings delayed
- Notifications minimized
- Gentle reminders only
- Protecting the flow state

**User awareness:**
- You're in a precious state
- Stay hydrated
- But don't force-break unless ☕! appears

---

### Overwhelmed State 💥
```
dopemux-mvp main | 📊 Debugging production issue [45m] | 🧠↓·👁️💥 ☕! 88K/200K (44%) | Sonnet 4.5
```

**What's happening:**
- 💥 Cognitive overload detected
- ☕! Urgent break needed
- Low energy + overwhelmed attention
- Despite only 45 minutes - stress detected

**Action:**
1. **STOP NOW** - This is not sustainable
2. Deep breath, close eyes for 30 seconds
3. Step away from computer
4. 15-minute minimum break
5. When returning: simplify the problem
6. Consider asking for help

**Why it matters:** Production stress + low energy = recipe for mistakes. The system is protecting you.

---

## Context Window Scenarios

### Green Zone - Working Freely 🟢
```
dopemux-mvp main | 📊 Feature implementation [35m] | 🧠↑·👁️ 45K/200K (22%) | Sonnet 4.5
```
- ✅ 22% - Plenty of room
- ✅ Work on complex features
- ✅ No need to think about context

---

### Yellow Zone - Wrap Up Soon 🟡
```
dopemux-mvp main | 📊 API integration [1h 50m] | 🧠•·👁️ 138K/200K (69%) | Sonnet 4.5
```
- ⚠️ 69% - Entering yellow zone
- ⚠️ Start wrapping up
- ⚠️ Log important decisions now:
  ```bash
  mcp__conport__log_decision \
    --workspace_id $(pwd) \
    --summary "API integration patterns decided" \
    --implementation_details "..." \
    --tags "api,architecture"
  ```

---

### Red Zone - Save Now! 🔴
```
dopemux-mvp main | 📊 Complex refactoring [2h 30m] | 🧠•·👁️ 174K/200K (87%) | Sonnet 4.5
```
- 🚨 87% - DANGER ZONE
- 🚨 Autocompact in ~13K tokens
- 🚨 Save EVERYTHING NOW:
  ```bash
  # Emergency dump
  echo "Current state: $(git status)" > /tmp/context_save.txt
  git diff HEAD >> /tmp/context_save.txt

  mcp__conport__log_decision \
    --workspace_id $(pwd) \
    --summary "Emergency context save - 87% full" \
    --implementation_details "$(cat /tmp/context_save.txt)" \
    --tags "emergency,context-save"
  ```

---

## Model Variants

### Sonnet 4.5 Standard (200K)
```
dopemux-mvp main | 📊 Development [1h 15m] | 🧠•·👁️ 125K/200K (62%) | Sonnet 4.5
```

### Sonnet 4.5 Extended (1M) - Regional
```
dopemux-mvp main | 📊 Development [1h 15m] | 🧠•·👁️ 125K/1000K (12%) | Sonnet 4.5
```

### Opus (200K)
```
dopemux-mvp main | 📊 Analysis [45m] | 🧠•·👁️ 85K/200K (42%) | Opus
```

### Haiku (200K)
```
dopemux-mvp main | 📊 Quick task [15m] | 🧠•·👁️ 12K/200K (6%) | Haiku
```

---

## Terminal Width Variations

### Narrow Terminal (< 90 columns)
```
dopemux-mvp | 📊 [1h] | 🧠• 125K/200K (62%) | Sonnet 4.5
```
- Minimal display
- Essential info only
- Focus shortened
- Attention state hidden (unless critical)

### Standard Terminal (90-120 columns)
```
dopemux-mvp main | 📊 Feature dev [1h 15m] | 🧠•·👁️ 125K/200K (62%) | Sonnet 4.5
```
- Standard display
- Most information shown
- Good balance

### Wide Terminal (> 120 columns)
```
dopemux-mvp main | 📊 Implementing authentication system [1h 15m] | 🧠•·👁️·🛡️ ☕ 125K/200K (62%) | Sonnet 4.5
```
- Full display
- Extended focus description
- All accommodation indicators
- Full attention states

---

## Progressive Disclosure Examples

### Minimal State (Essential Only)
```
dopemux-mvp main | 125K/200K (62%) | Sonnet 4.5
```
- No ConPort (disconnected)
- No ADHD Engine (offline)
- Just basics: directory, branch, tokens, model

### Partial State (ConPort Only)
```
dopemux-mvp main | 📊 Feature work [1h 15m] | 125K/200K (62%) | Sonnet 4.5
```
- ConPort connected
- Focus and time shown
- ADHD Engine offline (no energy/attention)

### Full State (Everything)
```
dopemux-mvp main | 📊 Deep architectural work [2h 45m] | 🧠⚡·👁️✨·🛡️ 125K/200K (62%) | Sonnet 4.5
```
- Everything active
- All systems operational
- Maximum context awareness

---

## Decision Point Examples

### Should I Take a Break?

**No - Keep Working:**
```
dopemux-mvp | 📊 [25m] | 🧠↑·👁️ 15K/200K (7%)
```
- Fresh session (25m)
- High energy
- Focused attention
- No warnings

**Maybe - Finish Task First:**
```
dopemux-mvp | 📊 [1h 45m] | 🧠•·👁️~ ☕ 95K/200K (47%)
```
- Yellow warning
- Attention transitioning
- Medium energy
- Finish current subtask, then break

**Yes - Break Now:**
```
dopemux-mvp | 📊 [2h 15m] | 🧠↓·👁️🌀 ☕! 145K/200K (72%)
```
- Red urgent warning
- Low energy
- Scattered attention
- **STOP IMMEDIATELY**

---

### Should I Save My Work?

**No Urgency:**
```
dopemux-mvp | 📊 [45m] | 🧠•·👁️ 35K/200K (17%)
```
- 17% context - plenty of room
- Regular saves okay

**Start Saving Important Decisions:**
```
dopemux-mvp | 📊 [1h 30m] | 🧠•·👁️ 135K/200K (67%)
```
- 67% context - yellow zone
- Log key decisions now
- Don't wait

**EMERGENCY SAVE EVERYTHING:**
```
dopemux-mvp | 📊 [2h 30m] | 🧠↓·👁️ 182K/200K (91%)
```
- 91% context - RED ZONE
- Autocompact in ~18K tokens
- Save ALL context NOW
- Consider ending session

---

## Legend Summary

### Quick Reference
| Symbol | Meaning | Action Required |
|--------|---------|-----------------|
| 📊 | Connected | ✅ None - working well |
| 📴 | Disconnected | ⚠️ Fix ConPort |
| ⚡↑•↓⇣ | Energy levels | ℹ️ Match tasks to energy |
| 👁️✨/👁️/👁️~/👁️🌀/👁️💥 | Attention states | ℹ️ Self-awareness |
| ☕ | Break soon | ⚠️ Plan to break |
| ☕! | Break NOW | 🚨 Stop immediately |
| 🛡️ | Protected | ✅ Flow state protected |
| 🟢/🟡/🔴 | Context zones | ℹ️ Manage context |

---

**Remember:** The statusline is your co-pilot, not your boss. Use it to make informed decisions about your work and well-being. 💚
