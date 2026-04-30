# PREIMPLEMENTATION.md

> Read this **before** any implementer touches code.
> The Dopemux cockpit design system is a **visual reference**. It is not
> implementation-ready code. Treat every file in this folder as design
> intent, not a build target.

---

## What this package is

A design-system reference for the Dopemux operator cockpit. It contains:

- `colors_and_type.css` — tokens (palette, type, chip mapping, grid invariants)
- `preview/*.html` — design-system reference cards (palette, chips, frame
  grid, etc.)
- `surfaces/A1..A3` — static terminal snapshots, the canonical TUI form
- `surfaces/B`       — live Textual cockpit *direction* (not implemented)
- `surfaces/C`       — web/operator dashboard *direction* (not implemented)
- `ui_kits/cockpit/` — composed React mockups for visual review only

It does **not** contain backend code, service adapters, RTE runner
integrations, state stores, API routes, or database schemas. Nothing in
this folder may be copied into production as-is.

---

## What this package is NOT

- A new product architecture.
- A unified backend authority.
- A bridge / proxy / adapter promoted to authority.
- A live cockpit. Surfaces B and C are scope-marker mockups.
- A redefinition of the status taxonomy.
- A proof-bundle generator. There is no proof generation here.
- A live RTE runner. There is no extraction execution here.

---

## Authority boundaries (preserve these literally)

The cockpit shows data from many separate authorities. **Do not collapse
them.** Every authority below is independent and remains source of truth
for its own domain:

| Authority             | Owns                                           | Cockpit role     |
|-----------------------|------------------------------------------------|------------------|
| `dopemux`             | operator control surface, command authority    | shell + chrome   |
| `dopetask`            | external execution handoff (wrapper scripts)   | reference only   |
| `task-orchestrator`   | workflow-significant transitions, workflow vw  | reference        |
| `leantime`            | passive PM metadata, project/ticket snapshot   | reference        |
| `conport`             | structured decisions, progress, custom data    | reference        |
| `dope-memory`         | chronicle / evidence-preserving history        | reference        |
| `dope-context`        | deterministic code/docs retrieval, indexing    | reference        |
| `dopecon-bridge`      | adapter/proxy/event transport                  | **segregator**   |
| `adhd-engine`         | operator-support / cognitive-state             | reference        |
| `repo-truth-extractor`| extraction runtime + proof artifacts           | RTE pane         |

`dopecon-bridge` is **never an authority** for the data it transports.
The cockpit segregates bridge actions into their own pane and labels them
`[EDGE] adapter-only segregated`. If any future implementation surfaces
bridge-routed data without a real authority, label that authority
`UNKNOWN` and keep the segregator visible.

---

## Token mapping (do not invent)

### Color → meaning
| Token              | Hex       | Encodes                             |
|--------------------|-----------|--------------------------------------|
| `--ritual-cyan`    | `#7DFBF6` | LIVE · heading · primary accent      |
| `--serum-mint`     | `#94FADB` | LOGGED · verified trace              |
| `--gremlin-pink`   | `#FF8BD1` | BLOCKER · failed gate · critical     |
| `--gilt-edge`      | `#F5F26D` | OVERRIDE · attention · operator gate |
| `--aftercare-violet`| `#9B78FF`| AFTERCARE · follow-up                |
| `--mint-dim`       | `#4A9E94` | frame / panel border / muted rule    |

**No** `--severity-*`, `--success-*`, `--warning-*`, `--error-*`,
`--info-*`, `--debug-*`, `--hazard-*`, `--danger-*`. The closed chip set
*is* the status taxonomy.

If a state isn't in `{LIVE, BLOCKER, OVERRIDE, LOGGED, AFTERCARE, EDGE}`,
it doesn't exist. Map external vocab at the boundary:
`DEGRADED → OVERRIDE`, `FAILED → BLOCKER`, `BLOCKED → BLOCKER`,
`SYNC → AFTERCARE`, `UNKNOWN → EDGE`.

If you genuinely need a new color, mark it `NEEDS TOKEN` in the design
and surface the request to the design owner. Do not invent hex values.

---

## Chrome vs. data: the SRC rule

`SRC=<service>` is **provenance**. It belongs only to:

- data rows (run rows, service rows)
- the inspector pane
- evidence / proof traces
- bridge segregator action lines

`SRC=` does **not** belong on:

- the top frame header / chrome rail
- the mode bar
- the command rail
- the status rail
- the bottom flag rail

Chrome communicates surface state. Data carries provenance. Crossing
that line implies the cockpit owns data it merely displays.

---

## Implementation guardrails

When (later) implementing any of this in real code:

1. **Map every visual to an existing Dopemux primitive first.**
   Do not duplicate `Button`, `Card`, `Input`, `Badge`, `Tag`, `Dialog`.
   The TUI primitives in `src/dopemux/ui/cockpit/` (`Frame`, `PaneHeader`,
   `Rule`, `Row`, `Chip`, `ServiceRow`, `RunRow`, `ModeBar`,
   `CommandRail`, `StatusRail`, `Inspector`, `BridgeSegregator`) are the
   set. If a new primitive seems necessary, justify it before adding.
2. **Use strict TSX** if implementing on the web. No untyped JSX. No
   `any`. Type the closed chip set as a string-literal union; let the
   compiler reject invented chips.
3. **Preserve token names verbatim** (`--ritual-cyan`, `--chip-blocker`,
   etc.). Do not rename to `--primary-500`, `--brand-50`, etc.
4. **No global state rewrites.** Cockpit state belongs to the cockpit
   surface; backend authorities own their own state.
5. **No DOM duplication for responsiveness.** Three sizes
   (120×40 / 100×32 / 80×24) are character-grid breakpoints, not
   viewport breakpoints. Do not mirror this with two parallel JSX trees.
6. **No CSS/web idioms in TUI references.** If you are implementing the
   Textual TUI, do not lift hover/focus-ring/transition CSS from
   Surface C. The TUI is keyboard-only, single-frame, no animation.
7. **No file writes without an explicit implementation packet.**
   Surfaces A/B and the design-system reference are not contracts to
   ship anything. A separate, scoped implementation request is required
   per surface.

---

## Forbidden assumptions

- The cockpit owns the data it shows.
- The cockpit can write to any service.
- A bridge / adapter is an authority.
- A live stream exists in the static cockpit.
- The RTE runner has been executed by the cockpit.
- Proof bundles are generated client-side.
- Status chips are an open set extensible by callers.
- Color encodes decoration; removing it is safe; chips alone are enough.
  (False — chips *plus* color is the spec; both must survive in
  no-color rendering as bracketed literal tokens.)
- 120×40 is the only size; 100×32 and 80×24 are nice-to-have.
  (False — all three are required, in this order of preference.)

---

## Review gate

Before any implementation PR:

- [ ] Map every JSX/Textual component to a primitive in this folder.
- [ ] Confirm no new hex values, no new chip values, no new severity tokens.
- [ ] Confirm SRC appears nowhere in chrome.
- [ ] Confirm authorities are not collapsed.
- [ ] Confirm static surfaces still label themselves static.
- [ ] Confirm live surfaces label their write scope explicitly.
- [ ] Confirm three sizes still work (or reduce to a 80×24 BLOCKER panel).
- [ ] Run the validator from `cockpit/tokens.py::validate_rendered_text`.
