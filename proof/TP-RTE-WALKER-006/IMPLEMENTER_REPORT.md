# TP-RTE-WALKER-006 Implementer Report

## 1. Change summary

Hardened the Repo Truth Extractor prescan corpus path so default walker input excludes generated RTE outputs, proof/audit outputs, local operator/runtime metadata, common caches, and known secret-bearing files before `FileEntry` creation or hashing.

The v5 integrated prescan stage now explicitly passes the shared default excludes into `LibPrescanConfig`, so the actual `run_integrated_prescan_stage` path uses the hardened walker behavior.

## 2. Authority used

- `AGENTS.md`
- `PROJECT.md`
- `docs/research/mcp-customization/dopemux-constraints/RULES.md`
- `docs/research/mcp-customization/dopemux-constraints/SYSTEM_RepoTruthExtractor.md`
- `docs/research/mcp-customization/dopemux-constraints/TRUTH_GAPS.md`
- `docs/research/mcp-customization/dopemux-constraints/TRUTH_INTERFACES.md`
- `task-packets/INDEX.md`
- `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `services/repo-truth-extractor/lib/prescan/models.py`
- `services/repo-truth-extractor/lib/prescan/corpus_walker.py`
- `services/repo-truth-extractor/run_extraction_v5.py`
- Existing tests under `services/repo-truth-extractor/tests/`

## 3. Files created

- `task-packets/generated/TP-RTE-WALKER-006.json`
- `proof/TP-RTE-WALKER-006/PROOF.json`
- `proof/TP-RTE-WALKER-006/IMPLEMENTER_REPORT.md`

## 4. Files modified

- `services/repo-truth-extractor/lib/prescan/models.py`
- `services/repo-truth-extractor/lib/prescan/corpus_walker.py`
- `services/repo-truth-extractor/run_extraction_v5.py`
- `services/repo-truth-extractor/tests/test_prescan_core_pipeline.py`
- `services/repo-truth-extractor/tests/test_prescan_v5_integration.py`
- `task-packets/INDEX.md`

## 5. Behavior changes

- Added shared prescan default exclude constants for base dependency/build outputs, RTE generated output trees, operator-local/runtime metadata, caches, and known secret-bearing file patterns.
- Changed `CorpusWalker` to normalize relative paths to POSIX form and skip effective exclude glob matches before adding them to the corpus inventory or hashing content.
- Preserved `.claude/**` for now because current runtime code and tests intentionally include `.claude` in non-prescan governance/boundary phases.
- Wired `run_integrated_prescan_stage` to pass `DEFAULT_PRESCAN_EXCLUDE_GLOBS` explicitly into `LibPrescanConfig`.

## 6. Tests added

- Generated-output default exclusion fixture.
- Nested generated-output exclusion fixture.
- Secret-bearing file exclusion fixture.
- Prescan manifest source-preservation and excluded-input regression.
- Integrated v5 prescan wrapper fixture proving generated and secret-bearing paths are absent from emitted `corpus_manifest.json`.

## 7. Validation commands and exit codes

- `python -m json.tool task-packets/generated/TP-RTE-WALKER-006.json` -> 0
- Task packet Draft7 schema validation -> 0
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_prescan_core_pipeline.py` -> 0
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_prescan_v5_integration.py` -> 0
- `python -m compileall -q services/repo-truth-extractor` -> 0
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests -k "walker or prescan or corpus or exclude or secret"` -> 1; same failing subset reproduced on untouched starting checkout.
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_output_safety.py` -> 0
- `RTE_DISABLE_LIVE_LLM_IN_TESTS=1 pytest -q services/repo-truth-extractor/tests/test_prescan_core_pipeline.py services/repo-truth-extractor/tests/test_prescan_v5_integration.py` -> 0
- `python -m json.tool proof/TP-RTE-WALKER-006/PROOF.json` -> 0
- `git diff --check` -> 0
- `pre-commit run --files <changed allowlist files>` -> 0

## 8. Safety boundary confirmation

- No provider calls were run.
- No live extraction was run.
- No batch execution was run.
- No promptsets were touched.
- No model routing files were touched.
- No docs sweep was included.
- No dependency files were changed.
- No real extraction artifacts were mutated.

## 9. Commit readiness

Manual codereview of the scoped diff passed with no blockers found. Pre-commit passed for changed allowlist files. Commit, push, and PR creation remain pending at this report update.

## 10. Residual risks and UNKNOWNs

- Broader prescan-related pytest selection still has 7 failures that reproduce on the untouched starting checkout; they are not addressed by this TP.
- `.claude/**` default prescan treatment remains intentionally unchanged due current runtime evidence. Whether prescan should classify or exclude parts of `.claude/**` is still `UNKNOWN`.
- The walker still discovers files under excluded trees before skipping them because it uses `Path.rglob`; the poisoning blocker is closed at input/inventory level, not optimized at traversal-pruning level.
