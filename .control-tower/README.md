# Control Tower Installation

This repository installation began from `CONTROL_TOWER_SUPERVISOR_KIT_v1.0.0.zip`.
Repository-maintained validation and packaging repairs are tracked in Git. It is
not an unmodified upstream payload or a new upstream release.

## Configuration Authority

`project.json` is installed runtime configuration and canonical project identity
for this CLI. `config/defaults.json` is retained installer scaffold only. The CLI
does not read or merge defaults at runtime, so editing defaults cannot reconfigure
an existing installation.

## Package Guarantees

`proof-pack` and `return-pack` stage inputs into a private directory, validate
repository and packet identity, screen every staged regular-file byte, generate
and screen metadata, bind member hashes and sizes, rehash bytes written to ZIP,
and semantically verify the private archive before exclusive publication.
`verify-zip` checks those contracts by default. `verify-zip --crc-only` names
the intentionally narrower CRC-only mode.

The built-in secret patterns are bounded heuristics. A PASS receipt proves every
exported member was read and checked without a configured match; it does not prove
that arbitrary sensitive data is absent.

## Routing Scope

Control Tower ExecutionBindings apply only to supervised packets and workstreams.
Ordinary unsupervised work keeps existing repository, user, and local model-selection
authority. Tool inventory performs executable/version probes only by default;
`runner-inventory --probe-models` is the explicit model-catalog opt-in.

Packaging prepares local evidence. It does not perform an audit, accept proof,
authorize upload or merge, change signer/finality authority, or activate anything.
Historical proof remains historical after substantive changes.

## Execution Bindings and MacroPackets

Current exact runner/model/effort records use `execution_binding.schema.json`,
`EXECUTION_BINDING.template.json` and `EXECUTION_BINDING.json`. Record a complete
binding with `ct bind-record --file <binding.json>` and validate it with
`ct validate-binding --file <binding.json>`. Mutable current records live under
`state/bindings/`; preserve consumed records in immutable evidence before changes.
Use packet_id for a child and macro_id for a coordinator, never both.

Historical `route_decision.schema.json`, `ROUTING_DECISION.template.json`,
`state/routes/` and `validate-route` are retained for explicit read compatibility.
The deprecated `route-record` convenience command now emits an ExecutionBinding
and preserves its legacy input representation. It cannot infer external policy,
identity, containment or authority. A canonical binding takes precedence over a
historical record; a malformed canonical binding blocks instead of falling back.
Legacy fallbacks omit effort and therefore block conversion until an explicit
complete fallback tuple is rebound; historical validation remains read-compatible.
New ZIPs contain only EXECUTION_BINDING.json; the verifier still accepts legacy
ZIPs and rejects conflicting dual root records. Old verifiers need upgrading
before consuming new packages. DCP RouteDecision artifacts are unchanged.

The supervisor authors program/child authority; the team lead coordinates bounded
work. See [MacroPacket contract](contracts/SUPERVISOR_MACROPACKET_CONTRACT.md).
`ct validate-macro --file <package>/SUPERVISOR_MACRO_PACKET.json` validates static
integrity. Its result has authority NONE. The standard-library preview/return
helpers are inert projections for caller-verified child snapshots; there are no
service integrations, workflow writes, runner dispatch or finality decisions.

Generic operation requires no DCP runtime. External policy/workflow/context/audit
references stay UNKNOWN/NOT_RUN until their canonical producers are verified.
Parallel mutation requires disjoint child writers and current legal state.
Audit obligations cannot be weakened. Automatic next-action dispatch is absent.
