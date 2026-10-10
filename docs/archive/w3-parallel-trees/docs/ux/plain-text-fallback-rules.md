---
id: PLAIN_TEXT_FALLBACK_RULES
title: Plain Text Fallback Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Plain Text Fallback Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Plain Text Fallback Rules

## Purpose

These are normative rules governing all PLAIN and AUDIT mode output.  Violations are bugs.

---

## Rule 1: `RenderMode` Detection Order

Detection must follow this exact priority (implemented in `detect_render_mode()`):

1. `audit=True` → `RenderMode.AUDIT`
2. `plain=True` OR `not sys.stdout.isatty()` → `RenderMode.PLAIN`
3. `compact=True` OR terminal columns < 100 → `RenderMode.COMPACT`
4. Default → `RenderMode.RICH`

No rule may be skipped.  Detection happens once at startup and is passed to `RichTerminalRenderer`.

---

## Rule 2: No Rich Objects in PLAIN/AUDIT Mode

In `PLAIN` and `AUDIT` modes:

- `RichTerminalRenderer` must **never** import or instantiate Rich renderables
- The `console.print()` method must **not** be called
- Only `print()` (stdlib) is permitted for output
- `return_obj=True` must return a `str`, not a Rich `Panel`, `Table`, or `Text`

Reference implementation: `badge()` method in `ux_engine.py`.

---

## Rule 3: Log-Safe Output Requirement

PLAIN mode output must be safe for:

- Redirection to files (`> output.log`)
- Piping through grep/awk
- CI log storage (GitHub Actions, Jenkins)
- Log aggregation systems (Splunk, Datadog)

This means:

- No ANSI escape codes (`\033[...]`)
- No Unicode characters that break fixed-width terminals (emojis are allowed but optional)
- Lines should not exceed 200 characters
- Output must be valid UTF-8

---

## Rule 4: `badge()` as Reference Pattern

The `badge()` method is the canonical reference for the PLAIN-mode pattern:

```python
def badge(self, label: str, severity: str = "INFO") -> str:
    # In RICH/COMPACT: may use styling
    # In PLAIN/AUDIT: returns plain text "[label]" — no ANSI
    return f"[{label}]"
```

All other methods follow this same pattern: inspect `self.mode` and return/print
plain text when `self.mode in (RenderMode.PLAIN, RenderMode.AUDIT)`.

---

## Rule 5: Component Method Signature Contract

Every component method must:

1. Accept `return_obj: bool = False` as a keyword argument
2. In PLAIN/AUDIT mode with `return_obj=False`: call `print()` and return `None`
3. In PLAIN/AUDIT mode with `return_obj=True`: return a `str` and do not print
4. In RICH/COMPACT mode with `return_obj=False`: call `self.console.print()` and return `None`
5. In RICH/COMPACT mode with `return_obj=True`: return a Rich renderable and do not print

---

## Automated Validation

The following tests in `tests/test_strategy_scenarios.py` enforce these rules:

- `TestUXRenderModes::test_badge_no_ansi_in_plain_mode`
- `TestUXRenderModes::test_blocker_table_plain_no_rich`
- `TestUXRenderModes::test_detect_render_mode_non_tty`
- `TestMonitoringHealthPanel::test_thin_sample_label_in_plain_output`
