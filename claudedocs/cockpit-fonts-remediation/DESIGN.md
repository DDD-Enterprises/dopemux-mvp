# DMX-COCKPIT-FONTS — Design Spec (cockpit font build/patch remediation)

**Status:** Approved design → authoring Task Packets
**Date:** 2026-06-15
**Authoring branch:** `feat/cockpit-fonts-series` (worktree off `origin/main` @ `a2396a922`)
**Execution base:** `origin/main`
**Scope decision (operator):** Full audit remediation — every codex+grok REQUEST-CHANGES finding + 3 research refinements.
**Series id:** `dmx-cockpit-fonts` · **TP ids:** `DMX-COCKPIT-FONTS-101..106`

---

## 1. Context & problem

PR [#879](https://github.com/DDD-Enterprises/dopemux-mvp/pull/879) (**MERGED** 2026-06-14, squash) shipped a reproducible Dopemux cockpit font build+patch pipeline under
`docs/03-reference/Dopemux Cockpit TUI Design System/fonts/` (`build-dopemux-fonts.sh`, `patch-nerd-font.sh`, `private-build-plans.toml`) plus `@font-face` in `…/colors_and_type.css`. The live patch **was** run (`DopemuxTerm Nerd Font Mono` → 3519 PUA glyphs, all 7 documented codepoints). An external **codex + grok** audit returned **REQUEST-CHANGES**, but the PR merged with the findings unaddressed and a Codex-agent design-system normalization half-applied. This series remediates those findings on merged main — it is a **refinement/remediation** series, not a rescue.

### 1.1 Verified state (`origin/main` a2396a922)

| Finding | Status | Disposition |
|---|---|---|
| `patch-nerd-font.sh:62` `--mono` guard `family=="DopemuxTerm"` never fires (`family` derives from filename = plan key `IosevkaDopemuxTerm`) → **Term currently patched WITHOUT `--mono`** | live, **worse than reported** | TP-101 (rename fixes it) |
| Editor patched with bare default (no `--variable-width-glyphs`) → double-width icon advances | live | TP-102 |
| Patched family CamelCases to `DopemuxTerm Nerd Font Mono` (no space) ≠ docs `Dopemux Term Nerd Font` | live | TP-102 + TP-103 + TP-105 |
| TTF filenames `IosevkaDopemux*` (plan-key derived); build pre-clean glob `DopemuxTerm-*.ttf` misses → stale-file accumulation | live (latent bug) | TP-101 |
| `build-dopemux-fonts.sh`: no `mkdir -p OUT_DIR` (line 30 hard-errors); clobbers Iosevka's `private-build-plans.toml` (line 35, no backup); stale final manifest window on mid-build fail | live | TP-101 |
| No-binary-commit guarantee unenforced: `fonts/.gitignore` is dir-scoped; `build.md` says build into `$PWD/out` (not ignored); manifest dotfile not ignored anywhere | live | TP-101 |
| `colors_and_type.css` `@font-face` covers only Term Regular/Medium **upright** (no Italic, no Oblique, no Editor) | live | TP-103 |
| 6 case-collision pairs (ACCEPTANCE, PREIMPLEMENTATION, README, SKILL, assets/README, ui_kits/cockpit/README) — all 6 repo-wide collisions are in the design-system dir | live (the audit's real merge-blocker) | TP-104 |
| `README.md:291` still claims `IosevkaHueTerm-Regular.ttf` is "canonical brand mono"; `build.md:123` references legacy `IosevkaHue*` | live | TP-105 |
| `review-pack.md:54` references `fonts/BUILD.md` (real file: `build.md`) | live | TP-105 |

### 1.2 Stale / dropped (do NOT re-address)

- "Nerd glyphs missing" — **RESOLVED** (3519 PUA glyphs, 7/7 codepoints present after patch).
- "live patch NOT_RUN" — **RESOLVED** (ran 2026-06-14 on freed disk; 24 faces installed).
- "2 routing-gate `asyncio_mode` pytest reds" — **RESOLVED** (behind-main artifact; cleared on merge).
- D1 `cv__/ss__` ambiguity-reduction variant keys — **out of scope** (an *enhancement* needing manual Iosevka Customizer export, not an audit finding; YAGNI).

---

## 2. Adversarial challenge (PAL-substitute)

The PAL MCP was **down** this session; the PAL `challenge`/`codereview` role was performed by a **Plan subagent** doing a file-grounded adversarial review of the first-draft decomposition. Verdict: **RESTRUCTURE**. Findings that reshaped the plan:

- **C1 (critical):** Term mono is broken *today*; the plan-key rename (101) is the load-bearing fix, and the rename's blast radius straddles `patch-nerd-font.sh` (the `--mono` guard `:62` and pre-clean glob `:50`). → **101 owns the full rename end-to-end; 101 → 102**, and 102 becomes additive-only (new flags).
- **M1 (critical risk):** **drop `--name full`** — Medium faces export as `Dopemux Term Medium`, which `--name full` would parse as a *different family* per weight, fragmenting the family and breaking the `font-weight: 500 700` single-family range trick in `colors_and_type.css`. → use **explicit per-face `--name "<Family> Nerd Font"`** and **test the name tables**.
- **M5 (restructure):** 106 cannot be a CI-blocking TP — no committed CI builds fonts (binaries aren't committed; the toolchain is Iosevka+nerd-fonts+FontForge+Node). → heavyweight checks become **per-TP manual gate-notes**; 106 shrinks to toolchain-free asserts.
- **C2/H3/M6 (missing scope, folded in):** `.gitignore`/OUT_DIR don't prevent binary commits (→101); README still calls `IosevkaHueTerm` canonical (→105); the face matrix is **12 faces** (Regular/Medium × Upright/Italic/Oblique × 2 families), not "add Italic" (→103).

**Confirmed non-issues:** there is no 7th `fonts/` collision pair on origin/main (the working-tree `fonts/README.md` is a `feat/conport-optimal-series` artifact); the 6 cased pairs are **byte-identical** on origin/main, so 104 has no content-merge hazard there — only the `core.ignorecase=true` git mechanic matters.

---

## 3. Decomposition — 6 Task Packets

Executor assignment is deferred to the load plan (`executor_defaults`: impl=`claude-code-sonnet`, audit=`claude-code-opus`, per model-routing policy). `execution` is omitted from the packets (its `agent` enum lacks a Claude value). `pal_chain` is authored for **execution time** (PAL may be up then); RED-LANE packets carry the risky chain.

### TP-101 — Rename plan keys + harden build/patch scripts **(foundation, RED-LANE)**
**Files:** `private-build-plans.toml`, `build-dopemux-fonts.sh`, `patch-nerd-font.sh`, `fonts/.gitignore`, `build.md`, `readme.md`
**Scope:**
- Rename `IosevkaDopemux{Term,Editor}` → `Dopemux{Term,Editor}` across **all four call sites**: TOML `[buildPlans.…]` section headers; `build-dopemux-fonts.sh` `PLANS=(…)` (:27), dist path `dist/$plan/TTF` (:50-51), pre-clean glob (:43); `patch-nerd-font.sh` pre-clean glob (:50) **and the `--mono` family guard (:62) so it fires for Term**.
- Hardening: `mkdir -p "$OUT_DIR"` instead of hard-error (:30); back up + restore Iosevka's `private-build-plans.toml` around the `cp` (:35) instead of clobbering; close the stale-final-manifest window on mid-build failure (delete old TTFs only after a successful build, or `trap` cleanup).
- No-binary-commit: ignore the manifest dotfile `.dopemux-built-fonts.txt`, the patched output dir, and a canonical `OUT_DIR`; reconcile `build.md`/`readme.md` so the documented `OUT_DIR` sits inside an ignored path.

**Gates:** post-rename Term patched cmap is single-width (manual build+patch); no residual `IosevkaDopemux*` files; `git status` clean after a build (no TTF/manifest appears); `shellcheck` clean; bash-3.2 portable.
**Deps:** none. **Blocks:** 102, 103, 105, 106. **PAL:** risky chain.

### TP-102 — Patch flags: Editor proportional + stable family name **(RED-LANE)**
**Files:** `patch-nerd-font.sh`, `fonts/test-name-tables.sh` (or `tests/fonts/…`)
**Scope:**
- Editor faces → add `--variable-width-glyphs`; keep Term `--mono`.
- Family name: **explicit per-face `--name "<Family> Nerd Font"`** (family known from the post-rename filename stem). NOT `--name full`. Output contract pinned: Term family = `Dopemux Term Nerd Font` (single family across weights; weight via OS/2), Editor family = `Dopemux Editor Nerd Font`.
- Reconcile Editor patched family against the CSS `--font-editor` expectation (avoid a ` Propo` fork).

**Gate (name-table test, partly manual):** extract `name` IDs 1/2/4/6/16/17 for all patched faces; assert ID 16 (typographic family) **identical** across Regular+Medium of the same spacing family; assert Term advances single-width, Editor proportional; assert family strings equal the pinned contract.
**Deps:** 101. **Blocks:** 103, 105, 106. **PAL:** risky chain.

### TP-103 — `colors_and_type.css`: full `@font-face` matrix + family reconcile
**Files:** `colors_and_type.css`
**Scope:**
- Enumerate the full face matrix — Term + Editor × {Regular, Medium} × {Upright, Italic, Oblique}. **Decide and document** whether Oblique is web-exposed (default: map Italic→`font-style: italic`, Oblique→`oblique`, or explicitly omit Oblique with a one-line rationale).
- Confirm which faces the CSS serves (plain vs patched NF) and make `src` filenames consistent with TP-101's renamed output.
- Reconcile `--font-mono` / `--font-editor` tokens to TP-102's pinned family names (replace the stale no-space `DopemuxTerm Nerd Font Mono` at :81).

**Gate:** every `@font-face` `src` references a real built/patched file; every `var(--font-mono)`/`--font-editor` consumer resolves; family names equal the TP-102 contract.
**Deps:** 101, 102. **Blocks:** 106. **PAL:** `analyze→planner→codereview→precommit`.

### TP-104 — Resolve 6 design-system case-collisions **(foundation, RED-LANE)**
**Files:** the redundant cased member of each of the 6 pairs (via `git rm --cached`)
**Scope:**
- Decision gate per pair: canonical casing = the casing inbound links already use (default `README.md` UPPER per GitHub convention; verify each).
- Procedure: gate on byte-identity (`git diff <UPPER> <lower>` empty); `git rm --cached "<redundant>"` (NOT `git mv` — `core.ignorecase=true` no-ops); commit. If a future branch diverges, reconcile content into the keeper first.
- Run from a **clean `origin/main`** branch; verify via `git ls-tree -r origin/main` (not the working tree); expect exactly 6 pairs; ignore the `fonts/README.md` branch artifact.
- Fix any inbound references pointing at the removed casing.

**Gate:** `git ls-tree -r <branch> | tr A-Z a-z | sort | uniq -d` empty for the design-system dir; a fresh checkout on a case-insensitive FS materializes all expected files.
**Deps:** none. **Blocks:** 105, 106. **PAL:** risky chain (file removal is contract-sensitive).

### TP-105 — Purge legacy/stale doc refs + reconcile examples
**Files:** `review-pack.md`, `README.md` (post-104 keeper), `ACCEPTANCE.md` (post-104 keeper), `build.md`, `fonts/readme.md`, `preview/04b-brand-font.html`
**Scope:**
- `review-pack.md:54` `fonts/BUILD.md` → `build.md`.
- Purge `IosevkaHueTerm` "canonical brand mono" claims (README:291; build.md:123) and any `IosevkaHue*` / off-brand-font references.
- Reconcile doc-embedded `@font-face`/family/filename examples (README:162,262; ACCEPTANCE:74-75; preview/04b-brand-font.html:20; fonts/readme.md) to TP-101 filenames + TP-102 family names.

**Gate:** `rg` sweep finds zero `BUILD.md`, zero `IosevkaHue`, zero no-space `DopemuxTerm Nerd Font`, zero forbidden-font names (per `build.md`'s own forbidden list).
**Deps:** 101, 102, 104. **Blocks:** 106. **PAL:** minimum chain.

### TP-106 — Lightweight end-to-end verify + manual gate-note **(final packet)**
**Files:** `fonts/verify-remediation.sh`, `claudedocs/cockpit-fonts-remediation/VERIFICATION.md`, `proof/cockpit-fonts-106/**`
**Scope:**
- Toolchain-free, CI-able asserts: zero case-collisions; zero stale refs (the TP-105 sweep); `@font-face` matrix complete; every page loading `colors_and_type.css` resolves `--font-mono`/`--font-editor` to a declared face.
- Documented **manual** gate: re-run `build-dopemux-fonts.sh` + `patch-nerd-font.sh` with the full toolchain; inspect name tables (TP-102 gate), advance widths (Term single / Editor proportional), glyph coverage (7/7 codepoints), clean filenames (`DopemuxTerm-*.ttf`), `git status` clean.

**Deps:** 101, 102, 103, 104, 105. **PAL:** minimum chain. `final_packet=true`.

---

## 4. Dependency DAG & waves

```
101 ─┬─▶ 102 ─┬─▶ 103 ─┐
     ├────────┼─▶ 105 ─┤
     ├────────┴────────┤
     └─────────────────┤
104 ─┬─▶ 105 ──────────┤
     └─────────────────┴─▶ 106
103 ─────────────────────▶ 106
```

- **Edges (8):** 101→102, 101→103, 101→105, 101→106, 102→103, 102→105, 102→106, 103→106, 104→105, 104→106, 105→106. *(11 edges total; the ASCII is illustrative.)*
- **First wave (unblocked): 101, 104.**
- **After 101: 102.** **After 101+102: 103.** **After 101+102+104: 105.** **After all: 106.**

---

## 5. Open decisions & recommendations

1. **Editor family suffix** — resolved by the explicit-`--name` approach: set Editor family = `Dopemux Editor Nerd Font` (no auto ` Propo`), proportional advances still come from `--variable-width-glyphs`. TP-102 must verify the flag interaction empirically.
2. **Oblique web-exposure** (TP-103) — recommend mapping Italic→`italic`, Oblique→`oblique`; if the preview never uses oblique, omit with a documented rationale.
3. **Canonical casing** (TP-104) — keep the casing inbound links already use; default `README.md` UPPER. Pairs are byte-identical on origin/main so content is not at risk.

## 6. Validation strategy

- **Per-TP gates** carry the heavyweight, toolchain-dependent checks (name tables, advance widths, glyph coverage) as **manual** steps, because CI can't build fonts.
- **TP-106** carries only the toolchain-free, CI-able invariants.
- Each packet's `commit.verify` includes JSON validity + `python -m jsonschema` against `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` + `git diff --check`.

## 7. Risks

- **Medium-weight name parsing** (TP-102) — the primary technical risk; mitigated by explicit `--name` + name-table assertions, validated live in TP-106.
- **CSS serves plain vs patched faces** (TP-103) — must be pinned during execution; if the browser preview needs Nerd glyphs, the `@font-face` `src` must point at the patched NF files and the family must match TP-102.
- **Case-collision resolution on case-insensitive FS** (TP-104) — `git rm --cached` is the only safe mechanic; `git mv` silently no-ops.
- **PAL down now** — packets are authored for execution-time PAL; if still down at execution, executors fall back to `advisor()` + the per-TP gates.
