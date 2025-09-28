Docs Audit CLI
================

Purpose
- Inventory all docs across `docs/` and historical folders.
- Detect exact and near-duplicate documents.
- Ensure every doc has frontmatter.
- Propose descriptive, date-in-title filenames.

Outputs
- `reports/docs-audit/inventory.json` and `inventory.csv`: all scanned docs with metadata.
- `reports/docs-audit/duplicates_groups.json` and `duplicates_pairs.csv`: duplicate clusters and pairwise sims.
- `reports/docs-audit/report.md`: human-readable summary.
- `reports/docs-audit/rename_plan.csv`: proposed renames (dry-run).
- `reports/docs-audit/frontmatter_*.csv`: records of frontmatter insertions (dry-run or applied).

Quickstart
1) Scan main and historical roots
   python scripts/docs_audit/audit_docs.py scan --roots docs CCDOCS CHECKPOINT archive --out reports/docs-audit

2) Generate summary report
   python scripts/docs_audit/audit_docs.py report --out reports/docs-audit

3) Propose date-in-title renames (dry-run)
   python scripts/docs_audit/audit_docs.py plan-rename --out reports/docs-audit --template "{date} - {title}.md"
   # Review reports/docs-audit/rename_plan.csv

4) Enforce minimal frontmatter (dry-run by default)
   python scripts/docs_audit/audit_docs.py enforce-frontmatter --out reports/docs-audit
   # When ready to apply:
   python scripts/docs_audit/audit_docs.py enforce-frontmatter --out reports/docs-audit --apply

5) Apply selected renames (optional)
   python scripts/docs_audit/audit_docs.py apply-rename --plan reports/docs-audit/rename_plan.csv

Notes
- Near-duplicate detection uses 5-word shingles + Jaccard (default threshold 0.82).
- File changes are only made when using --apply flags or the apply-rename command.
- Dates are taken from frontmatter if present; otherwise inferred from the first Git commit (fallback to mtime).

