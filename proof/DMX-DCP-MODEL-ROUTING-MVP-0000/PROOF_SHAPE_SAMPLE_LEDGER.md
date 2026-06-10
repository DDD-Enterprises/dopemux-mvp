# DMX-DCP-MODEL-ROUTING-MVP-0000 — PROOF_SHAPE_SAMPLE_LEDGER.md

## Proof Bundle Shape Samples (OBSERVED)

### TP-DCP-0001 (task-packets/TP-DCP-0001.json)

**Shape**:
```json
{
  "id": "TP-DCP-0001",
  "project": "dopemux-mvp",
  "target": "...",
  "repo_binding": "...",
  "series": "...",
  "commit": "...",
  "pr": "...",
  "steps": [...]
}
```

**Evidence**: task-packets/TP-DCP-0001.json (OBSERVED)

### TP-DCP-0002 (task-packets/TP-DCP-0002.md)

**Shape**: Markdown with frontmatter (id, title, type, owner, date) + ADHD metadata per docs/03-reference/documentation-standards.md

**Evidence**: task-packets/TP-DCP-0002.md (OBSERVED)

### DCP Schema Samples

**dcp_mutation_class.schema.json**:
- Defines mutation classification taxonomy
- Evidence: schemas/dcp/dcp_mutation_class.schema.json (OBSERVED)

**dcp_red_lane_report.schema.json**:
- Defines red lane reporting structure
- Evidence: schemas/dcp/dcp_red_lane_report.schema.json (OBSERVED)

**dcp_red_lane_taxonomy.schema.json**:
- Defines red lane classification
- Evidence: schemas/dcp/dcp_red_lane_taxonomy.schema.json (OBSERVED)

### Proof Bundle Examples

**cockpit-pm-implementer-processing-pack-2026-04-24.proof.json**:
- 14k LOC proof artifact
- Evidence: proof/cockpit-pm-implementer-processing-pack-2026-04-24.proof.json (OBSERVED)

**rte-prelive-audit-pack-2026-04-23.proof.json**:
- 11k LOC pre-live audit pack
- Evidence: proof/rte-prelive-audit-pack-2026-04-23.proof.json (OBSERVED)

**Total Proof Shapes Sampled**: 8
**Canonical Pattern**: All TP-DCP-* follow dopetask-canonical-spec.json (when present) or manual schema check
**DCP-Specific Shapes**: mutation_class, red_lane_report, red_lane_taxonomy schemas observed
