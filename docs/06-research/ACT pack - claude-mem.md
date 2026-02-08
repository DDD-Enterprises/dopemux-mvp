---
id: ACT pack - claude-mem
title: Act Pack   Claude Mem
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-08'
last_review: '2026-02-08'
next_review: '2026-05-09'
prelude: Act Pack   Claude Mem (reference) for dopemux documentation and developer
  workflows.
---
hue    • 󰎙  󰁔  node -e "console.log('HOME', require('os').homedir())" ; \
node -e "console.log('CLAUDE_CONFIG_DIR', process.env.CLAUDE_CONFIG_DIR || require('path').join(require('os').homedir(), '.claude'))"

[2] 34629
HOME /Users/hue
CLAUDE_CONFIG_DIR /Users/hue/.claude
[1] 34676

 hue claude-mem  main •  via 🥟 v1.3.8     # Clone the repositoryy
git clone https://github.com/thedotmack/claude-mem.git
cd claude-mem

# Install dependencies
npm install

# Build hooks and worker service
npm run build

# Worker service will auto-start on first Claude Code session
# Or manually start with:
npm run worker:start

# Verify worker is running
npm run worker:status
[2] 32337
Cloning into 'claude-mem'...
[2]  + 32337 done       dopemux trigger shell-command --context "{\"command\": \"$1\"}" --async
remote: Enumerating objects: 19017, done.
remote: Counting objects: 100% (964/964), done.
remote: Compressing objects: 100% (533/533), done.
remote: Total 19017 (delta 626), reused 465 (delta 430), pack-reused 18053 (from 3)
Receiving objects: 100% (19017/19017), 72.43 MiB | 1.67 MiB/s, done.
Resolving deltas: 100% (12959/12959), done.
npm warn deprecated glob@11.1.0: Old versions of glob are not supported, and contain widely publicized security vulnerabilities, which have been fixed in the current version. Please update. Support for old versions may be purchased (at exorbitant rates) by contacting i@izs.me

added 556 packages, and audited 557 packages in 11s

178 packages are looking for funding
  run `npm fund` for details

6 low severity vulnerabilities

To address all issues (including breaking changes), run:
  npm audit fix --force

Run `npm audit` for details.

> claude-mem@9.0.17 build
> node scripts/build-hooks.js

🔨 Building claude-mem hooks and worker service...

📌 Version: 9.0.17

📦 Preparing output directories...
✓ Output directories ready

📦 Generating plugin package.json...
✓ plugin/package.json generated

📋 Building React viewer...
Building React viewer...
✓ React viewer built successfully
  - plugin/ui/viewer-bundle.js
  - plugin/ui/viewer.html (from viewer-template.html)
  - plugin/ui/assets/fonts/* (font files)
  - plugin/ui/icon-thick-*.svg (4 icon files)

🔧 Building worker service...
✓ worker-service built (1722.09 KB)

🔧 Building MCP server...
✓ mcp-server built (334.17 KB)

🔧 Building context generator...
✓ context-generator built (69.67 KB)

✅ Worker service, MCP server, and context generator built successfully!
   Output: plugin/scripts/
   - Worker: worker-service.cjs
   - MCP Server: mcp-server.cjs
   - Context Generator: context-generator.cjs

> claude-mem@9.0.17 worker:start
> bun plugin/scripts/worker-service.cjs start

[SETTINGS] Created settings file with defaults: /Users/hue/.claude-mem/settings.json
{"continue":true,"suppressOutput":true,"status":"ready"}

> claude-mem@9.0.17 worker:status
> bun plugin/scripts/worker-service.cjs status

Worker is running
  PID: 33098
  Port: 37777
  Started: 2026-02-06T18:01:31.437Z
[1] 33141


 hue claude-mem  main [ 2 ] •  • 󰎙  󰁔  lsof -iTCP:37777 -sTCP:LISTEN || true
curl -sS http://127.0.0.1:37777/ | head

COMMAND   PID USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
bun     33098  hue    6u  IPv4 0xb864b46c2612622e      0t0  TCP localhost:37777 (LISTEN)
<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>claude-mem viewer</title>
  <link rel="icon" type="image/webp" href="claude-mem-logomark.webp">
  <style>
    @font-face {
[1] 35372

 hue claude-mem  main [ 2 ] •  • 󰎙  󰁔  lsof -iTCP:37777 -sTCP:LISTEN || true
curl -sS http://127.0.0.1:37777/ | head

COMMAND   PID USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
bun     33098  hue    6u  IPv4 0xb864b46c2612622e      0t0  TCP localhost:37777 (LISTEN)
<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>claude-mem viewer</title>
  <link rel="icon" type="image/webp" href="claude-mem-logomark.webp">
  <style>
    @font-face {
[1] 35372

 hue claude-mem  main [ 2 ] •  • 󰎙  󰁔
[1]  + 35372 done       dopemux trigger command-done --async --quiet

 hue claude-mem  main [ 2 ] •  • 󰎙  󰁔  sqlite3 ~/.claude-mem/claude-mem.db ".tables"
sqlite3 ~/.claude-mem/claude-mem.db ".schema sdk_sessions"
sqlite3 ~/.claude-mem/claude-mem.db ".schema observations"
sqlite3 ~/.claude-mem/claude-mem.db ".schema session_summaries"
sqlite3 ~/.claude-mem/claude-mem.db ".schema user_prompts"

[2] 35716
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
CREATE TABLE sdk_sessions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          content_session_id TEXT UNIQUE NOT NULL,
          memory_session_id TEXT UNIQUE,
          project TEXT NOT NULL,
          user_prompt TEXT,
          started_at TEXT NOT NULL,
          started_at_epoch INTEGER NOT NULL,
          completed_at TEXT,
          completed_at_epoch INTEGER,
          status TEXT CHECK(status IN ('active', 'completed', 'failed')) NOT NULL DEFAULT 'active'
        , worker_port INTEGER, prompt_counter INTEGER DEFAULT 0);
CREATE INDEX idx_sdk_sessions_claude_id ON sdk_sessions(content_session_id);
CREATE INDEX idx_sdk_sessions_sdk_id ON sdk_sessions(memory_session_id);
CREATE INDEX idx_sdk_sessions_project ON sdk_sessions(project);
CREATE INDEX idx_sdk_sessions_status ON sdk_sessions(status);
CREATE INDEX idx_sdk_sessions_started ON sdk_sessions(started_at_epoch DESC);
CREATE TABLE IF NOT EXISTS "observations" (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          memory_session_id TEXT NOT NULL,
          project TEXT NOT NULL,
          text TEXT,
          type TEXT NOT NULL CHECK(type IN ('decision', 'bugfix', 'feature', 'refactor', 'discovery', 'change')),
          title TEXT,
          subtitle TEXT,
          facts TEXT,
          narrative TEXT,
          concepts TEXT,
          files_read TEXT,
          files_modified TEXT,
          prompt_number INTEGER,
          discovery_tokens INTEGER DEFAULT 0,
          created_at TEXT NOT NULL,
          created_at_epoch INTEGER NOT NULL,
          FOREIGN KEY(memory_session_id) REFERENCES sdk_sessions(memory_session_id) ON DELETE CASCADE ON UPDATE CASCADE
        );
CREATE INDEX idx_observations_sdk_session ON observations(memory_session_id);
CREATE INDEX idx_observations_project ON observations(project);
CREATE INDEX idx_observations_type ON observations(type);
CREATE INDEX idx_observations_created ON observations(created_at_epoch DESC);
CREATE TRIGGER observations_ai AFTER INSERT ON observations BEGIN
        INSERT INTO observations_fts(rowid, title, subtitle, narrative, text, facts, concepts)
        VALUES (new.id, new.title, new.subtitle, new.narrative, new.text, new.facts, new.concepts);
      END;
CREATE TRIGGER observations_ad AFTER DELETE ON observations BEGIN
        INSERT INTO observations_fts(observations_fts, rowid, title, subtitle, narrative, text, facts, concepts)
        VALUES('delete', old.id, old.title, old.subtitle, old.narrative, old.text, old.facts, old.concepts);
      END;
CREATE TRIGGER observations_au AFTER UPDATE ON observations BEGIN
        INSERT INTO observations_fts(observations_fts, rowid, title, subtitle, narrative, text, facts, concepts)
        VALUES('delete', old.id, old.title, old.subtitle, old.narrative, old.text, old.facts, old.concepts);
        INSERT INTO observations_fts(rowid, title, subtitle, narrative, text, facts, concepts)
        VALUES (new.id, new.title, new.subtitle, new.narrative, new.text, new.facts, new.concepts);
      END;
CREATE TABLE IF NOT EXISTS "session_summaries" (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          memory_session_id TEXT NOT NULL,
          project TEXT NOT NULL,
          request TEXT,
          investigated TEXT,
          learned TEXT,
          completed TEXT,
          next_steps TEXT,
          files_read TEXT,
          files_edited TEXT,
          notes TEXT,
          prompt_number INTEGER,
          discovery_tokens INTEGER DEFAULT 0,
          created_at TEXT NOT NULL,
          created_at_epoch INTEGER NOT NULL,
          FOREIGN KEY(memory_session_id) REFERENCES sdk_sessions(memory_session_id) ON DELETE CASCADE ON UPDATE CASCADE
        );
CREATE INDEX idx_session_summaries_sdk_session ON session_summaries(memory_session_id);
CREATE INDEX idx_session_summaries_project ON session_summaries(project);
CREATE INDEX idx_session_summaries_created ON session_summaries(created_at_epoch DESC);
CREATE TRIGGER session_summaries_ai AFTER INSERT ON session_summaries BEGIN
        INSERT INTO session_summaries_fts(rowid, request, investigated, learned, completed, next_steps, notes)
        VALUES (new.id, new.request, new.investigated, new.learned, new.completed, new.next_steps, new.notes);
      END;
CREATE TRIGGER session_summaries_ad AFTER DELETE ON session_summaries BEGIN
        INSERT INTO session_summaries_fts(session_summaries_fts, rowid, request, investigated, learned, completed, next_steps, notes)
        VALUES('delete', old.id, old.request, old.investigated, old.learned, old.completed, old.next_steps, old.notes);
      END;
CREATE TRIGGER session_summaries_au AFTER UPDATE ON session_summaries BEGIN
        INSERT INTO session_summaries_fts(session_summaries_fts, rowid, request, investigated, learned, completed, next_steps, notes)
        VALUES('delete', old.id, old.request, old.investigated, old.learned, old.completed, old.next_steps, old.notes);
        INSERT INTO session_summaries_fts(rowid, request, investigated, learned, completed, next_steps, notes)
        VALUES (new.id, new.request, new.investigated, new.learned, new.completed, new.next_steps, new.notes);
      END;
CREATE TABLE user_prompts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_session_id TEXT NOT NULL,
        prompt_number INTEGER NOT NULL,
        prompt_text TEXT NOT NULL,
        created_at TEXT NOT NULL,
        created_at_epoch INTEGER NOT NULL,
        FOREIGN KEY(content_session_id) REFERENCES sdk_sessions(content_session_id) ON DELETE CASCADE
      );
CREATE INDEX idx_user_prompts_claude_session ON user_prompts(content_session_id);
CREATE INDEX idx_user_prompts_created ON user_prompts(created_at_epoch DESC);
CREATE INDEX idx_user_prompts_prompt_number ON user_prompts(prompt_number);
CREATE INDEX idx_user_prompts_lookup ON user_prompts(content_session_id, prompt_number);
CREATE TRIGGER user_prompts_ai AFTER INSERT ON user_prompts BEGIN
        INSERT INTO user_prompts_fts(rowid, prompt_text)
        VALUES (new.id, new.prompt_text);
      END;
CREATE TRIGGER user_prompts_ad AFTER DELETE ON user_prompts BEGIN
        INSERT INTO user_prompts_fts(user_prompts_fts, rowid, prompt_text)
        VALUES('delete', old.id, old.prompt_text);
      END;
CREATE TRIGGER user_prompts_au AFTER UPDATE ON user_prompts BEGIN
        INSERT INTO user_prompts_fts(user_prompts_fts, rowid, prompt_text)
        VALUES('delete', old.id, old.prompt_text);
        INSERT INTO user_prompts_fts(rowid, prompt_text)
        VALUES (new.id, new.prompt_text);
      END;
[1] 35746
