# Next Three Packets

## 1. Ops-Owned-Lane-Readiness

Why first:

- `R1D` is the current hard blocker for restart.
- The failure is operational and explicit:
  - OpenRouter returned `401 auth_rejected`
  - OpenAI returned `429 quota_or_billing`
  - no live attempts were admitted

Goal:

- Determine whether the environment can support a truthful owned strict-extraction live control pair.

Must produce:

- provider-specific readiness findings
- auth/quota remediation path or explicit non-readiness classification
- a new bounded live proof only if provider readiness actually improves

## 2. Phase-S-Contract-Parity

Why second:

- The audit does not support parity claims for Phase S relative to the core runtime-route lane.
- Phase S has registry and prompt discipline, but not the same route/admissibility/live evidence depth.

Goal:

- Decide which parts of core-phase contract rigor should be mirrored into Phase S and implement only those justified surfaces.

Must produce:

- parity target list
- explicit non-goals
- stronger contract/evidence surface or an honest lane-specific limitation memo

## 3. Pricing-Truth-Followup

Why third:

- Cost-profile design is still partially blocked by xAI pricing gaps and stale rows.
- `PROFILE-SYNTH-001` is already correctly blocking optimization around those unknowns.

Goal:

- Resolve whether xAI pricing can be upgraded from `UNPRICED_UNKNOWN` and `STALE_NEEDS_REFRESH` to truthful current pricing classes.

Must produce:

- updated pricing source audit
- updated pricing coverage report
- explicit statement of which profile-design blockers are removed and which remain

## Why these three and not others

- Not scheduler work: restart truth is still blocked.
- Not UI: operator truth is the binding constraint.
- Not more synthesis cleverness: the advisory loop already exists and is behaving correctly.
- Not a broad architecture rewrite: the most valuable unknowns are now concrete and packetizable.
