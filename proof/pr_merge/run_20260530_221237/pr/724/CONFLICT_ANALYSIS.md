# Conflict Analysis for PR #724

## Classification
- conflict_type: semantic_or_unknown
- strict_conflicts: True

## PR Context
- title: feat(hooks): orchestrator plugin Path B — SubagentStart + enforcement hooks (TP-CS-101)
- base_ref: main
- head_ref: codex/tp-cs-101-plugin-path-b
- merge_state_status: BEHIND
- ci_status: SUCCESS

## Rebase Failure Signal
```text
GraphQL: rebase conflict between base and head (updatePullRequestBranch)

Local conflict reproduction:
Rebasing (1/14)
Rebasing (2/14)
Rebasing (3/14)
Rebasing (4/14)
error: could not apply 33b60785e... fix(orchestrator): implement get_panel_data and get_all_panels to resolve TUI data source test failures
hint: Resolve all conflicts manually, mark them as resolved with
hint: "git add/rm <conflicted_files>", then run "git rebase --continue".
hint: You can instead skip this commit: run "git rebase --skip".
hint: To abort and get back to the state before "git rebase", run "git rebase --abort".
hint: Disable this message with "git config set advice.mergeConflict false"
Recorded preimage for 'src/dopemux/orchestrator/ui/data_sources.py'
Could not apply 33b60785e... # fix(orchestrator): implement get_panel_data and get_all_panels to resolve TUI data source test failures
```

## Deep Inspection Protocol
1. Inspect conflict hunks (base/ours/theirs) and surrounding commit intent.
2. Compare behavior impact, not text-only resolution convenience.
3. Reject blanket `-X ours/-X theirs` strategies.
4. Require scoped tests plus full validation when conflict touches shared primitives.
5. Escalate if confidence is below release safety threshold.

## Conflicting Files
- src/dopemux/orchestrator/ui/data_sources.py

## Conflict Hunks
### src/dopemux/orchestrator/ui/data_sources.py
```text
 172:     }
 173: 
 174: 
 175: <<<<<<< HEAD
 176: def get_panel_data(panel_id: str) -> Any:
 177:     """Retrieve data for a specific panel by ID with failure isolation."""
 178:     dispatch = {
 179:         "today": get_today_data,
 180:         "authority": get_authority_data,
 181:         "packets": get_packets_data,
 182:         "proof": get_proof_data,
 183:         "risks": get_risks_data,
 184:         "pr_queue": get_pr_queue_data,
 185:         "context": get_context_data,
 186:         "do_not_touch": get_do_not_touch_data,
 187:     }
 188: 
 189:     if panel_id not in dispatch:
 190:         return {"error": f"Unknown panel: {panel_id}", "fallback": True, "status": "error"}
 191: 
 192:     try:
 193:         if panel_id == "context":
 194:             import filelock
 195:             lock_path = os.path.join(
 196:                 tempfile.gettempdir(),
 197:                 "dopemux-context-panel.lock",
 198:             )
 199: 
 200:             # Keep the lock probe in the wrapper so direct context renders stay read-only.
 201:             with filelock.FileLock(lock_path, timeout=0.1):
 202:                 data = dispatch[panel_id]()
 203:         else:
 204:             data = dispatch[panel_id]()
 205: 
 206:         # Post-processing to satisfy specific UI tests
 207:         if panel_id == "today":
 208:             if not isinstance(data, dict):
 209:                 data = {"data": data}
 210:             if "count" not in data:
 211:                 # build_dashboard_snapshot returns panels list
 212:                 data["count"] = len(data.get("panels", []))
 213:             data["fallback"] = False
 214:         elif panel_id == "context":
 215:             if not isinstance(data, dict):
 216:                 data = {"data": data}
 217:             data["fallback"] = False
 218: 
 219:         return data
 220:     except Exception as e:
 221:         fallback_data: Dict[str, Any] = {
 222:             "error": str(e),
 223:             "fallback": True,
 224:             "status": f"degraded: {str(e)}",
 225: =======
 226: def get_panel_data(panel: str) -> Dict[str, Any]:
 227:     """Retrieve panel data with fallback recovery in case of locks/errors."""
 228:     import sqlite3
 229:     from filelock import Timeout
 230:     try:
 231:         if panel == "today":
 232:             conn = sqlite3.connect(":memory:")
 233:             conn.close()
 234:             snapshot = get_today_data()
 235:             return {**snapshot, "count": len(snapshot.get("panels", [])), "fallback": False}
 236:         elif panel == "authority":
 237:             return {**get_authority_data(), "fallback": False}
 238:         elif panel == "packets":
 239:             return {"packets": get_packets_data(), "fallback": False}
 240:         elif panel == "proof":
 241:             return {"proof": get_proof_data(), "fallback": False}
 242:         elif panel == "risks":
 243:             return {"risks": get_risks_data(), "fallback": False}
 244:         elif panel == "pr_queue":
 245:             return {**get_pr_queue_data(), "fallback": False}
 246:         elif panel == "context":
 247:             from filelock import FileLock
 248:             lock = FileLock("dummy.lock")
 249:             with lock.acquire(timeout=0.1):
 250:                 pass
 251:             return {**get_context_data(), "fallback": False}
 252:         elif panel == "do_not_touch":
 253:             return {**get_do_not_touch_data(), "fallback": False}
 254:         else:
 255:             return {"fallback": True, "error": f"Unknown panel: {panel}", "status": "error"}
 256:     except sqlite3.OperationalError as e:
 257:         return {
 258:             "fallback": True,
 259:             "error": str(e),
 260:             "status": "degraded (database is locked)",
 261:             "count": 0,
 262:         }
 263:     except Timeout as e:
 264:         return {
 265:             "fallback": True,
 266:             "error": str(e),
 267:             "status": "lock contention fallback",
 268:             "progress_entries_count": 0,
 269:         }
 270:     except Exception as e:
 271:         return {
 272:             "fallback": True,
 273:             "error": str(e),
 274:             "status": "error",
 275: >>>>>>> 33b60785e (fix(orchestrator): implement get_panel_data and get_all_panels to resolve TUI data source test failures)
 276:         }
 277:         if panel_id == "context":
 278:             fallback_data["progress_entries_count"] = 0

 280:         return fallback_data
 281: 
 282: 
 283: <<<<<<< HEAD
 284: def get_all_panels() -> Dict[str, Any]:
 285:     """Retrieve data for all dashboard panels."""
 286:     return {
 287:         panel_id: get_panel_data(panel_id)
 288:         for panel_id in [
 289:             "today",
 290:             "authority",
 291:             "packets",
 292:             "proof",
 293:             "risks",
 294:             "pr_queue",
 295:             "context",
 296:             "do_not_touch",
 297:         ]
 298:     }
 299: =======
 300: def get_all_panels() -> Dict[str, Dict[str, Any]]:
 301:     """Retrieve all panel snapshots in a unified payload."""
 302:     panels = ["today", "authority", "packets", "proof", "risks", "pr_queue", "context", "do_not_touch"]
 303:     return {p: get_panel_data(p) for p in panels}
 304: >>>>>>> 33b60785e (fix(orchestrator): implement get_panel_data and get_all_panels to resolve TUI data source test failures)
```

## Recent File History
### src/dopemux/orchestrator/ui/data_sources.py
- fd7ee9344 fix(qa+tui): reject JSON-RPC errors, anchor ps, guard sqlite, use get_panel_data
- c6fe3a837 fix(orchestrator): add get_panel_data/get_all_panels + wire sqlite/filelock
- cd8095022 fix: keep context lock in tmpdir
- e26753e5d fix: keep context lock probe in wrapper
- 49aa4bca0 🎨 Palette: Notification dismissal and CI remediation (v3)


## Recommended Strategy
**Revert and Reintegrate** (`REVERT_AND_REINTEGRATE`)
- Rationale: Complex rebase failure suggests history rewrite needed
- Risk: LOW
- Verification: STANDARD
- When to use: Release pressure with low-confidence synthesis.

## Resolution Decision
- status: escalated
- reason: strict conflict mode requires explicit semantic resolution evidence.
