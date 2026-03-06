# PROMPT D0 — Documentation Inventory & Partition Plan

## Goal
Scan the **{{ repo.name }}** repository for all documentation files and produce a structured inventory with logical partitions for downstream deep-extraction.

## Inputs
Scan the following directories and patterns:

{% for scope in scopes.get('D0', ['docs/**/*.md', 'README*.md', 'INSTALL*.md', 'CHANGELOG*.md', 'CONTRIBUTING*.md', '**/*.rst', 'wiki/**/*']) %}
- `{{ scope }}`
{% endfor %}

Include top-level markdown files (README, INSTALL, CHANGELOG, CONTRIBUTING, LICENSE).
{% if features.get('docs_structured', {}).get('present') %}
This project has a structured documentation directory — enumerate all files within it.
{% endif %}

## Outputs
- `DOCS_INVENTORY.json`
- `DOCS_PARTITIONS.json`

## Schema
```json
{
  "documents": [
    {
      "id": "string (sha256 of path)",
      "path": "string (repo-relative)",
      "title": "string (first heading or filename)",
      "format": "string (markdown|rst|txt|yaml)",
      "word_count": "integer",
      "has_frontmatter": "boolean",
      "category": "string (tutorial|reference|guide|changelog|readme|adr|rfc|other)",
      "evidence": [
        { "path": "string", "line_range": [1, 5], "excerpt": "string ≤200 chars" }
      ]
    }
  ],
  "partitions": [
    {
      "partition_id": "string",
      "description": "string",
      "file_count": "integer",
      "files": ["string"]
    }
  ]
}
```

## Extraction Procedure
1. Walk `docs/` and top-level markdown files.
2. For each file: read first heading as title, count words, detect frontmatter.
3. Categorize by content (tutorial, reference, guide, changelog, ADR, RFC).
4. Group into partitions by directory structure and category.
5. Emit inventory and partition JSON files.

## Evidence Rules
- Every document must carry ≥1 evidence object with its first heading.
- `path` must be repo-relative.
- `excerpt` must be verbatim from the file, ≤200 chars.

## Determinism Rules
- Sort all arrays by `path`.
- Use SHA-256 of repo-relative path as `id`.
- No timestamps in output.

## Anti-Fabrication Rules
- If a file has no heading, use the filename as title.
- If category is ambiguous, use `"other"`.
- Never invent documents that don't exist on disk.

## Failure Modes
- If no documentation files found: emit empty arrays.
- If a file cannot be read: skip with error note.
