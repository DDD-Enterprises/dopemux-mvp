# Dopemux Cockpit Design System Review Pack

## Scope

- Package path: `docs/03-reference/Dopemux Cockpit TUI Design System/`
- Branch required by task packet: `codex/cockpit-design-system`
- Worktree required by task packet: `/Users/hue/code/dopemux-mvp-wt-cockpit-design-system`
- Package status: review package only. It does not generate final PM or Implementer screens.
- Runtime status: no runtime code modified.
- Staging status: not staged, not committed, not pushed.
- Claude Design handoff: blocked. `safe_for_claude_design: NO`. This package is not safe for Claude Design final-screen generation until browser visual review, runtime renderer validation, screenshot approval, proof JSON validation, and static line-fit evidence are package-contained or explicitly waived.

## Files Included

Observed package inventory after remediation, excluding `.DS_Store`: 53 files.

Inventory command:

```sh
find "docs/03-reference/Dopemux Cockpit TUI Design System" -maxdepth 4 -type f ! -name .DS_Store | sort | wc -l
```

Observed result:

```text
53
```

### Doctrine docs

- `ACCEPTANCE.md`
- `ARCHITECTURE_SAFETY_OVERLAY.md`
- `PM_IMPLEMENTER_COCKPIT_REDIRECTION.md`
- `PREIMPLEMENTATION.md`
- `README.md`
- `REVIEW_PACK.md`
- `SKILL.md`
- `UX_REFERENCE_RECONCILIATION.md`

### Font recipe docs

- `fonts/.gitignore`
- `fonts/BUILD.md`
- `fonts/README.md`
- `fonts/patch-nerd-font.sh`
- `fonts/private-build-plans.toml`

### Assets text docs

- `assets/README.md`
- `assets/brand_mark.txt`
- `assets/frame_chars.md`
- `assets/glyphs.md`

### Preview HTML/CSS

- `preview/01-brand-palette.html`
- `preview/02-surfaces-text.html`
- `preview/03-status-chips.html`
- `preview/04-type-specimen.html`
- `preview/04b-brand-font.html`
- `preview/05-type-roles.html`
- `preview/06-frame-grid-120.html`
- `preview/07-adaptation.html`
- `preview/08-row-anatomy.html`
- `preview/09-authority-bridge.html`
- `preview/10-mode-bar.html`
- `preview/11-rails.html`
- `preview/12-render-modes.html`
- `preview/13-error-panel.html`
- `preview/14-status-language.html`
- `preview/15-glyphs.html`
- `preview/16-frame-chars.html`
- `preview/17-spacing.html`
- `preview/18-inspector.html`
- `preview/19-voice.html`
- `preview/20-cockpit-composition.html`
- `preview/21-ascii-fallback.html`
- `preview/_shared.css`

### Surfaces

- `surfaces/A1-services-repo-truth-workload-120x40.html`
- `surfaces/A2-services-repo-truth-workload-100x32.html`
- `surfaces/A3-services-repo-truth-workload-80x24.html`
- `surfaces/B-textual-cockpit-direction.html`
- `surfaces/C-web-dashboard-direction.html`
- `surfaces/_surface.css`

### UI kit

- `ui_kits/cockpit/Cockpit.jsx`
- `ui_kits/cockpit/Primitives.jsx`
- `ui_kits/cockpit/README.md`
- `ui_kits/cockpit/cockpit.css`
- `ui_kits/cockpit/index.html`
- `ui_kits/cockpit/seed.js`

## Exclusions

- `screenshots/*.png`: removed from package-contained inventory.
- `uploads/*.png`: removed from package-contained inventory.
- Font binaries: absent from package inventory.
- Runtime source paths (`src/**`, `services/**`, `scripts/**`): not modified.
- `AGENTS.md`: dirty before this pass and intentionally not modified by this remediation.

## Remediation 002 Summary

- Remediation 002 patches the GPT-5.5 Pro NOT_READY findings against the package files only.
- Top-level cockpit modes are intended to remain exactly `PM`, `Implementer`, `Overview`, `Services`, `Events`.
- repo-truth-extractor is intended to appear as a Services child/workload surface only.
- Local gate reported no positive-content hits for old sixth-mode workload labels.
- Local gate reported no source-label misuse hits.
- Major positive panes and examples were patched to declare `domain`, `authority`, `role`, and `next_action`.
- Allowed pane role values are constrained to `canonical`, `derived`, `mirrored`, `proxied`, `authoring`, and `chrome`.
- Static mocks and reference cards were normalized toward the allowed role enum and ASCII direction markers.
- `dopecon-bridge` remains adapter/proxy/event transport only, never canonical PM/workflow/decision/progress authority.
- PM authority remains split across Leantime, task-orchestrator, ConPort, and dope-memory mirror receipts.
- UI kit status is downgraded to CDN-dependent visual reference only; it is not self-contained runtime proof.
- Unicode arrows and Unicode ellipsis remain forbidden; ASCII `->` is allowed when directionality is needed.

## Remediation 003 Summary

- Remediation 003 is limited to filename and reference cleanup after remediation 002.
- A1/A2/A3 static snapshot filenames were renamed from stale run-history wording to Services repo-truth workload wording.
- Package references were updated to the renamed Services workload files.
- No runtime code, final screens, screenshots, uploads, proof JSON, font binaries, images, archives, source paths, services paths, scripts paths, Opus pack files, or `AGENTS.md` were modified by this remediation.
- `safe_for_claude_design` remains `NO`.
- Browser visual review, runtime renderer validation, proof JSON validation, screenshot approval, and static line-fit proof remain `UNKNOWN`.

## Glyph Stylization 001 Summary

- Glyph Stylization 001 is limited to visual identity and glyph-contract documentation.
- Canonical stylized wordmark is `DØPΞM∪X`; plain fallback wordmark is `DOPEMUX`.
- Compact seal is `◆DØPΞM∪X◆`.
- Rejected artifact `ᗪØƤΞM∪╳` is non-canonical and must not be used as the wordmark.
- The stylized wordmark is limited to chrome, title bars, splash / brand previews, and non-semantic headers.
- Glyphs remain visual cues only and do not define authority, provenance, workflow legality, validation result, source truth, or state.
- The wordmark and rich glyphs do not replace `domain`, `authority`, `role`, `next_action`, `SRC`, `status`, or `result`.
- No runtime code, final screens, screenshots, uploads, proof JSON, font binaries, images, archives, source paths, services paths, scripts paths, Opus pack files, or `AGENTS.md` were modified by this pass.
- `safe_for_claude_design` remains `NO`.
- Browser visual review, runtime renderer validation, proof JSON validation, screenshot approval, and static line-fit proof remain `UNKNOWN`.

## CSS Class Cleanup Summary

- Stale short-form tab CSS selector names in the Services web-dashboard reference were renamed to `.repo-truth-workload-tabs`.
- Matching HTML class references were updated in the same file.
- This cleanup changes class names only. It does not change pane authority text, mode lists, SRC values, glyph contract, readiness recommendation, or visual semantics.
- `safe_for_claude_design` remains `NO`.

## Repair Package 003 Current Verification Summary

- Current filesystem verification found the run-history, stale `rte-*`, SRC misuse, active command-copy, glyph semantic-field, Unicode arrow / ellipsis, stale CSS selector, binary, screenshot, upload, proof, and archive findings absent from positive package content.
- Current filesystem verification found pane authority wording still present in rendered or seed content where dopemux was described as both the authority and the control-surface function in one authority field. Those declarations were patched to `authority: dopemux`; prose still describes dopemux's function as the operator control surface and not a data authority.
- Current filesystem verification found one prose hit where agent authority was described through implication wording. It was patched to explicit `declare` wording.
- Final Semantic Patch 005 blockers were real authoritative-zip package blockers before the 005 patch, not stale upload-only findings. Findings not reproduced by current filesystem gates after the 005 patch are classified as remediated by current package state.
- No runtime code, final PM / Implementer screens, screenshots, uploads, proof JSON, font binaries, images, archives, source paths, services paths, scripts paths, Opus pack files, or `AGENTS.md` were modified by this repair package pass.
- `safe_for_claude_design` remains `NO`.
- Browser visual review, runtime renderer validation, proof JSON validation, screenshot approval, and static line-fit proof remain `UNKNOWN`.

## Final Semantic Patch 005 Summary

- Final Semantic Patch 005 is limited to GPT-5.5 Pro package blockers in rendered review content.
- GPT-5.5 Pro found these blockers in the authoritative current package zip; this was not classified as an upload-artifact-only problem.
- A2 compact surface command copy was changed from active create wording to inspect-only wording.
- The canonical frame-grid preview now declares all four chrome fields in the shortcut rail example: `domain`, `authority`, `role`, and `next_action`.
- The canonical frame-grid preview no longer uses `R T E child` shorthand; it uses repo-truth child wording while keeping repo-truth-extractor as a Services child/workload surface only.
- No runtime code, final screens, screenshots, uploads, proof JSON, font binaries, images, archives outside the requested audit artifacts, source paths, services paths, scripts paths, Opus pack files, or `AGENTS.md` were modified by this semantic patch.
- `safe_for_claude_design` remains `NO`.
- Browser visual review, runtime renderer validation, proof JSON validation, screenshot approval, and static line-fit proof remain `UNKNOWN`.

## Verification Snapshot

Run these commands from `/Users/hue/code/dopemux-mvp-wt-cockpit-design-system` before staging:

```sh
pwd
git rev-parse --show-toplevel
git branch --show-current
test -f .dopetaskroot
test -f .dopetask-pin
git status --short --untracked-files=all
rg -n "DØPΞM∪X|◆DØPΞM∪X◆|DOPEMUX" "docs/03-reference/Dopemux Cockpit TUI Design System"
rg -n "DØPΞMUX" "docs/03-reference/Dopemux Cockpit TUI Design System" || true
rg -n "ᗪ" "docs/03-reference/Dopemux Cockpit TUI Design System" || true
rg -n "$(printf '\\u2192|\\u21d2|\\u279c|\\u2026')" "docs/03-reference/Dopemux Cockpit TUI Design System" || true
rg -n "Run[ ]History|6\\*Run[ ]History|surface.*r[t]e|A[123]-r[t]e-runs|r[t]e-runs" "docs/03-reference/Dopemux Cockpit TUI Design System" || true
rg -n "SRC=r[t]e|src=r[t]e|SRC=repo-truth-ext[r]|SRC=UNKNOW[N]|src: \"UNKNOW[N]\"|src: 'UNKNOW[N]'" "docs/03-reference/Dopemux Cockpit TUI Design System" || true
rg -n "<span class=\"c-dim\">n</span> <span class=\"c-cyan-b\">new</span>|\bn[[:space:]]+new\b|new run|doctor|follow tail|pause|export|compare|proof generation|execute|execution" "docs/03-reference/Dopemux Cockpit TUI Design System/surfaces" "docs/03-reference/Dopemux Cockpit TUI Design System/preview" "docs/03-reference/Dopemux Cockpit TUI Design System/ui_kits" || true
rg -n "\bnew\b" "docs/03-reference/Dopemux Cockpit TUI Design System/surfaces" "docs/03-reference/Dopemux Cockpit TUI Design System/preview" "docs/03-reference/Dopemux Cockpit TUI Design System/ui_kits" || true
rg -n "\\.r[t]e-tabs|class=\"r[t]e-tabs\"" "docs/03-reference/Dopemux Cockpit TUI Design System" || true
find "docs/03-reference/Dopemux Cockpit TUI Design System" -type f \( -name '*.ttf' -o -name '*.otf' -o -name '*.woff' -o -name '*.woff2' -o -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.gif' -o -name '*.zip' \) -print
rg -n "domain:" "docs/03-reference/Dopemux Cockpit TUI Design System" || true
rg -n "authority:" "docs/03-reference/Dopemux Cockpit TUI Design System" || true
rg -n "role:" "docs/03-reference/Dopemux Cockpit TUI Design System" || true
rg -n "next_action:" "docs/03-reference/Dopemux Cockpit TUI Design System" || true
```

Expected classification:

- Guard commands: PASS only if cwd, git root, branch, `.dopetaskroot`, and `.dopetask-pin` match.
- `DØPΞM∪X`: allowed in chrome / brand docs / previews only.
- `◆DØPΞM∪X◆`: allowed as compact seal in brand docs / previews only.
- `DOPEMUX`: allowed as the plain fallback wordmark.
- `DØPΞMUX`: stale drift; expected empty outside this verification command.
- `ᗪ`: allowed only where explicitly documented as rejected / non-canonical or in this verification command.
- Semantic-field glyph grep: expected empty.
- Font binary check: PASS when empty.
- Drift grep: PASS when empty for positive package content; non-rendered recipe references must be classified separately.
- Pane wording grep from the task packet: PASS when empty for the blocked declaration / implication phrases and stale dopemux chrome-authority wording.
- Active command-copy grep: PASS when empty in rendered surfaces, previews, and UI kit seed hints. It must catch rendered `n new`, plain `n new`, and active run/execute/proof controls.
- Broad `new` grep: evidence only; classify code constructors such as `new Set(...)` and explicit negated prose separately from rendered create commands.
- CSS selector grep from the task packet: PASS when empty for stale short-form tab selector names and matching HTML class attributes.
- Pane declaration grep: evidence only; reviewer must inspect major panes for complete four-field blocks.
- Screenshot/upload/proof finds: expected empty unless operator-approved evidence is later added.

## Known UNKNOWNs

- Browser visual review: UNKNOWN.
- Runtime renderer validation: UNKNOWN.
- Screenshot approval: UNKNOWN.
- Proof JSON validation: UNKNOWN.
- Static line-fit and row-count proof: UNKNOWN unless package-contained logs are added.
- CDN/self-contained status: known not self-contained for `ui_kits/cockpit/index.html`.
- Unrelated dirty files: `AGENTS.md` is dirty before this pass; unrelated audit reports/task packets may also be untracked outside this package.

## Staging Safety

Allowed for this remediation scope:

- `docs/03-reference/Dopemux Cockpit TUI Design System/**/*.md`
- `docs/03-reference/Dopemux Cockpit TUI Design System/**/*.html`
- `docs/03-reference/Dopemux Cockpit TUI Design System/**/*.css`
- `docs/03-reference/Dopemux Cockpit TUI Design System/**/*.jsx`
- `docs/03-reference/Dopemux Cockpit TUI Design System/**/*.js`

Never stage for this remediation without explicit operator approval:

- `AGENTS.md`
- `docs/03-reference/Dopemux Cockpit TUI Design System/uploads/*.png`
- `docs/03-reference/Dopemux Cockpit TUI Design System/screenshots/*.png`
- font binaries
- runtime code under `src/**`, `services/**`, or `scripts/**`
- generated archives
- proof files not generated and validated by this package

## GPT-5.5 Pro Re-Audit Prompt

Re-audit the Dopemux Cockpit TUI Design System review package at `docs/03-reference/Dopemux Cockpit TUI Design System/` for architecture safety and package truthfulness. Confirm or reject:

- Top-level cockpit modes remain exactly `PM`, `Implementer`, `Overview`, `Services`, `Events`.
- repo-truth-extractor remains only a Services child/workload surface and is not a sixth top-level cockpit mode.
- Every major pane declares `domain`, `authority`, `role`, and `next_action`.
- Pane role values are limited to `canonical`, `derived`, `mirrored`, `proxied`, `authoring`, and `chrome`.
- Positive content does not render unknown as an `SRC` value; `UNKNOWN` appears only as state text.
- dopecon-bridge is adapter/proxy/event transport only and never canonical PM/workflow/decision/progress authority.
- PM authority remains split across Leantime, task-orchestrator, ConPort, and dope-memory mirror receipts.
- Staging safety excludes `AGENTS.md`, uploads, screenshots, font binaries, runtime code, and unsupported proof artifacts.
- Browser visual review, runtime validation, screenshot approval, and proof JSON validation remain `UNKNOWN` unless package-contained evidence is added.
- Brand and glyph updates remain visual only: `DØPΞM∪X` and rich glyphs are not semantic substitutes for `domain`, `authority`, `role`, `next_action`, `SRC`, `status`, or `result`.
- CSS class cleanup remains naming-only and does not change visual semantics or authority semantics.

Report any drift as `BLOCKER`, `PATCH_REQUIRED`, or `UNKNOWN`; do not promote Claude Design readiness unless all blockers and UNKNOWN evidence gaps are resolved or explicitly waived.

## Final Readiness Statement

READY_WITH_PATCHES_FOR_5_5_PRO_AUDIT

safe_for_claude_design: NO

This recommendation is limited to a re-audit pass after remediation 003 filename/reference cleanup, Glyph Stylization 001 brand/glyph contract updates, CSS Class Cleanup naming-only updates, Repair Package 003 current-filesystem verification / pane wording cleanup, and Final Semantic Patch 005 rendered-content cleanup. It does not assert Claude Design readiness, runtime renderer validation, proof JSON validity, browser visual approval, screenshot approval, or static line-fit proof.
