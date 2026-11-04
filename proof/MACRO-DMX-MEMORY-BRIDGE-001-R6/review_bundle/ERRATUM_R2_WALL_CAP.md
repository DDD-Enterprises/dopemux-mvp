# Erratum - MACRO-DMX-MEMORY-BRIDGE-001-R2 wall-time cap (Copilot finding C4)

Recorded 2026-11-01 under R6 amendment v2, workstream W03. The R2 files are not edited; this note corrects them.

## What R2 says

`proof/MACRO-DMX-MEMORY-BRIDGE-001-R2/review_bundle/RETURN-01.md:29` says the interval "includes a session-limit pause and a supervisor-session restart, so wall time is not a useful measure against the 6 h cap", and "No cap was hit".

## What the cap was

R2 `MACRO_PACKET.json` `base_policy`: "elapsed wall time 6 h from the authorization to a frozen head, excluding the operator-gated audit" and "Hitting any cap: stop dispatching, preserve uncommitted diffs, return NEEDS_SUPERVISOR with the counters". It has no pause or restart exemption, and no operator extension was recorded.

## What happened (UTC)

| Event | Time | Source |
|---|---|---|
| R2 team-lead binding recorded (issuance) | 2026-10-23T20:38:50Z | R2 `EXECUTION_BINDING.json` `recorded_at` |
| W02 dispatched (the R2 authorization came before this) | 2026-10-23T20:44:55Z | R2 `W02_EXECUTION_BINDING.json` `recorded_at` |
| W03 dispatched | 2026-10-23T21:03:11Z | R2 `W03_EXECUTION_BINDING.json` `recorded_at` |
| 6 h after W02's dispatch (the latest the cap could have expired) | 2026-10-24T02:44:55Z | computed |
| W04 dispatched | 2026-10-24T03:11:17Z | R2 `W04_EXECUTION_BINDING.json` `recorded_at` |
| Frozen head: content commit `52855fb35` | 2026-10-24T03:13:35Z (2026-10-23T20:13:35-07:00) | `git log -1 --format=%cI 52855fb35` |

Elapsed time from the authorization to the frozen head was at least 6 h 28 min 40 s (from W02's dispatch) and at most 6 h 34 min 45 s (from issuance). The cap was exceeded. W04 was dispatched after it had expired. Under the R2 packet, the team lead should have stopped before W04 and returned `NEEDS_SUPERVISOR`. The correct line for `RETURN-01.md:29` is: "Wall-time cap exceeded: at least 6 h 28 min from authorization to the frozen head (session-limit pause and supervisor restart included; the packet has no pause exemption). Status should have been NEEDS_SUPERVISOR."

The other R2 caps hold as recorded: tokens 920,498 of 3,000,000, dispatches 4 of 5, correction rounds 1 of 2, advisor 0.

## Effect

- On the code: none directly. The R2 content was audited (Grok, PASS_WITH_RISKS) and has since been repaired and re-audited in R3, R4 and R5. The R6 audit covers the whole current Memory Bridge diff.
- On the record: the operator accepted the R2 verdict on 2026-10-24 without this breach disclosed. Ratifying the overrun after the fact, or recording R2's aggregate as `NEEDS_SUPERVISOR`, is the operator's decision. This erratum does neither.
- Lesson: a pause or restart doesn't stop a wall-time cap unless the packet says so. A return must report the cap against its own wording, not a re-reading of it.
