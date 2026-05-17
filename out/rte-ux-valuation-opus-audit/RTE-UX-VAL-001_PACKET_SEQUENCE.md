# RTE-UX-VAL-001 Packet Sequence

Packet labels below are proposed sequence labels for the implementation campaign. Only `RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001` was explicitly named in the packet text; the remaining labels are derived from the approved sequence described there.

## Next

| Order | Packet | Recommendation ids | Decision | Why now |
| --- | --- | --- | --- | --- |
| 1 | `RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001` | `R-OPUS-2` | `ACCEPT_NEXT` | Fix the authority spine first so later docs and prompts stop arguing about what wins. |
| 2 | `RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001` | `R-OPUS-3`, `R-OPUS-14` | `ACCEPT_NEXT` | Once authority is stable, teach the agent surfaces the RTE safety invariants. |
| 3 | `RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001` | `R-OPUS-1`, `R-OPUS-4` | `ACCEPT_NEXT` | Bring the operator CLI back into the brand-voice contract before polishing help layout. |
| 4 | `RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001` | `R-OPUS-8` | `ACCEPT_NEXT` | Improve the failure surface that blocks live runs. This is still safety-adjacent, not cosmetic. |
| 5 | `RTE-UX-PKT-RUN-HELP-PROGRESSIVE-DISCLOSURE-001` | `R-OPUS-9` | `ACCEPT_NEXT` | Reduce help-text overload after the safety and authority packets are in place. |

## Accepted Later

| Order | Packet | Recommendation ids | Decision | Why later |
| --- | --- | --- | --- | --- |
| 6 | `RTE-UX-PKT-UX-DOC-CLEANUP-001` | `R-OPUS-5`, `R-OPUS-6` | `ACCEPT_LATER` | Documentation cleanup is useful, but it does not change operator gating or authority. |
| 7 | `RTE-UX-PKT-ARCHITECTURE-UPGRADES-RECONCILIATION-001` | `R-OPUS-10`, `R-OPUS-11` | `ACCEPT_LATER` | Alias and command reconciliation should follow the spine and gate work so the docs can point at one story. |
| 8 | `RTE-UX-PKT-V5-PROMPTSET-AUDIT-STRATEGY-001` | `R-OPUS-7` | `ACCEPT_LATER` | Important strategy work, but not a blocker for the more direct operator-safety fixes. |
| 9 | `RTE-UX-PKT-DPMX-LIVE-OK-HINTS-001` | `R-OPUS-15`, `R-OPUS-19` | `ACCEPT_LATER` | Helpful hinting and deprecation cleanup are downstream refinements once the core sequence lands. |

## Deferred

| Bucket | Recommendation ids | Why deferred |
| --- | --- | --- |
| Opportunistic | `R-OPUS-12`, `R-OPUS-13`, `R-OPUS-16`, `R-OPUS-17`, `R-OPUS-18` | Lowest practical value in the packet text. They do not move the authority spine or live-gate surface, so they can wait until the higher-priority packets complete. |
