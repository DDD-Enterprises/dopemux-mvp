# Self-Check Prompt — 0001

You are OpenCode/Grok self-check.

You are not final auditor.

Review your own diff for obvious mistakes.

**Check**:
1. Any forbidden file touched?
2. Any out-of-scope file touched?
3. Any runtime routing code added?
4. Any arbitrary selector allowed?
5. Any unknown MCP surface marked safe?
6. Any forbidden task marked ready?
7. Any OpenCode authority leak?
8. Any proof-family flattening?
9. auditor_verdict distinct from validation_state?
10. GPT55_REVIEW_BRIEF complete?

**Return**:
- self_check_verdict
- issues_found
- fixes_needed
- confidence
