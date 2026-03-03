# Dopemux GitHub Specialist

A cheap-model-friendly specialist for repo chores (PR hygiene, CI failure summaries, release notes).

## Architecture

1.  **Deterministic Engine:** Rule-based logic for safety, redaction, and artifact generation.
2.  **Gemini Adapter:** Uses Gemini CLI to extract structured data from raw inputs (logs, diffs).
3.  **Trinity Compliance:** Every run generates a proof bundle under `proof/github_specialist/<run_id>/`.

## Features

- **CI Failure Summarizer:** Extract failing jobs/steps and suggest next actions from logs.
- **PR Hygiene:** (Planned) Check for missing tests/docs in PRs.
- **Release Notes:** (Planned) Draft release notes from commits.

## Usage

### Run with a local input bundle

```bash
dopemux-github run --input examples/github_specialist/ci_bundle.json
```

### Input Bundle Format

```json
{
  "scope": "ci",
  "target": "CI:run/abc123",
  "repo": "dopemux/dopemux-mvp",
  "ci": {
    "job": "tests",
    "step": "pytest",
    "log_excerpt": "..."
  }
}
```

## Proof Artifacts

Under `proof/github_specialist/<run_id>/`:
- `INPUTS.json`: Redacted input.
- `PROMPT.txt`: Exact system prompt.
- `RAW_STDOUT.txt`: Raw model output.
- `REPORT.json`: Validated, deterministic Report.
- `REPORT.md`: Comment-ready Markdown.
