#!/usr/bin/env python3
"""
Generate terminal and web artifacts from tokens.json.

Emits:
  generated/dopemux_theme.py   — Rich Theme (TRUECOLOR + ANSI16 maps)
  generated/dopemux.tcss       — Textual CSS vars + spacing
  generated/colors.css          — Web CSS custom properties

Validation (run before emit):
  - No ANSI-16 collision among status tokens
  - WCAG AA (≥4.5) for all status + text tokens on base surface
  - Inverse text AA on filled status chips
"""
import json, sys, math
from pathlib import Path

HERE = Path(__file__).parent
TOKENS = HERE / "tokens.json"
OUT   = HERE / "generated"
OUT.mkdir(exist_ok=True)

# Live paths — written when --live flag is passed
REPO_ROOT   = HERE.parent.parent
LIVE_TCSS   = REPO_ROOT / "src/dopemux/ui/dopemux.tcss"
LIVE_WEB_TS = REPO_ROOT / "ui-dashboard/src/theme.ts"

def load():
    with open(TOKENS) as f:
        return json.load(f)

def srgb_lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def luminance(hex_color):
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.2126*srgb_lin(r) + 0.7152*srgb_lin(g) + 0.0722*srgb_lin(b)

def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)

def validate(tok):
    colors = tok["color"]
    base   = colors["base"]["hex"]
    errors = []

    # ANSI collision check
    ansi16_map = tok["_meta"]["ansi16_map"]
    seen_ansi = {}
    for slot, ansi_family in ansi16_map.items():
        if ansi_family in seen_ansi:
            errors.append(f"ANSI collision: {slot} and {seen_ansi[ansi_family]} both map to {ansi_family}")
        seen_ansi[ansi_family] = slot

    # AA check on base for status + text tokens (skip disabled — WCAG exempt)
    aa_tokens = ["success","error","warning","info","aftercare",
                 "brand","text_primary","text_secondary","text_muted"]
    for name in aa_tokens:
        if name not in colors:
            continue
        r = contrast(colors[name]["hex"], base)
        if r < 4.5:
            errors.append(f"AA FAIL: {name} {colors[name]['hex']} on base = {r:.2f} (need 4.5)")

    # Inverse text on filled chips
    inverse = colors.get("text_inverse", {}).get("hex", "#020617")
    for name in ["success","error","warning","info","aftercare","brand"]:
        if name not in colors:
            continue
        r = contrast(inverse, colors[name]["hex"])
        if r < 3.0:
            errors.append(f"CHIP FAIL: text_inverse on {name} = {r:.2f} (need 3.0 large-text min)")

    return errors

def emit_rich_theme(tok):
    c = tok["color"]
    lines = [
        '"""Auto-generated Rich theme — Direction B Electric Refresh. DO NOT EDIT."""',
        'from rich.theme import Theme',
        '',
        '# ANSI-16 fallback map (NO_COLOR / 16-color terminals)',
        '_ANSI16 = {',
        f'    "success":   "bold green",',
        f'    "error":     "bold red",',
        f'    "warning":   "bold yellow",',
        f'    "info":      "bold cyan",',
        f'    "aftercare": "bold blue",',
        '}',
        '',
        'def build_theme(truecolor: bool = True) -> Theme:',
        '    """Return Rich Theme. Pass truecolor=False for 16-color terminal."""',
        '    if not truecolor:',
        '        return Theme({',
        '            "success":  _ANSI16["success"],',
        '            "error":    _ANSI16["error"],',
        '            "warning":  _ANSI16["warning"],',
        '            "info":     _ANSI16["info"],',
        '            "aftercare":_ANSI16["aftercare"],',
        '            "text":     "default",',
        '            "text.dim": "dim",',
        '            "heading":  "bold",',
        '        })',
        '    return Theme({',
        f'        "brand":          "bold {c["brand"]["hex"]}",',
        f'        "brand.dim":      "{c["brand_dim"]["hex"]}",',
        f'        "success":        "bold {c["success"]["hex"]}",',
        f'        "error":          "bold {c["error"]["hex"]}",',
        f'        "warning":        "bold {c["warning"]["hex"]}",',
        f'        "info":           "{c["info"]["hex"]}",',
        f'        "aftercare":      "{c["aftercare"]["hex"]}",',
        f'        "accent":         "{c["gremlin_pink"]["hex"]}",',
        f'        "text":           "{c["text_primary"]["hex"]}",',
        f'        "text.dim":       "{c["text_secondary"]["hex"]}",',
        f'        "text.muted":     "{c["text_muted"]["hex"]}",',
        f'        "text.disabled":  "{c["text_disabled"]["hex"]}",',
        f'        "heading":        "bold {c["brand"]["hex"]}",',
        f'        "subheading":     "bold {c["brand_dim"]["hex"]}",',
        f'        "chip.live":      "bold {c["info"]["hex"]}",',
        f'        "chip.done":      "bold {c["success"]["hex"]}",',
        f'        "chip.blocked":   "bold {c["error"]["hex"]}",',
        f'        "chip.warn":      "bold {c["warning"]["hex"]}",',
        f'        "chip.aftercare": "{c["aftercare"]["hex"]}",',
        f'        "table.header":   "bold {c["brand"]["hex"]}",',
        f'        "table.border":   "{c["border_strong"]["hex"]}",',
        f'        "panel.border":   "{c["border_strong"]["hex"]}",',
        f'        "panel.title":    "bold {c["brand"]["hex"]}",',
        f'        "bar.complete":   "{c["brand"]["hex"]}",',
        f'        "bar.pulse":      "{c["gremlin_pink"]["hex"]}",',
        '    })',
        '',
        '# Convenience singleton (truecolor)',
        'THEME = build_theme()',
    ]
    return '\n'.join(lines)

def emit_tcss(tok):
    c = tok["color"]
    sp = tok["spacing"]
    r  = tok["radius"]
    h  = tok["hue"]
    lines = [
        '/* Auto-generated Textual CSS vars — Direction B Electric Refresh */',
        ':root {',
        f'    --hue-display: {h["display"]};',
        f'    --hue-body:    {h["body"]};',
        f'    --hue-mono:    {h["mono"]};',
        f'    --base:           {c["base"]["hex"]};',
        f'    --raised:         {c["raised"]["hex"]};',
        f'    --overlay:        {c["overlay"]["hex"]};',
        f'    --border:         {c["border"]["hex"]};',
        f'    --border-strong:  {c["border_strong"]["hex"]};',
        f'    --brand:          {c["brand"]["hex"]};',
        f'    --brand-dim:      {c["brand_dim"]["hex"]};',
        f'    --success:        {c["success"]["hex"]};',
        f'    --error:          {c["error"]["hex"]};',
        f'    --warning:        {c["warning"]["hex"]};',
        f'    --info:           {c["info"]["hex"]};',
        f'    --aftercare:      {c["aftercare"]["hex"]};',
        f'    --accent:         {c["gremlin_pink"]["hex"]};',
        f'    --text:           {c["text_primary"]["hex"]};',
        f'    --text-dim:       {c["text_secondary"]["hex"]};',
        f'    --text-muted:     {c["text_muted"]["hex"]};',
        f'    --text-disabled:  {c["text_disabled"]["hex"]};',
        f'    --text-inverse:   {c["text_inverse"]["hex"]};',
        f'    --sp-xs:  {sp["xs"]}px;',
        f'    --sp-sm:  {sp["sm"]}px;',
        f'    --sp-md:  {sp["md"]}px;',
        f'    --sp-lg:  {sp["lg"]}px;',
        f'    --sp-xl:  {sp["xl"]}px;',
        f'    --radius-sm:   {r["sm"]}px;',
        f'    --radius-md:   {r["md"]}px;',
        f'    --radius-pill: {r["pill"]}px;',
        '}',
    ]
    return '\n'.join(lines)

def emit_css(tok):
    c = tok["color"]
    sp = tok["spacing"]
    r  = tok["radius"]
    el = tok["elevation"]
    h  = tok["hue"]
    lines = [
        '/* Auto-generated web CSS vars — Direction B Electric Refresh */',
        ':root {',
        f'    --hue-display: "{h["display"]}";',
        f'    --hue-body:    "{h["body"]}";',
        f'    --hue-mono:    "{h["mono"]}";',
        f'    --color-base:          {c["base"]["hex"]};',
        f'    --color-raised:        {c["raised"]["hex"]};',
        f'    --color-overlay:       {c["overlay"]["hex"]};',
        f'    --color-border:        {c["border"]["hex"]};',
        f'    --color-border-strong: {c["border_strong"]["hex"]};',
        f'    --color-brand:         {c["brand"]["hex"]};',
        f'    --color-brand-dim:     {c["brand_dim"]["hex"]};',
        f'    --color-success:       {c["success"]["hex"]};',
        f'    --color-error:         {c["error"]["hex"]};',
        f'    --color-warning:       {c["warning"]["hex"]};',
        f'    --color-info:          {c["info"]["hex"]};',
        f'    --color-aftercare:     {c["aftercare"]["hex"]};',
        f'    --color-accent:        {c["gremlin_pink"]["hex"]};',
        f'    --color-text:          {c["text_primary"]["hex"]};',
        f'    --color-text-dim:      {c["text_secondary"]["hex"]};',
        f'    --color-text-muted:    {c["text_muted"]["hex"]};',
        f'    --color-text-disabled: {c["text_disabled"]["hex"]};',
        f'    --color-text-inverse:  {c["text_inverse"]["hex"]};',
        f'    --sp-xs:  {sp["xs"]}px;',
        f'    --sp-sm:  {sp["sm"]}px;',
        f'    --sp-md:  {sp["md"]}px;',
        f'    --sp-lg:  {sp["lg"]}px;',
        f'    --sp-xl:  {sp["xl"]}px;',
        f'    --radius-sm:   {r["sm"]}px;',
        f'    --radius-md:   {r["md"]}px;',
        f'    --radius-pill: {r["pill"]}px;',
        f'    --shadow-subtle:  {el["subtle"]};',
        f'    --shadow-overlay: {el["overlay"]};',
        '}',
    ]
    return '\n'.join(lines)

def emit_textual(tok):
    """Emit Textual CSS $var syntax for src/dopemux/ui/dopemux.tcss."""
    c = tok["color"]
    h = tok["hue"]
    lines = [
        '/* Dopemux Direction B Electric Refresh — shared Textual CSS',
        ' *',
        ' * Source of truth: claudedocs/design/tokens.json',
        ' * Generated by: claudedocs/design/generate_tokens.py',
        ' * Used by: dashboard.py, dashboard_detail.py',
        ' */',
        '',
        f'$base: {c["base"]["hex"]};',
        f'$mantle: {c["raised"]["hex"]};',
        f'$crust: {c["overlay"]["hex"]};',
        f'$text: {c["text_primary"]["hex"]};',
        f'$text-dim: {c["text_secondary"]["hex"]};',
        f'$text-muted: {c["text_muted"]["hex"]};',
        f'$green: {c["success"]["hex"]};',
        f'$blue: {c["brand"]["hex"]};',
        f'$mauve: {c["aftercare"]["hex"]};',
        f'$red: {c["error"]["hex"]};',
        f'$peach: #FFCF78;',
        f'$yellow: {c["warning"]["hex"]};',
        f'$mint-dim: #4A9E94;',
    ]
    return '\n'.join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate dopemux design tokens")
    parser.add_argument("--live", action="store_true",
                        help="Also write to live src/dopemux/ui/dopemux.tcss")
    args = parser.parse_args()

    tok = load()
    errs = validate(tok)
    if errs:
        print("VALIDATION FAILED:")
        for e in errs:
            print(f"  ✗ {e}")
        sys.exit(1)
    print("Validation: PASS")

    (OUT / "dopemux_theme.py").write_text(emit_rich_theme(tok))
    print("  ✓ generated/dopemux_theme.py")

    (OUT / "dopemux.tcss").write_text(emit_tcss(tok))
    print("  ✓ generated/dopemux.tcss (web CSS vars preview)")

    textual_out = emit_textual(tok)
    (OUT / "dopemux_textual.tcss").write_text(textual_out)
    print("  ✓ generated/dopemux_textual.tcss (Textual $vars)")

    (OUT / "colors.css").write_text(emit_css(tok))
    print("  ✓ generated/colors.css")

    if args.live:
        if LIVE_TCSS.exists():
            # Preserve the rule blocks below the palette vars header
            existing = LIVE_TCSS.read_text()
            # Find the first blank line after the var block (after $mint-dim line)
            split_marker = "$mint-dim"
            idx = existing.find(split_marker)
            if idx != -1:
                tail = existing[idx + len(split_marker):]
                # tail starts from after $mint-dim: ...; — find end of that line
                eol = tail.find('\n')
                rule_blocks = tail[eol:]  # everything after the vars
                LIVE_TCSS.write_text(textual_out + rule_blocks)
                print(f"  ✓ LIVE {LIVE_TCSS} (palette vars updated, rules preserved)")
            else:
                print(f"  ⚠ LIVE {LIVE_TCSS}: split marker not found — skipped (run manually)")
        else:
            print(f"  ⚠ LIVE {LIVE_TCSS}: not found — skipped")

if __name__ == "__main__":
    main()
