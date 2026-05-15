# RTE-PKT-05 Remaining Unknowns

## UNKNOWN: Prescan-derived value merge

Observed code paths show prescan can influence context, routing hints, and receipts, but this packet did not find a runtime path where prescan directly supplies values into normalized artifacts. No `prescan_derived` field record is emitted by the changed path unless a future merge path calls the provenance helper.

Recommended downstream handling: RTE-PKT-06 should preserve this as `UNKNOWN` unless a concrete prescan-to-artifact merge path is identified.

## PARTIAL: Envelope repair fixture coverage

The envelope repair branch now uses the same provider-repair provenance helper as targeted repair. This packet does not add a dedicated envelope-only fixture.

Recommended downstream handling: add an envelope-specific semantic fixture if RTE-PKT-06 expands repair truth-label coverage.

## PARTIAL: Full UNKNOWN/CONFLICTING preservation

This packet distinguishes derived lanes from primary observed extraction. It does not solve full semantic preservation of `UNKNOWN` and `CONFLICTING` labels through all repairs and sidefills.

Recommended downstream handling: leave full semantic assertions to RTE-PKT-06-TRUTH-LABELS.

## ACCEPTED_WITH_RISK: Live provider behavior

Provider repair and sidefill tests use local monkeypatch fixtures. They prove runtime metadata behavior without provider calls, not provider-specific live response behavior.

Recommended downstream handling: keep live validation blocked until an explicit later packet authorizes it.
