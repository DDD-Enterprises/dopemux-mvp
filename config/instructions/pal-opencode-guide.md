# PAL for OpenCode

Use PAL tools as workflow gates, not decoration.

## Core Chain (non-trivial repo work)

```
analyze → thinkdeep → challenge → planner → challenge → codereview → precommit → challenge
```

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
| `pal_codereview`| After diff stabilizes                            | Quality, security, performance findings |
| `pal_precommit` | Before any commit                                | Checklist + residual risk               |
| `pal_challenge` | Before advancing any major phase                 | Attack assumptions + failure modes      |

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
