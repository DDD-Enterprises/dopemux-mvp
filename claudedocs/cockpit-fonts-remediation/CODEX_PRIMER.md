# DMX-COCKPIT-FONTS — Codex Execution Primer

> **Read order:** this primer → repo `AGENTS.md` → the specific packet JSON → the actual files on `origin/main`. Runtime code outranks every doc, including this one.

You are executing a **6-packet remediation series** for the Dopemux cockpit font build/patch pipeline (follow-on to **merged PR #879**). It is already loaded in task-orchestrator. Your job: take one unblocked packet at a time, make the **smallest correct change** that satisfies its invariants, **prove it**, and advance. Do not broaden scope across packet boundaries.

---

## 0. Coordinates

| Thing | Value |
|---|---|
| Workspace | `/Users/hue/code/dopemux-mvp` |
| Orchestrator root | `7890cbc1-3c2f-40a4-bacb-61eb705f3a6f` |
| Base branch | **`origin/main` @ `a2396a922`** (NOT local `main` — it's a squash-merge with a different SHA) |
| Packets | `task-packets/generated/DMX-COCKPIT-FONTS/<id>.json` |
| Design authority | `claudedocs/cockpit-fonts-remediation/DESIGN.md` |
| Load plan | `docs/ops/load-plans/load_plan-DMX-COCKPIT-FONTS.json` |
| Target tree | `docs/03-reference/Dopemux Cockpit TUI Design System/` (`fonts/*`, `colors_and_type.css`, doc `*.md`) |

**Leaf UUIDs** (for direct orchestrator ops):

| TP | id | uuid |
|----|----|------|
| 101 | `…-101-rename-plan-keys-harden-scripts` | `f2c374cd-abd8-4c59-bbd2-e9c5d8e6ce3d` |
| 102 | `…-102-patch-flags-editor-proportional-family-name` | `cd11b6c7-372b-4f95-84e4-5253ed6bb17a` |
| 103 | `…-103-css-font-face-matrix-reconcile` | `6a538831-770e-45fe-bc60-bddc12da1a3a` |
| 104 | `…-104-resolve-case-collisions` | `04f9d15d-a5d3-4e81-b652-133bb3991fed` |
| 105 | `…-105-purge-legacy-doc-refs` | `9010543e-f0a0-469e-8bb5-9b4698ff59f6` |
| 106 | `…-106-verify-remediation` | `cf9a4c16-fd0b-4fae-9a72-7f28258d7164` |

---

## 1. Pickup protocol (per packet)

1. **Find work** — `get_next_item` / `query_items overview` on root `7890cbc1`. **First wave = 101 + 104** (both unblocked, parallel-safe — they touch disjoint files).
2. **Claim** — `claim_item` the leaf UUID.
3. **Branch** — `codex/cockpit-fonts-<nnn>-<slug>` off `origin/main` (a dedicated worktree is ideal). *(The load plan's `claude/…` default reflects CC-first; since you are Codex, use `codex/…`.)*
4. **Read before edit** — the packet JSON (`invariants`, `steps`, `commit.allowlist`, `commit.verify`), the matching `DESIGN.md` section, and the real files. **Patch from runtime truth, not the packet prose.**
5. **Run the PAL chain** — PAL MCP is up (`mcp__pal__*`). RED-LANE packets (**101, 102, 104**) run the risky chain `analyze→thinkdeep→challenge→planner→[challenge]→implement→codereview→precommit→challenge`; the rest run `analyze→planner→codereview→precommit`. The packet's `pal_chain.steps` is authoritative.
6. **Implement** — honor every invariant; stay strictly inside `commit.allowlist`.
7. **Validate** — run `commit.verify`. Run the **manual font-toolchain gate** if you have the toolchain; otherwise record **NOT_RUN** with the missing dependency + static substitute evidence. Never fabricate a build result.
8. **Proof bundle** — every orchestrator item has a **required `proof-bundle` note** (AGENTS.md §9). Fill it: TP id, worktree, branch, files changed, validations with exit codes, codereview status, precommit status, commit SHA, PR URL or exact blocker, residual risks, UNKNOWNs.
9. **Land** — commit (allowlist only) → PR (`base: main`) → record proof note → `advance_item`.

---

## 2. The DAG — don't reorder

```
wave 1:  101   104        (parallel, no deps)
wave 2:  102               (after 101)
wave 3:  103  105          (103 after 101+102; 105 after 101+102+104)
wave 4:  106               (after 101,102,103,104,105 — fan-in)
```

- `101 → {102, 103, 105, 106}`  ·  `102 → {103, 105, 106}`  ·  `104 → {105, 106}`  ·  `103 → 106`  ·  `105 → 106`
- **101 is the load-bearing foundation** — almost everything depends on it.

---

## 3. Per-packet cheat sheet — with the gotcha that *will* bite you

**101 — rename plan keys + harden scripts (RED-LANE, foundation)**
Rename `IosevkaDopemux{Term,Editor}` → `Dopemux{Term,Editor}` across **four** sites: TOML `[buildPlans.*]` headers; `build-dopemux-fonts.sh` `PLANS=` + dist path + pre-clean glob; **`patch-nerd-font.sh` pre-clean glob (~:50) AND the `--mono` family guard (~:62)**.
🔴 **Why it matters:** the guard tests `family == "DopemuxTerm"`, but `family` is derived from the `IosevkaDopemux*` filename — so **Term is patched WITHOUT `--mono` today**. The rename is what makes Term mono actually fire. Prove it (patched Term faces single-width).
Also: `mkdir -p OUT_DIR` (don't hard-error); back up/restore Iosevka's `private-build-plans.toml` (don't clobber); no stale manifest on mid-build fail; ensure binaries + the manifest dotfile can't be committed. **Do NOT change the `family =` values.**

**102 — Editor proportional + stable family (RED-LANE)**
Add `--variable-width-glyphs` to the Editor patch branch (Term keeps `--mono`). Set the family via **explicit per-face `--name "<Family> Nerd Font"`**.
🔴 **`--name full` is forbidden** — Medium faces export as `Dopemux Term Medium`, which `--name full` parses as a *different family per weight*, breaking the `colors_and_type.css` `font-weight: 500 700` single-family range. Test name tables (ID 16 identical across Regular+Medium of a spacing family) + advance widths (Term single, Editor proportional).

**103 — full @font-face matrix + reconcile** (`colors_and_type.css` only)
Declare the **full 12-face matrix** (Term+Editor × Regular/Medium × Upright/Italic/Oblique). Italic→`font-style:italic`, Oblique→`font-style:oblique`. Align `--font-mono`/`--font-editor` to 102's family names (kill the stale no-space `DopemuxTerm Nerd Font Mono`). Decide plain-vs-patched `src` (Nerd glyphs in-browser need the patched faces) and document it.

**104 — resolve 6 case-collisions (RED-LANE, foundation)**
🔴 Use **`git rm --cached`** on the redundant casing — **never `git mv`** (`core.ignorecase=true` makes it a silent no-op). The 6 pairs are byte-identical on `origin/main`. Run from a clean `origin/main`; enumerate via `git ls-tree -r origin/main`; expect **exactly 6** (the working-tree `fonts/README.md` is a different-branch artifact — ignore it). Keep the casing inbound links use (default `README.md` UPPER).

**105 — purge legacy doc refs** (post-104 canonical-cased files)
`review-pack.md` `fonts/BUILD.md`→`build.md`; delete the `IosevkaHueTerm` "canonical brand mono" claims (README, build.md); reconcile doc-embedded `@font-face`/family/filename examples to 101 filenames + 102 families.

**106 — verify + manual gate (final_packet)**
`verify-remediation.sh`: **toolchain-free** asserts (zero collisions, zero stale refs, complete `@font-face`, all `--font-mono`/`--font-editor` consumers resolve) — fail-closed. `VERIFICATION.md`: document the manual full-toolchain gate. CI cannot build fonts, so this is the CI-runnable slice + a manual checklist.

---

## 4. Environment gotchas

- **codex CLI config:** `~/.codex/config.toml` has `service_tier="default"`, which codex 0.130.0 **rejects at parse** (the API also rejects `"flex"`). Override per-invocation with **`-c service_tier="fast"`**.
- **Base off `origin/main`**, not local `main` (squash-merge → different SHA). Repo is a **shallow clone** → three-dot diffs show false "no merge base"; use `gh api repos/DDD-Enterprises/dopemux-mvp/compare/main...<branch>` for the real diff.
- **Font toolchain** (for the manual gates only): local Iosevka checkout + nerd-fonts checkout + FontForge (`brew install fontforge`) + Node. Set `IOSEVKA_REPO` / `NERD_FONTS_REPO` / `OUT_DIR`. font-patcher runs via `fontforge -script font-patcher` — **not** `python3 font-patcher`. No toolchain → **NOT_RUN** + static evidence.
- **task-orchestrator** is stdio and can drop under SQLite contention from leaked per-client containers; if it drops, `docker kill` the leaked `task-orchestrator-*` containers (single-id; `docker stop/rm` 404 on Docker Desktop) and retry. Your workspace DB is `dopemux-mvp`; ignore `dnh_crm` containers (different workspace).

---

## 5. Governance (non-negotiable)

- **Authority order:** latest user instruction → `AGENTS.md`/packet → runtime code → schema → tests → config → docs → assumptions. **Runtime (`origin/main`) outranks the packet.**
- **Validation buckets:** **PASS / FAIL / NOT_RUN** — never collapse NOT_RUN into PASS.
- **Locked decisions (do not re-litigate):** Oblique→`font-style:oblique`; explicit per-face `--name` (not `--name full`); per-TP manual toolchain gates + toolchain-free 106.
- **Final confidence** for repo-changing work must be `VERIFIED` with the proof bundle attached (AGENTS.md §8).

## 6. Definition of done (series)

All 6 packets terminal, each with a proof bundle. `verify-remediation.sh` green. The manual build+patch gate run (or NOT_RUN documented) shows: clean `DopemuxTerm-*`/`DopemuxEditor-*` filenames, Term single-width + Editor proportional advances, **one typographic family per spacing**, 7/7 documented PUA codepoints, zero case-collisions, zero stale refs.
