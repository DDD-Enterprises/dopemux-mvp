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

The sole current contract for supervised execution artifacts is
`schemas/governed_execution/`, with its hash-bound `manifest.v1.json`.
Current bindings use `execution_binding.v2.schema.json`; MacroPackets use
`macro_packet.v2.schema.json`. Templates in this kit emit these v2 shapes.
`jsonschema` and `referencing` (existing repository dependencies) are required;
missing dependencies or schemas block validation without a fallback.

Record a complete v2 binding with `ct bind-record --file <binding.json>`.
Validate with `ct validate-binding --file <binding.json>`. Every binding carries
`macro_id`; child bindings additionally carry `packet_id`. Coordinator bindings
omit `packet_id`. Mutable records under `state/bindings/` are technical,
noncanonical local state, not an authority store or a persistence/replay service.
ExecutionBinding and WriterCustody are evidence and constraints, never grants.

The byte-preserved CT v1 schemas are `LEGACY_READ_ONLY` in the manifest.
`validate-binding --legacy-read-only` and `validate-macro --legacy-read-only`
explicitly validate historical compatibility. `validate-route` reads historical
route records; `route-record` refuses writes. Legacy validators and ZIP inspection
cannot authorize execution or produce current bindings. No automatic conversion
fills missing v2 evidence. New packaging requires a valid v2 binding; missing or
malformed current bindings block even when historical routes exist. Historical
ZIPs remain inspectable as historical transport only. `return_packet.schema.json`
and route schemas describe transport/compatibility, not competing current
supervised execution contracts. DCP RouteDecision artifacts remain unchanged.

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

## M0 boundaries

Control Tower remains a thin operator/supervision layer. Task Orchestrator owns
workflow legality; DCP owns eligibility, policy and context; Audit Broker owns
audit judgment and dispatch; Dopetask owns authorized effects; PR Steward owns
readiness classification. Merge, activation, security, credentials, production
and destructive authority remain with the operator. Donor helper modules are
reused as local libraries only: M0 adds no service, database, automatic next-action
dispatch, CT persistence/replay wiring, or M1-M7 behavior.

Benchmark fixtures under `tests/unit/governed_execution/benchmark/fixtures/`
are synthetic test inputs, including their nested proof/task-packet examples.
They are not imported donor proof, current audit evidence, or acceptance receipts.
