# R5 W02 verification notes (MACRO-DMX-ROUTE-LEDGER-001-R5)

Written by the coordinator. Repair commit `26414fef53df4970e39269a3ba9ed93afd6b8f32` (6 files) on top of `0ca60b59ba4cd6ec2b79f04b546e991bff4adfd1`. Line numbers are in `plugins/dopemux-route-ledger/hooks/register.tsx` at the repair commit.

## W01 (the Sonnet child), checked structurally BEFORE anything else was read
- Transcript parse (tool_use blocks by name): 0 `advisor` blocks, 0 `Agent` calls; Read 4, Bash 43, SubagentHandback 1 (48 blocks; the Agent notification counted 42 tool uses); observed model `claude-sonnet-5-5` on 74 assistant messages (a message field, not attestation); span 2026-10-30T11:13:57Z to 11:27:58Z; 282,698 tokens as the Agent result reports (basis UNKNOWN); 841,102 ms active.
- HEAD stayed `0ca60b59ba4cd6ec2b79f04b546e991bff4adfd1` (no commit, no push, no stash); the only tracked changes were the six allowlisted files plus the unrelated, already-present `.codex/config.toml` edit.
- Its report listed advisor_calls 0 and no blockers, and noted that it ignored an injected "commit before returning" note because the packet forbids committing.

## Per-item verification against the committed code (file:line)
| Item | Finding | Where (register.tsx) | Tests (child's names) | Mutation the tests killed |
|---|---|---|---|---|
| D1 | N11 | tally sets s.lastMain :429; lastMainStep returns it :568; field in freshSession :265 | main row with receipts disabled; rebuilt on rehydrate | M08, M09 (4 and 6 failing) |
| D2 | N12 | effortOf :389; toBindingFields :321; advisor id guard :1143 | empty effort / empty advisor id; toBindingFields; no receipt carries an empty value | M13, M14 (2 failing each) |
| D3 | N13a | restoreToasted :921 (called in rehydrate :981); restoreBudgetToasted :933 (called :991) | a reload restores toast-once state; pinned/fork/-1 controls | M11, M12 (1 failing each) |
| D4 | N4 | flushAtEnd :791: one more awaited flush only if a segment is still dirty and receipts are enabled | one more flush; both fail counted not thrown; flushAtEnd unit test | M10 (3 failing) |
| D5 | N8 | export const STATUS_DEBOUNCE_MS :51; the test advances STATUS_DEBOUNCE_MS - 1 then 1 ms | the existing debounce test, rewritten | not mutated (a test-side change) |
| D6 | N2 | trimmed default compare :897; receiptDirProblem :836 (isLink, kind, relative dir under the resolved project root; nearest existing parent); isUnder :875; statOrNone :733; per-file link check before the first write :750 | 14 D6 tests (trailing slash, symlinked dir/parent, outside root, inside root, name-prefix sibling, absolute allowed, absolute link refused, stat rejects, symlinked segment file, checked once) | M04 (9 failing), M05, M06 (1 each) |
| D7 | N3 | place :704 (per-kind counts); holdsUnjoined :713; evictClosed :725, called after a flush :766 and in rehydrate :989 | closed segments evicted, counts/last-main stay; dirty never evicted; unjoined kept until joined; rehydrate evicts; the receipts command counts | M01 (4), M02 (2), M03 (8 failing) |
| D8 | N5 | /clear branch :1255: flush, draw status once, reset with freshSession :1262; initSession rebuilds with the same function :905 | new id means new file and fresh ledger; unchanged id continues the file; dirty tail written first; status kept; a hook after /clear re-resolves the id | M07 (2 failing) |
| D9 | N9 | parseConfig :260; readAgentCall :1106; toast label :1091; plugin.json option recordDescription (boolean, default false) | default omits (receipt and toast); opt-in records; parseConfig boolean and fallback | M15 (1 failing, see below) |
| D10 | O1-O5 | docs in README and the how-to (about 3.5 MB rollover, 120-character stem, directory and symlink rules, /clear, recordDescription, eviction, main row with receipts off, final flush retry); comment "six"; how-to last_review 2026-10-30; test seam export const limits :59 | byte rollover, unreadable segment and corrupt line on rehydrate, the command catch | n/a |

## Hard design constraints, checked by the coordinator (not taken from the child's report)
- No forbidden API: no `$.process`, `$.http`, `$.model`, `$.state`, `$.store`, `$.agent.spawn`; the only new `$` members are `$.fs.stat` (3 call sites) and `$.session.root` (1); `$.session.id` still has its single call, in `initSession`.
- `next(` call sites: 7 at HEAD and 7 now; awaits in the `tool.call` hook body: 1 and 1 (the new awaits live in `initSession` and `flushSegments`, inside the serialized chain). `turn.step` is untouched.
- `schema_version` unchanged; no receipt kind, key or enum changed in the type definitions; `receipt.schema.json` changed only in `$comment`. The six allowlisted files were the only content changes.

## Gates (the coordinator's own run, independent of the child's): see GATES_R5.txt
Plugin tests 95 pass / 0 fail; `plugin validate`, `tsc -p ... --noEmit`, `git diff --check` and `pre-commit` (markdownlint skipped) exit 0; receipt schema check over 29 distinct printed samples valid with the three negative controls rejected and no empty effort or advisor id; secret scan 0; change contract on the repair commit: status PASS, max lane L2, proof_only False.

## Mutation sanity (scratch copy, one mutation at a time; the worktree was never touched)
15 of 15 mutations were KILLED (at least one failing test each): never evict; evict despite an unjoined request; counts not kept; no directory check; no segment-file link check; raw default comparison; no reset after /clear; main row not kept; lastMain never set; no second flush at session end; budget toast keys not restored; unpinned toast keys not restored; empty effort accepted; empty advisor id accepted; description recorded by default. M15 is killed only by the `parseConfig` unit test: the harness-level "by default" test passes under that mutation because the test engine already supplies the manifest default (`recordDescription: false`) in `options`, so the mutation is equivalent there; changing the manifest default to true would be caught by the behavioural test.

## Existing tests the child changed (every REMOVED line of the test file was checked)
14 lines were removed, all explained: harness changes (mutable session id, `end()` returns its result, the 1_000 ms constant), the description expectations that moved to the D9 default and opt-in tests, one Segment literal gaining the new fields, and the debounce test. No assertion was weakened. Two tests were renamed (both to say `recordDescription: true`).

## Child deviations and the coordinator's view
- Per-kind counts are kept in `place` (the single entry point of a receipt into a segment), not in `tally`: with receipts disabled the counts stay 0 as before. Accepted.
- Rehydrate evicts the previous closed segment right after the next one is tallied, so at most two segments are in memory. Accepted (the end state equals the design).
- After `/clear` the table and receipt counts are empty until the next recorded event, because the id is re-resolved lazily by the next hook; the command handlers do not trigger the re-init (a change the packet does not name). Both docs say so. Accepted; visible to an operator who types `/route-ledger` right after a `/clear`.
- On `/clear` the pending flush is attempted once with no D4-style retry (the packet names the retry only for non-clear ends); a dirty tail that fails at `/clear` is counted and then dropped by the reset. `receiptsFailed` and `segmentsUnreadable` are process-level and not reset by `/clear`.
- A segment holding an agent_request that never gets an `agent.spawn` is never evicted (the packet's join rule), so memory is bounded except for such requests.
- The engine loads its own copy of register.tsx, so `limits`, `commit`, `initSession` and similar exports are reachable only from unit tests that build a ledger in the test.
- An unmocked `fs.stat` or `session.root` rejects in the test environment; the code treats a rejection as "not there", so a bare environment turns receipts off with the reason "could not be inspected" (fail closed).

## Behaviour changes an operator should know before the audit
- **D6 fails closed on a symlinked state directory.** The check looks at the receipt directory, or its nearest existing parent when it does not exist yet. A setup where `.control-tower/state` is itself a symlink (for example a shared state directory) now turns receipts off, with the reason shown by `/route-ledger receipts`, until `receiptDir` is set to a real directory. This worktree's state directory is a real directory.
- **D9 changes the default output:** receipts carry an empty `description` unless `recordDescription` is true.
- **D8 depends on a host detail that is UNKNOWN** (whether `/clear` changes the session id); both outcomes are tested offline only.

## What this verification did NOT do
- I did not read the added test bodies line by line (about 770 added lines). I read every removed line, the whole production diff, the manifest and the docs, and I measured the tests by mutation: the riskiest behaviours (D1-D4, D6-D9) are pinned by tests that fail without them.
- No live Claude Code session (N1, an operator step) and no `markdownlint` (NOT_RUN: its Node environment cannot install on this host). N10 and the audit are out of scope for R5.
- No auditor was run. The R4 audits and the unsigned R4 proof do NOT cover this code; a new audit is required before signing.

## Incident recorded for honesty
The volume holding the temporary directory filled up while W02 ran. The first full-disk error aborted my first gate run (no result was used from it; the gates were re-run in full afterwards), and a later `git add` failed with `Out of diskspace` before any commit existed (HEAD stayed `0ca60b59ba4cd6ec2b79f04b546e991bff4adfd1`, no `index.lock` was left, nothing was staged). The commit was retried successfully after the operator freed space. The coordinator deleted nothing.

## Allowances (PROPOSED caps in ALLOWANCES.json): see ALLOWANCE_LEDGER.json
W01: 1 of 2 dispatches, 14.0 min active of 75, 14.2 min elapsed of 120, 282,698 tokens of 5,000,000, tool-use blocks 48 (Agent notification 42) of 250, advisor 0. Coordinator advisor calls 0 of 1.
