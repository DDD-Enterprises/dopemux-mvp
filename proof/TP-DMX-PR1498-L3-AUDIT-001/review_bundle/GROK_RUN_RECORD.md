# Grok audit run, PR 1498

Head 97b79962936da518888c12f3ff1ae8b6f0084eda, base 4cd889877f929c88ce69958d6ee42b8a643bfab8. One attempt, sealed dir, prompt sha256 31fe6da6... verified before launch.

- CLI grok 1.0.70, started 2026-11-04T13:16:29Z, exit 0 at 13:19:38Z, stderr empty, $0.408945 reported.
- Requested grok-4.5. Observed: init.model grok-4.5, modelUsage key grok-4.5-build, model_self_reported grok-4. Provider attestation UNKNOWN.
- init.tools == [], 0 tool_use blocks, input 281,866 tokens (same-size filler 247,559), so the whole prompt arrived.
- Verdict PASS_WITH_RISKS, validation_status NOT_RUN. Q1-Q18 all PASS. 3 medium, 3 low, all disclosed limitations in the brief; no new defect.
- Weakness: the brief asked for path:line and the reply gives paths and function names only.

Supervisor spot checks at the head, all matched: hmac.compare_digest in both auth_identity.py; ValueError on a bad mode in both; bridge _scrub, empty ProxyHandler, _hide_filled_required, _fill_ids; fill_instance=False; --allow-sequenced is a removal error and --apply needs --output-dir; security -i over stdin; 22 Wave 2A exemptions (31 anchored lookahead lines minus 9 older dope-context and workflow lines).
These are spot checks, not a re-audit.
