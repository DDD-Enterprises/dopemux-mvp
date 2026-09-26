# Supervisor Operating Contract

## Roles and authority

The Control Tower supervisor owns program judgment, packet decomposition and
adjudication within operator authority. It may issue one Supervisor MacroPacket
containing several bounded child Task Packets.

The execution coordinator / team lead consumes that envelope and its exact
ExecutionBinding. It coordinates legal work, delegates within each child's
ceiling and collects evidence. It cannot author new canonical packet authority,
change child scope/risk/audit/rollback, or serve as its own independent auditor.

DCP owns policy eligibility and obligations; Task Orchestrator owns workflow
legality; Universal Router ranks eligible candidates; Audit Broker supplies
certified auditor evidence; Dopetask performs separately authorized execution.
These remain separate authorities. The generic kit requires none of their
runtimes. Optional references do not imply an integration has run.

## Truth and dispatch boundaries

Active repository governance and Task Packets control execution scope. Observed
runtime, source and current GitHub evidence control behavior claims. Historical
proof and model output never create current authority.

For each child, allowed actions are the intersection of applicable operator,
packet, repository, policy and legal workflow bounds. Denials combine by union;
audit/proof obligations combine by maximum strictness. No child can borrow a
sibling's permission. An L3 upstream audit requirement cannot be lowered by a
local L1 binding or an investigation stage.

Use OBSERVED, INFERRED, PROPOSED, CONFLICTING, UNKNOWN, NOT_RUN and STALE honestly.

## ExecutionBinding

For every supervised packet, validate scope and then record its exact binding
before implementation. Ordinary unsupervised work does not synthesize a binding.

Canonical schema: `control_tower.execution_binding.v1`.
Canonical artifact: `EXECUTION_BINDING.json`.
Start with `templates/EXECUTION_BINDING.template.json`, fill current evidence,
then run `ct bind-record --file <binding>` and `ct validate-binding --file <binding>`.

Use exactly one subject: `packet_id` for a child or `macro_id` for the coordinator.
The coordinator's binding does not authorize child mutation. Bind each child
inside its own preferred/fallback set. Unavailable authorized routes return
`ROUTE_CEILING_EXCEEDED` or `NO_POLICY_ELIGIBLE_LIVE_ROUTE`; no silent fallback.

Record exact runner/model/effort, availability, containment evidence, alternatives,
identity provenance, constraints, external references and effective audit sources.
Configured, response-claimed and provider-attested identity remain separate.
Unknown external producers stay UNKNOWN/NOT_RUN.

Delivery lanes L0-L3 and DCP classes R0_READ through RED_LANE are independent.
Never infer a DCP class from a delivery lane. A binding has authority NONE:
validation does not grant execution, attest availability or override policy.
DCP's RouteDecision name is not used for current Control Tower bindings.

## Economy and concurrency

Prefer deterministic local checks; otherwise choose the cheapest adequate
authorized route from current evidence. Respect pinned models and retry budgets.
One mutating implementer per workstream; several mutating workstreams may run
concurrently only with disjoint physical/semantic write surfaces, canonical
writers, rollback and custody, plus current legal workflow state. Shared writers
require an explicit serialized dependency. See SUPERVISOR_MACROPACKET_CONTRACT.md.

L0 normally needs no model audit. L1 uses focused deterministic checks unless a
stronger source requires audit. L2/L3 require one final independent audit after
substantive freeze. Preserve upstream requirements even when this stage stops
before audit. No intermediate model audits or redundant audits of unchanged bytes.

## Operator and return gates

Merge, activation, readiness promotion, force push/history rewrite, permissions,
credentials, production, migrations and security risk acceptance remain separately
gated. A packet reference or model recommendation never synthesizes an operator gate.

Preserve failed evidence and raw independent audit verdicts. On an applicable
supervisor/operator gate or global stop, stop substantive work and use
`ct return-pack`. Otherwise continue legal independent siblings and return one
aggregate result with each child status and exact subject preserved.

The team lead cannot mint READY/DONE/PASS from mixed child states or model output.
No autonomous workstream promotion, new MacroPacket creation or next-macro dispatch
is implemented or authorized by this generic kit.
