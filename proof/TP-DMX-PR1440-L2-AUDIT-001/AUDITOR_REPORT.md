# AUDITOR REPORT — PR #1440 L2 embedded audit (TP-DMX-PR1440-L2-AUDIT-001)

- **Auditor**: AGY CLI 1.4.2, `gemini-4-argon-high` (operator-approved fallback; recorded as schema `auditor_model: gemini`), `--sandbox --disable-slash-commands`, no tools, no checkout; prompt built by the repo's trusted builder (`scripts/audit/pal_clink_runner.py --build-prompt`)
- **Implementer**: Claude Code (Anthropic Claude) — different runner and model family
- **Audited head**: `6b14dbfd488b8fd4cccafbd07960b941b473dd07` · **Base**: `95e95bee88cae5e6c95e6e34f7c28bb423ad9496` (main)
- **Verdict**: **PASS_WITH_RISKS**
- **Containment**: step types observed ['agent_response', 'user_input']; conversation `93de3c66-99d0-45af-8e9b-8b10d950f135`; raw output sha256 `467abd011656cb426615fa4c0860b77d502d674c5fbb3adffbd786e0ab1a9fdf`
- **Instruction-like scan** (trusted scanner): detected=False, matches=0
- **Raw output**: `review_bundle/AUDIT_OUTPUT_RAW.json`; prompt `review_bundle/AUDIT_INPUT.md`; parsed verdict `review_bundle/AUDITOR_VERDICT.json`

## Fallback approval

Operator-approved packet-specific fallback auditor: user reply 'YES AGY' on 2026-10-19 (Claude Code CLI session 76436141-ff29-41f5-9965-9b025f7f3adf) approving AGY with model gemini-4-argon-high because the docs route #1 exact model gemini-3.1-pro-high is absent from `agy models` (agy 1.4.2). Recorded per docs/ops/embedded-audit.md 'Packet-specific supervisor-approved fallback auditors'.

## Auditor return (verbatim JSON)

```json
{
  "status": "OK",
  "verdict": "PASS_WITH_RISKS",
  "findings": [
    "In src/dopemux/commands/mcp_commands.py:1785-1800, mcp_doctor_cmd invokes plan_repair(..., dry_run=True) only in the human-readable output branch and passes repair_status into format_human_summary, leaving report.recommended_next_actions unfiltered when --json output is requested.",
    "In src/dopemux/commands/mcp_commands.py:1785-1797, plan_repair is called unconditionally on every non-JSON doctor invocation even when report.recommended_next_actions does not contain a 'repair-config --apply' recommendation.",
    "In src/dopemux/mcp/doctor.py:1365-1428, format_human_summary suppresses 'repair-config --apply' recommendations when repair_status is in {'NOOP', 'BLOCKED'} and falls back to an explanatory dry-run message only when all recommended actions were filtered out.",
    "Documentation updates in .claude/claude.md, AGENTS.md, and docs/02-how-to/mcp-setup-other-repos.md consistently document DOPEMUX_MVP_ROOT/DOPEMUX_PRODUCT_ROOT requirements for external installs, Postgres restoration via dopemux mcp up --services postgres, serena as a single container bound to dopemux-mvp (reducing per-worktree container cost from 3N to 2N), and the implemented vs. partial/planned mcp CLI verbs.",
    "Candidate changes include agent instruction files (.claude/claude.md and AGENTS.md); although instruction_like_scan_summary reported detected=false, all directive-like prose in the diff was treated strictly as untrusted candidate data."
  ],
  "risks": [
    "Behavioral divergence between CLI output modes: 'dopemux mcp doctor --json' serializes report.recommended_next_actions before format_human_summary filtering, so JSON consumers can still receive 'repair-config --apply' recommendations when repair-config dry-run status is NOOP or BLOCKED.",
    "The CLI integration path in src/dopemux/commands/mcp_commands.py:1785-1800 (calling plan_repair and swallowing exceptions via broad 'except Exception') is only indirectly covered; tests/unit/test_mcp_doctor_repo_aware.py:867-892 unit-tests format_human_summary directly rather than invoking mcp_doctor_cmd.",
    "Test suite and runtime validation were not executed in this embedded audit environment (validation_status=NOT_RUN) because tools and candidate code execution are disabled by audit policy."
  ],
  "rationale": "Audited PR #1440 (head 6b14dbfd488b8fd4cccafbd07960b941b473dd07 against base 95e95bee88cae5e6c95e6e34f7c28bb423ad9496) across all 6 changed files. In src/dopemux/mcp/doctor.py, format_human_summary adds an optional repair_status parameter (defaulting to None for backward compatibility) that filters out 'repair-config --apply' entries from report.recommended_next_actions when repair_status is 'NOOP' or 'BLOCKED', substituting a clear diagnostic message if no other actions remain. In src/dopemux/commands/mcp_commands.py, mcp_doctor_cmd computes repair_status via dopemux.mcp.config_repair.plan_repair(..., dry_run=True) inside a defensive try/except block so advisory repair checks cannot crash doctor output. Unit test coverage in tests/unit/test_mcp_doctor_repo_aware.py verifies default, NOOP, BLOCKED, and fallback-only action lists. Documentation updates across .claude/claude.md, AGENTS.md, and docs/02-how-to/mcp-setup-other-repos.md are internally consistent. Verdict is PASS_WITH_RISKS due to minor non-blocking divergence between --json and human output modes, lack of direct unit test coverage on the mcp_doctor_cmd wrapper, and unexecuted runtime tests in the sealed audit environment.",
  "inspected_paths": [
    ".claude/claude.md",
    "AGENTS.md",
    "docs/02-how-to/mcp-setup-other-repos.md",
    "src/dopemux/commands/mcp_commands.py",
    "src/dopemux/mcp/doctor.py",
    "tests/unit/test_mcp_doctor_repo_aware.py"
  ],
  "evidence_refs": [
    ".claude/claude.md:261-262",
    ".claude/claude.md:271-277",
    "AGENTS.md:295-299",
    "AGENTS.md:375",
    "AGENTS.md:385-393",
    "docs/02-how-to/mcp-setup-other-repos.md:48-63",
    "docs/02-how-to/mcp-setup-other-repos.md:164-177",
    "src/dopemux/commands/mcp_commands.py:1782-1800",
    "src/dopemux/mcp/doctor.py:1365-1377",
    "src/dopemux/mcp/doctor.py:1417-1428",
    "tests/unit/test_mcp_doctor_repo_aware.py:867-892"
  ],
  "validation_status": "NOT_RUN",
  "instruction_like_acknowledged": true
}
```

## Normalization notes

- `findings` were returned as prose strings; each is carried verbatim into `embedded_audit.findings[].body` with an id, a severity (LOW for the two actionable observations, INFO for descriptive notes) and status assigned by the proof author, not the auditor.
- `risks` are carried verbatim into `remaining_risks`, followed by the fallback-model and NOT_RUN-validation risks added by the proof author.
- Test and lint evidence at the audited head: see `PROOF.json` → `validations` (CI run links and local targeted runs).
