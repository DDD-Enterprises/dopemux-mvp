---
id: route-ledger
title: Route Ledger Mod (dopemux-route-ledger)
type: how-to
owner: '@hu3mann'
author: 'claude-code-agent (claude-haiku-5-5)'
date: '2026-10-23'
last_review: '2026-10-23'
next_review: '2027-01-21'
prelude: How to load the dopemux-route-ledger mod, read its status segment and toasts, use the /route-ledger table, configure its receipts, and hand receipts to a supervisor for ExecutionBinding merge.
---
# Route Ledger Mod (dopemux-route-ledger)

`dopemux-route-ledger` is a read-only Claude Code mod that records which model each
Agent call requested, which model each step reported back, and every advisor call.
It shows the result as a status segment, toasts, and a `/route-ledger` table, and
writes each record as a JSONL receipt. Source: `plugins/dopemux-route-ledger/`.

Live behaviour is NOT VERIFIED. The offline tests in `hooks/register.test.ts` are the
only evidence so far. Before you rely on the mod, run it in a real session (section 1)
and check what it shows.

## 1. Load the mod

From the repo root:

```bash
claude --plugin-dir plugins/dopemux-route-ledger
```

Offline checks, from the repo root:

```bash
claude plugin validate plugins/dopemux-route-ledger
claude plugin test plugins/dopemux-route-ledger
```

Nothing is installed. The mod lasts for that session
(`plugins/dopemux-route-ledger/README.md`, "Load it").

## 2. What you see

- **Status segment**, for example `agents S×4 H×2 · advisor 1`. Agents appear in the
  order S (sonnet), O (opus), H (haiku), F (fable), then `?` for any other or unknown
  model. Only non-zero counts show. With none, the segment reads `agents –`.
  `advisor N` appears when N > 0. Once a budget applies and is exceeded it reads
  `advisor N/B ⚠`.
- `· ledger off` is appended when receipts are disabled. `· receipts ✗` is appended
  when a receipt write failed.
- **Toasts**, each shown once:
  - a subagent whose advisor count exceeds `childAdvisorBudget`;
  - the session, once its total exceeds `sessionAdvisorBudget`;
  - an Agent call with no model pinned (`unpinnedAgent`).
  Every advisor toast says the mod counts advisor calls and cannot block them.
- **`/route-ledger`** prints a table with one row per loop: `main`, then one row per
  subagent, at most 60 rows and then `+N more`. Columns: `agent | runner | model
  requested | model observed | effort requested | match | advisor`. Unknown cells read
  `UNKNOWN`.
- **`/route-ledger receipts`** prints the receipt file, the receipt counts, and
  `receiptsEnabled` / `receiptsFailed`. Any other argument prints a one-line usage.

The command reads the ledger and writes nothing.

## 3. The `/route` alias

`/route` is an alias with the same output. It is a best-effort name: it may collide
with a built-in or another plugin's command, and some builds refuse it. If `/route` is
refused, use `/route-ledger`. That name is registered on its own and keeps working.

## 4. Options (`userConfig`)

| key | default | meaning |
| --- | --- | --- |
| `receiptDir` | `.control-tower/state/route-ledger` | Where `<sessionId>.jsonl` files go. The default is used only when `.control-tower/state` exists. An explicit directory is created on first write. A `..` segment disables receipts. |
| `unpinnedAgent` | `warn` | `warn` toasts once per Agent call with no model pinned (forks excepted). `off` records only. |
| `childAdvisorBudget` | `0` | Advisor calls allowed per child agent. `0` means a child's first call exceeds it. A negative number turns the check off. |
| `sessionAdvisorBudget` | `-1` | Advisor calls allowed per session. `-1` turns it off. |
| `maxReceiptsPerFile` | `500` | Allowed range 50 to 5000. A new segment starts after this many records. |

## 5. Receipts

Receipts are JSONL under `receiptDir`. The file stem is the session id with any
character outside `A-Za-z0-9_-` replaced by `_`, so the file is `<stem>.jsonl`, then
`<stem>.1.jsonl` and so on. Each record has `schema_version`
`dopemux.route_ledger.receipt.v1`. The format is defined by `receipt.schema.json`.

Three record kinds exist:

- `agent_request`: the requested model and effort. It also carries nullable
  `spawned_agent_id` and `resolved_model`, filled when `agent.spawn` fires.
- `step_observed`: the requested model against the `usage.model` the API reported,
  with token usage.
- `advisor_call`: one advisor server-tool-use, deduplicated by its id.

Prompts, file contents and tool output never enter a receipt.

### binding_fields

`agent_request` and `step_observed` receipts carry `binding_fields`, a partial mapping:

- `selection` = `{ runner: "claude-code-agent", model, effort }` from the request;
- `effort_requested` = the requested effort, or `UNKNOWN`;
- `effort_observed` = always `UNKNOWN`, because the API does not report effort;
- `response_claimed_model` = the API-reported model, or `UNKNOWN`;
- `provider_attested_model` = always `UNKNOWN`;
- `independence_class` = always `UNKNOWN`.

A receipt is not a valid binding. A supervisor merges receipts into an ExecutionBinding
and runs `ct bind-record`. The mod never runs `ct`.

## 6. What the mod does not do

- It counts advisor calls after the fact. It cannot block, deny or retry any call.
- The observed model is what the API response claimed. It is not provider attestation.
  Effort observed is always UNKNOWN.
- A fork inherits its parent's model, so a fork with no model is recorded as
  inheriting, not as unpinned.
- It makes no network, process or model call. It writes nothing to the repository
  except its own receipt files under `receiptDir`, and nothing to `~/.claude`.
- Whether it coexists with another plugin's status line, for example dopemux-pulse,
  is unverified. The mod sets its own status line, and this was not run.
- The plugin API is early access and may change between Claude Code builds.

## 7. Troubleshooting

- **`· ledger off` in the status, or `receipts are off` in `/route-ledger receipts`.**
  The default `receiptDir` is used only when `.control-tower/state` exists. Either
  create that directory, or set `receiptDir` to an explicit path. The receipts text
  gives the reason.
- **`· receipts ✗`.** A receipt write failed. Run `/route-ledger receipts` and read
  `receiptsFailed`. Check that the receipt directory is writable.
- **Unpinned-agent toast.** An Agent call had no model. Pin the model on the call, or
  set `unpinnedAgent` to `off` to record without the toast.
- **`/route` refused.** Use `/route-ledger`.
- **`UNKNOWN` in the table.** The field was not reported. Do not read it as a pass.

## 8. Next step

To see the mod work, load it with section 1 in a real session, start one Agent call
with a pinned model, and run `/route-ledger`. Record what you observe. Until someone
does, treat the runtime behaviour as NOT VERIFIED.
