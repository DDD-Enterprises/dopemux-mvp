# Independent L2 audit — PR #1389, dopemux-mvp (final audit -005, successor to -001..-004)

You are the **sole final independent auditor** for this pull request. You are not the
implementer (the implementer was Claude Code). Your verdict is binding evidence. You have
**one** call; there is no second pass. Be adversarial: look for claims the repository does
not support. Do not accept a commit message's or PR description's word for anything you can
check against a primary file.

## 0. Custody — do this first

The mounted workspace is a git worktree. Run `git rev-parse HEAD`. It **must** print exactly:

```
dd6ee150cd2abcf5b59149fac1059e4057924752
```

If it prints anything else, stop and return `NEEDS_SUPERVISOR` with sole finding
`CUSTODY_MISMATCH`. The base to diff against is the merge-base with `main`:

```
728d7c42e9ab3050d7b449935f463e0e71fbf7aa
```

Use `git diff 728d7c42e9ab..dd6ee150c -- <path>` and `git show 728d7c42e9ab:<path>` to see
before/after content, including deleted files. If you cannot run shell/file tools, say so and
set `TOOL_ACCESS=NONE`; do **not** claim verification you did not perform.

## 1. What this PR is

Earlier audits: -001 PASS on `808c0c054`, -002 PASS on `176d965e8` (after merging `main` #1395), and
**-003 FAIL on `9932d542f`** (blocking F-01: `agents-2.md`, `agents-3.md`, `gemini-2.md` had no
byte-identical twin at HEAD because the kept `agents.md`/`gemini.md` had gained a "Superseded" banner).
The repair commit `a289260ca` restores both kept files to their merge-base bytes. **-004 PASS on `370d84f59`**
was then made stale by two final doc fixes in `dd6ee150c` (Codex review); content is frozen at this head. Review feedback then changed tests, docs and a proof
manifest, so **you are auditing the final head `dd6ee150cd2abcf5b59149fac1059e4057924752` in full**; do not rely on either earlier
verdict, and re-check -003's F-01 independently. Earlier proof directories (`proof/TP-DMX-PR1389-L2-AUDIT-001/`, `-002/`,
`proof/pr_merge/embedded-audit/pr-1389/`) are history and out of scope.

Commits since the -002 audited head:

```
dd6ee150c docs(mcp): verify full-stack startup with mcp doctor; fix .mcp.json path
25ee89493 / d6126e724  proof(audit) commits for the superseded -004 audit
370d84f59 docs(mcp): label task-orchestrator as host-singleton, not a per-repo sidecar
a2ebadee9 docs(mcp): distinguish full-stack start-all from project-scoped mcp start
a289260ca docs(instructions): drop Superseded banners so deleted copies stay byte-identical
9932d542f proof(ccar-002): re-pin reference_only_agents hashes for edited .github/agents files
6c2079f79 docs(gemini): describe both thread-resolution gates accurately
74003f686 fix(review): pin bare --paths fail-closed; make quarantine sig test non-vacuous; correct CLI count
bbebfa5e1 / b4780306e  proof(audit) commits for the superseded -002 audit
```

**Filenames with spaces.** Three deleted files contain a space (`… DMPX IMPORT …`). Use
NUL-delimited listings (`git diff -z --name-status …`, `git ls-files -z`) or quote paths; a
whitespace-split check silently skips them and cannot substantiate points 1–2 for those files.

**Pre-existing `… (1).md` copies.** `docs/04-explanation/history/sourceFiles/` already contains ~679 tracked
`… (1).md` duplicates on `main` (added in 71f60c601, not by this PR). A deleted file whose twin is one of those
still counts as lossless; say which twin you matched.

**Do not create or modify any file in the mounted worktree.** Run checks inline or under `/tmp`.

## 2. Challenge each point — state UPHELD / DISPUTED / UNVERIFIABLE with evidence

1. **Deletions are lossless.** All 19 deleted files (`git diff -z --name-status 728d7c42e9ab..dd6ee150c  (NUL-delimited; filter status D)`) are claimed to be either byte-identical to a file kept in the tree, or identical to a kept file except for a prepended 12-line YAML frontmatter block (the `docs/archive/history/sourceFiles/` copies vs `docs/04-explanation/history/sourceFiles/`), or (`docker__mcp-servers__zen__zen-mcp-server__CLAUDE.md`) superseded by the live `docker/mcp-servers-source/pal/pal-mcp-server/CLAUDE.md`. For each deleted file, name its kept twin and verify (e.g. `git show 728d7c42e9ab:<deleted> | shasum -a 256` vs the twin; for archive copies compare after dropping the first 12 lines). Flag any deleted file with no lossless twin.
2. **No dangling references.** `git grep` at HEAD for each deleted file's basename (excluding `proof/`, `audit_inputs/`, `reports/`, `extraction/`, `claudedocs/` which are dated records). Confirm the two repointed references are correct: `docs/01-tutorials/installation-3.md` -> `contributing-zen.md`, and `config/docs_hygiene/docs_placement_policy.yaml` `docs/GEMINI.md` target -> `gemini.md`.
3. **Factual claims written into instruction files are true.** Spot-check at least these against primary files: ports in `services/.claude/claude.md` and `.github/copilot-instructions.md` vs `services/registry.yaml`, `.mcp.json`, `compose.yml` (adhd-engine host 3025 / container 8095; serena 3006; conport 3004 HTTP / 3005 MCP); Makefile targets cited (`make test`, `test-fast`, `test-integration`, `lint`, `format`, `type-check`, `install`, `install-dev`); the claim that `pytest.ini` overrides `[tool.pytest.ini_options]` in pyproject; the Pydantic v2 example in `config/.claude/claude.md` vs pyproject pins; `src/dopemux/cli.py` size and "~29 legacy inline commands"; every directory/script/tool path added to a subdirectory `.claude/claude.md` exists; GEMINI.md's `decide_thread_disposition` claim vs `src/dopemux_pr_merge_specialist/thread_resolution.py`; AGENTS.md §12.4's container naming vs `scripts/mcp-wrappers/task-orchestrator-http-singleton.sh` and `src/dopemux/mcp/docker_runtime.py`. Report any new false or misleading claim.
4. **Doctrine not altered.** AGENTS.md is authority #2. Verify the only AGENTS.md changes are: a §4 "Commands (step 9)" line, retitling the second duplicate `## 10.` heading to `## 10a.` (no other renumbering), `(§8)`->`(§9)` for the proof-and-finality pointer, and the §12.4 container-name commands. Verify §9 (not §8) actually holds proof/finality and `VERIFIED` so the `§8`->`§9` pointer fixes in `.claude/claude.md` and `.claude/modules/shared/governance-principles.md` are correct. Flag any change to truth order, authority, PAL/evidence-economy rules, or audit requirements.
5. **CCAR-002 re-pin integrity.** In `proof/CCAR-002/SOURCE_MANIFEST.json` verify exactly 10 `sha256` values changed, all in `active_personas`, none in `active_agents`, and each new value equals `shasum -a 256` of the file at HEAD. Verify the persona edits are limited to: `# Uses:` footer lines `zen-<tool>` -> `PAL <tool>` in 9 `*-dopemux.md` files, and removal of the `model: GPT-5` frontmatter line in `se-product-manager-advisor.agent.md`. Is editing a manifest the build script calls "immutable" adequately justified (precedent: #1388 commit "proof(ccar-002): re-pin active agent hashes", now merged on main)? Does anything else hash the manifest itself?
6. **Governance CLI change is fail-closed.** In `scripts/governance/validate_change_contract.py`, an explicit empty `--paths` previously fell back to the staged+unstaged working-tree diff; now it exits 2. Verify this cannot weaken any gate: find every caller (`.pre-commit-config.yaml`, `.github/workflows/*`, scripts) and confirm none passes `--paths` (or that the change only makes them stricter). Confirm non-empty `--paths` behaviour is unchanged.
7. **Test fix does not mask a product bug.** `tests/unit/test_pm_source_events.py` autouse fixture now clears `DOPEMUX_WORKSPACE_ROOT`, `WORKSPACE_ID`, `DOPEMUX_PROJECT_ROOT`. Read `_resolve_capture_repo_root` in `src/dopemux/pm/writes.py`: is clearing ambient env the right isolation, or does the failing test reveal production behaviour that should change instead? Do the tests that need `DOPEMUX_WORKSPACE_ROOT` still set it explicitly?
8. **Scope / allowlist.** Any changed path that does not fit the stated purpose? Any secret, absolute machine path, or machine-specific port/instance id introduced?

9. **Merge resolution (`176d965e8`).** Inspect the merge with `git show --cc 176d965e8` and `git diff 728d7c42e9ab dd6ee150c -- .claude/claude.md .claude/modules/shared/governance-principles.md AGENTS.md`. Verify: (a) in `.claude/claude.md` main's "PAL workflows and audit budgets" line and main's Control Tower / mandatory-hierarchy text survive unaltered, and every branch edit (Commands & Environment section, §9 pointers, link fixes) survives; (b) main's "M0 supervised contract convergence" section in `governance-principles.md` is intact; (c) the AGENTS.md commands line is now labelled "Commands (tests/lint step above)" and §4's tests/lint step is the one directly above it (main renumbered §4); (d) nothing from main was dropped or altered by the resolution (compare each conflicted file against `728d7c42e9ab` outside the branch's own hunks).
10. **Test fix in the merge.** `tests/governance/test_validate_change_contract.py::test_quarantine_deleted_sig_path_is_not_treated_as_carried` (added on main in #1395) previously diffed the real checkout's HEAD~1..HEAD; it now builds a hermetic two-commit temp repo (signed proof, then signature deleted) with `cwd=tmp_path`. Does the rewritten test still assert the same rule (a `.sig` present only as a deletion, no tip blob, does not trigger `quarantine_forbids_signature` / `proof_only_missing_signature`) — not a weaker one? Confirm no production code in `validate_change_contract.py` was changed by the merge beyond the branch's `--paths` fix.

11. **Review-fix tests (`74003f686`).** `test_cli_refuses_empty_without_base` must assert exit 2 exactly; `test_cli_bare_paths_never_falls_back_to_git_diff` (with and without `--base`) must fail if `changed_paths`/`_run_git` is consulted. `test_quarantine_deleted_sig_path_is_not_treated_as_carried` now copies `schemas/proof/embedded_audit.schema.json` into its temp repo and asserts `quarantine_mixed_proof_status` is absent (previously the check returned before reaching the signature rule — a vacuous pass); `test_quarantine_sig_carried_at_tip_is_forbidden` is its positive companion. Are these non-vacuous? (Optionally run them.) Is the CLI-count claim "27 (26 `@cli.command` + 1 `@click.command`)" in `.claude/claude.md` and `src/.claude/claude.md` exact?
12. **GEMINI.md thread-resolution rule (`6c2079f79`).** Verify against `src/dopemux_pr_merge_specialist/thread_resolution.py` (`decide_thread_disposition`, `resolve_verified_threads`) and `queue_drain.py` (`_resolve_applied_threads_after_validation`) that both described gates exist and behave as stated.
13. **reference_only re-pin (`9932d542f`).** Verify exactly 3 `sha256` values changed under `reference_only_agents` (dopemux-{implementer,reviewer,testgen}.agent.md), each equals `shasum -a 256` of the file at HEAD, and that every hash in `proof/CCAR-002/SOURCE_MANIFEST.json` now matches HEAD.

14. **F-01 repair (`a289260ca`).** Verify `docs/03-reference/instructions/agents.md` and `gemini.md` at HEAD are byte-identical to their merge-base versions, and that every one of the 19 deletions now has a byte-identical twin at HEAD (or, for the 5 `docs/archive/history/sourceFiles/` copies, a twin equal after dropping the first 12 lines). Report the twin for each deletion.

15. **`mcp start` vs `start-all` (`a2ebadee9`, `370d84f59`, `dd6ee150c`).** In `docker/.claude/claude.md`, `scripts/.claude/claude.md` and `.github/copilot-instructions.md`, verify against `src/dopemux/commands/mcp_commands.py` (`mcp_start_cmd`, `mcp_start_all_cmd`) that `dopemux mcp start-all` starts the full stack and `dopemux mcp start` only the repo sidecars. Confirm the docs no longer promise `--verify` health checks: in `mcp_start_all_cmd`, `--verify` is only forwarded when `scripts/start-all.sh` exists (it does not in this tree), so the recipes must pair start-all with `dopemux mcp doctor`. Check the scope labels against `mcp_catalog.yaml` and AGENTS.md §12.6: conport and dope-memory worktree-scoped; task-orchestrator a host-wide wrapper-singleton on :7890 serving one active project.

16. **`.mcp.json` path (`dd6ee150c`).** In `config/.claude/claude.md` Key Files, the MCP client config entry must be `.mcp.json` (repo-relative, the tracked root file), consistent with that file's own note.

## 3. Output format (return exactly this structure)

```
TOOL_ACCESS=<FULL|PARTIAL|NONE>
CUSTODY=<MATCH|MISMATCH>  head=<sha you observed>
VERDICT=<PASS|PASS_WITH_RISKS|FAIL|NEEDS_SUPERVISOR>
POINTS:
  1: <UPHELD|DISPUTED|UNVERIFIABLE> — <evidence>
  ... (1-16)
FINDINGS:
  - id: F-01
    severity: <CRITICAL|HIGH|MEDIUM|LOW|INFO>
    blocking: <true|false>
    title: ...
    body: ... (file:line evidence)
REMAINING_RISKS:
  - ...
```

`FAIL` if any deletion is lossy, any doctrine/authority rule changed, the re-pin does not match file bytes, or the CLI change weakens a gate. `PASS_WITH_RISKS` for non-blocking defects.
