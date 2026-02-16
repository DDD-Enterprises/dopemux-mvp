# Complete Extraction Pipeline: Priority-First Run Order

**Run this pipeline to extract ALL architectural truth with zero silent loss.**

---

## Pipeline Overview

```
Priority Phases (I, W, H) → Code (A-F) → Docs (D0-CL) → Arbitration (GPT-5.2) → Synthesis (Opus)
```

### Complete Phase List

**Priority Phases (Run First):**
1. **I1-I3** - LLM Instruction Plane (control plane truth)
2. **W1-W3** - Workflow Plane (multi-service orchestration)
3. **H** - Home Config Pass (runtime config truth)

**Code Extraction:**
4. **A-F** - Code surfaces (services, CLI, API, MCP, events, DB, env, risks)

**Documentation Extraction:**
5. **D0** - Inventory & Partition
6. **D1** - Normative Extraction (claims, boundaries per partition)
7. **D2** - Deep Extraction (interfaces, workflows, decisions)
8. **D3** - Citation Graph
9. **M1** - Merge & Normalize
10. **QA** - Coverage Report
11. **CL** - Topic Clustering

---

## Why Priority Phases Come First

The "real wiring" of Dopemux lives in:
- **LLM instruction files** (.claude/, AGENTS.md, .dopemux/) - defines tool availability, routing, guardrails
- **Multi-service workflows** (compose, scripts, instruction sequences) - defines actual system behavior
- **Home configs** (~/.dopemux, ~/.config/dopemux) - runtime enablement, "why it works on your machine"

If you extract code first, you'll miss 60% of the system. ⚡

---

## Phase I: LLM Instruction Plane (3 runs)

**Purpose:** Capture control plane that defines tool/server availability and policies.

### I1: Index Instruction Files
```bash
flash run PROMPT_I1_INSTRUCTION_INDEX.md \
  --output-dir ./extraction/i1/
```

**Outputs:**
- `LLM_INSTRUCTION_INDEX.json`

**Expected:** ~50-80 files (.claude/, .dopemux/, compose, scripts, AGENTS.md)

### I2: Extract Tooling & Server References
```bash
flash run PROMPT_I2_TOOLING_REFERENCES.md \
  --input ./extraction/i1/LLM_INSTRUCTION_INDEX.json \
  --output-dir ./extraction/i2/
```

**Outputs:**
- `LLM_TOOLING_REFERENCES.json`
- `LLM_SERVER_CALL_SURFACE.json`

### I3: Extract Policy Gates
```bash
flash run PROMPT_I3_POLICY_GATES.md \
  --input ./extraction/i1/LLM_INSTRUCTION_INDEX.json \
  --output-dir ./extraction/i3/
```

**Outputs:**
- `LLM_POLICY_GATES.json`

---

## Phase W: Workflow Plane (3 runs)

**Purpose:** Capture multi-service orchestration and runtime flows.

### W1: Ops Workflow Surface
```bash
flash run PROMPT_W1_OPS_WORKFLOW_SURFACE.md \
  --output-dir ./extraction/w1/
```

**Outputs:**
- `WORKFLOW_SURFACE_OPS.json`

**Sources:** compose files, scripts, Makefiles, package.json

### W2: LLM Workflow Cues
```bash
flash run PROMPT_W2_LLM_WORKFLOW_CUES.md \
  --input ./extraction/i1/LLM_INSTRUCTION_INDEX.json \
  --input ./extraction/i2/*.json \
  --output-dir ./extraction/w2/
```

**Outputs:**
- `WORKFLOW_SURFACE_LLM.json`

**Sources:** Instruction file step sequences

### W3: Global Workflow Graph
```bash
flash run PROMPT_W3_WORKFLOW_GRAPH.md \
  --input ./extraction/w1/WORKFLOW_SURFACE_OPS.json \
  --input ./extraction/w2/WORKFLOW_SURFACE_LLM.json \
  --input ./extraction/code/SERVICE_MAP.json \
  --output-dir ./extraction/w3/
```

**Outputs:**
- `WORKFLOW_GRAPH_GLOBAL.json`

**Note:** Requires SERVICE_MAP.json from code extraction. If not available, run without and rerun later.

---

## Phase H: Home Config Pass (1 run)

**Purpose:** Capture runtime config truth from home directory (with redaction).

```bash
flash run PROMPT_H_HOME_CONFIG.md \
  --output-dir ./extraction/h/
```

**Outputs:**
- `HOME_CONFIG_INVENTORY.json`
- `HOME_CONFIG_KEYS.json`
- `HOME_CONFIG_MCP_REFERENCES.json`
- `HOME_CONFIG_DIFF_HINTS.json`

**Scanned paths:**
- `~/.dopemux/**`
- `~/.config/dopemux/**`

**Safety:** All secrets are redacted. Only structure, keys, and server/tool names extracted.

---

## Code Extraction (Prompts A-F)

See original `RUN_ORDER.md` for code extraction sequence.

**Run order:**
1. Prompt A → STRUCTURE_MAP, SERVICE_MAP, ENTRYPOINTS
2. Prompt B → CLI_SURFACE, API_SURFACE, MCP_SURFACE, HOOKS_SURFACE
3. Prompt C → EVENT_EMITTERS, EVENT_CONSUMERS, EVENT_ENVELOPE_FIELDS
4. Prompt D → DB_SURFACE, MIGRATIONS, DAO_SURFACE
5. Prompt E → ENV_VARS, CONFIG_LOADERS, SECRETS_RISK_LOCATIONS
6. Prompt F → DETERMINISM_RISKS

---

## Documentation Extraction (Phases D0-CL)

See `PHASED_PIPELINE_GUIDE.md` for detailed doc extraction steps.

**Summary:**
1. **D0**: Inventory & partition all docs into 17 partitions
2. **D1**: Normative extraction (claims, boundaries) per partition (17 runs)
3. **D2**: Deep extraction (interfaces, workflows) for CAP_NOTICES (~8 runs)
4. **D3**: Citation graph (1 run)
5. **M1**: Merge all partNN.json files (1 run)
6. **QA**: Coverage report with quality gates (1 run)
7. **CL**: Topic clustering with instruction plane boost (1 run)

---

## Estimated Execution Time

| Phase Group         | Runs | Est. Time | Total   |
| ------------------- | ---- | --------- | ------- |
| **I (Instruction)** | 3    | 5 min     | 15 min  |
| **W (Workflow)**    | 3    | 5 min     | 15 min  |
| **H (Home Config)** | 1    | 3 min     | 3 min   |
| **Code (A-F)**      | 6    | 5-8 min   | 40 min  |
| **Docs (D0-CL)**    | ~30  | varies    | 3 hours |

**Total:** ~4-4.5 hours sequential, ~1.5 hours if parallelized

**Priority-first shortcut:** Run I→W→H→A→B→D0 first (~1.5 hours), then decide onremaining doc partitions.

---

## Output Directory Structure

```
extraction/
├── i1/
│   └── LLM_INSTRUCTION_INDEX.json
├── i2/
│   ├── LLM_TOOLING_REFERENCES.json
│   └── LLM_SERVER_CALL_SURFACE.json
├── i3/
│   └── LLM_POLICY_GATES.json
├── w1/
│   └── WORKFLOW_SURFACE_OPS.json
├── w2/
│   └── WORKFLOW_SURFACE_LLM.json
├── w3/
│   └── WORKFLOW_GRAPH_GLOBAL.json
├── h/
│   ├── HOME_CONFIG_INVENTORY.json
│   ├── HOME_CONFIG_KEYS.json
│   ├── HOME_CONFIG_MCP_REFERENCES.json
│   └── HOME_CONFIG_DIFF_HINTS.json
├── code/
│   ├── STRUCTURE_MAP.json
│   ├── SERVICE_MAP.json
│   ├── ... (17 code artifacts)
│   └── DETERMINISM_RISKS.json
└── docs/
    ├── d0/
    ├── d1/
    ├── d2/
    ├── d3/
    ├── merged/
    ├── qa/
    └── clusters/
```

---

## Next Steps: Arbitration & Synthesis

### GPT-5.2 Extended Thinking

Hand ALL extracted artifacts to GPT-5.2 for arbitration:

**Input priority order:**
1. Instruction plane artifacts (highest authority)
2. Workflow graph + surfaces
3. Home config diff hints
4. Doc claims/boundaries/supersession
5. Code extraction artifacts

**Expected outputs:**
- `INSTRUCTION_PLANE_TRUTH_MAP.md`
- `INSTRUCTION_TO_SERVICE_TRACE.md`
- `WORKFLOW_CONSISTENCY_LEDGER.md` (doc vs instruction vs ops vs code)
- `MCP_SERVER_CANONICAL_MAP.json`
- `CONFLICT_RESOLUTION_LOG.md`

### Opus (2 runs)

1. **Architecture synthesis:** Boundary map creation from truth maps + clusters
2. **Migration impact:** TaskX integration + MCP→hooks migration plan

---

## Critical Success Factors

✅ **Run I/W/H first** - captures "magic" that makes the system work  
✅ **Use QA gates** - prevents silent detail loss  
✅ **Instruction plane is authoritative** - when code/docs conflict with instructions, instructions win  
✅ **Home configs reveal portability risks** - drift between home and repo = deployment failure  
✅ **Workflow graph enables impact analysis** - know what breaks when you change X
