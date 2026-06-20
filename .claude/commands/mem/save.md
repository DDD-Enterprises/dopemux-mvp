# mem/save (deprecated — use ConPort)

Store durable context via **ConPort** `log_custom_data` (Memory Trinity plane 1).

**Args**: `$ARGUMENTS` = `<TITLE> :: <TEXT>`

**Steps**
1) `mcp__conport__log_custom_data` with `category: "mem"`, `key: <TITLE>`, `value: {text, tags}`.
2) Return entry key and one-liner summary.

For session checkpoints use `/save` (Dopemux `.dopemux/context.db`), not this command.