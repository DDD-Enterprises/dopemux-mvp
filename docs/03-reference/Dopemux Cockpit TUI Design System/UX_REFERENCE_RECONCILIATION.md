---
id: COCKPIT_UX_REFERENCE_RECONCILIATION
title: UX Reference Reconciliation
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-25'
last_review: '2026-04-25'
next_review: '2026-07-25'
prelude: Reconciles the docs/ux supporting reference set with the cockpit doctrine. The cockpit doctrine wins on conflict; UX references are supporting constraints, not cockpit runtime proof.
---

# UX Reference Reconciliation

## Purpose

The cockpit design system has its own doctrine. The UX reference set under `docs/ux/` (referred to in this package as `docs-ux/`) provides supporting visual, fallback, and component constraints. UX references are not cockpit runtime proof and are not authority on cockpit pane semantics.

This file states which docs-ux rules are preserved, which are demoted, and how conflicts are resolved.

---

## Reference Trust Order

In order of authority for cockpit decisions:

1. `ARCHITECTURE_SAFETY_OVERLAY.md` (this package) — overrides all others on conflict.
2. `PM_IMPLEMENTER_COCKPIT_REDIRECTION.md` (this package) — narrower than the overlay; compatible with it.
3. `PREIMPLEMENTATION.md` and `ACCEPTANCE.md` (this package) — gating preconditions and contradiction checks.
4. `SKILL.md` (this package) — operational summary; reflects the overlay.
5. `docs-ux/plain-text-fallback-rules.md` — binding for fallback / log-safe rendering.
6. `docs-ux/status-and-severity-model.md` — supporting; severity preserved, badge set demoted where it conflicts.
7. `docs-ux/spaceage-visual-language.md` — supporting; color-secondary preserved, decorative rules demoted.
8. `docs-ux/component-library.md` — supporting inspiration only; not cockpit runtime proof.
9. `docs-ux/terminal-rendering-guide.md` — UNKNOWN unless local content proves otherwise.
10. `docs-ux/ux-style-guide.md` — compatibility-only legacy reference.

---

## Mapping Table

| docs-ux file                                | Role in cockpit                                                                                                | Status                                       |
|---------------------------------------------|----------------------------------------------------------------------------------------------------------------|----------------------------------------------|
| `docs-ux/plain-text-fallback-rules.md`      | Binding fallback / log-safe render constraints. PLAIN and AUDIT modes follow these rules.                       | Preserved (binding)                          |
| `docs-ux/component-library.md`              | Reusable component inspiration. Not cockpit runtime proof. A component existing here does not mean it is wired. | Preserved as inspiration; demoted as proof   |
| `docs-ux/spaceage-visual-language.md`       | Preserve color-is-secondary and density principles. Demote emoji/icon list and old color tokens.               | Mixed: preserved core, demoted decorations   |
| `docs-ux/status-and-severity-model.md`      | Preserve severity distinction. Demote UNKNOWN chip and the older badge set.                                    | Mixed: preserved severity, demoted chips     |
| `docs-ux/terminal-rendering-guide.md`       | UNKNOWN / no body content unless local content proves otherwise. Treat as candidate reference, not contract.   | UNKNOWN unless proven                        |
| `docs-ux/ux-style-guide.md`                 | Legacy reference. Use only for compatibility checks; do not cite as cockpit doctrine.                          | Compatibility-only                           |

---

## Preserved Rules

The following rules from docs-ux are preserved and binding on cockpit work:

1. PLAIN and AUDIT modes must be log-safe. Output must remain machine-readable and stable across runs.
2. PLAIN and AUDIT output must not contain ANSI escape codes.
3. Color is secondary. Text and symbols must carry meaning without color. Removing color must not destroy meaning.
4. Components should support plain string rendering where applicable.
5. Tables, cards, and rails must remain scannable and deterministic. No animation in PLAIN/AUDIT.
6. Severity distinctions (HIGH / MEDIUM / LOW or equivalent ordered scale) are preserved as a property of records, not as cockpit chips.
7. Density and information-first layout are preserved. Decoration may not push canonical fields below the fold.

---

## Demoted / Stale Rules

The following docs-ux rules are demoted because they conflict with this package's doctrine:

1. Emoji / icon-only signaling. Symbols may appear as a secondary cue; meaning must be carried by text. Glyph-only signals are demoted.
2. UNKNOWN as a chip / badge. UNKNOWN is literal text in the affected field. The closed chip set is `LIVE | BLOCKER | OVERRIDE | LOGGED | AFTERCARE | EDGE`.
3. Older color token models that conflict with the mint-mojo production default. Use the production default; older tokens are reference-only.
4. "Spaceage" rhetoric used as decoration or hype. The aesthetic is information-density and symbol-first; "spaceage" is style language, not a feature.
5. PR Merge Specialist component patterns that imply cockpit runtime proof. Those patterns may inspire components but do not certify a runtime.
6. Any docs-ux passage that implies dopemux owns canonical PM, decision, or workflow state. Authority is per-domain (see overlay).

---

## Conflict Resolution Rule

When a docs-ux passage conflicts with this package:

1. The cockpit doctrine wins.
2. The docs-ux passage is preserved in place (read-only references) but is annotated in this file as demoted or compatibility-only.
3. If a mock or implementation cites a demoted docs-ux rule as cockpit doctrine, the citation is a violation. Replace it with a citation to the corresponding cockpit doctrine file.
4. If a docs-ux passage and this package disagree on a chip name, on a status word, on bridge phrasing, or on SRC placement, this package wins. The docs-ux file is not patched (it is read-only); the cockpit work is patched to follow this package.

When in doubt, declare UNKNOWN in the cockpit work and open a question, rather than promoting a docs-ux rule that conflicts with the overlay.
