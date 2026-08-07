# Audit Route Incident — DeepSeek route unavailable

**Packet**: TP-DMX-DCP-WORKFLOW-SEAM-LIFT-001R
**Stage**: Final independent audit of PR #1193 at head `34cc73c3edcde27ea362cf2046995ada9db97999`
**Originally authorized route**: `runner: opencode`, `model: openrouter/deepseek/deepseek-v4-pro`, `agent: ccar-audit-readonly`, `variant: high`
**Outcome**: Route declared `UNAVAILABLE` after two attempts. No content verdict was produced by this route. Superseded by a separately authorized route (see below) — not a silent substitution.

## Attempt 1

- Invocation: `opencode run --dir <audit worktree> --agent ccar-audit-readonly --model openrouter/deepseek/deepseek-v4-pro --variant high -f <files> "<message>"`
- Result: exited 0. Session transcript showed the model emitting one short reasoning note, then a text part containing literal pseudo-tool-call markup (`<read path="...AUDIT_PROMPT.md"></read>`) instead of invoking its real `read` tool, then `finish: "stop"` after ~75 output tokens / 19 reasoning tokens.
- Diagnosis: no real tool use occurred; zero audit content was produced.

## Attempt 2 (retry1)

- Invocation: `opencode run --dir <audit worktree> --agent ccar-audit-readonly --model openrouter/deepseek/deepseek-v4-pro --title "SEAM-LIFT-001R-final-audit-retry1" "Read _AUDIT_CONTEXT/AUDIT_PROMPT.md now using your read tool, then carry out every instruction in it in full... Produce the complete audit report as your final answer in this same turn."`
- Result: exited 0. Produced a 1930-line, well-formed transcript containing pseudo `<Tool>read_file</Tool>` / `<tool_result>` blocks. Every one of those "tool results" was fabricated: the model invented a completely different, nonexistent task packet (`TP-MULTI-FIX-002`, an MCP transport/port-fix packet), a nonexistent companion repository (`_AUDIT_CONTEXT/wat/`, `pseudomux`), and fictional file contents (a docker-compose.yml, a health-check script, MCP catalog/config diffs) — none of which exist anywhere in this repository, this PR, or the actual `_AUDIT_CONTEXT/AUDIT_PROMPT.md` that was really passed to it.
- Independently verified: the real `_AUDIT_CONTEXT/AUDIT_PROMPT.md` in the audit worktree was read directly (not via the model) and confirmed to contain the genuine seam-lift audit instructions (PR #1193, `DCP-RED-MERGE-SEAM-0001`, etc.) — completely different from what the model claimed to have read.
- The transcript never reached its own (fabricated) verdict section; it terminates mid-sentence, consistent with hitting an output/token limit while generating fictional content rather than auditing the real target.
- Diagnosis: the model hallucinated an entire fictional tool-call session rather than grounding its output in the real repository state. This is not partial or degraded audit evidence — it is entirely unrelated to the audited PR and must not be treated as any signal about PR #1193's correctness.

## Resolution

Per the standing decision's explicit no-substitution instruction
(`fallback: {runner: null, model: null, trigger: "stop and report route
unavailable"}`), no alternate model or runner was substituted unilaterally.
The failure was reported to the supervisor as `DEEPSEEK_AUDIT_ROUTE=UNAVAILABLE`
with `PR_CONTENT_AUDIT=NOT_RUN` and `CONTENT_FINDING=NONE` — i.e. this
incident carries no finding about PR #1193 itself, only about the DeepSeek
route's reliability under `opencode run` non-interactive invocation with
this agent/model combination.

The supervisor then explicitly authorized a distinct alternate route (Kimi
K3, `openrouter/moonshotai/kimi-k3`, exact non-aliased selector) invoked
with a tool-free agent (`ccar-audit-notools`) against a deterministic,
hash-manifested, entirely self-contained evidence bundle assembled outside
the repository — specifically to remove the fictional-tool-session escape
hatch that both DeepSeek attempts exploited (whether by malfunction or
model limitation). See `FINAL_AUDIT_REPORT.md`, `FINAL_AUDIT_VERDICT.json`,
and `FINAL_AUDIT_ROUTE_PROVENANCE.json` in this directory for that audit's
result.

## Evidence preservation

The two raw DeepSeek session transcripts and the real `AUDIT_PROMPT.md` they
were given are preserved outside this repository (not committed, per the
FAIL/NEEDS_SUPERVISOR handling instruction for a failed route) at:

- `/tmp/seam-lift-final-audit-34cc73c3ed/_AUDIT_CONTEXT/RAW_OUTPUT.txt` (attempt 1)
- `/tmp/seam-lift-final-audit-34cc73c3ed/_AUDIT_CONTEXT/RAW_OUTPUT_retry1.txt` (attempt 2)
- `/tmp/seam-lift-final-audit-34cc73c3ed/_AUDIT_CONTEXT/AUDIT_PROMPT.md` (the real prompt given to both attempts)

SHA-256 hashes of these files are recorded in `AUDIT_ROUTE_INCIDENT_HASHES.txt`
in this directory, so their content can be verified as unchanged if a
reviewer later needs to inspect them, without committing the 1,930-line
fabricated transcript to the repository itself.
