# mem/summarize (deprecated — use ConPort search)

Summarize recent **ConPort** mem/scratch/decision entries for this repo.

**Args**: *(optional)* `$ARGUMENTS` = `<TAG>` filter

**Steps**
1) `mcp__conport__conport_get_custom_data` (categories `mem`, `scratch`) and/or `mcp__conport__conport_get_decisions` with `limit: 20`.
2) Filter by tag if provided; output digest grouped by category with ids for follow-up.

For chronicle recap use `/mem:recap` (dope-memory).
