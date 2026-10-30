# AUDITOR REPORT — PR #1447 L3 embedded audit (TP-DMX-PR1447-L3-AUDIT-001)

- **Auditor**: AGY CLI 1.4.2, `gemini-4-argon-high` (operator-approved fallback; recorded as schema `auditor_model: gemini`), `--sandbox --disable-slash-commands`, no tools, no checkout; prompt built by the repo's trusted builder (`scripts/audit/pal_clink_runner.py --build-prompt`)
- **Implementer**: Claude Code (Anthropic Claude) — different runner and model family
- **Audited head**: `3a61393607a90cd31f8b6fba0f91f0951e42e2f8` · **Base**: `95e95bee88cae5e6c95e6e34f7c28bb423ad9496` (main)
- **Verdict**: **PASS**
- **Containment**: step types observed ['agent_response', 'user_input']; conversation `ab4e5c51-c792-4053-a833-8fa322a9fd54`; raw output sha256 `aad7b7100885b88ec21c84ff888d9221200c751e8caee3f471d062aeb9b5aaea`
- **Instruction-like scan** (trusted scanner): detected=False, matches=0
- **Raw output**: `review_bundle/AUDIT_OUTPUT_RAW.json`; prompt `review_bundle/AUDIT_INPUT.md`; parsed verdict `review_bundle/AUDITOR_VERDICT.json`

## Fallback approval

Operator-approved packet-specific fallback auditor: user selected 'YES AGY' on 2026-10-19 (Claude Code desktop session f10afffd-f9c0-4a2e-86ad-17f8109a3a3a, question: approve AGY gemini-4-argon-high for ONE audit attempt on branch claude/rr-renaissance-integration / PR #1447) after the user instruction 'commit all, unblock'. Fallback because the docs route #1 exact model gemini-3.1-pro-high is absent from `agy models` (agy 1.4.2). Recorded per docs/ops/embedded-audit.md 'Packet-specific supervisor-approved fallback auditors'.

## Auditor return (verbatim JSON)

```json
{
  "status": "PASS",
  "verdict": "PASS",
  "findings": [
    {
      "id": "F-001",
      "severity": "low",
      "category": "validation_consistency",
      "path": "src/dopemux_pr_merge_specialist/dopetask_bundle_loader.py",
      "lines": "94-127",
      "summary": "DopetaskBundleLoader.load validates that identity fields (tp_id/pr_id) and artifact entries are strings via isinstance(..., str), but unlike DopetaskSeriesLoader.parse_dict does not reject empty or whitespace-only strings."
    },
    {
      "id": "F-002",
      "severity": "info",
      "category": "code_hygiene",
      "path": "tests/scripts/test_docs_filename_hygiene.py",
      "lines": "65,100",
      "summary": "Duplicate top-level `import pytest` statements added in test_docs_filename_hygiene.py."
    }
  ],
  "risks": [
    "Candidate test suite and runtime behavior were not executed inside this embedded audit because tools and code execution are disabled by contract (validation_status=NOT_RUN); CI and supervisor validation gates must verify runtime execution.",
    "Removing `scripts` from `norecursedirs` and enabling `--import-mode=importlib` in pytest.ini expands default pytest collection to `tests/scripts/`, which could surface latent collection or ordering assumptions in other script tests not modified in this PR."
  ],
  "rationale": "Audited all 39 changed files in PR #1447 (head 3a61393607a90cd31f8b6fba0f91f0951e42e2f8 against base 95e95bee88cae5e6c95e6e34f7c28bb423ad9496 in DDD-Enterprises/dopemux-mvp). The changes implement fail-closed input validation, path containment, transactional preflight checks, thread lifecycle synchronization, TOML-aware merge guards, and deterministic test clock/mock isolation: (1) `dopetask_archive_resolver.py` uses `candidate.is_file()` instead of `exists()` so directories named `.zip` cannot spoof archives; (2) `dopetask_bundle_loader.py`, `dopetask_compatibility_mode.py`, and `dopetask_series_loader.py` enforce JSON object/field type invariants before assembly, and `dopetask_packet_launcher.py` validates `engine_lane` before creating output directories, with byte parity maintained across `src/`, `templates/`, `.claude/`, and `.github/` copies; (3) `scripts/check_docs_filename_hygiene.py` enforces lexical and `os.path.realpath` repo-root containment on explicit `requested_paths`; (4) `scripts/check_docs_hygiene.py` adds fail-closed preflight detection for identical-destination collisions and NFC+casefold path aliases without unlinking sources; (5) `src/dopemux/agent_orchestrator.py` separates `_lifecycle_lock` from `_lock`, starts LiteLLM monitoring with rollback before launching the worker, uses per-generation `stop_event` instances, joins outside `_lock`, and refuses to start a new generation if a timed-out worker thread is still alive; (6) `src/dopemux/mcp/fleet_catalog.py` preserves CRLF/LF offsets and uses `tomllib.loads` with fail-closed decode fallback to reject hand-authored `mcp_servers` definitions outside managed markers; and (7) `pytest.ini` and test files isolate `questionary` mocking and pin `_steward_gate_now` timestamps.",
  "inspected_paths": [
    ".claude/skills/pr-merge-specialist/scripts/dopemux_pr_merge_specialist/dopetask_archive_resolver.py",
    ".claude/skills/pr-merge-specialist/scripts/dopemux_pr_merge_specialist/dopetask_bundle_loader.py",
    ".claude/skills/pr-merge-specialist/scripts/dopemux_pr_merge_specialist/dopetask_compatibility_mode.py",
    ".claude/skills/pr-merge-specialist/scripts/dopemux_pr_merge_specialist/dopetask_packet_launcher.py",
    ".claude/skills/pr-merge-specialist/scripts/dopemux_pr_merge_specialist/dopetask_series_loader.py",
    ".github/skills/pr-merge-specialist/scripts/dopemux_pr_merge_specialist/dopetask_archive_resolver.py",
    ".github/skills/pr-merge-specialist/scripts/dopemux_pr_merge_specialist/dopetask_bundle_loader.py",
    ".github/skills/pr-merge-specialist/scripts/dopemux_pr_merge_specialist/dopetask_compatibility_mode.py",
    ".github/skills/pr-merge-specialist/scripts/dopemux_pr_merge_specialist/dopetask_packet_launcher.py",
    ".github/skills/pr-merge-specialist/scripts/dopemux_pr_merge_specialist/dopetask_series_loader.py",
    "pytest.ini",
    "scripts/check_docs_filename_hygiene.py",
    "scripts/check_docs_hygiene.py",
    "src/dopemux/agent_orchestrator.py",
    "src/dopemux/mcp/fleet_catalog.py",
    "src/dopemux_pr_merge_specialist/dopetask_archive_resolver.py",
    "src/dopemux_pr_merge_specialist/dopetask_bundle_loader.py",
    "src/dopemux_pr_merge_specialist/dopetask_compatibility_mode.py",
    "src/dopemux_pr_merge_specialist/dopetask_packet_launcher.py",
    "src/dopemux_pr_merge_specialist/dopetask_series_loader.py",
    "templates/skills/pr-merge-specialist/scripts/dopemux_pr_merge_specialist/dopetask_archive_resolver.py",
    "templates/skills/pr-merge-specialist/scripts/dopemux_pr_merge_specialist/dopetask_bundle_loader.py",
    "templates/skills/pr-merge-specialist/scripts/dopemux_pr_merge_specialist/dopetask_compatibility_mode.py",
    "templates/skills/pr-merge-specialist/scripts/dopemux_pr_merge_specialist/dopetask_packet_launcher.py",
    "templates/skills/pr-merge-specialist/scripts/dopemux_pr_merge_specialist/dopetask_series_loader.py",
    "tests/orchestrator/test_adhd_orchestrator.py",
    "tests/orchestrator/test_dynamic_layouts.py",
    "tests/orchestrator/test_status_updates.py",
    "tests/pr_merge_specialist/test_queue_drain_integration.py",
    "tests/pr_merge_specialist/test_template_contracts.py",
    "tests/scripts/test_adhd_ux.py",
    "tests/scripts/test_docs_filename_hygiene.py",
    "tests/scripts/test_docs_hygiene.py",
    "tests/unit/test_agent_manager_lifecycle_guards.py",
    "tests/unit/test_dopetask_archive_resolver_regression.py",
    "tests/unit/test_dopetask_bundle_loader_shapes.py",
    "tests/unit/test_dopetask_compatibility_regression.py",
    "tests/unit/test_dopetask_packet_launcher_validate_first.py",
    "tests/unit/test_dopetask_series_loader.py",
    "tests/unit/test_mcp_fleet_catalog_merge_safety.py",
    "tests/unit/test_pytest_collection_contract.py"
  ],
  "evidence_refs": [
    "src/dopemux_pr_merge_specialist/dopetask_archive_resolver.py:32-35 (replaces candidate.exists() with candidate.is_file() across src, templates, .claude, and .github mirrors)",
    "src/dopemux_pr_merge_specialist/dopetask_bundle_loader.py:85-128 (enforces dict root, string tp_id/pr_id identity, and list-of-strings artifacts)",
    "src/dopemux_pr_merge_specialist/dopetask_compatibility_mode.py:28-43 (enforces dict type checks on bundle and optional nested body)",
    "src/dopemux_pr_merge_specialist/dopetask_packet_launcher.py:109-121 (resolves engine_lane handler and raises ValueError on unknown lane before out_dir.mkdir)",
    "src/dopemux_pr_merge_specialist/dopetask_series_loader.py:42-117 (validates dict root, non-empty series_id/project_id, string status, list of packet dicts, and non-empty string depends_on IDs)",
    "scripts/check_docs_filename_hygiene.py:127-171 (blocks absolute paths, '..' traversal, and symlinks resolving outside realpath(repo_root))",
    "scripts/check_docs_hygiene.py:328-484 (adds NFC+casefold _alias_key/_existing_alias and fail-closed preflight in apply_moves without unlinking on collision)",
    "src/dopemux/agent_orchestrator.py:97-210,273-286 (adds _lifecycle_lock, startup rollback of _litellm_manager, per-generation _stop_event, lock-free join, and alive-worker guard)",
    "src/dopemux/mcp/fleet_catalog.py:325-415 (preserves CRLF/LF offsets in _locate_marked_region and validates non-managed TOML via tomllib.loads in _reject_hand_authored_mcp_servers)",
    "pytest.ini:15-28 (adds --import-mode=importlib and removes scripts from norecursedirs)",
    "tests/pr_merge_specialist/test_queue_drain_integration.py:325-506 (pins _steward_gate_now to deterministic fresh and expired UTC timestamps)"
  ],
  "validation_status": "NOT_RUN"
}
```

## Normalization notes

- `findings` were returned as structured objects; id, severity (upper-cased to the schema enum) and summary are carried verbatim, path/lines/category go into `body`. `status: OPEN` is assigned by the proof author (no risk acceptance is claimed; acceptance is the owner's decision).
- `risks` are carried verbatim into `remaining_risks`, followed by the fallback-model and NOT_RUN-validation risks added by the proof author.
- Test and lint evidence at the audited head: see `PROOF.json` → `validations` (CI run links and local targeted runs).
