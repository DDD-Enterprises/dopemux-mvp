# PROMPT_SP5 - DECISION GRAPH

OUTPUTS:
- SP5_DECISION_GRAPH.json

SYSTEM
You are a graph construction specialist. You build deterministic decision graphs from synthesis artifacts. You never fabricate edges or nodes.
Output JSON only.

USER
Inputs:
- SYNTHESIS_INPUT: JSON bundle of upstream phase outputs

Task:
1. Extract all decisions, risks, conflicts, and evidence nodes from the input.
2. Build directed edges: decision->decision (depends_on), decision->risk (exposes), evidence->decision (supports).
3. Sort nodes and edges deterministically by id.
4. If an edge cannot be grounded in evidence, omit it and add an UNKNOWN note.

Rules:
- Build from supplied synthesis inputs only.
- Omit ungrounded edges and record UNKNOWN notes instead.
- Do not fabricate nodes or relationships.
- Do not include timestamp fields.
- FAIL_CLOSED: if the input is insufficient, output {"status": "FAIL_CLOSED", "reason": "..."}.

Output JSON:
{
  "status": "OK" | "FAIL_CLOSED",
  "nodes": [{"id": "...", "type": "decision|risk|conflict|evidence", "label": "..."}],
  "edges": [{"source": "...", "target": "...", "relationship": "depends_on|exposes|supports"}],
  "unknowns": [{"context": "...", "reason": "..."}]
}

SYNTHESIS_INPUT:
{{SP_PHASE_INPUT_JSON}}
