# Cockpit UI Kit

React+Babel recreation of the dopemux cockpit TUI as it renders in a real
terminal. Mirrors `src/dopemux/ui/cockpit/render.py` and the seed data in
`src/dopemux/ui/cockpit/seed.py`.

## Files

- `index.html` — interactive cockpit, default 120x40, with a size toggle
  for 100x32 and 80x24
- `Primitives.jsx` — the cockpit primitives: `Frame`, `Pane`, `PaneHeader`,
  `Rule`, `Row`, `ServiceRow`, `RunRow`, `ModeBar`, `Inspector`, `Chip`,
  `Src`, `Selector`, `CommandRail`, `StatusRail`, `HintRail`
- `Cockpit.jsx` — composed screen + size-switch shell
- `seed.js` — deterministic seed data (mirrors `seed.py`)
- `cockpit.css` — styling layer; consumes `colors_and_type.css`

## Component contract

Every component enforces:
- closed chip set: `LIVE | BLOCKER | OVERRIDE | LOGGED | AFTERCARE | EDGE`
- every row carries `SRC=<service>` (the `Src` component)
- panes declare `authority:` in their header
- bridge / proxy actions live in their own pane, labeled `adapter-only segregated`

## Not included

By contract:
- no hover states (this is a TUI; the keyboard is the input)
- no mouse handlers beyond the size switcher
- no animations
- no chat / chat composer / unified PM record
- no new chips, modes, or status tokens beyond the closed set
