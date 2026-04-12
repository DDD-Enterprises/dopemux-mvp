# Packet: dopemux recovery audit and consolidation

**Objective:** Recover all surviving work signals, map them to canonical subsystem boundaries, and produce a verified consolidation plan.
**Risk:** high
**Task class:** unknown subsystem + architecture-sensitive

## Phase 0: Freeze (Complete)
- Created `.recovery/` directory
- Exported worktrees to `.recovery/worktrees.porcelain.txt`
- Exported reflog to `.recovery/reflog.all.txt`
- Exported dangling objects to `.recovery/fsck.txt`
- Exported refs to `.recovery/ref_inventory.txt`
- Exported stashes to `.recovery/stashes.txt`

## Phase 1: Rebuild the Inventory
1. **Recover all surviving refs from branch, stash, reflog, fsck.**
   - Recreate worktrees only for branches with unique surviving value.
2. **Build branch -> packet -> subsystem -> authority inventory.**
   - Create `RECOVERY_INVENTORY.md` using the schema: `status | branch/ref | sha | last_commit | likely_packet | subsystem | authority_slice | worktree_path | dirty | keep? | notes`
3. **Classify by Subsystem & Authority Slice.**
   - Apply labels: `active_candidate`, `merged_candidate`, `orphan_candidate`, `stale_but_unique`, `duplicate_line`, `needs_diff_review`, `unknown_authority`.
   - Separate:
     - operator/control (`src/dopemux/*`)
     - PM (`Leantime`, `task-orchestrator`)
     - memory (`ConPort`, `dope-memory`)
     - retrieval (`dope-context`)
     - bridge (`dopecon-bridge`)
     - docs/truth extraction

## Phase 2: Consolidate
4. **Consolidate duplicate lines only after git cherry and diff review.**
   - Merge into one branch **only if all are true**:
     - same packet/objective
     - same authority slice
     - no conflicting ownership assumptions
     - diff is still coherent after review
5. **Archive stale-but-unique work instead of deleting it.**
   - `git branch archive/<old-name> <sha>`

## Phase 3: Verification & Proof
6. **Produce `proof/recovery-audit.proof.json`.**
   - The file must track the evidence ledger, commit-sized slices, and final verification state.

### `proof/recovery-audit.proof.json` Schema Reference:
```json
{
  "packet": "recovery-audit",
  "objective": "Reconstruct lost temporary worktree state into a verified branch/worktree inventory and consolidation plan.",
  "evidence_ledger": [
    ".recovery/branches.vv.txt",
    ".recovery/worktrees.porcelain.txt",
    ".recovery/reflog.all.txt",
    ".recovery/refs.txt",
    ".recovery/fsck.txt",
    ".recovery/stashes.txt"
  ],
  "slices": [
    {
      "name": "freeze-and-capture",
      "status": "complete",
      "verification": ["git status", "git worktree list --porcelain", "git reflog --all"]
    },
    {
      "name": "recover-orphans",
      "status": "in_progress",
      "verification": ["git show <sha>", "git branch recover/<slug> <sha>"]
    },
    {
      "name": "classify-and-consolidate",
      "status": "pending",
      "verification": ["git cherry -v", "git log base..branch"]
    }
  ],
  "branch_decisions": [],
  "residual_risks": [
    "reflog expiry may have dropped older detached work",
    "untracked files from deleted worktree directories may be permanently gone",
    "authority mapping remains unresolved for some drifted subsystems"
  ],
  "final_confidence": "MEDIUM"
}
```

## Next Immediate Steps upon Execution:
1. Initialize `proof/recovery-audit.proof.json` with the "freeze-and-capture" slice marked `complete`.
2. Parse `.recovery/ref_inventory.txt` and `.recovery/reflog.all.txt` into `RECOVERY_INVENTORY.md` to begin classification.
3. Create missing worktrees in `.recovery/` for active/orphan branches mapping them against the inventory.
