TOOL_ACCESS=FULL
CUSTODY=MATCH head=66a628dd54e5f007f2684ca6855ea08a53e10546 base=58b00013067933ba7989eea5bb8929f275512a94
VERDICT=PASS_WITH_RISKS

# Embedded audit: TP-DMX-MD-R6-ROUTING-PAL-AGENTS-001 (re-audit after repair)

I found no blocking findings. All five verification dimensions pass. Five non-blocking risks are listed under Risks.

## Custody
- `git rev-parse HEAD` returns `66a628dd…`, `origin/main` returns `58b00013…`, and `git merge-base HEAD origin/main` returns the same base. The head is one commit directly on the base.
- The worktree is not clean (`uv.lock`, `.claude/.dopemux-advisor-cache.json`, an untracked `proof/…/review_bundle`). None of it is in the audited commit, so the audit covers committed content only.

## 1. Bounded allowlist: PASS
- I checked all 43 changed paths against `commit.allowlist` in `task-packets/TP-DMX-MD-R6-ROUTING-PAL-AGENTS-001.json`, treating entries ending in `/` as prefixes. There were 0 violations.
- No changes under `.claude/agents/`, `cli_clients/` or `.github/`.
- `validate_change_contract.py --base origin/main --head HEAD --format text` returns `status=PASS`, `max_lane=L2`, `model_audit_required=True`, `paths=43`.

## 2. Routing catalog and PAL manifest generation: PASS
- `python3 scripts/generate_pal_model_manifest.py --check` returns rc=0, so the three committed manifests are byte-identical to the generator output.
  - `custom_models.json` (compatibility, 60 models)
  - `custom_models.direct-ci.json` (59 models)
  - `custom_models.gateway.json` (2 models: `fable-5-ci`, `kimi-k3-ci`)
- Output is deterministic: `sort_keys=True`, models sorted by name, a trailing newline, and inputs limited to `templates/routing.yaml` and the tracked `config/cheaperinference_models.snapshot.json`.
- `templates/routing.yaml` defines the following.
  - Kimi K3 and Fable 5 routes: `kimi-k3-ci` and `fable-5-ci` are enabled on `cheaperinference`, which is also `enabled: true`.
  - Disabled L3 candidates: the OpenRouter, Moonshot and Anthropic routes and providers are `enabled: false`.
  - PAL compatibility models: a top-level `pal_compatibility_models` block (`llama3.2`).
  - Both Kimi K3 and Fable 5 appear in the direct-ci manifest with the expected capabilities (1M context, always-on or adaptive thinking).
- `src/dopemux/model_catalog.py` is a pure projection with a bounded field allowlist (`PAL_CAPABILITY_FIELDS`) and rejects unknown projections.
- `routing_config.py` gains `audit_catalog_contract` and `sync_catalog_contract`. The sync backs up with `shutil.copy2` and writes with `os.replace` for an atomic write. It is dry-run by default.
- `routing_cli.py` adds `audit-catalog` (exit 1 on stale, exit 2 on error) and `sync-catalog [--apply]`, matching the template's header comments.

## 3. Economical agent guidance: PASS
- `.codex/agents/*.toml` pin economical models per role:

  | Role | Model | Effort |
  |---|---|---|
  | `dmx_explorer` | `gpt-6-luna` | medium |
  | `dmx_housekeeper` | `gpt-6-luna` | low |
  | `project-manager` | `gpt-6-luna` | low |
  | `researcher` | `gpt-6-luna` | medium |
  | `dmx_worker` | `gpt-6.1-sol` | medium |
  | `developer` | `gpt-6.1-sol` | medium |
  | `dmx_reviewer` | `gpt-6.1-sol` | high |
  | `architect` | `gpt-6.1-sol` | high |

- `.codex/config.toml` sets a `gpt-6-luna`/medium subagent default.
- The cost-first text is consistent across `AGENTS.md` §5, `GEMINI.md`, `.claude/claude.md`, `governance-principles.md`, `CHANGELOG.md`, and `config/ai/model-routing.policy.yaml`. It covers the cheapest adequate qualified model, the lowest sufficient effort, no hidden fallback, and a supervisor-owned bounded escalation. It also says Codex is never the formal embedded auditor, and the route YAML is declared advisory.
- Availability and actual model identity are explicitly left `UNKNOWN` rather than asserted.
- `.claude/claude.md` carries a purely additive 2-line change, so existing sections are not clobbered (B4).

## 4. MCP runtime contract: PASS
- `compose.yml` changes are minimal and as specified:
  - The `litellm` build now uses the tracked `docker/mcp-servers-source/litellm/Dockerfile`, which exists.
  - The `pal` and `pal-stdio` services set `CUSTOM_MODELS_CONFIG_PATH=/app/conf/custom_models.direct-ci.json`.
  - PAL's `providers/registries/custom.py` reads that variable.
- B2: the dope-context mount `${HOST_CODE_PARENT_DIR…}:/workspaces:ro` is untouched in the diff and still read-only.
- B3: the `mcp<2` build-time guard is intact in the PAL Dockerfile (line 38), and `pyproject.toml` pins `mcp>=1.28.1,<2`. The only Dockerfile change is a `/opt/venv` symlink for Codex's `docker exec`.
- B4: `config.py` temperature constants are unchanged (0.2 / 0.5 / 0.7), and the diff is limited to comments and a version bump. The `cli_clients` JSON files exist under `conf/cli_clients/`.
- `ensure-pal.sh` runs `docker build` from the canonical PAL source only when the image is absent. It leaves a running container alone and does not rebuild on every run. `ROOT_DIR` is defined.

## 5. Deterministic verification: PASS
| Check | Result |
|---|---|
| `uv run pytest tests/test_model_catalog.py tests/test_model_routing_policy.py tests/test_pal_model_manifest.py tests/test_routing_config.py tests/test_mcp_pal_runtime_contract.py -q` | PASS (46 passed) |
| `uv run pytest tests/commandcode_router/test_normalized_catalog.py -q` | PASS (26 passed) |
| `git diff --check origin/main..HEAD` | PASS (clean) |
| `validate_change_contract.py` | PASS |
| `generate_pal_model_manifest.py --check` | PASS |
| `.claude/agents/*.md` vs `origin/main` | PASS (identical, so CCAR-002 pins are intact, B1) |

## Risks (non-blocking)
1. **Unverified model IDs.** `gpt-6-luna`, `gpt-6.1-sol`, `claude-sonnet-5-5`, `claude-opus-5-5` and `gemini-3.8-flash` cannot be checked offline. The docs mark availability as `UNKNOWN` or `NOT_RUN`, but `.codex/config.toml` and the role TOMLs hard-pin them. An unavailable selector would fail at dispatch, not at validation.
2. **Cost direction of two pins.** `dmx_worker` moved from `gpt-5.4-mini` to `gpt-6.1-sol`, and `dmx_reviewer` from `gpt-5.5` to `gpt-6.1-sol`. The worker change makes that role less economical, and the supervisor default also rises from `gpt-5.5` to `gpt-6.1-sol`. This matches the packet's stated tiers, but there is no relative price evidence in the repo.
3. **Role-name inconsistency.** The TOML `name` values for the pre-existing roles use underscores (`dmx_explorer`), while the new roles and the `role_models` keys in `model-routing.policy.yaml` use hyphens. The tests pass, so this is cosmetic, but a name-based lookup could mismatch.
4. **Unrelated PAL upstream sync.** `config.py` and `pyproject.toml` move from 9.0.x to 9.8.2, and the `openai`, `gemini` and `openrouter` conf JSONs are updated (for example `gemini-3-pro-preview` and `gpt-5.2`). These are allowlisted and pinned by a test, but they are not generator-derived. Only the three `custom_models*.json` files are verified by `--check`.
5. **No stale-image rebuild in `ensure-pal.sh`.** It builds only when the image is missing, so a source change will not refresh an existing `pal-mcp-server:latest`. That fits "no unnecessary rebuild", but it does not give the source-fingerprint rebuild that packet step S1 mentions.

Authority: I did not modify the repository. The audit is deterministic evidence plus direct diff inspection, and it does not mint finality or merge authority.

```json
{
  "tool_access": "FULL",
  "custody": {
    "match": true,
    "head": "66a628dd54e5f007f2684ca6855ea08a53e10546",
    "base": "58b00013067933ba7989eea5bb8929f275512a94"
  },
  "verdict": "PASS_WITH_RISKS",
  "blocking_findings": [],
  "risks": [
    "Model IDs (gpt-6-luna, gpt-6.1-sol, claude-sonnet-5-5, claude-opus-5-5, gemini-3.8-flash) are unverifiable offline and hard-pinned in .codex config/role TOMLs; availability and actual identity remain UNKNOWN/NOT_RUN",
    "dmx_worker moved from gpt-5.4-mini to gpt-6.1-sol, dmx_reviewer from gpt-5.5 to gpt-6.1-sol, and the supervisor default from gpt-5.5 to gpt-6.1-sol; no relative price evidence in repo, so the worker change cuts against the economical goal",
    "Role-name inconsistency: existing role TOML names use underscores (dmx_explorer) while new roles and the policy YAML role_models keys use hyphens; cosmetic, but a name-based lookup could mismatch",
    "PAL upstream version bump 9.0.x to 9.8.2 and openai/gemini/openrouter conf JSON refreshes are allowlisted and test-pinned but not generator-derived; only the three custom_models*.json are covered by the --check",
    "ensure-pal.sh builds only when the image is absent, so source changes do not refresh an existing pal-mcp-server:latest; this fits 'no unnecessary rebuild' but gives no source-fingerprint rebuild"
  ]
}
```
