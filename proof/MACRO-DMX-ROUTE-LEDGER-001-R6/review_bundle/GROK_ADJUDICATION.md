# Grok adjudication (MACRO-DMX-ROUTE-LEDGER-001-R6, W04, PRIMARY route)

Written by the coordinator after BOTH custody commits existed (`ced97d784` Grok, `91bf32291` AGY). Source examined: the seven content paths at `b275543fe1011bf3a9351a10448c24d94f205370` (`git diff --quiet b275543fe HEAD` over those paths: no difference, so the working tree equals the subject). Line numbers are in `plugins/dopemux-route-ledger/hooks/register.tsx` unless stated. Authority NONE.

## Verdict as returned
- `status`: `PASS_WITH_RISKS`; Q1-Q13 all PASS; 5 findings (1 HIGH, 4 INFO), none BLOCKING; `tools_used: none`; `instruction_like_content.detected: false`. Raw: `GROK_AUDIT_RESPONSE_RAW.txt` (sha256 in `SHA256SUMS_GROK.txt`).
- `model_self_reported`: `grok-4`. The CLI was run with `-m grok-4.5` and every init event shows `grok-4.5`; R4's answer said `grok-4.7`. The self-report is a claim, not attestation: UNRESOLVED, provider attestation UNKNOWN.
- Input integrity: the Grok answer cites `advisor_use_id` `minLength 1`, which is `receipt.schema.json:156`, past the point where AGY's copy was cut (see `AGY_ADJUDICATION.md` N5). Grok shows no sign of truncation and its stream has no `<truncated` marker. This is evidence, not proof, that Grok received the whole prompt.

## Findings (severity kept as the auditor gave it)
| Id | Severity | Adjudication | Evidence |
|---|---|---|---|
| N1 | HIGH | CONFIRMED | The frozen head has not run in a real Claude Code session. `GATES_PRE_AUDIT.txt` records the live check as NOT_RUN; the README ("Not run yet: a live Claude Code session loading the mod. Offline tests only.") and the how-to ("Live behaviour is NOT VERIFIED") say the same. A fact about evidence, not a code defect; it can only be cleared by the operator's live check. |
| N10 | INFO | CONFIRMED | README "Limits": the plugin API is early access and coexistence with another plugin's status line is unverified and "was not run". The declaration file is not in the diff. |
| N14 | INFO | CONFIRMED | `receiptDirProblem` returns no problem for an absolute directory once the link and kind checks pass (`register.tsx:874`, `if (!isRelative) return undefined`); the test "D6: an absolute directory is allowed by design" pins it; README Options and the how-to say "An absolute directory is allowed". Disclosed limitation (vii). By design. |
| N15 | INFO | CONFIRMED | The 15-mutation check ran on `26414fef5` only: `SUCCESSOR_NOTE_CODEX_CLEAR.md` and `SUCCESSOR_NOTE_CODEX_LIST_BYTES.md` both say "Not re-run" (the scratch harness no longer exists), and `61c371f28` and `3d2af4b20` changed production code afterwards. Disclosed limitation (e). |
| N16 | INFO | CONFIRMED | `GATES_PRE_AUDIT.txt`: the markdownlint hook is NOT_RUN (the hook is skipped; its Node environment cannot install on this host, carried from the R5 notes and not re-tested here). Disclosed limitation (g). |

Totals: 5 findings, 5 CONFIRMED, 0 REFUTED, 0 UNVERIFIABLE; none BLOCKING.

## Question-level notes (Q1-Q13)
All thirteen PASS. The coordinator did not re-adjudicate each evidence sentence; the findings above are what the auditor asked to be tracked. Its Q12 list (D1-D10 and the three later fixes, each with pinning tests) agrees with the coordinator's own mapping in `PRIOR_FINDINGS_AS_CLAIMS.md`.

## What the Grok audit does not cover
- The auditor had no tools: it judged the diff text and could not run the code or the tests. It named as not run: the live session, the host's `/clear` session-id behaviour, status-line coexistence, `/route` acceptance, the mutation re-run and markdownlint.
- Provider attestation of the model is UNKNOWN; the CLI still injected home-level instruction, skill and MCP-server names (no tools, no secret values).
