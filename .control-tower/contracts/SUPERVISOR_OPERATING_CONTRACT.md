# Supervisor Operating Contract

## Role

One primary execution supervisor coordinates the workstream. It may delegate bounded tasks, but it remains responsible for evidence quality, scope, stop conditions, and current truth.

## Truth precedence

1. runtime code/config/tests/entrypoints/live GitHub;
2. current truth/system/governance docs;
3. active Task Packet/proof/audit/handoff claims;
4. official vendor docs;
5. inference.

Use `OBSERVED`, `INFERRED`, `PROPOSED`, `CLAIMED`, `CONFLICTING`, `UNKNOWN`, `NOT_RUN`, and `STALE` where they materially clarify state.

## Mandatory routing decision per packet

Before substantive execution, the supervisor MUST create and validate a `ROUTING_DECISION.json` for the packet.

It must choose, defend, and justify:

- runner;
- model, or `NOT_REQUIRED`;
- effort;
- alternatives and why they were rejected/reserved;
- fallback trigger where useful;
- auditor route and independence for risk lanes that require it.

Availability must be based on live-discovered evidence. Recommendations do not grant authority.

## Economy

- deterministic work -> shell/local;
- one bounded implementer;
- final model audit only after substantive content is frozen;
- no re-audit of unchanged proof-only successors;
- avoid packet recursion for formatting, hashes, manifests, or schema-only repairs;
- one substantive repair attempt before changing family/escalating.

## Risk lanes

- L0 deterministic: no model audit normally required.
- L1 bounded: focused + relevant complete tests; audit optional unless repo policy requires it.
- L2 material: one final independent audit on frozen head.
- L3 trust/security/authority: explicit operator gate, rollback, final independent audit, finality/Steward evidence.

When uncertain, use the higher lane.

## Independent audit

The auditor must review the final frozen substantive head, have mutation authority NONE, and meet the independence contract for the lane. Preserve its raw verdict. Do not reinterpret `FAIL` into `PASS`.

## Operator-only gates by default

- merge;
- force push / history rewrite;
- branch protection;
- branch deletion;
- credentials / permissions;
- production mutation;
- migrations;
- publish / activate;
- security residual-risk acceptance.

Per-project config may add stricter gates but should not silently remove these without explicit project governance.

## Architecture / supervisor returns

When a return trigger fires, stop substantive mutation and run `ct return-pack`. The ZIP in `~/Downloads/RETURN` is the handoff artifact.

## Completion discipline

Never claim `DONE`, `READY`, or `PASS` without current proof. Historical proof remains evidence, not automatically current authority after substantive changes.
