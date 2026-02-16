---
id: implementation_plan
title: Implementation Plan
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-05-07'
prelude: Implementation Plan (explanation) for dopemux documentation and developer
  workflows.
---
# Phase 7: Brand & Persona Injection Plan

**Goal**: Transform the CLI from "Generic Python Tool" to "DØPEMÜX Ritual Daemon" using the primitives defined in `docs/04-explanation/branding/`.

## 1. Create Brand Primitives
We will create `src/dopemux/ui/branding.py` to house the brand logic.

### Components:
* **Color Palette**: `ink.black`, `ritual.cyan`, `server.mint`, `gilt.edge`, etc.
* **Chips**: `[LIVE]`, `[BLOCKER]`, `[LOGGED]`, `[AFTERCARE]`, `[CONSENT CHECK?]`.
* **RitualConsole**: A `rich.console.Console` subclass that:
  * Applies the global theme.
  * Prefixes output with `[LIVE]` by default.
  * Handles `brand_status()` calls.
* **Copy Library**:
  * `ROASTS`: Self-deprecating one-liners.
  * `AFTERCARE`: Hydration reminders and reassurance.

## 2. Inject into CLI (`src/dopemux/cli.py`)
We will refactor `cli.py` to use `RitualConsole`.

### Changes:
* **Replace Console**: Switch `console = Console()` to `console = RitualConsole()`.
* **Update Banner**: Add the "Ø" ascii art banner to the `cli()` entry point.
* **Exit Hook**: Add an `atexit` or `finally` block to the main execution to print an `[AFTERCARE]` message.
* **Status Messages**: Replace generic `console.print` with `brand_status` where appropriate (e.g., successful initialization, context loading).

## 3. Persona "Glow-Up"
We will update `src/dopemux/ui/dashboard.py` (if feasible) to use the new color palette for TUI elements.

---

## Proposed File Structure

### `src/dopemux/ui/branding.py`
```python
from rich.console import Console
from rich.theme import Theme
from rich.text import Text
import random

# Brand Palette
COLORS = {
    "ink.black": "#020617",
    "ritual.cyan": "#7DFBF6",
    "serum.mint": "#94FADB",
    # ...
}

THEME = Theme({
    "brand.live": "bold #7DFBF6",
    "brand.blocker": "bold #FF8BD1",
    # ...
})

class RitualConsole(Console):
    def __init__(self, *args, **kwargs):
        super().__init__(theme=THEME, *args, **kwargs)

    def print(self, *objects, chip="[LIVE]", **kwargs):
        # Prefix logic...
```
