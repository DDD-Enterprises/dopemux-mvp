# VALIDATIONS at the frozen head 30b0fdec996fcd782bf2f816900f9ff4dabd4c01 (feat/mcp-just-works-m1), recorded 2026-11-07T04:58:51Z

| check | command | result | bucket |
|---|---|---|---|
| unit suite | `make test-fast` (uv run --frozen --extra test pytest tests/unit --maxfail=1 --disable-warnings --no-cov) | 4229 passed, 2 skipped, 2 warnings in 496.08s (0:08:16) ; exit 0 (implementer-run at this SHA, controller-verified from the log) | PASS |
| hooks workflow | `.venv/bin/python -m pytest tests/test_native_hooks_workflow.py -v` | 12 passed at 7ae26f045 (file unchanged in eb3f0624b) | PASS |
| docs validators | `scripts/docs_validator.py` + `scripts/docs_frontmatter_guard.py` on docs/02-how-to/mcp-setup-other-repos.md and both claudedocs files | rc=0 (implementer-run; verifier re-ran the how-to validator rc=0) | PASS |
| ruff F/E9 vs base 583720375 | per-file/per-code diff over the 49 changed .py files | 0 new entries | PASS |
| flake8 F/E7/E9/W6 vs base | same method, flake8 7.5.0 | 0 new entries | PASS |
| black / isort | the five NEW modules (conport_tenant, launcher, locks, reap, stdio_proxy) with the repo config | clean | PASS |
| mypy | the five NEW modules (--explicit-package-bases --ignore-missing-imports; the repo-wide run aborts on main) | 0 errors in those files | PASS |
| make lint / make type-check (repo-wide) | not clean/functional on main (21828 flake8 findings; mypy aborts on a duplicate-module mapping) | not a gate; per-file diffs above | NOT_RUN |
| live: launcher cold path (worktree) | dopemux mcp launch conport / dope-memory + claude mcp list, DOPEMUX_BIN=worktree venv, at 7f5cb621a | both Connected; sibling-lease collision healed | PASS (earlier head) |
| live: fresh project init + launch + gate | throwaway repo, at 8f12edee4 / baf8b1151 | tenant provisioned, images built, conport connected, gate cleared, container on the tenant DB | PASS (earlier head) |
| live: reap --dry-run | at 859fd844d | empty plan with the kill-switch | PASS (earlier head) |
| live: reap --apply, switch-project, Codex/EnterWorktree, legacy-envrc adoption, T1–T11 acceptance | — | owner-run | NOT_RUN |
| known flaky test | tests/unit/test_mcp_port_allocator.py::test_sequential_single_service_allocations_never_share_a_port fails ~1/30 isolated runs (tmp-path hash dependent; allocator logic untouched by the last rounds) | residual risk | UNKNOWN |
