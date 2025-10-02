# MetaMCP Setup Guide - Phase 1A
**Goal:** Configure 2 working modes (QUICKFIX + ACT) in 20 minutes

## Step 1: Access MetaMCP Web UI
Open in browser: **http://localhost:12008**

---

## Step 2: Add MCP Servers (4 servers)

Click **"MCP Servers"** → **"Add Server"** for each:

### Server 1: conport
- **Name:** `conport`
- **Type:** `STDIO`
- **Command:** `curl`
- **Args:**
  ```
  -X
  POST
  http://localhost:3004/mcp
  -H
  Content-Type: application/json
  -d
  @-
  ```
- **Environment Variables:** (leave empty)
- Click **Save**

### Server 2: context7
- **Name:** `context7`
- **Type:** `STDIO`
- **Command:** `curl`
- **Args:**
  ```
  -X
  POST
  http://localhost:3002/mcp
  -H
  Content-Type: application/json
  -d
  @-
  ```
- **Environment Variables:** (leave empty)
- Click **Save**

### Server 3: zen
- **Name:** `zen`
- **Type:** `STDIO`
- **Command:** `curl`
- **Args:**
  ```
  -X
  POST
  http://localhost:3003/mcp
  -H
  Content-Type: application/json
  -d
  @-
  ```
- **Environment Variables:** (leave empty)
- Click **Save**

### Server 4: serena
- **Name:** `serena`
- **Type:** `STDIO`
- **Command:** `curl`
- **Args:**
  ```
  -X
  POST
  http://localhost:3006/mcp
  -H
  Content-Type: application/json
  -d
  @-
  ```
- **Environment Variables:** (leave empty)
- Click **Save**

---

## Step 3: Create Namespaces (3 namespaces)

Click **"Namespaces"** → **"Create Namespace"**

### Namespace 1: dopemux-quickfix
- **Name:** `dopemux-quickfix`
- **Description:** `ADHD-optimized quick wins mode (3 tools, minimal cognitive load)`
- **Select Servers:**
  - ☑ conport
  - ☑ serena
  - ☑ context7
- **Middleware:** (none for now)
- Click **Save**

### Namespace 2: dopemux-act
- **Name:** `dopemux-act`
- **Description:** `Implementation mode with code navigation and debugging (4 tools)`
- **Select Servers:**
  - ☑ conport
  - ☑ serena
  - ☑ context7
  - ☑ zen
- **Middleware:** (none for now)
- Click **Save**

### Namespace 3: dopemux-all
- **Name:** `dopemux-all`
- **Description:** `All available tools mode - full flexibility (4 tools in Phase 1A)`
- **Select Servers:**
  - ☑ conport
  - ☑ serena
  - ☑ context7
  - ☑ zen
- **Middleware:** (none for now)
- Click **Save**

---

## Step 4: Create Endpoints (3 endpoints)

Click **"Endpoints"** → **"Create Endpoint"**

### Endpoint 1: quickfix-endpoint
- **Endpoint ID:** `quickfix-endpoint`
- **Namespace:** Select `dopemux-quickfix`
- **Transport:** `SSE` (Server-Sent Events)
- **Authentication:** `API Key`
- **Generate API Key** → Click button and **SAVE THE KEY SECURELY**
- Click **Save Endpoint**

**COPY THIS API KEY!** You'll need it for Claude config:
```
QUICKFIX_API_KEY: <paste-here>
```

### Endpoint 2: act-endpoint
- **Endpoint ID:** `act-endpoint`
- **Namespace:** Select `dopemux-act`
- **Transport:** `SSE`
- **Authentication:** `API Key`
- **Generate API Key** → Click button and **SAVE THE KEY SECURELY**
- Click **Save Endpoint**

**COPY THIS API KEY!** You'll need it for Claude config:
```
ACT_API_KEY: <paste-here>
```

### Endpoint 3: all-endpoint
- **Endpoint ID:** `all-endpoint`
- **Namespace:** Select `dopemux-all`
- **Transport:** `SSE`
- **Authentication:** `API Key`
- **Generate API Key** → Click button and **SAVE THE KEY SECURELY**
- Click **Save Endpoint**

**COPY THIS API KEY!** You'll need it for Claude config:
```
ALL_API_KEY: <paste-here>
```

---

## Step 5: Test Endpoints

In MetaMCP UI:
1. Click **"Inspector"**
2. Select `quickfix-endpoint`
3. Click **"Connect"**
4. Verify you see 3 tools: conport tools, serena tools, context7 tools
5. Repeat for `act-endpoint` (should see 4 servers' tools)
6. Repeat for `all-endpoint` (should see 4 servers' tools - same as act for Phase 1A)

---

## Step 6: Enable Idle Server Initialization

Click **"Settings"** → **"Advanced"**
- ☑ Enable idle server initialization
- This pre-warms servers for faster response

Click **Save Settings**

---

## Next Steps

Once you've completed this:
1. Save your 3 API keys securely:
   - QUICKFIX_API_KEY
   - ACT_API_KEY
   - ALL_API_KEY
2. Update the config files with your keys (see ROLE_SWITCHING_QUICKSTART.md)
3. Test role switching with: ~/.claude/switch-role.sh
4. Start using your optimized modes!

**Time estimate:** 15-20 minutes for first-time setup
