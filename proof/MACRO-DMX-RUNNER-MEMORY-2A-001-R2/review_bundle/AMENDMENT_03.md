# MACRO-DMX-RUNNER-MEMORY-2A-001-R2 — Amendment 03: the Codex gate accepts `log` mode

**Recorded:** 2026-11-01 (UTC), by the team lead (Control Tower supervisor session), after W07 was committed (`29203f1eb`).

**Operator words (verbatim):** "Allow log mode (Recommended)"

**In answer to (verbatim):** "The Codex config gate requires both memory servers in `enforce`, which can't happen in 2A (container callers, and Claude until 2B). How should Codex get its memory access?"

The chosen option read: "Gate check 1 accepts `log` or `enforce` (identity-required writes still true). Codex goes live in 2A and every Codex write is verified as runner:codex; tokenless writers stay accepted-but-recorded until enforce. Needs a small W07 follow-up and the ADR-MCPINT-002 amendment worded to match."

## Why

- Design 5.7 and W07 B01 make the Codex config write wait until both servers report `enforce`.
- `enforce` cannot be switched on in 2A:
  - container callers cannot present a token (`W05_RETURN.md`, open item 2);
  - since Amendment 02, Claude Code's direct HTTP writes carry no token until Wave 2B.
- So, as built, the gate could never write Codex's config in 2A, and G4 ("Codex reaches dope-memory and ConPort through generated config") could not be met.
- Codex's own writes are verified either way: the bridge always sends `runner:codex`'s token, and the servers store the verified principal in `log` mode too. `enforce` only adds rejection of writers that send no token.

## Effect

**Gate check 1** now passes when, for both servers:
- `auth_mode` is `log` or `enforce`;
- `identity_required_writes` is `True`;
- ConPort `auth_principal_column` is `ok`.

`off` fails.

**In `log` mode** the apply output states it: Codex's writes are verified as `runner:codex`, and writers without a token are still accepted and recorded `unverified` until `enforce`.

**Gate check 2** (a keychain token for the runner) is unchanged.

**Design deviation (2A revision 2):**
- 5.7 check 1 is relaxed from "`enforce`" to "`log` or `enforce`".
- G4 becomes reachable in 2A.
- G2 ("once a server is in `enforce` mode, an HTTP write without a valid token is rejected") is unchanged: it was always conditional on `enforce`.
- 5.5's rule that `enforce` follows the smoke test and the accepted-writer review stands, now also after container token delivery and Claude Code's 2B move.

**W08:** the ADR-MCPINT-002 amendment draft says, for the memory servers, that verified per-runner identity on HTTP writes with identity-required writes replaces the actor-auth precondition. It also says Codex is admitted while servers run in `log` mode, with `enforce` to follow the conditions above.

**W07 follow-up round:** W07's write surface (no new files) is authorized under this ruling. A03 of W07 permits an extra attempt only with a new operator ruling; this is that ruling.

## Still not authorized

Push or PR; signing; the audit route; token issuance; migrations against a real database; the enforce switch; the ADR-MCPINT-002 amendment's acceptance; the live Codex run; merge.
