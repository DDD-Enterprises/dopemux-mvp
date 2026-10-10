---
id: UX_RISK_LEDGER
title: Ux Risk Ledger
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-17'
last_review: '2026-05-17'
next_review: '2026-08-15'
prelude: Ux Risk Ledger (explanation) for dopemux documentation and developer workflows.
---
# UX_RISK_LEDGER.md

Prioritized operator-experience risk ledger. Risks are operator-impact-ordered. Each row names the trigger condition, the operator harm, the mitigation already in place (if any), and the residual gap.

Risks are not the same as findings — a risk can exist *because* a finding exists, but several risks predate any specific finding (e.g., the inherent risk of a 22,547-line runtime). The ledger answers "where does an operator most likely get hurt?" not "what is broken."

---

## R-UX-1 — Operator runs RTE live without realizing `DPMX_LIVE_OK=1` exists

- **Trigger:** Operator reads `dopemux rte run --help`, sees `--execute` flag, runs `dopemux rte run --execute`.
- **Harm:** Consent gate refuses with `parser.error(...)` listing `DPMX_LIVE_OK=1` as missing. Operator either (a) sets the env var and re-runs without reading further safety material, or (b) gives up confused.
- **Mitigation in place:** Hard gate at `run_extraction_v5.py:3008-3019` refuses to dispatch. Error message names the missing consent.
- **Residual gap:** The `--help` text for `dopemux rte run` does not mention `DPMX_LIVE_OK=1`. Operators discover the env var only by hitting the wall. (`F-OPUS-MED-6`)
- **Operator-harm tier:** **high** — concerns the most expensive surface.

## R-UX-2 — Operator reads "Spaceage Operationalism" style guide and ships UI with `[READY]`/`[BLOCKED]`/`[DEFERRED]`/`[SUPERVISED]` chips

- **Trigger:** Contributor or Claude agent searching for UX guidance lands in `docs/ux/ux-style-guide.md` (it's the obvious file by name and path).
- **Harm:** They follow the prescribed status chip set + green/red/yellow/blue palette, which is incompatible with the runtime `[LIVE]/[BLOCKER]/[OVERRIDE]/[LOGGED]/[AFTERCARE]/[EDGE]` chips and the mint/pink/violet palette. Result: drift between the new surface and the runtime brand.
- **Mitigation in place:** A single self-demotion line at `docs/ux/ux-style-guide.md:14-15` redirects to `cli-ux-design-spec.md`.
- **Residual gap:** The body of the file (16 substantive lines) keeps prescribing the deprecated palette in imperative tone. Self-demotion + opposing prescription is fragile. (`F-OPUS-HIGH-2`)
- **Operator-harm tier:** **medium-high** — visible in every new contributor's first design-pass and likely to compound.

## R-UX-3 — Operator copies CLI help-text prose into operator runbooks

- **Trigger:** Operator writes a runbook for a teammate, copy-pastes `dopemux rte run --help` output.
- **Harm:** Runbook now contains brand-voice violations (`Ignite Pipeline`, `Engages the high-fidelity extraction engines`, `Ritual Apothecary`, `ritual session`, `cockpit telemetry`). New teammate either (a) learns to expect this register everywhere, or (b) becomes confused about whether RTE is a serious operations tool. (`F-OPUS-CRIT-1`)
- **Mitigation in place:** `brand-voice-guidelines.md` §2A is the production spec, and `brand_lint.py` enforces it for some files.
- **Residual gap:** Click docstrings/help text appear to be outside the lint surface. The hype-voice gets through.
- **Operator-harm tier:** **medium-high**.

## R-UX-4 — Claude agent runs RTE without internalizing safety invariants

- **Trigger:** A Claude or Codex agent is asked to "extend the RTE preflight command" and loads `.claude/CLAUDE.md` for project context.
- **Harm:** None of the four `CLAUDE.md` files in the repo (`.claude/`, `services/.claude/`, `src/.claude/`, and the lowercase variant) mention `DPMX_LIVE_OK`, consent gates, or spend caps. The agent must derive these invariants from runtime code. If the agent doesn't read `run_extraction_v5.py:2992-3076` carefully, it may propose changes that weaken consent. (`F-OPUS-CRIT-3`)
- **Mitigation in place:** AGENTS.md §6 line 81 scopes RTE outputs; the runtime code is comprehensive and grep-discoverable.
- **Residual gap:** Nothing in the Claude-facing material teaches the safety contract proactively.
- **Operator-harm tier:** **high** — agents acting on RTE without context is the single largest *new* risk surface introduced by Claude/agent integration.

## R-UX-5 — Operator runs `dopemux rte promptset audit` on canonical v5 promptset and is refused

- **Trigger:** Operator follows the canonical command guide, runs `dopemux rte promptset audit` on a v5 promptset.
- **Harm:** `ClickException("Promptset audit is implemented for v4 only.")`. Operator either tries `--pipeline-version v4` (wrong engine) or gives up. The pre-flight audit they wanted is unavailable. (`F-OPUS-HIGH-4`)
- **Mitigation in place:** Error message names "v4 only."
- **Residual gap:** No fallback to a v5-equivalent audit; no doc that says "v5 promptsets are audited differently — try X."
- **Operator-harm tier:** **medium**.

## R-UX-6 — Pre-live validator NO_GO produces an unstructured stderr line

- **Trigger:** Operator runs `dopemux rte run --execute` after setting `DPMX_LIVE_OK=1`; the v25 validator returns NO_GO.
- **Harm:** A `RuntimeError("Pre-live validator blocked live execution: verdict=NO_GO_CODE reason_codes=CRITICAL_TEST_FAILURE output_dir=/path/...")` propagates. No problem/why/fix structure, no `[BLOCKER]` chip, no actionable next step beyond "read the output_dir." Operator has to open the output directory and find `VALIDATION_REPORT.json` to know what to fix. (`F-OPUS-HIGH-5`)
- **Mitigation in place:** The validator does write a structured `VALIDATION_REPORT.json`; the error message includes the path.
- **Residual gap:** The error message is not in the `error_panel(problem, why, fix)` shape the brand-voice spec mandates. The reason codes are stringified into one line rather than separated by purpose. The next-step is implicit.
- **Operator-harm tier:** **medium-high** — this is the *most consequential* error path in RTE.

## R-UX-7 — Operator scans 33-flag help text and misses a critical option

- **Trigger:** Operator runs `dopemux rte run --help`.
- **Harm:** ~33 Click options dumped in flat list. Critical safety options (`--max-cost-usd` not present in the rte run signature itself, `--allow-multi-phase-live-batch`, `--prescan-online`, `--allow-online-llm`) sit alongside cosmetic flags (`--ui`, `--pretty`, `--quiet`). Operators scan and miss the one they need. (`F-OPUS-HIGH-6`)
- **Mitigation in place:** Click does its standard help formatting.
- **Residual gap:** No progressive disclosure (`--verbose`/`--debug` for extended help), no grouping by safety vs cosmetic vs routing, no scan-friendly summary at the top.
- **Operator-harm tier:** **medium**.

## R-UX-8 — Operator discovers `dopemux rte wizard` and invokes it without context

- **Trigger:** Operator runs `dopemux rte --help`, sees `wizard` in the subcommand list, runs `dopemux rte wizard` curiously.
- **Harm:** Behavior is the `audit.commands["wizard"]` registered at `cli.py:5516` — undocumented in README.md or AGENTS.md. Operator has no idea what they're starting. (`F-OPUS-MED-4`)
- **Mitigation in place:** The wizard sub-app may have its own help text (not inspected here).
- **Residual gap:** Documentation gap.
- **Operator-harm tier:** **low-medium**.

## R-UX-9 — Operator confuses `dopemux upgrades run` and `dopemux rte run` as different commands

- **Trigger:** Operator reads ARCHITECTURE.md §5.5 (still mentions `dopemux upgrades`), runs `dopemux upgrades run`, then later reads README.md §4 saying use `dopemux rte run`.
- **Harm:** Two command paths, same behavior. Operator may try one, see something they don't recognize, try the other, get the same thing, and become uncertain about whether they're using the canonical path. Documentation drift compounds the confusion. (`F-OPUS-MED-1`, `F-OPUS-MED-2`)
- **Mitigation in place:** Both paths produce identical behavior (canonical commands aliased into both Click groups).
- **Residual gap:** ARCHITECTURE.md needs the deprecation note; eventual `upgrades` removal needs a plan.
- **Operator-harm tier:** **low-medium**.

## R-UX-10 — Operator uses `dopemux extractor status` in either mode without realizing it has two

- **Trigger:** Operator runs `dopemux extractor status` (no flags) hoping for runtime status.
- **Harm:** Gets a `SYNC_MANIFEST.json` reading from a generated promptset, not the run status they wanted. With flags they get a deprecation pointing to `dopemux rte status`. Either way the behavior is not what an operator hoping for "show me what's happening with my run" expects. (`F-OPUS-MED-3`)
- **Mitigation in place:** Docstring partially explains.
- **Residual gap:** Dual-mode commands need explicit framing.
- **Operator-harm tier:** **low**.

## R-UX-11 — Operator misreads spend cap floats as something other than USD

- **Trigger:** Operator runs `dopemux rte validate-live --help`, sees `--provider-probe-max-usd 0.10` defaults.
- **Harm:** A tired or non-English-first operator may briefly misread the float-without-unit. Compounded by adjacent `--provider-probe-max-minutes` (also a float, also unit-bearing-via-name). (`F-OPUS-LOW-1`)
- **Mitigation in place:** Flag name has `-usd` suffix.
- **Residual gap:** Help description doesn't restate the unit.
- **Operator-harm tier:** **low**.

## R-UX-12 — Empty terminal-rendering-guide.md misleads operators looking for it

- **Trigger:** Operator searches `docs/ux/` for terminal-rendering reference, finds `terminal-rendering-guide.md`, opens it.
- **Harm:** File has only frontmatter; no body content. Operator wastes time, then must find the actual rendering specifics elsewhere (`cli-ux-design-spec.md §7 Render Modes`). (`F-OPUS-HIGH-3`)
- **Mitigation in place:** None.
- **Residual gap:** Either delete the stub or write the content.
- **Operator-harm tier:** **low**.

## R-UX-13 — Cockpit audit reports look like specifications

- **Trigger:** A contributor or Claude agent searches `docs/05-audit-reports/` for cockpit design and finds six 2026-04-24 cockpit-pm-implementer-* reports.
- **Harm:** Files are long, structured, headed with "Authority map" / "Callable Surface Inventory" — they read like specs. The "evidence pack only, do not implement" caveat is prose at the head, not a structured frontmatter flag. An impatient reader (or an agent that summarizes rather than reads) could miss it. (`F-OPUS-MED-7`)
- **Mitigation in place:** Verdict prose at top of each file.
- **Residual gap:** Structured frontmatter flag would make the caveat machine-checkable.
- **Operator-harm tier:** **medium**.

## R-UX-14 — Brand-voice conformance for runtime emitters is partially unverifiable from static reading alone

- **Trigger:** Audit tries to confirm that every CLI/agent emit ends with `NEXT:` / `Receipt:` / `PROGRESS` per `brand-voice-guidelines.md` §3.5.
- **Harm:** Static reading shows the rule but cannot exhaustively verify every emit path. Some are obviously compliant (the truth-deprecation message ends with three example commands functioning as a NEXT). Others are not (the consent-gate `parser.error(...)` at run_extraction_v5.py:3015-3019). (`F-OPUS-LOW-2`)
- **Mitigation in place:** `brand_lint.py` audits a defined set of files; runtime wrapper `validate_or_fallback()` exists.
- **Residual gap:** Audit cannot say from static reading whether the closer rule is consistently met across all RTE runtime emitters. Recorded as `UNKNOWN`.
- **Operator-harm tier:** **low** (audit-completeness risk, not operator-harm).

---

## Risk-tier rollup

| Tier | Count | Risk IDs |
|------|------:|----------|
| high | 2 | R-UX-1, R-UX-4 |
| medium-high | 3 | R-UX-2, R-UX-3, R-UX-6 |
| medium | 4 | R-UX-5, R-UX-7, R-UX-13, (R-UX-2 also slots here) |
| low-medium | 2 | R-UX-8, R-UX-9 |
| low | 4 | R-UX-10, R-UX-11, R-UX-12, R-UX-14 |

The two `high` risks (`R-UX-1`, `R-UX-4`) deserve attention first because they concern the most consequential operator/agent paths — live execution discovery and Claude-agent safety priming.

End of UX_RISK_LEDGER.md.
