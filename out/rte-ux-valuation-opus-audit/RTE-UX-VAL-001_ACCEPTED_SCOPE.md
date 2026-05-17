# RTE-UX-VAL-001 Accepted Scope

## Accepted Next

1. `RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001`
1. `RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001`
1. `RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001`
1. `RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001`
1. `RTE-UX-PKT-RUN-HELP-PROGRESSIVE-DISCLOSURE-001`

## What These Packets Cover

- Truth-order reconciliation across the checked-in authority docs.
- Claude and agent guidance that makes the RTE safety invariants explicit.
- CLI tone cleanup so operator-facing copy matches the repo's brand-voice contract.
- Pre-live validator failure phrasing so blocked runs fail clearly instead of collapsing into a generic one-liner.
- Progressive disclosure for `dopemux rte run --help` so the command surface is readable without changing execution behavior.

## Accepted Later

1. `RTE-UX-PKT-UX-DOC-CLEANUP-001`
1. `RTE-UX-PKT-ARCHITECTURE-UPGRADES-RECONCILIATION-001`
1. `RTE-UX-PKT-V5-PROMPTSET-AUDIT-STRATEGY-001`
1. `RTE-UX-PKT-DPMX-LIVE-OK-HINTS-001`

## Scope Boundaries

- No runtime dispatch changes.
- No provider calls.
- No promptset/schema edits yet.
- No pricing or routing edits yet.
- No merge or branch choreography from this packet.

## Evidence Basis

- `AGENTS.md` and `.claude/PROJECT_INSTRUCTIONS.md` both require evidence-first, deterministic change control.
- `.claude/brand-voice-guidelines.md` requires terse operator output on production surfaces.
- `src/dopemux/cli.py` still uses ritualized emoji-heavy operator text in the RTE and truth surfaces.
- `services/repo-truth-extractor/validate_pre_live_gate_v25.py` uses structured JSON internally, but the CLI wrapper still collapses failure into a generic `ClickException`.
- `services/repo-truth-extractor/README.md` and the RTE how-to docs already distinguish canonical operator paths from legacy compatibility surfaces.
