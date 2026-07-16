# EVIDENCE_LEDGER — UR-AUDIT-001R3

Claim labels: OBSERVED · INFERRED · PROPOSED · UNKNOWN · CONFLICTING · CLAIMED · STALE.
Authority order applied: current runtime/Git (tier 1) > tracked TRUTH_* (tier 2, **empty at HEAD**) >
tracked authority docs (tier 3) > tracked SYSTEM_* (tier 4) > runtime census > UR-INV-003 > UR-INV-004 >
UR-REV-004 > vendor matrix > prior policy > UR-ARCH-001 > inference.

## Kit / archive integrity
| Claim | Label | Evidence |
|---|---|---|
| Architecture archive SHA-256 = `9b78e2bd…d5e090` (expected match) | OBSERVED | `shasum -a 256` cmd 13 |
| Extracted 20 deliverables byte-identical to archive | OBSERVED | extract+shasum cmd 15 (0 mismatches) |
| Kit checksums 106/106 OK | OBSERVED | `shasum -c` cmd 12 |
| 5 nested archives CRC-OK (21/34/11/20/5 members) | OBSERVED | `unzip -t` cmd 14; hashes match KIT_MANIFEST.json |
| Architecture directory = exactly the 20 required deliverables | OBSERVED | `find`+`verify_kit.py` cmd 11,16 |

## Repository state
| Claim | Label | Evidence |
|---|---|---|
| HEAD = census commit `b176747…` (no commit drift) | OBSERVED | `rev-parse HEAD` cmd 6; UR-INV-004 BASELINE_DRIFT_CHECK concurs |
| Branch `main`; remotes → `DDD-Enterprises/dopemux-mvp` (no userinfo) | OBSERVED | cmd 7, 9 |
| Working tree pre-existingly dirty (4 tracked M, 39 untracked), unrelated to router domain | OBSERVED | `status` cmd 8; INV-003 notes `.claude/claude_config.json` pre-existing |
| Git status unchanged before vs after audit | OBSERVED | `diff` cmd 32 (identical) |

## Provenance (bundle-01)
| Claim | Label | Evidence |
|---|---|---|
| 23/32 bundle-01 files byte-identical to a tracked path; 9 no byte-identical match | OBSERVED | git-blob-oid match vs 16,058-blob census tree, cmd 18-19 |
| Root `RULES.md`, `SYSTEM_BOUNDARIES.md`, `TRUTH_SCOPE/SYSTEMS`, `SYSTEM_Dopemux/TaskOrchestrator`, PAL_*, `dopetask-cannonical-spec.json` ABSENT at root @census | OBSERVED | `git cat-file -e` cmd 20 |
| `PROJECT.md`,`ARCHITECTURE.md`,`SERVICE_CATALOG.md` byte-identical tracked-root | OBSERVED | blob match cmd 19; existence cmd 20 |
| Bundle `PM_PLANE.md`,`AGENTS.md` STALE vs tracked root (different blobs) | OBSERVED | `ls-tree` cmd 21 |
| `TRUTH_*`,`SYSTEM_Dopemux`,`SYSTEM_RepoTruthExtractor` match only `docs/research/…` (lower authority) | OBSERVED | blob match cmd 19 |
| Proof/handoff/adapter contracts byte-identical to tracked `docs/governance/…` refs | OBSERVED | blob match cmd 19 |
| Archive names do NOT prove tracked root authority; runtime+tracked-path evidence outranks | OBSERVED/CONFLICTING | this audit; confirms C-001, UR-OQ-001, UR-INV-004 |
| Tier-2 tracked `TRUTH_*` authority effectively empty at HEAD | OBSERVED | only research copies tracked, cmd 19-20 |

## Runtime authority & minimality
| Claim | Label | Evidence |
|---|---|---|
| DCP classifier pure/fail-closed, inert backend, RED_LANE override | OBSERVED | `routing_classifier.py:1-13` cmd 27 |
| Freeflow/LiteLLM/RTE/TaskOrchestrator/dopetask/DCP paths present @census | OBSERVED | `cat-file -e` cmd 23; UR-INV-004 file:line refs |
| `services/task-router` has no tracked source | OBSERVED | `ls-tree` cmd 24 (0 entries) |
| `agent_orchestrator.py` present; `services/agents/**` present (16 files) — dormant | OBSERVED | cmd 23, 25 |
| `universal_router` pkg + config/schemas/tests + `.dopemux/universal-router` absent @census (greenfield) | OBSERVED | `ls-tree` cmd 26 (all 0) |
| Existing CLI noun `routing`; proposed `route` free (no collision) | OBSERVED | `routing_cli.py:588` cmd 29; token grep cmd 28 |
| `config/ai/model-routing.policy.yaml` present, no runtime reader | OBSERVED (present) / CLAIMED (no reader, per C-003, not exhaustively traced) | cmd 23 |
| Router journal path `.dopemux/…` is gitignored | OBSERVED | `check-ignore` cmd 30 (`.gitignore:299`) |

## Evidence-pack facts used
| Claim | Label | Evidence |
|---|---|---|
| UR-REV-004 verdict `ACCEPT_WITH_CARRIED_UNKNOWNS`; corrections URREV-001..005, URQ-006/007 all addressed by architecture | OBSERVED | UR-REV-004_ACCEPTANCE_REVIEW.md |
| UR-INV-003 Codex smoke: probe-ok, 17,298 input / 8,960 cached / 29 output / 0 reasoning tokens; no attested model, no credits | OBSERVED | UR-INV-003 INVESTIGATION_SUMMARY |
| UR-INV-003 Claude bare smoke unavailable (zero usage, no provider) | OBSERVED | same |
| Sandbox network denial ≠ host unhealth; embedded independent audit NOT_RUN | OBSERVED | same; matches this run's own network-denied probe |
| Codex is the only runner with a successful contained smoke among supplied runners | OBSERVED | same (grounds Codex-first advisory adapter) |
| Authority ownership split (per UR-INV-004 AUTHORITY_OWNERSHIP_MATRIX) matches architecture | OBSERVED | AUTHORITY_OWNERSHIP_MATRIX.md |

## Audit self-limitations
| Claim | Label | Evidence |
|---|---|---|
| Network egress OS-blocked this session | OBSERVED | socket PermissionError cmd 2; curl tool-denied cmd 1 |
| Listed secret env vars absent this session | OBSERVED | env probe cmd 3 |
| `advisor` process-review tool present in harness; deliberately NOT invoked (clean-room) | OBSERVED | tool availability; 00_START_HERE.md line 13 prohibition honored |
| Auditor model identity runner-configured, NOT provider-attested | INFERRED | no provider-controlled served-model metadata available to this session |
| Not launched via `launch_claude_code_audit.sh`; full independent containment NOT claimed | OBSERVED | session harness differs from prescribed launcher (advisor present, additional-dir boundary) |
