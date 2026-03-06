# v4 Prompt Rewrite Harness (Opus diff-only microbatch)

This harness rewrites v4 prompt files by asking Opus for a unified diff patch that:
- replaces only the Extraction Procedure section body
- appends 1-2 domain-specific bullets in Failure Modes
- changes nothing else

Workflow (one file per batch by default):
1) Generate request_N.txt:
   python tools/prompt_rewrite_v4/run_batch.py --render

2) Run Opus 4.6 in Claude Code with:
   - tools/prompt_rewrite_v4/OPUS_SYSTEM_PROMPT.txt (system / instructions)
   - request_N.txt (contains heuristics + prompt file)

3) Save Opus output as:
   tools/prompt_rewrite_v4/out/response_N.patch

4) Apply + validate + advance cursor:
   python tools/prompt_rewrite_v4/run_batch.py --apply

Pending-only workflow (recommended when usage is limited):
1) Show pending prompts and reasons:
   python tools/prompt_rewrite_v4/run_batch.py --pending-report
2) Render next pending prompt only:
   python tools/prompt_rewrite_v4/run_batch.py --render --pending-only
3) Save patch to:
   tools/prompt_rewrite_v4/out/response_pending_<n>.patch
4) Apply + validate next pending prompt:
   python tools/prompt_rewrite_v4/run_batch.py --apply --pending-only

Hard gate (lint-only):
- python scripts/repo_truth_extractor_promptset_audit_v4.py --strict

Notes:
- Fail-closed: if patch is not a unified diff, too large, or touches outside allowed sections, it stops.
- Resume-safe: state.json tracks cursor and done/failed lists.

Benchmark helpers (single-prompt loop):
1) Prepare isolated benchmark input:
   python tools/prompt_rewrite_v4/benchmark_setup.py
2) Save Opus patch at:
   tools/prompt_rewrite_v4/benchmark/response_opus.patch
3) Validate + apply benchmark patch:
   python tools/prompt_rewrite_v4/benchmark_apply.py
