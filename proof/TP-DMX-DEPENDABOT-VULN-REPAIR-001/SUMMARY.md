# SUMMARY — TP-DMX-DEPENDABOT-VULN-REPAIR-001

Raised security floors across Python and JavaScript dependency graphs to clear
the 86 open Dependabot alerts on default branch (1 critical fastmcp SSRF/path
traversal, plus high/medium/low floors).

Residual: `ecdsa` via `python-jose` has no upstream patch (GHSA-wj6h-64fc-37mp).
`diskcache` was removed from the lock graph by the fastmcp 3.x upgrade.
