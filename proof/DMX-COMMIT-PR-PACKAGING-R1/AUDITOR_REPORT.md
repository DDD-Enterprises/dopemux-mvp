**Subject:** manifest SHA256 `ee97fb4d…c96e`, HEAD `75dacb43…da`. I reviewed the supplied files and the full incremental diff statically. I ran nothing.

**Verdict: PASS_WITH_RISKS. Acceptance NOT_GRANTED.**

**1. Guard coverage (verified).**
- The guard calls `merge_known_inventory(store.replay()["known_inventory"], inventory)`.
- `known_inventory` is replay-derived and already unions admitted and approved-imported inventories. Import-only reservations in earlier import manifests are therefore included.
- Source-key conflicts raise `ContractError("Conflicting historical allocation")` (a `ValueError`) when the same key has a different `project_id`.
- Legacy source-key conflicts are caught the same way.
- Reverse `(project_id, task_id)` conflicts are caught by the `AllocationInventory` uniqueness validator on the merged result.
- All three are mapped to `StoreError(409, "invalid_import_inventory")`.

**2. Transaction placement (verified).**
- The guard is the first statement inside `store._transaction()`, before the registry check, `_identity_absent`, `_dependencies` and `_append`.
- `BEGIN IMMEDIATE` runs first. On exception the transaction rolls back, and the head is unchanged, so no checkpoint is advanced.
- No journal, task, operation or outbox row is written, so the idempotency key is not consumed.
- `_replay_operation` still runs before `dry_run` and the new checks, so completed-import replay is unchanged.
- `replay()` integrity failures raise `StoreError`, not `ValueError`, so they are not mislabelled as inventory denial.

**3. Compatibility (verified).**
- `merge_known_inventory` is unchanged and already takes the max revision.
- Equal-revision additive imports still merge. The `(1, 1)` parametrization exercises this.
- Replay and reopen are unchanged, because the guard is read-only before `_append`.
- Suspension and revocation checks are untouched.
- The existing `invalid_admission_replacement` path is still exercised.

**4. Tests (verified, with caveats).**
- The new test drives public `import_bound` and `dry_run` for all three conflict forms.
- It asserts status 409, byte-equal state before and after the denial (replay, table rows and checkpoint bytes), and reuse of the denied key with a corrected manifest.
- It also checks the post-import union and revision, replay of both completed imports, and reopen.
- The private `_db` access is read-only and used only for snapshots.
- The parametrization of the existing union test is sensible, but only part of that test is visible.

**5. Scope and docs (verified).** The diff is narrow: one production hunk, the tests and one doc paragraph. The doc matches the behavior. It does not add enrollment, a schema change or a completeness claim.

**Residual risks (low):**
- The guard catches every `ValueError`, including pydantic validation errors, so an unexpected validation failure in the merge would also surface as `invalid_import_inventory`.
- The `s.Error` alias used by the tests is not visible in the supplied `sqlite_store` excerpt, but earlier tests already use it.
- Unchanged hunks of the modified union test and the rest of the test file were not supplied.
- The legacy `inventory["revision"] < policy[...]` and superset checks still compare against policy, not known inventory. This is consistent with the stated contract, since the merge handles the union.

```json
{"status":"PASS_WITH_RISKS","findings":[{"id":"L1","severity":"low","location":"maintenance.py import_bound guard","summary":"Guard maps any ValueError from merge (including unexpected pydantic validation errors) to invalid_import_inventory","evidence":"except ValueError around merge_known_inventory"},{"id":"L2","severity":"low","location":"tests/unit/pm/test_ownership_maintenance.py","summary":"Unchanged parts of modified union test and s.Error alias not in supplied excerpt","evidence":"Hunk context gaps; sqlite_store lines 45-50 not supplied"}],"checks":[{"id":"1","bucket":"PASS","evidence":"Guard merges replay known_inventory with the manifest inventory; the source key, legacy key and reverse (project,task) conflicts all raise ValueError and map to a typed 409"},{"id":"2","bucket":"PASS","evidence":"Guard is first in _transaction before _append; rollback leaves head unchanged so no checkpoint; _replay_operation runs earlier"},{"id":"3","bucket":"PASS","evidence":"merge_known_inventory unchanged; equal-revision case parametrized; read-only guard leaves replay/reopen unchanged; grant/suspension checks untouched"},{"id":"4","bucket":"PASS","evidence":"New test uses public import_bound/dry_run, asserts 409, full state equality (rows, checkpoint bytes), denied-key reuse, replay of both imports"},{"id":"5","bucket":"PASS","evidence":"Single production hunk plus doc paragraph consistent with the contract; no schema or enrollment change"}],"instruction_like_content":[],"author_claims_not_reproduced":["306 passed in 4.42s, exit 0 (NOT_RUN by reviewer)"],"remaining_risks":["Broad ValueError catch","Partial test-file visibility","No runtime or concurrency verification"],"unknowns":["s.Error alias definition","Unchanged lines of the modified union test"],"acceptance":"NOT_GRANTED"}
```