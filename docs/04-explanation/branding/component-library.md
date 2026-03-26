---
id: component-library
title: Component Library
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Component Library (explanation) for dopemux documentation and developer workflows.
---
# Dopemux Component Library

Developer reference for the dopemux CLI design system. All CLI output should use these themed components to ensure consistent styling and render mode support.

**Source**: `src/dopemux/ui/theme.py`

---

## Quick Start

```python
from dopemux.console import console
from dopemux.ui.theme import (
    Glyphs, StatusChip, styled_table, styled_panel, error_panel,
    get_render_mode, RenderMode,
)

# Themed table
table = styled_table(
    "Dependencies",
    "Name",
    ("Version", {"justify": "right"}),
    ("Status", {"justify": "center"}),
)
table.add_row("rich", "13.9", "[success]installed[/]")
console.print(table)

# Themed panel
console.print(styled_panel("All checks passed", title="Results"))

# Error panel (3-part structure)
console.print(error_panel(
    problem="Connection refused",
    why="Database not running",
    fix="docker compose up db",
))
```

---

## Component Catalog

### `styled_table(title, *columns, compact=False, **kw)`

Creates a branded Rich Table respecting the current render mode.

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | `str` | Table title (rendered with `table.header` style) |
| `*columns` | `str \| tuple[str, dict]` | Column names or `(name, kwargs)` tuples |
| `compact` | `bool` | Force SIMPLE box with tighter padding |
| `**kw` | `Any` | Forwarded to `rich.table.Table` |

**Render mode behavior**:
- **RICH**: ROUNDED box, title, normal padding
- **COMPACT**: SIMPLE box, no title, zero padding
- **PLAIN**: Same structure but no ANSI colors (via Console)
- **AUDIT**: Prepends ISO timestamp column to every row

**Column tuple format**:
```python
("Column Name", {"style": "info", "justify": "right", "width": 20, "no_wrap": True})
```

### `styled_panel(content, title="", border_style="panel.border", **kw)`

Creates a branded Rich Panel respecting the current render mode.

| Parameter | Type | Description |
|-----------|------|-------------|
| `content` | `Any` | Panel body (string or Rich renderable) |
| `title` | `str` | Panel title (rendered with `panel.title` style) |
| `border_style` | `str` | Rich style name for the border |
| `**kw` | `Any` | Forwarded to `rich.panel.Panel` |

**Render mode behavior**:
- **RICH**: Full ROUNDED panel with border and padding
- **COMPACT**: Returns plain text with title header (no border)
- **AUDIT**: Returns timestamped text line
- **PLAIN**: Panel structure without colors

### `error_panel(problem, why, fix, title="Error")`

Creates a 3-part error panel with the mandatory structure: Problem / Why / Fix.

```python
error_panel(
    problem="API key not found",
    why="ANTHROPIC_API_KEY environment variable is not set",
    fix="export ANTHROPIC_API_KEY=sk-ant-...",
    title="Configuration Error",
)
```

All errors must use this 3-part structure for consistency.

### `create_console(**kwargs)`

Factory for creating themed Rich Console instances. **Never call `Console()` directly.**

```python
from dopemux.ui.theme import create_console

# For one-off consoles (rare — prefer importing from dopemux.console)
c = create_console(stderr=True)
```

The shared console at `dopemux.console.console` is pre-configured.

---

## StatusChip Reference

Status chips are bracketed labels for inline status indicators.

| Chip | Style | When to use |
|------|-------|-------------|
| `StatusChip.LIVE` | `chip.live` (cyan) | Active/running processes |
| `StatusChip.BLOCKER` | `chip.blocker` (pink) | Blocking errors |
| `StatusChip.OVERRIDE` | `chip.override` (yellow) | Manual overrides |
| `StatusChip.LOGGED` | `chip.logged` (mint) | Successfully recorded |
| `StatusChip.AFTERCARE` | `chip.aftercare` (violet) | Post-action follow-up |
| `StatusChip.EDGE` | `chip.edge` (cyan) | Edge cases/experimental |

**Usage**:
```python
console.print(StatusChip.LIVE.render("Pipeline running"))
# Output: [LIVE] Pipeline running

console.print(StatusChip.BLOCKER.render("Missing API key"))
# Output: [BLOCKER] Missing API key
```

---

## Glyphs Reference

Nerd Font glyphs (JetBrains Mono Nerd Font) with ASCII fallbacks.

| Glyph | Constant | Nerd Font | Fallback | Color |
|-------|----------|-----------|----------|-------|
| Status check | `Glyphs.SUCCESS` | `\uf058` | `✓` | success |
| Status error | `Glyphs.ERROR` | `\uf057` | `✗` | error |
| Warning | `Glyphs.WARNING` | `\uf06a` | `!` | warning |
| Info | `Glyphs.INFO` | `\uf05a` | `i` | info |
| Running | `Glyphs.RUNNING` | `\uf04b` | `▶` | info |
| Pending | `Glyphs.PENDING` | `\uf017` | `~` | text.dim |
| Blocked | `Glyphs.BLOCKED` | `\uf05e` | `#` | error |
| Git branch | `Glyphs.GIT` | `\ue725` | `Y` | info |
| Code | `Glyphs.CODE` | `\uf121` | `<>` | mint |
| Package | `Glyphs.PACKAGE` | `\uf487` | `[]` | violet |
| Bug | `Glyphs.BUG` | `\uf188` | `*` | error |
| Wrench | `Glyphs.WRENCH` | `\uf0ad` | `%` | warning |
| Docker | `Glyphs.DOCKER` | `\uf308` | — | info |
| Server | `Glyphs.SERVER` | `\uf233` | — | info |
| Database | `Glyphs.DATABASE` | `\uf1c0` | — | violet |
| Arrow right | `Glyphs.ARROW_RIGHT` | `\uf054` | `>` | mint |
| Brand mark | `Glyphs.BRAND_MARK` | `━━━◆ Ø ◆━━━` | — | mint |

**Usage**:
```python
console.print(f"{Glyphs.SUCCESS} All checks passed", style="success")
console.print(f"{Glyphs.ERROR} Connection failed", style="error")
```

---

## RenderMode Guide

| Mode | CLI Flag | Env Var | Behavior |
|------|----------|---------|----------|
| `RICH` | (default) | `DOPEMUX_RENDER_MODE=rich` | Full themed output with colors and borders |
| `COMPACT` | `--compact` | `DOPEMUX_RENDER_MODE=compact` | No borders, no titles, minimal spacing |
| `PLAIN` | `--plain` | `NO_COLOR=1` | No ANSI codes — safe for piping |
| `AUDIT` | `--render-mode audit` | `DOPEMUX_RENDER_MODE=audit` | Timestamps on every line |

`--json` implies PLAIN mode and emits structured JSON instead of Rich output.

**Programmatic access**:
```python
from dopemux.ui.theme import get_render_mode, set_render_mode, RenderMode

mode = get_render_mode()
if mode == RenderMode.COMPACT:
    # skip decorative elements
    pass
```

---

## Style Token Cheatsheet

### Mint family (hero)
| Token | Style |
|-------|-------|
| `mint` | bold #7DFBF6 |
| `mint.soft` | #94FADB |
| `mint.bright` | bold #B4FFEE |
| `mint.dim` | #4A9E94 |

### Accent pops
| Token | Style |
|-------|-------|
| `magenta` | bold #FF8BD1 |
| `violet` | #9B78FF |
| `violet.dim` | #6B4FBF |

### Warm tones (warnings only)
| Token | Style |
|-------|-------|
| `gold` | #F5F26D |
| `amber` | #FFCF78 |

### Text hierarchy
| Token | Style |
|-------|-------|
| `text` | #E2E8F0 |
| `text.dim` | #94A3B8 |
| `text.muted` | #64748B |
| `text.disabled` | #475569 |
| `text.emphasis` | bold #94FADB |

### Headings
| Token | Style |
|-------|-------|
| `heading` | bold #7DFBF6 |
| `subheading` | bold #94FADB |
| `label` | #94A3B8 |

### Semantic status
| Token | Style |
|-------|-------|
| `success` | #94FADB |
| `error` | bold #FF8BD1 |
| `warning` | #F5F26D |
| `info` | #7DFBF6 |
| `debug` | #9B78FF |

### Chips
| Token | Style |
|-------|-------|
| `chip.live` | bold #7DFBF6 |
| `chip.blocker` | bold #FF8BD1 |
| `chip.override` | bold #F5F26D |
| `chip.logged` | #94FADB |
| `chip.aftercare` | #9B78FF |
| `chip.edge` | bold #7DFBF6 |

### Table / Panel
| Token | Style |
|-------|-------|
| `table.header` | bold #7DFBF6 |
| `table.border` | #4A9E94 |
| `table.row.alt` | on #041628 |
| `panel.border` | #4A9E94 |
| `panel.title` | bold #94FADB |

### Progress
| Token | Style |
|-------|-------|
| `bar.complete` | #7DFBF6 |
| `bar.remaining` | #1A0520 |
| `bar.pulse` | #FF8BD1 |
| `spinner` | #7DFBF6 |

### Severity
| Token | Style |
|-------|-------|
| `severity.healthy` | #94FADB |
| `severity.warning` | #F5F26D |
| `severity.critical` | bold #FF8BD1 |
| `severity.unknown` | #64748B |

---

## Do / Don't Examples

### Tables

```python
# DO: Use styled_table with column tuples
table = styled_table(
    "Health Status",
    ("Service", {"style": "info"}),
    ("Status", {"style": "bold"}),
)

# DON'T: Raw Table constructor
table = Table(title="Health Status")  # bypasses render modes
table.add_column("Service", style="cyan")  # raw color, not semantic
```

### Panels

```python
# DO: Use styled_panel
console.print(styled_panel("Content here", title="Title"))

# DON'T: Raw Panel constructor
console.print(Panel("Content here", title="Title"))  # no mode support
```

### Errors

```python
# DO: Use error_panel with 3-part structure
console.print(error_panel(
    problem="File not found",
    why="The config file was deleted",
    fix="Run dopemux init to regenerate",
))

# DON'T: Ad-hoc error formatting
console.print("[red]Error: File not found[/red]")  # no structure, raw color
```

### Console

```python
# DO: Import the shared console
from dopemux.console import console

# DON'T: Create your own Console
from rich.console import Console
c = Console()  # no theme, no render mode awareness
```

### Colors

```python
# DO: Use semantic style tokens
console.print("Passed", style="success")
console.print("Failed", style="error")

# DON'T: Use raw hex colors or color names
console.print("Passed", style="green")
console.print("Failed", style="bold red")
```

---

## JSON Output Pattern

For commands that support `--json`, use the `emit()` dispatch:

```python
from dopemux.ui.output import emit

@cli.command()
@click.pass_context
def my_command(ctx):
    results = do_work()

    def _rich_output():
        table = styled_table("Results", "Name", "Value")
        for r in results:
            table.add_row(r.name, r.value)
        console.print(table)

    emit(
        ctx,
        data={"results": [{"name": r.name, "value": r.value} for r in results]},
        rich_render=_rich_output,
    )
```

---

## Migration Checklist

When converting old code to themed components:

- [ ] Replace `Table(...)` with `styled_table(title, *columns, **kw)`
- [ ] Replace `Panel(...)` with `styled_panel(content, title, border_style)`
- [ ] Replace ad-hoc error output with `error_panel(problem, why, fix)`
- [ ] Replace `Console()` imports with `from dopemux.console import console`
- [ ] Replace raw color names (`"green"`, `"red"`) with semantic tokens (`"success"`, `"error"`)
- [ ] Replace raw hex colors with named style tokens from the theme
- [ ] Remove `from rich.table import Table` if only using `styled_table`
- [ ] Ensure `import` comes from `dopemux.ui.theme`, not `rich` directly
