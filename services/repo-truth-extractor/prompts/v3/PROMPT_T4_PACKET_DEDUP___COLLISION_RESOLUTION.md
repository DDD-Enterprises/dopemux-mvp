# PROMPT_T4 — PACKET DEDUP / COLLISION RESOLUTION

TASK: Deduplicate Task Packets and resolve title/id collisions deterministically.

OUTPUTS:
- TP_DEDUPED.json
- TP_COLLISIONS.json

Rules:
- Detect duplicate `tp_id`, duplicate normalized titles, and materially overlapping scopes.
- Resolve collisions with deterministic tie-breaks: higher evidence density, lower blast radius, earlier dependency.
- Preserve traceability from deduped packets to source packet IDs.
- Record dropped/merged packets and reason codes in `TP_COLLISIONS.json`.
