# DMX-DCP-MODEL-ROUTING-MVP-0000C — ROUTING_POLICY_ORIGIN_MAIN_LEDGER.md

## `config/ai/model-routing.policy.yaml` on Clean `origin/main`

**Status**: `OBSERVED`

### Evidence

- **Location**: `config/ai/model-routing.policy.yaml` on detached `origin/main` (SHA `55a713be4c49c59f1d4fedeed6a1930477dd54fb`)
- **Presence**: PRESENT
- **Content summary** (first 50 lines captured):
  - Version: 1
  - Status: `proposed_governance_policy`
  - Authority: `advisory_until_runtime_wiring_verified`
  - Explicitly states it is **NOT** a runtime router
  - Explicitly states it does **NOT** override:
    - `templates/routing.yaml` + `dopemux routing` (LiteLLM proxy)
    - `model_map_v2_tp008.yaml` + RTE cost profiles (lane assignment)
  - Defines stage routing (read / investigate / plan / implement / judge / audit)
  - Defines model tiers per stage

### Delta vs 0000B

| Source | Status in 0000B | Status in 0000C | Impact |
|--------|-----------------|-----------------|--------|
| Current DCP branch | MISSING | — | U-01 HIGH blocker |
| Local `main` | PRESENT (advisory) | — | Confirmed |
| `origin/main` | Not verified on clean detached HEAD | **PRESENT** (clean) | **U-01 RESOLVED** |

### Conclusion for 0001

`U-01` is now **RESOLVED** when using clean `origin/main` as the baseline.

The policy file exists on the authoritative clean main branch. Any implementation branch (including future 0001 work) must either:
1. Merge or cherry-pick this file from `origin/main`, or
2. Explicitly document why it is being omitted.

**Recommendation**: 0001 should treat this file as **advisory governance** (not runtime authority) and must preserve the three-separate-concerns warning already present in the file.
