---
id: TMUX_STYLING_RESEARCH
title: Tmux_Styling_Research
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Tmux_Styling_Research (explanation) for dopemux documentation and developer
  workflows.
---
# tmux Pane Styling & Visual Formatting Research

## Research Summary (2024-2025)

### Key Findings

1. **Native tmux Styling Capabilities**
1. **Popular Theme Frameworks**
1. **TUI Libraries for Rich Formatting**
1. **Python Integration Examples**

---

## 1. Native tmux Styling Options

### Pane Border Customization

```bash
# Global pane border colors
set-option -g pane-border-style fg=colour235,bg=colour236
set-option -g pane-active-border-style fg=colour39,bg=colour236

# Per-pane styling (limited support)
# NOTE: Individual pane colors not directly supported
# Workaround: Use pane titles and conditional formatting
```

### Status Bar Styling

```bash
# Status bar
set-option -g status-bg colour234
set-option -g status-fg colour231
set-option -g status-left '#[fg=colour39] Session: #S'
set-option -g status-right '#[fg=colour141]%R'

# Window status
set-option -g window-status-current-style fg=colour39,bg=colour235
```

### Color Support

```bash
# Enable 256 colors
set-option -g default-terminal "screen-256color"

# Enable 24-bit true color
set-option -ga terminal-overrides ",xterm-256color:Tc"
```

---

## 2. Popular tmux Theme Frameworks (2024)

### Tmux Plugin Manager (TPM)
**Repository**: https://github.com/tmux-plugins/tpm

Standard package manager for tmux plugins and themes.

```bash
# Installation
set -g @plugin 'tmux-plugins/tpm'

# Install plugins: Ctrl+B, Shift+I
```

### Top Themes for 2024

#### 1. **Dracula**
```bash
set -g @plugin 'dracula/tmux'
```
- High contrast
- Deep purples, pinks
- Highly customizable

#### 2. **Nord**
```bash
set -g @plugin 'nordtheme/nord-tmux'
```
- Arctic-inspired cool colors
- Excellent legibility
- Cohesive with desktop themes

#### 3. **Gruvbox**
```bash
set -g @plugin 'egel/tmux-gruvbox'
```
- Warm retro aesthetics
- Day/night variants
- Eye-friendly for long sessions

#### 4. **Tokyo Night**
- Modern, sleek dark theme
- Popular in 2024
- Inspired by VS Code theme

### tmux-powerline

**Repository**: https://github.com/erikw/tmux-powerline

Beautiful status lines with visual separators and system info.

Features:
- Segmented status bar
- Git integration
- System metrics (CPU, memory, battery)
- Weather, Spotify integration

---

## 3. TUI Libraries for Rich Formatting

### Textual (Python)
**Repository**: https://github.com/Textualize/textual

Modern Python TUI framework with rich styling:

```python
from textual.app import App
from textual.widgets import Static

class MyApp(App):
    CSS = """
    Screen {
        background: #0a1628;
    }
    .pane {
        border: solid #7dfbf6;
        background: #041628;
    }
    """
```

**tmux Integration**:
- Works inside tmux panes
- Requires 24-bit color support
- Set `TERM=xterm-256color` or better

### Rich (Python)
**Repository**: https://github.com/Textualize/rich

Terminal formatting library:

```python
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()
text = Text("Orchestrator", style="bold #7dfbf6 on #0a1628")
panel = Panel(text, border_style="#7dfbf6")
console.print(panel)
```

### Urwid (Python)
**Repository**: https://github.com/urwid/urwid

Mature TUI library:
- Comprehensive color support
- Complex layouts
- Event handling

### Blessed (Python)
**Repository**: https://github.com/jquast/blessed

Elegant terminal formatting:
- Easy colors and positioning
- Cross-platform
- Pythonic API

---

## 4. Python Code Examples from Research

### Example 1: tmux Monitor with Styling

```python
import subprocess

def set_pane_style(pane_id, fg_color, bg_color):
    """Set pane border color (tmux 3.2+)"""
    subprocess.run([
        'tmux', 'select-pane',
        '-t', pane_id,
        '-P', f'fg={fg_color},bg={bg_color}'
    ])

# Set orchestrator pane
set_pane_style('%1', '#7dfbf6', '#0a1628')

# Set agent pane
set_pane_style('%2', '#94fadb', '#041628')
```

### Example 2: Rich Panel in tmux Pane

```python
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout

console = Console()
layout = Layout()

# Create styled panels
layout.split_row(
    Layout(Panel("Orchestrator",
                 style="bold #7dfbf6 on #0a1628",
                 border_style="#7dfbf6"), name="left"),
    Layout(Panel("Sandbox",
                 style="bold #ff8bd1 on #1a0520",
                 border_style="#ff8bd1"), name="right"),
)

console.print(layout)
```

### Example 3: Textual App for tmux Pane

```python
from textual.app import App
from textual.widgets import Static

class DopePaneApp(App):
    CSS = """
    #orchestrator {
        background: #0a1628;
        color: #7dfbf6;
        border: solid #7dfbf6;
    }
    #agent {
        background: #041628;
        color: #94fadb;
        border: solid #94fadb;
    }
    """

    def compose(self):
        yield Static("Orchestrator Content", id="orchestrator")
        yield Static("Agent Output", id="agent")
```

---

## 5. Limitations & Workarounds

### Per-Pane Border Colors

**Problem**: tmux doesn't natively support different border colors per pane

**Workarounds**:
1. Use pane titles with conditional formatting
1. Rely on pane background colors for differentiation
1. Use hooks to dynamically change border on pane focus
1. Run TUI apps inside panes for custom borders

### Example: Conditional Border Styling

```bash
# Set based on pane title
set-hook -g pane-focus-in 'run-shell "
  if [ \"#{pane_title}\" = \"orchestrator:control\" ]; then
    tmux select-pane -P fg=#7dfbf6,bg=#0a1628
  elif [ \"#{pane_title}\" = \"agent:primary\" ]; then
    tmux select-pane -P fg=#94fadb,bg=#041628
  fi
"'
```

### Unicode Border Characters

**Problem**: Borders show as `x q` instead of lines

**Solution**:
```bash
# Ensure UTF-8 locale
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

# Use modern terminal emulator
# Recommended: Kitty, iTerm2, Alacritty, WezTerm
```

---

## 6. Best Practices for DOPE Layout

### Approach 1: tmux Native Styling (Current)

✅ What we're using:
- Global pane border colors
- Per-pane background colors via `pane-style`
- Per-pane border via `pane-border-style` (where supported)
- Pane titles for identification

```bash
# Example from your code
tmux select-pane -t %1 -P 'fg=#7dfbf6,bg=#0a1628'
tmux set-option -p -t %1 pane-border-style 'fg=#7dfbf6,bg=#020617'
```

### Approach 2: TUI Apps in Panes

Run Textual/Rich apps inside panes for maximum visual control:

```bash
# Orchestrator pane runs a Textual app
tmux send-keys -t %1 'python orchestrator_ui.py' Enter

# Agent pane runs Rich output
tmux send-keys -t %2 'python agent_monitor.py' Enter
```

### Approach 3: Hybrid (Recommended)

- **tmux native**: Global theming, status bar, pane borders
- **TUI apps**: Rich content inside panes with custom styling
- **Best of both**: Visual consistency + powerful formatting

---

## 7. Recommended Tools for Your Stack

### For dopemux-mvp:

1. **Textual** - For interactive dashboard panes
   ```bash
   pip install textual
   ```

1. **Rich** - For formatted output in non-interactive panes
   ```bash
   pip install rich
   ```

1. **tmux native styling** - For global theme consistency
- Already implemented in your NEON/HOUSE themes

1. **libtmux** - Python library for tmux automation
   ```bash
   pip install libtmux
   ```

   Example:
   ```python
   import libtmux

   server = libtmux.Server()
   session = server.find_where({"session_name": "dopemux"})
   pane = session.attached_window.attached_pane

   pane.set_option('pane-border-style', 'fg=#7dfbf6')
   ```

---

## 8. Color Support Requirements

### For Full NEON Theme Support:

```bash
# In .tmux.conf
set-option -g default-terminal "screen-256color"
set-option -ga terminal-overrides ",*256col*:Tc"
set-option -g allow-passthrough on

# Environment variables
export TERM=xterm-256color
export COLORTERM=truecolor
```

### Testing Color Support:

```bash
# Test 24-bit color
printf "\x1b[38;2;255;100;0mTRUECOLOR\x1b[0m\n"

# Test in tmux
tmux new-session "printf '\x1b[38;2;255;100;0mTRUECOLOR\x1b[0m\n'; read"
```

---

## 9. Example Projects Using Similar Approaches

### Projects Found in Research:

1. **JASMIN** - Pentesting cockpit with tmux layouts
- Python + tmux automation
- Custom pane styling
- https://github.com/smoovmove/JASMIN

1. **haconiwa** - tmux monitoring tool
- Python-based tmux integration
- Custom status bars

1. **claude-orc** - AI orchestration in tmux
- Similar to your use case
- tmux layouts for Claude Code integration

---

## 10. Resources

### Documentation:
- tmux manual: `man tmux`
- Textual docs: https://textual.textualize.io/
- Rich docs: https://rich.readthedocs.io/
- awesome-tmux: https://github.com/rothgar/awesome-tmux

### Color Tools:
- tmux color reference: https://www.ditig.com/256-colors-cheat-sheet
- Color scheme generator: https://coolors.co/
- Terminal color test: https://github.com/robertknight/konsole/blob/master/tests/color-spaces.pl

### Community:
- r/tmux on Reddit
- tmux GitHub Discussions
- Textual Discord server

---

## Conclusion

For your dopemux DOPE layout:

✅ **Current approach is solid**: Using tmux native pane styling
✅ **Enhancement opportunity**: Add Textual apps for interactive panes
✅ **Already optimal**: NEON theme color choices work great
✅ **Future**: Consider Textual for orchestrator pane rich UI

The combination of tmux's native styling + Python TUI libraries gives you the best balance of performance, aesthetics, and functionality.

---

**Research Date**: 2025-10-29
**Sources**: Web search, GitHub code search, tmux documentation
**Relevance**: High - directly applicable to dopemux-mvp DOPE layout
