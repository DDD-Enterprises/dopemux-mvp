# Handoff — TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001

## Disposition

```
PASS_WITH_NONBLOCKING_RISKS_READY_FOR_PROOF_CLOSURE
```

## Where things are

- **Worktree**: `.worktrees/TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001` (local, not pushed)
- **Branch**: `tp/DMX-MCP-CAPABILITY-FAIL-CLOSED-001`
- **Base**: `origin/main` @ `9dce8ffaec489f486d0356d300f0e8ea5aefa3d2`
- **Frozen substantive head C1**: `40783797fe30325766a2cb6f53aaa53254785712`
- **Proof bundle**: `proof/TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001/` (this commit, on top of the same branch, touching only the proof path)

## What was repaired

- **DMX-W1-04-F018**: env URL overrides no longer erase repo-profile authority classification.
- **DMX-W1-04-F019**: a "transport active, handshake required" warning no longer suppresses
  required-tool-glob validation for mandatory services.
- **Reuse-safety fix found during audit**: `InstanceResolver.resolve()` now resets its per-call
  state, closing a latent authority-broadening path a reused resolver instance could otherwise hit.

## Validation summary

| Gate | Result |
|---|---|
| Focused tests (`test_resolver.py` + `test_discovery_gate_strict.py`) | PASS (16/16) |
| `tests/mcp` relevant suite | PASS (63/63) |
| Adjacent MCP smoke | PASS with 1 proven-unrelated baseline failure (ambient env leak, independent of packet files) |
| `git diff --check` | PASS |
| Changed-file allowlist | PASS (6 files, all within §4) |
| Task Packet schema | PASS |
| Pre-commit (changed-file lane) | PASS |
| Secret scan (gitleaks) | PASS — no leaks |
| Repo commit-hook preflight | PASS |
| Independent L3 audit (Codex, cross-family) | PASS_WITH_RISKS — sole risk is the auditor's own sandbox tempdir limitation, non-blocking, corroborated by real local test execution |

## Explicitly NOT done by this packet

- No push to any remote.
- No PR opened.
- No mark-ready, merge, or GitHub mutation of any kind.
- No signing.
- No production or service mutation.

## Requested next step

Publication (push + draft PR) requires a **separate explicit operator authorization** per packet
section 8 (S8) and section 12. Before that authorization is acted on: refresh `origin/main`,
re-check scoped drift/open-PR overlap (both were clean at the time of this proof bundle but may have
moved), then push the exact proof-closed head and open a draft PR per the packet's §23 metadata
template. Do not mark ready or merge without further separate authority.
