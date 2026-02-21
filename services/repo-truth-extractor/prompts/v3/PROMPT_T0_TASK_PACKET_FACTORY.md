Goal: Produce an implementation-ready top-10 TP backlog from R/X norm artifacts.

Role:
- Arbitration planner only. Do not implement code.
- Truth authority is R norm artifacts.

Inputs:
- R norm artifacts (R0-R8 outputs) from extraction/runs/<run_id>/R_arbitration/norm/
- X feature/risk catalogs from extraction/runs/<run_id>/X_feature_index/norm/
- Repo governance constraints from AGENTS.md and .claude/PROJECT_INSTRUCTIONS.md

Outputs:
- TP_BACKLOG_TOPN.json
- TP_INDEX.json

Required schema keys for TP_BACKLOG_TOPN.json:
- run_id
- generated_at
- packets (array)
- packets[].tp_id
- packets[].title
- packets[].priority
- packets[].problem_statement
- packets[].authority_inputs (array of repo paths to R artifacts)
- packets[].invariants (array)
- packets[].scope_in
- packets[].scope_out
- packets[].acceptance_criteria (array)
- packets[].rollback
- packets[].stop_conditions (array)
- packets[].implementer_target

Hard rules:
- implementer_target must equal "Codex Desktop (GPT-5.3-Codex)" for every packet.
- authority_inputs must reference only R/X norm artifacts by path.
- No packet may require repo re-scan or truth reinterpretation.
- No packet may omit deterministic verification commands.

Stop conditions:
- Any TP missing scope, invariants, commands, acceptance criteria, rollback, or stop conditions.
- Any TP proposes a refactor without evidence-driven necessity.
