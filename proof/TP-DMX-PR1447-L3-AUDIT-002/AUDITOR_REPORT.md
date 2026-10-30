# AUDITOR REPORT — PR #1447 L3 embedded audit (TP-DMX-PR1447-L3-AUDIT-002)

- **Auditor**: AGY CLI 1.4.2, `gemini-4-argon-high` (operator-approved fallback; recorded as schema `auditor_model: gemini`), `--sandbox --disable-slash-commands`, no tools, no checkout; prompt built by the repo's trusted builder (`scripts/audit/pal_clink_runner.py --build-prompt`)
- **Implementer**: Claude Code (Anthropic Claude) — different runner and model family
- **Audited head**: `3db51791c710d21cccefaab9f4ac7b6a21bcd0e9` · **Base**: `95e95bee88cae5e6c95e6e34f7c28bb423ad9496` (main)
- **Verdict**: **PASS**
- **Containment**: step types observed ['agent_response', 'user_input']; conversation `961766b8-a96c-4804-9f77-e51cba656574`; raw output sha256 `2f406112dd0a0617f4d9f6bf84a1a45d4cab5bb5ebe414df7263d2a3f9514e1c`
- **Instruction-like scan** (trusted scanner): detected=False, matches=0
- **Raw output**: `review_bundle/AUDIT_OUTPUT_RAW.json`; prompt `review_bundle/AUDIT_INPUT.md`; parsed verdict `review_bundle/AUDITOR_VERDICT.json`

## Fallback approval

Operator-approved packet-specific fallback auditor for a RE-AUDIT: user selected 'YES AGY' on 2026-10-20 (Claude Code desktop session f10afffd-f9c0-4a2e-86ad-17f8109a3a3a, question: re-run the AGY fallback audit (gemini-4-argon-high, ONE attempt) on PR #1447's new head after the Codex-review fix and F-001/F-002). The first approved attempt (2026-10-19, head 3a6139360, verdict PASS, packet TP-DMX-PR1447-L3-AUDIT-001) was invalidated by that semantic change. The audit diff excludes proof/** so no prior audit artifact reached the auditor. Fallback because the docs route #1 exact model gemini-3.1-pro-high is absent from `agy models` (agy 1.4.2). Recorded per docs/ops/embedded-audit.md 'Packet-specific supervisor-approved fallback auditors'.

## Auditor return (verbatim JSON)

```json
{
  "status": "PASS",
  "verdict": "PASS",
  "findings": [
    {
      "id": "AUDIT-1447-INFO-1",
      "severity": "info",
      "path": "src/dopemux_pr_merge_specialist/dopetask_bundle_loader.py",
      "summary": "_is_valid_identity allows any non-boolean int for pr_id without requiring a positive integer (value > 0), though in practice PR numbers supplied by context are positive integers."
    },
    {
      "id": "AUDIT-1447-INFO-2",
      "severity": "info",
      "path": "scripts/check_docs_hygiene.py",
      "summary": "apply_moves preflight checks _existing_alias against the pre-move filesystem state even if an aliased path is vacated earlier in the same batch; this is an intentional fail-closed design documented in comments to avoid cross-platform filesystem ambiguity."
    }
  ],
  "risks": [
    "Validation tests were not executed inside the sealed embedded-audit session (validation_status=NOT_RUN); merge readiness relies on CI and steward verification of the test suite.",
    "Enabling default collection of tests/scripts via pytest.ini (--import-mode=importlib and removing scripts from norecursedirs) increases the default pytest collection surface if other script tests assume standalone execution."
  ],
  "rationale": "Audited all 40 changed files in PR #1447 (head SHA 3db51791c710d21cccefaab9f4ac7b6a21bcd0e9 against base SHA 95e95bee88cae5e6c95e6e34f7c28bb423ad9496 in DDD-Enterprises/dopemux-mvp). (1) Dopetask PR merge specialist hardening is byte-identical across src/dopemux_pr_merge_specialist, templates/skills/pr-merge-specialist, .claude/skills/pr-merge-specialist, and .github/skills/pr-merge-specialist, and parity is enforced in tests/pr_merge_specialist/test_template_contracts.py: dopetask_archive_resolver.py now checks candidate.is_file() instead of candidate.exists(); dopetask_bundle_loader.py enforces dict top-level shape, non-blank string/int identity fields, and non-blank string artifact lists; dopetask_compatibility_mode.py rejects non-dict bundles and non-dict nested body values with TypeError; dopetask_packet_launcher.py validates engine_lane before creating out_dir; dopetask_series_loader.py validates top-level dict shape, non-empty series_id/project_id strings, string status fields, list packets, and non-empty string depends_on entries. (2) Docs hygiene scripts fail closed: scripts/check_docs_filename_hygiene.py confines explicit requested_paths to repo_root lexically and after symlink resolution (os.path.realpath + relative_to); scripts/check_docs_hygiene.py adds transactional preflight checks for byte-identical collisions and NFC+casefold path aliases before any file is moved and removes source unlinking on dedupe. (3) src/dopemux/agent_orchestrator.py introduces _lifecycle_lock and per-generation _stop_event to serialize start()/stop(), start LiteLLM monitoring with rollback before worker launch, release the data lock before bounded worker join, and fail closed with AgentError if a prior worker thread outlived stop(). (4) src/dopemux/mcp/fleet_catalog.py preserves CRLF line endings via character-offset slicing (_locate_marked_region) and replaces substring probing with a tomllib.loads check (_reject_hand_authored_mcp_servers) that fails closed on unparseable TOML mentioning mcp_servers. (5) Test isolation and determinism fixes in pytest.ini, tests/orchestrator/*, tests/scripts/test_adhd_ux.py, and pinned steward gate clocks in tests/pr_merge_specialist/test_queue_drain_integration.py are sound and accompanied by targeted unit regressions.",
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
    "src/dopemux_pr_merge_specialist/dopetask_archive_resolver.py:L32-L35 (candidate.is_file() replaces candidate.exists())",
    "src/dopemux_pr_merge_specialist/dopetask_bundle_loader.py:L86-L145 (dict shape guard, _is_valid_identity, and artifacts list element validation)",
    "src/dopemux_pr_merge_specialist/dopetask_compatibility_mode.py:L28-L43 (dict type checks for bundle and bundle['body'])",
    "src/dopemux_pr_merge_specialist/dopetask_packet_launcher.py:L109-L120 (validate engine_lane before out_dir.mkdir)",
    "src/dopemux_pr_merge_specialist/dopetask_series_loader.py:L42-L116 (parse_dict top-level, series field, and packet field validation)",
    "scripts/check_docs_filename_hygiene.py:L126-L172 (iter_docs lexical and realpath containment checks for requested_paths)",
    "scripts/check_docs_hygiene.py:L328-L483 (_alias_key, _existing_alias, transactional preflight in apply_moves, and removal of src.unlink on dedupe)",
    "src/dopemux/agent_orchestrator.py:L97-L210 (_lifecycle_lock, _stop_event, transactional start rollback, and unlocked worker join in stop)",
    "src/dopemux/mcp/fleet_catalog.py:L325-L415 (_locate_marked_region, _line_terminator, _reject_hand_authored_mcp_servers via tomllib.loads)",
    "tests/pr_merge_specialist/test_queue_drain_integration.py:L325-L506 (pinned _steward_gate_now clock for fresh and expired steward artifact tests)",
    "tests/pr_merge_specialist/test_template_contracts.py:L42-L69 (runtime, template, .claude, and .github parity assertions for dopetask modules)"
  ],
  "validation_status": "NOT_RUN"
}
```

## Normalization notes

- `findings` were returned as structured objects; id, severity (upper-cased to the schema enum) and summary are carried verbatim, path/lines/category go into `body`. `status: OPEN` is assigned by the proof author (no risk acceptance is claimed; acceptance is the owner's decision).
- `risks` are carried verbatim into `remaining_risks`, followed by the fallback-model and NOT_RUN-validation risks added by the proof author.
- Test and lint evidence at the audited head: see `PROOF.json` → `validations` (CI run links and local targeted runs).
