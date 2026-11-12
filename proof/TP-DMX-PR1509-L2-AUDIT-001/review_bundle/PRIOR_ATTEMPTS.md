# Earlier audit attempts at a2ca0ee4b (superseded)

The code was frozen at `a2ca0ee4bf2ee1b673a479f38cdbb4f3fe52f6d6` and both routes ran on the same prompt (sha256 `fd3b7b42697d7035d8c1bbdda6b6a9e9e1f8413b311e2081275f1afe1f6bc7f2`).

| Route | Result | Record |
|---|---|---|
| AGY 1.5.6, `gemini-4-argon-high` (planned governing auditor) | no verdict: `error: Individual quota reached. Please upgrade your subscription to increase your limits. Resets in 37h43m16s.`; status ERROR, 0 tokens | `R1_AGY_OUTPUT_RAW.txt`, `R1_AGY_STDERR.txt`; log and conversation store in custody |
| Grok `grok-4.7` (planned corroboration) | PASS_WITH_RISKS; findings: LOW OVERTIME_COLOR is declared between import declarations, ahead of the taskSequencerTransitions import. | `R1_GROK_VERDICT.json`; raw stream in custody |

With AGY out of quota, the operator chose "Fix, Grok governs" (2026-11-12T13:18:49Z): fix the round-1 Grok finding and run a fresh
Grok audit as the governing auditor. `eb5b6a1dd` moves `OVERTIME_COLOR` below the imports and adds a test for Retry over a
cleared forecast (Grok's round-1 medium risk). This packet's verdict is the fresh run at `eb5b6a1dd`.
