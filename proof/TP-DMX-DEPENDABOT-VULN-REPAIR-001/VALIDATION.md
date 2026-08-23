# VALIDATION — TP-DMX-DEPENDABOT-VULN-REPAIR-001

## Scope
Close open GitHub Dependabot alerts on `DDD-Enterprises/dopemux-mvp` default branch
(observed: 86 = 1 critical + 48 high + 31 medium + 6 low).

## Worktree
- Path: `.worktrees/TP-DMX-DEPENDABOT-VULN-REPAIR-001`
- Branch: `fix/dependabot-vuln-repair-86`
- Base: `origin/main` @ `cfa4927a883b469c06f37343c18e6582f23d1443`

## Patched floors applied

### Python (root `uv.lock` via `pyproject.toml` + `[tool.uv].override-dependencies`)
| Package | Before | After | Notes |
|---|---|---|---|
| aiohttp | 3.14.1 | 3.14.3 | |
| cryptography | 48.0.1 | 50.0.0 | |
| fastmcp | 2.14.0 | 3.4.6 | critical SSRF/path-traversal fix (>=3.2.0) |
| mcp | 1.23.3 | 1.29.0 | pinned `<2` to avoid major jump |
| h2 | 4.3.0 | 4.4.1 | |
| mako | 1.3.10 | 1.4.1 | |
| setuptools | 82.0.1 | 84.0.0 | |
| diskcache | 5.6.3 | **removed** | dropped with fastmcp 3.x graph |

### Secondary Python
- `services/dopemux-gpt-researcher/backend/requirements.txt`: aiohttp 3.14.3
- `services/working-memory-assistant/.../requirements.txt`: cryptography 50.0.0
- PAL `uv.lock`: cryptography 50.0.0, mcp 1.29.0 (`mcp>=1.28.1,<2`)

### Root npm
- next 15.5.21, postcss 8.5.23, overrides for nanoid/js-yaml/@babel/core/sharp/brace-expansion
- `npm audit --package-lock-only --legacy-peer-deps` → **0 vulnerabilities**

### ui-dashboard
- npm + pnpm overrides for nanoid, babel, postcss, brace-expansion, socket.io-parser, undici, ws, yaml, esbuild
- npm audit → **0 vulnerabilities**; pnpm audit → **No known vulnerabilities found**

## Residual (no upstream patch)
| Package | GHSA | Why residual |
|---|---|---|
| ecdsa (via python-jose) | GHSA-wj6h-64fc-37mp | Vulnerable range `>=0`; no patched release. Minerva timing on P-256. |

## Smoke
```
uv run: fastmcp 3.4.6, mcp 1.29.0, aiohttp 3.14.3, cryptography 50.0.0
FastMCP('smoke') has http_app=True; @tool registration works
dope-context FastMCP import path works
```

## Validation buckets
| Check | Result |
|---|---|
| `uv lock --check` | PASS |
| root npm audit (package-lock-only) | PASS (0 vulns) |
| ui-dashboard npm audit | PASS (0 vulns) |
| ui-dashboard pnpm audit | PASS |
| FastMCP smoke import | PASS |
| `git diff --check` | PASS |
| `validate_change_contract.py` (uncommitted) | NOT_RUN against commit head until after commit |
| Full service integration suite | NOT_RUN |
| Formal embedded L2 audit (Claude Code) | NOT_RUN — required before FINALIZATION gate |

## Expected Dependabot impact
- Close all alerts with published patched versions across touched manifests.
- Leave open: ecdsa / GHSA-wj6h-64fc-37mp until python-jose migrates off ecdsa or an ecdsa patch ships.
