# Dopemux Brand System: Enriched Implementation Plan

**Date**: 2026-03-18
**Status**: Ready for execution
**Estimated Phases**: 0–8 (Phase 0 first, then sequential)

---

## Assessment: Who Should Execute Each Phase

| Phase | Best Executor | Rationale |
|-------|--------------|-----------|
| **Deliverable 1** (Brand Resource Pack) | **Opus** | Consolidation of 30+ files into one canonical doc — needs deep context, cross-referencing, voice fidelity |
| **Phase 0** (Foundation) | **Opus or Sonnet** | New module creation (voice.py), CSV enrichment, token sync script |
| **Phase 1** (CLI Core) | **Sonnet or Codex** | Mechanical migration: find/replace Rich constructors → themed helpers across 17 files |
| **Phase 2** (TUI Dashboard) | **Sonnet** | Dashboard widget migration, CSS enforcement |
| **Phase 3** (Web) | **Sonnet** | TypeScript theme expansion, component branding |
| **Phase 4** (TMUX) | **Sonnet** | Config file generation, color token injection |
| **Phase 5** (Agent Prompts) | **Opus** | Voice header design requires brand voice fidelity |
| **Phase 6** (Notifications) | **Sonnet** | Template branding, copy injection |
| **Phase 7** (Docs) | **Opus or Sonnet** | Formatting consistency across 25+ flight deck docs |
| **Phase 8** (Verification) | **Opus** | Lint script design, voice gate middleware, snapshot tests |

**Visual assets** (gradients, glows, icons): Not needed as code artifacts. All visual effects are CSS/Rich markup — no external design tool required.

---

## Deliverable 1: Canonical Brand Resource Pack

**Output**: `docs/04-explanation/branding/brand-resource-pack.md`

**Source files to consolidate**:
- `docs/04-explanation/branding/dopemux-brand-system.md` — pillars, colors, voice dial
- `docs/04-explanation/branding/cli-ux-design-spec.md` — palette details, component specs
- `docs/04-explanation/branding/component-library.md` — API reference
- `dopemux_voice_branding_bundle/BRAND_VOICE_BIBLE.md` — 6 voice modes
- `dopemux_voice_branding_bundle/VOICE_GATES.yaml` — lexical/structure gates
- `dopemux_voice_branding_bundle/SCORING_RUBRIC.md` — 7-dimension rubric
- `src/dopemux/ui/theme.py` — canonical color constants (lines 33–57)
- `src/dopemux/ui/dopemux.tcss` — CSS variable mapping (lines 7–19)
- `ui-dashboard/src/theme.ts` — TS brandTokens (lines 3–32)

**Structure** (sections with exact content sources):

### Section 1: Brand Identity
- Pillars table from `dopemux-brand-system.md` §1
- Metaphor system: Cockpit/Flight-Deck/HUD/Ritual-Daemon mapping
- Personality matrix: 5 surfaces × 3 ADHD states
- Brand name variants: dopemux, DOPEMUX, DPMX, 💊dopemux, DOMUX

### Section 2: Visual System — Cross-Platform Token Table

Source of truth: `src/dopemux/ui/theme.py` lines 33–57.

```
| Token          | Hex     | theme.py const   | dopemux.tcss var    | theme.ts key     | TMUX           |
|----------------|---------|-------------------|---------------------|------------------|----------------|
| ink.black      | #020617 | INK_BLACK         | $base               | inkBlack         | colour234      |
| void.navy      | #041628 | VOID_NAVY         | $mantle             | voidNavy         | colour235      |
| velvet.plum    | #1A0520 | VELVET_PLUM       | (not mapped)        | velvetPlum       | colour53       |
| ritual.cyan    | #7DFBF6 | RITUAL_CYAN       | $blue               | ritualCyan       | colour123      |
| serum.mint     | #94FADB | SERUM_MINT        | $green              | serumMint        | colour122      |
| mint.bright    | #B4FFEE | MINT_BRIGHT       | (not mapped)        | (not mapped)     | colour159      |
| mint.dim       | #4A9E94 | MINT_DIM          | (not mapped)        | mintDim          | colour73       |
| gremlin.pink   | #FF8BD1 | GREMLIN_PINK      | $pink               | gremlinPink      | colour212      |
| aftercare.viol | #9B78FF | AFTERCARE_VIOLET  | $mauve              | aftercareViolet  | colour141      |
| violet.dim     | #6B4FBF | VIOLET_DIM        | (not mapped)        | (not mapped)     | colour98       |
| gilt.edge      | #F5F26D | GILT_EDGE         | $yellow             | giltEdge         | colour227      |
| saint.gold     | #FFCF78 | SAINT_GOLD        | $peach              | saintGold        | colour222      |
| text.primary   | #E2E8F0 | TEXT_PRIMARY       | $text               | (MUI text.prim)  | colour253      |
```

### Section 3: Typography
- Display: Space Grotesk (from brand-system.md + theme.ts)
- Body: Inter
- Code/CLI: JetBrains Mono Nerd Font

### Section 4: Component System
- CLI components: from `component-library.md` + `theme.py` lines 300–428
- TUI: Textual widgets mapped to `dopemux.tcss`
- Web: MUI via `theme.ts` brandTokens
- Status chips: 6 chips from `theme.py` StatusChip enum (lines 192–221)
- Glyphs: from `theme.py` Glyphs class (lines 128–185)

### Section 5: Voice System
- 6 modes from `BRAND_VOICE_BIBLE.md`
- Gates from `VOICE_GATES.yaml`
- Scoring rubric dimensions from `SCORING_RUBRIC.md`
- Emoji whitelist: 💊 🧪 📼 📎 📈 🧷 🧠 🗜️ (CLI subset: 💊 🧪 🧠 ⚡ 💧 🔬)
- Surface-voice mapping table
- ~150 curated specimens (index only, sourced from enriched ledger)

### Section 6: Surface Catalog

| Surface | Files | Current Status | Target |
|---------|-------|---------------|--------|
| CLI commands (17 files) | `src/dopemux/commands/*.py` | Raw Rich constructors | styled_table/styled_panel |
| CLI entry | `src/dopemux/cli.py` | Partial theme imports | Full brand banner + aftercare |
| TUI dashboard | `src/dopemux/ui/dashboard.py` | Raw Panel/Text | Themed + voice copy |
| Web dashboard | `ui-dashboard/src/` | theme.ts applied | Expand tokens |
| TMUX | `configs/tmux*` | Generic colors | Brand tokens |
| Agent prompts | `services/agents/*.py` | No voice headers | Voice header injection |
| Notifications | `services/adhd-notifier/*.py` | Unbranded | StatusChip + copy |

### Section 7: Verification Protocol
- Brand lint rules
- Voice gate enforcement
- Token sync validation
- WCAG AA compliance checks

**Acceptance criteria**: Single .md file that any developer can reference for _every_ brand decision. No need to open other files.

---

## Phase 0: Foundation Infrastructure

### File 1: `src/dopemux/ui/voice.py`

**Purpose**: Programmatic voice engine for brand copy.

```python
"""Dopemux Voice Engine — programmatic brand copy for all surfaces.

Usage:
    from dopemux.ui.voice import VoiceMode, CopyLibrary, validate_output

    copy = CopyLibrary()
    console.print(copy.banner("extract"))
    console.print(copy.random_aftercare())
    violations = validate_output("maybe this works")
"""

from __future__ import annotations

import csv
import enum
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import yaml


class VoiceMode(enum.Enum):
    """Brand voice modes from BRAND_VOICE_BIBLE.md."""
    FILTH_DAEMON = "FilthDaemon"
    CLINICAL_FORENSICS = "ClinicalForensics"
    UX_SCOLD = "UXScold"
    UI_STRICT = "UIStrict"
    BANNER_ONE_LINER = "BannerOneLiner"
    KINK_ACCENT = "KinkAccent"


@dataclass
class VoiceViolation:
    """A voice gate violation found in output text."""
    gate_type: str          # "hard_avoid" | "soft_avoid" | "missing_closer"
    matched_text: str       # The offending text or missing element
    severity: str           # "error" | "warning"
    suggestion: str         # What to do instead


class CopyLibrary:
    """Brand copy sourced from enriched specimen ledger."""

    def __init__(self, ledger_path: Path | None = None) -> None:
        # Default: look for enriched CSV relative to repo root
        if ledger_path is None:
            ledger_path = Path(__file__).resolve().parents[3] / (
                "dopemux_voice_branding_bundle/SPECIMEN_LEDGER_ENRICHED.csv"
            )
        self._ledger_path = ledger_path
        self._specimens: dict[str, list[str]] = {}  # usable_as -> [excerpts]
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not self._ledger_path.exists():
            return
        with open(self._ledger_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                category = row.get("usable_as", "").strip()
                excerpt = row.get("excerpt", "").strip()
                if category and excerpt:
                    self._specimens.setdefault(category, []).append(excerpt)

    def random_roast(self) -> str:
        self._ensure_loaded()
        pool = self._specimens.get("roast", [])
        return random.choice(pool) if pool else "[UXScold] You're still here? Ship something."

    def random_aftercare(self) -> str:
        self._ensure_loaded()
        pool = self._specimens.get("aftercare", [])
        if pool:
            return random.choice(pool)
        return random.choice([
            "💧 Hydrate. You earned it.",
            "💊 Session logged. Go touch grass.",
            "🧠 Context saved. Take a break.",
            "💧 Water check. Posture check. You shipped.",
        ])

    def banner(self, command: str) -> str:
        self._ensure_loaded()
        pool = self._specimens.get("banner", [])
        if pool:
            return random.choice(pool)
        return f"━━━◆ Ø ◆━━━  dopemux {command}"

    def error_copy(self, error_type: str) -> str:
        self._ensure_loaded()
        pool = self._specimens.get("error", [])
        return random.choice(pool) if pool else f"[BLOCKER] {error_type}"

    def success_copy(self, action: str) -> str:
        self._ensure_loaded()
        pool = self._specimens.get("success", [])
        return random.choice(pool) if pool else f"[LOGGED] {action}"


def _load_voice_gates() -> dict:
    """Load VOICE_GATES.yaml from the branding bundle."""
    gates_path = Path(__file__).resolve().parents[3] / (
        "dopemux_voice_branding_bundle/VOICE_GATES.yaml"
    )
    if not gates_path.exists():
        return {"lexical_gates": {}, "structure_gates": {}}
    with open(gates_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def validate_output(text: str) -> list[VoiceViolation]:
    """Check text against VOICE_GATES.yaml. Returns list of violations."""
    gates = _load_voice_gates()
    violations: list[VoiceViolation] = []
    text_lower = text.lower()

    # Hard avoids
    for phrase in gates.get("lexical_gates", {}).get("hard_avoid_phrases", []):
        if phrase.lower() in text_lower:
            violations.append(VoiceViolation(
                gate_type="hard_avoid",
                matched_text=phrase,
                severity="error",
                suggestion=f"Remove '{phrase}'. Use direct language instead.",
            ))

    # Soft avoids
    for phrase in gates.get("lexical_gates", {}).get("soft_avoid_phrases", []):
        if phrase.lower() in text_lower:
            violations.append(VoiceViolation(
                gate_type="soft_avoid",
                matched_text=phrase,
                severity="warning",
                suggestion=f"Consider removing '{phrase}'. Too soft for dopemux voice.",
            ))

    return violations
```

**Acceptance criteria**:
- `from dopemux.ui.voice import VoiceMode, CopyLibrary, validate_output` imports cleanly
- `validate_output("as an ai, probably")` returns 2 violations (both hard_avoid)
- `CopyLibrary().random_aftercare()` returns a string (fallback if no CSV)
- `pytest tests/dopemux/ui/test_voice.py` passes

### File 2: `dopemux_voice_branding_bundle/SPECIMEN_LEDGER_ENRICHED.csv`

**Purpose**: Curated subset of `SPECIMEN_LEDGER_REGEN.csv` with added columns.

**Input**: `SPECIMEN_LEDGER_REGEN.csv` (columns: specimen_id, excerpt, location, context_tags, tone_flags)

**Output columns**: specimen_id, excerpt, location, context_tags, tone_flags, **surface**, **voice_mode**, **usable_as**

**New column values**:
- `surface`: cli | ui | agent | notification | docs
- `voice_mode`: FilthDaemon | ClinicalForensics | UXScold | UIStrict | BannerOneLiner | KinkAccent
- `usable_as`: banner | error | roast | aftercare | success | tagline | instruction

**Enrichment rules** (for scripting or manual pass):
1. Skip rows where `excerpt` starts with `"result":` or `"text":` followed by raw JSON/chat dumps (these are raw extracts, not usable copy)
2. Rows with `context_tags` containing "roast" → `usable_as=roast`, `voice_mode=UXScold`
3. Rows with `context_tags` containing "error" → `usable_as=error`, `voice_mode=ClinicalForensics`
4. Rows with `context_tags` containing "tagline" → `usable_as=banner`, `voice_mode=BannerOneLiner`
5. Rows with `context_tags` containing "naming" → `usable_as=tagline`, `voice_mode=BannerOneLiner`
6. Rows with `context_tags` containing "instruction" → `usable_as=instruction`, `voice_mode=ClinicalForensics`
7. Default surface=cli unless excerpt references UI/web/notification context

**Target**: ~150 rows from the ~650 input rows. Most raw JSON dumps get filtered out.

**Acceptance criteria**: CSV loads without errors, `usable_as` column has at least 5 entries per category.

### File 3: `scripts/sync_brand_tokens.py`

**Purpose**: Validate cross-platform token sync (theme.py → tcss, ts, tmux).

```python
#!/usr/bin/env python3
"""Brand token sync validator.

Reads theme.py as source of truth, validates dopemux.tcss and theme.ts match.
Exit 0 = all synced, Exit 1 = drift detected.

Usage:
    python scripts/sync_brand_tokens.py
"""

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def extract_python_constants(path: Path) -> dict[str, str]:
    """Extract color hex constants from theme.py."""
    constants = {}
    source = path.read_text()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                    val = node.value.value
                    if isinstance(val, str) and val.startswith("#") and len(val) == 7:
                        constants[target.id] = val.upper()
    return constants


def extract_tcss_variables(path: Path) -> dict[str, str]:
    """Extract $variable: #hex from dopemux.tcss."""
    variables = {}
    for line in path.read_text().splitlines():
        m = re.match(r'\s*\$(\w[\w-]*):\s*(#[0-9a-fA-F]{6})', line)
        if m:
            variables[m.group(1)] = m.group(2).upper()
    return variables


def extract_ts_tokens(path: Path) -> dict[str, str]:
    """Extract key: '#hex' from theme.ts brandTokens.colors."""
    tokens = {}
    for line in path.read_text().splitlines():
        m = re.search(r"(\w+):\s*['\"](#[0-9a-fA-F]{6})['\"]", line)
        if m:
            tokens[m.group(1)] = m.group(2).upper()
    return tokens


# Expected mappings: python_const -> tcss_var
PYTHON_TO_TCSS = {
    "INK_BLACK": "base",
    "VOID_NAVY": "mantle",
    "RITUAL_CYAN": "blue",
    "SERUM_MINT": "green",
    "GREMLIN_PINK": "pink",
    "AFTERCARE_VIOLET": "mauve",
    "GILT_EDGE": "yellow",
    "SAINT_GOLD": "peach",
    "TEXT_PRIMARY": "text",
}

# Expected mappings: python_const -> ts_key
PYTHON_TO_TS = {
    "INK_BLACK": "inkBlack",
    "VOID_NAVY": "voidNavy",
    "RITUAL_CYAN": "ritualCyan",
    "SERUM_MINT": "serumMint",
    "GREMLIN_PINK": "gremlinPink",
    "AFTERCARE_VIOLET": "aftercareViolet",
    "GILT_EDGE": "giltEdge",
    "SAINT_GOLD": "saintGold",
}


def main() -> int:
    py_path = ROOT / "src/dopemux/ui/theme.py"
    tcss_path = ROOT / "src/dopemux/ui/dopemux.tcss"
    ts_path = ROOT / "ui-dashboard/src/theme.ts"

    py_consts = extract_python_constants(py_path)
    tcss_vars = extract_tcss_variables(tcss_path)
    ts_tokens = extract_ts_tokens(ts_path)

    drift = []

    for py_name, tcss_name in PYTHON_TO_TCSS.items():
        py_val = py_consts.get(py_name)
        tcss_val = tcss_vars.get(tcss_name)
        if py_val and tcss_val and py_val != tcss_val:
            drift.append(f"TCSS drift: {py_name}={py_val} but ${tcss_name}={tcss_val}")

    for py_name, ts_name in PYTHON_TO_TS.items():
        py_val = py_consts.get(py_name)
        ts_val = ts_tokens.get(ts_name)
        if py_val and ts_val and py_val != ts_val:
            drift.append(f"TS drift: {py_name}={py_val} but {ts_name}={ts_val}")

    if drift:
        print("❌ Brand token drift detected:")
        for d in drift:
            print(f"  • {d}")
        return 1
    else:
        print("✅ All brand tokens in sync across theme.py, dopemux.tcss, theme.ts")
        return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Acceptance criteria**: `python scripts/sync_brand_tokens.py` exits 0 if tokens match, 1 with drift report if not.

---

## Phase 1: CLI Core Migration (17 command files)

### Migration Pattern (apply to each file)

**Step 1**: Replace imports

```python
# BEFORE (find this pattern):
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# AFTER (replace with):
from ..ui.theme import styled_table, styled_panel, error_panel, Glyphs, StatusChip
# Keep Progress imports — no branded replacement yet
from rich.progress import Progress, SpinnerColumn, TextColumn
```

**Step 2**: Replace `Table(` constructors

```python
# BEFORE:
table = Table(title="Results", box=ROUNDED, border_style="cyan")
table.add_column("Name", style="bold")
table.add_column("Status")

# AFTER:
table = styled_table(
    f"{Glyphs.PACKAGE} Results",
    ("Name", {"style": "bold"}),
    "Status",
)
```

**Step 3**: Replace `Panel(` constructors

```python
# BEFORE:
console.print(Panel("[bold cyan]📊 Running audit…[/bold cyan]", border_style="cyan"))

# AFTER:
console.print(styled_panel("[mint]📊 Running audit…[/mint]", title="Audit"))
```

**Step 4**: Replace raw color strings with theme style names

```python
# BEFORE:
"[bold cyan]text[/bold cyan]"   →   "[mint]text[/mint]"
"[bold red]error[/bold red]"    →   "[error]error[/error]"
"[green]ok[/green]"             →   "[success]ok[/success]"
"[yellow]warn[/yellow]"         →   "[warning]warn[/warning]"
border_style="cyan"             →   border_style="panel.border"
border_style="red"              →   border_style="error"
```

**Step 5**: Add StatusChip on completion

```python
# At end of successful command:
console.print(StatusChip.LOGGED.render("Done"))
```

### Files to migrate (with raw Rich constructor counts from grep)

| File | Table() | Panel() | Priority |
|------|---------|---------|----------|
| `extract_commands.py` | 3 | 1 | High (most constructors) |
| `extractor_commands.py` | 1 | 1 | High |
| `decisions_commands.py` | 1 | 0 | Medium |
| `upgrades_commands.py` | 1 | 0 | Medium |
| `update_commands.py` | 1 | 0 | Medium |
| `audit_commands.py` | 0 | 1 | Medium |
| `memory_commands.py` | 4 | 0 | High |
| `profile_commands.py` | 1 | 0 | Medium |
| `dev_commands.py` | 1 | 0 | Medium |
| `code_commands.py` | 1 | 0 | Medium |
| `trigger_group_commands.py` | 1 | 0 | Medium |
| `workflow_group_commands.py` | 1 | 0 | Medium |
| `capture_group_commands.py` | 1 | 0 | Medium |
| `autoresponder_commands.py` | 1 | 0 | Medium |
| `instances_commands.py` | 1 | 0 | Medium |
| `personas_commands.py` | 1 | 1 | Medium |
| `worktrees_commands.py` | 0 | 0 | Low (verify) |

### CLI Entry Point Branding (`src/dopemux/cli.py`)

cli.py already imports `Glyphs, StatusChip, styled_panel, styled_table` (line 46-54) but also imports raw `Panel, Table, Text` (lines 37-39).

**Changes needed**:
1. Remove raw Rich imports that are now unused after migration
2. Add banner display on CLI startup (in the main `@click.group` callback)
3. Add `atexit` hook for aftercare message

```python
# In the @cli.command() or main group callback:
import atexit
from .ui.voice import CopyLibrary

_copy = CopyLibrary()

# After CLI setup:
if get_render_mode() == RenderMode.RICH:
    console.print(f"[mint]{Glyphs.BRAND_MARK}[/mint]", justify="center")

# atexit hook:
def _aftercare():
    if get_render_mode() == RenderMode.RICH:
        console.print(f"\n[violet]{_copy.random_aftercare()}[/violet]")
atexit.register(_aftercare)
```

**Acceptance criteria**:
- `grep -r "from rich.table import Table" src/dopemux/commands/` returns 0 matches
- `grep -r "from rich.panel import Panel" src/dopemux/commands/` returns 0 matches
- Every command output uses branded colors (mint/violet/gold, not cyan/red/green)
- `dopemux --help` shows Ø brand mark
- All 4 RenderModes work (test: `DOPEMUX_RENDER_MODE=plain dopemux status`)

---

## Phase 2: TUI Dashboard

### Files to modify

**`src/dopemux/ui/dashboard.py`**:
- Replace raw `Panel(Text(...), title=..., border_style=...)` with `styled_panel()`
- Replace raw `Text(...)` construction with theme style names
- Inject voice copy: roasts on error states, aftercare on break warnings
- Ensure all color references use dopemux.tcss variables (not hex literals)

**`src/dopemux/ui/dashboard_detail.py`**:
- Same migration pattern
- TabbedContent borders should use `$blue` (ritual.cyan) from tcss

**`scripts/dopemux_dashboard.py`**:
- Import from `dopemux.ui.theme` instead of inline styling
- TMUX pane borders use brand colors

### New ADHD-HUD branded elements

| Element | Color Mapping | Glyph |
|---------|--------------|-------|
| Energy gauge (low) | `serum.mint` / `$green` | 💧 |
| Energy gauge (optimal) | `ritual.cyan` / `$blue` | ⚡ |
| Energy gauge (high) | `gilt.edge` / `$yellow` | 🔥 |
| Energy gauge (critical) | `gremlin.pink` / `$pink` | 🚨 |
| Flow indicator | `ritual.cyan` | Glyphs.RUNNING |
| Break timer | `aftercare.violet` | StatusChip.AFTERCARE |
| Service health | `severity.*` styles | Glyphs.SUCCESS/ERROR/WARNING |

**Acceptance criteria**: Dashboard renders with consistent brand colors, no raw hex in Python code.

---

## Phase 3: Web Dashboard

### `ui-dashboard/src/theme.ts` — Token Expansion

Add missing tokens (currently 13 colors, need ~16):

```typescript
// Add to brandTokens.colors:
mintBright: '#B4FFEE',
mintDim: '#4A9E94',
violetDim: '#6B4FBF',

// Add text hierarchy:
textPrimary: '#E2E8F0',
textSecondary: '#94A3B8',
textMuted: '#64748B',
```

### Component branding targets

| Component | File | Change |
|-----------|------|--------|
| CognitiveLoadGauge | `src/components/CognitiveLoadGauge.tsx` | Brand gradients (halo/velvet), glow effects |
| PredictionPanel | `src/components/PredictionPanel.tsx` | Status colors from brandTokens.status |
| TaskSequencer | `src/components/TaskSequencer.tsx` | StatusChip MUI component |
| TeamDashboard | `src/components/TeamDashboard.tsx` | Full brand treatment |

**Acceptance criteria**: `npm run build` succeeds, no hardcoded hex colors outside theme.ts.

---

## Phase 4: TMUX & Terminal Chrome

### Create `configs/tmux.dopemux.conf`

```tmux
# Dopemux TMUX Brand Config
# Source of truth: src/dopemux/ui/theme.py

# Status bar
set -g status-style "fg=#7DFBF6,bg=#020617"
set -g status-left "#[fg=#020617,bg=#7DFBF6,bold] ◆ Ø ◆ #[default] "
set -g status-right "#[fg=#9B78FF]💧 hydrate #[fg=#4A9E94]%H:%M"

# Pane borders
set -g pane-border-style "fg=#4A9E94"
set -g pane-active-border-style "fg=#7DFBF6"

# Window tabs
setw -g window-status-style "fg=#64748B"
setw -g window-status-current-style "fg=#7DFBF6,bold"

# Messages
set -g message-style "fg=#94FADB,bg=#041628"
```

### Modify `src/dopemux/tmux/layouts.py` and `controller.py`
- Replace hardcoded colors with constants imported from `theme.py`
- Pane borders: `MINT_DIM`, active: `RITUAL_CYAN`

**Acceptance criteria**: TMUX sessions started via dopemux use brand palette.

---

## Phase 5: Agent Prompts & AI Output

### Create `src/dopemux/voice/agent_headers.py`

```python
"""Voice header injection for agent prompts."""

HEADERS = {
    "cli": "[LIVE] You are the DØPEMÜX Ritual Daemon. Terse. Forensic. No fluff.",
    "ui": "[LIVE] DØPEMÜX UI mode. Crisp. Direct. No threats. {label, message, action}.",
    "agent": "[LIVE] DØPEMÜX agent mode. FACT and INFERENCE clearly split. UNKNOWN+TODO over guessing.",
}

def inject_voice_header(prompt: str, surface: str = "agent") -> str:
    """Prepend the appropriate voice header to an agent prompt."""
    header = HEADERS.get(surface, HEADERS["agent"])
    return f"{header}\n\n{prompt}"
```

### Files to brand
- `services/agents/persona_enhancer.py` — add voice header to enhancement prompts
- `services/agents/dopemux_enforcer.py` — run `validate_output()` on AI responses
- `services/agents/cognitive_guardian_kg.py` — brand guardian notifications
- `src/dopemux/roles/catalog.py` — inject voice into role definitions

**Acceptance criteria**: Agent prompts include voice header, AI output passes voice gate validation.

---

## Phase 6: Notifications & ADHD Features

### Files to brand
- `services/adhd-notifier/notify.py` — StatusChip prefixes, brand copy
- `services/adhd-notifier/mobile_push.py` — branded push templates
- `services/adhd-notifier/daily_reporter.py` — brand formatting
- `services/adhd_engine/` — brand user-facing metrics
- `services/voice-commands/voice_api.py` — branded response templates

**Pattern**: Import `StatusChip` and `CopyLibrary`, prefix notifications with chips, use branded copy for messages.

**Acceptance criteria**: All user-facing notifications include StatusChip prefix and use branded copy.

---

## Phase 7: Documentation & Governance

### Flight deck docs (25 files in `docs/flight_deck/`)
- Add `━━━◆ Ø ◆━━━` brand mark to document headers
- Use StatusChip notation in status fields: `[LIVE]`, `[BLOCKER]`
- Consistent formatting per `documentation-standards.md`

### `src/dopemux/ux/launcher_wizard.py`
- Brand welcome message with Ø mark
- Brand completion with aftercare copy

### Create `docs/03-reference/brand-compliance-checklist.md`
- Checklist for new code: uses styled_table? uses styled_panel? no raw hex? voice gate passes?

**Acceptance criteria**: All flight deck docs have consistent brand headers.

---

## Phase 8: Verification & Enforcement

### Create `scripts/brand_lint.py`

Static analysis checking:
1. No `from rich.table import Table` in `commands/` (use `styled_table`)
2. No `from rich.panel import Panel` in `commands/` (use `styled_panel`)
3. No raw hex color strings like `"#7DFBF6"` in command files (use theme styles)
4. No `hard_avoid_phrases` from VOICE_GATES.yaml in user-facing strings
5. All error outputs use 3-part structure (check for `error_panel(` usage)

```python
#!/usr/bin/env python3
"""Brand lint — static analysis for brand compliance."""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMANDS_DIR = ROOT / "src/dopemux/commands"

RULES = [
    {
        "name": "no-raw-table",
        "pattern": r"from rich\.table import Table",
        "message": "Use styled_table() from dopemux.ui.theme instead of raw Table",
        "severity": "error",
    },
    {
        "name": "no-raw-panel",
        "pattern": r"from rich\.panel import Panel",
        "message": "Use styled_panel() from dopemux.ui.theme instead of raw Panel",
        "severity": "error",
    },
    {
        "name": "no-raw-hex",
        "pattern": r'(?:border_style|style)=["\']#[0-9a-fA-F]{6}',
        "message": "Use named theme styles instead of raw hex colors",
        "severity": "warning",
    },
    {
        "name": "no-hard-avoid",
        "pattern": r"(?i)(as an ai|probably|maybe|generally speaking)",
        "message": "Voice gate violation: hard_avoid phrase in user-facing string",
        "severity": "error",
        "scope": "strings_only",
    },
]

def lint_file(path: Path) -> list[dict]:
    issues = []
    content = path.read_text()
    for rule in RULES:
        for i, line in enumerate(content.splitlines(), 1):
            if re.search(rule["pattern"], line):
                issues.append({
                    "file": str(path.relative_to(ROOT)),
                    "line": i,
                    "rule": rule["name"],
                    "severity": rule["severity"],
                    "message": rule["message"],
                })
    return issues

def main() -> int:
    all_issues = []
    for py_file in COMMANDS_DIR.glob("*.py"):
        all_issues.extend(lint_file(py_file))
    # Also lint cli.py
    cli_py = ROOT / "src/dopemux/cli.py"
    if cli_py.exists():
        all_issues.extend(lint_file(cli_py))

    errors = [i for i in all_issues if i["severity"] == "error"]
    warnings = [i for i in all_issues if i["severity"] == "warning"]

    for issue in all_issues:
        icon = "❌" if issue["severity"] == "error" else "⚠️"
        print(f"{icon} {issue['file']}:{issue['line']} [{issue['rule']}] {issue['message']}")

    print(f"\n{'❌' if errors else '✅'} {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
```

### Pre-commit hook integration

Add to `.pre-commit-config.yaml`:
```yaml
- repo: local
  hooks:
    - id: brand-lint
      name: Brand compliance check
      entry: python scripts/brand_lint.py
      language: python
      pass_filenames: false
      files: ^src/dopemux/(commands/|cli\.py)
```

**Acceptance criteria**:
- `python scripts/brand_lint.py` exits 0 after Phase 1 migration
- `python scripts/sync_brand_tokens.py` exits 0
- Pre-commit hook blocks raw Rich imports in commands/

---

## Execution Order

```
Phase 0 (Foundation)     → voice.py, enriched CSV, sync script
     ↓
Deliverable 1            → BRAND_RESOURCE_PACK.md (can parallel with Phase 0)
     ↓
Phase 1 (CLI Core)       → 17 command files + cli.py entry branding
     ↓
Phase 8 (Verification)   → brand_lint.py validates Phase 1 (run early!)
     ↓
Phase 2 (TUI Dashboard)  → dashboard.py, dashboard_detail.py
     ↓
Phase 3 (Web)            → theme.ts expansion, component branding
     ↓
Phase 4 (TMUX)           → tmux.dopemux.conf, layouts.py, controller.py
     ↓
Phase 5 (Agent Prompts)  → agent_headers.py, voice header injection
     ↓
Phase 6 (Notifications)  → adhd-notifier branding
     ↓
Phase 7 (Docs)           → flight deck formatting, compliance checklist
```

---

## Verification Plan

| Check | Command | Expected |
|-------|---------|----------|
| Token sync | `python scripts/sync_brand_tokens.py` | Exit 0 |
| Brand lint | `python scripts/brand_lint.py` | 0 errors |
| Voice gates | `python -c "from dopemux.ui.voice import validate_output; print(validate_output('test'))"` | Empty list |
| Import test | `python -c "from dopemux.ui.voice import VoiceMode, CopyLibrary"` | No error |
| Render modes | `DOPEMUX_RENDER_MODE=plain dopemux --help` | No ANSI escapes |
| Web build | `cd ui-dashboard && npm run build` | Exit 0 |
| WCAG AA | All mint/cyan on ink.black > 4.5:1 | ritual.cyan=#7DFBF6 on #020617 = 15.2:1 ✅ |
