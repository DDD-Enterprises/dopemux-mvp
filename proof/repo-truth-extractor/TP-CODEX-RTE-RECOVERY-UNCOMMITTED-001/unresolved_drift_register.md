# TP-CODEX-RTE-RECOVERY-UNCOMMITTED-001 Unresolved Drift Register

| Path | Classification | Why Excluded | What Would Be Needed | Blocks TP004? |
| --- | --- | --- | --- | --- |
| `services/repo-truth-extractor/run_extraction_v5.py` | `UNRESOLVED` | Mixed uncommitted TP001, TP002, and TP003 work in one file; file-level ownership is not singular enough for truthful recovery. | Separate the file by packet-owned change sets or create a dedicated hunk-level recovery packet with explicit proof. | yes |
| `config/pricing.yaml` | `UNRESOLVED` | TP001 spend-cap authority file depends on unresolved mixed runner changes. | Recover matching TP001 runner code first or together in a dedicated packet. | yes |
| `services/repo-truth-extractor/tests/test_run_extraction_v5_cost_cap.py` | `UNRESOLVED` | TP001 regression test depends on unresolved runner changes. | Recover TP001 runner code coherently. | yes |
| `services/repo-truth-extractor/tests/test_run_extraction_v5_validator_repair_provenance.py` | `UNRESOLVED` | Test file spans runner-side validator enforcement and repair provenance against unresolved mixed code. | Separate TP002 and TP003 runner work or recover together in a truthful packet. | yes |
| `docs/05-audit-reports/*` deletions | `UNRELATED_DRIFT` | Not part of repo-truth-extractor prelive recovery. | Separate docs cleanup or restore/delete under a docs-scoped packet. | no |
| `.codex-tmp-doc-placement/` | `GENERATED_OR_IGNORED` | Tool scratch output. | None. Leave uncommitted or clean locally. | no |
| `.codex-worktrees/` | `GENERATED_OR_IGNORED` | Tool worktree cache. | None. Leave uncommitted or clean locally. | no |
| `LIVE_LOG*.txt` | `GENERATED_OR_IGNORED` | Runtime log output. | None. Leave uncommitted or clean locally. | no |
| `reports/repo-truth-extractor/pre_live_gate_v25/...` | `GENERATED_OR_IGNORED` | Generated validator artifacts, not recovery code. | None. Keep as local evidence only. | no |
| `llm-plans/*.md` | `UNRELATED_DRIFT` | Planning notes outside packet scope. | Separate planning/docs packet if these should land. | no |

## Summary

- Unresolved files that directly block continued prelive packet recovery: 4
- Unrelated drift left out intentionally: docs deletions and planning notes
- Generated/local-only outputs left out intentionally: logs, reports, scratch directories
