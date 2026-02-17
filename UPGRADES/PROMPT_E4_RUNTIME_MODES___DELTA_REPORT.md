# PROMPT_E4 — Runtime modes + delta report

ROLE: Execution plane extractor.
GOAL: compare runtime modes (dev/prod/smoke/test) and highlight configuration deltas.

OUTPUTS:
  • EXEC_RUNTIME_MODES.json (modes[]: {name, toggles[], changed_services[], changed_env[], changed_ports[]})
  • EXEC_MODE_DELTA_REPORT.json (deltas[]: {from_mode, to_mode, differences[]})

RULES:
  • Report each mode only if referenced in docs/configs.
  • Capture environment/service differences verbatim where possible.
