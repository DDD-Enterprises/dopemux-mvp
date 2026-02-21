✅ Dopemux Enforcement Checklist
Process Integrity · Determinism · Audit Safety
════════════════════════════════════════════════════════════
🎯 Purpose
This checklist enforces process discipline in Dopemux.
It is designed to be used:
During reviews
Before merges
As a CI or pre-commit reference
By humans and LLMs alike
Passing this checklist is a prerequisite for shipping non-trivial changes.
────────────────────────────────────────────────────────────
🧠 Task Packet Enforcement
☐ A Task Packet exists for this change
☐ The packet is listed in task_packets/INDEX.md
☐ The packet scope matches the actual diff
☐ No files outside scope were modified
☐ Stop conditions are defined
────────────────────────────────────────────────────────────
🧪 Determinism & Safety
☐ Changes are minimal and scoped
☐ No undocumented side effects introduced
☐ Fail-closed behavior preserved
☐ No implicit injection added
☐ State changes are explicit and auditable
────────────────────────────────────────────────────────────
🧾 Evidence & Testing
☐ Exact commands are documented
☐ Command outputs captured verbatim
☐ Exit codes recorded
☐ Tests added or explicitly waived with justification
☐ CI results reviewed (not assumed)
────────────────────────────────────────────────────────────
🧭 Documentation Integrity
☐ ADR referenced or explicitly waived
☐ PRIMER process followed for investigations
☐ No architectural decisions hidden in Task Packets
☐ Superseded docs clearly marked
────────────────────────────────────────────────────────────
🔍 Review Gate (Supervisor)
☐ Acceptance criteria satisfied
☐ Invariants preserved
☐ Risks assessed and logged
☐ Rollback steps validated
☐ Next action determined (new packet or halt)
────────────────────────────────────────────────────────────
🧨 Final Gate
☐ If any box above is unchecked, this change does not ship.