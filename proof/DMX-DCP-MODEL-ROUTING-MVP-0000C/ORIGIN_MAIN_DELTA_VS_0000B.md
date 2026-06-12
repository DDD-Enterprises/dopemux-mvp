# DMX-DCP-MODEL-ROUTING-MVP-0000C — ORIGIN_MAIN_DELTA_VS_0000B.md

## Key Differences: Clean `origin/main` vs Dirty DCP Branch

### Branch Identity

| Attribute | 0000B (Dirty DCP Branch) | 0000C (Clean origin/main) |
|-----------|---------------------------|---------------------------|
| Branch | `dcp/chatgpt-mcp-ro-0006-dope-context-and-task-orchestrat` | `detached (origin/main)` |
| HEAD SHA | `8be0675579f501582c74e14a409343ac6384edb3` | `55a713be4c49c59f1d4fedeed6a1930477dd54fb` |
| Worktree | Dirty (9 tracked + 24 untracked) | Clean (detached HEAD) |
| Red-lane conflict | `.github/workflows/gemini-review.yml` modified | `.github/workflows/gemini-review.yml` clean |

### Routing Policy (U-01)

| Source | 0000B Status | 0000C Status | Resolution |
|--------|--------------|--------------|------------|
| `config/ai/model-routing.policy.yaml` on current branch | MISSING | — | — |
| `config/ai/model-routing.policy.yaml` on `main` / `origin/main` | PRESENT (advisory) | **PRESENT** (clean) | **U-01 RESOLVED** when using clean baseline |

### Red-Lane Files

| File | 0000B Status | 0000C Status |
|------|--------------|--------------|
| `.github/workflows/gemini-review.yml` | Modified (DCP test failure) | Present and clean |

### Conclusion

The clean `origin/main` evidence bundle proves that:

1. `config/ai/model-routing.policy.yaml` **exists** on the authoritative main branch.
2. The red-lane workflow file is **not modified** on clean main.
3. The dirty state and red-lane conflict in 0000B are artifacts of the DCP development branch, not the canonical baseline.

**Recommendation for 0001**: Use the clean `origin/main` evidence as the primary authority for routing policy and red-lane classification. The dirty DCP branch evidence should be treated as "work-in-progress" rather than canonical truth.
