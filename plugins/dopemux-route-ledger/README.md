# dopemux-route-ledger

dopemux-route-ledger is a read-only Claude Code mod that keeps a ledger of delegation. It records which model each Agent call asked for, which model each model step reported back in the API response, and every advisor server-tool-use, then shows the result as a status segment, as toasts when an advisor budget is exceeded, and as a `/route-ledger` table (alias `/route`). Each record is also written as a JSONL receipt that a supervisor can merge into an ExecutionBinding.

## What it shows

- Status segment, for example `agents S×4 H×2 · advisor 1`. Agents appear in the fixed order S (sonnet), O (opus), H (haiku), F (fable), then `?` for any other or unknown model, and only the non-zero ones; with none the segment reads `agents –`. `advisor N` (the session total) appears when N > 0 and becomes `advisor N/B ⚠` once `sessionAdvisorBudget` B applies and N exceeds it. A separate ` · child M/B ⚠` segment appears once the busiest child agent's count M exceeds `childAdvisorBudget` B, so a clean agent never makes the session total look like a child overage. ` · ledger off` is appended when receipts are disabled and ` · receipts ✗` when a receipt write failed. The line is redrawn at most about once per half second.
- Toasts. A subagent whose advisor count exceeds `childAdvisorBudget` toasts once, naming a shortened agent id, the count and the budget. The session toasts once when its total exceeds `sessionAdvisorBudget`. An Agent call with no model pinned also toasts once (`unpinnedAgent`), naming the subagent type and a shortened tool_use id (the description only when `recordDescription` is on). After a hot reload the toasts that were already shown stay shown: the mod restores that from the receipt files. The advisor toasts say the mod counts advisor calls and cannot block them.
- `/route-ledger` prints a table, one row per loop (`main`, then one per subagent, at most 60 rows then `+N more`) with the columns `agent | runner | model requested | model observed | effort requested | match | advisor`. Unknown cells read `UNKNOWN`. The `main` row comes from the last main-loop step the mod saw, not from the receipt files, so it is filled even when receipts are disabled. `/route-ledger receipts` prints the receipt file, the receipt counts, `receiptsEnabled` / `receiptsFailed` and, when receipts are off, the reason. Any other argument prints a one-line usage. The command never writes, spawns or reads outside its own state.
- `/route` is an alias with identical output.

## Load it

```
claude --plugin-dir plugins/dopemux-route-ledger
```

Check it offline with `claude plugin validate plugins/dopemux-route-ledger` and `claude plugin test plugins/dopemux-route-ledger`.

## Options (`userConfig`)

| key | default | meaning |
| --- | --- | --- |
| `receiptDir` | `.control-tower/state/route-ledger` | Where `<stem>.jsonl` files go (see Receipts for the stem). The default (compared without a trailing slash) is used only when `.control-tower/state` exists; an explicit directory is created on first write. Receipts are disabled for a `..` segment, for a directory (or, if it does not exist yet, its nearest existing parent) that is a symbolic link or not a directory, and for a relative directory that resolves outside the project root. An absolute directory is allowed. |
| `unpinnedAgent` | `warn` | `warn` toasts once per Agent call with no model pinned (forks excepted); `off` records only. |
| `childAdvisorBudget` | `0` | Advisor calls allowed per child agent. 0 means a child's first call exceeds it; a negative number turns the check off. |
| `sessionAdvisorBudget` | `-1` | Advisor calls allowed per session; -1 turns it off. |
| `maxReceiptsPerFile` | `500` | 50 to 5000; a new `<stem>.<n>.jsonl` segment starts after this many, or earlier at about 3.5 MB (see Receipts). |
| `recordDescription` | `false` | `false`: the Agent call's description is not recorded (the receipt keeps an empty `description`) and the unpinned-agent toast names the subagent type and a shortened tool_use id. `true`: record the first 80 characters and name them in the toast. |

## Receipts

Receipts are JSONL under `receiptDir`, one file (segment) per session, named `<stem>.jsonl`, then `<stem>.1.jsonl` and so on. The stem is the session id with every character outside `A-Za-z0-9_-` replaced by `_`, cut to 120 characters. A segment rolls to the next file after `maxReceiptsPerFile` receipts or when it reaches about 3.5 MB (the host refuses files over 4 MiB), whichever comes first. Three kinds exist: `agent_request` (the requested model and effort, joined to the spawned agent id and resolved model when `agent.spawn` fires), `step_observed` (requested versus the API-reported `usage.model`, with token usage) and `advisor_call`. The format is defined by `receipt.schema.json`. Prompts, file contents and tool output never enter a receipt.

`agent_request` and `step_observed` receipts carry `binding_fields`, a partial mapping a supervisor can merge into an ExecutionBinding:

- `selection` = `{ runner: "claude-code-agent", model, effort }` from what was requested
- `effort_requested` = the requested effort, or `UNKNOWN`
- `effort_observed` = always `UNKNOWN` (the API does not report effort)
- `response_claimed_model` = the API-reported model, or `UNKNOWN`
- `provider_attested_model` = always `UNKNOWN`
- `independence_class` = always `UNKNOWN`

A receipt is not a valid binding: the mod knows only these fields. A supervisor merges the receipts into a binding and runs `ct bind-record`; the mod never does.

An empty effort string is treated as no effort (`UNKNOWN`), and an advisor server-tool-use with an empty id is not recorded, so no receipt carries an empty `selection.effort`, `effort_requested` or `advisor_use_id`. The Agent call's `description` key is always present; it is the empty string unless `recordDescription` is on.

### Where receipts go, and what happens to them

- **Directory and file safety.** Once per session the mod looks at the receipt directory with `$.fs.stat` (the directory if it exists, else its nearest existing parent). It turns receipts off, with a reason that `/route-ledger receipts` shows, when that path is a symbolic link or not a directory, or, for a relative `receiptDir`, when its real path is not under the project root's real path. An absolute `receiptDir` is allowed by design, subject to the link and directory checks. Before the first write of each segment file the mod also looks at the file itself: a symbolic link there turns receipts off and nothing is written. A `$.fs.stat` that rejects means "not there"; if no part of the directory can be inspected, receipts are off.
- **Memory.** Once a closed segment has been written, its receipts are dropped from memory; only its path, number, size and receipt count stay, and the open (last) segment stays whole. A segment that still holds an Agent call waiting for its `agent.spawn` join is kept until that join is written. The counts in `/route-ledger receipts` and the `main` row do not depend on the dropped receipts.
- **Session end.** At `session.end` the mod flushes, and if a segment is still unwritten it makes one more attempt. A second failure is counted in `receiptsFailed` and not retried.
- **`/clear`.** The mod writes what is pending (one more try if the first write fails), keeps the status line, then resets its ledger so that the next hook re-resolves the session id. If receipts are still unwritten after that, the reset waits and nothing is dropped: the ledger keeps the old session's state, the next hook flushes again, and the reset happens once the tail is on disk. While it waits, new receipts carry the old session id. If the id changed, receipts go to a new file and the counts and the table start again. If it did not change, the mod rehydrates the same file and carries on. Whether Claude Code changes the session id on `/clear` is UNKNOWN (the declaration says the process goes on under a new id, not verified in a live session); both cases are handled and tested offline. Until the next recorded event the table and counts are empty after a `/clear`.

## Limits

- It counts advisor calls after the fact. It cannot block, deny or retry any call.
- The observed model is what the API response claimed (`response_claimed`), not provider attestation. Effort observed is UNKNOWN.
- A fork inherits its parent's model, so a fork with no model is recorded as inheriting, not as unpinned.
- The plugin API is early access and may change between Claude Code builds.
- `/route` may collide with a built-in or another plugin's command in some builds. If it is refused, use `/route-ledger`, which is registered independently and keeps working.
- The mod pins its own status line. Whether it coexists with another plugin's status line (for example dopemux-pulse) is unverified and was not run.
- The mod is read-only toward the repository except its own receipt files under `receiptDir`. It makes no network, process or model call. Its only file-system calls are exists, list, read, write and stat on those paths.
- Whether `/clear` changes the session id is UNKNOWN; see Receipts.
- Not run yet: a live Claude Code session loading the mod. Offline tests only.
