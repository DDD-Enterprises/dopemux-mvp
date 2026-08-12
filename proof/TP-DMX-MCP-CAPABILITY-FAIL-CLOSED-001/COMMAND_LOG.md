# Command Log — TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001

Chronological record of substantive commands. Full raw output for the commands marked
`(see review_bundle/...)` is captured verbatim in that file.

## S0 — Custody & characterization (read-only)

```
git fetch origin main --quiet
git rev-parse origin/main                     # 9dce8ffaec489f486d0356d300f0e8ea5aefa3d2
git branch --show-current                     # feat/pr-prep-specialist-v2-contract (pre-existing session branch, untouched)
git status --porcelain=v1
ls src/dopemux/mcp/ ; ls tests/mcp/
find . -iname resolver.py                     # confirmed exists at src/dopemux/mcp/resolver.py
wc -l src/dopemux/mcp/resolver.py src/dopemux/mcp/gate.py tests/mcp/test_resolver.py tests/mcp/test_discovery_gate_strict.py
# Read resolver.py and gate.py in full -- confirmed F018/F019 present exactly as packet describes.
grep -rn 'provenance|repo_profile|"env_var"' --include='*.py' src/ tests/   # consumer inventory
grep -rln InstanceResolver / DiscoveryGate --include='*.py' src/ tests/
# Only non-allowlist consumer: src/dopemux/mcp/server_manager.py:449 (opaque debug field, no branching)
gh pr list --state open --json number,title,headRefName --limit 100 | filter by keyword
gh pr diff 1166/1161/1128 --name-only | grep resolver/gate    # no overlap found
```

## S1 — Reproduce F018/F019 (pre-fix, execution base)

```
python3 repro_f018.py    # F018 DEFECT CONFIRMED: repo-profile authority silently downgraded to env_var
python3 repro_f019.py    # F019 DEFECT CONFIRMED: mandatory service with zero proven tools reached PASS via handshake suppression
```
(see review_bundle/f018_pre_fix_repro.txt, review_bundle/f019_pre_fix_repro.txt)

## Worktree/branch setup

```
git fetch origin main --quiet
git worktree add -b tp/DMX-MCP-CAPABILITY-FAIL-CLOSED-001 .worktrees/TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001 origin/main
# HEAD is now at 9dce8ffaec fix(dcp): fail closed on incomplete control evidence (#1223)
```

## S2 — Add failing regressions

```
python -m pytest -q tests/mcp/test_resolver.py tests/mcp/test_discovery_gate_strict.py   # baseline: 6 passed
# edited tests/mcp/test_resolver.py: R1/R2/R3 cases + corrected the F018-embodying assertion
# edited tests/mcp/test_discovery_gate_strict.py: G1/G2/G4/G5/G6/R4 cases
python -m pytest -q tests/mcp/test_resolver.py tests/mcp/test_discovery_gate_strict.py
# 6 new assertions failed for the expected F018/F019 reasons; R1/R3/R4/G4 controls already passed
```

## S3 — Implement minimal repair

```
# src/dopemux/mcp/resolver.py: env override only sets provenance=env_var when not already repo_profile
# src/dopemux/mcp/gate.py: removed handshake_required exemption from required-glob validation
python3 repro_f018.py    # F018 NOT PRESENT (already repo_profile)
python3 repro_f019.py    # F019 NOT PRESENT (blocked as expected)
python -m pytest -q tests/mcp/test_resolver.py tests/mcp/test_discovery_gate_strict.py   # 15 passed
```

## S4 — Deterministic validation (first pass)

```
python -m pytest -q tests/mcp                                    # 62 passed
python -m pytest -q tests/test_cli_mcp_startup.py tests/test_mcp_config_generation.py tests/test_mcp_health_probe.py tests/test_mcp_registry.py
  # 1 failed: test_extract_port_default (ambient CONPORT_MCP_PORT=3007 env leak, unrelated to packet files)
git stash; python -m pytest -q tests/test_mcp_health_probe.py::test_extract_port_default; git stash pop
  # identical failure reproduced on unmodified execution base -> BASELINE_FAILURE_PROVEN_NONREGRESSION
git diff --check                                                  # clean
git diff --name-only origin/main...HEAD                           # 4 files, all in allowlist
# wrote task-packets/TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001.{json,md}
python3 -c "...validate_packet_file(...)"                         # PASS against dopetask-canonical-spec.json
git add -A -- <allowlisted files>
pre-commit run --files <allowlisted files>
  # docs-frontmatter-guard mutated task-packets/....md (auto-inserted frontmatter)
git add task-packets/TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001.md
pre-commit run --files <allowlisted files>                        # clean pass, second time
python -m pytest -q tests/mcp/test_resolver.py tests/mcp/test_discovery_gate_strict.py tests/mcp
  # re-run after hook mutation, all green
gitleaks protect --staged --verbose                                # no leaks found
```

## S5 — Freeze substantive head C1 (first version, later amended)

```
git commit -m "fix(mcp): fail closed on downgraded authority and unproven required tools" ...
# repo commit-hook preflight (repo_preflight) ran automatically: OK across all checks
git rev-parse HEAD    # c1fbf8e6ce15535e6bfe1c215c874736da2b8ea3
```

## S6 — Independent audit, pass 1

```
codex:codex-rescue task-resume-candidate --json    # available: false
Agent(subagent_type=codex:codex-rescue, run_in_background=false, ...)   # full audit prompt in transcript
# Verdict: NEEDS_SUPERVISOR (see review_bundle/audit_pass_1_needs_supervisor.md)
```

## Repair per audit finding

```
# src/dopemux/mcp/resolver.py: resolve() now resets self.resolution_report at top of every call
# tests/mcp/test_resolver.py: added test_reused_resolver_does_not_leak_stale_provenance
export TMPDIR=<scratchpad>
python -m pytest -q tests/mcp/test_resolver.py tests/mcp/test_discovery_gate_strict.py   # 16 passed
python -m pytest -q tests/mcp                                                            # 63 passed
python -m pytest -q tests/test_cli_mcp_startup.py ...                                    # same baseline exception only
git diff --check                                                                          # clean
git diff --name-only origin/main...HEAD                                                   # still 6 files, all allowlisted
pre-commit run --files src/dopemux/mcp/resolver.py tests/mcp/test_resolver.py            # clean
gitleaks protect                                                                           # no leaks found
git add src/dopemux/mcp/resolver.py tests/mcp/test_resolver.py
git commit --amend -m "..."
git rev-parse HEAD    # 40783797fe30325766a2cb6f53aaa53254785712  (new C1)
```

## S6 — Independent audit, pass 2 (controlling)

```
Agent(subagent_type=codex:codex-rescue, run_in_background=false, ...)   # re-audit prompt, full context of pass-1 finding + fix
# Verdict: PASS_WITH_RISKS (see review_bundle/audit_pass_2_pass_with_risks.md)
```

## S7 — Proof-only closure

```
mkdir -p proof/TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001/review_bundle
git diff --name-only origin/main...HEAD > proof/.../CHANGED_FILES.txt
python -m pytest -q tests/mcp/test_resolver.py tests/mcp/test_discovery_gate_strict.py > review_bundle/focused_tests_output.txt
python -m pytest -q tests/mcp > review_bundle/relevant_suite_output.txt
python -m pytest -q tests/test_cli_mcp_startup.py ... > review_bundle/adjacent_smoke_output.txt
python3 -c "...validate_packet_file(...)" > review_bundle/packet_schema_validation.txt
gitleaks protect > review_bundle/secret_scan.txt
git diff --check > review_bundle/diff_check.txt
# wrote PROOF.json, VALIDATION.json, AUDITOR_REPORT.md, HANDOFF.md, MANIFEST.json, CHANGED_FILES.txt
```
