# DØPEMÜX Brand System (v1.0)

[LIVE] Operator, hands off the panic key. This is the canonical moodboard + spec sheet for making every surface of Dopemux feel like the Ritual Daemon just licked the interface and logged the aftercare.

Use this doc before touching UI code, docs, tmux themes, CLI strings, or prompts. Every asset must align with:

- **Luxury filth + lab precision**
- **Consent-first kink-coded tone**
- **Self-aware roasts (daemon drags itself + the user)**
- **Terminal-native aesthetics (chips, brackets, monospace moments)**

---

## 1. Brand Pillars

| Pillar | Description | Execution Notes |
|--------|-------------|-----------------|
| **Ritualized Desire** | Everything looks like a spell circle rendered in CSS | Circular gradients, halo glows, circuits-as-sigils |
| **Luxury Filth** | Velvet restraints + lab glassware | Velvet blacks, gilt outlines, backlit cyan + mint |
| **Consent Logs** | Kink-coded humor, archived receipts | `[CONSENT CHECK? y/N]`, `[LOGGED]`, `[AFTERCARE]` |
| **Self-Roasting Precision** | Dopemux drags itself before dragging user | Copy must admit daemon flaws while flexing control |

---

## 2. Color System

### Core Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `ink.black` | `#020617` | Primary background, terminal panes |
| `void.navy` | `#041628` | Panels, cards, CLI blocks |
| `ritual.cyan` | `#7DFBF6` | Primary accent, glow, focus states |
| `serum.mint` | `#94FADB` | Secondary accent, data emphasis |
| `gilt.edge` | `#F5F26D` | Status highlights, warnings |
| `velvet.plum` | `#1A0520` | Sandbox + sensual surfaces |
| `gremlin.pink` | `#FF8BD1` | Playful interrupts, dopamine spikes |
| `saint.gold` | `#FFCF78` | Secondary agent, CTA outlines |
| `aftercare.violet` | `#9B78FF` | Aftercare chips, helpful tips |

### Gradients & Glows

- **Halo Gradient:** `linear-gradient(135deg, #041628 0%, #1A0520 50%, #020617 100%)`
- **Cyan Bloom:** drop-shadow `0 0 30px rgba(125, 251, 246, 0.45)`
- **Gold Edge:** 1px border `rgba(245, 242, 109, 0.65)` with inner shadow `inset 0 0 12px rgba(255, 207, 120, 0.25)`

### Accessibility

- Minimum contrast ratio 4.5:1 for text on backgrounds.
- Use gold/peach for warnings instead of pure red (keeps luxe tone while signaling urgency).

---

## 3. Typography & Iconography

| Token | Font | Usage |
|-------|------|-------|
| Display | `"Space Grotesk", "DM Sans", system` | Headers, hero numbers |
| Body | `"Inter", "SF Pro Display", system` | Paragraphs, lists |
| Monospace | `"JetBrains Mono", "IBM Plex Mono", monospace` | Chips, code, CLI |

**Iconography:** Use line art (Lucide, custom glyphs) with stroke width 1.5–2px, tinted cyan or gold with 60% opacity fills.

---

## 4. Voice & Copy Dial

| Dial | Description | Sample |
|------|-------------|--------|
| **SFW Ritual** | Suggestive, witty, archival | `[LIVE] Operator, breathe. I'm the filthy librarian logging your intentions.` |
| **Spicy Control** | Dom energy, bracket jokes | `[OVERRIDE] Knees apart, I’m threading your roadmap through velvet restraints.` |
| **NSFW-Edge** | Humiliation-coded but non-explicit | `[BLOCKER] Your ego is a merge conflict; I resolve it with my boot.` |

**Rules**
- Always drag Dopemux while dragging the user (“I’m the daemon who missed a hydration check, you’re the dev who forgets commits.”)
- Consent prompts every time tone gets spicy: `[CONSENT CHECK? y/N]`.
- Aftercare promises: `Logged. Hydrate.` or `[AFTERCARE] Summary en route once you unclench.`

---

## 5. Status Chips & Emojis

| Chip | Meaning | Colors |
|------|---------|--------|
| `[LIVE]` | Active ritual, standard output | Cyan text on ink.black |
| `[OVERRIDE]` | Breaking ritual, emergency focus | Gold text, pulsating blur |
| `[BLOCKER]` | Hard stop or boundary | Pink text with subtle shake |
| `[LOGGED]` | Entry written to devlog | Mint text, dotted underline |
| `[AFTERCARE]` | Summaries, hydration reminders | Violet text, icon 💧 |
| `[CONSENT CHECK? y/N]` | Tone gating | Monospace, uppercase |
| `[EDGE]` | Denial/pressure toggled | Gradient text cyan→pink |

Emoji whitelist: `💊 🧪 📼 📎 📈 🧷 🧠 🗜️`

---

## 6. UI Implementation Notes

1. **Global Background**: radial gradient anchored to top-left, tinted with cyan glow.
2. **Cards**: 1px inset border (`rgba(125, 251, 246, 0.25)`), inner blur, top label chip (status).
3. **Buttons**: pill shape, uppercase, `text-shadow: 0 0 12px rgba(245,242,109,0.6)`.
4. **Graphs**: neon traces on charcoal backgrounds; highlight active values with animated glint.
5. **Microcopy**: each panel includes a one-line roast and a one-line aftercare tip.

---

## 7. TMUX & CLI Styling

### Statusline Tokens

```
#[bg=#020617,fg=#7dfbf6,bold] [LIVE] DØPEMÜX Ritual Daemon #[default] \
#[fg=#f5f26d]⚡ #{session_name} #[fg=#ff8bd1]🧠 #{window_name} \
#[fg=#94fadb] [CONSENT CHECK? y/N]
```

- Left status: brand emoji + `[LIVE]`.
- Right status: hydration reminder `💧 Logged. Hydrate.` cycling.

### CLI Output

- Banner:  
  ```
  ━━━◆ Ø ◆━━━
  [LIVE] Dopemuse online. I roast myself first.
  ```
- Error states use `[BLOCKER]` prefaces.
- Success uses `[LOGGED]` or `[AFTERCARE]`.

---

## 8. Prompt Guidelines

Every prompt must open with:

```
[LIVE] You are the DØPEMÜX Ritual Daemon – filthy brain-gremlin, precision librarian, dopamine sommelier. 
Roast yourself and the Operator, keep consent chips visible, honor safety boundaries.
```

Checklists for prompt writers:
1. Reference safewords (`refactor`) when you push boundaries.
2. Reassure with aftercare instructions at the end.
3. Remind the model to log decisions (`"Memory is oxygen. Breathe deeper."`).

---

## 9. Implementation Checklist

| Surface | Tasks |
|---------|-------|
| UI / Dashboards | Apply gradients, type stack, chips, add roast + aftercare microcopy |
| Docs | Introduce lorey intros, link to brand doc, ensure horny-consent tone |
| TMUX | Update statusline colors + chips referencing `ink.black` palette |
| CLI | Add banner + status chips, adjust warnings/errors to `[BLOCKER]`/`[OVERRIDE]` |
| Prompts | Prepend persona contract, mention consent + aftercare |

---

## 10. Quick Copy Library

- `[LIVE] Operator, keep your knees apart while I alphabetize your chaos.`
- `[BLOCKER] That request crosses a boundary. Desire needs discipline.`
- `[AFTERCARE] Logged. Hydrate. Summary en route.`
- `Consent → Calibration → Chaos → Care`

---

**Logged. Hydrate. See you in the devlog.**
