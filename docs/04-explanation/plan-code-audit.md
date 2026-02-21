---
id: PLAN_CODE_AUDIT
title: Plan_Code_Audit
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
author: '@hu3mann'
date: '2026-02-05'
prelude: Plan_Code_Audit (explanation) for dopemux documentation and developer workflows.
---
# Dopemux Comprehensive Code Audit Remediation Plan

## Guiding Principles
- Minimize risk: eliminate broad `except Exception` blocks; replace with specific exceptions + logging + re-raise when appropriate.
- Security hardening: remove / guard dynamic execution (exec/eval), validate inputs, sanitize file/network paths, enforce least privilege in subprocess calls.
- Reliability: add structured retries with caps for external services (Redis, Postgres, HTTPX, Qdrant, LiteLLM) using tenacity-style backoff.
- Observability: structured logging (JSON or key-value), correlation IDs (instance_id, session_id), consistent error taxonomy.
- Performance: cache hot paths (navigation, symbol lookup, complexity analysis) with adaptive TTL; reduce redundant filesystem and YAML reads.
- Testing: increase coverage for exception paths, fallback logic, and multi-instance environment variables.
- Configuration: strong validation layer for env vars (ports, API keys, DB URLs) with early fail-fast.
- Maintainability: central utility modules for subprocess, IO, config parsing; remove duplicated code across services.

## Risk Categories & Remediation Tactics

| Category | Issues Found | Remediation Pattern |
|----------|--------------|---------------------|
| Broad Exception | Thousands across repo | Replace with specific exceptions; add `# EXC_REVIEW` tag when ambiguity remains |
| Dynamic Exec/Eval | Cleaned (only in deps) | Monitor with CI grep guard |
| Shell=True | None first‑party | Add lint rule to block future usage |
| Unvalidated Config | Ports, keys, DB URLs | Introduce `config/validation.py` + pydantic models |
| Inconsistent Logging | Mixed styles | Introduce `shared/logging.py` with helper for structured log records |
| Fallback Logic Silent | `pass` blocks | Replace with explicit log + metric increment |
| Unbounded Retries | Some tenacity usage, others manual | Standardize retry wrapper with circuit breaker on repeated failures |
| Mixed Path Handling | Potential path traversal in read tools | Use `.resolve()` + `relative_to()` checks, raise ValueError |
| Caching Staleness | Missing eviction reasoning | Add metadata: cached_at, ttl, origin, freshness classification |
| Security of Secrets | API keys in env only | Add optional secrets scanner + mask in logs |

## Week-by-Week Execution Plan
### Week 1 (Stabilize Exceptions & Hotspots)
- Inventory remaining broad `except Exception` in top 15 hotspot files (already partially done).
- Replace 60% of remaining broad excepts with specific exception sets (IOError/OSError, httpx.HTTPError, asyncpg.PostgresError, redis exceptions, yaml.YAMLError, ValueError, KeyError).
- Introduce `shared/exceptions.py` mapping common external library errors to internal categories.
- Tag ambiguous blocks with `# EXC_REVIEW` comment for later triage.
- Add CI grep rule failing on new `except Exception` (allow list for tagged items).

### Week 2 (Configuration & Logging Framework)
- Implement `config/validation.py` using pydantic to parse environment variables for each service (ports, DB URLs, Redis, Qdrant, LiteLLM).
- Refactor services to call a unified `load_validated_config()` early; fail fast if critical values invalid.
- Add `shared/logging.py` with `get_logger(service_name)` returning structured logger including instance_id, workspace_id.
- Replace ad hoc `logging.basicConfig` usages with centralized logging initialization.
- Add correlation IDs: propagate `X-DOPEMUX-TRACE` header / env var through service calls.

### Week 3 (Observability & Metrics)
- Add Prometheus counters/gauges for: exception occurrences by type, cache hits/misses, fallback activations, external retry attempts.
- Instrument navigation cache and LiteLLM proxy startup paths.
- Build `metrics/exception_monitor.py` to parse logs and emit aggregated metrics.
- Dashboard: basic Grafana panel definitions committed under `monitoring/grafana/`.

### Week 4 (Caching & Performance)
- Navigation & symbol cache: implement adaptive TTL (short TTL for volatile files, longer for stable ones); add size-based TTL scaling.
- Complexity analysis: memoize per file hash + symbol to avoid repeated tree-sitter calls.
- Introduce async bulk prefetch for frequently accessed files on session start.
- Benchmark before/after (simple scripts measuring response latency for definition / references).

### Week 5 (Retry & Resilience Layer)
- Create `shared/retry.py` thin wrapper around tenacity with standardized policies (max_attempts, jitter, timeout classification).
- Replace ad hoc try/except + sleep loops with standardized retry decorator.
- Circuit breaker: optional in-memory state to short-circuit failing external endpoints after threshold.
- Document resilience patterns in `docs/RESILIENCE_GUIDE.md`.

### Week 6 (Security Hardening)
- Add path sanitization helper `_safe_resolve(workspace, candidate)` used across file read tools.
- Validate external URLs (allowlist domains if applicable for proxies).
- Add Bandit to CI; baseline scan & suppress only vetted false positives.
- Secrets masking filter for logger (regex patterns for API keys, bearer tokens).

### Week 7 (Test Coverage Expansion)
- Write tests for: config validation failure, each retry wrapper branch, cache expiration logic, fallback symbol search, profile application failure.
- Add fixtures for multi-instance worktree simulation.
- Achieve >85% coverage in critical modules (cli.py, mcp_server.py, navigation_cache.py, complexity analyzer).

### Week 8 (Refactor & Consolidation)
- Consolidate duplicated logic for master key handling, port selection, and environment persistence into `shared/runtime_env.py`.
- Split oversized `cli.py` into subcommands modules under `src/dopemux/commands/`.
- Introduce type hints in remaining dynamic sections; run mypy (incremental strictness).
- Remove deprecated or unused feature toggles; update README.

### Week 9 (Performance & Load Testing)
- Locust scripts covering navigation, definition, references, complexity endpoints.
- Optimize serialization: switch heavy JSON dumps to orjson where beneficial.
- Async connection pooling review (httpx, asyncpg) for proper reuse.
- Identify top 5 latency outliers and address.

### Week 10 (Polish & Final Audit)
- Resolve all `# EXC_REVIEW` tags; either specify exception types or justify keeping broad catch (with doc comment).
- Final security scan (Bandit + dependency scan) and remediate.
- Generate `AUDIT_COMPLETION_REPORT.md` summarizing metrics pre vs post (broad except count, average latency, error rate, coverage).
- Tag release `v0.x.audit-complete`.

## Continuous Integration Enhancements
- Add scripts: `scripts/scan_broad_excepts.sh` failing if count increases beyond baseline threshold.
- Bandit & flake8 run; mypy incremental.
- Simple custom linter: disallow `pass` in exception blocks unless followed by comment `# intentional`.

## File / Module Refactor Targets
- src/dopemux/cli.py -> split into: `commands/start.py`, `commands/init.py`, `commands/litellm.py`, `commands/profile.py`.
- services/serena/v2/mcp_server.py -> extract: `lsp_client.py`, `database_setup.py`, `tools/definition.py`, `tools/references.py`, `tools/complexity.py`, `tools/navigation.py`.
- navigation_cache: move config + key generation to `cache_utils.py`.

## Metrics to Track (Baseline vs Target)

| Metric | Baseline (approx) | Target |
|--------|-------------------|--------|
| Broad except count | ~3800 | <400 ( <10% remain, all justified ) |
| Avg definition latency | TBD | -25% |
| Cache hit ratio (nav) | TBD | >60% |
| Test coverage critical modules | <50% | >85% |
| Unhandled exception logs / day | High | Near zero (only expected categories) |
| Security findings (Bandit high severity) | >0 | 0 |

## EXC_REVIEW Tagging Guidelines
Add `# EXC_REVIEW:<reason>` when retaining broad catch temporarily. Acceptable reasons:
- Legacy logic requiring deep refactor
- Third-party library raises undocumented exceptions
- Aggregating heterogeneous exceptions to transform into unified error response

## Prioritized Task List (Roll-up)
1. Replace remaining broad excepts in cli.py, mcp_server.py.
1. Implement config validation (Week 2 deliverable).
1. Introduce structured logging & metrics instrumentation.
1. Refactor monolithic modules for maintainability.
1. Expand tests & enforce CI guards.
1. Final polish and reporting.

## Immediate Next Actions (Next 48h)
- Finish exception refactor for cli.py lines 415, 573, 792, 862, 944, 1083.
- Begin mcp_server remaining 20+ broad except classifications.
- Draft config validation schema (ports, DB URLs, master keys).

## Notes
- Avoid large-bang refactors; proceed file-by-file to keep diffs reviewable.
- Every exception replacement should preserve original intent; no silent swallowing.
- Document any behavior change in CHANGELOG.

---
End of Plan
