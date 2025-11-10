---
id: quick-launch-commands
title: Quick Launch Commands
type: tutorial
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# Quick Launch Commands - Easy Dopemux Shortcuts

**New in Dopemux:** Easy-to-use commands that launch complete configurations without memorizing complex tmux options.

## Quick Reference

```bash
# Easiest commands (recommended for most users)
dopemux dope              # Full DOPE layout with muted theme ⭐
dopemux quick             # Fast medium layout
dopemux layouts           # Show this guide

# Preset-based launch
dopemux launch                      # Standard setup
dopemux launch --preset dope-neon   # Full DOPE with neon colors
dopemux launch --preset minimal     # Just Claude Code, no tmux

# Custom DOPE themes
dopemux dope --theme muted    # Soft colors (default)
dopemux dope --theme neon     # Bright vibrant
dopemux dope --theme house    # Professional
```

---

## Commands

### `dopemux dope`

**The recommended way to start Dopemux.** 🔥

Launches the complete DOPE experience:
- Full DOPE layout with all monitoring panes
- Orchestrator + dual agent panes
- Dashboard panels
- Auto-bootstrap services
- Your choice of visual theme

**Options:**
- `--theme [muted|neon|house]` - Visual theme (default: muted)
- `--attach/--no-attach` - Attach to session after creation

**Examples:**
```bash
dopemux dope                   # DOPE with muted theme (recommended)
dopemux dope --theme neon      # Bright neon colors
dopemux dope --theme house     # Professional look
dopemux dope --no-attach       # Create but don't attach
```

**What you get:**
```
┌─────────────────────────────────────────────┐
│ Monitor Panes (top)                         │
│  - Worktree | Logs | Metrics | ADHD | ...  │
├─────────────────────────────────────────────┤
│ Orchestrator Pane (middle)                  │
│  - Task coordination and management         │
├─────────────────────────────────────────────┤
│ Agent Panes (bottom)                        │
│  - Primary Agent | Secondary Agent          │
└─────────────────────────────────────────────┘
```

---

### `dopemux quick`

**Fastest way to get started.** ⚡

Perfect when you:
- Just want to code quickly
- Don't need full monitoring
- Are testing something fast

**No options** - just runs!

```bash
dopemux quick
```

Creates a simple medium layout:
```
┌─────────────────┐
│ Shell/Main      │
├─────────────────┤
│ Claude Agent    │
└─────────────────┘
```

---

### `dopemux launch`

**Flexible preset-based launcher.**

Choose from predefined configurations that combine layout + theme.

**Options:**
- `--preset [minimal|standard|full|dope-muted|dope-neon|dope-house]`
- `--attach/--no-attach`

**Presets:**

| Preset | Layout | Theme | Description |
|--------|--------|-------|-------------|
| `minimal` | none | none | Just Claude Code, no tmux |
| `standard` | medium | default | Basic split panes (default) |
| `full` | dope | default | Everything enabled |
| `dope-muted` | dope | muted | DOPE with soft colors ⭐ |
| `dope-neon` | dope | neon | DOPE with vibrant colors |
| `dope-house` | dope | house | DOPE with professional theme |

**Examples:**
```bash
dopemux launch                        # Standard medium layout
dopemux launch --preset full          # Full DOPE, default theme
dopemux launch --preset dope-muted    # Recommended preset
dopemux launch --preset minimal       # No tmux, just Claude
```

---

### `dopemux layouts`

**Educational command - shows this guide!**

Learn about available:
- Layouts (structure/pane arrangement)
- Themes (visual appearance)
- Presets (layout + theme combinations)
- Example commands

```bash
dopemux layouts
```

Displays comprehensive help with tables and examples.

---

## Understanding Layouts vs Themes

### Layouts (Structure)

Controls **pane arrangement** - where things are placed.

| Layout | Description | Best For |
|--------|-------------|----------|
| `low` | Minimal: main + agent | Simplicity |
| `medium` | Standard split | General use |
| `high` | More panes | Need visibility |
| `orchestrator` | Full orchestrator | Managing tasks |
| `dope` | Complete experience | Power users |

### Themes (Appearance)

Controls **colors and styling** - how things look.

| Theme | Style | Best For |
|-------|-------|----------|
| `muted` | Soft, low contrast | Long sessions, eye comfort |
| `neon` | Bright, vibrant | High energy, clear distinctions |
| `house` | Balanced, professional | General use |

**Think of it like:**
- Layout = furniture arrangement in a room
- Theme = paint colors on the walls

---

## Migration from Old Commands

If you were using:

```bash
# Old way (still works!)
dopemux tmux start --layout dope --bootstrap
dopemux tmux theme neon --apply
```

Now you can use:

```bash
# New way (easier!)
dopemux dope --theme neon
```

**The old commands still work** - these are just shortcuts!

---

## Advanced Usage

### Traditional tmux Commands

For full control, use the traditional commands:

```bash
# Start with specific layout
dopemux tmux start --layout orchestrator --bootstrap --alt-routing

# Apply theme separately
dopemux tmux theme muted --apply

# List current panes
dopemux tmux list

# Preview theme without applying
dopemux tmux theme neon
```

### Combining Options

```bash
# DOPE layout, don't attach, then manually apply theme
dopemux dope --no-attach
dopemux tmux theme neon --apply

# Quick start, then switch to existing session
dopemux quick --no-attach
tmux attach -t dopemux
```

---

## Recommended Workflows

### First Time User

```bash
# Start with the guide
dopemux layouts

# Try the recommended setup
dopemux dope

# Play around with themes
dopemux tmux theme neon --apply
dopemux tmux theme house --apply
```

### Quick Coding Session

```bash
# Fastest start
dopemux quick
```

### Full Production Workflow

```bash
# Complete setup with muted theme (easy on eyes)
dopemux dope --theme muted

# Or use preset
dopemux launch --preset dope-muted
```

### Testing/Experimenting

```bash
# Minimal setup
dopemux launch --preset minimal

# Or quick tmux
dopemux quick
```

---

## Troubleshooting

### "Nothing runs correctly"

Make sure you're using a valid layout, not a theme:

```bash
# ❌ Wrong - "neon" is a theme, not a layout
dopemux tmux start --layout neon

# ✅ Right - Use shortcut
dopemux dope --theme neon

# ✅ Or traditional way
dopemux tmux start --layout dope
dopemux tmux theme neon --apply
```

### Session already exists

If you get "session already exists":

```bash
# Kill existing session first
tmux kill-session -t dopemux

# Then launch
dopemux dope
```

### Theme not applying

Themes only work inside tmux. Make sure you:

1. Created a tmux session first
2. Are inside tmux when applying theme
3. Have a valid theme name

```bash
# Check if in tmux
echo $TMUX

# List available themes
dopemux tmux theme --help
```

---

## Examples Gallery

### Example 1: Morning Startup

```bash
# Start your day with DOPE
dopemux dope --theme muted
```

### Example 2: Quick Bug Fix

```bash
# Fast minimal setup
dopemux quick
```

### Example 3: Presentation Demo

```bash
# Bright vibrant colors for visibility
dopemux dope --theme neon
```

### Example 4: Long Coding Session

```bash
# Soft colors to reduce eye strain
dopemux launch --preset dope-muted
```

---

## Tips & Tricks

1. **First time?** Start with `dopemux dope` - it's the complete experience

2. **Long sessions?** Use muted theme to reduce eye strain:
   ```bash
   dopemux dope --theme muted
   ```

3. **Quick tests?** Use `dopemux quick` for minimal setup

4. **Learning?** Run `dopemux layouts` to see all options

5. **Can't decide?** The recommended command is:
   ```bash
   dopemux dope --theme muted
   ```

---

## See Also

- [Tmux Documentation](../02-how-to/operations/) - Traditional tmux commands
- [DOPE Layout Design](../systems/dashboard/TMUX_DASHBOARD_DESIGN.md) - How DOPE layout works
- [Architecture Overview](../04-explanation/architecture/DOPEMUX_ARCHITECTURE_OVERVIEW.md) - System architecture

---

**Last Updated:** 2025-10-29
**Status:** Production ready
**Recommended Command:** `dopemux dope --theme muted` 🌟
