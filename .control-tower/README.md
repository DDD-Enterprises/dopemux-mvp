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

Control Tower routing records apply only to supervised packets and workstreams.
Ordinary unsupervised work keeps existing repository, user, and local model-selection
authority. Tool inventory performs executable/version probes only by default;
`runner-inventory --probe-models` is the explicit model-catalog opt-in.

Packaging prepares local evidence. It does not perform an audit, accept proof,
authorize upload or merge, change signer/finality authority, or activate anything.
Historical proof remains historical after substantive changes.
