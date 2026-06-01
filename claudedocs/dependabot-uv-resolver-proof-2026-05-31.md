# Dependabot uv Resolver Repair Proof - 2026-05-31

## Scope

- Task Packet: `TP-DMX-DEPENDABOT-UV-RESOLVER-001`
- Worktree: `/Users/hue/code/dopemux-mvp-wt-dependabot-uv-resolver`
- Branch: `codex/dependabot-uv-resolver-20260531`
- Base: `origin/main` at `ffda644b9827d94d1fe2e502e94d38c2ce109030`
- Triggering failure: GitHub Actions run `26727373180`, Dependabot job `78764854616`

## Observed Failure

The post-merge Dependabot uv security-update workflow on `main` failed outside the PR #759 CI gate. The failing run was a GitHub Dependabot security update job for uv dependencies. The log reported an unsatisfiable dependency split involving newer `litellm`, `semgrep`, and `mcp` resolution for Python 3.14 / Windows markers.

Observed failure classification:

- `🚀 Complete CI Pipeline (ADHD-Optimized)`: passed on merge commit `ffda644b9827d94d1fe2e502e94d38c2ce109030`
- `CodeQL`: passed on merge commit `ffda644b9827d94d1fe2e502e94d38c2ce109030`
- Dependabot uv security-update workflow: failed while resolving update files

## Analysis

Root package metadata advertised `requires-python = ">=3.11"` while project classifiers listed Python 3.11, 3.12, and 3.13 only. The existing lockfile therefore carried Python 3.14 resolver splits.

The root `services` extra also allowed `mcp>=1.0.0`. Dependabot's security update set attempted to resolve a patched MCP/LiteLLM/Semgrep combination. Current Semgrep versions compatible with newer LiteLLM resolve through `mcp==1.23.3`, so a lower patched MCP floor can still fail in the grouped security update.

## Repair

- Bounded root Python support metadata to `>=3.11,<3.14`, matching the advertised classifiers.
- Raised the root `services` MCP floor from `mcp>=1.0.0` to `mcp>=1.23.3`.
- Regenerated `uv.lock` so Python 3.14 resolution splits are removed and the lock contains `mcp==1.23.3` with compatible Semgrep transitive resolution.
- Added changelog and Task Packet bookkeeping.

## Validation

| Command | Exit | Result |
| --- | ---: | --- |
| `python -m json.tool task-packets/generated/TP-DMX-DEPENDABOT-UV-RESOLVER-001.json >/dev/null` | 0 | PASS |
| `python -m jsonschema -i task-packets/generated/TP-DMX-DEPENDABOT-UV-RESOLVER-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` | 0 | PASS |
| `uv tool run --from uv==0.11.8 uv lock --check` | 0 | PASS |
| `uv tool run --from uv==0.11.8 uv lock --dry-run -P litellm -P Mako -P PyJWT -P ecdsa -P fastmcp -P mcp -P semgrep` | 0 | PASS |
| `uv tool run --from uv==0.11.8 uv sync --frozen --dry-run --all-extras` | 0 | PASS |
| `git diff --check` | 0 | PASS |
| `pre-commit run --files pyproject.toml uv.lock CHANGELOG.md task-packets/INDEX.md task-packets/generated/TP-DMX-DEPENDABOT-UV-RESOLVER-001.json claudedocs/dependabot-uv-resolver-proof-2026-05-31.md` | 0 | PASS |

## Remaining Unknowns

- The exact GitHub Dependabot service run cannot be proven fixed until this repair is merged to `main` and the Dependabot update workflow reruns.
- The dry-run validates the resolver with uv `0.11.8`, matching the observed Dependabot updater version, but it is not a full Dependabot service execution.
