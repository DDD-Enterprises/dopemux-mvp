# /doc:new
Create a new documentation file with correct path, naming, and YAML front-matter.

**Usage examples**
- `/doc:new how-to add-oauth-step-up "How to add OAuth step-up"`
- `/doc:new reference auth-api "Auth API Reference"`
- `/doc:new runbook api-latency-spike "Runbook — API latency spike"`

**What you do**
1) Parse: `/doc:new <type> <slug> "<Title>"` where `<type>` ∈ tutorial|how-to|reference|explanation|runbook|rfc.
2) Compute target path:
   - tutorial → docs/01-tutorials/{slug or "tutorial-" + slug}.md
   - how-to   → docs/02-how-to/how-to-{slug}.md
   - reference→ docs/03-reference/{slug}.md
   - explanation → docs/04-explanation/{slug}.md
   - runbook  → docs/92-runbooks/runbook-{slug}.md
   - rfc      → docs/91-rfc/rfc-<auto-number>-{slug}.md (if you cannot number, use `rfc-{slug}.md` and warn)
3) Write a new file with YAML front-matter:
   id: <slug>
   title: <Title>
   type: <type>
   owner: @hu3mann
   last_review: today
   next_review: +90d
4) If a Model Context Protocol file-write tool is available (e.g., Desktop Commander), CREATE the file at the computed path. Otherwise, return the full Markdown for manual copy.
5) After creating, list the relative path and remind me to run: `pre-commit run -a` and `python scripts/docs_manifest.py`.

**Notes**
- Never duplicate an existing file; if exists, propose updating it instead.
- Link the new file to any relevant Feature Hub using `feature_id:` in the YAML.
