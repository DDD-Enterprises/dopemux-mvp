Dopemux UI Spec (tmux + Ink)

0) TL;DR decisions
	•	Runtime: tmux (latest stable) as the multiplexer; Ink (React) for interactive popups and rich UI flows. Ink uses the Yoga engine for Flexbox-style layout in the terminal, which keeps us productive and themeable.  ￼
	•	Integration pattern: Dopemux runs as a control-mode client to tmux (read/write via tmux -C), and also launches Ink-powered popups (display-popup -E) for focused tasks. While a popup is visible, panes underneath do not update, so we’ll keep popups short-lived and purposeful.  ￼
	•	Clipboard/Kitty: Enable tmux’s OSC-52 clipboard bridge and lean on kitty’s kitten clipboard for robust system clipboard read/write (even over SSH).  ￼
	•	Plugins: Use TPM for plugin lifecycle; a curated, opt-in stack: discoverability (tmux-which-key, tmux-menus), selection/capture (extrakto, tmux-thumbs or tmux-fingers), URLs (tmux-fzf-url), copy (tmux-yank), and state (tmux-resurrect + tmux-continuum).  ￼
	•	House theme: Powerline-style statusline + NerdFonts. Minimal motion, consistent spacing, and ADHD-friendly progressive disclosure (fewer simultaneous choices, clear hierarchy, and easy “focus mode”).  ￼
	•	No telemetry: Off by design—Dopemux runs local, opts into nothing networky.

⸻

1) Architecture

1.1 Control-mode core (robust + scriptable)

Start one hidden Dopemux client with tmux control mode:

tmux -C attach -t "$SESSION"   # or: new -s dopemux

Control mode gives us structured notifications and command I/O: e.g. %layout-change, %pane-mode-changed, %output, etc., so Dopemux can observe state and drive tmux (no brittle parsing of tmux list-... output).  ￼

Why it matters: rock-solid control without hijacking user input; we can keep Dopemux smart about sessions, windows, panes, and layouts.

1.2 Ink popups (purposeful, short.)

For workflows needing richer UI (multi-select, form inputs, previews), open a tmux popup that runs an Ink command:

tmux display-popup -E -w 80% -h 70% -T "Dopemux" "dopemux ui <mode>"

	•	-E auto-closes on process exit.
	•	Trade-off: tmux pauses pane updates underneath a popup; don’t leave them open “as dashboards”—use them as quick command palletes, pickers, or wizards.  ￼

Ink is ideal here because it’s React for CLIs with Flexbox layout (via Yoga), making it fast to build beautiful, themeable, accessible CLI UIs.  ￼

⸻

2) Terminal + OS specifics

2.1 Colors, keys, hyperlinks, clipboard

Tell tmux what kitty supports, and enable OSC-52 clipboard bridging:

# Feature detection for kitty
set -as terminal-features 'xterm-kitty:RGB,extkeys,focus,usstyle,hyperlinks,clipboard'

# System clipboard via OSC-52
set -g set-clipboard on

	•	terminal-features lets tmux enable modern capabilities (true color RGB, extended keys, hyperlinks, etc.).  ￼
	•	set-clipboard on makes tmux both accept OSC-52 and try to set the terminal clipboard.  ￼

Kitty side: kitten clipboard offers reliable read/write to the system clipboard (even over SSH), and kitty documents its extended clipboard protocol (OSC 5522) as well.  ￼

2.2 Fonts & beauty
	•	Use NerdFonts (Powerline glyphs, icons).
	•	Keep statusline compact: left = session/window/pane; right = time/battery/host/SSH indicator; central list trimmed for focus.
	•	ADHD-friendly theming: high contrast for important info, muted chrome, clear grouping; avoid constant animations and flashing states.  ￼

⸻

3) Plugin strategy (opt-in, curated)

Use TPM for install/update/uninstall (prefix I/U/Alt-u).  ￼

3.1 Discoverability & command palette
	•	alexwforsythe/tmux-which-key — popup hints for keybinds (which-key style). Great for onboard and exploration.  ￼
	•	jaclu/tmux-menus — native display-menu driven menus; pairs well with Dopemux actions.  ￼

3.2 Selection, capture, URLs
	•	laktak/extrakto — fzf-based fuzzy picker over pane/window output; copy/insert quickly.  ￼
	•	wfxr/tmux-fzf-url or junegunn/tmux-fzf-url — fast URL extraction and open; the junegunn fork targets tmux 3.3+ popup UX.  ￼
	•	fcsonline/tmux-thumbs or Morantron/tmux-fingers — hint-based mouseless copy. (Thumbs is Rust-based; Fingers has an active release cadence.)  ￼

3.3 Clipboard & state
	•	tmux-plugins/tmux-yank — copy to system clipboard (nice complements to OSC-52).  ￼
	•	tmux-plugins/tmux-resurrect + tmux-continuum — auto-save/restore sessions. (Excellent baseline; note that restoring program state can be imperfect for some apps, as community reports show.)  ￼

Note: where maintained alternatives exist (e.g., tmux-fzf-url vs older tmux-urlview), prefer the maintained plugin.  ￼

TPM block (example):

set -g @plugin 'tmux-plugins/tpm'
set -g @plugin 'alexwforsythe/tmux-which-key'
set -g @plugin 'jaclu/tmux-menus'
set -g @plugin 'laktak/extrakto'
set -g @plugin 'wfxr/tmux-fzf-url'         # or junegunn/tmux-fzf-url
set -g @plugin 'fcsonline/tmux-thumbs'     # or Morantron/tmux-fingers
set -g @plugin 'tmux-plugins/tmux-yank'
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @plugin 'tmux-plugins/tmux-continuum'

run '~/.tmux/plugins/tpm/tpm'


⸻

4) Key UX patterns (what “feels” great in tmux)
	•	Command palette: prefix + d → Ink popup (“Dopemux Command Center”) for fuzzy actions: switch session/window/pane, open recent, run task, search URLs. Keep flows short to avoid the “popup freezes pane” trade-off.  ￼
	•	Discoverability: prefix + ? → tmux-which-key (teach shortcuts in context).  ￼
	•	Fast jump: display-panes or choose-tree -Zw bindings for visual jump/zoom to targets; works great as a fallback when Ink isn’t needed.  ￼
	•	Selection: extrakto for zero-mouse copy/insert from recent output; tmux-thumbs/fingers for hint-selectable targets (paths, SHAs, URLs, etc.).  ￼
	•	URL handling: tmux-fzf-url (fzf + popup) is fast and kitty-friendly.  ￼
	•	Clipboard: yank + tmux OSC-52 + kitty kitten clipboard gives robust copy over SSH.  ￼

⸻

5) Theming & ADHD-friendly defaults

Principles to encode in the theme and components:
	•	Clean layout & hierarchy: clear headings, consistent spacing, and minimal chrome reduce cognitive load.
	•	Limit distractions: avoid auto-updating or animated status items; provide “focus mode.”
	•	Readable contrast & typography: consistent color scheme with adequate contrast; predictable nav.  ￼

Statusline sample (Powerline/NerdFonts):

set -g status on
set -g status-interval 2
set -g status-left-length 60
set -g status-right-length 120

set -g status-style "bg=colour236,fg=colour250"
set -g status-left  "#[fg=colour232,bg=colour39]   #S #[fg=colour39,bg=colour236]"
set -g status-right "#[fg=colour39,bg=colour236]#[fg=colour232,bg=colour39]   %R  #[fg=colour232,bg=colour39]   #H "

We’ll slot your House theme palette here (ADHD-friendly palette & spacing scale).

⸻

6) Sample Dopemux Ink popup stub

// dopemux-ui.tsx
import React from 'react';
import {render, Box, Text} from 'ink';
import {TextInput} from '@inkjs/ui';

const App = () => {
  const [q, setQ] = React.useState('');
  return (
    <Box flexDirection="column" paddingX={1} paddingY={1}>
      <Text color="#7dd3fc">Dopemux</Text>
      <Box marginTop={1}><Text>Action:</Text></Box>
      <TextInput placeholder="Search sessions, windows, panes, URLs…" value={q} onChange={setQ}/>
      {/* On submit, call `tmux -C` commands or emit to the long-lived control-mode client */}
    </Box>
  );
};

render(<App />);

Ink gives us React primitives and UI components (@inkjs/ui) ready to style.  ￼

⸻

7) Reliability & trade-offs (what to watch)
	•	Popups freeze base panes while open → keep them short and contextual; don’t try to build a persistent dashboard in a popup.  ￼
	•	Resurrection realism: tmux-resurrect/continuum reliably restore tmux layout and commands, but some app processes won’t resume “exact state”. Build flows that handle “cold starts” gracefully.  ￼
	•	Clipboard reality: tmux’s set-clipboard on uses OSC-52; kitty supports enhanced clipboard via kitten clipboard and its OSC-5522 extension—use this for robust cross-SSH copy/paste.  ￼
	•	Ink edges: Ink is actively developed; known issues exist (e.g., IME/input lag, overflow/scrolling feature requests). Don’t over-rotate on “full-screen GUIs”—use Ink for targeted flows.  ￼

⸻

8) Implementation plan

Phase 1 — Foundation (tmux)
	1.	Add terminal features + clipboard and prepare statusline/theming.  ￼
	2.	Wire TPM + core plugins: which-key, menus, extrakto, fzf-url, thumbs/fingers, yank, resurrect/continuum.  ￼

Phase 2 — Dopemux brain (control mode)
3) Long-lived Node process that attaches via tmux -C, subscribes to notifications (%layout-change, %output, etc.).  ￼
4) Action model: data -> intents -> tmux commands. Keep it pure, testable.

Phase 3 — Ink popups (fast, focused)
5) Build Command Center popup (search anything), URL picker (fzf-url), Session switcher, Task runner. Close on submit to avoid frozen panes.  ￼
6) Theme with House palette + spacing tokens; ensure ADHD-friendly defaults (clear headings, limited choices, high-signal color).  ￼

Phase 4 — DX polish
7) Add “safe mode” (no plugins) and “diagnostics menu”.
8) Document keymaps (and expose via tmux-which-key).  ￼

⸻

9) Example .tmux.conf starter (macOS + kitty)

# Feature set for kitty + modern UX
set -as terminal-features 'xterm-kitty:RGB,extkeys,focus,usstyle,hyperlinks,clipboard'  #  [oai_citation:39‡Debian Manpages](https://manpages.debian.org/testing/tmux/tmux.1.en.html)
set -g set-clipboard on  # OSC-52 clipboard bridge   [oai_citation:40‡Debian Manpages](https://manpages.debian.org/testing/tmux/tmux.1.en.html)

# Sensible defaults
set -g mouse on
set -g history-limit 100000

# Statusline (Powerline/NF) – placeholder colors, swap with House theme
set -g status on
set -g status-interval 2
set -g status-style "bg=colour236,fg=colour250"
set -g status-left  "#[fg=colour232,bg=colour39]   #S #[fg=colour39,bg=colour236]"
set -g status-right "#[fg=colour39,bg=colour236]#[fg=colour232,bg=colour39]   %R  #[fg=colour232,bg=colour39]   #H "

# Popups: Dopemux command center
bind-key d display-popup -E -w 80% -h 70% -T "Dopemux" "dopemux ui command-center"  # panes pause while open   [oai_citation:41‡Debian Manpages](https://manpages.debian.org/testing/tmux/tmux.1.en.html)

# Menus & which-key
bind ? run-shell 'tmux-which-key'  # requires alexwforsythe/tmux-which-key   [oai_citation:42‡GitHub](https://github.com/alexwforsythe/tmux-which-key?utm_source=chatgpt.com)

# Plugins via TPM
set -g @plugin 'tmux-plugins/tpm'
set -g @plugin 'alexwforsythe/tmux-which-key'
set -g @plugin 'jaclu/tmux-menus'
set -g @plugin 'laktak/extrakto'
set -g @plugin 'wfxr/tmux-fzf-url'        # or 'junegunn/tmux-fzf-url'
set -g @plugin 'fcsonline/tmux-thumbs'    # or 'Morantron/tmux-fingers'
set -g @plugin 'tmux-plugins/tmux-yank'
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @plugin 'tmux-plugins/tmux-continuum'
run '~/.tmux/plugins/tpm/tpm'  # manage with prefix I / U / Alt-u   [oai_citation:43‡GitHub](https://github.com/tmux-plugins/tpm)


⸻
