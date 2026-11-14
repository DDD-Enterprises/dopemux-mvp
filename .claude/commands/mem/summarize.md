# mem/summarize (deprecated — use ConPort search)

Summarize recent **ConPort** mem/scratch/decision entries for this repo.

**Args**: *(optional)* `$ARGUMENTS` = `<TAG>` filter

**Steps**
1) `get_custom_data` (`workspace_id`, `category: "mem"`) and `get_custom_data` (`workspace_id`, `category: "scratch"`), plus `get_decisions` (`workspace_id`, `limit: 20`).
2) Filter by tag if provided; output digest grouped by category with ids for follow-up.

For chronicle recap use dope-memory tools when exposed via `/mem:recap` (planned).