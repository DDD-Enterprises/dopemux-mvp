---
id: DASHBOARD_DAY4_TEST_GUIDE
title: Dashboard_Day4_Test_Guide
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Dashboard_Day4_Test_Guide (explanation) for dopemux documentation and developer
  workflows.
---
# Dashboard Day 4 - Quick Test Guide 🧪

**How to test the new drill-down modals**

---

## 🚀 Quick Start

```bash
# Start the dashboard
python dopemux_dashboard.py

# Or in tmux
tmux split-window -h "python dopemux_dashboard.py"
```

---

## ⌨️ Keyboard Shortcuts to Test

### Drill-Down Modals (NEW! 🎯)

```
d  →  Task Details Modal
      • Shows full task context
      • Metrics, insights, history
      • Actions: complete, priority, notes
      • Press Esc to close

l  →  Service Logs Modal
      • Live log viewer
      • Color-coded by level
      • Filter and search
      • Press Esc to close

p  →  Pattern Details Modal
      • Behavioral pattern analysis
      • Success rate, occurrences
      • Recommendations
      • Press Esc to close

h  →  Metric History Modal
      • Historical graphs
      • 7-day trends
      • Annotations and insights
      • Press Esc to close
```

### Existing Features

```
?  →  Help Screen
      • Shows all keybindings
      • Updated with drill-down docs

f  →  Focus Mode
      • Enlarges ADHD panel
      • Dims services panel

t  →  Cycle Themes
      • Mocha → Nord → Dracula

b  →  Force Break
      • 5-minute break timer

n  →  Toggle Notifications
      • Enable/disable alerts

r  →  Refresh
      • Force update all panels

q  →  Quit
      • Exit dashboard
```

---

## 🧪 Test Cases

### Test 1: Task Detail Modal

**Steps:**
1. Start dashboard
1. Press `d`
1. Verify modal opens centered
1. Check content loads (should show task #1)
1. Press `c` (complete task)
1. Verify notification appears
1. Press `Esc`
1. Verify back to main view

**Expected:**
- Modal centers on screen (85% size)
- Blue border clearly visible
- Content shows task overview, metrics, insights
- Footer shows available actions
- Closes cleanly with Esc

---

### Test 2: Service Logs Modal

**Steps:**
1. Press `l`
1. Verify modal opens
1. Check log table renders
1. Look for color-coded log levels
1. Press `f` to toggle filter
1. Press `s` to toggle auto-scroll
1. Press `Esc`

**Expected:**
- Modal shows service name in title
- DataTable with 3 columns (Time, Level, Message)
- ERROR in red, WARN in yellow, INFO in blue
- Notifications appear when toggling options
- Smooth return to main view

---

### Test 3: Pattern Detail Modal

**Steps:**
1. Press `p`
1. Check pattern statistics load
1. Scroll through content
1. Review recommendations section
1. Press `Esc`

**Expected:**
- Pattern #7 "Deep Work Morning Block" shown
- Stats: occurrences, success rate, confidence
- Recommendations clearly formatted
- Rich text formatting visible
- Clean exit

---

### Test 4: Metric History Modal

**Steps:**
1. Press `h`
1. View metric summary
1. Check sparkline renders
1. Press `z` (zoom - shows notification)
1. Press `e` (export - shows notification)
1. Press `Esc`

**Expected:**
- Metric name "Cognitive Load" in title
- Current/avg/min/max stats shown
- Sparkline visible
- Insights section populated
- All actions trigger notifications

---

### Test 5: Modal Keyboard Navigation

**Steps:**
1. Press `d` → modal opens
1. Press `Esc` → modal closes
1. Press `l` → new modal opens
1. Press `q` → modal closes
1. Press `p` → modal opens
1. Press `?` → help opens (modal on top of modal)
1. Press `Esc` → help closes, pattern modal visible
1. Press `Esc` → pattern modal closes

**Expected:**
- All modals respond to Esc
- All modals respond to `q`
- Modals can stack (help on top of modal)
- Clean state management
- No visual glitches

---

### Test 6: Rapid Modal Opening/Closing

**Steps:**
1. Press `d` → `Esc` (repeat 10x)
1. Press `l` → `Esc` (repeat 10x)
1. Press `p` → `Esc` (repeat 10x)
1. Press `h` → `Esc` (repeat 10x)

**Expected:**
- No errors or crashes
- No memory leaks
- Consistent performance
- No visual artifacts

---

### Test 7: Help Screen Integration

**Steps:**
1. Press `?` to open help
1. Scroll down to "Drill-Downs (NEW! 🎯)" section
1. Verify all new keybindings listed
1. Press `Esc`
1. Press `d` to verify binding works
1. Press `Esc`

**Expected:**
- Help shows drill-down section
- All 4 keys documented (d, l, p, h)
- Tips section mentions drill-downs
- All keybindings functional

---

## 🐛 Known Limitations (Day 4)

**Mock Data:**
- All modals show sample/mock data
- Not connected to real APIs yet
- Fixed task ID, pattern ID, etc.

**Actions:**
- Modal actions show notifications but don't persist
- Complete task, change priority, etc. are placeholders
- Export functions show notification but don't create files

**Selection:**
- Can't select specific tasks/services/patterns yet
- Always shows same sample item
- Arrow key navigation not implemented

**Live Updates:**
- Service logs don't auto-update yet
- No WebSocket streaming
- Metrics don't refresh in modals

---

## ✅ What Should Work

**Working Features:**
- ✅ All modals open instantly
- ✅ Rich text formatting displays correctly
- ✅ Color coding visible
- ✅ Sparklines render
- ✅ Icons show up (📊, 🎯, 🧠, etc.)
- ✅ All keybindings respond
- ✅ Multiple exit strategies (Esc, q)
- ✅ Notifications appear for actions
- ✅ Help screen updated
- ✅ No syntax errors
- ✅ No crashes

---

## 🔜 Coming in Day 5

**Real Data Integration:**
- Wire up Task Orchestrator API
- Connect service log endpoints
- Fetch patterns from Serena
- Pull metrics from Prometheus

**Live Features:**
- Auto-updating service logs
- Real-time sparklines
- Live metric graphs
- Selection system with arrow keys

**Enhanced UX:**
- Search in logs
- Filter by log level
- Export to actual files
- Nested drill-downs

---

## 📊 Performance Benchmarks

**Expected Performance:**
- Modal open: < 100ms
- Content render: < 200ms
- Key response: < 50ms
- Memory usage: < 50MB total
- CPU usage: < 5%

**Test Command:**
```bash
# Monitor while testing
top -pid $(pgrep -f dopemux_dashboard.py)
```

---

## 🎯 Success Criteria

A successful Day 4 test should show:

- [x] All 4 modals open without errors
- [x] Content displays correctly
- [x] Keyboard shortcuts work
- [x] Help documentation accurate
- [x] No visual glitches
- [x] Clean modal close behavior
- [x] Consistent UX across modals
- [x] Performance within targets

---

## 🆘 Troubleshooting

**Modal doesn't open:**
- Check terminal size (minimum 80x24)
- Verify Textual installed: `pip install textual rich`
- Check for syntax errors: `python -m py_compile dopemux_dashboard.py`

**Visual artifacts:**
- Try different terminal (iTerm2, Terminal.app, etc.)
- Check color support: `echo $COLORTERM`
- Update Textual: `pip install --upgrade textual`

**Slow performance:**
- Check system resources
- Close other tmux panes
- Reduce update frequency in code

**Colors not showing:**
- Verify terminal supports 256 colors
- Check theme compatibility
- Try different theme with `t` key

---

## 📝 Feedback Checklist

When testing, note:

- [ ] Which modals opened successfully?
- [ ] Any visual glitches or artifacts?
- [ ] Keyboard shortcuts responsive?
- [ ] Content readable and well-formatted?
- [ ] Performance acceptable?
- [ ] Any crashes or errors?
- [ ] Suggestions for improvement?

---

## 🚀 Ready to Test!

```bash
# Start dashboard
python dopemux_dashboard.py

# Press these keys in order:
? → d → Esc → l → Esc → p → Esc → h → Esc → f → t → n → r → q
```

**Happy testing! 🎉**
