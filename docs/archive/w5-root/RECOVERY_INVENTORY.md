# Recovery Inventory

| status | branch/ref | sha | last_commit | likely_packet | subsystem | authority_slice | worktree_path | dirty | keep? | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| consolidated | recovery/consolidated | 4240d74ad | 2026-04-12 | recovery | multiple | multiple | /Users/hue/code/dopemux-mvp | dirty | keep | TARGET CONSOLIDATION BRANCH |
| consolidated | recover/statusline-docs-023e2e6 | 023e2e609 | 2026-04-12 | statusline-docs | docs | ControlPlane | - | - | archive | merged surgically into recovery/consolidated |
| consolidated | recover/security-review-5bac763 | 5bac76363 | 2026-04-12 | security-ci | operator | CI/Security | - | - | archive | merged surgically into recovery/consolidated |
| consolidated | recover/integration-tests-5bb06a7 | 5bb06a7f2 | 2026-04-12 | sync-manager-tests | operator/control | SyncManager | - | - | archive | merged surgically into recovery/consolidated |
| side-car | recover/adhd-engine-extraction-562efe1 | 562efe1f7 | 2026-04-12 | adhd-migration | cognitive-plane | ConPort | - | - | keep | CRITICAL ARCHIVE: contains full cognitive plane work from 2025 |
| active_candidate | packet/rte-07-post-v1-deferred | c3b98beda | 2026-04-12 | packet-07 | docs/rte | rte | /Users/hue/code/dopemux-mvp | dirty | keep | current branch (base for recovery) |
| active_candidate | packet/rte-06-operator-decisions | 461abfde3 | 2026-04-12 | packet-06 | docs/rte | rte | - | - | keep | record packet 06 decisions |
| stale_but_unique | origin/main | ec44f7b51 | 2025-10-04 | ? | ? | ? | - | - | keep | chore: Remove nested git repo from zen-mcp-server |
| stale_but_unique | origin/codex/add-option-to-specify-drive-type | 7d3a8a2c0 | 2025-06-14 | ? | operator | Codex | - | - | keep | feat: allow custom data root |
| stale_but_unique | origin/master | c7c505e80 | 2025-06-14 | ? | ? | ? | - | - | keep | remote ref |
| stale_but_unique | origin/codex/install-starship-theme-and-custom-zsh-plugin | d346ccdd3 | 2025-06-14 | ? | operator | Codex | - | - | keep | starship zsh theme |

## Summary of Changes
- Created `recovery/consolidated` based on `packet/rte-07-post-v1-deferred`.
- Surgically merged unique documentation, commands, and tests from orphan branches.
- Kept `recover/adhd-engine-extraction-562efe1` as a side-car for future architectural restoration.
