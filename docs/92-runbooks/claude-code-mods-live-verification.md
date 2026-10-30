---
id: RUNBOOK-CLAUDE-CODE-MODS-LIVE-VERIFICATION
title: Claude Code Mods Live Verification
type: runbook
owner: '@hu3mann'
author: claude-code
date: '2026-10-29'
last_review: '2026-10-29'
next_review: '2027-01-27'
prelude: How to run the Pulse, Route Ledger and Memory Bridge mods in a real Claude Code session for the first time, what to record, and what a result changes.
---
# Claude Code Mods Live Verification

None of the three mods has ever run in a real Claude Code session. Their audits and offline tests describe the code against a mocked host. This runbook is how that gap is closed. The exact per-step commands and pass/fail observations live in each mod's reference; this page orders the work and says what to do with the results.

| Mod | Checklist |
|---|---|
| Pulse | [Pulse reference, section 9](../03-reference/mods/pulse.md) (14 steps) |
| Route Ledger | [Route Ledger reference, section 10](../03-reference/mods/route-ledger.md) (17 steps) |
| Memory Bridge | [Memory Bridge reference, section 10](../03-reference/mods/memory-bridge.md) (10 steps) |

## Before you start

- The operator runs this. It needs a real session and, for Pulse and Memory Bridge, real local services. An agent can prepare commands and read results but should not claim a step passed that it did not observe.
- Use a checkout that contains the mod. Until the PRs merge that means the PR branch: `feat/pulse-001` (#1472), `claude/route-ledger-001-8d8032` (#1482), `claude/memory-bridge-001-b349d8` (#1483).
- Run each mod **alone first**. Only run the coexistence steps after each passes alone.
- **Memory Bridge writes to the real capture ledger** (`dopemux capture emit`) and to `.dopemux/` in the repo. Run its steps 3-5 in a repository where an extra test event is acceptable, and say so before you start.
- Pulse needs the ADHD engine reachable at `127.0.0.1:3025` (its step 3 checks this).
- Do not edit a mod while verifying it. A change to audited code is a new audit subject.

## Order

1. **Offline gates for all three**, as step 1 of each checklist (`claude plugin validate`, `claude plugin test`). These confirm the checkout is the audited one: Pulse 29 pass, Route Ledger 53 pass, Memory Bridge 105 pass.
2. **Route Ledger alone.** It has no service dependency, so it is the cheapest way to learn whether the host calls hooks the way the mods assume. Its steps 5-7 answer the open question about `tool_use_id` and hook ordering (finding N1).
3. **Pulse alone**, with the engine up. Include its engine-down and hung-engine steps (9 and 13); step 13 is the one that answers finding N2.
4. **Memory Bridge alone**, in the repository you chose for its writes.
5. **Coexistence.** Load two mods in one session, then all three, and record:
   - what the status line shows when more than one mod sets it;
   - which `AbovePrompt` band shows first when Pulse and Memory Bridge both draw one;
   - whether any slash command is refused as a name collision (Route Ledger's `/route` alias is the known candidate).

   Whether `--plugin-dir` can be repeated is itself unverified; the references say to check `claude --help`.

## What to record

For every step write one of **PASS**, **FAIL**, **NOT_RUN** or **UNKNOWN**, plus what you saw. Never fold NOT_RUN or UNKNOWN into PASS. Keep it next to the mod's proof, for example a `LIVE_VERIFICATION.md` under `proof/<PACKET_ID>/` with:

| Field | Content |
|---|---|
| Date and operator | who ran it, when |
| Host | Claude Code version, CLI or desktop, OS |
| Mod head | `git rev-parse HEAD` of the checkout and the audited content head |
| Steps | the table of results, one row per checklist step |
| Surprises | anything the reference did not predict, verbatim |
| Output samples | the status line, band and toast text you saw, copied exactly |

## What a result changes

| Result | What it means | What to do |
|---|---|---|
| Step passes as predicted | The finding it covers (for example N1 or N7) can be closed in the follow-up list. | Record it. The audit verdict does not change. |
| Step fails or behaves differently | The mod does not do what its docs say. | Record it verbatim. Do not patch the mod in the same change. Open a follow-up. A code repair changes the audited subject and needs a new audit on an operator-approved route. |
| A document is wrong but the code is right | Docs drift, not a mod defect. | Fix the docs in a docs-only PR opened after the mod's PR has merged, so the audited PR is not changed. |
| Coexistence breaks (status line overwritten, band order wrong) | A cross-mod defect no single audit covered. | Record it and decide with the operator whether the mods ship together. |

## After all steps

- Update the "Run in a real session" row in [Dopemux Claude Code Mods](../04-explanation/claude-code-mods.md) and the status box in each reference from NOT_RUN to the recorded result.
- Close or reopen the live-run findings in each mod's `review_bundle/FOLLOWUPS.md` with a pointer to the recorded results.
- Update the agent guidance in `.claude/modules/shared/plugin-integration.md` with the new state. Agents may describe a mod as working live only after a recorded PASS.
