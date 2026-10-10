---
id: RECOMMENDATIONS
title: Recommendations
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-17'
last_review: '2026-05-17'
next_review: '2026-08-15'
prelude: Recommendations (explanation) for dopemux documentation and developer workflows.
---
# RECOMMENDATIONS.md

All recommendations are labeled `RECOMMENDED`. They are intentionally separated from observed findings (per the audit packet's hard requirement). Recommendations cite the finding they address and propose a specific change; they do **not** implement anything.

Each recommendation:
- **Addresses** — finding ID(s) it resolves.
- **Action** — concrete proposed change in one sentence.
- **Authority** — which doc/file should change first to keep authority order intact.
- **Verification** — how a future maintainer can check that the recommendation landed.
- **Cost class** — `S` (single-file/small), `M` (multi-file or careful), `L` (cross-cutting change).

---

## CRIT-tier recommendations

### R-OPUS-1 — Re-tone the RTE Click help text against `brand-voice-guidelines.md §2A`

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-CRIT-1`.
- **Action:** Rewrite the docstrings of `rte_scan`, `extractor_list`, `extractor_run`, `extractor_doctor`, `extractor_status`, `extractor_preflight`, `extractor_validate_live`, `extractor_promptset_audit`, `extractor_trace`, and `truth_command` in `src/dopemux/cli.py` to match the §2A operator-production register: terse, procedural, lead with the result, end with `NEXT:` where an operator action is needed. Replace "Ignite Pipeline" / "Ritual Apothecary" / "Catalog Phases" / "Pre-Ignition Check" / "Ritual Status" / "Ritual Integrity" with plain action verbs ("Run", "Diagnose", "List", "Preflight", "Show status", "Audit").
- **Authority:** Runtime first; `brand-voice-guidelines.md` already covers the rule, no doc change needed.
- **Verification:** `rg -n "Ignite|Ritual|Catalog Phases|Pre-Ignition|Apothecary|Cognitive Routing|cockpit telemetry" src/dopemux/cli.py` returns zero matches; sample help text matches §2A "✅ Right" examples.
- **Cost class:** S.

### R-OPUS-2 — Reconcile truth-order across `AGENTS.md`, `README.md`, and `brand-voice-guidelines.md §9`

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-CRIT-2`.
- **Action:** Pick *one* canonical truth-order document (recommend `AGENTS.md §2`) and replace the divergent orderings in `README.md §5` and `brand-voice-guidelines.md §9` with explicit references back to AGENTS.md (`"See AGENTS.md §2 for repo-wide truth order. The list below is scoped to <X> only and does not override repo truth order."`). Keep brand-voice's *scoped* decision ladder if useful — but mark it as a sub-order, not a competing repo-wide order.
- **Authority:** Governance (`AGENTS.md`) wins; downstream docs adapt.
- **Verification:** `rg -n "Truth Order|truth order|Decision Ladder|decision ladder" AGENTS.md README.md .claude/brand-voice-guidelines.md` shows one normative source; the other two reference it.
- **Cost class:** M (multi-doc but small per-doc).

### R-OPUS-3 — Add an RTE-specific section to `.claude/CLAUDE.md` (or a sibling `.claude/RTE.md`)

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-CRIT-3` and indirectly `F-OPUS-MED-5`.
- **Action:** Write a short section/file teaching Claude/agents the RTE invariants:
  1. `DPMX_LIVE_OK=1` requirement for any live operation.
  2. `--dry-run` is the default for `dopemux rte run`; never weaken this default.
  3. Consent gate paths in `run_extraction_v5.py:2992-3076` are the source of truth for live-capable classification.
  4. The `first-live` preset (`services/repo-truth-extractor/README.md:147-169`) is the conservative onboarding path.
  5. `$10` accidental-run anchor — quote it.
  6. Generated `.proof.json` and `out/rte-pkt-*` artifacts never outrank runtime per `lib/proof_contract.py:119-127`.
  7. AGENTS.md §6 line 81 is the authority bound: "RTE outputs are evidence artifacts, not runtime truth."
- **Authority:** Claude guidance (tier 5), but writes the bridge to runtime invariants.
- **Verification:** A new contributor (or Claude agent) reading the file can answer: "What's the env var for live execution?" and "What's the safest first command to try?" without reading runtime code.
- **Cost class:** S.

## HIGH-tier recommendations

### R-OPUS-4 — Bring CLI emoji usage onto the 6-emoji whitelist (or migrate to nerd-font glyphs)

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-HIGH-1`.
- **Action:** In `src/dopemux/cli.py` and `src/dopemux/commands/extractor_commands.py`, replace off-whitelist emojis (📊 🆔 📦 📂 ⏪ 🔧 🌊 🚀 ⏯️ 🎭 💸 ⚖️ ⏩ 📥 📡 🛫 🏥 👁️ 💰 🛡️ ✅ 🔄 🗺️ 🔥) with the nerd-font status glyphs documented at `cli-ux-design-spec.md §4` and `brand-voice-guidelines.md §4.6`, or remove them. Keep the six allowed emojis where they appear (`💊 🧪 🧠 ⚡ 💧 🔬`).
- **Authority:** Runtime first; spec is already aligned.
- **Verification:** `rg -n "[^[:print:][:space:]]" src/dopemux/cli.py src/dopemux/commands/extractor_commands.py` then filter against the whitelist; expect ≤6 unique emoji characters.
- **Cost class:** S–M (mechanical).

### R-OPUS-5 — Replace `docs/ux/ux-style-guide.md` body with a one-line redirect

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-HIGH-2`.
- **Action:** Replace lines 18–42 of `docs/ux/ux-style-guide.md` with a single forwarding paragraph: "This file is non-authoritative. The CLI/TUI UX authority is `../04-explanation/branding/cli-ux-design-spec.md`. The runtime brand voice is `.claude/brand-voice-guidelines.md`. Do not prescribe palette or chip semantics here." Preserve the frontmatter for indexing.
- **Authority:** Docs only.
- **Verification:** `wc -l docs/ux/ux-style-guide.md` is small; `rg -n "READY|BLOCKED|DEFERRED|SUPERVISED|Spaceage" docs/ux/ux-style-guide.md` returns zero matches.
- **Cost class:** S.

### R-OPUS-6 — Either delete `docs/ux/terminal-rendering-guide.md` or fill its body

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-HIGH-3`.
- **Action:** Decide intent. If still desired, fill the body with content covering the `DOPEMUX_RENDER_MODE` and `NO_COLOR` semantics from `cli-ux-design-spec.md §7` plus actual terminal color-space/unicode-fallback behavior. If not desired, delete the file and remove its `_manifest.yaml` entry.
- **Authority:** Docs only.
- **Verification:** `wc -c docs/ux/terminal-rendering-guide.md` is either zero (deleted) or substantially larger (filled). If filled, it cross-references `cli-ux-design-spec.md §7` rather than restating it.
- **Cost class:** S.

### R-OPUS-7 — Either implement v5 promptset audit or rename the command to clarify v4-only scope

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-HIGH-4`.
- **Action:** Two viable paths. (a) Implement a v5 promptset audit (preferred — operators on the canonical engine deserve a canonical audit). (b) Rename the command to `dopemux rte promptset audit-v4` and have `dopemux rte promptset audit` either alias to v4 with a deprecation note or refuse with a message that says "v5 promptset audit is not yet implemented; v4-only is available at `dopemux rte promptset audit-v4`."
- **Authority:** Runtime first.
- **Verification:** `dopemux rte promptset audit --pipeline-version v5` either succeeds or returns a message that explicitly states the v5-audit gap and offers the v4 fallback.
- **Cost class:** M (option a) or S (option b).

### R-OPUS-8 — Reshape pre-live validator NO_GO error to `error_panel(problem, why, fix)` shape

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-HIGH-5`.
- **Action:** In `run_extraction_v5.py:3067-3070`, replace the `RuntimeError("Pre-live validator blocked live execution: " f"verdict={verdict} reason_codes={detail} output_dir={output_dir}.{stderr_suffix}")` raise with a structured error that includes:
  - **Problem:** "Pre-live validator returned NO_GO."
  - **Why:** Each reason code on its own line, optionally with the human-readable label from `validate_pre_live_gate_v25.py:101-113` (`CRITICAL_TEST_FAILURE`, `TARGET_TRUTH_SPLIT_MISMATCH`, etc.).
  - **Fix:** "Read `<output_dir>/VALIDATION_REPORT.json` for details. If a `CRITICAL_TEST_FAILURE`, run the failing test (`pytest <path>`) and re-validate. Do not waive without operator sign-off."
  - Use `[BLOCKER]` chip if rendering via `dopemux.console` is available; otherwise format as three labeled lines.
- **Authority:** Runtime + brand-voice spec §5.
- **Verification:** A simulated NO_GO produces a three-section message; `rg -n "Problem:|Why:|Fix:" services/repo-truth-extractor/run_extraction_v5.py` shows the structure.
- **Cost class:** S.

### R-OPUS-9 — Add progressive disclosure to `dopemux rte run --help`

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-HIGH-6`.
- **Action:** Split the 30+ options into groups using Click's option-group features (or split into a small set of essential options at the top and the rest under `--help-extended` or a dedicated `dopemux rte run --advanced-help` subcommand). At minimum, the help text should lead with: phase, pipeline version, dry-run/execute, routing-policy, run-id, promptset-root. Move batch, ui, prescan, escalation, and worker options under an "Advanced" header.
- **Authority:** Runtime first.
- **Verification:** `dopemux rte run --help` first screen (24 lines) shows ≤8 options; remaining options appear under a clearly named group or sub-help.
- **Cost class:** S–M.

## MED-tier recommendations

### R-OPUS-10 — Update `ARCHITECTURE.md §5.5` to name `dopemux rte` as the canonical operator path

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-MED-1`.
- **Action:** Replace the prose at `ARCHITECTURE.md:150` so it reads "operator invocation comes through `dopemux rte ...` or direct runner execution; `dopemux upgrades ...` remains as a legacy compatibility alias and is not the canonical operator path."
- **Authority:** Governance doc, downstream of runtime.
- **Verification:** `rg -n "dopemux upgrades" ARCHITECTURE.md` either returns zero (preferred) or returns a line that is explicitly a legacy reference.
- **Cost class:** S.

### R-OPUS-11 — Plan a re-identification of canonical RTE commands from `upgrades` to `rte`

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-MED-2`.
- **Action:** Schedule a refactor (not in this audit) to make `@rte.command(...)` the canonical decorator for `rte_run`/`rte_doctor`/`rte_status`/etc., with `@upgrades.command(...)` reduced to an alias adapter. Until then, document the inversion in `services/repo-truth-extractor/README.md` ("Note: the canonical command identity currently lives under the `upgrades` Click group as a historical artifact; both `dopemux rte X` and `dopemux upgrades X` resolve to the same handler.").
- **Authority:** Runtime change is the eventual fix; doc note is the interim.
- **Verification:** `rg -n "@upgrades.command|@rte.command" src/dopemux/cli.py` count: post-refactor, `@rte.command` should outnumber `@upgrades.command` for RTE-canonical commands.
- **Cost class:** M (refactor).

### R-OPUS-12 — Disambiguate `dopemux extractor status` dual mode

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-MED-3`.
- **Action:** Split into two commands: `dopemux extractor status` (always reads SYNC_MANIFEST.json from a promptset directory) and remove the flag-based branch into runtime status. Operators wanting runtime status use `dopemux rte status`. Alternative: emit a single-line preamble such as `"Mode: promptset-sync-manifest"` / `"Mode: runtime-status (deprecated, use dopemux rte status)"` so the operator knows which job they got.
- **Authority:** Runtime.
- **Verification:** `rg -n "if pipeline_version is not None" src/dopemux/commands/extractor_commands.py` returns zero (split) or the dual-mode is explicitly framed in the output.
- **Cost class:** S.

### R-OPUS-13 — Document `dopemux rte wizard`

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-MED-4`.
- **Action:** Add a one-paragraph section to `services/repo-truth-extractor/README.md` and `README.md §4` describing what `dopemux rte wizard` does, when to use it, and what safety posture it adopts. If the wizard is internal-only or unfinished, mark its `--help` text with `[INTERNAL]` or remove it from the `rte` group alias at `cli.py:5516`.
- **Authority:** Docs first; runtime second if the command should be hidden.
- **Verification:** `rg -n "rte wizard|rte.add_command\\(audit.commands" src/dopemux/cli.py README.md services/repo-truth-extractor/README.md` shows aligned references.
- **Cost class:** S.

### R-OPUS-14 — Add `repo-truth-extractor` to `services/.claude/CLAUDE.md` Key Services table

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-MED-5` (paired with `F-OPUS-CRIT-3`).
- **Action:** Add a row to the table at `services/.claude/CLAUDE.md:38-44`: `| repo-truth-extractor | (CLI, no HTTP port) | Repo truth extraction; uses DPMX_LIVE_OK gate, $-cost surface |`. Add it to the ASCII service tree (~line 67).
- **Authority:** Claude guidance.
- **Verification:** `rg -n "repo-truth-extractor" services/.claude/CLAUDE.md` returns at least two lines (table row + tree entry).
- **Cost class:** S.

### R-OPUS-15 — Add `DPMX_LIVE_OK=1` to the `--help` epilog of every live-capable command

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-MED-6` (paired with `R-UX-1`).
- **Action:** Use Click's `epilog=...` on `extractor_run`, `extractor_validate_live`, `extractor_preflight` (when `--auth-doctor` is set), and `rte_scan` to include a short note: `"Live execution requires DPMX_LIVE_OK=1 in the environment in addition to --execute (or stage-specific flags). See services/repo-truth-extractor/README.md §Live batch safety."`
- **Authority:** Runtime.
- **Verification:** `rg -n "DPMX_LIVE_OK" src/dopemux/cli.py` returns at least four matches (one per command); manual `dopemux rte run --help` shows the epilog.
- **Cost class:** S.

### R-OPUS-16 — Add a structured frontmatter flag to cockpit audit reports

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-MED-7`.
- **Action:** Add a frontmatter field such as `implementation_authority: none` and/or `claude_design_evidence_only: true` to every `docs/05-audit-reports/cockpit-*-2026-04-24.md` file. Optionally introduce a canonical vocabulary documented in `AGENTS.md` (e.g., values `none`, `advisory`, `runtime_spec`).
- **Authority:** Docs + governance (AGENTS.md gains a sub-section on the vocabulary).
- **Verification:** `rg -n "implementation_authority|claude_design_evidence_only" docs/05-audit-reports/cockpit-*.md` returns one match per file.
- **Cost class:** S.

## LOW-tier recommendations

### R-OPUS-17 — Annotate `validate-live` USD options with explicit unit in `--help`

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-LOW-1`.
- **Action:** Add `help="USD spend cap for the provider probe stage. Default $0.10 USD."` and equivalents on the four `*-max-usd` options at `cli.py:5317, 5321, 5326, 5328`.
- **Authority:** Runtime.
- **Verification:** `rg -n "USD" src/dopemux/cli.py` shows entries on each of the four flags.
- **Cost class:** S.

### R-OPUS-18 — Add a brand-voice closer audit to RTE runtime emitters

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-LOW-2`.
- **Action:** Either (a) extend `scripts/brand_lint.py` to audit RTE runtime emitter sites for `NEXT:` / `Receipt:` / `PROGRESS` closers, or (b) add a one-time pass over `run_extraction_v5.py` adding closers to user-visible emit paths and document a maintainer rule. Closer rule is at `brand-voice-guidelines.md:181-183`.
- **Authority:** Lint extension is governance; runtime change is runtime.
- **Verification:** `python scripts/brand_lint.py` reports zero closer-rule violations for any RTE runtime file.
- **Cost class:** M.

### R-OPUS-19 — Carry `DPMX_LIVE_OK=1` into the `dopemux truth` deprecation message

- **Label:** `RECOMMENDED`.
- **Addresses:** `F-OPUS-LOW-3` (paired with `R-OPUS-15`).
- **Action:** Append a line to the deprecation message at `cli.py:5495-5500`: `"Note: live execution also requires DPMX_LIVE_OK=1 in the environment."` Keep the three dry-run-safe redirects.
- **Authority:** Runtime.
- **Verification:** `rg -n "DPMX_LIVE_OK" src/dopemux/cli.py` includes a match in the `truth_command` function body.
- **Cost class:** S.

---

## Recommendation rollup

| Tier | Count | IDs |
|------|------:|-----|
| CRIT | 3 | R-OPUS-1, R-OPUS-2, R-OPUS-3 |
| HIGH | 6 | R-OPUS-4 through R-OPUS-9 |
| MED  | 7 | R-OPUS-10 through R-OPUS-16 |
| LOW  | 3 | R-OPUS-17, R-OPUS-18, R-OPUS-19 |

**Suggested execution order if implementing in one campaign:**

1. R-OPUS-2 (truth-order reconciliation) — unblocks every other governance change.
2. R-OPUS-3 + R-OPUS-14 (Claude-guidance for RTE) — protects agent operations.
3. R-OPUS-1 + R-OPUS-4 (CLI tone + emoji whitelist) — most operator-visible.
4. R-OPUS-8 (validator error shape) — most consequential error path.
5. R-OPUS-9 (progressive disclosure) — improves the most-used help surface.
6. R-OPUS-5 + R-OPUS-6 (UX doc cleanup) — eliminates two drift surfaces.
7. R-OPUS-10 + R-OPUS-11 (ARCH/upgrades reconciliation) — long-term cleanliness.
8. R-OPUS-7 (v5 promptset audit) — closes a real operator gap.
9. R-OPUS-15 + R-OPUS-19 (DPMX_LIVE_OK in help/deprecation) — small safety wins.
10. Remaining (R-OPUS-12, 13, 16, 17, 18) — opportunistic.

This sequencing is suggestive only; the audit packet's hard non-goal forbids implementing any of these.

End of RECOMMENDATIONS.md.
