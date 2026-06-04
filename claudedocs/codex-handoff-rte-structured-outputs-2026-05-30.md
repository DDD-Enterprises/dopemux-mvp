# Codex Handoff: RTE Structured-Output Attestation Wiring

**Created:** 2026-05-30  
**Branch target:** cut off `main` (`755bf3846`)  
**Service:** `services/repo-truth-extractor`  
**Audit doc:** `claudedocs/rte-structured-outputs-corrected-plan-2026-05-30.md`

---

## What this is and why

The Repo Truth Extractor (RTE) uses a two-flag system to gate strict structured output:
- `strict_json_schema: bool` — model *claims* it supports `response_format.type=json_schema`
- `strict_passthrough_verified: bool` — we have *empirically confirmed* output is schema-exact

In `lib/structured_output_contracts.py:213`, `strict_capability_reason()` returns `"openrouter_strict_passthrough_unverified"` for any OpenRouter route where `strict_passthrough_verified` is false — so calling `chat.completions.create(response_format=...)` without first flipping this flag is wired to fail closed. The production v4 route map (`promptsets/v4/model_map.yaml`) routes **zero traffic through OpenRouter** today; all strict routes are direct-provider (OpenAI).

A prior plan (Antigravity draft) proposed bypassing this gate. That was rejected. This task implements the **correct** approach:

1. Register missing candidate routes in the benchmark registry
2. Add non-strict `json_object` mode to the prescan path (the one safe prescan improvement)
3. Add telemetry when the repair cascade fires on claimed-strict routes
4. Wire the verification harness for the Phase-D Gemini candidate

**The flag flip** (`strict_passthrough_verified: true` in `model_map.yaml` for `gemini-3.1-pro-preview`) is **NOT** part of this task — that happens only after the live benchmark campaign passes. This task wires everything so that campaign can be run and the flip can be made.

---

## Governance before you start

- Read `services/repo-truth-extractor/lib/structured_output_contracts.py` before touching it — it is **contract-sensitive**. Do not change `provider_schema_variant()`, `strict_capability_reason()`, or the `is_strict_capable_route()` gate.
- `tests/test_strict_passthrough_attestations.py` must remain green after your changes — it is the attestation gate.
- `promptsets/v4/model_map.yaml` is contract-sensitive. **Do not edit it** in this task.
- All changes must be minimal-blast-radius. No refactors, no cosmetic changes.
- Run the full test suite before declaring done: `python -m pytest tests/ -x -q` from `services/repo-truth-extractor/`.

---

## Step 1 — Register two new candidate routes in the benchmark registry

**File:** `services/repo-truth-extractor/benchmarking/registry/registry_loader.py`

This file contains a function that returns a hardcoded list of `RouteRecord` objects used by the benchmarking campaign. The existing entries are `route_local_fixture_v1`, `route_openrouter_openai_gpt_5_4_v1`, and `route_openai_gpt_5_4_v1` (around line 105–160 of the file).

Add **two new entries** to the same `routes = [...]` list:

```python
RouteRecord(
    route_id="route_gemini_direct_gemini_3_1_pro_preview_v1",
    surface_id="surface_gemini_direct_api_v1",
    model_key="gemini/gemini-3.1-pro-preview",
    provider_model_id="gemini-3.1-pro-preview",
    api_key_ref="GEMINI_API_KEY",
    route_pin="gemini-3.1-pro-preview",
    strict_json_schema_declared=True,
    strict_passthrough_verified=False,   # ← NOT flipped — awaits campaign
    route_hash=hash_json({"route_id": "route_gemini_direct_gemini_3_1_pro_preview_v1"}),
    content_hash=hash_json({"route_id": "route_gemini_direct_gemini_3_1_pro_preview_v1"}),
    source_ref="m1_registry_seed",
),
RouteRecord(
    route_id="route_openrouter_gemini_3_1_pro_preview_v1",
    surface_id="surface_openrouter_api_v1",
    model_key="google/gemini-3.1-pro-preview",
    provider_model_id="google/gemini-3.1-pro-preview",
    api_key_ref="OPENROUTER_API_KEY",
    route_pin="google/gemini-3.1-pro-preview",
    strict_json_schema_declared=True,
    strict_passthrough_verified=False,   # ← NOT flipped — awaits campaign
    route_hash=hash_json({"route_id": "route_openrouter_gemini_3_1_pro_preview_v1"}),
    content_hash=hash_json({"route_id": "route_openrouter_gemini_3_1_pro_preview_v1"}),
    source_ref="m1_registry_seed",
),
```

**Validation:** The `RouteRecord` dataclass/namedtuple is defined elsewhere in the file — match its field signature exactly. After adding, confirm the existing registry tests pass.

---

## Step 2 — Add the two Gemini routes to the live-readiness smoke set

**File:** `services/repo-truth-extractor/benchmarking/cli/benchmark_live_route_readiness_smoke.py`

Around line 29 there is:

```python
STRICT_LIVE_ROUTE_IDS = {
    "route_openrouter_openai_gpt_5_4_v1",
    "route_openai_gpt_5_4_v1",
    "route_openrouter_openai_gpt_5_3_codex_v1",
    "route_openai_gpt_5_4_mini_v1",
}
```

Add the two new route IDs to this set:

```python
STRICT_LIVE_ROUTE_IDS = {
    "route_openrouter_openai_gpt_5_4_v1",
    "route_openai_gpt_5_4_v1",
    "route_openrouter_openai_gpt_5_3_codex_v1",
    "route_openai_gpt_5_4_mini_v1",
    "route_gemini_direct_gemini_3_1_pro_preview_v1",        # NEW
    "route_openrouter_gemini_3_1_pro_preview_v1",           # NEW
}
```

No other changes to this file.

---

## Step 3 — Add `json_object` mode to the prescan path

**File:** `services/repo-truth-extractor/lib/prescan/grok_passes.py`

**Function:** `_call_grok()` at line 512.

Background: this function calls `client.chat.completions.create()` at line 537 with no `response_format`, then raw-`json.loads(content)` at line 548. Provider research confirmed:
- xAI accepts `response_format: {"type": "json_object"}` on the Grok models used by this path
- xAI **rejects** `response_format: {"type": "json_schema", "strict": true}` + `additionalProperties: false` (HTTP 400) — that is why `strict_passthrough_verified=False` and we must NOT add strict mode here
- `json_object` mode (non-strict, no schema) is safe and reduces bare `json.loads` failures

**What to add:** Derive `response_format` from the candidate and transport. Add it to the `chat.completions.create()` call only when the provider supports `json_object` mode; skip it for mock and any provider not in the known safe set. Keep the `json.loads(content)` repair as-is — it remains the fallback.

Read the function at line 512–557 carefully before editing. The specific change:

```python
# After line 526 (limiter acquire), before line 528 (import openai):
# Derive response_format for json_object mode.
# - Do NOT use json_schema / strict here: xAI rejects additionalProperties:false (HTTP 400).
# - json_object is safe: instructs model to emit valid JSON without schema enforcement.
# - Skip for mock provider (no real API call).
_PRESCAN_JSON_OBJECT_PROVIDERS = {"openai", "xai", "openrouter"}
_prescan_response_format = (
    {"type": "json_object"}
    if provider in _PRESCAN_JSON_OBJECT_PROVIDERS
    else None
)
```

Then update the `chat.completions.create()` call at line 537 to pass it:

```python
create_kwargs: dict = {
    "model": model_id,
    "messages": [{"role": "user", "content": payload}],
    "temperature": self.config.temperature,
}
if _prescan_response_format is not None:
    create_kwargs["response_format"] = _prescan_response_format
response = client.chat.completions.create(**create_kwargs)
```

Keep everything after line 546 (`content = ...`, `json.loads(content)`, etc.) unchanged.

**Validation:** The existing prescan unit tests must pass. Check for any mock-provider tests that assert the exact kwargs passed to `create()` — update mocks to tolerate the new `response_format` kwarg where the provider is in `_PRESCAN_JSON_OBJECT_PROVIDERS`.

---

## Step 4 — Add repair-cascade telemetry in `llm_runtime.py`

**File:** `services/repo-truth-extractor/llm_runtime.py`

**Function:** `parse_json_from_response_with_provenance()` at line 1247–1339.

Background: this is the 5-stage repair cascade. When stage 1 (`json.loads`) succeeds at line 1264, `repair_applied` stays `False`. When any of stages 2–5 fires, it sets `repair_applied=True` and `repair_type=<stage_name>`.

**What to add:** A new `"claimed_strict_route"` key in the provenance dict, passed in from the call site. The goal is to make it queryable later: "this repair cascade fired on a route that claimed strict output support" — surfacing models whose advertised support degrades in practice.

This is a **two-part change**:

**Part A — add the parameter to `parse_json_from_response_with_provenance`:**

Change the signature at line 1247 from:
```python
def parse_json_from_response_with_provenance(
    deps: LLMRuntimeDeps,
    text: str,
) -> Tuple[Optional[Any], Dict[str, Any]]:
```
to:
```python
def parse_json_from_response_with_provenance(
    deps: LLMRuntimeDeps,
    text: str,
    *,
    claimed_strict_route: bool = False,
) -> Tuple[Optional[Any], Dict[str, Any]]:
```

Add `"claimed_strict_route": claimed_strict_route` to the initial `provenance` dict at line 1251. No other changes to the function body.

**Part B — pass `claimed_strict_route` at call sites:**

Find calls to `parse_json_from_response_with_provenance` in `llm_runtime.py` (use `grep -n "parse_json_from_response_with_provenance"` in the file). For each call site that has access to a route dict (i.e., where `is_strict_capable_route(route, transport)` or `strict_json_schema` is already in scope), pass `claimed_strict_route=bool(route.get("strict_json_schema", False))`. For call sites where no route is in scope, leave the default (`False`).

**IMPORTANT:** `parse_json_from_response` at line 1342 delegates to `parse_json_from_response_with_provenance` — update it to thread the kwarg through:

```python
def parse_json_from_response(
    deps: LLMRuntimeDeps,
    text: str,
    metadata_out: Optional[Dict[str, Any]] = None,
    *,
    claimed_strict_route: bool = False,
) -> Optional[Any]:
    parsed, provenance = parse_json_from_response_with_provenance(
        deps, text, claimed_strict_route=claimed_strict_route
    )
    ...
```

**Validation:** `grep -n "def parse_json_from_response"` to find all signatures and call sites. Existing tests must pass unchanged — the kwarg is optional with a safe default so no callers break.

---

## Step 5 — Run the full test suite and confirm no regressions

From `services/repo-truth-extractor/`:

```bash
python -m pytest tests/ -x -q 2>&1 | tail -20
```

All existing tests must pass. Pay particular attention to:
- `tests/test_strict_passthrough_attestations.py` — the attestation gate (must not change what passes)
- `tests/test_run_extraction_v5_benchmark_route_ownership.py` — the new route IDs must not violate ownership rules
- `tests/test_route_request_options.py` — exercises the `response_format` kwargs path
- Any test that mocks `_call_grok` or `chat.completions.create` in the prescan path

If a test asserts the exact absence of `response_format` in the prescan call kwargs, update the mock to reflect the new `json_object` mode for the `xai`/`openai`/`openrouter` providers, and add a test case that confirms `response_format` is **absent** for `provider="mock"`.

---

## Step 6 — Open a PR

Branch name: `codex/rte-strict-output-attestation-wiring`

PR title: `feat(rte): wire strict-output attestation candidates + prescan json_object + repair telemetry`

PR body must include:
- What was changed (Steps 1–4 summary)
- What was intentionally NOT changed: `model_map.yaml` not modified, no strict flags flipped, `provider_schema_variant()` untouched
- Test output (last 20 lines of pytest)
- The next step: run `benchmarking/cli/benchmark_live_route_readiness_smoke.py` with a real `GEMINI_API_KEY` to get the live attestation result for `route_gemini_direct_gemini_3_1_pro_preview_v1`

---

## What success looks like

- `python -m pytest tests/ -x -q` exits 0 with no new failures
- `benchmarking/registry/registry_loader.py` contains both new Gemini `RouteRecord` entries with `strict_passthrough_verified=False`
- `benchmarking/cli/benchmark_live_route_readiness_smoke.py::STRICT_LIVE_ROUTE_IDS` contains both new route IDs
- `lib/prescan/grok_passes.py::_call_grok()` passes `response_format={"type":"json_object"}` for xai/openai/openrouter, nothing for mock
- `llm_runtime.py::parse_json_from_response_with_provenance()` accepts `claimed_strict_route:bool=False` and includes it in provenance
- `promptsets/v4/model_map.yaml` **unchanged**
- `lib/structured_output_contracts.py` **unchanged**

## What is explicitly out of scope

- Flipping `strict_passthrough_verified: true` on any route — that requires the live benchmark campaign to pass first
- Changing `provider_schema_variant()` — the audit confirmed this would break Gemini/xAI schema shaping
- Adding `strict:true` / `json_schema` format to the prescan path — xAI rejects `additionalProperties:false` (HTTP 400); provider docs confirm grok strict is best-effort only
- Adding Claude/Anthropic routes — not in the map, requires a separate API key decision
- Migrating strict CE/AGG routes to OpenRouter — production routes them direct; no benefit

## Reference files (read before editing)
- Plan + research: `claudedocs/rte-structured-outputs-corrected-plan-2026-05-30.md`
- Gate logic: `services/repo-truth-extractor/lib/structured_output_contracts.py:213–233`
- Schema shaping: `services/repo-truth-extractor/lib/structured_output_contracts.py:507–525`
- Prescan path: `services/repo-truth-extractor/lib/prescan/grok_passes.py:512–557`
- Parse cascade: `services/repo-truth-extractor/llm_runtime.py:1247–1339`
- Registry shape: `services/repo-truth-extractor/benchmarking/registry/registry_loader.py:105–160`
- Smoke harness: `services/repo-truth-extractor/benchmarking/cli/benchmark_live_route_readiness_smoke.py:29–34`
- Attestation gate test: `services/repo-truth-extractor/tests/test_strict_passthrough_attestations.py`
