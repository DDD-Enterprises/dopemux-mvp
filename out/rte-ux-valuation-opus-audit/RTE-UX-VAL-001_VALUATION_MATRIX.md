# RTE-UX-VAL-001 Valuation Matrix

Source truth note: the local checkout does not contain `out/rte-opus-uiux-claude-design-audit/`, so the finding ids below use the packet's ordering and counts as the best local approximation. Runtime and docs evidence came from `AGENTS.md`, `.claude/PROJECT_INSTRUCTIONS.md`, `.claude/brand-voice-guidelines.md`, `src/dopemux/cli.py`, `services/repo-truth-extractor/README.md`, `services/repo-truth-extractor/validate_pre_live_gate_v25.py`, and the RTE how-to docs.

Net priority formula: `(operator safety + agent safety + dependency priority) - implementation risk`

| recommendation id | finding id | title | operator safety | agent safety | dependency priority | implementation risk | effort | net priority | decision | packet order | accepted/deferred/rejected | rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-OPUS-2 | CRIT-2 | Truth-order reconciliation | 5 | 5 | 5 | 3 | M | 12 | ACCEPT_NEXT | 1 | accepted | `AGENTS.md`, `.claude/PROJECT_INSTRUCTIONS.md`, and `truth-canonicals.md` disagree on authority order. This is the spine fix; every later packet inherits from it. |
| R-OPUS-3 | CRIT-3 | Claude/RTE safety guidance | 5 | 5 | 5 | 3 | M | 12 | ACCEPT_NEXT | 2 | accepted | The current agent-facing guidance does not clearly teach the RTE safety invariants. This needs to land before other operator copy changes. |
| R-OPUS-14 | CRIT-3 | Claude/RTE safety guidance companion | 4 | 5 | 4 | 2 | S | 11 | ACCEPT_NEXT | 2 | accepted | Bundled with the safety-guidance packet because it reinforces the same authority rules with lower direct operator impact. |
| R-OPUS-1 | CRIT-1 | CLI tone cleanup | 4 | 4 | 4 | 2 | M | 10 | ACCEPT_NEXT | 3 | accepted | `src/dopemux/cli.py` still emits ritualized, emoji-heavy operator copy where `.claude/brand-voice-guidelines.md` calls for terse, procedural output. |
| R-OPUS-4 | CRIT-1 | CLI emoji cleanup | 3 | 2 | 3 | 1 | S | 7 | ACCEPT_NEXT | 3 | accepted | Narrow follow-on to the tone packet. Lower impact than the voice rewrite, but still worth bundling while the CLI surface is open. |
| R-OPUS-8 | HIGH-1 | Pre-live validator error shape | 4 | 4 | 4 | 2 | M | 10 | ACCEPT_NEXT | 4 | accepted | `validate_pre_live_gate_v25.py` already produces structured outputs, but the CLI wrapper still reduces failure to a single `ClickException`. That is operator-visible safety debt. |
| R-OPUS-9 | HIGH-2 | Progressive disclosure for `dopemux rte run --help` | 4 | 3 | 4 | 2 | M | 9 | ACCEPT_NEXT | 5 | accepted | The current `rte run` surface exposes a dense flag wall. Progressive disclosure reduces operator overload without changing runtime behavior. |
| R-OPUS-5 | HIGH-3 | UX doc cleanup | 3 | 2 | 3 | 2 | S | 6 | ACCEPT_LATER | 6 | accepted | Useful documentation normalization, but lower leverage than the authority and gate packets above it. |
| R-OPUS-6 | HIGH-3 | UX doc cleanup companion | 3 | 2 | 3 | 2 | S | 6 | ACCEPT_LATER | 6 | accepted | Companion doc clean-up. Same value class as R-OPUS-5, so it should travel in the same later packet. |
| R-OPUS-10 | HIGH-4 | Architecture command reconciliation | 3 | 3 | 3 | 2 | M | 7 | ACCEPT_LATER | 7 | accepted | The repo already documents `dopemux rte` as canonical, but the remaining architecture/alias story still needs a reconciliation packet once the authority spine is fixed. |
| R-OPUS-11 | HIGH-4 | Upgrades command reconciliation | 3 | 3 | 3 | 2 | M | 7 | ACCEPT_LATER | 7 | accepted | Companion alias cleanup for `dopemux upgrades`. This is important, but it is downstream of the authority and safety packets. |
| R-OPUS-7 | HIGH-5 | V5 promptset audit strategy | 2 | 3 | 2 | 2 | M | 5 | ACCEPT_LATER | 8 | accepted | Strategic, but not on the critical path for operator safety. Best left until the higher-risk copy and gate packets settle. |
| R-OPUS-15 | HIGH-6 | DPMX_LIVE_OK help/deprecation hints | 2 | 2 | 2 | 1 | S | 5 | ACCEPT_LATER | 9 | accepted | Helpful hinting around the live gate, but it is a refinement after the main authority and help-text cleanup work. |
| R-OPUS-19 | HIGH-6 | DPMX_LIVE_OK help/deprecation hints companion | 2 | 2 | 2 | 1 | S | 5 | ACCEPT_LATER | 9 | accepted | Companion hinting/deprecation item. Bundle with R-OPUS-15. |

## Scoring Notes

- The top three finding ids are grounded in the packet text.
- The `HIGH-1` through `HIGH-6` labels are inferred from the packet's sequencing hint and count.
- `IMPLEMENTATION_RISK` stays low because the approved sequence is still docs/CLI text work, not runtime dispatch or provider behavior changes.
- `ACCEPT_LATER` here means "approved in sequence, but not part of the first implementation packet."
