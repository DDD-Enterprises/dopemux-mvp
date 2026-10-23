# dopemux-route-ledger

dopemux-route-ledger is a read-only Claude Code mod that keeps a ledger of delegation. It records which model each Agent call asked for, which model each model step reported back in the API response, and every advisor server-tool-use, then shows the result as a status segment, as toasts when an advisor budget is exceeded, and as a `/route-ledger` table (alias `/route`). Each record is also written as a JSONL receipt that a supervisor can merge into an ExecutionBinding.

## What it shows

- Status segment, for example `agents S×4 H×2 · advisor 1`. Agents appear in the fixed order S (sonnet), O (opus), H (haiku), F (fable), then `?` for any other or unknown model, and only the non-zero ones; with none the segment reads `agents –`. `advisor N` appears when N > 0 and becomes `advisor N/B ⚠` once a budget B applies and is exceeded. ` · ledger off` is appended when receipts are disabled and ` · receipts ✗` when a receipt write failed. The line is redrawn at most about once per half second.
- Toasts. A subagent whose advisor count exceeds `childAdvisorBudget` toasts once, naming a shortened agent id, the count and the budget. The session toasts once when its total exceeds `sessionAdvisorBudget`. An Agent call with no model pinned also toasts once (`unpinnedAgent`). The toasts say the mod counts advisor calls and cannot block them.
- `/route-ledger` prints a table, one row per loop (`main`, then one per subagent, at most 60 rows then `+N more`) with the columns `agent | runner | model requested | model observed | effort requested | match | advisor`. Unknown cells read `UNKNOWN`. `/route-ledger receipts` prints the receipt file, the receipt counts and `receiptsEnabled` / `receiptsFailed`. Any other argument prints a one-line usage. The command never writes, spawns or reads outside its own state.
- `/route` is an alias with identical output.

## Load it

```
claude --plugin-dir plugins/dopemux-route-ledger
```

Check it offline with `claude plugin validate plugins/dopemux-route-ledger` and `claude plugin test plugins/dopemux-route-ledger`.

## Options (`userConfig`)

| key | default | meaning |
| --- | --- | --- |
| `receiptDir` | `.control-tower/state/route-ledger` | Where `<sessionId>.jsonl` files go. The default is used only when `.control-tower/state` exists; an explicit directory is created on first write. A `..` segment disables receipts. |
| `unpinnedAgent` | `warn` | `warn` toasts once per Agent call with no model pinned (forks excepted); `off` records only. |
| `childAdvisorBudget` | `0` | Advisor calls allowed per child agent. 0 means a child's first call exceeds it; a negative number turns the check off. |
| `sessionAdvisorBudget` | `-1` | Advisor calls allowed per session; -1 turns it off. |
| `maxReceiptsPerFile` | `500` | 50 to 5000; a new `<sessionId>.<n>.jsonl` segment starts after this many. |

## Receipts

Receipts are JSONL under `receiptDir`, one file (segment) per session, named `<sessionId>.jsonl`, then `<sessionId>.1.jsonl` and so on. Three kinds exist: `agent_request` (the requested model and effort, joined to the spawned agent id and resolved model when `agent.spawn` fires), `step_observed` (requested versus the API-reported `usage.model`, with token usage) and `advisor_call`. The format is defined by `receipt.schema.json`. Prompts, file contents and tool output never enter a receipt.

`agent_request` and `step_observed` receipts carry `binding_fields`, a partial mapping a supervisor can merge into an ExecutionBinding:

- `selection` = `{ runner: "claude-code-agent", model, effort }` from what was requested
- `effort_requested` = the requested effort, or `UNKNOWN`
- `effort_observed` = always `UNKNOWN` (the API does not report effort)
- `response_claimed_model` = the API-reported model, or `UNKNOWN`
- `provider_attested_model` = always `UNKNOWN`
- `independence_class` = always `UNKNOWN`

A receipt is not a valid binding: the mod knows only these fields. A supervisor merges the receipts into a binding and runs `ct bind-record`; the mod never does.

## Limits

- It counts advisor calls after the fact. It cannot block, deny or retry any call.
- The observed model is what the API response claimed (`response_claimed`), not provider attestation. Effort observed is UNKNOWN.
- A fork inherits its parent's model, so a fork with no model is recorded as inheriting, not as unpinned.
- The plugin API is early access and may change between Claude Code builds.
- `/route` may collide with a built-in or another plugin's command in some builds. If it is refused, use `/route-ledger`, which is registered independently and keeps working.
- The mod pins its own status line. Whether it coexists with another plugin's status line (for example dopemux-pulse) is unverified and was not run.
- The mod is read-only toward the repository except its own receipt files under `receiptDir`. It makes no network, process or model call.
- Not run yet: a live Claude Code session loading the mod. Offline tests only.
