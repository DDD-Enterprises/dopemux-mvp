# AUDITOR REPORT — PR #1389 L2 embedded audit, final (TP-DMX-PR1389-L2-AUDIT-004)

- **Supersedes**: `-001` (PASS @ `808c0c054`), `-002` (PASS @ `176d965e8`, stale after merging `main`), `-003` (**FAIL** @ `9932d542f`)
- **Auditor**: AGY CLI 1.2.15, model `gemini-3.1-pro-high` (Gemini 3.1 Pro High), `--sandbox --mode plan`, worktree mounted via `--add-dir`; instructed not to write files (worktree verified clean after the run)
- **Implementer**: Claude Code (Anthropic Claude) — different runner and model family
- **Audited head**: `370d84f59b641ed04c4d8e48d241589d149eebbc` · **Base (merge-base with main)**: `728d7c42e9ab3050d7b449935f463e0e71fbf7aa`
- **Verdict**: **PASS** · 15/15 points UPHELD · TOOL_ACCESS=FULL · CUSTODY=MATCH
- **Raw output**: `review_bundle/AUDIT_OUTPUT_RAW.json` (verbatim; sha256 in `review_bundle/AUDIT_INVOCATION.txt`); prompt: `review_bundle/AUDIT_INPUT.md`

## Auditor return (verbatim)

```text
TOOL_ACCESS=FULL
CUSTODY=MATCH  head=370d84f59b641ed04c4d8e48d241589d149eebbc
VERDICT=PASS
POINTS:
  1: UPHELD — All 19 deleted files have a lossless kept twin. The redundant files in `docs/03-reference/instructions/` match their canonical counterparts exactly. The `docs/04-explanation/history/sourceFiles/` copies perfectly match pre-existing `(1).md` files. The deleted `docs/archive/history/sourceFiles/` copies match the kept `(1).md` copies after excluding 12 lines of YAML frontmatter. The deleted `zen-mcp-server__CLAUDE.md` accurately supersedes to `docker/mcp-servers-source/pal/pal-mcp-server/CLAUDE.md`.
  2: UPHELD — `git grep` returned no dangling references for the 19 deleted basenames (excluding `proof/`, `audit_inputs/`, `reports/`, `extraction/`, `claudedocs/`). Repointed references correctly point to `contributing-zen.md` and `gemini.md`.
  3: UPHELD — Verified all factual claims: ports strictly match `registry.yaml` and `compose.yml`; Make targets exist; `pytest.ini` and `pyproject.toml` pins (Pydantic v2) exist; `cli.py` size (~6.5k lines) and command count (exactly 27 decorators) match; all `.claude/claude.md` directory additions exist at HEAD; thread logic in code matches `GEMINI.md`; container naming conventions accurately match `scripts/mcp-wrappers/task-orchestrator-http-singleton.sh` and `src/dopemux/mcp/docker_runtime.py`.
  4: UPHELD — The `AGENTS.md` diff only renames step 10 to 10a, updates a §8 pointer to §9, adds the container log paths, and correctly labels the "Commands" block. Section 9 is the true "Proof and Finality" section containing the `VERIFIED` rule. No doctrine, truth order, or PAL/evidence-economy rules were weakened or altered.
  5: UPHELD — In `proof/CCAR-002/SOURCE_MANIFEST.json`, exactly 10 hashes updated in `active_personas` (none in `active_agents`) and match their HEAD hashes. The only changes in the persona files were migrating `# Uses: zen-<tool>` to `PAL <tool>` and stripping `model: GPT-5` from `se-product-manager-advisor`. Re-pinning an immutable manifest file in the same PR follows established precedent (#1388).
  6: UPHELD — `validate_change_contract.py` now explicitly traps an empty `--paths` list and exits with code 2, failing closed rather than silently falling back. No CI workflows or scripts in the tree invoke it with a bare empty `--paths`, meaning gates stay strict without breaking.
  7: UPHELD — `test_pm_source_events.py` now correctly uses `monkeypatch.delenv` to clear ambient `DOPEMUX_WORKSPACE_ROOT` variables, ensuring host environment leaks do not mask production behavior. Tests needing the variable correctly set it to `tmp_path`.
  8: UPHELD — Only safe, PR-scoped doc, test, and config files were changed. No secrets, unexpected absolute paths, or machine-specific IDs were introduced.
  9: UPHELD — The merge resolution at `176d965e8` cleanly incorporated main's new clauses ("PAL workflows", "M0 supervised contract convergence", and step numbering) without dropping any branch-specific fixes or altering main's edits.
  10: UPHELD — `test_quarantine_deleted_sig_path_is_not_treated_as_carried` was rewritten to use a hermetic, temporary 2-commit repo, protecting the test against state pollution from the real checkout's branch tips, while still asserting that a `.sig` deletion does not yield a quarantine block. Production logic in `validate_change_contract.py` remained unaffected outside the explicit `--paths` check.
  11: UPHELD — The review-fix tests rigorously assert the new logic. `test_cli_refuses_empty_without_base` tests for `exit 2`, and `test_cli_bare_paths_never_falls_back_to_git_diff` effectively stubs git invocations to fail the test if the fallback is triggered. The CLI count of "26 `@cli.command` + 1 `@click.command`" is exactly accurate.
  12: UPHELD — `decide_thread_disposition` properly enforces the green validation / no newer objection logic, and `_resolve_applied_threads_after_validation` relies on `validation.passed`, safely resolving threads exactly as stated.
  13: UPHELD — Exactly 3 values updated in `reference_only_agents` in the CCAR-002 manifest (`dopemux-implementer.agent.md`, `dopemux-reviewer.agent.md`, `dopemux-testgen.agent.md`), correctly matching the new `shasum -a 256` of the files at HEAD.
  14: UPHELD — `docs/03-reference/instructions/agents.md` and `gemini.md` are exactly byte-identical to their `728d7c42e9ab` base versions. All 19 deletions map to byte-identical twins (or post-12-line strip equivalents): `agents-[2,3].md` -> `agents.md`, `claude-2-moved-2.md` -> `claude-3.md`, `codex-[...].md` -> `codex[-3].md`, `gemini-2.md` -> `gemini.md`, `project-*` -> their canonical names. The `04-explanation` copies match the pre-existing `(1).md` copies, and `archive` copies match the same after the frontmatter strip.
  15: UPHELD — `mcp_start_all_cmd` triggers full ecosystem ignition (`start-all.sh`), while `mcp_start_cmd` operates only on the repo sidecars via the runtime lifecycle logic. The `--verify` flag exists. The `mcp_catalog.yaml` confirms `task-orchestrator` as a host-wide wrapper-singleton serving a single project on port 7890, exactly as documented.
FINDINGS:
  - id: F-01
    severity: INFO
    blocking: false
    title: "Lossless Documentation Deduplication"
    body: "Archive and reference directories were safely pruned of redundant identical files, effectively reducing noise without losing any genuine historical context (git blob preservation guarantees integrity)."
REMAINING_RISKS:
  - "None. The PR changes are isolated to safely repinning hashes, deleting noise, ensuring CI isolation, and strict validation, without modifying any underlying runtime doctrine or product logic."
```

## Prior attempt -003 (FAIL) and repair

The -003 audit of `9932d542f` returned FAIL with one blocking finding, verbatim below. Repair `a289260ca` restored `docs/03-reference/instructions/agents.md` and `gemini.md` to their merge-base bytes (operator chose this over restating the rule). -004 point 14 independently re-verified the repair and all 19 twins. Full -003 prompt and raw output: `review_bundle/prior_attempt_003_FAIL/`.

```
TOOL_ACCESS=FULL
CUSTODY=MATCH  head=9932d542f68316d7f05a6ba8d60603065dc85bcf
VERDICT=FAIL
POINTS:
  1: DISPUTED — `docs/03-reference/instructions/agents-2.md`, `agents-3.md`, and `gemini-2.md` do not have byte-identical or frontmatter-stripped twins kept in the tree at HEAD. Their intended twins (`agents.md`, `gemini.md`) were modified in this PR to include a `> **Superseded (2026-10-02)**` warning, meaning the deleted `-2`/`-3` files are not byte-identical to any kept file.
  2: UPHELD — `git grep` confirmed no dangling references exist for any deleted file basename, and both repointed targets (`contributing-zen.md` and `gemini.md`) are correct.
  3: UPHELD — Spot checks against `services/registry.yaml`, `.mcp.json`, `compose.yml`, `Makefile`, `pytest.ini`, `pyproject.toml`, and CLI counts (26 `@cli.command` + 1 `@click.command`) exactly match the claims written into the instruction files, and all added directory/script paths exist.
  4: UPHELD — `AGENTS.md` changes are strictly limited to the allowed commands string additions and numbering fixes, and §9 correctly holds the proof/finality rules. No truth order, authority, or PAL rules were altered.
  5: UPHELD — Exactly 10 `active_personas` hashes changed (and 0 `active_agents`), matching the `PAL <tool>` renaming and GPT-5 model removal. Precedent #1388 justifies the manifest repin, and nothing else hashes the manifest itself.
  6: UPHELD — `validate_change_contract.py` now explicitly exits 2 when an empty `--paths` is provided, preventing fallback to git diff while maintaining non-empty path list behavior and breaking no callers.
  7: UPHELD — Clearing the ambient env in `test_pm_source_events.py` is the correct isolation because `_resolve_capture_repo_root` falls back to host environment variables like `DOPEMUX_WORKSPACE_ROOT`, which was leaking into the test context and masking behavior.
  8: UPHELD — The allowlist strictly matches the stated scope (docs cleanup, persona updates, test fixes) and no secrets or machine-specific paths were introduced.
  9: UPHELD — The merge resolution correctly preserved main's doctrine lines ("PAL workflows", "M0 supervised contract") and branch edits without dropping any of main's changes outside the branch's hunks.
  10: UPHELD — The rewritten `test_quarantine_deleted_sig_path_is_not_treated_as_carried` correctly asserts the absence of the signature rules (`quarantine_forbids_signature`, etc.) in a hermetic two-commit repo without altering any production code beyond the `--paths` fix.
  11: UPHELD — The review-fix tests are non-vacuous, correctly asserting `code == 2` for `test_cli_refuses_empty_without_base`, and preventing fallback via monkeypatching in `test_cli_bare_paths_never_falls_back_to_git_diff`. The CLI count claim is exactly 27.
  12: UPHELD — Both `decide_thread_disposition` and `_resolve_applied_threads_after_validation` exist and enforce the green validation requirement for resolving applied and outdated threads exactly as claimed in `GEMINI.md`.
  13: UPHELD — Exactly 3 `reference_only_agents` hashes changed, and all hashes in the `CCAR-002` manifest now correctly match the files at HEAD.
FINDINGS:
  - id: F-01
    severity: HIGH
    blocking: true
    title: Lossy deletion of instruction files
    body: Point 1 claimed all 19 deleted files were lossless twins of a file kept in the tree. However, `docs/03-reference/instructions/agents-2.md`, `agents-3.md`, and `gemini-2.md` do not have an exact byte-match at HEAD, as their target twins (`agents.md`, `gemini.md`) were mutated in this PR to include a `Superseded` warning. This makes the deletion lossy with respect to the strict byte-identical rule.
REMAINING_RISKS:
  - Lossy deletion means exact history of the `-2` and `-3` variants is not perfectly preserved as live files in the tree at HEAD, though the content remains available in git history.

## Implementer disclosures (not part of the auditor verdict)

- **D-01 (INFO)**: dispatch preceded completion of the `Unit Tests` CI check (operator said continue); it finished PASS on `370d84f59b641ed04c4d8e48d241589d149eebbc` during the run.
- **D-02 (INFO)**: `git diff --check b4780306e` exits 2 on two auditor-written scratch files in `proof/TP-DMX-PR1389-L2-AUDIT-002/review_bundle/auditor_scratch/` (blank line at EOF); kept byte-exact as evidence (Codex thread r4172453293).
- **D-03 (INFO)**: auditor point 4 paraphrases the AGENTS.md change as "renames step 10 to 10a"; the actual change retitles the duplicate second `## 10.` *section* heading to `## 10a.` (§4's step numbering is untouched).
