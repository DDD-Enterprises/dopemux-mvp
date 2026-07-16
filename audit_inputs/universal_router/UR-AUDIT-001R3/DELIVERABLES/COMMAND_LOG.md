# COMMAND_LOG — UR-AUDIT-001R3 (read-only)

All commands were read-only against the kit and the live repository. `set -o pipefail` semantics applied where
relevant. Remote URLs contain no userinfo; no redaction was required beyond confirming that. Timestamps are UTC.
Only credential-free, non-mutating commands were run; `curl`/`wget`/`ssh` etc. are permission-denied in this
session (a network-denial control), and no such command was executed against a live host.

## Session-control probes
| # | Command (abridged) | Result / exit |
|---|---|---|
| 1 | `curl -sS --max-time 6 https://example.com` | **permission-denied at tool layer** (curl in deny list) — network-egress control evidence |
| 2 | `python3` socket `create_connection(142.250.72.14:443 / 93.184.216.34:443)` | `NETWORK_BLOCKED: PermissionError [Errno 1] Operation not permitted` (both) — OS-enforced egress denial |
| 3 | `python3` env probe for 13 secret var names | all `ABSENT` (ANTHROPIC/OPENAI/GEMINI/GOOGLE/GITHUB/GH/AWS×3/LITELLM/DOPEMUX×2/CONPORT/LEANTIME) |
| 4 | `pwd`; `echo $TMPDIR` | cwd = kit root; TMPDIR = `/tmp/claude-501` |

## Repository baseline (live repo `/Users/hue/code/dopemux-mvp`)
| # | Command | Output / exit |
|---|---|---|
| 5 | `git -C REPO rev-parse --show-toplevel` | `/Users/hue/code/dopemux-mvp` · exit 0 |
| 6 | `git -C REPO rev-parse HEAD` | `b176747b339685e781de04268c46b7ae123abfbf` · exit 0 |
| 7 | `git -C REPO branch --show-current` | `main` · exit 0 |
| 8 | `git -C REPO -c core.fsmonitor=false status --porcelain=v1` | 43 lines (4 tracked M, 39 untracked) → saved `repo_status_before.txt` |
| 9 | `git -C REPO remote -v` (redaction-checked) | `origin`,`mvp` → `https://github.com/DDD-Enterprises/dopemux-mvp.git` (no userinfo) |
| 10 | `git -C REPO log -1` | author "Dj Dom", 2026-07-10, subject "fix(mcp): restore runtime stack … (#1037)" |

Note: a benign `fsmonitor_ipc__send_query` warning appears on first `git status`; re-run with
`-c core.fsmonitor=false` produces a clean, stable baseline. It does not affect correctness.

## Kit integrity
| # | Command | Output / exit |
|---|---|---|
| 11 | `python3 04_RUNTIME/verify_kit.py` | `KIT VERIFICATION PASSED` · exit 0 → `verify_kit_output.txt` |
| 12 | `shasum -a 256 -c 05_MANIFEST/SHA256SUMS.txt` | 106/106 `OK`, 0 FAILED · exit 0 → `independent_shasum_check.txt` |
| 13 | `shasum -a 256 02_ARCHITECTURE/ORIGINAL/UR-ARCH-001_DELIVERABLES.zip` | `9b78e2bd…d5e090` == expected → `ARCH_HASH_MATCH=TRUE` |
| 14 | `unzip -t` architecture archive + 4 evidence archives | all "No errors detected"; members 21/34/11/20/5 |
| 15 | extract archive to scratch; `shasum` each vs kit-extracted deliverable | 0 mismatches (kit files byte-identical to archive) |

## Architecture & open-questions integrity
| # | Command | Output |
|---|---|---|
| 16 | `find 02_ARCHITECTURE/UR-ARCH-001 -type f`; `wc -c` | 20 deliverables, 250,176 bytes total |
| 17 | `python -m json.tool 20_OPEN_QUESTIONS.json` (via reader) | valid JSON; total 20; ids unique 20; all `blocks_architecture_audit=false` |

## Bundle-01 provenance resolution (Git objects)
| # | Command | Output |
|---|---|---|
| 18 | `git -C REPO ls-tree -r b176747` | 16,058 tracked blobs → blob-id→path index |
| 19 | python git-blob-oid of 32 bundle-01 files, matched to census index | 23 byte-identical tracked; 9 no match → `13_PROVENANCE_RESOLUTION.md` |
| 20 | `git -C REPO cat-file -e b176747:<path>` for 15 root paths + 3 variants | RULES/SYSTEM_BOUNDARIES/TRUTH_*/SYSTEM_Dopemux/PAL_*/dopetask-cannonical ABSENT; PROJECT/ARCHITECTURE/PM_PLANE/SERVICE_CATALOG/AGENTS PRESENT; docs variants PRESENT |
| 21 | `git -C REPO ls-tree b176747 -- PM_PLANE.md AGENTS.md …` | root PM_PLANE blob 7725d672 ≠ bundle 3fd5fa11; root AGENTS b7bbdac1 ≠ bundle 020793c3 |
| 22 | diff bundle vs tracked variant (RULES/system-boundaries/dopetask-spec) | 29 / 6 / 6 changed lines → near-equivalent, not byte-identical |

## Runtime authority & minimality
| # | Command | Output |
|---|---|---|
| 23 | `git cat-file -e b176747:<runtime path>` ×11 | DCP classifier, backend policy, freeflow, routing_config, routing_cli, RTE v5+config, TO agents, scripts/dopetask, model-routing.policy.yaml, model_map_v2 — all PRESENT |
| 24 | `git ls-tree -r b176747 -- services/task-router` | **0 entries** (no tracked source) |
| 25 | `git ls-tree -r b176747 -- services/agents` | 16 entries (dormant family present) |
| 26 | `git ls-tree -r b176747 -- src/dopemux/universal_router / config/universal-router / schemas/universal-router / tests/universal_router / .dopemux/universal-router` | **0 / 0 / 0 / 0 / 0** (greenfield) |
| 27 | Read `src/dopemux/dcp/routing_classifier.py:1-55` | pure fail-closed classifier; no I/O; RED_LANE override; inert backend fields |
| 28 | Grep repo for `universal_router|dopemux route|route recommend|route explain` | 6 mentions across 4 planning docs only (no runtime) |
| 29 | Grep `src/dopemux` for command registration | `routing_cli.py:588 add_command(routing,"routing")`; no `route` group registered |
| 30 | `git check-ignore -v .dopemux/universal-router/router.sqlite3` | `.gitignore:299 '.dopemux/'` → journal path **ignored** |

## End-of-audit verification
| # | Command | Output |
|---|---|---|
| 31 | `git -C REPO -c core.fsmonitor=false status --porcelain=v1` (after) → `repo_status_after.txt` | 43 lines |
| 32 | `diff repo_status_before.txt repo_status_after.txt` | **identical** → `GIT_STATUS_UNCHANGED=TRUE` |
| 33 | `git rev-parse HEAD` (after) | `b176747…` (unchanged) |

**Repository was not modified by this audit.** All writes occurred only under
`OUTPUTS/UR-ARCH-001-OPUS-AUDIT-R3-20260713T011748Z/` (outside the repository).
