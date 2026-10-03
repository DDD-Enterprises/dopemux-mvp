# Independent L2 audit — PR #1389, dopemux-mvp

You are the **sole final independent auditor** for this pull request. You are not the
implementer (the implementer was Claude Code). Your verdict is binding evidence. You have
**one** call; there is no second pass. Be adversarial: look for claims the repository does
not support. Do not accept a commit message's or PR description's word for anything you can
check against a primary file.

## 0. Custody — do this first

The mounted workspace is a git worktree. Run `git rev-parse HEAD`. It **must** print exactly:

```
808c0c0549032761813e7eebeed1f8e8f99b1ccd
```

If it prints anything else, stop and return `NEEDS_SUPERVISOR` with sole finding
`CUSTODY_MISMATCH`. The base to diff against is the merge-base with `main`:

```
e047b542206df1d43d1f3b35cec2329769c39fcb
```

Use `git diff e047b542206d..808c0c0549 -- <path>` and `git show e047b542206d:<path>` to see
before/after content, including deleted files. If you cannot run shell/file tools, say so and
set `TOOL_ACCESS=NONE`; do **not** claim verification you did not perform.

## 1. What this PR is

Seven commits, 41 files changed (19 deletions). It edits agent-instruction surfaces (CLAUDE.md
family, AGENTS.md, GEMINI.md, `.github/copilot-instructions.md`, `.github/agents/*`, personas),
removes duplicate/historical copies, re-pins persona hashes in `proof/CCAR-002/SOURCE_MANIFEST.json`,
changes one CLI behaviour in `scripts/governance/validate_change_contract.py`, and fixes one test.

```
98b28b18f docs(agents): optimize agent instruction files and prune historical CLAUDE.md copies
513f55980 fix(governance): refuse bare --paths instead of falling back to working-tree diff
3bf5b94cd fix(personas): zen-* tool refs -> PAL; drop Copilot-only model pin
ac212b14c proof(ccar-002): re-pin 10 persona hashes after zen->PAL footer fixes
cb3f6dbb4 docs(instructions): dedupe -2/-3/-moved-2 copies; fix AGENTS §12.4 container names
eb17f498e test(pm): make source-event tests hermetic to ambient workspace env
808c0c054 docs(claude): cite CCAR-002 re-pin as precedent, not doctrine
```

## 2. Challenge each point — state UPHELD / DISPUTED / UNVERIFIABLE with evidence

1. **Deletions are lossless.** All 19 deleted files (`git diff --name-status e047b542206d..808c0c0549 | grep ^D`) are claimed to be either byte-identical to a file kept in the tree, or identical to a kept file except for a prepended 12-line YAML frontmatter block (the `docs/archive/history/sourceFiles/` copies vs `docs/04-explanation/history/sourceFiles/`), or (`docker__mcp-servers__zen__zen-mcp-server__CLAUDE.md`) superseded by the live `docker/mcp-servers-source/pal/pal-mcp-server/CLAUDE.md`. For each deleted file, name its kept twin and verify (e.g. `git show e047b542206d:<deleted> | shasum -a 256` vs the twin; for archive copies compare after dropping the first 12 lines). Flag any deleted file with no lossless twin.
2. **No dangling references.** `git grep` at HEAD for each deleted file's basename (excluding `proof/`, `audit_inputs/`, `reports/`, `extraction/`, `claudedocs/` which are dated records). Confirm the two repointed references are correct: `docs/01-tutorials/installation-3.md` -> `contributing-zen.md`, and `config/docs_hygiene/docs_placement_policy.yaml` `docs/GEMINI.md` target -> `gemini.md`.
3. **Factual claims written into instruction files are true.** Spot-check at least these against primary files: ports in `services/.claude/claude.md` and `.github/copilot-instructions.md` vs `services/registry.yaml`, `.mcp.json`, `compose.yml` (adhd-engine host 3025 / container 8095; serena 3006; conport 3004 HTTP / 3005 MCP); Makefile targets cited (`make test`, `test-fast`, `test-integration`, `lint`, `format`, `type-check`, `install`, `install-dev`); the claim that `pytest.ini` overrides `[tool.pytest.ini_options]` in pyproject; the Pydantic v2 example in `config/.claude/claude.md` vs pyproject pins; `src/dopemux/cli.py` size and "~29 legacy inline commands"; every directory/script/tool path added to a subdirectory `.claude/claude.md` exists; GEMINI.md's `decide_thread_disposition` claim vs `src/dopemux_pr_merge_specialist/thread_resolution.py`; AGENTS.md §12.4's container naming vs `scripts/mcp-wrappers/task-orchestrator-http-singleton.sh` and `src/dopemux/mcp/docker_runtime.py`. Report any new false or misleading claim.
4. **Doctrine not altered.** AGENTS.md is authority #2. Verify the only AGENTS.md changes are: a §4 "Commands (step 9)" line, retitling the second duplicate `## 10.` heading to `## 10a.` (no other renumbering), `(§8)`->`(§9)` for the proof-and-finality pointer, and the §12.4 container-name commands. Verify §9 (not §8) actually holds proof/finality and `VERIFIED` so the `§8`->`§9` pointer fixes in `.claude/claude.md` and `.claude/modules/shared/governance-principles.md` are correct. Flag any change to truth order, authority, PAL/evidence-economy rules, or audit requirements.
5. **CCAR-002 re-pin integrity.** In `proof/CCAR-002/SOURCE_MANIFEST.json` verify exactly 10 `sha256` values changed, all in `active_personas`, none in `active_agents`, and each new value equals `shasum -a 256` of the file at HEAD. Verify the persona edits are limited to: `# Uses:` footer lines `zen-<tool>` -> `PAL <tool>` in 9 `*-dopemux.md` files, and removal of the `model: GPT-5` frontmatter line in `se-product-manager-advisor.agent.md`. Is editing a manifest the build script calls "immutable" adequately justified (precedent: #1388 commit "proof(ccar-002): re-pin active agent hashes", now merged on main)? Does anything else hash the manifest itself?
6. **Governance CLI change is fail-closed.** In `scripts/governance/validate_change_contract.py`, an explicit empty `--paths` previously fell back to the staged+unstaged working-tree diff; now it exits 2. Verify this cannot weaken any gate: find every caller (`.pre-commit-config.yaml`, `.github/workflows/*`, scripts) and confirm none passes `--paths` (or that the change only makes them stricter). Confirm non-empty `--paths` behaviour is unchanged.
7. **Test fix does not mask a product bug.** `tests/unit/test_pm_source_events.py` autouse fixture now clears `DOPEMUX_WORKSPACE_ROOT`, `WORKSPACE_ID`, `DOPEMUX_PROJECT_ROOT`. Read `_resolve_capture_repo_root` in `src/dopemux/pm/writes.py`: is clearing ambient env the right isolation, or does the failing test reveal production behaviour that should change instead? Do the tests that need `DOPEMUX_WORKSPACE_ROOT` still set it explicitly?
8. **Scope / allowlist.** Any changed path that does not fit the stated purpose? Any secret, absolute machine path, or machine-specific port/instance id introduced?

## 3. Output format (return exactly this structure)

```
TOOL_ACCESS=<FULL|PARTIAL|NONE>
CUSTODY=<MATCH|MISMATCH>  head=<sha you observed>
VERDICT=<PASS|PASS_WITH_RISKS|FAIL|NEEDS_SUPERVISOR>
POINTS:
  1: <UPHELD|DISPUTED|UNVERIFIABLE> — <evidence>
  ... (1-8)
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
