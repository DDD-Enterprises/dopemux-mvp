# TP-DMX-FDOS-004-R7-CURRENT-MAIN-EXACT-HEAD-FINALIZATION

## 0. Execution Directive
Execute this packet in **Claude Code using Sonnet** as the primary implementer.
This packet finalizes existing PR **#1152**. It does not create a replacement PR, redesign the 40-file source selection, merge the PR, or upload files into ChatGPT.
The existing 40 uploaded files and prior generated packages are regression evidence only. They are not execution truth and must not be copied back into the repository as source authority.
Runtime repository state, current `origin/main`, the current PR branch, current GitHub review state, and current schemas govern execution.

# 1. Packet Identity
```yaml
packet_id: TP-DMX-FDOS-004-R7-CURRENT-MAIN-EXACT-HEAD-FINALIZATION
parent_packet: TP-DMX-FDOS-004-CHATGPT-PROJECT-SOURCE-REFRESH
supersedes_execution_packet: TP-DMX-FDOS-004-R6-CURRENT-MAIN-REPAIR
repository: DDD-Enterprises/dopemux-mvp
existing_pr: 1152
existing_branch: claude/chatgpt-40-source-refresh-f84dfc
base_branch: main
packet_class: governance-package-finalization
risk_class: HIGH
implementation_agent: Claude Code Sonnet
formal_auditor:
  preferred: AGY with an exact proven Sonnet model
  fallback: Claude Code Opus in a separate session
merge_authorized: false
chatgpt_upload_authorized: false
force_push_authorized: false
history_rewrite_authorized: false
```

# 2. Decision
## `PROPOSED`
Repair and finalize PR #1152 using the existing branch.
The implementation must:
1. synchronize the PR branch with the latest `origin/main`
2. rebuild the package from that exact main SHA
3. recapture the complete live open-PR inventory
4. close remaining package-safety defects
5. produce one substantive candidate commit
6. run a fresh independent formal audit against that commit
7. add one audit-proof-only tip commit
8. run exact-head CI
9. classify and resolve review threads
10. run PR Steward from trusted current-main tools
11. stop before merge and before ChatGPT Project upload
