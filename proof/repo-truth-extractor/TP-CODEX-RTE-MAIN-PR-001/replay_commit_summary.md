# Replay Commit Summary

## Source Replay Slice

Planned runtime-critical source commits:

1. `c660ab9df` `fix(repo-truth-extractor): recover deferred tp002-owned changes`
2. `2144d4e36` `fix(repo-truth-extractor): recover TP001 spend-cap logic from mixed runner`
3. `e14690d0d` `fix(repo-truth-extractor): recover TP003 bounded execution logic from mixed runner`
4. `0db7b8528` `fix(repo-truth-extractor): recover missing TP001 usage summary logic`
5. `91868d873` `feat(repo-truth-extractor): implement JSON repair provenance tracking and unify run status`
6. `6bc14c7bd` `fix(repo-truth-extractor): correct narrow post-tp004 live defects`
7. `d88a1bcc4` `fix(repo-truth-extractor): correct narrow bounded-live truth defect`
8. `9317a169d` `fix(repo-truth-extractor): correct narrow post-tp006 artifact truth contradiction`

## Replayed Commits

- `d4fc167d7` from `c660ab9df`
- `de544c137` from `2144d4e36`
- `ff29dd457` from `e14690d0d`
- `52d651b01` from `91868d873`
- `1052feba2` from `6bc14c7bd`

## Empty Replays

These source commits replayed as empty because their behavior was already preserved on the replay branch after earlier resolutions:

- `0db7b8528`
- `d88a1bcc4`
- `9317a169d`

## Bounded Repair Commit

- `c7250ecaf` `fix(repo-truth-extractor): restore selected-step validator replay integrity`

Reason:

- restore missing `return scope` in `validate_pre_live_gate_v25.py`
- make selected-step contract-map observed keys respect `--step`
- required so the replay branch would pass the packet validator command truthfully
