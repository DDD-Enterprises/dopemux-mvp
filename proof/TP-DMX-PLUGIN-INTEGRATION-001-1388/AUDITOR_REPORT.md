# Auditor Report — PR #1388 / Plugin integration (project enabledPlugins + plugin-skill routing)

**Verdict:** **PASS_WITH_RISKS**  
**Scope:** audit evidence only; never readiness/merge authority  
**Base:** `d39b691c7d420a95a1a1372a793623840b4e84b0`  
**Head:** `2c137b884719af77c5bc4b2c8124db13ea112d63`

## Scope and evidence

The diff is documentation and configuration only, confined to .claude/ and one proof manifest. I checked the objective claims directly with read-only tools: all 5 manifest hashes match recomputed sha256 values, the hooks block is byte-identical to base, all other pre-existing settings keys are unchanged, the enabledPlugins count is 25 as claimed, and the changed paths match the declared scope. The content does not weaken governance. It keeps Codex advisory, requires the PR route, preserves allowlist boundaries and gives the non-developer agents no new capabilities. The residual risks are the unpinned third-party marketplaces feeding preloaded skill text into a tool-bearing subagent, and the many machine-local claims that cannot be verified from the repo. Neither is a defect in the diff itself, so the verdict is PASS_WITH_RISKS rather than FAIL.

Validation status (auditor): PARTIAL: auditor spot-checks (manifest hashes, settings counts, hooks identity, changed-path scope) were run and passed. Operator suites (validate_change_contract.py, pre-commit, pytest 35/35) were NOT_RUN by this auditor and are unverified claims.

## Findings

- **F1 (RESOLVED):** SOURCE_MANIFEST integrity verified. I recomputed sha256 for all 5 active_agents entries (_index, architect, developer, project-manager, researcher) at head 2c137b884. Each matches the manifest value exactly. The manifest diff touches only those 5 hashes (10 lines changed, 5 insertions and 5 deletions).
- **F2 (RESOLVED):** The changed-file set from `git diff --name-only d39b691c7..HEAD` is exactly the 9 paths in the candidate metadata. All are under .claude/ or proof/CCAR-002/, which fits the stated plugin-integration scope. No code, workflow, or hook scripts changed.
- **F3 (RESOLVED):** .claude/settings.json: the `hooks` block is byte-identical to base (jq -S diff of .hooks is empty). All other top-level keys outside hooks, enabledPlugins and extraKnownMarketplaces are also identical to base. The change is purely additive: `extraKnownMarketplaces` (2 entries) and `enabledPlugins`.
- **F4 (RESOLVED):** enabledPlugins has 25 entries, matching the card's '25 explicit entries' claim. 7 are true (superpowers, codex, frontend-design, claude-md-management, pyright-lsp, andrej-karpathy-skills, superdevflow@synced) and 18 are false. There are no duplicate keys. The file parses as valid JSON.
- **F5 (RESOLVED):** The documentation is consistent with doctrine in the diff. Codex is explicitly advisory and never the §9.1 auditor. Finishing a branch is PR-route only. The packet allowlist stays the edit boundary. Plugin skills are subordinate to AGENTS.md. The 4 non-developer agents get no preloads. No agent `tools:` list gained `Skill`.
- **F6 (ACCEPTED_RISK):** developer.md adds `skills:` frontmatter that preloads two third-party plugin skills (`andrej-karpathy-skills:karpathy-guidelines`, `superpowers:verification-before-completion`). The developer agent has Bash, Edit and Write, so this is a prompt-injection surface that the card acknowledges.

## Remaining risks

- Supply chain: both new marketplaces (`openai/codex-plugin-cc`, `forrestchang/andrej-karpathy-skills`) are registered from GitHub with no ref or commit pin. The plugin version actually run is whatever each machine has installed, outside the repo. Skill text from a mutable third-party repo is injected into a subagent with Bash, Edit and Write. The card discloses this and says to re-read preloads after an update. It is a documented process control, not a technical one. Consider pinning a ref or SHA, or vendoring the 2.5 KB karpathy skill.
- Unverifiable machine-local claims (treated as claims, not evidence): the uninstalls of claude-mem, caveman, ck, hookify and feature-dev, the deletion of ~/.claude-mem (794 MB), `claude plugin list` results, the pyright 1.1.414 version, and `stopReviewGate: false`. The '~6 KB total' preload size and the 'preload names verified to load' statement could not be checked from the repo.
- claude.md directs the model to invoke several plugin skills automatically ('without being asked'). These skills are not in the repo and are only available if installed. The card adds a NOT_AVAILABLE fallback, which mitigates this. Behavior still varies by machine.
- `enabledPlugins` pins `hookify` and `feature-dev` to false for plugins the card says are uninstalled. This is a defensible guard but adds stale-looking config. Behavior of `code-review@claude-plugins-official` alongside the built-in `/code-review` is documented as UNKNOWN.
- The agent hash re-pin in SOURCE_MANIFEST means the proof bundle's generated_at (2026-07-31) and base_commit (683b2411) no longer describe the pinned contents. Only the hashes were refreshed. This is a minor provenance-labeling gap, not an integrity failure.
- The operator-reported results (validate_change_contract.py PASS at L2, pre-commit PASS, 35/35 tests PASS) were not re-run by this audit.

## Audit history

1. Round 1, head `1bf07278c`: tool-less Sonnet (`--tools ""`). Verdict **NEEDS_SUPERVISOR**: card claimed 28 enabledPlugins entries (actual 25), karpathy-skills marketplace undeclared, and manifest hashes not recomputable without tools.
2. Repair `2c137b884`: count corrected, marketplace registered, supply-chain note added. One repair attempt, per evidence-economy policy.
3. Round 2, head `2c137b884719af77c5bc4b2c8124db13ea112d63`: Sonnet with read-only tools in safe mode. Verdict **PASS_WITH_RISKS**.

## Route receipt

Claude Code 2.1.287, selector `sonnet` (observed `claude-sonnet-5-5`), high effort, plan permission mode, `--restricted --safe-mode`, strict empty MCP config, tools Read/Grep/Glob plus Bash restricted to shasum/git diff/show/log/jq. 4 turns, exit 0, cost $0.1222. Implementer and auditor are separate sessions of the same model family. The operator explicitly authorized implementer-orchestrated audit and signing.
