# Dopemux v1 Packet Baseline

## Baseline Choice
Use the following as v1 packet baselines:
- `task-packets/TP-PM-ARCH-04A.md`
- `task-packets/TP-PM-ARCH-04B.md`

These are the closest concrete packet examples with explicit objective, scope, invariants, commands, acceptance, rollback, and stop conditions.

## Packet Truth Rule
Filesystem packet files are truth.

Do not use `task-packets/INDEX.md` as packet registry authority.

## v1 Packet Minimum Fields
A v1 packet should include:
- `id`
- `objective`
- `scope`
- `invariants`
- `commands`
- `acceptance`
- `rollback`
- `stop_conditions`
- `base_commit`
- `task_reference` (if linked)
- `worker/worktree assignment`

## Packet Constraints
- packet IDs must resolve to actual files
- packet identity must survive task-manager selection
- packet IDs must be normalized before launcher automation
- packet state must remain separate from task-manager state and proof state

## Known Drift
- `task-packets/INDEX.md` contains missing and stale entries
- launcher IDs and filesystem packet IDs disagree in some PRMS cases
- any automation must derive from actual packet files, not index status prose

## v1 Registry Rule
The packet registry adapter should:
- discover files from `task-packets/**/*.md`
- parse packet metadata
- expose packet references to task-manager surfaces
- report index drift separately
