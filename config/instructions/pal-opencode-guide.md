# PAL for OpenCode

Use PAL tools as workflow gates, not decoration.

## Cost-first workflow

Load AGENTS.md §5 and docs/03-reference/governance/evidence-economy.md. Their risk lanes govern model-call budgets; no mandatory repetitive model chain. Deterministic preflight → one bounded implementer → focused validation → frozen head → one independent final audit only for L2/L3 → precommit/proof. PAL tools remain optional or explicitly packet-required.

Choose cheapest adequate qualified model and lowest sufficient supported effort. Pin documented per-agent/per-invocation model selectors before bounded delegation; verify actual identity. Full inherited supervisor context must not accidentally retain its expensive model. Keep decisions/finality with supervisor. Report missing delegation/model/effort controls; no unsupported runtime keys or hidden fallback. Preserve packet restrictions, approval gates, ownership/validation/stop conditions, and recorded bounded escalation. YAML is advisory, not a router.

## Rules

- **Do not** use `planner` before validated understanding (MEDIUM+ confidence).
- **Do not** implement before plan challenge.
- **Do not** use `consensus` unless there are at least two credible approaches.
- **Do not** use `debug` unless there is a failure, contradiction, or concrete uncertainty.
- **Do not** call completion without evidence.

## Tool Usage

| Tool            | When to Use                                      | Output Requirements                     |
|-----------------|--------------------------------------------------|-----------------------------------------|
| `pal_thinkdeep` | Hidden coupling, second-order effects, architecture risk | Evidence ledger + assumptions           |
| `pal_planner`   | Only after understanding reaches MEDIUM          | Phased breakdown + validation gates     |
| `pal_consensus` | Expensive or reversible design forks             | For/against/neutral synthesis           |
| `pal_debug`     | Concrete failure or contradiction                | Root cause + reproduction steps         |
| `pal_codereview` | Optional advisory review within lane budget | Quality, security, performance findings |
| `pal_precommit` | Optional; deterministic precommit always required | Checklist + residual risk |
| `pal_challenge` | Explicit requirement or recorded budget justification | Attack assumptions + failure modes |

## Required Output Shape (every PAL stage)

Every response from a PAL tool must contain:

- **Summary** — one sentence
- **Evidence Ledger** — what was inspected
- **Assumptions** — what is being taken as given
- **Confidence** — exploring / low / medium / high / certain
- **Next Action** — concrete next step (or stop)

## Lazy-Load Deeper Doctrine

Only when needed:

- `docs/03-reference/execution/pal-execution-rules.md`
- `docs/03-reference/execution/pal-chaining-doctrine.md`
