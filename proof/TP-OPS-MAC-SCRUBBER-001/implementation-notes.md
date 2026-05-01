# TP-OPS-MAC-SCRUBBER-001 Implementation Notes

## Scope

Implemented a new `dopemux system-data` feature area with required external
tool preflight, scanner, classifier, planner, executor, restore manifest
surface, proof writer, docs, and Textual TUI shell.

## Safety Notes

- `clean` defaults to dry-run.
- Real mutation requires `--execute --yes`.
- Same-volume quarantine is planned as zero reclaim.
- Review-first and blocked classes do not broad-delete.
- External tools discover and visualize; Dopemux owns policy and mutation.

## Verification

Verification results are recorded in `PROOF.json`.
