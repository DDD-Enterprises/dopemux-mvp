# 00 Scan Scope and Method

## Scope
- Repository root scanned from `/Users/hue/code/leantime`.
- Primary code scope: `app/Core/**`, `app/Domain/**`, `config/**`, `app/Views/**`.
- Schema authority scope: `app/Domain/Install/Services/SchemaBuilder.php` and `app/Domain/Install/Repositories/Install.php`.
- Integration/runtime seams scope: routing, middleware, event system, API controllers, connector/import, queue/jobs.
- Explicitly excluded from evidence claims: `vendor/**`, `.git/**`, runtime DB contents, external systems not represented in this repo.

## Method
- Evidence-first static inspection of executable code paths (schema, repositories, services, controllers, middleware, routing, event hooks).
- Preferred line-numbered inspection using `nl -ba` + `sed -n` on candidate files.
- Cross-cutting pattern search using `rg -n` before deep reads.
- Claims classified as:
- `implemented behavior` when directly evidenced in executable code.
- `documented intent` when comments/docs state intent without corresponding enforcement.
- `inferred capability` only when code composition strongly implies behavior.
- `absent/no evidence found` only when explicit scoped searches returned no match.

## Commands Used (Representative)
- File inventory and status:
- `ls -la`
- `git status --short`
- Targeted code search:
- `rg -n "status|state|dependingTicketId|milestone|sprint|patch|updateTicketStatus" app/Domain app/Core`
- `rg -n "dispatch_filter|dispatch_event|add_event_listener|add_filter_listener" app/Core app/Domain`
- `rg -n "jsonrpc|leantime\.rpc|parseMethodString|prepareParameters" app/Domain/Api`
- `rg -n "webhook|next action|state machine|allowedTransitions|decision log" app config`
- Line-cited reads:
- `nl -ba <file> | sed -n '<start>,<end>p'`
- Directory probing:
- `find app/Domain -maxdepth 2 -name 'register.php'`

## Search Terms
- PM state: `state`, `status`, `ticketlabels`, `projectsettings`, `sprint`, `milestone`.
- Transition/mutation: `patch`, `updateTicketStatus`, `updateProjectStatusAndSorting`, `editProject`, `addTicketChange`.
- Dependency/blocker: `dependingTicketId`, `blocked`, `status.blocked`.
- Progress/decision: `getProjectProgress`, `getMilestoneProgress`, `stepsComplete`, `conclusion`, `action`.
- History/chronicle: `zp_tickethistory`, `zp_audit`, `comment`, `notification`, `read`.
- Integrations/seams: `Jsonrpc`, `EventDispatcher`, `register.php`, `RouteLoader`, `LoadPlugins`, `Connector`, `Queue`, `webhook`.

## Files and Types Inspected
- PHP code in:
- `app/Core/**` (middleware, routing, events, base repository).
- `app/Domain/**` (controllers, services, repositories, register hooks).
- UI templates only when needed to confirm behavior surfaced in workflow UI.
- No claim relies solely on prose docs when conflicting executable evidence existed.

## Limitations
- Static pass only; no runtime requests executed.
- No DB instance was interrogated; table existence/shape taken from schema builders and install SQL definitions.
- No plugin private submodule internals evaluated beyond extension hooks visible in OSS tree.
- Some UI-triggered constraints may exist in JS/template interactions not equivalent to backend invariants.

## Negative-Evidence Method
- For every absence claim, ran explicit `rg` with bounded scope and recorded exact command + result in `99-evidence-index.md`.
- Search scope for negative claims was at least `app` and `config` unless otherwise noted.
- Example patterns: workflow legality engines (`allowedTransitions`, `state machine`), next-action computation (`nextAction`, `next action`), decision registries (`decision log`), inbound webhooks (`function .*webhook`, `/webhook`).
