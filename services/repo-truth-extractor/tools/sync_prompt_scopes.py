#!/usr/bin/env python3
"""
sync_prompt_scopes.py - V4 (Absolute 100% Coverage)

A repeatable tool to synchronize and update the 'Source scope' section
of repo-truth-extractor prompts, achieving 100% coverage of ALL ELIGIBLE files.
"""

import os
import re
import glob
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# These are the roots that MUST be covered by the collective prompt set.
ELIGIBLE_REPO_ROOTS = [
    "components/**", "compose/**", "config/**", "configs/**", "contracts/**", 
    "dashboard/**", "docker/**", "docs/**", "examples/**", "installers/**", 
    "interruption_shield/**", "ops/**", "plugins/**", "profiles/**", 
    "review_artifacts/**", "scripts/**", "services/**", "shared/**", "src/**", 
    "SYSTEM_ARCHIVE/**", "task-packets/**", "templates/**", "tests/**", 
    "tools/**", "ui-dashboard/**", "ui-dashboard-backend/**", "UPGRADES/**", 
    "vendor/**"
]

# Modern Architectural Surfaces (High Signal)
MODERN_SURFACES = {
    "HOOKS": ["`src/dopemux/hooks/**`", "`src/dopemux/mcp/hooks.py`"],
    "AGENTS": ["`services/agents/**`", "`src/dopemux/agent_orchestrator.py`"],
    "EDITOR": ["`.vibe/**`", "`.claude/**`", "`mcp-proxy-config.copilot.yaml`"]
}

SCOPE_RULES = {
    "PHASE_A": [
        "`.vibe/**`", "`.claude/**`", "`.dopemux/**`", "`.github/**`", "`.githooks/**`", "`.taskx/**`",
        "`mcp-proxy-config.copilot.yaml`"
    ] + [f"`{r}`" for r in ELIGIBLE_REPO_ROOTS if r.startswith(("config", "scripts", "tools", "compose", "docker"))],
    
    "PHASE_C": [
        "`src/**`", "`services/**`", "`components/**`", "`dashboard/**`", "`plugins/**`", 
        "`ui-dashboard/**`", "`ui-dashboard-backend/**`"
    ],
    "PHASE_X": [f"`{r}`" for r in ELIGIBLE_REPO_ROOTS],
    
    "PROMPT_A0": [f"`{r}`" for r in ELIGIBLE_REPO_ROOTS],
    "PROMPT_C0": [f"`{r}`" for r in ELIGIBLE_REPO_ROOTS],
    "PROMPT_A5": MODERN_SURFACES["HOOKS"],
    "PROMPT_C10": MODERN_SURFACES["AGENTS"],
    "PROMPT_C12": MODERN_SURFACES["AGENTS"]
}

PROMPTS_DIR = "services/repo-truth-extractor/promptsets/v4/prompts"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    filename = os.path.basename(filepath)
    parts = filename.split('_')
    phase = parts[1][0] if len(parts) > 1 and parts[1] else ""

    required_paths = []
    if phase == "A": required_paths.extend(SCOPE_RULES.get("PHASE_A", []))
    elif phase == "C": required_paths.extend(SCOPE_RULES.get("PHASE_C", []))
    elif phase == "X": required_paths.extend(SCOPE_RULES.get("PHASE_X", []))
    
    for key, paths in SCOPE_RULES.items():
        if filename.startswith(key):
            required_paths.extend(paths)
            
    required_paths = list(dict.fromkeys(required_paths))
    if not required_paths: return False
        
    # Find the Source scope block and the next header or list item that is NOT a scope
    pattern = r'(.*?## Inputs.*?-\s+Source scope \(scan these roots first\):)(.*?)(?=\n-[^-]|\n##|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if not match: return False
        
    prefix = match.group(1)
    scope_block = match.group(2)
    suffix = content[match.end(2):]
    
    # Extract all existing paths, normalized
    lines = scope_block.strip("\n").split("\n")
    existing_items = []
    seen_paths = set()
    
    for line in lines:
        line = line.strip()
        if not line: continue
        p_match = re.search(r'-\s+(`?[\w\./\-\*]+`?)', line)
        if p_match:
            path_val = p_match.group(1).replace("`", "").strip()
            if path_val not in seen_paths:
                existing_items.append(line)
                seen_paths.add(path_val)
        else:
            # Keep non-path lines if they exist?
            existing_items.append(line)

    # Add required paths if not seen
    for req in required_paths:
        req_clean = req.replace("`", "").strip()
        if req_clean not in seen_paths:
            existing_items.append(f"- {req}")
            seen_paths.add(req_clean)

    new_scope_block = "\n" + "\n".join(existing_items) + "\n"
    new_content = prefix + new_scope_block + suffix
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return True

def main():
    files = glob.glob(os.path.join(PROMPTS_DIR, "PROMPT_*.md"))
    updated = sum(1 for f in files if process_file(f))
    logging.info(f"Absolute 100% Coverage Sync Finished. Updated {updated} prompts.")

if __name__ == "__main__":
    main()
