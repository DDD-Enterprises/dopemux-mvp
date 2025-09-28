# mem/save
Use **memory_bank** to store durable context for this project.

**Args**: `$ARGUMENTS` = `<TITLE> :: <TEXT>`

**Steps**
1) Create/append an entry under the current repo name, with `<TITLE>` and `<TEXT>`.
2) Return the entry id and a one-liner summary. Offer to tag (e.g., "design", "decision", "todo").

**Tools**: memory_bank only.
