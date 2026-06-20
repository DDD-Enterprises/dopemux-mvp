# mem/summarize (deprecated — use ConPort search)

Summarize recent **ConPort** mem/scratch/decision entries for this repo.

**Args**: *(optional)* `$ARGUMENTS` = `<TAG>` filter

**Steps**
1) `search_custom_data_value_fts` and/or `get_decisions` with `limit: 20`.
2) Filter by tag if provided; output digest grouped by category with ids for follow-up.

For chronicle recap use dope-memory tools when exposed via `/mem:recap` (planned).