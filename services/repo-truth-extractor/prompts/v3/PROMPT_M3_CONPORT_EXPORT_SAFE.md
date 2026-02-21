Goal: M3_CONPORT_EXPORT_SAFE.json

Prompt:
- Task: produce a safe ConPort runtime export summary using M0/M1/M2 and config references.
- Include:
  - schema summary references
  - table count references
  - config surface references (path + key names only)
  - implementer metadata: implementer="GPT-5.3-Codex", authority="Codex CLI/Desktop"
- Hard rules:
  - Redact all values; keep key names only.
  - Hash stable identifiers as sha256(value)[:12].
  - Never include raw memory/chat/content fields.
