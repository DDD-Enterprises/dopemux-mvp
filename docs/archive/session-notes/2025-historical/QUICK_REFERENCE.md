---
id: QUICK_REFERENCE
title: Quick_Reference
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
---
# Dopemux Quick Reference Card

**Print this or keep it handy!** 📋

## ⚡ Quick Start (Choose One)

```bash
dopemux dope              # Recommended: Full DOPE with muted theme
dopemux quick             # Fast: Medium layout, no frills
dopemux launch            # Standard: Medium layout with defaults
```

## 🎨 DOPE with Different Themes

```bash
dopemux dope --theme muted    # Soft colors (default) ⭐
dopemux dope --theme neon     # Bright vibrant colors
dopemux dope --theme house    # Professional balanced
```

## 📋 All Presets

| Command | What You Get |
|---------|--------------|
| `dopemux launch --preset minimal` | Just Claude Code |
| `dopemux launch --preset standard` | Medium layout |
| `dopemux launch --preset full` | DOPE layout |
| `dopemux launch --preset dope-muted` | DOPE + muted ⭐ |
| `dopemux launch --preset dope-neon` | DOPE + neon |
| `dopemux launch --preset dope-house` | DOPE + house |

## 🏗️ Layouts (Structure)

- `low` - Minimal (main + agent)
- `medium` - Standard split
- `high` - More panes
- `orchestrator` - Full orchestrator
- `dope` - Complete experience 🔥

## 🎨 Themes (Colors)

- `muted` - Soft, eye-friendly
- `neon` - Bright, vibrant
- `house` - Balanced, professional

## 🛠️ Useful Commands

```bash
dopemux layouts           # Show detailed guide
dopemux tmux list         # List all panes
dopemux tmux theme neon   # Preview theme
dopemux --help            # All commands
```

## 🔧 Manual Control (Advanced)

```bash
# Traditional way (still works)
dopemux tmux start --layout dope --bootstrap
dopemux tmux theme muted --apply
```

## 💡 Common Tasks

**Start your day:**
```bash
dopemux dope
```

**Quick test:**
```bash
dopemux quick
```

**Change theme:**
```bash
dopemux tmux theme neon --apply
```

**Kill session:**
```bash
tmux kill-session -t dopemux
```

---

## 🎯 Recommended Setup

For most users, this is the best command:

```bash
dopemux dope --theme muted
```

Why?
- ✅ Full DOPE layout (all features)
- ✅ Muted theme (easy on eyes)
- ✅ Auto-bootstrap (everything starts)
- ✅ One command, zero fuss

---

**New to Dopemux?** Run: `dopemux layouts`

**Documentation:** See `docs/01-tutorials/quick-launch-commands.md`
