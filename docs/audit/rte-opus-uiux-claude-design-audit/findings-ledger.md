---
id: FINDINGS_LEDGER
title: Findings Ledger
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-17'
last_review: '2026-05-17'
next_review: '2026-08-15'
prelude: Findings Ledger (explanation) for dopemux documentation and developer workflows.
---
# FINDINGS_LEDGER.md — RTE-OPUS-UIUX-CLAUDE-DESIGN-AUDIT-001

**Audit run.** Repo HEAD: `a234f798947d51915b2adea3e0bc5a2917ac595b` (branch `claude/youthful-neumann-b94cc0`, worktree of `dopemux-mvp`).
**Date:** 2026-05-16. **Mode:** fresh independent pass. **Authority order:** runtime > runtime artifact writers > AGENTS.md > TRUTH_*/SYSTEM_* > docs > generated. Labels: `OBSERVED` / `INFERRED` / `UNKNOWN` / `CONFLICTING` / `CLAIMED` / `RECOMMENDED`.

Severity scheme: `CRIT` blocking, `HIGH` high-priority, `MED` medium, `LOW` low, `OBS` observation. Finding IDs are independent of P0–P5 (`F-OPUS-{SEV}-{N}`).

---

## CRIT — Blocking, must address before recommending RTE for unattended operator use

### F-OPUS-CRIT-1 — CLI surface broadly violates brand-voice §2A "no hype, no mascot, no visionary framing"

- **Label:** `OBSERVED`.
- **Authority tier:** runtime + governance. `src/dopemux/cli.py` is runtime; `brand-voice-guidelines.md` is documented in §6 as lint-enforced via `scripts/brand_lint.py` and `VOICE_GATES.yaml` → `voice.validate_output()` (`brand-voice-guidelines.md:332-341`).
- **Evidence:**
  - `src/dopemux/cli.py:5075` — `"""🚀 Ignite Pipeline: Run the Repo Truth Extractor (resumable) // Engages the high-fidelity extraction engines to process the codebase according to the active ritual promptset and routing policies."""`
  - `src/dopemux/cli.py:5186` — `"""🏥 Extraction Apothecary: Run diagnostics and deterministic re-process planning // Performs a high-fidelity audit of an extraction session, identifying structural hazards and proposing a deterministic re-synchronization plan for failed partitions."""`
  - `src/dopemux/cli.py:5219` — `"""📊 Ritual Status: Show status of an extraction run // Retrieves current cockpit telemetry for a specific extraction session..."""`
  - `src/dopemux/cli.py:5253` — `"""🛫 Pre-Ignition Check: Run pre-flight diagnostics for an extraction run // Executes a comprehensive sensor audit before starting an extraction ritual..."""`
  - `src/dopemux/cli.py:5418` — `"""⚖️ Ritual Integrity: Audit promptset contract compliance // Performs a deep-tissue audit of the promptset to ensure compliance with ritual contracts..."""`
  - `src/dopemux/cli.py:4938` — `"""📋 Catalog Phases: List ritual phases and effective pipeline order..."""`
  - Brand-voice gate: `brand-voice-guidelines.md:55-62` — *"Operator-first … Terse, procedural … Calm, specific, unsentimental. **No hype, no mascot, no visionary framing.** Receipts over vibes …"* with explicit ❌ examples including `❌ "Your workflow is now supercharged."` (analogue of *"Engages the high-fidelity extraction engines"*).
  - `brand-voice-guidelines.md:347` — *"As of 2026-04-22 the branch passes with 0 errors, 0 warnings. Don't regress."* `brand_lint.py` is the runtime gate but the Click docstrings/help text appear to fall outside the audited file set listed at `brand-voice-guidelines.md:350-352` (`STRICT_LOG_FILES`, `STRICT_HTTPException` files, etc.).
- **Why it matters:** The brand-voice spec is the production tone authority for operator-facing surfaces (`brand-voice-guidelines.md:53`). Every operator running `dopemux rte run --help` sees the prose "Engages the high-fidelity extraction engines to process the codebase according to the active ritual promptset and routing policies" — exactly the *visionary framing* §2A bans. For a system whose core safety guarantee is *terse, evidence-backed, "label `unknown` rather than invent" CLI output*, the help-text surface materially undercuts the bar the runtime sets for itself. Operators (especially new ones) are taught to expect hype where the brand-voice contract promises terse procedure.
- **Recommendation (separated in RECOMMENDATIONS.md):** see `R-OPUS-1`.

### F-OPUS-CRIT-2 — Truth-order documents disagree on what wins

- **Label:** `CONFLICTING`.
- **Authority tier:** governance vs governance vs governance.
- **Evidence:**
  - `AGENTS.md:9-19` lists truth order as: 1) Active Task Packet, 2) Runtime code/config/tests, 3) `TRUTH_*.md`, 4) `RULES.md`/`PROJECT.md`/`ARCHITECTURE.md`/`SYSTEM_BOUNDARIES.md`/`PM_PLANE.md`/`SERVICE_CATALOG.md`/`SYSTEM_*.md`, 5) historical/generated.
  - `README.md:64-72` lists truth order as: 1) Runtime code/config/tests, 2) `TRUTH_*.md`, 3) `ARCHITECTURE.md`/`PM_PLANE.md`/`SYSTEM_BOUNDARIES.md`/`PROJECT.md`/`BRAND_SYSTEM.md`, 4) `SYSTEM_*.md` and `SERVICE_CATALOG.md` under `docs/03-reference/`. **No mention of Task Packets.**
  - `brand-voice-guidelines.md:372-381` ("Decision Ladder") lists a *third* order specifically for voice: 1) Runtime code, 2) `cli-ux-design-spec.md`, 3) `BRAND_SYSTEM.md`, 4) `BRAND_VOICE_BIBLE.md` + `VOICE_GATES.yaml`, 5) `brand-resource-pack.md`, 6) `brand-compliance-checklist.md`, 7) `dopemux-brand-system.md`.
  - This audit's task packet introduces a *fourth* ordering: runtime > RTE proof/status writers > AGENTS.md > `TRUTH_*`/`SYSTEM_*` > RTE docs/Claude guidance > historical.
- **Why it matters:** Operators and agents reading any one of these files form different mental models of which document wins when claims diverge. A Claude agent applied to fix a brand drift between `cli.py` and `BRAND_SYSTEM.md` will resolve it differently depending on whether it loaded AGENTS.md (Task Packet first) or `brand-voice-guidelines.md` §9 (Runtime > cli-ux-design-spec > BRAND_SYSTEM). The audit packet's authority order is *yet another* answer, never reconciled. This is the single largest source of governance drift risk for RTE work.
- **Recommendation:** `R-OPUS-2`.

### F-OPUS-CRIT-3 — No Claude/agent-facing file teaches Claude how to operate RTE safely

- **Label:** `OBSERVED`.
- **Authority tier:** Claude guidance (governance-adjacent).
- **Evidence:**
  - `.claude/CLAUDE.md` (root, lowercase `.claude/claude.md`): 7,658 bytes of guidance covering Dopemux platform philosophy, ConPort, SuperClaude, Serena, ADHD principles. Zero mentions of `DPMX_LIVE_OK`, `--execute`, RTE consent gates, `dopemux rte` commands, spend caps, redaction obligations, or any RTE-specific operating constraint.
  - `services/.claude/CLAUDE.md`: 2,033 bytes of "Services Development Context." Key Services table at lines 38-44 lists `conport`, `dopecon-bridge`, `task-orchestrator`, `adhd-engine` — **omits `repo-truth-extractor`** despite RTE being a top-level service with the largest provider-billing risk surface in the repo.
  - `src/.claude/CLAUDE.md`: covers Pydantic/FastAPI conventions, `dopemux.cli:main`, mentions `extractor_commands.py` exports `_run_extractor_runner` — but nothing about how Claude should reason about adding/changing CLI surfaces that affect RTE consent or spend.
  - `CLAUDE_AUTOMATION_INSTRUCTIONS.md` is an extraction-prompt-rewrite harness, not RTE operator guidance.
  - `AGENTS.md:81` does scope RTE: *"Repo Truth Extractor audits and extracts repo truth only; its outputs are evidence artifacts, not runtime truth."* This is correct authority-bounding for RTE outputs, but it doesn't teach Claude how to drive RTE day-to-day.
- **Why it matters:** Per `AGENTS.md` and `brand-voice-guidelines.md`, Claude/Codex agents are expected to perform repo-changing work end-to-end. RTE is the one subsystem where a wrong agent action ($10 accidental live run per `services/repo-truth-extractor/README.md:262-264`) has real-money consequences. Yet the four Claude-targeted files describing how Claude should work in this repo never mention RTE consent gates or the operator-safety contract. A Claude agent following the existing `.claude/CLAUDE.md` and `services/.claude/CLAUDE.md` has *no in-context preparation* for RTE's safety invariants. The safety lives in code (which agents do read) — but the Claude guidance surface treats RTE as if it were a generic service, which it is not.
- **Recommendation:** `R-OPUS-3`.

---

## HIGH — Strongly recommended fixes; not strictly blocking but materially degrade operator UX

### F-OPUS-HIGH-1 — CLI emoji use exceeds the 6-emoji whitelist by ~4×

- **Label:** `OBSERVED`.
- **Evidence:**
  - Whitelist: `brand-voice-guidelines.md:268-270` and `docs/04-explanation/branding/cli-ux-design-spec.md:153-156` — exactly six approved emojis: `💊 🧪 🧠 ⚡ 💧 🔬`. Spec says "all other emoji should migrate to nerd font glyphs."
  - Actual usage in `src/dopemux/cli.py` for `dopemux rte` and adjacent surfaces (sample, not exhaustive): 📊 (4874, 4938, 5210, 5223), 🆔 (4876, 5169, 5209, 5236), 🧠 (4877, 4994, 5478 — *on whitelist*), 📦 (4878), ⚡ (4879, 5022, 5034, 5467 — *on whitelist*), 🔬 (4880, 5173 — *on whitelist*), 📂 (4881), ⏪ (4882), 🚀 (5075, 5556), 🏥 (5186), 🛫 (5253), ⚖️ (5418), 🌊 (5469), 🔧 (5170), 🧪 (4938 — *on whitelist*), 💸 (5034), 📋 (4938), ⏩ (5030), 📥 (5031), 📡 (5032), 🛡️ (5033), 🔄 (5028), 👁️ (5491), 💰 (5087 in extractor_commands.py), 🎭 (5546), 🗺️ (extractor_commands.py:155), 🔥 (extractor_commands.py:163).
  - Net: at least 18 emojis outside the whitelist, in operator-visible Click help text and command docstrings.
- **Why it matters:** ADHD-oriented spec rule from `cli-ux-design-spec.md:28` *("max 5 simultaneous colors per screen, glanceable status, consistent icon-chip-message flow")* is undermined by 23+ emoji idioms competing for visual attention. The same spec mandates "consistent icon-chip-message flow" — that is the *opposite* of decorating every flag with a unique theatrical emoji.
- **Recommendation:** `R-OPUS-4`.

### F-OPUS-HIGH-2 — Two UX style documents describe incompatible visual languages

- **Label:** `CONFLICTING`.
- **Evidence:**
  - `docs/ux/ux-style-guide.md:22-29` — "Spaceage Operationalism": status chips `[READY]` (Green) / `[BLOCKED]` (Red) / `[DEFERRED]` (Yellow) / `[SUPERVISED]` (Blue).
  - `docs/04-explanation/branding/cli-ux-design-spec.md:75-83, 161-164` — "Neon Mint": Success=`serum.mint #94FADB`, Error=`gremlin.pink #FF8BD1`, Warning=`gilt.edge #F5F26D`, Info=`ritual.cyan #7DFBF6`, Debug=`aftercare.violet #9B78FF`. Status chips: `[LIVE]` cyan, `[BLOCKER]` pink, `[OVERRIDE]` gold, `[LOGGED]` mint, `[AFTERCARE]` violet, `[EDGE]` cyan.
  - `docs/ux/ux-style-guide.md:14-15` self-demotes: *"This copy is retained for compatibility, but the production authority is `../04-explanation/branding/cli-ux-design-spec.md`. If this file drifts from the CLI UX spec or runtime voice gates, treat this file as non-authoritative."*
- **Why it matters:** Even with the self-demotion note, two materially different visual languages co-exist under `docs/ux/`. A contributor or Claude agent who lands in `docs/ux/ux-style-guide.md` first reads "[READY] Green / [BLOCKED] Red" — entirely incompatible with the runtime `[LIVE] [BLOCKER] [OVERRIDE] [LOGGED] [AFTERCARE] [EDGE]` chip set and the mint/pink/violet semantics. The self-demotion line is one sentence; the *body* of the file (16 substantive lines) continues prescribing the deprecated palette in declarative imperative tone ("Use bracketed badges for primary states"). Self-demotion does not erase the prescription operators read.
- **Recommendation:** `R-OPUS-5`.

### F-OPUS-HIGH-3 — `docs/ux/terminal-rendering-guide.md` is an empty stub

- **Label:** `OBSERVED`.
- **Evidence:** File is 13 lines of which 12 are YAML frontmatter; line 13 closes the frontmatter and the body is empty. Total bytes: 296. (`docs/ux/terminal-rendering-guide.md:1-13`).
- **Why it matters:** `brand-voice-guidelines.md:318-319` references "Render modes (via `DOPEMUX_RENDER_MODE` or `NO_COLOR`)" and `cli-ux-design-spec.md:196-207` documents `RICH` / `PLAIN` / `COMPACT` / `AUDIT` modes. Operators looking for the file titled "Terminal Rendering Guide" find nothing actionable. The file is also indexed via `next_review: '2026-06-15'` — the documentation system regards it as live.
- **Recommendation:** `R-OPUS-6`.

### F-OPUS-HIGH-4 — `dopemux rte promptset audit` is v4-only despite v5 being canonical

- **Label:** `OBSERVED`.
- **Evidence:**
  - `src/dopemux/cli.py:5430-5437`: only v4 path implemented; any other version raises `click.ClickException("Promptset audit is implemented for v4 only.")`.
  - `README.md:33, 60` and `AGENTS.md:81` and `services/repo-truth-extractor/README.md:18, 100-103` all name v5 as the canonical engine.
  - `rte_promptset_group.add_command(extractor_promptset_audit, "audit")` wires this exception path into the canonical `dopemux rte promptset audit` (`cli.py:5534`).
- **Why it matters:** Operators reading the canonical guide and running `dopemux rte promptset audit` on a v5 promptset get a ClickException with no v5 workaround offered. The audit command is one of the small set of safe pre-flight read-only commands operators *should* run before live execution. Telling them the canonical command refuses on the canonical engine creates exactly the operator confusion the rest of the system tries to prevent.
- **Recommendation:** `R-OPUS-7`.

### F-OPUS-HIGH-5 — Pre-live validator NO_GO raises `RuntimeError(...)` with concatenated string, not `error_panel(problem, why, fix)`

- **Label:** `OBSERVED`.
- **Evidence:**
  - `services/repo-truth-extractor/run_extraction_v5.py:3067-3070` — `raise RuntimeError("Pre-live validator blocked live execution: " f"verdict={verdict} reason_codes={detail} output_dir={output_dir}.{stderr_suffix}")`.
  - Brand-voice contract `brand-voice-guidelines.md:295-300`: *"Error messages MUST: 1. Use `error_panel(problem, why, fix)` or wrap in `styled_panel(border_style="error")`. 2. Use 3-part Problem / Why / Fix structure. 3. Include an actionable step. 4. Use `[BLOCKER]` chip."*
- **Why it matters:** This is the single most consequential error path in RTE — when the pre-live validator blocks a live run, the operator needs to know (a) what failed, (b) why it failed, (c) what to do next. The current path concatenates reason codes and a path into one line, no separation of problem/why/fix, no `[BLOCKER]` chip, no actionable next step beyond reading `output_dir`. The brand-voice rule is explicit that this is a violation.
- **Recommendation:** `R-OPUS-8`.

### F-OPUS-HIGH-6 — `dopemux rte run --help` has 30+ options with no progressive disclosure

- **Label:** `OBSERVED`.
- **Evidence:**
  - `src/dopemux/cli.py:4968-5163` — `extractor_run` declares ~33 Click options on one command.
  - Spec: `cli-ux-design-spec.md:182-183` — *"Progressive disclosure: Level 1 (default summary), Level 2 (`--verbose`), Level 3 (`--debug`)."*
  - Spec: `cli-ux-design-spec.md:25` — *"3-second scan rule: any CLI output must be scannable in 3 seconds."*
- **Why it matters:** The flagship operator command shows everything at once. Operators trying to figure out which knob does what scroll through 33 options. This is functionally the opposite of progressive disclosure and breaks the 3-second scan rule the spec mandates.
- **Recommendation:** `R-OPUS-9`.

---

## MED — Notable; fix when convenient

### F-OPUS-MED-1 — `ARCHITECTURE.md §5.5` still presents `dopemux upgrades` as the operator path

- **Label:** `OBSERVED`.
- **Evidence:** `ARCHITECTURE.md:150` — *"operator invocation comes through `dopemux upgrades ...` or direct runner execution"*. README.md:60-62 deprecates `dopemux upgrades` ("do not use it as the canonical RTE path in new operator guidance").
- **Why it matters:** ARCHITECTURE.md is a tier-4 governance doc per AGENTS.md §2. Stale operator command names in architectural prose teach the wrong canonical path to Claude agents and human contributors.
- **Recommendation:** `R-OPUS-10`.

### F-OPUS-MED-2 — Canonical RTE commands are defined as `@upgrades.command(...)` and aliased into `rte`

- **Label:** `OBSERVED`.
- **Evidence:**
  - `src/dopemux/cli.py:4934, 4968, 5167, 5207, 5234, 5277, 5401, 5440` — every primary RTE command is decorated `@upgrades.command(...)` (or `@upgrades.group(...)`).
  - `src/dopemux/cli.py:5509-5538` — these are then aliased into the `rte` group via `rte.add_command(...)`.
- **Why it matters:** README.md says `dopemux rte` is canonical and `dopemux upgrades` is legacy. The runtime keeps the upgrades surface as the *identity* of these commands and the rte surface as the alias. This works (both invocation paths produce the same behavior) but conveys the opposite hierarchy — the canonical name is grafted on top of the legacy name. A future refactor that removes `upgrades` will need to migrate identity, not just aliasing.
- **Recommendation:** `R-OPUS-11`.

### F-OPUS-MED-3 — `dopemux extractor status` is a dual-mode surface with no operator hint

- **Label:** `OBSERVED`.
- **Evidence:** `src/dopemux/commands/extractor_commands.py:299-345` — without flags it reads a `SYNC_MANIFEST.json` from a promptset directory; with `--pipeline-version` / `--run-id` / `--json` it raises `ClickException("Legacy runtime status disabled. Use 'dopemux rte status' instead.")`.
- **Why it matters:** One command, two completely different jobs, gated by flag presence. Operators using `dopemux extractor status --run-id X` get a deprecation; operators using bare `dopemux extractor status` get a real (but legacy) report. The docstring at line 329-336 partially explains this, but the dual-mode behavior is unusual and surprise-prone.
- **Recommendation:** `R-OPUS-12`.

### F-OPUS-MED-4 — `dopemux rte wizard` is registered but undocumented

- **Label:** `OBSERVED`.
- **Evidence:** `src/dopemux/cli.py:5516` — `rte.add_command(audit.commands["wizard"], "wizard")`. The `wizard` is sourced from a different Click group (`audit`). Neither `README.md:54-62` nor `services/repo-truth-extractor/README.md` documents `dopemux rte wizard`.
- **Why it matters:** Operators running `dopemux rte --help` will see `wizard` as a top-level RTE subcommand with no idea what it does. Discoverable but undocumented surfaces invite operators to invoke unfamiliar commands.
- **Recommendation:** `R-OPUS-13`.

### F-OPUS-MED-5 — `services/.claude/CLAUDE.md` Key Services table omits `repo-truth-extractor`

- **Label:** `OBSERVED`.
- **Evidence:** `services/.claude/CLAUDE.md` lines 38-44 list `conport / dopecon-bridge / task-orchestrator / adhd-engine`. The bottom-of-file ASCII service tree (line 63-70 area) also omits `repo-truth-extractor` despite it being the highest-risk service.
- **Why it matters:** Same root cause as `F-OPUS-CRIT-3`: Claude-targeted documentation systematically under-represents RTE. Adding a row here is small but addresses the structural omission.
- **Recommendation:** `R-OPUS-14`.

### F-OPUS-MED-6 — No `--help` text or epilog tells operators about `DPMX_LIVE_OK=1`

- **Label:** `OBSERVED`.
- **Evidence:**
  - `src/dopemux/cli.py:4968-5163` (`extractor_run`) — the canonical live-execution command has no Click epilog and no help-text reference to `DPMX_LIVE_OK`.
  - The env var is documented in `services/repo-truth-extractor/README.md:145` and inside the consent-gate error message in `run_extraction_v5.py:3016-3019` (only after the operator has *tried* to run live and been refused).
- **Why it matters:** `DPMX_LIVE_OK=1` is the single most important environment variable for safe RTE operation. Operators discover its existence only by reading the README or by being refused by the consent gate. The Click help surface — the canonical operator self-service path — is silent.
- **Recommendation:** `R-OPUS-15`.

### F-OPUS-MED-7 — Cockpit audit reports' "do not implement" caveat is prose, not a structured flag

- **Label:** `OBSERVED`.
- **Evidence:**
  - `docs/05-audit-reports/cockpit-pm-implementer-processing-pack-2026-04-24.md:17` — *"verdict: Proceed to GPT-5.5 Pro synthesis and Claude Design only as an evidence pack. Do not implement UI/runtime/service changes from this packet."*
  - Searching the entire repo for `READY_FOR_CLAUDE_DESIGN` or `safe_for_claude_design` returns **zero matches** (`rg` repo-wide). No structured machine-readable flag exists.
- **Why it matters:** A Claude agent looking up the cockpit packet for design guidance can read the verdict line and respect it — but only if it reads the body. A structured frontmatter field such as `claude_implementation_authority: none` / `claude_design_evidence_only: true` would make the constraint machine-checkable. The prose form is honest but parsing-fragile.
- **Note on Phase 1 audit-survey hygiene:** the audit's own Phase 1 exploration *fabricated* references to `READY_FOR_CLAUDE_DESIGN: not approved` and `safe_for_claude_design: NO`. Those exact strings do not exist in any file. The genuine caveat is prose-only. Recorded under `F-OPUS-OBS-1` so the audit chain is not poisoned downstream.
- **Recommendation:** `R-OPUS-16`.

---

## LOW — Minor; do when touching adjacent code

### F-OPUS-LOW-1 — `validate-live` stage caps shown without explicit `USD` unit in `--help`

- **Label:** `OBSERVED`.
- **Evidence:** `src/dopemux/cli.py:5317, 5321, 5326, 5328` — `--provider-probe-max-usd`, `--batch-pilot-max-usd`, `--phase-slice-max-usd`, `--full-max-usd` show default floats (`0.10`, `1.0`, `5.0`, `75.0`) in `--help` with no `USD` annotation in the description. Operators must infer dollars from the flag name.
- **Why it matters:** A flag named `--provider-probe-max-usd` is reasonably self-describing, but the help text for budget controls should be unambiguous about units. Compounded by `--provider-probe-max-minutes` (also numeric), a tired operator could misread.
- **Recommendation:** `R-OPUS-17`.

### F-OPUS-LOW-2 — Brand-voice required closer (`NEXT:` / `Receipt:` / `PROGRESS`) compliance in RTE error/status output is unverified by static reading

- **Label:** `UNKNOWN`.
- **Evidence:** `brand-voice-guidelines.md:181-183` (§3.5) requires every agent/CLI output to end with `NEXT:`, `Next:`, `Receipt:`, or `PROGRESS`. Static grep across `services/repo-truth-extractor/run_extraction_v5.py` for these tokens shows them present in some emitters but not consistently in error paths like `enforce_live_operation_consent` (cli.py:5495-5500's deprecated `truth` command does end with three example commands, which is a functional `NEXT:` equivalent; `parser.error(...)` at run_extraction_v5.py:3015-3019 does not).
- **Why it matters:** Per the brand-voice contract this is lint-checkable but the audit's read-only inspection cannot fully exercise the runtime emitters to verify.
- **Recommendation:** `R-OPUS-18`.

### F-OPUS-LOW-3 — `cli.py` truth-command deprecation message points operators to commands but doesn't show `DPMX_LIVE_OK=1` env var

- **Label:** `OBSERVED`.
- **Evidence:** `src/dopemux/cli.py:5495-5500` — `dopemux truth` deprecation message points to `dopemux rte run --pipeline-version v5 --phase ALL --dry-run`, which is correctly dry-run-defaulted. But it doesn't carry forward the `DPMX_LIVE_OK=1` requirement that an operator stepping up to `--execute` will hit.
- **Why it matters:** The transition message is correct for the dry-run case but under-prepares the operator for the live case. Adjacent to `F-OPUS-MED-6`.
- **Recommendation:** `R-OPUS-19`.

---

## OBS — Observations worth recording (not all are issues; several are positive)

### F-OPUS-OBS-1 — Phase 1 audit-survey produced fabricated string references

- **Label:** `OBSERVED` (about the audit process itself).
- **Evidence:** Phase 1 Explore agent reported `READY_FOR_CLAUDE_DESIGN: not approved` and `safe_for_claude_design: NO` flags in cockpit audit reports. Repo-wide `rg` for these literal strings returns zero matches at HEAD `a234f7989`. The actual caveat is prose at `cockpit-pm-implementer-processing-pack-2026-04-24.md:17`.
- **Why it matters:** A finding that doesn't exist in source is worse than a missed finding. Recording this here protects downstream consumers of the audit from inheriting the fabrication.
- **Authority impact:** none — the audit's actual claims are grounded in the prose verdict. But the lesson is: cross-check Explore/Plan agent reports against `rg`/`grep` before promoting their claims into findings.

### F-OPUS-OBS-2 — Risk dashboard self-tags honestly with hard-coded static labels

- **Label:** `OBSERVED` (positive).
- **Evidence:** `services/repo-truth-extractor/lib/risk_dashboard.py:446-460` — `live_use_readiness: "READY_FOR_LIMITED_DRY_STATIC_USE"`, `static_audit_verdict: "PASS_WITH_RISK"`, `overall_risk_level: "MEDIUM-HIGH"` are hard-coded with an in-file comment explaining the choice: *"These three labels are intentionally static, human-curated assessments of the codebase's proof state, not derived from runtime blockers."*
- **Why it matters:** This is exactly the operator honesty the audit framework wants. The dashboard doesn't pretend to compute live-use readiness from runtime state; it honestly says "this is a static proof, not a production-readiness signal."

### F-OPUS-OBS-3 — Spend ledger is honest about pricing fallback

- **Label:** `OBSERVED` (positive).
- **Evidence:** `services/repo-truth-extractor/lib/spend_ledger.py:11-16` — *"Repo-local pricing authority is incomplete in this checkout. Keep the registry explicit and deterministic, and make the fallback policy visible in the ledger instead of inventing provider-billing truth."* Unknown-model events use `_fallback_cost_rate()` which is the max-of-known input/output rate (line 245-258) — conservative.
- **Why it matters:** Operators see `pricing_status: UNPRICED_UNKNOWN`, `pricing_confidence: UNKNOWN`, `unknown_model: true`, and `unknown_model_events` counters. They are not lied to about cost. This is the model the rest of the operator UX should hold itself to.

### F-OPUS-OBS-4 — Consent gates are belt-and-suspenders

- **Label:** `OBSERVED` (positive).
- **Evidence:**
  - `src/dopemux/cli.py:4909-4915` — `rte scan` requires `--allow-legacy-v3-scan`.
  - Defense-in-depth comment at `cli.py:4916-4918` says `run_repscan.py` independently requires the same flag.
  - `run_extraction_v5.py:2992-3020` — `enforce_live_operation_consent` requires BOTH `--execute` AND `DPMX_LIVE_OK=1` for any live-capable op (provider preflight, auth doctor, doctor, gemini model list, batch watch/retrieve, async submit, online prescan, sync phase execution).
  - `run_extraction_v5.py:3023-3076` — `enforce_pre_live_validator_for_execution` runs the v25 validator subprocess and raises on `NO_GO`, returning `SKIPPED_NO_CONSENT` when env var unset.
- **Why it matters:** The runtime fail-closed posture for live execution is rigorous. Click guard + argparse classification + env-var requirement + validator subprocess — four independent layers. This is the right shape for $-cost surfaces.

### F-OPUS-OBS-5 — Output safety redaction is comprehensive and defense-in-depth

- **Label:** `OBSERVED` (positive).
- **Evidence:** `services/repo-truth-extractor/output_safety.py:7-37, 85-130` — patterns cover OAuth bearers, AWS access keys, JWT tokens, Google API keys, GitHub PATs (`gh[pousr]_*`), GitLab PATs (`glpat-*`), generic API-key assignments via regex, `Authorization` / `x-goog-api-key` headers, `-----BEGIN ... PRIVATE KEY-----` blocks. `sanitize_text_for_provider_payload` adds extra long-token candidate redaction (`_LONG_TOKEN_CANDIDATE_RE`, line 35-37) — defense in depth before provider POST. `_SAFE_SENSITIVE_KEYS` allowlist (line 40-63) curates env-name fields that should *not* be redacted.
- **Why it matters:** This is one of the strongest redaction surfaces in the repo. The allowlist for `*_env`/`*_env_name`/`*_present` fields prevents over-redaction of audit metadata while still catching real secrets.

### F-OPUS-OBS-6 — README cost-incident anchor is exemplary operator UX

- **Label:** `OBSERVED` (positive).
- **Evidence:** `services/repo-truth-extractor/README.md:262-264` — *"⚠️ Cost warning: Each run invokes provider APIs and may incur significant charges. A single accidental run cost $10 in March 2026. Never run without explicit authorization."*
- **Why it matters:** Operator UX for risky systems is dramatically improved by *concrete* prior-incident anchors. "$10 in March 2026" is short, specific, and unforgettable — far more effective than generic "may be expensive" warnings. The pattern is worth propagating to the consent-gate error messages.

### F-OPUS-OBS-7 — `lib/proof_contract.py` enforces a tight authority-rank model

- **Label:** `OBSERVED` (positive).
- **Evidence:** `services/repo-truth-extractor/lib/proof_contract.py:119-127` — explicit `_AUTHORITY_RANK`: `runtime_authority=100`, `proof_governance_artifact=60`, `runtime_generated_evidence=50`, `generated_audit_context=40`, `external_advisory_context=30`, `sample_artifact_uncertain_lineage=20`, `unknown=0`. The classifier (`classify_artifact`, line 286-358) hard-codes `services/repo-truth-extractor/run_extraction_v5.py` as `runtime_authority` and `out/rte-pkt-*` / `proof/TP-RTE-*` as `proof_governance_artifact`.
- **Why it matters:** The authority hierarchy required by AGENTS.md §2 and re-asserted by the audit packet is *operationalised in code* — proof bundles emit `authority_boundary: "runtime source authority outranks generated proof evidence"` (line 354) as a literal string field. Generated artifacts cannot be confused for runtime truth because the bundle itself carries the rank.

### F-OPUS-OBS-8 — `is_read_only_introspection_mode` cleanly enumerates safe introspection paths

- **Label:** `OBSERVED` (positive).
- **Evidence:** `services/repo-truth-extractor/run_extraction_v5.py:2880-2895` — explicit list of 11 read-only flags (`coverage_report`, `status`, `status_json`, `tail_run_log`, `show_provider_usage`, `print_config`, `print_run_order`, `print_phase_routing`, `print_phase_prompts`, `print_promptpack`, `promptgen_scan`, `verify_phase_output`). This classification is reused by `should_enforce_pre_live_validator` (line 2849-2870) to correctly skip validator overhead on read-only paths.
- **Why it matters:** The clean separation between read-only and dispatching modes is the right shape for an operator CLI with safety-critical execution paths. The same flags appear in both helpers, ensuring consistency.

### F-OPUS-OBS-9 — `dopemux truth` deprecation message redirects to the canonical surface and dry-runs

- **Label:** `OBSERVED` (positive).
- **Evidence:** `src/dopemux/cli.py:5495-5500` — `truth_command` raises `ClickException` with explicit three-line guidance: `dopemux rte run --pipeline-version v5 --phase ALL --dry-run` / `dopemux rte preflight ...` / `dopemux rte validate-live ...`. All three redirect targets are dry-run / read-only.
- **Why it matters:** A deprecated surface that points operators to the right *safer* path is doing its job well. Worth propagating the pattern.

### F-OPUS-OBS-10 — `extractor` group invocation prints a one-line redirect echo

- **Label:** `OBSERVED` (mixed).
- **Evidence:** `src/dopemux/commands/extractor_commands.py:38-43` — when any `dopemux extractor <subcommand>` is invoked, a Click callback echoes *"`dopemux extractor` is legacy promptset tooling. Use `dopemux rte run` for canonical v5 execution."* *before* running the subcommand.
- **Why it matters:** Helpful reminder, but the echo runs *every time* the legacy group is used (including for `init` and `validate` which are still operational). The redirect chatter can become noise for operators who use those still-supported legacy commands frequently.

### F-OPUS-OBS-11 — RTE README's `first-live` preset codifies conservative defaults

- **Label:** `OBSERVED` (positive).
- **Evidence:** `services/repo-truth-extractor/README.md:147-169` — `--preset first-live` defaults `--routing-policy cost`, `--max-cost-usd 5.0`, `--partition-workers 1`, `--no-batch`, `--batch-wait-timeout-seconds 1800`. Live preset execution runs the validator first unless `--skip-pre-live-validator` is set.
- **Why it matters:** This is the right shape for staged go-live: an operator-friendly preset name (`first-live`) bundles the conservative-default set in one flag. It pairs well with the README's $10-incident anchor (F-OPUS-OBS-6).

### F-OPUS-OBS-12 — Comparison lane is explicitly non-blocking and uses separate output trees

- **Label:** `OBSERVED` (positive).
- **Evidence:** `services/repo-truth-extractor/README.md:304-385` — comparison-lane outputs are written to `raw/comparison/...` and never overwrite canonical files; comparison failures do not abort the canonical run. Resume behavior is independent.
- **Why it matters:** A feature that *adds* dual-model evidence without weakening canonical output safety. The operator UX is clean: canonical run results are unchanged by the presence of comparison runs.

### F-OPUS-OBS-13 — Six cockpit audit reports exist but none are RTE-specific

- **Label:** `OBSERVED`.
- **Evidence:** `docs/05-audit-reports/cockpit-*.md` are six files covering PM/Implementer cockpit, callable inventory, design brief, processing pack, archive intent, and ADHD lifestyle feature map — all dated 2026-04-24. They focus on the *PM* cockpit, not RTE. RTE-specific audit reports live separately under names like `rte-state-of-work-audit-20260410.md`, `rte-live-certification-gates.md`, `rte-production-certification-audit-20260414.md`, `rte-prelive-audit-pack-2026-04-23.md`, `rte-canonical-entrypoint-implementation-2026-04-23.md`, `rte-gemini-deep-pal-audit-2026-04-23.md`, `rte-branch-integration-audit-2026-04-23.md`.
- **Why it matters:** No cockpit audit pack treats RTE as a cockpit surface. RTE has runtime telemetry (`RUN_DASHBOARD.json`, `TERMINAL_TIMELINE.jsonl`, `STEP_METRICS.json`) but the existing cockpit design work treats "cockpit" as the PM cockpit, not the RTE operator cockpit. There's no operator-cockpit ergonomic baseline for RTE specifically. Whether that gap should be filled is out of scope for this audit, but worth flagging.

---

## Verification on this ledger

Run from repo root:

```bash
rg -c "^### F-OPUS-" out/rte-opus-uiux-claude-design-audit/FINDINGS_LEDGER.md
# Expected: count == total findings (CRIT + HIGH + MED + LOW + OBS)
rg -n "^- \*\*Label:\*\* " out/rte-opus-uiux-claude-design-audit/FINDINGS_LEDGER.md | rg -v "OBSERVED|INFERRED|UNKNOWN|CONFLICTING|CLAIMED|RECOMMENDED"
# Expected: zero output (no label outside the allowed taxonomy)
```

End of FINDINGS_LEDGER.md.
