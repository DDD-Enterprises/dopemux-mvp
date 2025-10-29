# Dashboard Day 3: Interactive Navigation - Deep Research Plan 🎯

**Created:** 2025-10-29  
**Phase:** Advanced Features - Keyboard Navigation & Drill-Downs  
**Estimated Time:** 4-5 hours  

---

## 🎯 MISSION

Transform the dashboard from **passive display** to **interactive command center** with full keyboard navigation and drill-down capabilities.

---

## 📚 RESEARCH: KEYBOARD NAVIGATION PATTERNS

### Best-in-Class TUI Navigation (k9s, lazygit, btop)

**k9s (Kubernetes TUI):**
```
- Number keys (1-9): Jump to specific views
- Tab/Shift+Tab: Cycle through items
- Enter: Drill into details
- Escape: Go back
- /: Search
- ?: Help
```

**lazygit:**
```
- 1-5: Switch between panels
- Tab: Next panel
- h/j/k/l: Vim-style navigation
- Enter: Expand
- Escape: Collapse
- d: Delete/Detail
```

**btop:**
```
- m: Menu
- Arrow keys: Navigate
- Enter: Select
- p: Sort by CPU
- n: Sort by memory
```

### Our Design (ADHD-Optimized)
```
Panel Selection:
  1, 2, 3, 4    → Jump to specific panel (ADHD: direct > sequential)
  Tab           → Next panel (standard convention)
  Shift+Tab     → Previous panel (standard convention)

Panel Actions:
  Enter         → Expand focused panel (maximize)
  Escape        → Collapse all (return to normal)
  d             → Drill-down details (popup)
  
Specific Actions:
  t             → Tasks detail (when on metrics panel)
  l             → Logs viewer (when on services panel)
  s             → Sparkline stats (when on trends panel)
  h             → History view (when on ADHD panel)
```

---

## 🏗️ ARCHITECTURE

### State Management
```python
class DopemuxDashboard(App):
    # Reactive state
    focused_panel = reactive("adhd")  # Current focus
    expanded_panel = reactive(None)   # Which panel is expanded (or None)
    
    # Panel IDs
    PANELS = {
        "adhd": "adhd-state",
        "productivity": "metrics",
        "services": "services",
        "trends": "trends"
    }
    
    PANEL_ORDER = ["adhd", "productivity", "services", "trends"]
```

### Focus Indicators
```python
# Visual focus indicators (CSS classes)
.panel-focused {
    border: heavy $accent;     # Bright border when focused
    border-title: bold;         # Bold title
}

.panel-expanded {
    height: 30;                # Take up most of screen
    z-index: 10;               # Above other panels
}

.panel-dimmed {
    opacity: 0.3;              # Fade when not focused
}
```

---

## 🎨 VISUAL DESIGN

### Focus States
```
┌─ Normal State ──────────────────────────────────┐
│ All panels equal height, no special borders     │
└──────────────────────────────────────────────────┘

┌─ Panel 1 Focused ───────────────────────────────┐
│ ╔════ ⚡ ADHD State ════╗  ← Heavy bright border│
│ ║  Content here         ║                       │
│ ╚═══════════════════════╝                       │
│ ┌── 📊 Productivity ───┐  ← Dimmed              │
│ └──────────────────────┘                       │
└──────────────────────────────────────────────────┘

┌─ Panel 1 Expanded ──────────────────────────────┐
│ ╔════ ⚡ ADHD State (Expanded) ════╗            │
│ ║                                  ║            │
│ ║  Much more content...            ║            │
│ ║  Detailed stats...               ║            │
│ ║  Historical graphs...            ║            │
│ ║                                  ║            │
│ ╚══════════════════════════════════╝            │
│ [Other panels hidden or minimized]              │
└──────────────────────────────────────────────────┘
```

---

## 💻 IMPLEMENTATION PLAN

### Phase 1: Panel Focusing (Morning - 2 hours)

**Step 1: Add Focus State Management**
```python
class DopemuxDashboard(App):
    focused_panel = reactive("adhd", init=False)
    
    def watch_focused_panel(self, old: str, new: str) -> None:
        """React to focus changes"""
        # Remove focus from old panel
        if old:
            old_widget = self.query_one(f"#{self.PANELS[old]}")
            old_widget.remove_class("panel-focused")
        
        # Add focus to new panel
        if new:
            new_widget = self.query_one(f"#{self.PANELS[new]}")
            new_widget.add_class("panel-focused")
            new_widget.scroll_visible()  # Ensure visible
```

**Step 2: Add Keyboard Bindings**
```python
BINDINGS = [
    # Existing bindings...
    ("1", "focus_panel('adhd')", "ADHD"),
    ("2", "focus_panel('productivity')", "Productivity"),
    ("3", "focus_panel('services')", "Services"),
    ("4", "focus_panel('trends')", "Trends"),
    ("tab", "next_panel", "Next"),
    ("shift+tab", "prev_panel", "Previous"),
]

def action_focus_panel(self, panel_id: str) -> None:
    """Focus specific panel"""
    if panel_id in self.PANELS:
        self.focused_panel = panel_id

def action_next_panel(self) -> None:
    """Focus next panel"""
    current_idx = self.PANEL_ORDER.index(self.focused_panel)
    next_idx = (current_idx + 1) % len(self.PANEL_ORDER)
    self.focused_panel = self.PANEL_ORDER[next_idx]

def action_prev_panel(self) -> None:
    """Focus previous panel"""
    current_idx = self.PANEL_ORDER.index(self.focused_panel)
    prev_idx = (current_idx - 1) % len(self.PANEL_ORDER)
    self.focused_panel = self.PANEL_ORDER[prev_idx]
```

**Step 3: Update CSS**
```css
.panel-focused {
    border: heavy $accent;
    border-title-color: $accent;
    border-title-style: bold;
}

.panel-dimmed {
    opacity: 0.4;
}
```

---

### Phase 2: Panel Expansion (Afternoon - 1.5 hours)

**Step 1: Add Expansion State**
```python
expanded_panel = reactive(None, init=False)

def watch_expanded_panel(self, old: Optional[str], new: Optional[str]) -> None:
    """React to expansion changes"""
    # Collapse old panel
    if old:
        old_widget = self.query_one(f"#{self.PANELS[old]}")
        old_widget.remove_class("panel-expanded")
    
    # Expand new panel + dim others
    if new:
        new_widget = self.query_one(f"#{self.PANELS[new]}")
        new_widget.add_class("panel-expanded")
        
        # Dim all other panels
        for panel_id, widget_id in self.PANELS.items():
            if panel_id != new:
                widget = self.query_one(f"#{widget_id}")
                widget.add_class("panel-dimmed")
    else:
        # Restore all panels
        for widget_id in self.PANELS.values():
            widget = self.query_one(f"#{widget_id}")
            widget.remove_class("panel-dimmed")
```

**Step 2: Add Expand/Collapse Actions**
```python
BINDINGS = [
    # ...
    ("enter", "expand_panel", "Expand"),
    ("escape", "collapse_panel", "Collapse"),
]

def action_expand_panel(self) -> None:
    """Expand currently focused panel"""
    if self.expanded_panel == self.focused_panel:
        # Already expanded - toggle off
        self.expanded_panel = None
    else:
        # Expand this panel
        self.expanded_panel = self.focused_panel

def action_collapse_panel(self) -> None:
    """Collapse all panels"""
    self.expanded_panel = None
```

**Step 3: Update Widget Render for Expansion**
```python
class ADHDStateWidget(Static):
    def render(self) -> Panel:
        # Check if expanded
        is_expanded = self.app.expanded_panel == "adhd"
        
        if is_expanded:
            # Show detailed view
            content = self._render_detailed_view()
        else:
            # Show compact view
            content = self._render_compact_view()
        
        return Panel(content, ...)
    
    def _render_detailed_view(self) -> str:
        """Render expanded view with more details"""
        return f"""
{self._render_compact_view()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Historical Data (Last Hour):
  Cognitive Load: [sparkline here]
  Energy Trend:   [sparkline here]

Recent Events:
  • 15:30 - Entered flow state
  • 15:15 - Took 5-minute break
  • 15:00 - Context switch detected

Press 'd' for drill-down details
        """
```

---

### Phase 3: Drill-Down Popups (Afternoon - 1.5 hours)

**Step 1: Create Popup Screens**
```python
class DetailPopup(Screen):
    """Base class for detail popups"""
    
    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("q", "dismiss", "Close"),
    ]
    
    def __init__(self, title: str, content: str):
        super().__init__()
        self.popup_title = title
        self.popup_content = content
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static(self.popup_content, id="popup-content"),
            id="popup-container"
        )
    
    def action_dismiss(self) -> None:
        self.app.pop_screen()


class CognitiveLoadDetail(DetailPopup):
    """Detailed cognitive load history"""
    
    def __init__(self, data: dict):
        content = f"""
╔══════════════════════════════════════════════════════╗
║        Cognitive Load - Detailed History             ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  Current: {data['current']}%                         ║
║  Average (2h): {data['avg']}%                        ║
║  Peak (2h): {data['max']}%                          ║
║  Min (2h): {data['min']}%                           ║
║                                                      ║
║  Last 2 Hours:                                       ║
║  {data['sparkline_2h']}                             ║
║                                                      ║
║  Last 24 Hours:                                      ║
║  {data['sparkline_24h']}                            ║
║                                                      ║
║  Recommendations:                                    ║
║  {data['recommendation']}                           ║
║                                                      ║
╠══════════════════════════════════════════════════════╣
║  Press Escape or 'q' to close                        ║
╚══════════════════════════════════════════════════════╝
        """
        super().__init__("Cognitive Load Detail", content)
```

**Step 2: Add Drill-Down Actions**
```python
BINDINGS = [
    # ...
    ("d", "drill_down", "Details"),
]

async def action_drill_down(self) -> None:
    """Show drill-down details for focused panel"""
    
    if self.focused_panel == "adhd":
        # Fetch detailed cognitive load data
        data = await self.fetcher.get_cognitive_load_detail()
        popup = CognitiveLoadDetail(data)
        self.push_screen(popup)
    
    elif self.focused_panel == "trends":
        # Show sparkline statistics
        popup = SparklineStatsPopup(self.sparkline_data)
        self.push_screen(popup)
    
    elif self.focused_panel == "services":
        # Show service logs
        popup = ServiceLogsPopup(self.selected_service)
        self.push_screen(popup)
    
    elif self.focused_panel == "productivity":
        # Show task details
        popup = TaskDetailsPopup(self.task_data)
        self.push_screen(popup)
```

---

## 🎨 POPUP DESIGNS

### Cognitive Load Detail
```
╔══════════════════════════════════════════════════════╗
║        Cognitive Load - Detailed History             ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  Current: 65% [||||||||||||··········]              ║
║  Status: Moderate - Sustainable                      ║
║                                                      ║
║  Last 2 Hours:                                       ║
║  ▃▄▅▆▇▇▇▆▅▄▅▆▇▇▇▆▅▄▃▂▁▂▃▄▅▆▇▇▇▆  (Increasing)       ║
║                                                      ║
║  Last 24 Hours:                                      ║
║  ▁▁▁▂▃▄▅▆▇██▇▆▅▄▃▂▁▁▁▂▃▄▅▆▇▇▇▆  (Variable)          ║
║                                                      ║
║  Statistics:                                         ║
║  • Average: 58%                                      ║
║  • Peak: 87% (at 15:30)                             ║
║  • Low: 23% (at 09:15)                              ║
║  • Time in optimal zone: 6.5 hrs                    ║
║                                                      ║
║  Recommendation:                                     ║
║  ✓ Current load is sustainable                      ║
║  ⚠ Consider break in ~25 minutes                    ║
║                                                      ║
╠══════════════════════════════════════════════════════╣
║  Esc/q to close  |  h for history  |  r to refresh  ║
╚══════════════════════════════════════════════════════╝
```

---

## ✅ ACCEPTANCE CRITERIA

### Panel Focusing
- [ ] Press 1-4 to jump to specific panel
- [ ] Tab/Shift+Tab to cycle through panels
- [ ] Focused panel has bright border
- [ ] Only one panel focused at a time
- [ ] Focus indicator visible

### Panel Expansion
- [ ] Press Enter to expand focused panel
- [ ] Expanded panel takes 70%+ of screen
- [ ] Other panels dimmed when one expanded
- [ ] Press Escape to collapse all
- [ ] Expanded panel shows more detail

### Drill-Down
- [ ] Press 'd' to open detail popup
- [ ] Popup shows relevant data
- [ ] Popup dismisses with Escape or 'q'
- [ ] Multiple popups can be stacked
- [ ] Keyboard navigation in popup

### Performance
- [ ] Focus change < 50ms
- [ ] Expansion animation smooth
- [ ] Popup opens < 100ms
- [ ] No lag during navigation
- [ ] CPU < 5% during navigation

---

## 🧪 TESTING CHECKLIST

- [ ] Navigate with 1, 2, 3, 4 keys
- [ ] Navigate with Tab/Shift+Tab
- [ ] Expand each panel with Enter
- [ ] Collapse with Escape
- [ ] Open drill-down on each panel
- [ ] Navigate nested popups
- [ ] Rapid key presses (no lag)
- [ ] Test all combinations

---

## 🚀 QUICK START

### Run Tests
```bash
cd /Users/hue/code/dopemux-mvp
python3 dopemux_dashboard.py
```

### Test Keyboard Navigation
```
1. Press '1' → Should focus ADHD panel
2. Press Tab → Should move to next panel
3. Press Enter → Should expand panel
4. Press Escape → Should collapse
5. Press 'd' → Should open detail popup
6. Press Escape → Should close popup
```

---

**Ready to implement!** 🚀
