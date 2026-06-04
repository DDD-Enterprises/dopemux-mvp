# Audit — "DØPEMÜX Design System" Claude Design bundle (Palette Directions)

**Date:** 2026-06-04 · **Source:** `api.anthropic.com/v1/design/h/CViEiM5hApMmPIffQtUcMQ`
**Bundle:** `d-pem-x-design-system/` (README + 3 chats + project: HTML/JSX/CSS kits + previews)
**Auditor task:** implement `DOPEMUX Palette Directions.html`; advise if it's a sound design-system spine.
**Verdict:** **NOT ready as the design-system token spine as-is.** Its canonical token layer reverts
the merged Direction B (PR #803). The *voice / IA / component vocabulary* is strong and reusable.
Nothing written to repo tokens/theme — doing so would regress merged work.

---

## What the bundle is

A Claude Design handoff: a brand-grounded `DØPEMÜX Design System` with a README (voice + visual
foundations + iconography), CLI and Cockpit web kits, preview cards, and a
`DOPEMUX Palette Directions.html` canvas showing **three palette directions A/B/C** for comparison.
It read the real repo (`BRAND_SYSTEM.md`, `theme.py`, `theme.ts`, voice bible) and the voice/IA
capture is genuinely good.

## The core finding — the bundle contradicts itself on the one fence that matters

There are **three different "danger" definitions** in one bundle:

| Layer | Danger color | ANSI-16 downsample | Status |
|---|---|---|---|
| `Palette Directions.html` (the file to implement) — all 3 dirs | red-family (`#FF5577`/`#FF3D63`/`#D9697E`) | **red** | ✓ correct |
| `colors_and_type.css` (canonical "import this") | `#FF4FC4` | **magenta (hue 320°)** | ✗ wrong |
| README prose + both UI kits | `#FF4FC4` "danger as hot pink, not red" | **magenta** | ✗ wrong |

The exploration canvas says one thing (red danger); the actual shipped tokens, components, and
README narration say the opposite (pink danger). The component kits (`ui_kits/cli`, `ui_kits/cockpit`)
both hardcode `--gremlin-pink #FF4FC4` → `--chip-blocker` / `--state-critical` / `--energy-critical`.
So **every component inherits magenta danger.**

This is the exact regression PR #803 (merged) fixed: error→red `#FF2255` for ANSI/colorblind
fidelity, and `text-muted` `#64748B`→`#808DA0` for WCAG AA. The bundle's canonical CSS still ships
both old values (`--gremlin-pink #FF4FC4`, `--text-muted #64748B`).

## Computed fences (not asserted)

ANSI-16 hue anchor + WCAG AA on each layer's own declared base:

| Palette | error hue / ANSI | error AA | muted AA | ANSI collision | Verdict |
|---|---|---|---|---|---|
| **canonical `colors_and_type.css`** | 320° **magenta** ✗ | 6.99 ✓ | **4.31 ✗** | none | **FAIL** (danger not red; muted sub-AA) |
| Palette Directions **A** (structural-fix) | 348° red ✓ | 6.31 ✓ | 5.77 ✓ | none | PASS |
| Palette Directions **B** (electric) | 348° red ✓ | 5.64 ✓ | 6.26 ✓ | none | PASS |
| Palette Directions **C** (calm) | 349° red ✓ | 5.80 ✓ | 5.77 ✓ | none | PASS |
| **SHIPPED `tokens.json` (PR #803)** | 346° red ✓ | 5.39 ✓ | 5.99 ✓ | none | PASS (current spine) |

Key reads:
- The **canonical token file is the only FAIL** — and it's the file the README tells implementers to
  import and the kits actually consume.
- **Palette Directions "Direction A" ≈ our shipped Direction B** at the structural level: red danger
  + AA-passing `#808DA0` muted. The exploration canvas already agrees with the merged spine; it's the
  `colors_and_type.css` + README that are stale.
- Surface inconsistency: base is `#01040E` (CSS/README) vs `#0C0D10` (Palette Directions HTML/JSX) vs
  our shipped `#020617` — three bases.

## On "implement Palette Directions.html"

Largely a **no-op against current state**. It's a 3-way comparison, not a single palette; you pick
one, you don't "implement" all three. Its sound choice (Direction A: red danger, AA muted) is what we
**already shipped and merged** as Direction B in `tokens.json` (PR #803). The only thing in the bundle
that would change repo state is adopting `colors_and_type.css` — and that is a **regression** (reverts
#803's error→red and the AA muted fix). Per governance (contract-sensitive canonical writers; runtime
outranks a handoff doc; surface conflicts, don't silently revert), that was **not** applied.

## What IS worth adopting from the bundle

The token layer is stale, but these are strong and reusable for the TUI design system:
- **Voice capture** — operator/personality dual register, STATUS/KEY FACTS/RISKS/NEXT shape, 3-part
  errors, banned/avoid lexical gates, empty-state and success-state rules. Matches `BRAND_SYSTEM.md`.
- **IA + component vocabulary** — bracketed mono chips, panel eyebrows, halo/velvet surface model,
  energy-state naming, iconography (Iosevka Term + Nerd Font + box-drawing brand mark, no SVG).
- **The Palette Directions canvas itself** — a useful A/B/C comparison artifact; Direction A validates
  our shipped spine independently.

## Recommendation — build the TUI design system on the SHIPPED spine + bundle's identity

This mirrors the reconciliation already done earlier this session (and the merged #803 outcome):

1. **Token spine = `claudedocs/design/tokens.json`** (Direction B, merged, fences-pass). **Do not**
   adopt the bundle's `colors_and_type.css` — it reverts danger→magenta and muted→sub-AA.
2. **Voice + IA + component vocabulary = the bundle's README** (it's excellent and repo-grounded), folded
   into the existing `tui-design-spec.md` / Cockpit TUI Design System where not already covered.
3. If a refreshed palette is ever wanted, **Palette Directions Direction A** is the fences-passing pick
   and is ~= what's already shipped — a re-pick would be cosmetic, not structural.
4. One genuine open question for the user: the bundle revives **pink-as-danger** as deliberate brand
   doctrine ("the personality leaking into the operator surface"). PR #803 + `BRAND_SYSTEM.md` resolved
   that to **red danger + pink as non-status accent** for terminal/colorblind fidelity. That tension is
   a brand call, not a bug — but it's already decided in the merged direction. Reopening it would revert
   ANSI/AA fidelity.

## Bottom line

- **Ready to build the TUI design system on this bundle's token layer?** **No** — its canonical
  `colors_and_type.css` fails the ANSI-red and AA-muted fences and contradicts merged #803.
- **Ready to build on this bundle's voice/IA/component identity + the shipped `tokens.json` spine?**
  **Yes** — that's the reconciled path, and it's already most of the way there via #803 and the
  `tui-design-spec.md`.
- **Net:** adopt the bundle's *identity*, keep the shipped *tokens*. No repo tokens/theme changed by
  this audit.
