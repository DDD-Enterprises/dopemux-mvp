npm run build -- ttf-unhinted::IosevkaHueEditorQP📦 Dopemux Task Packets
Deterministic Execution Units · Binding Change Control
════════════════════════════════════════════════════════════
🎯 Purpose
Task Packets are the only authorized mechanism for executing non-trivial changes in Dopemux.
They convert architectural intent into:
Deterministic execution steps
Auditable evidence
Reversible outcomes
If work is not governed by a Task Packet, it is not valid Dopemux work.
────────────────────────────────────────────────────────────
🧠 What a Task Packet Is
A Task Packet is:
A binding execution contract
A single unit of irreversible change
A bridge between design and implementation
A mechanical instruction set, not a discussion
Task Packets are written by the Supervisor role and executed by an Implementer role.
────────────────────────────────────────────────────────────
🧠 What a Task Packet Is NOT
A Task Packet is not:
A design document
An ADR
A roadmap or backlog item
A brainstorming artifact
A suggestion
If ambiguity remains, return to the PRIMER and continue investigation.
Do not encode uncertainty into a Task Packet.
────────────────────────────────────────────────────────────
🧭 Authority & Precedence
Conflict resolution order:
Task Packet
.claude/PROJECT_INSTRUCTIONS.md
.claude/PRIMER.md
ADRs
Other documentation
If a Task Packet conflicts with documentation:
The Task Packet wins
The documentation is updated later if required
────────────────────────────────────────────────────────────
🔁 Relationship to ADRs
ADRs define what must be true.
Task Packets define how to make it true.
Every Task Packet must be traceable to:
An ADR
Or an explicit Supervisor decision with justification
Task Packets do not invent architecture.
────────────────────────────────────────────────────────────
🧭 When to Create a Task Packet
Create a Task Packet when:
A design decision has been frozen
Invariants are known
The change is irreversible or stateful
Tests or migrations are required
Multiple files or systems are affected
Failure would create silent corruption or drift
Do not create Task Packets for:
Exploratory investigation
Open-ended refactors
Unscoped cleanups
────────────────────────────────────────────────────────────
🧩 Required Structure
Every Task Packet MUST include:
Objective
Scope (IN / OUT)
Invariants (must remain true)
Plan (numbered, mechanical)
Files to touch
Exact commands to run
Output capture rules (verbatim)
Acceptance criteria
Rollback steps
Stop conditions
If any section is missing, the packet is invalid.
────────────────────────────────────────────────────────────
🧪 Determinism Requirements
Task Packets must:
Prefer minimal diffs
Avoid refactors unless explicitly authorized
Fail closed on ambiguity or safety risk
Produce reproducible results
Capture command outputs verbatim
Return exit codes explicitly
If execution deviates from the packet:
Stop
Report
Do not improvise
────────────────────────────────────────────────────────────
🗂 Recommended Naming Convention
Use deterministic, sortable filenames:
PACKET_<id>_<subsystem>_<short-description>.md
Examples:
PACKET_031_memory_dual_capture_adapter.md
PACKET_044_pm_task_identity_normalization.md
PACKET_052_search_ranking_determinism.md
Packet IDs should be monotonically increasing per subsystem when possible.
────────────────────────────────────────────────────────────
🧷 Packet Storage Rules
Store Task Packets in this directory
Do not overwrite executed packets
Amend via a new packet if changes are required
Reference related ADRs and DESIGN_DELTA documents explicitly
────────────────────────────────────────────────────────────
🧭 Execution Lifecycle
Packet authored by Supervisor
Packet reviewed for completeness
Packet executed by Implementer
Evidence returned verbatim
Supervisor audits results
Risks / decisions updated
Next packet issued or execution halted
No step may be skipped.
────────────────────────────────────────────────────────────
🛑 Stop Conditions Are Mandatory
Every Task Packet must define explicit stop conditions.
Examples:
Required file not found
Unexpected file must be touched
Test failure outside packet scope
Command output diverges from expectation
Ambiguity in invariant enforcement
If a stop condition triggers:
Stop immediately
Return evidence
Await instruction
────────────────────────────────────────────────────────────
🧨 Final Rule
If a change cannot be expressed as a Task Packet,
it is not ready to be made.