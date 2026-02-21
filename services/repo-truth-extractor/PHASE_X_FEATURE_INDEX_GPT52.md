# Phase X (GPT-5.2): Feature index + contracts catalog (developer gold)

## Purpose
A lot of your repo power is buried in instruction files, configs, and “workflow glue”. This phase builds a contract catalog:
commands
events
schemas
config knobs
instruction file levers
services + ports
workflows and artifacts

## Output artifacts
FEATURE_INDEX.json (developer queryable)
CONTRACT_CATALOG.md (human)
WORKFLOW_CATALOG.md (human)

## Prompt
ROLE: Systems cataloger.
SCOPE: Produce a developer-queryable feature index and contract catalog.
INPUTS: Phase A/H/D/C normalized JSONs + Phase R outputs. No scanning.

OUTPUTS:
1) FEATURE_INDEX.json
   - keys:
     - features[]
     - each feature:
       - id
       - name
       - planes[]
       - implemented_status (implemented|planned|partial|unknown)
       - evidence_refs[]
       - surfaces: {code_paths[], repo_ctrl_paths[], home_ctrl_paths[], doc_paths[]}
       - commands[] (cli/tools/scripts)
       - events[] (producer/consumer/topic)
       - stores[] (sqlite/postgres/tables)
       - configs[] (key paths only)
       - instruction_levers[] (instruction file names/blocks)
       - tests[] (if known)
       - risks[] (from Phase R risk ledger)

2) CONTRACT_CATALOG.md
   - tables: events, schemas, CLI/API surfaces, config levers, instruction levers
   - each entry includes citations and location

3) WORKFLOW_CATALOG.md
   - list workflows with triggers, steps, events, stores, outputs, and acceptance checks

RULES:
- Cite every entry.
- No invention.
- Deterministic ordering by id.
