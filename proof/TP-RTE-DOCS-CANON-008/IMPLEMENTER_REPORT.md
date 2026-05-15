# TP-RTE-DOCS-CANON-008 Implementer Report

## 1. Change summary

- Updated current RTE operator docs to present `dopemux rte` as the canonical operator command family.
- Reclassified `dopemux upgrades`, `dopemux extractor`, `dopemux truth`, hidden `dopemux extract truth-run`, v3/v4, `run_repscan.py`, and direct runner usage according to runtime evidence.
- Updated active index/reference docs surfaced by review so they no longer describe `dopemux upgrades` as the canonical RTE command namespace.
- Preserved `services/repo-truth-extractor/run_extraction_v5.py` as strongest v5 runtime authority and kept proof/source-truth boundaries explicit.
- Updated go-live posture to say full unattended go-live is not claimed and remains gated by P5 rerun, supervisor verdict, and proof-gated acceptance.
- Applied narrow task-packet index hygiene for PR #616 and this packet.

## 2. Authority used

- User-provided TP-RTE-DOCS-CANON-008 prompt
- `AGENTS.md`
- `PROJECT.md`
- `ARCHITECTURE.md`
- `docs/research/mcp-customization/dopemux-constraints/RULES.md`
- `docs/research/mcp-customization/dopemux-constraints/SYSTEM_RepoTruthExtractor.md`
- `docs/research/mcp-customization/dopemux-constraints/TRUTH_INTERFACES.md`
- `docs/research/mcp-customization/dopemux-constraints/TRUTH_CANONICALS.md`
- `docs/research/mcp-customization/dopemux-constraints/TRUTH_GAPS.md`
- `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `task-packets/INDEX.md`
- `src/dopemux/cli.py`
- `src/dopemux/commands/extractor_commands.py`
- `src/dopemux/commands/extract_commands.py`
- `services/repo-truth-extractor/run_extraction_v5.py`
- `services/repo-truth-extractor/run_extraction_v4.py`
- `services/repo-truth-extractor/run_extraction_v3.py`
- `services/repo-truth-extractor/run_repscan.py`
- `proof/TP-RTE-STRICT-ATTESTATION-007/IMPLEMENTER_REPORT.md`

## 3. Files created

- `task-packets/generated/TP-RTE-DOCS-CANON-008.json`
- `proof/TP-RTE-DOCS-CANON-008/PROOF.json`
- `proof/TP-RTE-DOCS-CANON-008/IMPLEMENTER_REPORT.md`

## 4. Files modified

- `README.md`
- `docs/00-MASTER-INDEX.md`
- `docs/02-how-to/extraction/batch-quickstart.md`
- `docs/02-how-to/extraction/repo-truth-extractor-user-guide.md`
- `docs/02-how-to/extraction/repo-truth-extractor-v5-first-live-run.md`
- `docs/02-how-to/extraction/run-prescan.md`
- `docs/02-how-to/extraction/run-v4-from-dopemux-cli.md`
- `docs/02-how-to/extraction/truth-run-command.md`
- `docs/03-reference/extraction/pipeline-reliability.md`
- `docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md`
- `docs/03-reference/truth/truth-canonicals.md`
- `docs/03-reference/truth/truth-data-events.md`
- `docs/03-reference/truth/truth-gaps.md`
- `docs/03-reference/truth/truth-interfaces.md`
- `docs/03-reference/truth/truth-scope.md`
- `docs/03-reference/truth/truth-systems.md`
- `task-packets/INDEX.md`

## 5. Docs behavior changes

- Current operator examples now use `dopemux rte` where the CLI exposes matching options.
- Active index/reference pointers now describe `dopemux rte` as canonical instead of advertising `dopemux upgrades`.
- `dopemux upgrades` is preserved only as a legacy compatibility alias.
- `dopemux extractor`, `dopemux truth`, and hidden `dopemux extract truth-run` are documented as deprecated/refusal/legacy surfaces, not v5 paths.
- First-live preset examples remain direct runner invocations because `--preset`, `--print-cost-preview`, `--print-config`, and `--output-root` are runner-level controls; the runbook labels that direct path as runner-level.
- v3 and `dopemux rte scan` remain legacy/gated, with explicit consent requirements where live execution is discussed.
- Proof packs, generated truth docs, dashboards, and coverage outputs are described as evidence artifacts, not source truth above runtime code/config/tests.

## 6. Runtime safety confirmation

- Runtime code changed: no
- Provider/model calls run: no
- Live extraction run: no
- External batch jobs submitted: no
- Promptsets touched: no
- Model routing touched: no
- Walker/prescan code touched: no
- Batch client or strict attestation code touched: no
- Dependency files touched: no

## 7. Validation commands and exit codes

- `gh pr view 616 --json number,state,mergedAt,mergeCommit,headRefName,baseRefName,title,url` -> 0
- `python -m json.tool task-packets/generated/TP-RTE-DOCS-CANON-008.json` -> 0
- `python -c "import json, pathlib; from jsonschema import Draft7Validator; schema=json.loads(pathlib.Path('docs/03-reference/spec/dopetask/dopetask-canonical-spec.json').read_text()); doc=json.loads(pathlib.Path('task-packets/generated/TP-RTE-DOCS-CANON-008.json').read_text()); errs=sorted(Draft7Validator(schema).iter_errors(doc), key=lambda e: e.path); [print('/'.join(map(str,e.path)) + ': ' + e.message) for e in errs]; raise SystemExit(0 if not errs else 1)"` -> 0
- focused stale-canonical phrase validation for `dopemux upgrades`, `dopemux extractor`, `dopemux truth`, and `dopemux extract truth-run` -> 0
- focused legacy/direct-path classification validation -> 0
- `rg -n "dopemux rte.*canonical|canonical.*dopemux rte|services/repo-truth-extractor/run_extraction_v5.py|evidence artifacts|evidence artifact|not source truth|do not outrank|DPMX_LIVE_OK|--execute|P5|supervisor verdict|proof-gated|unattended go-live" README.md docs/00-MASTER-INDEX.md docs/02-how-to/extraction docs/03-reference/extraction/pipeline-reliability.md docs/03-reference/systems/repo-truth-extractor docs/03-reference/truth` -> 0
- forbidden runtime diff-name check -> 1, expected no-match result
- `python -m compileall -q src/dopemux services/repo-truth-extractor` -> 0
- `git diff --check` -> 0
- `python -m json.tool proof/TP-RTE-DOCS-CANON-008/PROOF.json` -> 0
- `pre-commit run --files README.md docs/00-MASTER-INDEX.md docs/02-how-to/extraction/batch-quickstart.md docs/02-how-to/extraction/repo-truth-extractor-user-guide.md docs/02-how-to/extraction/repo-truth-extractor-v5-first-live-run.md docs/02-how-to/extraction/run-prescan.md docs/02-how-to/extraction/run-v4-from-dopemux-cli.md docs/02-how-to/extraction/truth-run-command.md docs/03-reference/extraction/pipeline-reliability.md docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md docs/03-reference/truth/truth-canonicals.md docs/03-reference/truth/truth-data-events.md docs/03-reference/truth/truth-gaps.md docs/03-reference/truth/truth-interfaces.md docs/03-reference/truth/truth-scope.md docs/03-reference/truth/truth-systems.md proof/TP-RTE-DOCS-CANON-008/IMPLEMENTER_REPORT.md proof/TP-RTE-DOCS-CANON-008/PROOF.json task-packets/INDEX.md task-packets/generated/TP-RTE-DOCS-CANON-008.json` -> 0

## 8. F4-CRIT-2 classification

CLOSED. Evidence: current operator docs and active index/reference pointers now canonicalize `dopemux rte`, stale `dopemux upgrades` canonicalization has been removed, `dopemux extractor` and `dopemux truth` are classified as refusal/legacy surfaces, direct runner usage is advanced/runner-level, v5 runtime authority is documented, and full unattended go-live is not claimed.

## 9. Index hygiene summary

- `TP-RTE-BATCH-005` already marked `Merged (PR #614)`.
- `TP-RTE-BATCH-E2E-006` already marked `Merged (PR #615)`.
- `TP-RTE-STRICT-ATTESTATION-007` changed from `Active` to `Merged (PR #616)` after PR #616 merged into `main`.
- `TP-RTE-DOCS-CANON-008` added as `Active`.

## 10. Commit readiness

Ready for commit. Proof JSON parse, pre-commit, diff review, and status capture passed.

## 11. Residual risks and UNKNOWNs

- No live/provider/batch validation was run because this TP is docs/governance only and forbids those calls.
- First-live runner-only flags remain direct-runner examples because runtime evidence shows they are not currently exposed by `dopemux rte run`.
- docs/assembled was not edited because current operator docs did not require generated pointer bundle updates.
