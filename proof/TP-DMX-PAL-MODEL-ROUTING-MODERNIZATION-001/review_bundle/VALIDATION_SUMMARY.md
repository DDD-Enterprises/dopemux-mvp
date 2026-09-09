# Validation Summary

## PASS

- Issued Task Packet schema validation: exit 0.
- Baseline focused tests: 23 passed.
- Relevant repository tests: 101 passed.
- Vendored PAL non-integration suite: 880 passed, 4 skipped, 16 deselected.
- Ruff targeted changed Python: exit 0.
- Generated PAL manifest drift check: exit 0.
- Compose parse with scoped non-secret interpolation placeholder: exit 0.
- Disposable LiteLLM, PAL HTTP, and PAL stdio image builds: exit 0; no containers started.
- Docs frontmatter and docs validator: exit 0.
- Changed-file pre-commit lane: exit 0.
- Commit hook: repo preflight PASS, 6 smoke tests passed, syntax scan 1001 files.
- `git diff --cached --check`: exit 0 on frozen content.
- Gitleaks staged-diff scan: no leaks.
- Deterministic instruction-like scanner: zero matches.
- Changed-contract preflight: PASS, L2, 232 paths.
- Independent final audit: PASS, exact AGY model, no fallback, no findings.

## FAIL

- Changed-module mypy: exit 1, 48 errors in 7 files while checking 4 changed source files. Errors include missing PyYAML/requests stubs, existing imported-module errors, existing `routing_config` `Any` returns, and existing untyped `routing_cli` functions. Repository baseline is not mypy-clean.

## NOT_RUN

- Real provider calls or provenance probes.
- Live PAL-to-LiteLLM auth cutover or credential passthrough.
- Live `~/.dopemux/routing.yaml` mutation or reload.
- Container start/restart or live application handshake.
- Foreign adops LiteLLM access.
- PR Steward current-head readiness gate before draft PR exists.
