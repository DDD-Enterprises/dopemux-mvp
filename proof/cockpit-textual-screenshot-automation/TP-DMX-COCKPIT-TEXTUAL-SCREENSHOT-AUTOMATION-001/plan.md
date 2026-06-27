# Cockpit Textual Screenshot Automation Plan

Packet: `TP-DMX-COCKPIT-TEXTUAL-SCREENSHOT-AUTOMATION-001`

## Steps

1. Add Task Packet and index row.
   - Verify: `python -m jsonschema -i task-packets/generated/TP-DMX-COCKPIT-TEXTUAL-SCREENSHOT-AUTOMATION-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`

2. Add focused test first.
   - Verify red: `PYTHONPATH=src python -m pytest tests/unit/dopemux/ui/cockpit/test_textual_screenshot_automation.py -q`

3. Implement proof generator.
   - File: `scripts/cockpit_textual_screenshot_automation.py`
   - Verify green: `PYTHONPATH=src python -m pytest tests/unit/dopemux/ui/cockpit/test_textual_screenshot_automation.py -q`

4. Generate proof artifacts.
   - Directory: `proof/cockpit-textual-screenshot-automation/TP-DMX-COCKPIT-TEXTUAL-SCREENSHOT-AUTOMATION-001/`
   - Verify: `PYTHONPATH=src python scripts/cockpit_textual_screenshot_automation.py --output proof/cockpit-textual-screenshot-automation/TP-DMX-COCKPIT-TEXTUAL-SCREENSHOT-AUTOMATION-001`
   - Verify: `python -m json.tool proof/cockpit-textual-screenshot-automation/TP-DMX-COCKPIT-TEXTUAL-SCREENSHOT-AUTOMATION-001/TEXTUAL_SCREENSHOT_AUTOMATION_REPORT.json >/dev/null`

5. Record independent audit outcomes.
   - File: `proof/cockpit-textual-screenshot-automation/TP-DMX-COCKPIT-TEXTUAL-SCREENSHOT-AUTOMATION-001/INDEPENDENT_AUDITS.md`
   - Verify: audit artifact records `PASS`, `FAIL`, or `NOT_RUN` for Claude Code, Grok Build, and agy.

6. Run bounded validation and precommit.
   - Verify: packet schema, focused and broader Cockpit tests, compileall, `git diff --check`, scoped pre-commit.

## Rollback

Revert the allowlisted packet files only. No runtime state, PM data, service data, uploaded PNG references, or live integration state should be mutated by this packet.
