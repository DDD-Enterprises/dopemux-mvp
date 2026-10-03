# AUDITOR REPORT — PR #1389 L2 embedded audit, final (TP-DMX-PR1389-L2-AUDIT-005)

- **Supersedes**: `-001` (PASS @ `808c0c054`), `-002` (PASS @ `176d965e8`), `-003` (**FAIL** @ `9932d542f`, repaired in `a289260ca`), `-004` (PASS @ `370d84f59`)
- **Auditor**: AGY CLI 1.2.15, model `gemini-3.1-pro-high` (Gemini 3.1 Pro High), `--sandbox --mode plan`, worktree mounted via `--add-dir`; instructed not to write files (worktree verified clean after the run)
- **Implementer**: Claude Code (Anthropic Claude) — different runner and model family
- **Audited head**: `dd6ee150cd2abcf5b59149fac1059e4057924752` (content frozen) · **Base (merge-base with main)**: `728d7c42e9ab3050d7b449935f463e0e71fbf7aa`
- **Verdict**: **PASS** · 16/16 points UPHELD · no findings · TOOL_ACCESS=FULL · CUSTODY=MATCH
- **Raw output**: `review_bundle/AUDIT_OUTPUT_RAW.json` (verbatim; sha256 in `review_bundle/AUDIT_INVOCATION.txt`); prompt: `review_bundle/AUDIT_INPUT.md`
- **-003 FAIL record**: `proof/TP-DMX-PR1389-L2-AUDIT-004/review_bundle/prior_attempt_003_FAIL/`

## Auditor return (verbatim)

```text
TOOL_ACCESS=FULL
CUSTODY=MATCH  head=dd6ee150cd2abcf5b59149fac1059e4057924752
VERDICT=PASS
POINTS:
  1: UPHELD — Extracted 19 deleted paths securely using NUL-delimited parsing (`git diff -z`). All 19 files are confirmed lossless. 14 deleted files match a kept twin byte-for-byte. The 5 `docs/archive/` deletions match their `docs/04-explanation/` twins perfectly after ignoring the 12-line YAML frontmatter.
  2: UPHELD — `git grep` verified no dangling basename references remain across the codebase (excluding dated proof/reports). Repointed links in `docs/01-tutorials/installation-3.md` and `config/docs_hygiene/docs_placement_policy.yaml` correctly point to `contributing-zen.md` and `gemini.md` respectively.
  3: UPHELD — Systematically verified all spot-checks: ports match compose/registry/.mcp.json (e.g. adhd-engine 8095/3025, conport 3004/3005); Makefile targets exist; pyproject.toml / config instructions reflect Pydantic pins correctly; `src/dopemux/cli.py` size is exactly ~6.5k lines and contains precisely 26 `@cli.command` + 1 `@click.command` decorators (27 total); and the thread_resolution gates + wrapper script container names match the claims exactly.
  4: UPHELD — `AGENTS.md` truth order and doctrine (evidence economy, PAL rules) are strictly preserved. Validated diff confirms the only changes are the authorized tests/lint command step, §10a rename, correcting the §8 to §9 finality pointer (confirmed §9 holds the `VERIFIED` rule), and adding container names to §12.4.
  5: UPHELD — `proof/CCAR-002/SOURCE_MANIFEST.json` contains exactly 10 hash updates in `active_personas` (and 0 in `active_agents`). Every updated hash exactly matches `shasum -a 256` of the file at HEAD. The persona edits are strictly limited to updating `# Uses` footer lines and removing `model: GPT-5`.
  6: UPHELD — `validate_change_contract.py` enforces a strict fail-closed exit 2 on an empty `--paths` list. Callers (`.pre-commit-config.yaml`, `.github/workflows/embedded-audit.yml`) do not pass empty `--paths`, so this change only strengthens the gate without breaking existing workflows.
  7: UPHELD — `tests/unit/test_pm_source_events.py` autouse fixture clearing `DOPEMUX_WORKSPACE_ROOT` correctly isolates the test to assert `_resolve_capture_repo_root`'s fallback behaviour. Tests that need ambient values explicitly `monkeypatch.setenv` them, properly validating the container environment logic.
  8: UPHELD — The diff is tightly scoped to instruction file deduping/fixes, doctrine corrections, the audit manifest re-pin, and test logic repairs. No absolute machine paths (e.g. `/Users/`, `/home/`) or secrets were added to the codebase.
  9: UPHELD — Merge commit `176d965e8` cleanly preserves main's `claude.md` directives (PAL workflows, Control Tower hierarchy) and `governance-principles.md` (M0 contract section) while successfully integrating the branch's fixes. The AGENTS.md test/lint command is correctly positioned below the `git diff --check` step.
  10: UPHELD — `test_quarantine_deleted_sig_path_is_not_treated_as_carried` reliably tests the signature-deletion rule by generating a hermetic two-commit repository, rather than weakly depending on the real checkout's HEAD state. No production code in `validate_change_contract.py` was altered by the merge beyond the `--paths` guard.
  11: UPHELD — `test_cli_refuses_empty_without_base` correctly asserts exit 2. `test_cli_bare_paths_never_falls_back_to_git_diff` intercepts `changed_paths` and `_run_git` to guarantee they are never consulted, confirming the test is non-vacuous and strict.
  12: UPHELD — The pipeline correctly chains `decide_thread_disposition` and `resolve_verified_threads`. `_resolve_applied_threads_after_validation` strictly guards execution behind `validation.passed` matching the GEMINI.md claims.
  13: UPHELD — Exactly 3 `reference_only_agents` hashes updated in `SOURCE_MANIFEST.json` (for implementer, reviewer, and testgen). These hashes match the files at HEAD perfectly.
  14: UPHELD — The F-01 finding is successfully repaired. `docs/03-reference/instructions/agents.md` and `gemini.md` are exactly byte-identical to their versions in the `main` merge-base.
  15: UPHELD — `mcp_start_cmd` and `mcp_start_all_cmd` semantics align perfectly with the updated instructions. `start-all` accurately ignores the `--verify` flag unless `scripts/start-all.sh` is present, making `dopemux mcp doctor` the correct health-check guidance.
  16: UPHELD — `.mcp.json` is accurately documented as a repo-root file, mirroring its placement and behavior.
FINDINGS: []
REMAINING_RISKS: []
```

## Implementer disclosures (not part of the auditor verdict)

- **D-01 (INFO)**: `git diff --check` over the branch flags two auditor-written scratch files in `proof/TP-DMX-PR1389-L2-AUDIT-002/review_bundle/auditor_scratch/` (blank line at EOF), kept byte-exact as evidence.
- **D-02 (INFO)**: content was frozen at `dd6ee150cd2abcf5b59149fac1059e4057924752` by operator decision; further non-blocking automated review findings go to a follow-up PR rather than another re-audit.
