# UX/UI Branding Expansion Plan

**Objective**: Deeply analyze the DØPEMÜX codebase and implement maximum-fidelity branding, UX/UI flair, and Ritual Daemon personality across all untamed surfaces. This plan expands upon the foundational `BRAND_SYSTEM_IMPLEMENTATION.md`.

## 1. The Branded Progress Ritual (Custom Spinners)
The codebase heavily utilizes `rich.progress.Progress` (over 100 occurrences). Currently, these use default spinners and styles.
- **Action**: Create `src/dopemux/ui/progress.py`.
- **Implementation**: Define a `branded_progress()` context manager that utilizes a custom `SpinnerColumn`.
- **Flair**: Implement a custom animation sequence (e.g., a rotating `Ø`, or a pulsing `[=] [>] [=]` cyberpunk matrix). Use brand colors (`ritual.cyan`, `gremlin.pink` for errors) and replace "Time Remaining" with "Temporal Limit".

## 2. Clinical Forensics Exception Handler
Unhandled exceptions and `ClickException`s currently dump standard Python tracebacks or basic error messages.
- **Action**: Intercept `sys.excepthook` and Click's error handling.
- **Implementation**: Create a `dopemux.ui.errors` module. When a crash occurs, catch the traceback and render it inside a `styled_panel` with a bright `gremlin.pink` border.
- **Voice**: Inject `VoiceMode.CLINICAL_FORENSICS` or `VoiceMode.UX_SCOLD` (e.g., `[BLOCKER] 🚨 Critical Ritual Failure. Core dump initiated...`). Use `rich.traceback` for beautiful, syntax-highlighted error logs.

## 3. The Ignition Sequence (Boot Splash Screens)
Commands like `dopemux start` and `dopemux launch` output basic text (e.g., "🚀 Launching...").
- **Action**: Create a cinematic, high-fidelity boot sequence.
- **Implementation**: Use `rich.live.Live` to display an ASCII art DØPEMÜX logo that glitches into existence, followed by a rapid, fake "system mounting" log stream.
- **Flair**: `Mounting neural telemetry... [OK]`, `Synchronizing MCP arrays... [OK]`, `Engaging flight-deck... [ACTIVE]`.

## 4. Ritual Prompts (Interactive Inputs)
The codebase uses raw `click.prompt` and `rich.prompt.Prompt` across many setup scripts (`profile_wizard.py`, `install.py`).
- **Action**: Wrap interactive inputs in a branded function.
- **Implementation**: Create `dopemux_prompt()` and `dopemux_confirm()` in `dopemux.ui.theme`.
- **Voice**: Style the question text using `[mint]` and prefix with emojis. (e.g., `⚡ [mint]Engage destructive sequence?[/mint] [y/N]: `).

## 5. Telemetry Log Styling
Standard `console.logger` logs look like generic Python logs.
- **Action**: Customize the `rich.logging.RichHandler`.
- **Implementation**: Modify `src/dopemux/console.py` to format log records.
- **Flair**: Prefix debug logs with `[text.dim][SIGNAL][/text.dim]`, info logs with `[mint][TELEMETRY][/mint]`, and warnings with `[gilt.edge][HAZARD][/gilt.edge]`. Format timestamps as `T-minus` style if possible.

## 6. Textual Dashboard Overdrive (TUI Flair)
The `src/dopemux/ui/dopemux.tcss` file establishes colors, but lacks kinetic flair.
- **Action**: Enhance the Textual UI.
- **Implementation**:
    - Add `text-style: blink;` to active state indicators.
    - Change static panel titles (e.g., "Services") to Ritual Daemon equivalents ("Daemon Neural Array", "Mission Velocity").
    - Inject ASCII sparklines or block characters (` ▂▃▄▅▆▇█`) for resource monitoring instead of plain numbers.

## 7. Web Dashboard Materialization (`ui-dashboard`)
The web UI uses basic MUI components.
- **Action**: Inject cyberpunk/HUD elements into the DOM.
- **Implementation**: 
    - Add subtle CSS drop-shadows (glow effects) to `mint` and `cyan` elements.
    - Add a "CRT scanline" overlay to the main container.
    - Implement a typing animation (glitch text) for header loading states.

## 8. Agent Auto-Correction Middleware
Agents sometimes break character ("I am an AI...").
- **Action**: Implement output filtering middleware.
- **Implementation**: In the `dopemux/claude_tools/` integrations, pass all LLM responses through a regex filter that strips out apologetic AI jargon, enforcing the terse, forensic `[LIVE]` personality before it ever hits the terminal.

---
**Verification**: All new components should be validated against the `BRAND_SYSTEM_IMPLEMENTATION.md` specs and pass the `scripts/brand_lint.py` scanner.