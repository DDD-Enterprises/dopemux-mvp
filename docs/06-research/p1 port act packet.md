---
id: p1 port act packet
title: P1 Port Act Packet
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-08'
last_review: '2026-02-08'
next_review: '2026-05-09'
prelude: P1 Port Act Packet (reference) for dopemux documentation and developer workflows.
---
```text
# Terminal B: port discovery
COMMAND     PID USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
bun       33098  hue    6u  IPv4 0xb864b46c2612622e      0t0  TCP localhost:37777 (LISTEN)
node      72143  hue   14u  IPv4 0xbab19cbdef14b5e2      0t0  TCP localhost:vat (LISTEN)
0
PORT=37777
```

```text
# Worker startup logs (from /Users/hue/.claude-mem/logs/claude-mem-2026-02-06.log)
[2026-02-06 10:01:31.316] [INFO ] [SYSTEM] Starting worker daemon
[2026-02-06 10:01:31.436] [INFO ] [SYSTEM] HTTP server started {host=127.0.0.1, port=37777, pid=33098}
[2026-02-06 10:01:31.437] [INFO ] [SYSTEM] Worker started {host=127.0.0.1, port=37777, pid=33098}
[2026-02-06 10:01:31.489] [INFO ] [SYSTEM] Mode loaded: code
[2026-02-06 10:01:31.512] [INFO ] [DB    ] Initializing fresh database with migration004
[2026-02-06 10:01:31.515] [INFO ] [DB    ] Migration004 applied successfully
[2026-02-06 10:01:31.521] [INFO ] [DB    ] Creating FTS5 tables
[2026-02-06 10:01:31.521] [INFO ] [DB    ] FTS5 tables created successfully
[2026-02-06 10:01:31.521] [INFO ] [DB    ] Database initialized
[2026-02-06 10:01:31.522] [INFO ] [WORKER] SearchManager initialized and search routes registered
[2026-02-06 10:01:31.582] [INFO ] [SYSTEM] Claude-mem search server started
[2026-02-06 10:01:31.588] [INFO ] [WORKER] ✓ Connected to MCP server
[2026-02-06 10:01:31.588] [INFO ] [SYSTEM] Background initialization complete
[2026-02-06 10:01:31.588] [INFO ] [SYSTEM] Started orphan reaper (runs every 5 minutes)
[2026-02-06 10:01:31.616] [INFO ] [SYSTEM] Worker available {"workerUrl":"http://127.0.0.1:37777"}
[2026-02-06 10:01:31.834] [INFO ] [SYSTEM] Worker started successfully
0
```

```text
# 2A) Quick probe common endpoints
===== GET / =====
HTTP/1.1 200 OK
Vary: Origin
Content-Type: text/html; charset=utf-8
Date: Fri, 06 Feb 2026 18:08:07 GMT
Content-Length: 69201
ETag: W/"10e51-eRtsCRFuhEpep39640hRNn+9Yig"
X-Powered-By: Express

===== GET /health =====
HTTP/1.1 200 OK
Vary: Origin
Content-Type: application/json; charset=utf-8
Date: Fri, 06 Feb 2026 18:08:07 GMT
Content-Length: 41
ETag: W/"29-sQ6OiayrNP66GVrrCusE6CMRNZ0"
X-Powered-By: Express

===== GET /api/health =====
HTTP/1.1 200 OK
Vary: Origin
Content-Type: application/json; charset=utf-8
Date: Fri, 06 Feb 2026 18:08:07 GMT
Content-Length: 144
ETag: W/"90-e8Xc1pWHwVrO96sSjnXqaqWH2YY"
X-Powered-By: Express

===== GET /api =====
HTTP/1.1 404 Not Found
Vary: Origin
Content-Security-Policy: default-src 'none'
X-Content-Type-Options: nosniff
Content-Type: text/html; charset=utf-8
Date: Fri, 06 Feb 2026 18:08:07 GMT
Content-Length: 142
X-Powered-By: Express

===== GET /api/context/inject =====
HTTP/1.1 400 Bad Request
Vary: Origin
Content-Type: application/json; charset=utf-8
Date: Fri, 06 Feb 2026 18:08:07 GMT
Content-Length: 44
ETag: W/"2c-H9gqSxMjrArCW+yBc48hncnk5is"
X-Powered-By: Express

===== GET /api/sessions/init =====
HTTP/1.1 404 Not Found
Vary: Origin
Content-Security-Policy: default-src 'none'
X-Content-Type-Options: nosniff
Content-Type: text/html; charset=utf-8
Date: Fri, 06 Feb 2026 18:08:07 GMT
Content-Length: 156
X-Powered-By: Express

===== GET /api/sessions/summarize =====
HTTP/1.1 404 Not Found
Vary: Origin
Content-Security-Policy: default-src 'none'
X-Content-Type-Options: nosniff
Content-Type: text/html; charset=utf-8
Date: Fri, 06 Feb 2026 18:08:07 GMT
Content-Length: 161
X-Powered-By: Express

===== GET /api/sessions/complete =====
HTTP/1.1 404 Not Found
Vary: Origin
Content-Security-Policy: default-src 'none'
X-Content-Type-Options: nosniff
Content-Type: text/html; charset=utf-8
Date: Fri, 06 Feb 2026 18:08:07 GMT
Content-Length: 160
X-Powered-By: Express

===== GET /api/search =====
HTTP/1.1 500 Internal Server Error
Vary: Origin
Content-Type: application/json; charset=utf-8
Date: Fri, 06 Feb 2026 18:08:07 GMT
Content-Length: 55
ETag: W/"37-D42aLk9un2ev10VSdTkruyxv5aM"
X-Powered-By: Express

0
```

```text
# 2B) docs/openapi/routes probes
===== GET /openapi.json =====
HTTP/1.1 404 Not Found
...
===== GET /docs =====
HTTP/1.1 404 Not Found
...
===== GET /api/docs =====
HTTP/1.1 404 Not Found
...
===== GET /routes =====
HTTP/1.1 404 Not Found
...
===== GET /api/routes =====
HTTP/1.1 404 Not Found
...
0
```

```text
# 3-5 using packet JSON as written (session_id)
{"error":"Missing contentSessionId"}0
{"error":"Missing contentSessionId"}
{"error":"Missing contentSessionId"}0
{"error":"Missing contentSessionId"}
{"error":"Missing contentSessionId"}0
{"error":"Missing contentSessionId"}
{"error":"Missing contentSessionId"}0
{"error":"Missing contentSessionId"}
{"error":"Missing contentSessionId"}0
{"error":"Missing contentSessionId"}
```

```text
# Corrected contract run (contentSessionId + project + internal /sessions/{id}/init)
{"sessionDbId":1,"promptNumber":1,"skipped":false}0
{"sessionDbId":1,"promptNumber":1,"skipped":false}
SESSION_DB_ID=1
PROMPT_NUM=1
{"status":"initialized","sessionDbId":1,"port":37777}0
{"status":"initialized","sessionDbId":1,"port":37777}
{"status":"queued"}0
{"status":"queued"}
{"status":"queued"}0
{"status":"queued"}
{"status":"queued"}0
{"status":"queued"}
0
{"status":"completed","sessionDbId":1}0
{"status":"completed","sessionDbId":1}
```

```text
# /tmp JSON artifacts
===== /tmp/claude_mem_init.json =====
-rw-r--r--@ 1 hue  wheel  50 Feb  6 10:09 /tmp/claude_mem_init.json
{"sessionDbId":1,"promptNumber":1,"skipped":false}

===== /tmp/claude_mem_session_init_internal.json =====
-rw-r--r--@ 1 hue  wheel  53 Feb  6 10:09 /tmp/claude_mem_session_init_internal.json
{"status":"initialized","sessionDbId":1,"port":37777}

===== /tmp/claude_mem_summarize_safe.json =====
-rw-r--r--@ 1 hue  wheel  19 Feb  6 10:09 /tmp/claude_mem_summarize_safe.json
{"status":"queued"}

===== /tmp/claude_mem_summarize_secrets.json =====
-rw-r--r--@ 1 hue  wheel  19 Feb  6 10:09 /tmp/claude_mem_summarize_secrets.json
{"status":"queued"}

===== /tmp/claude_mem_summarize_private.json =====
-rw-r--r--@ 1 hue  wheel  19 Feb  6 10:09 /tmp/claude_mem_summarize_private.json
{"status":"queued"}

===== /tmp/claude_mem_complete.json =====
-rw-r--r--@ 1 hue  wheel  38 Feb  6 10:09 /tmp/claude_mem_complete.json
{"status":"completed","sessionDbId":1}
0
```

```text
# DB path + schema + data
-rw-r--r--@ 1 hue  staff  4096 Feb  6 10:01 /Users/hue/.claude-mem/claude-mem.db

sqlite3 "$DB" ".tables"
observations                   session_summaries_fts_config
observations_fts               session_summaries_fts_data
observations_fts_config        session_summaries_fts_docsize
observations_fts_data          session_summaries_fts_idx
observations_fts_docsize       user_prompts
observations_fts_idx           user_prompts_fts
pending_messages               user_prompts_fts_config
schema_versions                user_prompts_fts_data
sdk_sessions                   user_prompts_fts_docsize
session_summaries              user_prompts_fts_idx
session_summaries_fts

sqlite3 "$DB" "pragma table_info(sdk_sessions);"
0|id|INTEGER|0||1
1|content_session_id|TEXT|1||0
2|memory_session_id|TEXT|0||0
3|project|TEXT|1||0
4|user_prompt|TEXT|0||0
5|started_at|TEXT|1||0
6|started_at_epoch|INTEGER|1||0
7|completed_at|TEXT|0||0
8|completed_at_epoch|INTEGER|0||0
9|status|TEXT|1|'active'|0
10|worker_port|INTEGER|0||0
11|prompt_counter|INTEGER|0|0|0

sqlite3 "$DB" "pragma table_info(observations);"
0|id|INTEGER|0||1
1|memory_session_id|TEXT|1||0
2|project|TEXT|1||0
3|text|TEXT|0||0
4|type|TEXT|1||0
5|title|TEXT|0||0
6|subtitle|TEXT|0||0
7|facts|TEXT|0||0
8|narrative|TEXT|0||0
9|concepts|TEXT|0||0
10|files_read|TEXT|0||0
11|files_modified|TEXT|0||0
12|prompt_number|INTEGER|0||0
13|discovery_tokens|INTEGER|0|0|0
14|created_at|TEXT|1||0
15|created_at_epoch|INTEGER|1||0

sqlite3 "$DB" "pragma table_info(session_summaries);"
0|id|INTEGER|0||1
1|memory_session_id|TEXT|1||0
2|project|TEXT|1||0
3|request|TEXT|0||0
4|investigated|TEXT|0||0
5|learned|TEXT|0||0
6|completed|TEXT|0||0
7|next_steps|TEXT|0||0
8|files_read|TEXT|0||0
9|files_edited|TEXT|0||0
10|notes|TEXT|0||0
11|prompt_number|INTEGER|0||0
12|discovery_tokens|INTEGER|0|0|0
13|created_at|TEXT|1||0
14|created_at_epoch|INTEGER|1||0

sqlite3 "$DB" "select id, memory_session_id, content_session_id, project, user_prompt, started_at, started_at_epoch, completed_at, completed_at_epoch, status, worker_port, prompt_counter from sdk_sessions order by id desc limit 5;"
1|f0451e82-6f38-4802-bc8e-2c6074027c6a|test-session-001|tmp|hello from local probe|2026-02-06T18:09:02.475Z|1770401342475|||active||0

sqlite3 "$DB" "select id, memory_session_id, project, type, title, created_at, created_at_epoch, prompt_number from observations order by id desc limit 20;"
-- no rows --

sqlite3 "$DB" "select id, memory_session_id, project, request, investigated, learned, completed, next_steps, notes, created_at, created_at_epoch from session_summaries order by id desc limit 20;"
-- no rows --
0
```

```text
# 6B secret leakage checks
0
0
0
0
```

```text
# 7 determinism probe
0
```

```text
# Relevant worker log evidence during summarize
[2026-02-06 10:09:03.065] [INFO ] [QUEUE ] [session-1] ENQUEUED | sessionDbId=1 | messageId=1 | type=summarize | depth=1
[2026-02-06 10:09:04.761] [INFO ] [SDK   ] [session-1] ← Response received (59 chars) {promptNumber=1} You're out of extra usage · resets 12pm (America/Vancouver)
[2026-02-06 10:09:04.762] [INFO ] [DB    ] [session-1] STORING | ... | obsCount=0 | hasSummary=false
[2026-02-06 10:09:04.762] [INFO ] [DB    ] [session-1] STORED | ... | summaryId=none
...
[2026-02-06 10:09:12.852] [INFO ] [DB    ] [session-1] STORED | ... | summaryId=none
```
