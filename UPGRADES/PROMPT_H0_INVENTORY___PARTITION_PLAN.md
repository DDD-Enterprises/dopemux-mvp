Goal: HOME_INVENTORY.json, HOME_PARTITIONS.json

Prompt:
- INPUT dirs:
  - ~/.dopemux/**
  - ~/.config/dopemux/**
  - ~/.config/taskx/**
  - ~/.config/litellm/**
  - ~/.config/mcp/**
- Output inventory + partitions:
  - home router/provider ladders
  - home mcp configs
  - home litellm configs
  - profiles/sessions/tmux helpers
  - sqlite metadata files (ONLY metadata, not dumping private content)