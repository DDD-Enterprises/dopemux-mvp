#!/usr/bin/env python3
"""Generate rewrite_data.json from phase templates."""
import json
from pathlib import Path

# Phase-family configs: (prefix_pattern, domain_steps, extra_failure_modes)
# Each prompt gets 5 domain steps + 7 foundation steps = 12 total

INVENTORY_STEPS = lambda domain, inv, part: [
    f"Scan {domain} targets; collect path, type, and content metadata for each artifact",
    f"Classify each artifact by category relevant to the {domain} domain",
    f"Build {part} by grouping files into logical categories with rationale",
    f"For each {inv} item, populate `id`, `path`, `kind`, `summary`, and `evidence`",
    f"For each {part} item, populate `id`, `partition_id`, `files` (sorted), `reason`, and `evidence`",
]

MERGE_STEPS = lambda phase, arts, merged, qa: [
    f"Load all {phase} upstream artifacts; verify schema compliance, required fields, and sort order before merging",
    f"Merge all {arts} artifacts into {merged} using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts",
    f"Run QA checks: verify all {phase} artifacts present, coverage complete, sort order deterministic; emit {qa}",
    f"Cross-check coverage: verify every inventory item has corresponding extraction entries",
    f"For each output item, populate `id`, required fields, and `evidence` per schema contracts",
]

EXTRACT_STEPS = lambda upstream, domain, output: [
    f"Load upstream inventory and partitions; use the {domain} partition as primary scan surface",
    f"Extract {domain} facts: scan relevant files for domain-specific patterns and structures",
    f"Build relationship graph: trace connections between extracted {domain} elements",
    f"Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts",
    f"For each {output} item, populate `id`, required fields, and `evidence`",
]

INV_FM = lambda: ["Policy without enforcement: if a policy exists but nothing enforces it, emit with `status: unenforced`",
                   "Overlapping artifacts: if multiple files cover the same concern, emit all with `status: overlapping`"]
MERGE_FM = lambda phase: [f"Missing {phase} artifact: if any upstream artifact is absent, proceed with available and record gap with `status: incomplete_merge`",
                          "Suspicious gap: if an inventory item has no extraction entry, flag with `status: uncovered`"]
EXTRACT_FM = lambda: ["Hidden dependency: if an element depends on something not explicitly documented, emit with `status: implicit_dependency`",
                      "Shadowed config: if a config overrides another at a different level, emit both with `status: shadow`"]

D = {}

# A-Phase
D["PROMPT_A0_REPO_CONTROL_INVENTORY___PARTITION_PLAN.md"] = {"steps": INVENTORY_STEPS("repo control-plane (`*.yaml`, `*.toml`, `*.json`, `docker-compose*`, `.claude/`)", "REPO_CTRL_INVENTORY", "REPO_CTRL_PARTITIONS"), "failure_modes": INV_FM()}
for n, domain in [("A1","instruction"), ("A2","MCP server definition"), ("A3","MCP proxy"), ("A4","router"), ("A5","hooks"), ("A6","compose service graph"), ("A7","LiteLLM"), ("A8","TaskX")]:
    out = {"A1":"INSTRUCTION_SURFACES","A2":"MCP_SERVER_DEFS","A3":"MCP_PROXY_SURFACE","A4":"ROUTER_SURFACE","A5":"HOOKS_SURFACE","A6":"COMPOSE_SERVICE_GRAPH","A7":"LITELLM_SURFACE","A8":"TASKX_SURFACE"}[n]
    fname = [f for f in Path("/Users/hue/code/dopemux-mvp/tools/prompt_rewrite_v4/benchmark/prompts").glob(f"PROMPT_{n}_*.md")][0].name
    D[fname] = {"steps": EXTRACT_STEPS("A0", domain, out), "failure_modes": EXTRACT_FM()}
D["PROMPT_A9_IMPLICIT_BEHAVIOR_HINTS.md"] = {"steps": [
    "Load all upstream A-Phase artifacts (A0-A8); use the full repo control inventory as scan surface for implicit behavior discovery",
    "Scan instruction files and config for implicit behaviors: defaults not documented, fallback chains, silent retries, auto-migrations",
    "Cross-reference declared behavior with actual code to find undocumented side effects",
    "For each implicit behavior, assess risk: classify impact if the behavior changes unexpectedly",
    "For each IMPLICIT_BEHAVIOR_HINTS item, populate `id`, behavior description, risk, and `evidence`",
], "failure_modes": ["Intentional undocumented behavior: if a behavior appears intentionally undocumented, emit with `status: likely_intentional`",
                     "Version-dependent behavior: if behavior depends on a specific version, emit with `version_constraint` and evidence"]}
D["PROMPT_A99_MERGE___QA.md"] = {"steps": MERGE_STEPS("A-Phase", "REPO_CTRL_*", "REPO_CTRL_MERGED", "REPO_CTRL_QA"), "failure_modes": MERGE_FM("A-Phase")}

# B-Phase
D["PROMPT_B0_BOUNDARY_INVENTORY___PARTITION_PLAN.md"] = {"steps": INVENTORY_STEPS("boundary/guardrail files (permission checks, auth middleware, validation layers)", "BOUNDARY_INVENTORY", "BOUNDARY_PARTITIONS"), "failure_modes": INV_FM()}
D["PROMPT_B1_BOUNDARY_ASSERTIONS___CODE_ENFORCEMENT_POINTS.md"] = {"steps": EXTRACT_STEPS("B0", "boundary assertion and code enforcement", "BOUNDARY_ASSERTIONS"), "failure_modes": EXTRACT_FM()}
D["PROMPT_B2_REFUSAL_RAILS___GUARDRAILS_SURFACE.md"] = {"steps": EXTRACT_STEPS("B0", "refusal rails and guardrails", "REFUSAL_RAILS"), "failure_modes": EXTRACT_FM()}
D["PROMPT_B3_BYPASS_PATHS___WEAK_GUARDS.md"] = {"steps": [
    "Load upstream B0-B2 artifacts; scan for paths that bypass boundary enforcement",
    "Identify weak guards: locate checks that can be circumvented via env vars, debug flags, or missing validation",
    "Trace bypass paths end-to-end: for each bypass, document the entry point, the skipped check, and the unguarded action",
    "Assess bypass severity: classify as critical (security bypass), high (auth bypass), medium (validation skip), or low (cosmetic)",
    "For each BYPASS_PATHS item, populate `id`, bypass description, severity, and `evidence`",
], "failure_modes": ["Intentional bypass: if a bypass is clearly intentional (e.g., admin override), emit with `status: intentional`",
                     "Test-only bypass: if a bypass only exists in test code, emit with `scope: test_only`"]}
D["PROMPT_B9_MERGE___QA.md"] = {"steps": MERGE_STEPS("B-Phase", "BOUNDARY_*", "BOUNDARY_MERGED", "BOUNDARY_QA"), "failure_modes": MERGE_FM("B-Phase")}

# C-Phase
D["PROMPT_C0_CODE_INVENTORY___PARTITION_PLAN.md"] = {"steps": INVENTORY_STEPS("source code (`services/`, `src/`, `lib/`, `scripts/`, `tools/`)", "CODE_INVENTORY", "CODE_PARTITIONS"), "failure_modes": INV_FM()}
for n, domain, out in [("C1","service entrypoint","SERVICE_ENTRYPOINTS"),("C2","eventbus wiring","EVENTBUS_SURFACES"),
    ("C3","dope memory storage","DOPE_MEMORY_SURFACES"),("C4","trinity boundary enforcement","TRINITY_SURFACES"),
    ("C5","TaskX integration","TASKX_INTEGRATION_SURFACES"),("C6","workflow runner and multi-service coordination","WORKFLOW_RUNNER_SURFACES"),
    ("C7","API endpoint and dashboard","API_DASHBOARD_SURFACES"),("C8","determinism, idempotency, and concurrency","DETERMINISM_SURFACES"),
    ("C10","deep service catalog","SERVICE_CATALOG_DEEP")]:
    fname = [f for f in Path("/Users/hue/code/dopemux-mvp/tools/prompt_rewrite_v4/benchmark/prompts").glob(f"PROMPT_{n}_*.md")][0].name
    D[fname] = {"steps": EXTRACT_STEPS("C0", domain, out), "failure_modes": EXTRACT_FM()}
D["PROMPT_C9_MERGE___NORMALIZE___QA.md"] = {"steps": MERGE_STEPS("C-Phase", "CODE_*", "CODE_MERGED", "CODE_QA"), "failure_modes": MERGE_FM("C-Phase")}

# D-Phase
D["PROMPT_D0_INVENTORY___PARTITION_PLAN.md"] = {"steps": INVENTORY_STEPS("documentation (`docs/**`, archive dirs)", "DOC_INVENTORY", "DOC_PARTITIONS"), "failure_modes": INV_FM()}
for n, domain, out in [("D1","doc claims, boundaries, and supersession","DOC_INDEX"),("D2","deep doc extraction (interfaces, workflows, decisions)","DOC_DEEP"),
    ("D3","citation and reference graph","DOC_CITATIONS"),("D5","doc topic clustering","DOC_TOPIC_CLUSTERS")]:
    fname = [f for f in Path("/Users/hue/code/dopemux-mvp/tools/prompt_rewrite_v4/benchmark/prompts").glob(f"PROMPT_{n}_*.md")][0].name
    D[fname] = {"steps": EXTRACT_STEPS("D0", domain, out), "failure_modes": EXTRACT_FM()}
D["PROMPT_D4_MERGE___NORMALIZE___COVERAGE_QA.md"] = {"steps": MERGE_STEPS("D-Phase", "DOC_*", "DOC_MERGED", "DOC_QA"), "failure_modes": MERGE_FM("D-Phase")}

# E-Phase
D["PROMPT_E0_EXECUTION_INVENTORY___PARTITION_PLAN.md"] = {"steps": INVENTORY_STEPS("execution-plane targets (`Makefile`, `scripts/`, `*.sh`, `.github/`, `docker*/`)", "EXEC_INVENTORY", "EXEC_PARTITIONS"), "failure_modes": INV_FM()}
for n, domain, out in [("E1","bootstrap commands","BOOTSTRAP_COMMANDS"),("E2","env loading and config chain","ENV_CHAIN"),
    ("E3","service startup graph","STARTUP_GRAPH"),("E4","runtime modes and delta report","RUNTIME_MODES"),
    ("E5","artifact outputs, logs, and state","ARTIFACT_OUTPUTS"),("E6","execution risks, ordering, and state dependency","EXEC_RISKS")]:
    fname = [f for f in Path("/Users/hue/code/dopemux-mvp/tools/prompt_rewrite_v4/benchmark/prompts").glob(f"PROMPT_{n}_*.md")][0].name
    D[fname] = {"steps": EXTRACT_STEPS("E0", domain, out), "failure_modes": EXTRACT_FM()}
D["PROMPT_E9_MERGE___NORMALIZE___QA.md"] = {"steps": MERGE_STEPS("E-Phase", "EXEC_*", "EXEC_MERGED", "EXEC_QA"), "failure_modes": MERGE_FM("E-Phase")}

# G-Phase
D["PROMPT_G0_GOVERNANCE_INVENTORY___PARTITION_PLAN.md"] = {"steps": INVENTORY_STEPS("governance targets (`.github/workflows/`, `.pre-commit-config.yaml`, `CODEOWNERS`, `LICENSE`)", "GOV_INVENTORY", "GOV_PARTITIONS"), "failure_modes": INV_FM()}
for n, domain, out in [("G1","CI gates and quality bars","GOV_CI_GATES"),("G2","repo hygiene and allowlists","GOV_HYGIENE_POLICIES"),
    ("G3","policy files and enforcement","GOV_POLICIES"),("G4","security, secrets, and reduction facts","GOV_SECRETS_SURFACE")]:
    fname = [f for f in Path("/Users/hue/code/dopemux-mvp/tools/prompt_rewrite_v4/benchmark/prompts").glob(f"PROMPT_{n}_*.md")][0].name
    D[fname] = {"steps": EXTRACT_STEPS("G0", domain, out), "failure_modes": EXTRACT_FM()}
D["PROMPT_G9_MERGE___QA.md"] = {"steps": MERGE_STEPS("G-Phase", "GOV_*", "GOV_MERGED", "GOV_QA"), "failure_modes": MERGE_FM("G-Phase")}

# H-Phase
D["PROMPT_H0_INVENTORY___PARTITION_PLAN.md"] = {"steps": INVENTORY_STEPS("home control-plane dirs (`~/.claude/`, `~/.config/`, shell profiles, dotfiles)", "HOME_INVENTORY", "HOME_PARTITIONS"), "failure_modes": [
    "Sensitive file: if a home file may contain secrets, reference by path only; emit with `kind: sensitive` and `content: REDACTED`",
    "Missing home dir: if the home scan target does not exist, emit with `status: inaccessible`"]}
for n, domain, out in [("H1","keys and credential references","HOME_KEYS_SURFACE"),("H2","MCP server definitions","HOME_MCP_SURFACE"),
    ("H3","router and provider ladder","HOME_ROUTER_SURFACE"),("H4","LiteLLM config","HOME_LITELLM_SURFACE"),
    ("H5","profiles and sessions","HOME_PROFILES_SURFACE"),("H6","tmux and workflow helpers","HOME_TMUX_WORKFLOW_SURFACE"),
    ("H7","SQLite and state DB metadata","HOME_SQLITE_SCHEMA")]:
    fname = [f for f in Path("/Users/hue/code/dopemux-mvp/tools/prompt_rewrite_v4/benchmark/prompts").glob(f"PROMPT_{n}_*.md")][0].name
    D[fname] = {"steps": EXTRACT_STEPS("H0", domain, out), "failure_modes": EXTRACT_FM()}
D["PROMPT_H9_MERGE___QA.md"] = {"steps": MERGE_STEPS("H-Phase", "HOME_*", "HOMECTRL_NORM_MANIFEST", "HOMECTRL_QA"), "failure_modes": MERGE_FM("H-Phase")}

# W-Phase
D["PROMPT_W0_WORKFLOW_INVENTORY___PARTITION_PLAN.md"] = {"steps": INVENTORY_STEPS("workflow sources (orchestration scripts, runbooks, CI workflows, compose, tmux sessions)", "WORKFLOW_INVENTORY", "WORKFLOW_PARTITIONS"), "failure_modes": INV_FM()}
for n, domain, out in [("W1","workflow catalog and runbook","WORKFLOW_CATALOG"),("W2","workflow inputs/outputs/artifacts","WORKFLOW_IO_MAP"),
    ("W3","multi-service coordination (compose/tmux)","WORKFLOW_COORDINATION_SURFACE"),("W4","workflow failure modes and recovery","WORKFLOW_FAILURE_RECOVERY"),
    ("W5","workflow state dependencies (home vs repo)","WORKFLOW_STATE_COUPLING")]:
    fname = [f for f in Path("/Users/hue/code/dopemux-mvp/tools/prompt_rewrite_v4/benchmark/prompts").glob(f"PROMPT_{n}_*.md")][0].name
    D[fname] = {"steps": EXTRACT_STEPS("W0", domain, out), "failure_modes": EXTRACT_FM()}
D["PROMPT_W9_MERGE___QA.md"] = {"steps": MERGE_STEPS("W-Phase", "WORKFLOW_*", "WORKFLOW_MERGED", "WORKFLOW_QA"), "failure_modes": MERGE_FM("W-Phase")}

# Q-Phase
for n, domain, out in [("Q0","pipeline completeness and manifest","QA_RUN_MANIFEST"),("Q1","missing artifacts and recovery plan","QA_MISSING_ARTIFACTS"),
    ("Q2","duplicate IDs and prompt collisions","QA_PROMPT_COLLISIONS"),("Q3","drift detection and norm diffs","QA_NORM_DRIFT_REPORT")]:
    fname = [f for f in Path("/Users/hue/code/dopemux-mvp/tools/prompt_rewrite_v4/benchmark/prompts").glob(f"PROMPT_{n}_*.md")][0].name
    D[fname] = {"steps": EXTRACT_STEPS("all merged phase artifacts", domain, out), "failure_modes": EXTRACT_FM()}
D["PROMPT_Q9_MERGE___QA.md"] = {"steps": MERGE_STEPS("Q-Phase", "QA_*", "PIPELINE_DOCTOR_REPORT", "QA_SERVICE_COVERAGE"), "failure_modes": MERGE_FM("Q-Phase")}

# R-Phase (synthesis/report prompts)
for n, domain, out in [("R0","control plane truth map synthesis","CONTROL_PLANE_TRUTH_MAP"),
    ("R1","dope memory implementation truth","DOPE_MEMORY_IMPLEMENTATION_TRUTH"),("R2","eventbus wiring truth","EVENTBUS_WIRING_TRUTH"),
    ("R3","trinity boundary enforcement trace","TRINITY_BOUNDARY_ENFORCEMENT_TRACE"),("R4","TaskX integration truth","TASKX_INTEGRATION_TRUTH"),
    ("R5","workflows truth graph","WORKFLOWS_TRUTH_GRAPH"),("R6","portability and migration risk ledger","PORTABILITY_RISK_LEDGER"),
    ("R7","conflict ledger","CONFLICT_LEDGER"),("R8","risk register top-20","RISK_REGISTER_TOP20")]:
    fname = [f for f in Path("/Users/hue/code/dopemux-mvp/tools/prompt_rewrite_v4/benchmark/prompts").glob(f"PROMPT_{n}_*.md")][0].name
    D[fname] = {"steps": [
        f"Load all relevant merged phase artifacts as synthesis inputs for {domain}",
        f"Synthesize {out}: combine extracted facts into a coherent truth document organized by domain category",
        f"For each element, produce prose summary with: what it does, where configured, dependencies, and risks",
        f"Cross-reference with governance and QA artifacts to annotate enforcement and coverage status",
        f"Embed evidence citations as inline references throughout the document",
    ], "failure_modes": ["Incomplete synthesis input: if key phase data is missing, produce partial document and note gaps in header",
                         "Conflicting truth: if sources contradict, present both versions with evidence and flag as `status: conflict`"]}

# T-Phase (task packet prompts)
for n, domain, out in [("T0","task packet factory design","TASK_PACKET_FACTORY"),("T1","top-10 task packet emission","TASK_PACKETS_TOP10"),
    ("T2","packet schema and authority rules","PACKET_SCHEMA_RULES"),("T3","batched packet generation","PACKET_BATCH"),
    ("T4","packet dedup and collision resolution","PACKET_DEDUP"),("T5","packet ordering and run plan","PACKET_RUN_PLAN")]:
    fname = [f for f in Path("/Users/hue/code/dopemux-mvp/tools/prompt_rewrite_v4/benchmark/prompts").glob(f"PROMPT_{n}_*.md")][0].name
    D[fname] = {"steps": [
        f"Load all upstream extraction artifacts and synthesis reports as input for {domain}",
        f"Analyze extraction outputs to identify actionable work items for {out}",
        f"For each task packet, determine scope, priority, dependencies, and acceptance criteria from evidence",
        f"Validate packet completeness: ensure each packet has sufficient context for execution",
        f"For each output item, populate `id`, required fields, and `evidence` per schema contracts",
    ], "failure_modes": ["Insufficient evidence for packet: if a task cannot be fully scoped from available data, emit with `status: needs_more_context`",
                         "Duplicate packet: if two packets cover the same work, flag with `status: potential_duplicate` and evidence"]}
D["PROMPT_T9_MERGE___QA.md"] = {"steps": MERGE_STEPS("T-Phase", "TASK_*", "TASK_PACKETS_MERGED", "TASK_PACKETS_QA"), "failure_modes": MERGE_FM("T-Phase")}

# X-Phase (feature index)
D["PROMPT_X0_FEATURE_INDEX_INVENTORY___PARTITION_PLAN.md"] = {"steps": INVENTORY_STEPS("feature-relevant sources (user-facing code, docs, configs)", "FEATURE_INVENTORY", "FEATURE_PARTITIONS"), "failure_modes": INV_FM()}
for n, domain, out in [("X1","feature surface extraction","FEATURE_SURFACES"),("X2","feature-to-code mapping","FEATURE_CODE_MAP"),
    ("X3","feature-to-doc mapping","FEATURE_DOC_MAP"),("X4","feature dependency graph","FEATURE_DEPS")]:
    fname = [f for f in Path("/Users/hue/code/dopemux-mvp/tools/prompt_rewrite_v4/benchmark/prompts").glob(f"PROMPT_{n}_*.md")][0].name
    D[fname] = {"steps": EXTRACT_STEPS("X0", domain, out), "failure_modes": EXTRACT_FM()}
D["PROMPT_X9_MERGE___QA.md"] = {"steps": MERGE_STEPS("X-Phase", "FEATURE_*", "FEATURE_INDEX_MERGED", "FEATURE_INDEX_QA"), "failure_modes": MERGE_FM("X-Phase")}

# Z-Phase (freeze/proof)
for n, domain, out in [("Z0","freeze inventory and checksums","FREEZE_INVENTORY"),("Z1","proof pack and runbook","PROOF_PACK"),
    ("Z2","opus input bundle and manifest","OPUS_INPUT_BUNDLE")]:
    fname = [f for f in Path("/Users/hue/code/dopemux-mvp/tools/prompt_rewrite_v4/benchmark/prompts").glob(f"PROMPT_{n}_*.md")][0].name
    D[fname] = {"steps": [
        f"Load all finalized extraction artifacts as input for {domain}",
        f"Compute checksums and integrity metadata for {out}",
        f"Build {out}: compile all required components with provenance tracking",
        f"Validate completeness: verify all expected artifacts are present and checksums match",
        f"For each output item, populate `id`, required fields, and `evidence` per schema contracts",
    ], "failure_modes": ["Missing artifact for freeze: if a required artifact is absent, record gap with `status: incomplete_freeze`",
                         "Checksum mismatch: if an artifact changed after freeze, flag with `status: post_freeze_mutation`"]}
D["PROMPT_Z9_FREEZE_MANIFEST___CHECKSUMS.md"] = {"steps": MERGE_STEPS("Z-Phase", "FREEZE_*", "FREEZE_MANIFEST", "FREEZE_CHECKSUMS"), "failure_modes": MERGE_FM("Z-Phase")}

# M-Phase (runtime export)
for n, domain, out in [("M0","runtime export inventory","RUNTIME_EXPORT_INVENTORY"),("M1","SQLite schema snapshots","SQLITE_SCHEMA_SNAPSHOTS"),
    ("M2","SQLite table counts","SQLITE_TABLE_COUNTS"),("M3","conport export (safe)","CONPORT_EXPORT"),
    ("M4","dope context export (safe)","DOPE_CONTEXT_EXPORT"),("M5","MCP health export (safe)","MCP_HEALTH_EXPORT"),
    ("M6","runtime export index","RUNTIME_EXPORT_INDEX")]:
    fname = [f for f in Path("/Users/hue/code/dopemux-mvp/tools/prompt_rewrite_v4/benchmark/prompts").glob(f"PROMPT_{n}_*.md")][0].name
    D[fname] = {"steps": [
        f"Load runtime state and configuration as input for {domain}",
        f"Extract {domain} data: query live state, sanitize sensitive values, and capture metadata",
        f"Build {out}: compile extracted data with timestamps and provenance",
        f"Validate export safety: ensure no secrets or sensitive data in output; redact if found",
        f"For each output item, populate `id`, required fields, and `evidence` per schema contracts",
    ], "failure_modes": ["Runtime unavailable: if the target service is not running, emit with `status: service_offline` and skip",
                         "Sensitive data in export: if sensitive data is detected, replace with `REDACTED` and flag with `status: redacted`"]}

# S-Phase (opus synthesis)
for n, domain, out in [("S0","opus architecture synthesis","ARCHITECTURE_SYNTHESIS"),("S1","MCP-to-hooks migration plan","MCP_HOOKS_MIGRATION"),
    ("S2","decision dossier","DECISION_DOSSIER"),("S3","architecture proof hooks","ARCHITECTURE_PROOF_HOOKS")]:
    fname = [f for f in Path("/Users/hue/code/dopemux-mvp/tools/prompt_rewrite_v4/benchmark/prompts").glob(f"PROMPT_{n}_*.md")][0].name
    D[fname] = {"steps": [
        f"Load all upstream extraction and synthesis artifacts as input for {domain}",
        f"Synthesize {out}: integrate findings across all phases into a cohesive analysis",
        f"For each finding, trace evidence chain back to source artifacts with inline citations",
        f"Identify architectural implications and recommend actionable next steps",
        f"For each output section, ensure evidence coverage and cite specific artifact IDs",
    ], "failure_modes": ["Incomplete evidence chain: if a finding cannot be traced to source, emit with `status: unverified`",
                         "Contradictory findings: if synthesis reveals conflicts between phases, present both with evidence"]}

# Write output
out = Path(__file__).parent / "rewrite_data.json"
out.write_text(json.dumps(D, indent=2))
print(f"Generated {len(D)} entries -> {out}")
