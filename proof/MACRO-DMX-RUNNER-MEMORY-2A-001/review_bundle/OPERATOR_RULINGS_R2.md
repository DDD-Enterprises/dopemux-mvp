# MACRO-DMX-RUNNER-MEMORY-2A-001 — Operator Rulings for R2

**Recorded**: 2026-10-31 by the team lead, after J01-GATE held W01-W08 (`J01_GATE.md`). Each ruling is the operator's chosen option, verbatim, with the question it answered.

| # | Question (verbatim) | Operator's answer (verbatim) |
|---|---|---|
| 1 | "W01 and W02 must edit dope-memory and ConPort source, but the DCP red lane blocks Claude Code from those folders. How should Wave 2A get past it?" | "Narrow carve-out ADR (Recommended)" |
| 2 | "Upstream task-orchestrator 4.0.0 isn't released (latest is v3.16.0), and 4.0 drops every tool our /dx commands call. What happens to the orchestrator part (W05)?" | "Split it out (Recommended)" |
| 3 | "Some writers (hooks, the capture client) write SQLite or Redis directly and can't carry a token, and about 15 other in-repo callers write ConPort's REST API. What should 'verified identity on every write' (G2) cover?" | "HTTP writes only (Recommended)" |

## What each option meant when chosen (the option descriptions shown to the operator)

1. **Narrow carve-out ADR**: "A new ADR in the ADR-224/226 pattern allows exactly the files these workstreams name, for this macro only. That keeps the guard and records the exception."
2. **Split it out**: "Wave 2A ships memory identity (dope-memory, ConPort, tokens, bridge, generator) so Codex gets memory now. The orchestrator becomes its own wave once 4.0.0 is out, with the tool-surface migration planned."
3. **HTTP writes only**: "Every HTTP write to dope-memory and ConPort is verified. Local file and Redis writers are recorded as self-asserted internal principals. The ~15 REST callers get tokens in a widened workstream before enforce mode is switched on."

## Consequences for R2 (supervisor's, to be issued; nothing dispatched)

- The design is revised (a new design revision with its own sha256; the R1 design stays as the R1 record). Its approval and R2's execution need a new operator authorization.
- The carve-out ADR is drafted as a deliverable; the operator accepts its text before any workstream edits a red-lane path.
- The orchestrator (R1 W05, the orchestrator gate check in W06, the cross-repo :7890 cutover) leaves Wave 2A.
- G2 is re-worded; the ConPort REST callers W00 found become an in-scope workstream.
- R1's packets, W00 findings and this record stay unchanged.
