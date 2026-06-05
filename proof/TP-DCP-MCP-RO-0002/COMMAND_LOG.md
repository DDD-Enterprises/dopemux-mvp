+ pwd
/Users/hue/code/dopemux-mvp/.worktrees/chatgpt-mcp-ro-0002
+ git rev-parse --show-toplevel
/Users/hue/code/dopemux-mvp/.worktrees/chatgpt-mcp-ro-0002
+ git remote -v
mvp	https://github.com/DDD-Enterprises/dopemux-mvp.git (fetch)
mvp	https://github.com/DDD-Enterprises/dopemux-mvp.git (push)
origin	https://github.com/DDD-Enterprises/dopemux-mvp.git (fetch)
origin	https://github.com/DDD-Enterprises/dopemux-mvp.git (push)
+ git branch --show-current
dcp/chatgpt-mcp-ro-0002-architecture-doc-and-multi-proje
+ git rev-parse HEAD
62d16375119c8c7fac2fc3280152c4095c5898ac
+ git status --short --branch
## dcp/chatgpt-mcp-ro-0002-architecture-doc-and-multi-proje
 M task-packets/INDEX.md
?? docs/03-reference/dcp/chatgpt-mcp-readonly/
?? run_checks.sh
?? task-packets/dcp/
+ test -d docs/03-reference/dcp/chatgpt-mcp-readonly
+ python -m json.tool docs/03-reference/dcp/chatgpt-mcp-readonly/READ_ONLY_SURFACE_INVENTORY.json
+ rg -n 'dopecon-bridge|search_all|project_id|readonly|read-only|registry|response envelope|Secure MCP Tunnel' docs/03-reference/dcp/chatgpt-mcp-readonly task-packets/dcp/chatgpt-mcp-readonly
docs/03-reference/dcp/chatgpt-mcp-readonly/DECISIONS.md:5:- Enforce strict `project_id` requirements on all non-discovery tools.
docs/03-reference/dcp/chatgpt-mcp-readonly/DECISIONS.md:6:- Implement explicit registry-based exposure.
docs/03-reference/dcp/chatgpt-mcp-readonly/DECISIONS.md:9:- **Global search / `search_all`**: Rejected due to high risk of cross-project context pollution.
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:9:  "objective": "Implement the minimal read-only MCP facade scaffold with project registry, workspace resolver, response envelope, redaction baseline, repo-state tool, proof listing, and proof fetch tools.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:10:  "why_this_packet_exists_now": "This is the first code slice. It keeps to local filesystem/git read-only surfaces before touching service backends. If this fails, we learn cheaply.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:18:    "branch": "dcp/chatgpt-mcp-ro-0004-facade-scaffold-registry-resolve"
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:22:      "Create services/dcp-readonly-facade package.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:23:      "Implement registry schema loader and validator.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:24:      "Implement workspace resolver with project_id-only access.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:25:      "Implement response envelope.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:28:      "Add tests for registry/resolver/path/proof/git tools.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:41:    "All project-scoped tools require project_id.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:50:    "services/dcp-readonly-facade/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:51:    "docs/03-reference/dcp/chatgpt-mcp-readonly/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:57:    "services/dopecon-bridge/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:66:    "Create package skeleton under services/dcp-readonly-facade.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:67:    "Define registry schema and sample redacted fixture registry for tests.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:68:    "Implement registry loader with schema validation and disabled-project rejection.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:70:    "Implement response envelope module.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:86:    "python -m pytest -q services/dcp-readonly-facade/tests",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:87:    "python -m compileall -q services/dcp-readonly-facade",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:88:    "rg -n \"write_text|open\\(.*['\\\"]w|mkdir|unlink|remove|rmtree|POST|PUT|PATCH|DELETE|/route/pm|/kg/|/ddg/|index_workspace|clear_index|transition|memory_correct|subprocess\" services/dcp-readonly-facade || true",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:90:    "git diff -- services/dcp-readonly-facade docs/03-reference/dcp/chatgpt-mcp-readonly proof/TP-DCP-MCP-RO-0004",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:108:    "AUDIT.md challenging filesystem safety, registry validation, and proof freshness.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:116:    "Implementation stays inside services/dcp-readonly-facade."
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:119:    "Delete services/dcp-readonly-facade if this packet is the first implementation and fails.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:147:    "message": "feat(dcp): scaffold readonly mcp facade registry and proof tools",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:149:      "services/dcp-readonly-facade/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:150:      "docs/03-reference/dcp/chatgpt-mcp-readonly/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:154:      "rg -n \"write_text|open\\(.*['\\\"]w|mkdir|unlink|remove|rmtree|POST|PUT|PATCH|DELETE|/route/pm|/kg/|/ddg/|index_workspace|clear_index|transition|memory_correct|subprocess\" services/dcp-readonly-facade || true",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:156:      "git diff -- services/dcp-readonly-facade docs/03-reference/dcp/chatgpt-mcp-readonly proof/TP-DCP-MCP-RO-0004",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:161:    "title": "Scaffold DCP readonly MCP facade with registry and proof tools",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:176:    "lane": "dcp-readonly-facade",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:181:      "readonly",
docs/03-reference/dcp/chatgpt-mcp-readonly/READ_ONLY_SURFACE_INVENTORY.json:50:      "name": "dopecon-bridge",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0008.json:49:    "services/dcp-readonly-facade/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0008.json:50:    "docs/03-reference/dcp/chatgpt-mcp-readonly/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0008.json:55:    "services/dopecon-bridge/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0008.json:59:    "src/** outside services/dcp-readonly-facade if service is not under src",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0008.json:70:    "Add tests denying dopecon-bridge, mutating routes, arbitrary URLs, arbitrary ports, arbitrary backend routes.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0008.json:83:    "python -m pytest -q services/dcp-readonly-facade/tests",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0008.json:84:    "python -m compileall -q services/dcp-readonly-facade",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0008.json:85:    "rg -n \"write_text|open\\(.*['\\\"]w|mkdir|unlink|remove|rmtree|POST|PUT|PATCH|DELETE|/route/pm|/kg/|/ddg/|index_workspace|clear_index|transition|memory_correct|memory_generate_reflection|subprocess|os.system|shell=True\" services/dcp-readonly-facade || true",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0008.json:86:    "rg -n \"OPENAI_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY|sk-|Bearer |TOKEN=|PASSWORD=|SECRET=\" services/dcp-readonly-facade docs/03-reference/dcp/chatgpt-mcp-readonly || true",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0008.json:150:    "message": "test(dcp): harden readonly facade isolation and denylist",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0008.json:152:      "services/dcp-readonly-facade/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0008.json:153:      "docs/03-reference/dcp/chatgpt-mcp-readonly/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0008.json:157:      "rg -n \"OPENAI_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY|sk-|Bearer |TOKEN=|PASSWORD=|SECRET=\" services/dcp-readonly-facade docs/03-reference/dcp/chatgpt-mcp-readonly || true",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0008.json:164:    "title": "Harden DCP readonly facade for cross-project isolation and PR readiness",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0008.json:179:    "lane": "dcp-readonly-facade",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0008.json:184:      "readonly",
docs/03-reference/dcp/chatgpt-mcp-readonly/RESPONSE_ENVELOPE_SCHEMA.md:7:  "project_id": "string",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.md:1:# TP-DCP-MCP-RO-0007 — Secure MCP Tunnel Integration Docs And Manual Validation
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.md:3:Objective: Document local Secure MCP Tunnel integration, redacted sample configs, local-only runtime posture, manual validation, and ChatGPT connector test flow without committing secrets.
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.md:3:Objective: Add project-scoped ConPort and dope-memory read adapters with strict route allowlists, denylist tests, redaction, pagination, and canonical response envelopes.
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.json:3:  "title": "Secure MCP Tunnel Integration Docs And Manual Validation",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.json:9:  "objective": "Document local Secure MCP Tunnel integration, redacted sample configs, local-only runtime posture, manual validation, and ChatGPT connector test flow without committing secrets.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.json:22:      "Add Secure MCP Tunnel local integration guide.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.json:45:    "docs/03-reference/dcp/chatgpt-mcp-readonly/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.json:49:    "services/** except if updating README under services/dcp-readonly-facade is strictly needed",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.json:71:    "python -m pytest -q services/dcp-readonly-facade/tests",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.json:72:    "rg -n \"CONTROL_PLANE_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY|sk-|Bearer |TOKEN=|PASSWORD=|SECRET=|tunnel_[A-Za-z0-9]\" docs/03-reference/dcp/chatgpt-mcp-readonly services/dcp-readonly-facade || true",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.json:74:    "git diff -- docs/03-reference/dcp/chatgpt-mcp-readonly services/dcp-readonly-facade proof/TP-DCP-MCP-RO-0007",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.json:127:      "docs/03-reference/dcp/chatgpt-mcp-readonly/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.json:131:      "rg -n \"CONTROL_PLANE_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY|sk-|Bearer |TOKEN=|PASSWORD=|SECRET=|tunnel_[A-Za-z0-9]\" docs/03-reference/dcp/chatgpt-mcp-readonly services/dcp-readonly-facade || true",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.json:133:      "git diff -- docs/03-reference/dcp/chatgpt-mcp-readonly services/dcp-readonly-facade proof/TP-DCP-MCP-RO-0007",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.json:138:    "title": "Secure MCP Tunnel integration docs for readonly facade",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.json:153:    "lane": "dcp-readonly-facade",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.json:158:      "readonly",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.md:3:Objective: Implement the minimal read-only MCP facade scaffold with project registry, workspace resolver, response envelope, redaction baseline, repo-state tool, proof listing, and proof fetch tools.
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:9:  "objective": "Add project-scoped dope-context and task-orchestrator read adapters while denying indexing, search_all, sync, transitions, PM write routes, and bridge/proxy access.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:25:      "Add tests for denial of search_all, indexing/sync/clear, transitions, PM routes.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:29:      "No search_all in Phase 1.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:39:    "Caller cannot provide backend route or workflow project ID unless registry-bound.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:43:    "services/dcp-readonly-facade/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:44:    "docs/03-reference/dcp/chatgpt-mcp-readonly/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:50:    "services/dopecon-bridge/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:53:    "services/registry.yaml"
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:61:    "Add denied-route tests for search_all/index_workspace/index_docs/clear_index/sync/start_autonomous.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:73:    "python -m pytest -q services/dcp-readonly-facade/tests",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:74:    "python -m compileall -q services/dcp-readonly-facade",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:75:    "rg -n \"search_all|index_workspace|index_docs|clear_index|sync_workspace|sync_docs|start_autonomous|stop_autonomous|transition|/api/pm|/api/workflow/ideas|/api/workflow/epics|promote|/kg/|/ddg/|/route/pm\" services/dcp-readonly-facade || true",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:77:    "git diff -- services/dcp-readonly-facade docs/03-reference/dcp/chatgpt-mcp-readonly proof/TP-DCP-MCP-RO-0006",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:82:    "search_all denied.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:108:    "dope-context requires search_all to produce useful results.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:116:      "Is search_all truly denied?",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:130:    "message": "feat(dcp): add dope-context and task-orchestrator readonly adapters",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:132:      "services/dcp-readonly-facade/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:133:      "docs/03-reference/dcp/chatgpt-mcp-readonly/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:137:      "rg -n \"search_all|index_workspace|index_docs|clear_index|sync_workspace|sync_docs|start_autonomous|stop_autonomous|transition|/api/pm|/api/workflow/ideas|/api/workflow/epics|promote|/kg/|/ddg/|/route/pm\" services/dcp-readonly-facade || true",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:139:      "git diff -- services/dcp-readonly-facade docs/03-reference/dcp/chatgpt-mcp-readonly proof/TP-DCP-MCP-RO-0006",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:144:    "title": "Add dope-context and task-orchestrator read adapters to readonly facade",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:159:    "lane": "dcp-readonly-facade",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:164:      "readonly",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:174:      "search_all denied.",
docs/03-reference/dcp/chatgpt-mcp-readonly/TOOL_CONTRACT.md:4:- `list_projects`: Returns approved projects. No `project_id` required.
docs/03-reference/dcp/chatgpt-mcp-readonly/TOOL_CONTRACT.md:5:- `task_orchestrator_read`: Wraps read tools (`query_items`, etc). Requires `project_id`.
docs/03-reference/dcp/chatgpt-mcp-readonly/TOOL_CONTRACT.md:6:- `conport_read`: Reads structured context. Requires `project_id`.
docs/03-reference/dcp/chatgpt-mcp-readonly/TOOL_CONTRACT.md:7:- `memory_read`: Reads chronicle/memory. Requires `project_id`.
docs/03-reference/dcp/chatgpt-mcp-readonly/TOOL_CONTRACT.md:10:- `dopecon-bridge`: Denied in Phase 1.
docs/03-reference/dcp/chatgpt-mcp-readonly/TOOL_CONTRACT.md:11:- `search_all`: Denied in Phase 1.
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:9:  "objective": "Add project-scoped ConPort and dope-memory read adapters with strict route allowlists, denylist tests, redaction, pagination, and canonical response envelopes.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:44:    "services/dcp-readonly-facade/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:45:    "docs/03-reference/dcp/chatgpt-mcp-readonly/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:49:    "services/dopecon-bridge/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:55:    "services/registry.yaml"
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:58:    "Add adapter route registry definitions for ConPort and dope-memory.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:59:    "Implement read-only HTTP client wrapper with method/route checks.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:62:    "Normalize all outputs to response envelope.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:77:    "python -m pytest -q services/dcp-readonly-facade/tests",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:78:    "python -m compileall -q services/dcp-readonly-facade",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:79:    "rg -n \"POST|PUT|PATCH|DELETE|/kg/|/ddg/|/route/pm|memory_correct|memory_generate_reflection|memory_store|memory_mark_issue|memory_link_resolution|log_decision|upsert|graph.link\" services/dcp-readonly-facade || true",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:81:    "git diff -- services/dcp-readonly-facade docs/03-reference/dcp/chatgpt-mcp-readonly proof/TP-DCP-MCP-RO-0005",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:85:    "ConPort GET decisions/progress/search allowed only through registry-bound service profile.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:136:    "message": "feat(dcp): add conport and dope-memory readonly adapters",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:138:      "services/dcp-readonly-facade/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:139:      "docs/03-reference/dcp/chatgpt-mcp-readonly/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:143:      "rg -n \"POST|PUT|PATCH|DELETE|/kg/|/ddg/|/route/pm|memory_correct|memory_generate_reflection|memory_store|memory_mark_issue|memory_link_resolution|log_decision|upsert|graph.link\" services/dcp-readonly-facade || true",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:145:      "git diff -- services/dcp-readonly-facade docs/03-reference/dcp/chatgpt-mcp-readonly proof/TP-DCP-MCP-RO-0005",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:150:    "title": "Add ConPort and dope-memory read adapters to DCP readonly facade",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:165:    "lane": "dcp-readonly-facade",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:170:      "readonly",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:179:      "ConPort GET decisions/progress/search allowed only through registry-bound service profile.",
docs/03-reference/dcp/chatgpt-mcp-readonly/SECURITY_MODEL.md:3:## 1. Secure MCP Tunnel
docs/03-reference/dcp/chatgpt-mcp-readonly/SECURITY_MODEL.md:10:Sensitive fields (secrets, tokens, PII) are redacted by the facade before inclusion in the response envelope.
docs/03-reference/dcp/chatgpt-mcp-readonly/SECURITY_MODEL.md:13:No mutable operations are permitted. The facade operates entirely in a read-only projection context.
docs/03-reference/dcp/chatgpt-mcp-readonly/ARCHITECTURE.md:4:The read-only MCP evidence facade provides a secure, loopback-only projection of repository truth, execution state, and structured context to ChatGPT via the MCP protocol. It does not possess any write authority.
docs/03-reference/dcp/chatgpt-mcp-readonly/ARCHITECTURE.md:14:- All paths pass through the multi-project registry.
docs/03-reference/dcp/chatgpt-mcp-readonly/ARCHITECTURE.md:18:- `dopecon-bridge` is denied.
docs/03-reference/dcp/chatgpt-mcp-readonly/ARCHITECTURE.md:19:- `search_all` is denied.
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.md:3:Objective: Add project-scoped dope-context and task-orchestrator read adapters while denying indexing, search_all, sync, transitions, PM write routes, and bridge/proxy access.
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:9:  "objective": "Create repo-tracked architecture, registry, tool-contract, response-envelope, security-model, build-series, and decision docs for the multi-project read-only evidence facade.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:10:  "why_this_packet_exists_now": "Implementation should not start until the multi-project trust boundary, registry contract, response envelope, denylist, and packet series are committed. Design docs are the guardrails; without them Codex will freestyle with a flamethrower.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:22:      "Author architecture docs under docs/03-reference/dcp/chatgpt-mcp-readonly/.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:34:      "No changes to ConPort, dope-memory, dope-context, task-orchestrator, dopecon-bridge, dopetask, or repo-truth-extractor runtime files."
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:39:    "Every tool contract requires project_id except list_projects.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:40:    "Project registry is explicit approval; dopemux init is eligibility, not exposure.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:41:    "dopecon-bridge is denied in Phase 1.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:42:    "search_all is denied in Phase 1.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:46:    "docs/03-reference/dcp/chatgpt-mcp-readonly/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:47:    "task-packets/dcp/chatgpt-mcp-readonly/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:56:    "services/registry.yaml",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:63:    "Create MULTI_PROJECT_REGISTRY_CONTRACT.md with registry schema, validation rules, project eligibility vs exposure decision, resolver flow, symlink rules, and capability model.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:69:    "Create packet markdown files for TP-DCP-MCP-RO-0002 through 0008 in task-packets/dcp/chatgpt-mcp-readonly/.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:80:    "test -d docs/03-reference/dcp/chatgpt-mcp-readonly",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:81:    "python -m json.tool docs/03-reference/dcp/chatgpt-mcp-readonly/READ_ONLY_SURFACE_INVENTORY.json >/tmp/readonly_inventory.valid.json",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:82:    "rg -n \"dopecon-bridge|search_all|project_id|readonly|read-only|registry|response envelope|Secure MCP Tunnel\" docs/03-reference/dcp/chatgpt-mcp-readonly task-packets/dcp/chatgpt-mcp-readonly || true",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:83:    "rg -n \"READY|safe|complete\" docs/03-reference/dcp/chatgpt-mcp-readonly task-packets/dcp/chatgpt-mcp-readonly || true",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:85:    "git diff -- docs/03-reference/dcp/chatgpt-mcp-readonly task-packets/dcp/chatgpt-mcp-readonly task-packets/INDEX.md proof/TP-DCP-MCP-RO-0002",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:92:    "Docs include multi-project registry and resolver contract.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:100:    "AUDIT.md challenging authority labels, bridge denial, search_all denial, project registry assumptions, and scope boundaries.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:110:    "Delete docs created under docs/03-reference/dcp/chatgpt-mcp-readonly that were created by this packet.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:111:    "Delete task-packets/dcp/chatgpt-mcp-readonly files created by this packet.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:126:      "Does any doc allow dopecon-bridge in Phase 1?",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:128:      "Does registry design auto-expose initialized workspaces?",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:145:    "message": "docs(dcp): define readonly mcp facade architecture",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:147:      "docs/03-reference/dcp/chatgpt-mcp-readonly/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:148:      "task-packets/dcp/chatgpt-mcp-readonly/**",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:153:      "rg -n \"READY|safe|complete\" docs/03-reference/dcp/chatgpt-mcp-readonly task-packets/dcp/chatgpt-mcp-readonly || true",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:155:      "git diff -- docs/03-reference/dcp/chatgpt-mcp-readonly task-packets/dcp/chatgpt-mcp-readonly task-packets/INDEX.md proof/TP-DCP-MCP-RO-0002",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:160:    "title": "DCP readonly MCP facade architecture and task series",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:175:    "lane": "dcp-readonly-facade",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:180:      "readonly",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:192:      "Docs include multi-project registry and resolver contract.",
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:4:base_dir = "/Users/hue/code/dopemux-mvp/.worktrees/chatgpt-mcp-ro-0002/docs/03-reference/dcp/chatgpt-mcp-readonly"
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:40:            "name": "dopecon-bridge",
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:52:The read-only MCP evidence facade provides a secure, loopback-only projection of repository truth, execution state, and structured context to ChatGPT via the MCP protocol. It does not possess any write authority.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:62:- All paths pass through the multi-project registry.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:66:- `dopecon-bridge` is denied.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:67:- `search_all` is denied.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:73:registry_contract = """# Multi-Project Registry Contract
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:76:The registry tracks projects by a unique `project_id`.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:79:- All incoming requests must supply a valid `project_id` (except `list_projects`).
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:80:- If `project_id` is missing or invalid, the facade rejects the request.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:84:- Explicit approval in the registry configuration is required for exposure via the facade.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:87:- Request `project_id` is passed to the resolver.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:88:- Resolver checks registry and retrieves the canonical path (resolving symlinks).
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:93:    f.write(registry_contract)
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:98:- `list_projects`: Returns approved projects. No `project_id` required.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:99:- `task_orchestrator_read`: Wraps read tools (`query_items`, etc). Requires `project_id`.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:100:- `conport_read`: Reads structured context. Requires `project_id`.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:101:- `memory_read`: Reads chronicle/memory. Requires `project_id`.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:104:- `dopecon-bridge`: Denied in Phase 1.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:105:- `search_all`: Denied in Phase 1.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:121:  "project_id": "string",
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:138:## 1. Secure MCP Tunnel
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:145:Sensitive fields (secrets, tokens, PII) are redacted by the facade before inclusion in the response envelope.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:148:No mutable operations are permitted. The facade operates entirely in a read-only projection context.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:173:- Enforce strict `project_id` requirements on all non-discovery tools.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:174:- Implement explicit registry-based exposure.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:177:- **Global search / `search_all`**: Rejected due to high risk of cross-project context pollution.
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.md:3:Objective: Create repo-tracked architecture, registry, tool-contract, response-envelope, security-model, build-series, and decision docs for the multi-project read-only evidence facade.
docs/03-reference/dcp/chatgpt-mcp-readonly/TASK_ORCHESTRATOR_LOAD.md:14:- Objective: Create repo-tracked architecture, registry, tool-contract, response-envelope, security-model, build-series, and decision docs for the multi-project read-only evidence facade.
docs/03-reference/dcp/chatgpt-mcp-readonly/TASK_ORCHESTRATOR_LOAD.md:24:- Objective: Inspect actual dopemux init/workspace identity behavior and formalize the project registry validation contract without implementing the facade.
docs/03-reference/dcp/chatgpt-mcp-readonly/TASK_ORCHESTRATOR_LOAD.md:25:- Branch: `dcp/chatgpt-mcp-ro-0003-inspect-dopemux-init-registry-co`
docs/03-reference/dcp/chatgpt-mcp-readonly/TASK_ORCHESTRATOR_LOAD.md:34:- Objective: Implement the minimal read-only MCP facade scaffold with project registry, workspace resolver, response envelope, redaction baseline, repo-state tool, proof listing, and proof fetch tools.
docs/03-reference/dcp/chatgpt-mcp-readonly/TASK_ORCHESTRATOR_LOAD.md:35:- Branch: `dcp/chatgpt-mcp-ro-0004-facade-scaffold-registry-resolve`
docs/03-reference/dcp/chatgpt-mcp-readonly/TASK_ORCHESTRATOR_LOAD.md:44:- Objective: Add project-scoped ConPort and dope-memory read adapters with strict route allowlists, denylist tests, redaction, pagination, and canonical response envelopes.
docs/03-reference/dcp/chatgpt-mcp-readonly/TASK_ORCHESTRATOR_LOAD.md:54:- Objective: Add project-scoped dope-context and task-orchestrator read adapters while denying indexing, search_all, sync, transitions, PM write routes, and bridge/proxy access.
docs/03-reference/dcp/chatgpt-mcp-readonly/TASK_ORCHESTRATOR_LOAD.md:57:- Stop if: dope-context requires search_all to produce useful results.
docs/03-reference/dcp/chatgpt-mcp-readonly/TASK_ORCHESTRATOR_LOAD.md:59:### TP-DCP-MCP-RO-0007 — Secure MCP Tunnel Integration Docs And Manual Validation
docs/03-reference/dcp/chatgpt-mcp-readonly/TASK_ORCHESTRATOR_LOAD.md:64:- Objective: Document local Secure MCP Tunnel integration, redacted sample configs, local-only runtime posture, manual validation, and ChatGPT connector test flow without committing secrets.
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.md:3:Objective: Inspect actual dopemux init/workspace identity behavior and formalize the project registry validation contract without implementing the facade.
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:9:  "objective": "Inspect actual dopemux init/workspace identity behavior and formalize the project registry validation contract without implementing the facade.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:18:    "branch": "dcp/chatgpt-mcp-ro-0003-inspect-dopemux-init-registry-co"
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:43:    "docs/03-reference/dcp/chatgpt-mcp-readonly/Dopemux_INIT_REGISTRY_DISCOVERY.md",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:44:    "docs/03-reference/dcp/chatgpt-mcp-readonly/MULTI_PROJECT_REGISTRY_CONTRACT.md",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:48:    "src/** except read-only inspection",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:55:    "Search for dopemux init implementation, workspace validation, marker files, registry config, and project_id usage.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:58:    "Identify whether dopemux already has a project registry or list command.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:59:    "Update registry contract with OBSERVED marker rules or explicit UNKNOWN sections.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:60:    "Document validation algorithm for registry entry verification.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:71:    "rg -n \"dopemux init|def init|@.*init|workspace_id|workspace_root|repo_root|\\.dopemux|project_id|repo_marker|validate.*workspace|resolve.*workspace|projects list|list_projects|registry\" src services docs tests pyproject.toml",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:74:    "git diff -- docs/03-reference/dcp/chatgpt-mcp-readonly proof/TP-DCP-MCP-RO-0003",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:87:    "AUDIT.md challenging init marker findings and project registry assumptions.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:111:      "Does the registry contract fail closed?",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:121:    "message": "docs(dcp): formalize dopemux init registry contract",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:123:      "docs/03-reference/dcp/chatgpt-mcp-readonly/Dopemux_INIT_REGISTRY_DISCOVERY.md",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:124:      "docs/03-reference/dcp/chatgpt-mcp-readonly/MULTI_PROJECT_REGISTRY_CONTRACT.md",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:130:      "git diff -- docs/03-reference/dcp/chatgpt-mcp-readonly proof/TP-DCP-MCP-RO-0003",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:135:    "title": "Dopemux init registry discovery for readonly MCP facade",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:150:    "lane": "dcp-readonly-facade",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:155:      "readonly",
docs/03-reference/dcp/chatgpt-mcp-readonly/MULTI_PROJECT_REGISTRY_CONTRACT.md:4:The registry tracks projects by a unique `project_id`.
docs/03-reference/dcp/chatgpt-mcp-readonly/MULTI_PROJECT_REGISTRY_CONTRACT.md:7:- All incoming requests must supply a valid `project_id` (except `list_projects`).
docs/03-reference/dcp/chatgpt-mcp-readonly/MULTI_PROJECT_REGISTRY_CONTRACT.md:8:- If `project_id` is missing or invalid, the facade rejects the request.
docs/03-reference/dcp/chatgpt-mcp-readonly/MULTI_PROJECT_REGISTRY_CONTRACT.md:12:- Explicit approval in the registry configuration is required for exposure via the facade.
docs/03-reference/dcp/chatgpt-mcp-readonly/MULTI_PROJECT_REGISTRY_CONTRACT.md:15:- Request `project_id` is passed to the resolver.
docs/03-reference/dcp/chatgpt-mcp-readonly/MULTI_PROJECT_REGISTRY_CONTRACT.md:16:- Resolver checks registry and retrieves the canonical path (resolving symlinks).
+ rg -n 'READY|safe|complete' docs/03-reference/dcp/chatgpt-mcp-readonly task-packets/dcp/chatgpt-mcp-readonly
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:6:  "status": "READY",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0004.json:108:    "AUDIT.md challenging filesystem safety, registry validation, and proof freshness.",
docs/03-reference/dcp/chatgpt-mcp-readonly/DECISIONS.md:10:- **Live Writes**: Rejected for Phase 1 to maintain strict safety boundary.
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0008.json:6:  "status": "READY",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0008.json:114:    "Facade is implementation-complete for Phase 1.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0003.json:6:  "status": "READY",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0005.json:6:  "status": "READY",
docs/03-reference/dcp/chatgpt-mcp-readonly/TASK_ORCHESTRATOR_LOAD.md:10:- Status: READY
docs/03-reference/dcp/chatgpt-mcp-readonly/TASK_ORCHESTRATOR_LOAD.md:20:- Status: READY
docs/03-reference/dcp/chatgpt-mcp-readonly/TASK_ORCHESTRATOR_LOAD.md:30:- Status: READY
docs/03-reference/dcp/chatgpt-mcp-readonly/TASK_ORCHESTRATOR_LOAD.md:40:- Status: READY
docs/03-reference/dcp/chatgpt-mcp-readonly/TASK_ORCHESTRATOR_LOAD.md:50:- Status: READY
docs/03-reference/dcp/chatgpt-mcp-readonly/TASK_ORCHESTRATOR_LOAD.md:60:- Status: READY
docs/03-reference/dcp/chatgpt-mcp-readonly/TASK_ORCHESTRATOR_LOAD.md:70:- Status: READY
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:89:- Path is validated against the safe-paths allowlist.
docs/03-reference/dcp/chatgpt-mcp-readonly/generate_docs.py:178:- **Live Writes**: Rejected for Phase 1 to maintain strict safety boundary.
docs/03-reference/dcp/chatgpt-mcp-readonly/MULTI_PROJECT_REGISTRY_CONTRACT.md:17:- Path is validated against the safe-paths allowlist.
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:6:  "status": "READY",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:83:    "rg -n \"READY|safe|complete\" docs/03-reference/dcp/chatgpt-mcp-readonly task-packets/dcp/chatgpt-mcp-readonly || true",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0002.json:153:      "rg -n \"READY|safe|complete\" docs/03-reference/dcp/chatgpt-mcp-readonly task-packets/dcp/chatgpt-mcp-readonly || true",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.json:6:  "status": "READY",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0007.json:88:    "AUDIT.md challenging doc safety and secret leakage.",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:6:  "status": "READY",
task-packets/dcp/chatgpt-mcp-readonly/TP-DCP-MCP-RO-0006.json:10:  "why_this_packet_exists_now": "This completes the Phase-1 service-backed read model after ConPort/dope-memory are proven.",
+ git diff --stat
 task-packets/INDEX.md | 8 +++++++-
 1 file changed, 7 insertions(+), 1 deletion(-)
+ git diff -- docs/03-reference/dcp/chatgpt-mcp-readonly task-packets/dcp/chatgpt-mcp-readonly task-packets/INDEX.md proof/TP-DCP-MCP-RO-0002
diff --git a/task-packets/INDEX.md b/task-packets/INDEX.md
index 53a8573cd..eb975b326 100644
--- a/task-packets/INDEX.md
+++ b/task-packets/INDEX.md
@@ -109,7 +109,13 @@ A packet is superseded by another packet
 | TP-BETA-CLI-01-DECISIONS-REVIEW-001 | CLI Decisions | Repair PR #740 review blockers for decisions CLI subcommands | Active | N/A |
 | TP-DMX-ADHD-INTERACTIVE-PROMPTS-001 | ADHD UX | Wire interactive prompts into launch and profile flows | Active | N/A |
 | TP-DMX-ORCH-AUDIT-FIX-001 | Task Orchestrator | Close DMX-ORCH integration audit gaps | Active | N/A |
-
+| TP-DCP-MCP-RO-0002 | DCP / MCP | Architecture Doc And Multi Project Contract | Active | N/A |
+| TP-DCP-MCP-RO-0003 | DCP / MCP | Formalize MCP Facade Registry And Identity Contract | Active | N/A |
+| TP-DCP-MCP-RO-0004 | DCP / MCP | Facade Scaffold and Project Resolver | Active | N/A |
+| TP-DCP-MCP-RO-0005 | DCP / MCP | ConPort and Memory Adapters | Active | N/A |
+| TP-DCP-MCP-RO-0006 | DCP / MCP | Context and Task Orchestrator Adapters | Active | N/A |
+| TP-DCP-MCP-RO-0007 | DCP / MCP | Secure Tunnel Integration and Validation | Active | N/A |
+| TP-DCP-MCP-RO-0008 | DCP / MCP | Feature Flag Default Off and Series Closeout | Active | N/A |
 ────────────────────────────────────────────────────────────
 🟢 Completed Task Packets
 
+ git status --short --branch
## dcp/chatgpt-mcp-ro-0002-architecture-doc-and-multi-proje
 M task-packets/INDEX.md
?? docs/03-reference/dcp/chatgpt-mcp-readonly/
?? run_checks.sh
?? task-packets/dcp/
