---
id: DOPE_LAYOUT_COLORS
title: Dope_Layout_Colors
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Dope_Layout_Colors (explanation) for dopemux documentation and developer
  workflows.
---
# DOPE Layout Color Scheme

## Updated Pane Colors & Borders

### NEON Theme (Default)

Each pane now has distinct background colors and border colors for easy visual differentiation:

#### Monitor Panes (Top)
- **monitor:adhd** (Left)
  - Background: `#94fadb` (Cyan/Teal)
  - Text: `#020617` (Dark Blue)
  - Border: `#94fadb` (Cyan)
  - Purpose: ADHD energy/session monitoring

- **monitor:system** (Right)
  - Background: `#f5f26d` (Yellow)
  - Text: `#020617` (Dark Blue)
  - Border: `#f5f26d` (Yellow)
  - Purpose: Docker/MCP/LiteLLM health

#### Metrics Bar
- **metrics:bar**
  - Background: `#020617` (Very Dark)
  - Text: `#7dfbf6` (Bright Cyan)
  - Border: `#7dfbf6` (Bright Cyan)
  - Purpose: Context-aware metrics display

#### Middle Band Panes
- **orchestrator:control** (Left - 75% width)
  - Background: `#0a1628` (Dark Navy Blue)
  - Text: `#7dfbf6` (Bright Cyan)
  - Border: `#7dfbf6` (Bright Cyan)
  - Purpose: Claude Code/Copilot orchestration
  - **Now taller (55% height) and wider (75% width)**

- **sandbox:shell** (Right - 25% width)
  - Background: `#1a0520` (Dark Purple)
  - Text: `#ff8bd1` (Pink)
  - Border: `#ff8bd1` (Pink)
  - Purpose: Quick experiments

#### Agent Panes (Bottom - 25% height)
- **agent:primary**
  - Background: `#041628` (Very Dark Blue)
  - Text: `#94fadb` (Cyan/Teal)
  - Border: `#94fadb` (Cyan)
  - Purpose: Main agent output
  - **Now much taller (25% vs 18%)**

- **agent:secondary** (if dual_agent enabled)
  - Background: `#020617` (Very Dark)
  - Text: `#ffcf78` (Orange)
  - Border: `#ffcf78` (Orange)
  - Purpose: Secondary agent output

---

### HOUSE Theme (Alternative)

Softer, pastel colors for extended sessions:

#### Monitor Panes
- **monitor:adhd**: Green text `#a6e3a1` on dark `#1e1e2e`
- **monitor:system**: Cyan text `#89dceb` on dark `#1e1e2e`

#### Metrics Bar
- **metrics:bar**: Blue text `#89b4fa` on darker `#11111b`

#### Middle Band
- **orchestrator:control**: Light text `#cdd6f4` on `#181825`
- **sandbox:shell**: Pink text `#f5c2e7` on `#302d41`

#### Agents
- **agent:primary**: Green text `#a6e3a1` on `#1f1d2e`
- **agent:secondary**: Purple text `#b4befe` on `#262335`

---

## Visual Layout with Colors

```
┌─────────────────────────────────────────────────┐
│ MONITOR:ADHD (Cyan bg)  │ MONITOR:SYSTEM (Yellow)│ 20%
│ #94fadb background      │ #f5f26d background     │
├─────────────────────────────────────────────────┤
│ METRICS BAR (Dark bg, Cyan text)                │ 2%
│ #020617 bg, #7dfbf6 fg                          │
├─────────────────────────────────────────────────┤
│ ORCHESTRATOR (Navy bg, Cyan) │ SANDBOX (Purple) │ 55%
│ #0a1628 bg, #7dfbf6 fg       │ #1a0520 bg, Pink │
│ 75% width - BIGGER!          │ 25% width        │
├─────────────────────────────────────────────────┤
│ AGENT:PRIMARY (Dark Blue bg, Cyan text)         │ 25%
│ #041628 bg, #94fadb fg - MUCH TALLER!           │
└─────────────────────────────────────────────────┘
```

---

## Color Palette Reference

### NEON Theme Colors
- **Cyan/Teal**: `#94fadb`, `#7dfbf6` - Primary accent, orchestrator, agents
- **Yellow**: `#f5f26d` - System monitoring, warnings
- **Pink**: `#ff8bd1`, `#ff66a3` - Sandbox, task details
- **Orange**: `#ffcf78` - Secondary agent
- **Purple**: `#9b78ff` - Accents
- **Dark Navy**: `#0a1628` - Orchestrator background
- **Dark Purple**: `#1a0520` - Sandbox background
- **Very Dark**: `#020617`, `#041628`, `#041024` - Agent backgrounds

### HOUSE Theme Colors
- **Green**: `#a6e3a1` - Success, ADHD monitor, primary agent
- **Cyan**: `#89dceb` - Info, system monitor, logs
- **Yellow**: `#f9e2af` - Warnings, metrics
- **Pink**: `#f5c2e7` - Sandbox, task detail
- **Blue**: `#89b4fa` - Metrics bar
- **Purple**: `#b4befe` - Secondary agent
- **Light**: `#cdd6f4` - Orchestrator text
- **Dark**: `#1e1e2e`, `#181825`, `#11111b` - Backgrounds

---

## Benefits of New Color Scheme

1. **High Contrast**: Dark backgrounds with bright text for readability
2. **Visual Differentiation**: Each pane type has unique color
3. **Functional Grouping**:
   - Monitors = Bright backgrounds (Cyan, Yellow)
   - Work panes = Dark backgrounds with colored borders
   - Agents = Very dark with distinct text colors
4. **ADHD-Friendly**: Clear visual boundaries reduce cognitive load
5. **Neon Aesthetic**: Matches the cyberpunk/neon branding

---

## Configuration

The color scheme is applied automatically when using the DOPE layout.

To switch themes, edit `dopemux.toml`:

```toml
[tmux]
theme = "neon"  # or "house" for softer colors
```

The layout will apply colors and borders on next launch:
```bash
dopemux tmux start --layout dope
```

---

**Updated**: 2025-10-29
**Pane Size Changes**: Orchestrator 75% width × 55% height, Agents 25% height
**Color Scheme**: Full background colors + distinct borders for all panes
