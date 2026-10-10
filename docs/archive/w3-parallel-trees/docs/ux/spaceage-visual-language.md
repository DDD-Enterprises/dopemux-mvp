---
id: SPACEAGE_VISUAL_LANGUAGE
title: Spaceage Visual Language
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Spaceage Visual Language (explanation) for dopemux documentation and developer
  workflows.
---
# Spaceage Visual Language

## Design Philosophy

The operator cockpit follows a **spaceage** aesthetic: high-information-density, symbol-first,
color-as-accent. The design principle is "color is secondary" — removing all color must leave
the interface fully functional and unambiguous.

---

## Color Token Palette

| Token            | ANSI Code          | Rich Style      | Use                            |
|------------------|--------------------|-----------------|--------------------------------|
| `color.danger`   | `\033[1;31m`       | `bold red`      | HIGH severity, blockers        |
| `color.warning`  | `\033[1;33m`       | `bold yellow`   | MEDIUM severity, warnings      |
| `color.ok`       | `\033[32m`         | `green`         | LOW severity, ready state      |
| `color.info`     | `\033[36m`         | `cyan`          | Info, scanning, headers        |
| `color.neutral`  | (none)             | `white`         | Neutral, disabled              |
| `color.accent`   | `\033[1m`          | `bold`          | Key labels, column headers     |
| `color.selected` | `\033[1;32m`       | `bold green`    | Selected strategy row          |
| `color.muted`    | `\033[2m`          | `dim`           | Secondary metadata             |

---

## Spacing Tokens

| Token          | Value                  | Use                                  |
|----------------|------------------------|--------------------------------------|
| `padding.cell` | `(0, 1)` (Rich)        | Table cell padding                   |
| `padding.grid` | `(0, 2)` (Rich)        | Grid cell padding in panels          |
| `width.narrow` | 80 columns             | COMPACT / PLAIN target               |
| `width.full`   | 100+ columns           | RICH target                          |
| `truncate.art` | 40 chars               | Artifact value truncation (PLAIN)    |
| `truncate.use` | 50 chars               | Use-case truncation in tables        |

---

## Iconography Rules

Icons supplement text. They must never be the only signal.

| Icon | Meaning                 | Used In                            |
|------|-------------------------|------------------------------------|
| ✅   | Done / Pass / Approved  | Stage rail, status badges          |
| ❌   | Failed / Error          | Stage rail, blocker severity       |
| ⚠️   | Warning                 | Health panel warnings              |
| ▶    | Active / In Progress    | Stage rail active stage            |
| ⛔   | Blocked                 | Stage rail blocked stage           |
| ○    | Pending / Not started   | Stage rail future stages           |
| 🚀   | Ready / Launch          | Status badges                      |
| ⏳   | Waiting / Pending       | Signoff state                      |
| ➖   | Not Required            | Signoff state                      |
| 💚   | Healthy                 | Monitoring health                  |
| 🔴   | Drift / Degraded        | Monitoring drift signal            |
| 🔶   | Thin Sample             | Monitoring thin-sample warning     |
| ◀    | Selected                | Strategy table selected row marker |

---

## Color-is-Secondary Test Criterion

A component passes the color-is-secondary test if:

1. All ANSI codes are stripped from its PLAIN mode output
2. The remaining text is still unambiguous and conveys all status information
3. No status is communicated **only** by color

Implementation: the `test_badge_no_ansi_in_plain_mode` test in `test_strategy_scenarios.py`
validates this invariant automatically.
