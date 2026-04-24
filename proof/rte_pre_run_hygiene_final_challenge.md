# RTE Pre-Run Hygiene Final Challenge

Date: 2026-04-23

## Challenged Recommendation

- repo is ready for a bounded first-pass RTE run if `AGENTS.md` is isolated again immediately before the run or commit
- first-pass input should keep runtime/truth/proof/report/extraction evidence in scope
- hidden local state and transient caches should be excluded from traversal, not cleaned aggressively
- already-applied mutations are limited to tracked-drift stashing and transient cache/editor cleanup
- one cleanup command ran wider than intended, but no tracked source files changed

## Challenge Record

- `challenge` tool invocation executed
- output was a reassessment prompt, not a provider-signed verdict

## Final Challenge Outcome

The recommendation held with one mandatory qualification:

- do not describe the repo as clean without noting that `AGENTS.md` can reappear as unrelated local drift during validation

Secondary qualification:

- the wider-than-intended cache cleanup must stay visible in the final operator report
