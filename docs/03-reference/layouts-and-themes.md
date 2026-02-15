---
id: layouts-and-themes
title: Layouts and Themes Guide
type: reference
owner: '@hu3mann'
last_review: '2026-02-12'
next_review: '2026-05-12'
author: '@hu3mann'
date: '2026-02-12'
prelude: Reference guide for Dopemux layouts, themes, and presets.
---
# Dopemux Layouts & Themes Guide

## 🏗️ Layouts (Structure)

Layouts control **pane arrangement** - where things go in your tmux session.

| Layout       | Description | Use When |
|--------------|-------------|----------|
| `low`        | Minimal: main + agent | You want simplicity |
| `medium`     | Standard split panes | General development |
| `high`       | More monitoring panes | Need more visibility |
| `orchestrator` | Full orchestrator + monitors | Managing multiple tasks |
| `dope`       | Complete DOPE experience | You want it all! 🔥 |

## 🎨 Themes (Appearance)

Themes control **colors and styling** - how things look.

| Theme  | Style | Best For |
|--------|-------|----------|
| `muted` | Soft, low contrast | Long sessions, reduced eye strain |
| `neon`  | Bright, vibrant | High energy, clear distinctions |
| `house` | Balanced, professional | General use |

## 🚀 Easy Commands

Instead of memorizing complex tmux commands, use these shortcuts:

```bash
# Quick start commands
dopemux quick                    # Fast medium layout
dopemux dope                     # Full DOPE with muted theme
dopemux dope --theme neon        # Full DOPE with neon theme
dopemux launch --preset full     # Full DOPE, default theme

# Full control
dopemux launch --preset dope-muted  # Explicit preset

# Traditional (if you prefer)
dopemux tmux start --layout dope --bootstrap
dopemux tmux theme muted --apply
```

## 📋 Presets Reference

| Preset | Layout | Theme | Description |
|--------|--------|-------|-------------|
| `minimal` | none | none | Just Claude Code |
| `standard` | medium | default | Basic split panes |
| `full` | dope | default | Everything enabled |
| `dope-muted` | dope | muted | Recommended! 🌟 |
| `dope-neon` | dope | neon | Bright & vibrant |
| `dope-house` | dope | house | Professional |

## 💡 Tips

- **First time?** Try: `dopemux dope`
- **Long session?** Use: `dopemux launch --preset dope-muted`
- **Quick test?** Use: `dopemux quick`
- **Learning?** Start with: `dopemux launch --preset standard`

## 🔧 Advanced Usage

```bash
# Manual control (traditional way)
dopemux tmux start --layout dope --bootstrap --alt-routing
dopemux tmux theme neon --apply

# List current panes
dopemux tmux list

# Preview a theme without applying
dopemux tmux theme neon
```
