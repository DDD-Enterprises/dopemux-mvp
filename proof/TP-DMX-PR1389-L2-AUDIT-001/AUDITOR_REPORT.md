# AUDITOR REPORT — PR #1389 L2 embedded audit (TP-DMX-PR1389-L2-AUDIT-001)

- **Auditor**: AGY CLI 1.2.15, model `gemini-3.1-pro-high` (Gemini 3.1 Pro High), `--sandbox --mode plan`, worktree mounted via `--add-dir`
- **Implementer**: Claude Code (Anthropic Claude) — auditor is a different runner and model family
- **Audited head**: `808c0c0549032761813e7eebeed1f8e8f99b1ccd` · **Base (merge-base with main)**: `e047b542206df1d43d1f3b35cec2329769c39fcb`
- **Verdict**: **PASS** · TOOL_ACCESS=FULL · CUSTODY=MATCH
- **Raw output**: `review_bundle/AUDIT_OUTPUT_RAW.json` (verbatim, sha256 in `review_bundle/AUDIT_INVOCATION.txt`); prompt: `review_bundle/AUDIT_INPUT.md`

## Auditor return (verbatim)

```text
TOOL_ACCESS=FULL
CUSTODY=MATCH  head=808c0c0549032761813e7eebeed1f8e8f99b1ccd
VERDICT=PASS
POINTS:
  1: UPHELD — All 19 deleted files were verified to be lossless. Deleted files were checked against the base tree (`e047b542206d`) and confirmed to be either byte-identical to kept files (e.g., `docs/03-reference/instructions/agents.md`), identical to kept files after excluding a 12-line YAML frontmatter block (e.g., `docs/04-explanation/history/sourceFiles/docs__HISTORICAL__DMPX IMPORT__claude.md`), or specifically superseded (e.g., the deleted `zen` CLAUDE.md replaced by `docker/mcp-servers-source/pal/pal-mcp-server/CLAUDE.md`).
  2: UPHELD — `git grep` at HEAD across the repository (excluding `proof/`, `audit_inputs/`, `reports/`, `extraction/`, and `claudedocs/`) returned zero matches for any of the 19 deleted file basenames. The repointed references in `docs/01-tutorials/installation-3.md` and `config/docs_hygiene/docs_placement_policy.yaml` were confirmed correctly updated.
  3: UPHELD — Verified all factual claims against primary files: ports match `services/registry.yaml` and `compose.yml`; `Makefile` contains all cited targets; `pytest.ini` and `pyproject.toml` both exist; Pydantic pins match `pyproject.toml`; `src/dopemux/cli.py` size is ~6.5k lines and registers 27 legacy inline commands; all new paths documented in `.claude/claude.md` files (like `src/dopemux/commands/`, `services/`, `tests/`, and `tools/` additions) exist on disk; and `decide_thread_disposition` exists in `src/dopemux_pr_merge_specialist/thread_resolution.py`. The `AGENTS.md` §12.4 container naming explicitly matches the deterministic slugs returned by `docker_runtime.py` and wrapped in `scripts/mcp-wrappers/task-orchestrator-http-singleton.sh`.
  4: UPHELD — A strict diff of `AGENTS.md` confirmed only the specified changes were made: adding step 9 Makefile commands, renaming heading 10 to 10a, pointing to §9, and documenting container names. Section 9 properly defines the proof/finality and `VERIFIED` rules. Doctrine, Truth Order, and evidence-economy boundaries remain completely unaltered.
  5: UPHELD — Exactly 10 hashes changed in `proof/CCAR-002/SOURCE_MANIFEST.json`, all under `active_personas`. An automated `shasum -a 256` check confirmed all 10 hashes perfectly match the updated files at HEAD. File diffs on `.claude/personas/*.md` verify edits were strictly limited to swapping `zen-<tool>` to `PAL <tool>` and removing the GPT-5 model pin. Given #1388 as precedent, manually repinning the hashes within a PR before the build script's `--check` is adequately justified, and the manifest is not itself hashed.
  6: UPHELD — The update to `scripts/governance/validate_change_contract.py` now explicitly traps `if not args.paths:` and exits with code 2, failing-closed. This actively prevents a silent bypass that would fall back to the working-tree diff. Calls in `.pre-commit-config.yaml` and `.github/workflows/embedded-audit.yml` rely on `--base` and `--head`, avoiding `--paths`, meaning CI logic is unimpacted while the script is globally stricter.
  7: UPHELD — In `src/dopemux/pm/writes.py`, `_resolve_capture_repo_root` falls back to `DOPEMUX_WORKSPACE_ROOT` to properly function inside the containerized Task Orchestrator. The test failure occurred because ambient environment variables leaked a real host repository root into the test. Purging these with `monkeypatch.delenv` is the correct hermetic isolation. Tests like `test_emit_pm_promotable_source_event_resolves_repo_root_from_workspace_env` that explicitly rely on it continue to use `setenv`. This fixes a host leakage issue without masking a product bug.
  8: UPHELD — All modified files strictly align with agent instructions, document deduplication, testing isolation, governance script tightening, or manifest repinning. Grepping and visually inspecting the diff confirmed no machine-specific absolute paths, unprotected secrets, or unauthorized directories were introduced.
FINDINGS:
  - id: F-01
    severity: INFO
    blocking: false
    title: "Lossless Documentation Deduplication"
    body: "The historical archive and reference directories successfully shed multiple identical redundant files. Because Git blob preservation maintains identically hashed copies, no historical records were genuinely lost, and the documentation bloat is effectively reduced."
REMAINING_RISKS:
  - "None. The modifications successfully tighten authority, correct tool aliases, remove historical bloat, and restrict validation script parameters safely."
```

## Implementer disclosure (post-audit, not part of the auditor verdict)

- **D-01 (LOW, OPEN)**: `.claude/claude.md` and `src/.claude/claude.md` say `cli.py` hosts "~29 legacy inline commands". The auditor's count is 27; an implementer recount at `808c0c0549032761813e7eebeed1f8e8f99b1ccd` gives 26 `@cli.command` + 1 `@click.command` = 27. The approximation overstates by 2. Not corrected on this PR because any content change would move the audited head; to be fixed in a follow-up.
