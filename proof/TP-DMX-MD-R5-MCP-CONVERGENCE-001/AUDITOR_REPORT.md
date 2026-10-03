# AUDITOR REPORT — TP-DMX-MD-R5-MCP-CONVERGENCE-001

- Verdict: **PASS_WITH_RISKS** (0 BLOCKING, 0 HIGH, 2 MEDIUM, 3 LOW, 2 INFO)
- Auditor: `claude-code-cli`, model `claude-sonnet-5-5` (runtime_family `claude-code`)
- Base SHA: `73563404e840c3d603837527efd7475e92cd9cc5`
- Checked head: `9132beaa0f377478f7d29aed14fb267748db2df1` (equals `HEAD` of the audited worktree)
- Implementer per packet: `agy`/Gemini, so the auditor is a different provider family and runtime.
- Subject: committed diff `73563404e..9132beaa0`. `review_bundle/DIFF.patch` is byte-identical to `git diff` of that range.

## 1. Scope containment — PASS

12 files changed (11 modified, 1 added). Every one is on the allowlist; none is outside it.

| File | Allowlisted |
|---|---|
| docker/mcp-servers-source/pal-stdio/Dockerfile | yes |
| docker/mcp-servers-source/pal/Dockerfile | yes |
| docker/mcp-servers-source/pal/pal-mcp-server/requirements.txt | yes |
| docker/mcp-servers-source/services/mcp-client-python/services/mcp-client-python/requirements.txt | yes |
| docker/mcp-servers-source/services/mcp-client/requirements.txt | yes |
| pyproject.toml | yes |
| scripts/preflight.sh | yes |
| services/dope-context/Dockerfile | yes |
| services/dope-context/src/mcp/server.py | yes (`services/dope-context/src/`) |
| services/dope-context/src/preprocessing/document_processor.py | yes (`services/dope-context/src/`) |
| src/dopemux/litellm_proxy.py | yes |
| tests/test_cli_litellm_lazy_import.py | yes (new) |

- Root `uv.lock` is **not** in the committed diff (`git diff --name-status` confirms this).
- The working tree does have an uncommitted `uv.lock` modification (+27 lines, adding pypdf, python-magic and tiktoken). See AUDIT-003.

## 2. Implementation correctness

| Objective | Result | Evidence |
|---|---|---|
| MCP pins `mcp>=1.28.1,<2.0.0` and `mcp>=1.0.0,<2.0.0` | PASS | The three requirements files are changed as specified. Root `pyproject.toml` (lines 112, 352) and PAL `pyproject.toml` already carry `mcp>=1.28.1,<2`. Remaining unguarded entrypoints: AUDIT-001. |
| PAL Dockerfiles assert `mcp < 2.0.0` | PASS | I extracted the `RUN python -c` guard from `pal/Dockerfile`. It parses and ran with exit code 0 under `/bin/sh`. The run used mcp 1.29.0, a copy of the PAL source and all `*_API_KEY` variables unset. It imports `server` and registers the handlers. The `pal-stdio` Dockerfile carries the same guard text. I did not run `docker build`. |
| `preflight.sh` bash 3.2 empty-array guard | PASS | The new form is `${arr[@]+"${arr[@]}"}` under `set -euo pipefail`. On `/bin/bash` 3.2.57: an empty array gives 0 arguments, and `("a b" "c")` gives 2 arguments with the space preserved. The old `"${arr[@]}"` form fails with `unbound variable`. |
| `pyproject.toml` services extra | PASS | `tiktoken>=0.7.0`, `pypdf>=4.0.0` and `python-magic>=0.4.27` are in `[project.optional-dependencies].services`. The dope-context image installs `.[services]` from the root pyproject, so the declaration takes effect in the image. |
| dope-context Dockerfile: libmagic1 and tiktoken pre-warm | PASS | `libmagic1` is in the apt list. `TIKTOKEN_CACHE_DIR` is set, `get_encoding('cl100k_base')` runs at build time, and a non-empty-cache assertion follows. See AUDIT-005. |
| `document_processor.py` pypdf with PyPDF2 fallback, guarded tiktoken | PASS | pypdf is tried first, then PyPDF2, and `PYPDF2_AVAILABLE` is kept. `tiktoken.get_encoding` failure is caught and logged, and `self.encoding` is initialised to `None`. The broad `except Exception` is acceptable here because it logs and degrades. No tests: AUDIT-002. |
| `server.py` read handler narrowed | PASS | `except (OSError, UnicodeDecodeError)` in `get_chunk_complexity`. `read_text(..., errors="ignore")` cannot raise `UnicodeDecodeError`, so in practice only `OSError` is reachable. This is harmless. |
| `litellm_proxy.py` lazy import | PASS | The module-level `import litellm` is removed. A guarded import in `sync_litellm_database()` returns the "litellm package not installed" tuple on `ImportError`. The only use of the name is `litellm.__file__` after that import. No other `src/` module reaches `litellm` through the CLI import path (`litellm_trace_logger.py` still imports it at top level). The CLI-import test also confirms `import dopemux.cli` does not import litellm. |
| `tests/test_cli_litellm_lazy_import.py` | PASS | Three tests: isolated subprocess import with a blocked-litellm hook, a CLI import with litellm and network blocked, and an in-process lazy-import test. I ran the 2 import tests against the base `src/` and both fail there, so they reproduce the defect. The third runs in-process and does not discriminate against base (see AUDIT-004). |

## 3. Validation — independently re-run unless marked

| Check | Result |
|---|---|
| `git diff --check base..head` | PASS |
| `validate_change_contract.py --base <base> --head <head>` | PASS (exit code 0; `status=PASS`, `max_lane=L2`, `model_audit_required=True`; matches the receipt) |
| `uv run --frozen pytest tests/test_cli_litellm_lazy_import.py` | PASS (3 passed) |
| `uv run --frozen --extra services pytest services/dope-context/tests/test_qdrant_sdk_contract.py` | PASS (12 passed, 1 skipped; the skip needs a live Qdrant) |
| `uv run --frozen dopemux --help` and `dopemux --version` | PASS (usage printed; `Dopemux 0.1.0`) |
| Lazy-import tests against base `src/` | 2 of 3 FAIL on base, as expected |
| `bash scripts/preflight.sh` | NOT_RUN by auditor. Relied on the implementer receipt ("6 passed, syntax-ok files=1109"). The bash 3.2 idiom was verified in isolation. |
| `docker build` (any image) | NOT_RUN. The packet forbids build and service activation. Guard logic verified by emulation only. |
| Live Qdrant, live services | NOT_RUN |

All six receipts in `VALIDATION_RECEIPTS.json` are implementer-reported. The three I re-ran agree with them.

The audit's own runs used `--frozen` and did not change `uv.lock`. Its SHA-1 before and after was `01bc8753fba7fdb876a907f260017ef598f17bc9`.

## 4. Findings

- **AUDIT-001 (LOW): unguarded `mcp>=1.0.0` remains at non-allowlisted entrypoints.**
  - `docker/mcp-servers-source/services/mcp-client/services/mcp-client/requirements.txt`, `docker/mcp-servers-source/leantime-bridge/requirements.txt` and `.../mcp-client-python/setup.py` still declare `mcp>=1.0.0`.
  - They are outside the write surface, so leaving them is containment-correct.
  - The leantime-bridge Dockerfile does not reference its requirements file (that file's use is unverified).
  - The nested mcp-client duplicate is the likeliest to be built. Follow-up: pin the remaining entrypoints or confirm they are dead.
- **AUDIT-002 (MEDIUM): no tests for the dope-context behavior changes.**
  - Packet S1 requires "focused tests reproduce old defects or assert repaired behavior".
  - The only new test file covers the CLI lazy import.
  - Nothing exercises the pypdf/PyPDF2 fallback order, the guarded `tiktoken.get_encoding` degrade path, or the narrowed `except` in `get_chunk_complexity`.
  - The Qdrant contract test in the receipts predates this change; it was added at base commit `5048571db`.
- **AUDIT-003 (LOW): the working tree has an uncommitted `uv.lock` change.**
  - It adds pypdf, python-magic and tiktoken, and comes from `uv run` without `--frozen` after the `pyproject.toml` edit (the receipt command `uv run --extra services pytest ...` has no `--frozen`).
  - The candidate commit is clean and the packet says the DEP integrator owns `uv.lock`.
  - It must not be staged or pushed with this packet. Revert it with `git checkout -- uv.lock` after audit closure.
  - The committed `pyproject.toml` and `uv.lock` are inconsistent until the DEP integrator regenerates the lock.
  - The dope-context image build is unaffected, because its Dockerfile copies only `pyproject.toml`.
- **AUDIT-004 (LOW): `test_sync_litellm_database_imports_litellm_lazily` needs litellm installed.**
  - It asserts `"litellm" in sys.modules` after the call.
  - In an environment without litellm (the scenario this change targets), the function takes the new `ImportError` branch and the assertion fails.
  - That branch has no direct test.
  - The test is in-process, so it passes against base too when `dopemux` resolves to the candidate source.
  - It is a weaker regression guard than the two subprocess tests. Fixing this would require editing the test, which was out of audit scope.
- **AUDIT-005 (LOW, OPEN for operator acceptance): the tiktoken pre-warm makes the image build need egress.**
  - The build now needs outbound access to `openaipublic.blob.core.windows.net`.
  - If egress is blocked at build time, the build fails hard, which is the intended fail-closed behavior.
  - The pre-warm is untested because no build was run.
- **AUDIT-006 (INFO): packet S1 items not present in the diff.**
  - "Fix Qdrant SDK import contract": already fixed at base (`5048571db`), so no change was needed.
  - "Guard Docker/vendor context against logs/cache pollution": no `.dockerignore` was touched, and `.dockerignore` is not on the allowlist.
  - The dope-context image build context is the repo root, so the root `.dockerignore` governs; the service-level one is not applied.
  - The root file excludes `.git`, `__pycache__`, caches, `.venv`, `node_modules` and `*.log`, but has no `logs/` or `data/` directory pattern.
  - Neither `services/dope-context/logs` nor `data` exists in this worktree, so no pollution was observed. Whether S1 required a change is for the supervisor to decide.
- **AUDIT-007 (INFO, OPEN): the requested return shape conflicts with the repo schema.**
  - The task asks for `verdict`, `runner`, `model`, `runtime_family`, `checked_head`, `base_sha`.
  - `schemas/proof/embedded_audit.schema.json` has `additionalProperties:false`, requires different keys, and lists no `claude-sonnet-5-5` in the `auditor_model` enum.
  - `AUDIT_RETURN.json` conforms to the schema, using `auditor_tool` `claude-code-cli` and `auditor_model` `sonnet`. The literal model id is stated in `invocation`.
  - The extra identity fields are in the sidecar `AUDIT_RETURN.identity.json`.
  - `AUDIT_RETURN.json` validates against the schema with `jsonschema` Draft 7.

## 5. Remaining uncertainty

- No image build, no live service and no `preflight.sh` run by the auditor.
- The candidate commit message omits any attribution trailer. I treated that as out of scope.

## 6. Custody and status

- The three audit files are untracked in the worktree. I did not commit them, because a commit would move `HEAD` off the audited head and the auditor holds authority NONE. The canonical writer is named in the packet.
- AUDIT-005 and AUDIT-007 are `OPEN`; the operator or supervisor decides whether to accept them.

## Verdict

**PASS_WITH_RISKS.** The change is scope-contained and correct against every listed objective. No BLOCKING or HIGH issue was found. The open risks are the missing dope-context tests (AUDIT-002), the unguarded `mcp` entrypoints outside the write surface (AUDIT-001) and the uncommitted `uv.lock` side effect that must not be committed (AUDIT-003).
