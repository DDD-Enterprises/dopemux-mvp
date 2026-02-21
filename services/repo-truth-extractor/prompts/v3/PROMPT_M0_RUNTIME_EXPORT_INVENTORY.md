Goal: M0_RUNTIME_EXPORT_INVENTORY.json

Prompt:
- Task: detect runtime stores and config surfaces only within allowlisted home roots:
  - ~/.dopemux/**
  - ~/.config/dopemux/**
  - ~/.config/taskx/**
  - ~/.config/litellm/**
  - ~/.config/mcp/**
- Identify likely state stores: *.sqlite, *.sqlite3, *.db, context.db, global_index.sqlite.
- Output fields must include for each path:
  - path, size, mtime, classification (sqlite_db|config|cache|unknown), exportability (ok|permission_denied|missing_tool|unsafe).
- Hard rules:
  - No full file content dumps.
  - If caps are hit, emit TRUNCATED marker and counts.
  - Do not include secrets, tokens, or raw message content.
