# Phase H0: Home Control Plane Inventory + Partition Plan

You are running inside the Dopemux extraction pipeline.

Goal:
- Inventory only the HOME control-plane relevant files found in the provided context.
- Produce a deterministic partition plan for subsequent Phase H steps.

Hard rules:
- Do NOT invent paths or contents not present in the provided context.
- If something is commonly expected (~/.config/mcp, ~/.dopemux) but not present in context, record it as MISSING (not guessed).
- Output valid JSON only, no markdown fences.

Inputs:
- The runner provides a set of home-control-plane candidate files (safe mode filtering may already have excluded sensitive areas).

Outputs:
- HOME_INVENTORY.json
- HOME_PARTITIONS.json

HOME_INVENTORY.json format:
{
  "inventory_version": "H0.v1",
  "generated_at": "<iso8601>",
  "root_hint": "<string or empty>",
  "items": [
    {
      "path": "<string>",
      "ext": "<string>",
      "bytes": <int>,
      "mtime_epoch": <int>,
      "category_hint": "<one of: mcp|router|litellm|profiles|tmux|sqlite|shell|other|unknown>",
      "notes": "<string>"
    }
  ],
  "missing_expected_roots": [
    {"path": "<string>", "reason": "<string>"}
  ]
}

HOME_PARTITIONS.json format:
{
  "partition_version": "H0.v1",
  "generated_at": "<iso8601>",
  "max_files_per_partition": <int>,
  "partitions": [
    {
      "partition_id": "H_P0001",
      "focus": "<mcp|router|litellm|profiles|tmux|sqlite|mixed>",
      "paths": ["<path1>", "<path2>"],
      "notes": "<string>"
    }
  ],
  "determinism_notes": [
    "Paths sorted ascending before partitioning",
    "Stable partition_ids"
  ]
}

Partitioning requirements:
- Sort all paths ascending (bytewise).
- Group by category_hint when possible.
- Keep partitions small enough that downstream prompts won’t overflow context windows.
