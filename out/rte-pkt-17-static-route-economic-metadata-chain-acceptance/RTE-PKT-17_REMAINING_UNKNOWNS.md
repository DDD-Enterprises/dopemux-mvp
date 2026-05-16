# RTE-PKT-17 Remaining Unknowns

- `origin/main` in this checkout still resolves to `ac78f2184a2827ed5871d078f4763695a561241b`, so the user-supplied merged state of PR #638 is not re-proven from local refs here.
- PR #638 is reachable from `codex/rte-pkt-15-artifact-consumer-compat` in this clone, but not from local `main`.
- OpenRouter x-ai live upstream metadata, returned-model behavior, schema acceptance, retention/ZDR/billing/rate-limit equivalence, and direct xAI live safety remain the preserved UNKNOWNs from the earlier chain packets.
- Historical generated artifacts outside the checked test/runtime selectors were not exhaustively proven by this packet.
- The Opus-audit UI/UX cleanup series has not yet been packetized in this repository.
