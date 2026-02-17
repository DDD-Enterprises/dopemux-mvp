# Quick Start: Run Priority Extraction

This guide shows you how to run the priority extraction phases (I, W, H) immediately.

---

## Prerequisites

- Gemini Flash 2.0 API access
- Working directory: `/Users/hue/code/dopemux-mvp`
- Output directory: `./extraction/`

---

## Step 1: Prepare Output Directories

```bash
cd /Users/hue/code/dopemux-mvp
mkdir -p extraction/{i1,i2,i3,w1,w2,w3,h}
```

---

## Step 2: Run Executable Prompts in Order

### I1: Index Instruction Files (3-5 min)

```bash
# Copy the entire EXEC_I1_INSTRUCTION_INDEX.md file
# Paste into Gemini Flash 2.0 interface
# Or run via API:
gemini-flash run UPGRADE/EXEC_I1_INSTRUCTION_INDEX.md > extraction/i1/LLM_INSTRUCTION_INDEX.json
```

**Output:** `extraction/i1/LLM_INSTRUCTION_INDEX.json`

**Expected:** ~50-80 instruction files indexed

---

### I2: Extract Tooling References (3-5 min)

**First, provide the I1 output to the prompt:**

```bash
# Method 1: API
gemini-flash run UPGRADE/EXEC_I2_TOOLING_REFERENCES.md \
  --input extraction/i1/LLM_INSTRUCTION_INDEX.json \
  --output-dir extraction/i2/

# Method 2: Manual
# 1. Open EXEC_I2_TOOLING_REFERENCES.md
# 2. Append the contents of extraction/i1/LLM_INSTRUCTION_INDEX.json to the prompt
# 3. Paste into Gemini Flash
# 4. Save outputs to extraction/i2/
```

**Outputs:**
- `extraction/i2/LLM_TOOLING_REFERENCES.json`
- `extraction/i2/LLM_SERVER_CALL_SURFACE.json`

---

### W1: Extract Ops Workflows (5-7 min)

```bash
gemini-flash run UPGRADE/EXEC_W1_OPS_WORKFLOWS.md > extraction/w1/WORKFLOW_SURFACE_OPS.json
```

**Output:** `extraction/w1/WORKFLOW_SURFACE_OPS.json`

**Expected:** ~20-40 workflow items (compose services, scripts, tasks)

---

### H: Home Config Pass (2-3 min)

**⚠️ IMPORTANT: This scans your home directory. Review redaction rules first.**

```bash
gemini-flash run UPGRADE/EXEC_H_HOME_CONFIG.md --output-dir extraction/h/
```

**Outputs:**
- `extraction/h/HOME_CONFIG_INVENTORY.json`
- `extraction/h/HOME_CONFIG_KEYS.json`
- `extraction/h/HOME_CONFIG_MCP_REFERENCES.json`
- `extraction/h/HOME_CONFIG_DIFF_HINTS.json`

**Safety:** All secrets are automatically redacted. Only structure and server names extracted.

---

## Step 3: Verify Outputs

```bash
# Check file sizes (should all be >100 bytes)
ls -lh extraction/*/*.json

# Count instruction files
jq '.instruction_files | length' extraction/i1/LLM_INSTRUCTION_INDEX.json

# Count MCP references
jq '.refs | length' extraction/i2/LLM_TOOLING_REFERENCES.json

# Count workflows
jq '.workflows | length' extraction/w1/WORKFLOW_SURFACE_OPS.json

# Check for drift
jq '.comparisons[] | select(.drift_detected == true)' extraction/h/HOME_CONFIG_DIFF_HINTS.json
```

---

## What You'll Discover

After running these 4 prompts, you'll have:

✅ **Complete control plane map** - all instruction files, MCP servers, tools  
✅ **Operational workflows** - how services actually start and connect  
✅ **Home config truth** - runtime configs that make it work locally  
✅ **Drift detection** - where home and repo configs diverge

---

## Next Steps

### Option A: Continue with Code Extraction (Prompts A-F)

Run the existing code extraction prompts to get CLI, API, DB, events surfaces.

### Option B: Jump to Docs Extraction (Phases D0-CL)

Run the phased doc extraction to get claims, boundaries, workflows from docs.

### Option C: Quick Analysis

Feed the priority outputs to GPT-5.2:

```
Here are the instruction plane, workflow, and home config extractions from dopemux-mvp.

Produce:
1. INSTRUCTION_PLANE_TRUTH_MAP.md - what's the real control plane?
2. MCP_SERVER_CANONICAL_LIST.json - which servers are actually used?
3. PORTABILITY_RISKS.md - what breaks when you deploy elsewhere?

[Attach all JSON files from extraction/i1/, i2/, w1/, h/]
```

---

## Troubleshooting

### "Permission denied" on home directory

If scanning `~/.dopemux` fails:
- Check file permissions
- Run with appropriate access
- Or skip H phase and manually review configs

### Large output files

If JSON files are >10MB:
- Expected for large repos
- Consider splitting extraction by subdirectory
- Use `jq` to filter/analyze outputs

### Missing references

If fewer MCP servers found than expected:
- Check that instruction files are in scope
- Verify `.claude/` and `.dopemux/` are readable
- Review I1 output to see what files were indexed

---

## Estimated Time

**Total for priority phases:** ~15-20 minutes

This gives you the "real wiring" of dopemux before diving into code/docs extraction.
