---
id: METHODOLOGY
title: Methodology
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-17'
last_review: '2026-05-17'
next_review: '2026-08-15'
prelude: Methodology (explanation) for dopemux documentation and developer workflows.
---
# METHODOLOGY.md

How this audit was conducted, what was read, and the decision rules used to label evidence.

## Audit identity

- **ID:** `RTE-OPUS-UIUX-CLAUDE-DESIGN-AUDIT-001`
- **HEAD:** `a234f798947d51915b2adea3e0bc5a2917ac595b` on branch `claude/youthful-neumann-b94cc0` (worktree of `dopemux-mvp`).
- **Date:** 2026-05-16.
- **Model:** Claude Opus (executed by Claude Code harness with Plan-mode planning followed by ACT execution).
- **Mode chosen by user:** fresh independent pass with balanced weighting across five evaluation sections; durable output under `out/rte-opus-uiux-claude-design-audit/`.

## Authority order applied to every claim

From the audit packet, applied verbatim:

1. Runtime code, CLI wiring, checked-in tests, configs, active entrypoints.
2. RTE proof/status/runtime artifact writers.
3. AGENTS.md and repo governance files.
4. `TRUTH_*` and `SYSTEM_*` docs.
5. RTE docs, design docs, Claude/agent guidance, generated proof bundles.
6. Historical/generated exploratory docs.
7. External assumptions are not authority.

Generated artifacts never outrank the runtime they describe. `UNKNOWN` was never upgraded to `OBSERVED` by inference.

## Allowed labels

`OBSERVED`, `INFERRED`, `UNKNOWN`, `CONFLICTING`, `CLAIMED`, `RECOMMENDED` — used verbatim from the audit packet.

## Severity scheme

`CRIT`, `HIGH`, `MED`, `LOW`, `OBS`. Matches prior P0–P5 convention so the output is legible to anyone who's read those, but finding IDs are independent (`F-OPUS-{SEV}-{N}`) per the user's "fresh independent pass" decision.

## Five evaluation sections (balanced ~20% each)

1. **Operator CLI surfaces** — every `dopemux rte` subcommand, `extractor` deprecated surfaces, hidden argparse introspection flags, consent gates, default-safe semantics.
2. **Proof/dashboard/risk surfaces** — `RUN_DASHBOARD.json`, `STEP_METRICS.json`, `FAILURE_INDEX.json`, `SPEND_LEDGER.json`, `PROOF_PACK.json`, `RTE_RISK_DASHBOARD.json`, `TERMINAL_TIMELINE.jsonl`, `RUN_ROUTING_FINGERPRINT.json`; writers in `reporting.py`, `lib/proof_contract.py`, `lib/risk_dashboard.py`, `lib/spend_ledger.py`; redaction in `output_safety.py`; consent in `run_extraction_v5.py:2880-3076`.
3. **Claude/design adjacency** — `AGENTS.md`, all four `CLAUDE.md` variants, `brand-voice-guidelines.md`, `ux-style-guide.md`, `cli-ux-design-spec.md`, `terminal-rendering-guide.md`, cockpit audit reports, `proof/` artifacts, task packets, governance docs.
4. **Terminal ergonomics** — Click help text quality, JSON-vs-human output, `--watch` / `--tail-run-log`, voice consistency, status chips, render modes, ADHD optimisations.
5. **Error states** — `ClickException` paths, `enforce_live_operation_consent`, `enforce_pre_live_validator_for_execution`, `validate_pre_live_gate_v25.py` reason codes, failed sidecar redaction, hygiene/dry-run violations.

## Files inspected (read-only)

### Tier 1 — runtime (full reads or targeted ranges)

| File | Lines | Coverage |
|------|------:|----------|
| `src/dopemux/cli.py` | 6250 | 4830–5570 (RTE region) |
| `src/dopemux/commands/extractor_commands.py` | 523 | full |
| `services/repo-truth-extractor/run_extraction_v5.py` | 22547 | targeted (lines ~2780–3130 consent/sidecar/validator; grep on add_argument and key handlers) |
| `services/repo-truth-extractor/output_safety.py` | 206 | full |
| `services/repo-truth-extractor/rte_config.py` | 141 | full |
| `services/repo-truth-extractor/lib/proof_contract.py` | 549 | full |
| `services/repo-truth-extractor/lib/risk_dashboard.py` | 615 | full |
| `services/repo-truth-extractor/lib/spend_ledger.py` | 602 | partial (1–602 dataclasses and accumulators) |
| `services/repo-truth-extractor/reporting.py` | 1093 | partial (1–200) |
| `services/repo-truth-extractor/validate_pre_live_gate_v25.py` | 1375 | partial (1–300) |

### Tier 3 — governance

| File | Coverage |
|------|----------|
| `AGENTS.md` | full |
| `README.md` | full |
| `ARCHITECTURE.md` | full |

### Tier 5 — docs / Claude / design

| File | Coverage |
|------|----------|
| `.claude/CLAUDE.md` (root) | full (via system-reminder injection plus targeted Read) |
| `.claude/claude.md` (case variant) | full |
| `services/.claude/CLAUDE.md` | full (via system-reminder injection) |
| `src/.claude/CLAUDE.md` | full (via system-reminder injection) |
| `.claude/brand-voice-guidelines.md` | full |
| `docs/ux/ux-style-guide.md` | full |
| `docs/ux/terminal-rendering-guide.md` | full |
| `docs/04-explanation/branding/cli-ux-design-spec.md` | full |
| `docs/05-audit-reports/cockpit-pm-implementer-processing-pack-2026-04-24.md` | first 120 lines |
| `services/repo-truth-extractor/README.md` | full |

### Tier 6 — historical / generated audit reports

Surveyed by `ls` and grep; not read in depth:

- `docs/05-audit-reports/cockpit-*-2026-04-24.md` (6 files)
- `docs/05-audit-reports/rte-*.md` (7 files)
- `docs/05-audit-reports/supervisor-*.md` (4 files)
- `docs/05-audit-reports/repo-*.md` (8 files)

## Search commands used

```bash
git rev-parse HEAD
git status --short --branch
wc -l <runtime files>
ls <governance/design files>
find docs/04-explanation -iname '*cli-ux*'
rg -n "READY_FOR_CLAUDE|safe_for_claude|claude_design" .
rg -n "def main\(|def enforce_live|def enforce_pre|class SpendTracker" services/repo-truth-extractor/run_extraction_v5.py
grep -n "READY_FOR_CLAUDE\|safe_for_claude\|claude_design\|not approved" docs/05-audit-reports/*.md
ls docs/05-audit-reports/
```

No tests were executed. No provider calls were made. No code was changed. `git status` at the end of the audit confirms only files under `out/rte-opus-uiux-claude-design-audit/` are new.

## Decision rules used during the audit

1. **Generated artifacts never outrank runtime.** A claim in `*.proof.json` that disagrees with `run_extraction_v5.py` is `CONFLICTING`, never `OBSERVED` as if the proof bundle were authoritative.
2. **UNKNOWN is preserved, not promoted.** If runtime emit paths could not be exhaustively verified from static reading, the audit records `UNKNOWN` (see `F-OPUS-LOW-2`).
3. **Self-demoted documents still count.** A file that says "I am not authoritative" but continues to prescribe behavior is still teaching the reader something. The audit treats self-demotion as a partial mitigation, not full erasure (see `F-OPUS-HIGH-2`).
4. **Truth-order conflicts are surfaced, not resolved.** When `AGENTS.md`, `README.md`, and `brand-voice-guidelines.md` disagree, the audit records the conflict and lets reconciliation happen elsewhere (see `F-OPUS-CRIT-2`).
5. **Phase 1 agent reports are not authority.** When the Phase 1 Explore agent claimed `READY_FOR_CLAUDE_DESIGN: not approved` flags existed, a `grep` showed they did not. The audit corrected the record and recorded the meta-finding (`F-OPUS-OBS-1`).
6. **Severity reflects operator impact, not aesthetic preference.** A brand-voice violation in help text is `CRIT` not because the prose is bad in isolation, but because it teaches operators to expect hype from a system whose other safety properties depend on terse evidence-based output.

## What this audit did NOT do

- Did not run `dopemux rte run` or any RTE command.
- Did not run any `pytest` suite.
- Did not call any LLM provider.
- Did not submit, poll, retrieve, or cancel any batch job.
- Did not require provider credentials.
- Did not edit any source file outside `out/rte-opus-uiux-claude-design-audit/`.
- Did not merge, rebase, push, or open PRs.
- Did not claim live provider behavior.
- Did not collapse RTE into broader Dopemux authority.
- Did not cross-reference `F1-*` through `F5-*` finding IDs from prior P0–P5 audits (per user's "fresh independent pass" decision).
- Did not implement, mockup, or design UI changes.

## Reproducibility

To reproduce this audit at the same HEAD:

```bash
cd <repo-or-worktree>
git checkout a234f798947d51915b2adea3e0bc5a2917ac595b
# Read the files listed in METHODOLOGY.md §Files inspected.
# Apply the decision rules in §Decision rules used.
# Produce the seven output files under out/rte-opus-uiux-claude-design-audit/.
```

The output files are intended to be self-contained — a reader should be able to verify any finding by following the cited `file:line` references at the current HEAD.

End of METHODOLOGY.md.
