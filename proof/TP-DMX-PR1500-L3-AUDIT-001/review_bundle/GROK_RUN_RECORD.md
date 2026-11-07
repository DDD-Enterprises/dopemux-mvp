# Grok audit run, PR 1500

Head 9fbd5fe27da6b21b58c59df34a34c14671ab5007, base 583720375df69fbe50f7b8a6b199eaf026f46fb5. One attempt, sealed dir holding only the prompt, prompt sha256 91d3a072e4a8f8a8a96aba8f2815bd035d4f19a48fd9d89f2d3f6aa3e5e14126 checked before launch.

- CLI grok 1.0.70, exit 0 at 2026-11-05T06:24:02Z, stderr empty, $0.06045948 reported.
- Requested grok-4.5. Observed: init.model grok-4.5, modelUsage key grok-4.5-build, model_self_reported grok-4.7. Provider attestation UNKNOWN. On PR 1498 the same route self-reported grok-4, so the self-report is not evidence of identity.
- init.tools == [], 0 tool_use blocks. Input 62,985 tokens. The delivery token at the very end of the prompt was echoed, so the whole prompt arrived.
- Verdict PASS_WITH_RISKS, validation_status NOT_RUN. Q1-Q12 all PASS. 3 medium, 3 low. Triage: FINDING_TRIAGE.md.
- Weakness: evidence names paths and functions, mostly without the path:line the brief asked for.
