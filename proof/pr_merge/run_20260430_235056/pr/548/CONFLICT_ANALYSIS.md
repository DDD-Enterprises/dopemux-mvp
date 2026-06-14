# Conflict Analysis for PR #548

## Classification
- conflict_type: semantic_or_unknown
- strict_conflicts: True

## PR Context
- title: Restore deterministic runtime authority verifier
- base_ref: main
- head_ref: fix/restore-runtime-authority-verifier
- merge_state_status: DIRTY
- ci_status: FAILURE

## Rebase Failure Signal
```text
X Cannot update PR branch due to conflicts

Local conflict reproduction:
Rebasing (1/1)
error: could not apply 14b60d2db... Restore deterministic runtime authority verifier
hint: Resolve all conflicts manually, mark them as resolved with
hint: "git add/rm <conflicted_files>", then run "git rebase --continue".
hint: You can instead skip this commit: run "git rebase --skip".
hint: To abort and get back to the state before "git rebase", run "git rebase --abort".
hint: Disable this message with "git config set advice.mergeConflict false"
Recorded preimage for 'config/runtime_authority_manifest.json'
Recorded preimage for 'scripts/verify_runtime_authority.py'
Recorded preimage for 'tests/unit/test_runtime_authority_manifest.py'
Could not apply 14b60d2db... # Restore deterministic runtime authority verifier
```

## Deep Inspection Protocol
1. Inspect conflict hunks (base/ours/theirs) and surrounding commit intent.
2. Compare behavior impact, not text-only resolution convenience.
3. Reject blanket `-X ours/-X theirs` strategies.
4. Require scoped tests plus full validation when conflict touches shared primitives.
5. Escalate if confidence is below release safety threshold.

## Conflicting Files
- config/runtime_authority_manifest.json
- scripts/verify_runtime_authority.py
- tests/unit/test_runtime_authority_manifest.py

## Conflict Hunks
### config/runtime_authority_manifest.json
```text
   1: {
   2: <<<<<<< HEAD
   3:   "authority_rules": [
   4:     "Runtime code, config, and tests outrank generated docs.",
   5:     "Static verification must not call network services or mutate production state.",
   6:     "Bridge, proxy, retrieval, and mirror surfaces must not be promoted to PM-plane authority."
   7:   ],
   8:   "forbidden_legacy_targets": [
   9:     {
  10:       "expected_conflict": false,
  11:       "paths": [
  12:         "compose.yml",
  13:         "services/task-orchestrator/Dockerfile"
  14:       ],
  15:       "reason": "task_orchestrator.app hard-fails and is not the supported task-orchestrator runtime.",
  16:       "system": "task-orchestrator",
  17:       "target": "task_orchestrator.app:app"
  18:     }
  19:   ],
  20:   "generated_by": "TP-DMX-RUNTIME-VERIFY-001",
  21:   "known_conflicts": [
  22:     {
  23:       "evidence": [
  24:         {
  25:           "path": "services/dope-memory/mcp_stdio_adapter.py",
  26:           "patterns": [
  27:             "8096"
  28:           ]
  29:         },
  30:         {
  31:           "path": "scripts/mcp_smoke.sh",
  32:           "patterns": [
  33:             "8096"
  34:           ]
  35:         }
  36:       ],
  37:       "expected": "dope-memory registry and compose port 3020",
  38:       "observed": "legacy dope-memory adapter and smoke references still point at 8096",
  39:       "system": "dope-memory",
  40:       "type": "port_conflict"
  41:     },
  42:     {
  43:       "evidence": [
  44:         {
  45:           "path": "docker/mcp-servers-source/services/task-orchestrator/Dockerfile",
  46:           "patterns": [
  47:             "3014"
  48:           ]
  49:         },
  50:         {
  51:           "path": "services/mcp-integration-bridge/main.py",
  52:           "patterns": [
  53:             "3014"
  54:           ]
  55:         }
  56:       ],
  57:       "expected": "task-orchestrator registry and compose port 8000",
  58:       "observed": "legacy MCP bridge surfaces still reference 3014",
  59:       "system": "task-orchestrator",
  60:       "type": "port_conflict"
  61:     },
  62:     {
  63:       "evidence": [
  64:         {
  65:           "path": "docs/03-reference/truth/truth-canonicals.md",
  66:           "patterns": [
  67:             "src/conport/memory_server.py"
  68:           ]
  69:         },
  70:         {
  71:           "path": "compose.yml",
  72:           "patterns": [
  73:             "docker/mcp-servers/conport/Dockerfile"
  74:           ]
  75:         },
  76:         {
  77:           "path": "docker/mcp-servers/conport/Dockerfile",
  78:           "patterns": [
  79:             "docker/mcp-servers-source/conport/enhanced_server.py",
  80:             "docker/mcp-servers-source/conport/server.py"
  81:           ]
  82:         }
  83:       ],
  84:       "expected": "ConPort canonicality remains split between source-level memory_server.py and deployed Docker wrapper surfaces",
  85:       "observed": "runtime source and deployed container entrypoints are not the same file family",
  86:       "system": "ConPort",
  87:       "type": "runtime_pointer_conflict"
  88:     }
  89:   ],
  90:   "repo_identity": {
  91:     "origin_hint": "dopemux-mvp",
  92:     "repo_marker": ".dopetaskroot",
  93: "require_identity_match": false
  94:   },
  95:   "schema_version": "1.0",
  96:   "systems": [
  97:     {
  98:       "authority_notes": [
  99:         "pyproject.toml exposes the dopemux console script through dopemux.cli:main.",
 100:         "src/dopemux/cli.py contains the active Click command tree."
 101:       ],
 102:       "authority_status": "canonical",
 103:       "expected_entrypoints": [
 104:         "dopemux = dopemux.cli:main"
 105:       ],
 106:       "expected_paths": [
 107:         {
 108:           "path": "src/dopemux/cli.py",
 109:           "required": true,
 110:           "role": "CLI runtime"
 111:         },
 112:         {
 113:           "path": "pyproject.toml",
 114:           "required": true,
 115:           "role": "console-script declaration"
 116:         }
 117:       ],
 118:       "expected_ports": [],
 119:       "system": "dopemux",
 120:       "validation_mode": "static_required"
 121:     },
 122:     {
 123:       "authority_notes": [
 124:         "scripts/dopetask enforces .dopetaskroot and .dopetask-pin before executing the pinned dopetask binary.",
 125:         "scripts/taskx is a compatibility shim, not a separate runtime."
 126:       ],
 127:       "authority_status": "canonical",
 128:       "expected_entrypoints": [
 129:         "scripts/dopetask"
 130:       ],
 131: =======
 132:   "authority_status_values": [
 133:     "OBSERVED",
 134:     "CONFLICTING",
 135:     "UNKNOWN",
 136:     "DERIVED",
 137:     "TRANSPORT_ONLY",
 138:     "SHIM_ONLY"
 139:   ],
 140:   "schema_version": "1.0",
 141:   "systems": [
 142:     {
 143:       "authority_status": "OBSERVED",
 144:       "domain": "operator-control",
 145:       "expected_paths": [
 146:         {
 147:           "path": "pyproject.toml",
 148:           "required": true,
 149:           "role": "console_script_manifest"
 150:         },
 151:         {
 152:           "path": "src/dopemux/cli.py",
 153:           "required": true,
 154:           "role": "operator_cli_runtime"
 155:         },
 156:         {
 157:           "path": "src/dopemux/commands/kernel_commands.py",
 158:           "required": true,
 159:           "role": "dopetask_delegation"
 160:         }
 161:       ],
 162:       "expected_ports": [],
 163:       "forbidden_authority_paths": [],
 164:       "known_conflicts": [
 165:         {
 166:           "id": "legacy_truth_command_drift",
 167:           "markers": [
 168:             {
 169:               "contains": "no longer a supported operator entrypoint for Repo Truth Extractor",
 170:               "path": "src/dopemux/cli.py"
 171:             }
 172:           ],
 173:           "summary": "The legacy dopemux truth command remains present but is not the supported Repo Truth Extractor entrypoint."
 174:         }
 175:       ],
 176:       "notes": [
 177:         "Authority is limited to operator CLI and local coordination behavior.",
 178:         "PM, memory, retrieval, and extraction authorities are delegated to narrower downstream systems."
 179:       ],
 180:       "system": "dopemux",
 181:       "validation_mode": "static_paths_and_markers"
 182:     },
 183:     {
 184:       "authority_status": "OBSERVED",
 185:       "domain": "external-task-execution",
 186: >>>>>>> 14b60d2db (Restore deterministic runtime authority verifier)
 187:       "expected_paths": [
 188:         {
 189:           "path": "scripts/dopetask",

 188:         {
 189:           "path": "scripts/dopetask",
 190:           "required": true,
 191: <<<<<<< HEAD
 192:           "role": "dopetask wrapper runtime"
 193:         },
 194:         {
 195:           "path": ".dopetaskroot",
 196:           "required": true,
 197:           "role": "repo identity marker"
 198: =======
 199:           "role": "execution_wrapper"
 200: >>>>>>> 14b60d2db (Restore deterministic runtime authority verifier)
 201:         },
 202:         {
 203:           "path": ".dopetask-pin",
```

### scripts/verify_runtime_authority.py
```text
   1: #!/usr/bin/env python3
   2: <<<<<<< HEAD
   3: """Deterministic static verifier for Dopemux runtime authority pointers."""
   4: =======
   5: """Static verifier for Dopemux runtime authority manifest."""
   6: >>>>>>> 14b60d2db (Restore deterministic runtime authority verifier)
   7: 
   8: from __future__ import annotations
   9: 

   9: 
  10: import argparse
  11: import json
  12: <<<<<<< HEAD
  13: import re
  14: import subprocess
  15: =======
  16: >>>>>>> 14b60d2db (Restore deterministic runtime authority verifier)
  17: import sys
  18: from pathlib import Path
  19: from typing import Any, Iterable
```

### tests/unit/test_runtime_authority_manifest.py
```text
   1: from __future__ import annotations
   2: 
   3: <<<<<<< HEAD
   4: import importlib.util
   5: =======
   6: import copy
   7: >>>>>>> 14b60d2db (Restore deterministic runtime authority verifier)
   8: import json
   9: import subprocess
  10: import sys

  13: 
  14: REPO_ROOT = Path(__file__).resolve().parents[2]
  15: MANIFEST_PATH = REPO_ROOT / "config" / "runtime_authority_manifest.json"
  16: <<<<<<< HEAD
  17: SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_runtime_authority.py"
  18: 
  19: 
  20: def _load_verifier_module():
  21:     spec = importlib.util.spec_from_file_location("verify_runtime_authority", SCRIPT_PATH)
  22:     assert spec and spec.loader
  23:     module = importlib.util.module_from_spec(spec)
  24:     spec.loader.exec_module(module)
  25:     return module
  26: 
  27: 
  28: def _load_manifest() -> dict:
  29:     return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
  30: 
  31: 
  32: def test_manifest_has_required_system_entry_keys() -> None:
  33:     manifest = _load_manifest()
  34: 
  35:     assert manifest["schema_version"] == "1.0"
  36:     systems = manifest["systems"]
  37:     assert isinstance(systems, list)
  38:     assert {entry["system"] for entry in systems} == {
  39:         "ADHD Engine",
  40:         "ConPort",
  41:         "Repo Truth Extractor",
  42:         "dope-context",
  43:         "dope-memory",
  44:         "dopecon-bridge",
  45:         "dopemux",
  46:         "dopetask",
  47:         "task-orchestrator",
  48:     }
  49: 
  50:     for entry in systems:
  51:         assert {"system", "expected_paths", "authority_status", "validation_mode"} <= set(entry)
  52:         assert isinstance(entry["expected_paths"], list)
  53:         assert entry["authority_status"]
  54:         assert entry["validation_mode"]
  55: 
  56: 
  57: def test_static_verifier_passes_current_manifest_and_reports_known_conflicts() -> None:
  58:     result = subprocess.run(
  59:         [
  60:             sys.executable,
  61:             str(SCRIPT_PATH),
  62:             "--manifest",
  63:             str(MANIFEST_PATH),
  64:             "--check",
  65:             "static",
  66:         ],
  67:         cwd=REPO_ROOT,
  68:         capture_output=True,
  69:         text=True,
  70:         check=False,
  71:     )
  72: 
  73:     assert result.returncode == 0, result.stdout + result.stderr
  74:     report = json.loads(result.stdout)
  75:     assert report["ok"] is True
  76:     assert report["summary"]["errors"] == 0
  77: 
  78:     codes = [finding["code"] for finding in report["findings"]]
  79:     assert "expected_port_conflict" in codes
  80:     assert "expected_runtime_pointer_conflict" in codes
  81: 
  82:     sort_keys = [
  83:         (
  84:             finding["severity"],
  85:             finding["system"],
  86:             finding["code"],
  87:             finding.get("path", ""),
  88:             finding["message"],
  89:         )
  90:         for finding in report["findings"]
  91:     ]
  92:     assert sort_keys == sorted(
  93:         sort_keys,
  94:         key=lambda item: (
  95:             {"error": 0, "warning": 1, "info": 2}.get(item[0], 99),
  96:             item[1],
  97:             item[2],
  98:             item[3],
  99:             item[4],
 100:         ),
 101:     )
 102: 
 103: 
 104: def test_verifier_returns_nonzero_for_unexpected_missing_authority_file(tmp_path: Path) -> None:
 105:     manifest = {
 106:         "repo_identity": {
 107:             "origin_hint": "",
 108:             "repo_marker": "",
 109:             "require_identity_match": False,
 110:         },
 111:         "systems": [
 112:             {
 113:                 "authority_status": "canonical",
 114:                 "expected_paths": [
 115:                     {
 116:                         "path": "missing-authority.py",
 117:                         "required": True,
 118:                     }
 119:                 ],
 120:                 "system": "missing-system",
 121:                 "validation_mode": "static_required",
 122:             }
 123:         ],
 124:     }
 125:     manifest_path = tmp_path / "manifest.json"
 126:     manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
 127: 
 128:     result = subprocess.run(
 129:         [
 130:             sys.executable,
 131:             str(SCRIPT_PATH),
 132:             "--manifest",
 133:             str(manifest_path),
 134:             "--check",
 135:             "static",
 136:         ],
 137:         cwd=REPO_ROOT,
 138:         capture_output=True,
 139:         text=True,
 140:         check=False,
 141:     )
 142: 
 143:     assert result.returncode == 1
 144:     report = json.loads(result.stdout)
 145:     assert report["ok"] is False
 146:     assert report["summary"]["errors"] == 1
 147:     assert report["findings"][0]["code"] == "expected_path_missing"
 148: 
 149: 
 150: def test_unknown_authority_paths_are_advisory(tmp_path: Path) -> None:
 151:     module = _load_verifier_module()
 152:     repo_root = tmp_path
 153:     manifest = {
 154:         "systems": [
 155:             {
 156:                 "authority_status": "unknown",
 157:                 "expected_paths": [
 158:                     {
 159:                         "path": "candidate-only.py",
 160:                         "required": True,
 161:                     }
 162:                 ],
 163:                 "system": "unknown-system",
 164:                 "validation_mode": "static_required",
 165:             }
 166:         ],
 167:     }
 168: 
 169:     report = module.verify_manifest(manifest, repo_root)
 170: 
 171:     assert report["ok"] is True
 172:     assert report["summary"]["errors"] == 0
 173:     assert any(finding["code"] == "unknown_authority_not_asserted" for finding in report["findings"])
 174:     assert any(
 175:         finding["code"] == "expected_path_missing" and finding["severity"] == "warning"
 176:         for finding in report["findings"]
 177:     )
 178: =======
 179: VERIFIER = REPO_ROOT / "scripts" / "verify_runtime_authority.py"
 180: 
 181: REQUIRED_SYSTEMS = {
 182:     "dopemux",
 183:     "dopetask",
 184:     "taskx",
 185:     "task-orchestrator",
 186:     "ConPort",
 187:     "dope-memory",
 188:     "working-memory-assistant",
 189:     "dope-context",
 190:     "dopecon-bridge",
 191:     "ADHD Engine",
 192:     "Repo Truth Extractor",
 193:     "Leantime",
 194:     "Serena",
 195: }
 196: 
 197: REQUIRED_FIELDS = {
 198:     "system",
 199:     "domain",
 200:     "authority_status",
 201:     "expected_paths",
 202:     "expected_ports",
 203:     "forbidden_authority_paths",
 204:     "known_conflicts",
 205:     "validation_mode",
 206:     "notes",
 207: }
 208: 
 209: 
 210: def load_manifest() -> dict:
 211:     return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
 212: 
 213: 
 214: def systems_by_name() -> dict[str, dict]:
 215:     return {entry["system"]: entry for entry in load_manifest()["systems"]}
 216: 
 217: 
 218: def conflict_ids(entry: dict) -> set[str]:
 219:     return {conflict["id"] for conflict in entry["known_conflicts"]}
 220: 
 221: 
 222: def test_manifest_json_parses() -> None:
 223:     manifest = load_manifest()
 224:     assert manifest["schema_version"] == "1.0"
 225:     assert isinstance(manifest["systems"], list)
 226: 
 227: 
 228: def test_required_systems_exist() -> None:
 229:     assert set(systems_by_name()) == REQUIRED_SYSTEMS
 230: 
 231: 
 232: def test_every_entry_has_required_fields() -> None:
 233:     for entry in load_manifest()["systems"]:
 234:         assert REQUIRED_FIELDS <= set(entry)
 235:         assert isinstance(entry["expected_paths"], list)
 236:         assert isinstance(entry["expected_ports"], list)
 237:         assert isinstance(entry["forbidden_authority_paths"], list)
 238:         assert isinstance(entry["known_conflicts"], list)
 239:         assert isinstance(entry["notes"], list)
 240: 
 241: 
 242: def test_known_task_orchestrator_conflict_is_represented() -> None:
 243:     task_orchestrator = systems_by_name()["task-orchestrator"]
 244:     assert task_orchestrator["authority_status"] == "CONFLICTING"
 245:     assert "task_orchestrator_unsupported_runtime_variant" in conflict_ids(task_orchestrator)
 246:     assert "task_orchestrator_port_3014_vs_8000" in conflict_ids(task_orchestrator)
 247: 
 248: 
 249: def test_known_conport_conflict_is_represented() -> None:
 250:     conport = systems_by_name()["ConPort"]
 251:     assert conport["authority_status"] == "CONFLICTING"
 252:     assert "conport_runtime_surface_split" in conflict_ids(conport)
 253:     assert "conport_3004_3005_contract_split" in conflict_ids(conport)
 254: 
 255: 
 256: def test_dope_memory_port_drift_is_represented() -> None:
 257:     dope_memory = systems_by_name()["dope-memory"]
 258:     ports = {item["port"]: item["status"] for item in dope_memory["expected_ports"]}
 259:     assert ports[3020] == "observed"
 260:     assert ports[8096] == "conflicting"
 261:     assert "dope_memory_3020_vs_8096" in conflict_ids(dope_memory)
 262: 
 263: 
 264: def test_taskx_is_shim_only_not_runtime_authority() -> None:
 265:     taskx = systems_by_name()["taskx"]
 266:     assert taskx["authority_status"] == "SHIM_ONLY"
 267:     forbidden_domains = {
 268:         item["forbidden_domain"] for item in taskx["forbidden_authority_paths"]
 269:     }
 270:     assert "execution_runtime" in forbidden_domains
 271: 
 272: 
 273: def test_dopecon_bridge_is_transport_only_not_domain_authority() -> None:
 274:     bridge = systems_by_name()["dopecon-bridge"]
 275:     assert bridge["authority_status"] == "TRANSPORT_ONLY"
 276:     forbidden_domains = {
 277:         item["forbidden_domain"] for item in bridge["forbidden_authority_paths"]
 278:     }
 279:     assert "pm_workflow_decision_progress_authority" in forbidden_domains
 280: 
 281: 
 282: def run_verifier(*args: str) -> subprocess.CompletedProcess[str]:
 283:     return subprocess.run(
 284:         [sys.executable, str(VERIFIER), *args],
 285:         cwd=REPO_ROOT,
 286:         text=True,
 287:         capture_output=True,
 288:         check=False,
 289:     )
 290: 
 291: 
 292: def test_verifier_produces_stable_output() -> None:
 293:     args = (
 294:         "--manifest",
 295:         "config/runtime_authority_manifest.json",
 296:         "--check",
 297:         "static",
 298:     )
 299:     first = run_verifier(*args)
 300:     second = run_verifier(*args)
 301:     assert first.returncode == 0, first.stdout + first.stderr
 302:     assert second.returncode == 0, second.stdout + second.stderr
 303:     assert first.stdout == second.stdout
 304:     assert "SUMMARY status=passed failures=0" in first.stdout
 305: 
 306: 
 307: def test_verifier_exits_nonzero_for_missing_required_path(tmp_path: Path) -> None:
 308:     manifest = copy.deepcopy(load_manifest())
 309:     by_name = {entry["system"]: entry for entry in manifest["systems"]}
 310:     target_entry = by_name["dopemux"]
 311:     required_path = next(
 312:         (p for p in target_entry["expected_paths"] if p.get("required", True)),
 313:         None,
 314:     )
 315:     assert required_path is not None, "dopemux must have at least one required expected_path"
 316:     required_path["path"] = "missing-required-file.txt"
 317:     temp_manifest = tmp_path / "runtime_authority_manifest.json"
 318:     temp_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
 319: 
 320:     result = run_verifier(
 321:         "--manifest",
 322:         str(temp_manifest),
 323:         "--system",
 324:         "dopemux",
 325:         "--check",
 326:         "static",
 327:     )
 328: 
 329:     assert result.returncode == 1
 330:     assert "missing required expected path missing-required-file.txt" in result.stdout
 331: >>>>>>> 14b60d2db (Restore deterministic runtime authority verifier)
```

## Recent File History
### config/runtime_authority_manifest.json
- 26344de13 review-response: address thread suggestions (pr-merge/20260430_230955/PR-541)
- 31fa4aab6 Add deterministic runtime authority verifier
- 911ac39d9 🎨 Palette: Mitigate time blindness with absolute completion times
- 3a19442ea Add deterministic runtime authority verifier (#547)

### scripts/verify_runtime_authority.py
- dd649024e fix(runtime-authority): harden port validation
- 9df26bbd9 fix(runtime-authority): repair verifier syntax
- 1aff43c14 review-response: address thread suggestions (pr-merge/20260430_230955/PR-540)
- 31fa4aab6 Add deterministic runtime authority verifier
- 911ac39d9 🎨 Palette: Mitigate time blindness with absolute completion times

### tests/unit/test_runtime_authority_manifest.py
- 31fa4aab6 Add deterministic runtime authority verifier
- 911ac39d9 🎨 Palette: Mitigate time blindness with absolute completion times
- 3a19442ea Add deterministic runtime authority verifier (#547)

## Resolution Decision
- status: escalated
- reason: strict conflict mode requires explicit semantic resolution evidence.
