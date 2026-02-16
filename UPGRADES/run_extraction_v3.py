#!/usr/bin/env python3
"""
Master Extraction Runner for Dopemux (Phases A-Z) w/ Deterministic Prompts
"""

import os
import sys
import re
import json
import time
import argparse
import fnmatch
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# --- Configuration & Constants ---

MODEL_ROUTING = {
    # SCAN PHASES: Use Gemini Flash 3 (or equivalent fast scanner)
    "A": ("gemini-2.0-flash-001", "GEMINI_API_KEY"),
    "H": ("gemini-2.0-flash-001", "GEMINI_API_KEY"),
    "D": ("gemini-2.0-flash-001", "GEMINI_API_KEY"),
    "E": ("gemini-2.0-flash-001", "GEMINI_API_KEY"),
    "W": ("gemini-2.0-flash-001", "GEMINI_API_KEY"),
    "B": ("gemini-2.0-flash-001", "GEMINI_API_KEY"),
    "G": ("gemini-2.0-flash-001", "GEMINI_API_KEY"),
    "Q": ("gemini-2.0-flash-001", "GEMINI_API_KEY"),
    
    # CODE PHASE: Use Grok for code structure/symbology
    "C": ("grok-code-fast-1", "XAI_API_KEY"),
    
    # ARBITRATION/SYNTHESIS: Use GPT-5.2 Extended Thinking
    "R": ("gpt-5.2-extended", "OPENAI_API_KEY"),
    "X": ("gpt-5.2-extended", "OPENAI_API_KEY"),
    "T": ("gpt-5.2-extended", "OPENAI_API_KEY"),
    "Z": ("gpt-5.2-extended", "OPENAI_API_KEY"),
}

# Default text extensions to scan
TEXT_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".scss",
    ".md", ".json", ".yaml", ".yml", ".toml", ".xml", ".sh", ".bash",
    ".rb", ".go", ".rs", ".c", ".cpp", ".h", ".hpp", ".java", ".kt",
    ".swift", ".php", ".phtml", ".pl", ".pm", ".t", ".r", ".sql",
    ".ini", ".cfg", ".conf", ".env", ".dockerfile", "Dockerfile",
    "Makefile", "Justfile", "Rakefile", ".githooks", ".gitignore",
    "package.json", "package-lock.json"
}

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("extract_runner")

# --- Helpers ---

def load_run_id(root: Path) -> str:
    """Load latest run_id from file or fail."""
    id_file = root / "extraction/latest_run_id.txt"
    if not id_file.exists():
        raise FileNotFoundError(f"Run ID file not found at {id_file}. Run 'make x-run-init' first.")
    return id_file.read_text().strip()

def get_run_dirs(root: Path, run_id: str) -> Dict[str, Path]:
    """Return dict of paths for the given run."""
    base = root / "extraction/runs" / run_id
    if not base.exists():
        raise FileNotFoundError(f"Run directory {base} does not exist.")
    
    # Ensure all phase dirs exist per MASTER_PIPELINE_CHECKLIST
    dirs = {
        "root": base,
        "inputs": base / "00_inputs",
        # Standard Phases
        "A": base / "A_repo_control_plane",
        "H": base / "H_home_control_plane",
        "D": base / "D_docs_pipeline",
        "C": base / "C_code_surfaces",
        "E": base / "E_execution_plane",
        "W": base / "W_workflow_plane",
        "B": base / "B_boundary_plane",
        "G": base / "G_governance_plane",
        "Q": base / "Q_quality_assurance",
        "R": base / "R_arbitration",
        "X": base / "X_feature_index",
        "T": base / "T_task_packets",
        "Z": base / "Z_handoff_freeze",
    }
    
    # Auto-create subdirs
    for p, d in dirs.items():
        if p == "inputs" or p == "root": continue
        (d / "raw").mkdir(parents=True, exist_ok=True)
        (d / "norm").mkdir(parents=True, exist_ok=True)
        (d / "qa").mkdir(parents=True, exist_ok=True)

    return dirs

def safe_read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

# --- Collector Logic ---

class Collector:
    def __init__(self, root: Path, excludes: List[str]):
        self.root = root.resolve()
        self.excludes = excludes
        
    def _is_excluded(self, path: Path) -> bool:
        # Check against excludes list (glob patterns)
        name = path.name
        rel = str(path.relative_to(self.root)) if path.is_relative_to(self.root) else name
        
        for pat in self.excludes:
            if fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel, pat):
                return True
        return False
    
    def collect(self, subdirs: Optional[List[str]] = None) -> List[Dict]:
        items = []
        roots = [self.root / d for d in subdirs] if subdirs else [self.root]
        
        for r in roots:
            if not r.exists():
                # Allow .dopemux or .taskx to be missing without error, just warn
                if not r.name.startswith("."): 
                    logger.warning(f"Root not found: {r}")
                continue
                
            if r.is_file():
                if not self._is_excluded(r):
                    items.append(self._make_item(r))
                continue
            
            for root, dirs, files in os.walk(r):
                # Prune excluded dirs in-place
                dirs[:] = [d for d in dirs if not self._is_excluded(Path(root) / d)]
                
                for f in files:
                    p = Path(root) / f
                    if self._is_excluded(p):
                        continue
                    if f.startswith(".") and f not in [".env", ".gitignore", ".claude.json", ".taskx-pin", ".tmux.conf"]: 
                        continue # Default ignore dotfiles unless special
                    
                    # Extension filter (soft)
                    if p.is_file() and p.suffix.lower() not in TEXT_EXTS and p.name not in ["Dockerfile", "Makefile", "Justfile"]:
                         continue
                         
                    items.append(self._make_item(p))
        return items

    def _make_item(self, p: Path) -> Dict:
        try:
            st = p.stat()
            size = st.st_size
            mtime = st.st_mtime
        except Exception:
            # Handle broken symlinks or permission errors
            size = 0
            mtime = 0
            
        return {
            "path": str(p),
            "size": size,
            "mtime": mtime,
            "name": p.name
        }


# --- Prompt Loader ---

def load_prompt(phase: str, step_idx: str) -> str:
    # Look for PROMPT_{phase}{step_idx}_*.md in UPGRADES/
    # E.g. A0 -> PROMPT_A0_*.md
    upgrades = Path("UPGRADES")
    prefix = f"PROMPT_{phase}{step_idx}_"
    matches = list(upgrades.glob(f"{prefix}*.md"))
    
    if not matches:
        return ""
        
    # Make deterministic: sort matches (prompts with different suffixes)
    # and pick the first one consistently.
    matches.sort()
    
    # Priority check: If we have multiple, prefer '___' over others if any, 
    # but strictly picking the first after sort is stable.
    # To be extra safe against 'PROMPT_A0_FOO.md' vs 'PROMPT_A0_BAR.md',
    # we just log what we picked.
    
    if len(matches) > 1:
        logger.warning(f"Multiple prompts found for {phase}{step_idx}: {[m.name for m in matches]}. Picking: {matches[0].name}")
        
    return matches[0].read_text()

# --- Execution Logic ---

def call_llm(provider: str, model_id: str, api_key_env: str, system_prompt: str, user_content: str) -> str:
    """
    Execute LLM call with retries and error handling.
    Supports OpenAI-compatible endpoints (Grok/Gemini/GPT-4).
    """
    api_key = os.getenv(api_key_env)
    if not api_key:
        logger.error(f"Missing API Key: {api_key_env}")
        return ""

    # Minimal endpoint mapping
    if "grok" in provider or "xai" in provider:
        base_url = "https://api.x.ai/v1"
    elif "gemini" in provider:
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai" 
    else:
        base_url = "https://api.openai.com/v1"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.1, # Low temp for extraction
    }

    retries = 3
    for attempt in range(retries):
        try:
            resp = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"LLM call failed (attempt {attempt+1}/{retries}): {e}")
            time.sleep(2 * (attempt + 1))
    
    logger.error("LLM call failed after all retries.")
    return ""

def execute_step(phase: str, step_idx: str, prompt_path: Path, context_files: List[Dict], output_dir: Path, dry_run: bool):
    """
    Execute a single extraction step.
    Loads prompt, formats context, calls LLM, saves output.
    """
    try:
        prompt_text = prompt_path.read_text(encoding="utf-8")
    except Exception:
        logger.error(f"Could not read prompt {prompt_path}")
        return

    # Context Injection
    # We limit context size naively for now - production version should use tiktoken
    context_str = ""
    for item in context_files:
        # Naive truncation
        content = safe_read(Path(item['path']))
        if len(content) > 100000: content = content[:100000] + "\n...[TRUNCATED]..."
        context_str += f"\n--- FILE: {item['path']} ---\n{content}\n"

    # Routing
    model, key_env = MODEL_ROUTING.get(phase, ("grok-code-fast-1", "XAI_API_KEY"))

    if dry_run:
        trace_file = output_dir / f"{phase}{step_idx}_TRACE.md"
        trace_file.write_text(f"# SYSTEM PROMPT\n{prompt_text}\n\n# USER CONTEXT\n{context_str[:2000]}... [truncated for trace]")
        logger.info(f"Dry-run: wrote trace to {trace_file}")
        
        # Mock Output
        mock_out = output_dir / f"{phase}{step_idx}_OUTPUT.json"
        mock_out.write_text(json.dumps({
            "artifact_type": f"{phase}{step_idx}_MOCK",
            "generated_at": datetime.now().isoformat(),
            "items": []
        }, indent=2))
        return

    logger.info(f"Executing {phase}{step_idx} with {model}...")
    result = call_llm(model, model, key_env, prompt_text, f"Extract from these files:\n{context_str}")
    
    if result:
        # Strip markdown fences
        clean_json = re.sub(r"^```json\s*", "", result, flags=re.MULTILINE)
        clean_json = re.sub(r"\s*```$", "", clean_json, flags=re.MULTILINE)
        
        out_file = output_dir / f"{phase}{step_idx}_OUTPUT.json"
        try:
            # Validate JSON
            parsed = json.loads(clean_json)
            out_file.write_text(json.dumps(parsed, indent=2))
            logger.info(f"Saved {out_file}")
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response for {phase}{step_idx}. Saving raw.")
            (output_dir / f"{phase}{step_idx}_FAILED.txt").write_text(result)

# --- Phase Implementations ---

def _run_phase_inner(phase: str, dirs: Dict[str, Path], dry_run: bool, collector: Optional[Collector], targets: Optional[List[str]], precollected_items: Optional[List[Dict]] = None):
    """Internal runner reused by A/H/C/D/E/W/B/G/R/X/T/Z"""
    logger.info(f"--- Starting Phase {phase} Execution Loop ---")
    
    # 1. Identify Prompts
    prompts = sorted(Path("UPGRADES").glob(f"PROMPT_{phase}*_*.md"))
    
    if not prompts:
        logger.error(f"No prompts found for Phase {phase} in UPGRADES/")
        return

    # 2. Collect Context
    if precollected_items is not None:
        context_items = precollected_items
        logger.info(f"Using {len(context_items)} pre-collected input artifacts.")
    else:
        logger.info(f"Scanning targets: {targets}")
        context_items = collector.collect(subdirs=targets)
        logger.info(f"Collected {len(context_items)} file contexts.")

    # 3. Execute Steps
    raw_dir = dirs[phase] / "raw"
    
    seen_steps = set()

    for p in prompts:
        # Extract step ID (A0, A1, etc)
        match = re.search(r"PROMPT_([A-Z0-9]+)_", p.name)
        if not match: continue
        step_id = match.group(1)
        
        # Determinism check: Only run first encountered file for a given Step ID
        if step_id in seen_steps:
             logger.info(f"Skipping duplicate prompt for {step_id}: {p.name}")
             continue
        seen_steps.add(step_id)
        
        execute_step(phase, step_id, p, context_items, raw_dir, dry_run)


# --- Wrappers for specific phases ---

def run_phase_A(dirs: Dict[str, Path], dry_run: bool):
    """Run Phase A (Repo Control Plane)"""
    excludes = [".git", "node_modules", "venv", "src", "services", "tests", "docs"]
    collector = Collector(Path.cwd(), excludes)
    targets = [".claude", ".dopemux", ".githooks", ".github", ".taskx", "config", "scripts", "tools", "compose", "docker", "."]
    _run_phase_inner("A", dirs, dry_run, collector, targets)

def run_phase_H(dirs: Dict[str, Path], dry_run: bool):
    """Run Phase H (Home Control Plane)"""
    home = Path.home()
    excludes = ["Downloads", "Library", "Documents", "Pictures", "Music", "Public", "Desktop", ".cache", ".npm", ".pip"]
    collector = Collector(home, excludes)
    targets = [".dopemux", ".config/dopemux", ".config/taskx", ".config/litellm", ".config/mcp"]
    _run_phase_inner("H", dirs, dry_run, collector, targets)

def run_phase_C(dirs: Dict[str, Path], dry_run: bool):
    """Run Phase C (Code Surfaces)"""
    collector = Collector(Path.cwd(), [".git", "node_modules", "venv", "docs", "test-results"])
    targets = ["src", "services", "shared", "plugins", "tools", "scripts", "tests"]
    _run_phase_inner("C", dirs, dry_run, collector, targets)

def run_phase_D(dirs: Dict[str, Path], dry_run: bool):
    """Run Phase D (Docs Pipeline)"""
    collector = Collector(Path.cwd(), [".git"])
    targets = ["docs"]
    _run_phase_inner("D", dirs, dry_run, collector, targets)

def run_phase_E(dirs: Dict[str, Path], dry_run: bool):
    """Run Phase E (Execution Plane)"""
    # E scans execution artifacts: scripts, makefiles, compose, CI
    collector = Collector(Path.cwd(), [".git", "node_modules", "docs"])
    targets = ["scripts", "tools", "compose", ".github", "Makefile", "package.json"]
    _run_phase_inner("E", dirs, dry_run, collector, targets)

def run_phase_W(dirs: Dict[str, Path], dry_run: bool):
    """Run Phase W (Workflow Plane)"""
    # W scans previous artifacts mostly, but also docs/code for workflow definitions
    # For now, scan broadly like C+D combined to find workflow traces
    collector = Collector(Path.cwd(), [".git", "node_modules"])
    targets = ["docs", "scripts", "src", "services"]
    _run_phase_inner("W", dirs, dry_run, collector, targets)

def run_phase_B(dirs: Dict[str, Path], dry_run: bool):
    """Run Phase B (Boundary Plane)"""
    # B scans mostly code/docs for boundaries
    collector = Collector(Path.cwd(), [".git", "node_modules"])
    targets = ["src", "services", "docs"]
    _run_phase_inner("B", dirs, dry_run, collector, targets)

def run_phase_G(dirs: Dict[str, Path], dry_run: bool):
    """Run Phase G (Governance Plane)"""
    # G scans CI/Gates/Instruction files
    collector = Collector(Path.cwd(), [".git", "node_modules"])
    targets = [".github", "docs", ".claude", "AGENTS.md"]
    _run_phase_inner("G", dirs, dry_run, collector, targets)

def run_phase_Q(dirs: Dict[str, Path], dry_run: bool):
    """Run Phase Q (QA/Doctor)"""
    # Q needs to look at the ARTIFACTS produced by previous phases in the current run
    
    logger.info("--- Phase Q: Pipeline Doctor ---")
    
    # 1. Collect artifacts from current run
    items = []
    
    for p in ["A", "H", "D", "C", "E", "W", "B", "G"]:
        raw_dir = dirs[p] / "raw" # Check raw outputs for Q0
        if raw_dir.exists():
             for f in raw_dir.glob("*.json"):
                 items.append({"path": str(f), "size": f.stat().st_size, "mtime": f.stat().st_mtime, "name": f.name})
    
    _run_phase_inner("Q", dirs, dry_run, None, None, precollected_items=items)


def run_phase_R(dirs: Dict[str, Path], dry_run: bool):
    """Run Phase R (Arbitration)"""
    # Consumes normalized artifacts from Scan phases
    logger.info("--- Phase R: Arbitration ---")
    
    input_files = []
    # Collect from all possible scan/structure phases
    for p in ["A", "H", "D", "C", "E", "W", "B", "G"]:
        norm_dir = dirs[p] / "norm" # Expect normalized inputs
        if not norm_dir.exists():
             norm_dir = dirs[p] / "raw" # Fallback to raw if norm missing (e.g. initial run)
        
        if norm_dir.exists():
            input_files.extend(list(norm_dir.glob("*.json")))

    items = []
    for f in input_files:
        items.append({"path": str(f), "size": f.stat().st_size, "mtime": f.stat().st_mtime, "name": f.name})
        
    _run_phase_inner("R", dirs, dry_run, None, None, precollected_items=items)


def run_phase_X(dirs: Dict[str, Path], dry_run: bool):
    """Run Phase X (Feature Index)"""
    collector = Collector(Path.cwd(), [".git", "node_modules", "venv", "docs"])
    targets = ["src", "services", "shared"]
    _run_phase_inner("X", dirs, dry_run, collector, targets)

def run_phase_T(dirs: Dict[str, Path], dry_run: bool):
    """Run Phase T (Task Packets)"""
    # T consumes R outputs (Backlog)
    input_files = []
    r_out = dirs["R"] / "out" if (dirs["R"] / "out").exists() else dirs["R"] / "raw"
    if r_out.exists():
         input_files.extend(list(r_out.glob("*.json"))) # Conflict ledger, etc
         input_files.extend(list(r_out.glob("*.md")))

    items = []
    for f in input_files:
        items.append({"path": str(f), "size": f.stat().st_size, "mtime": f.stat().st_mtime, "name": f.name})
    
    _run_phase_inner("T", dirs, dry_run, None, None, precollected_items=items)

def run_phase_Z(dirs: Dict[str, Path], dry_run: bool):
    """Run Phase Z (Handoff Freeze)"""
    # Z consumes everything final.
    logger.info("--- Phase Z: Handoff ---")
    _run_phase_inner("Z", dirs, dry_run, None, None, precollected_items=[]) # Z prompt usually self-contains instructions or looks at filesystem state


# --- Master Orchestrator ---

def main():
    parser = argparse.ArgumentParser("Master Extraction Runner")
    # Add new phases to choices
    parser.add_argument("--phase", choices=["A","H","D","C","E","W","B","G","Q","R","X","T","Z","ALL"], required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    # Layout check
    root = Path.cwd()
    try:
        run_id = load_run_id(root)
        dirs = get_run_dirs(root, run_id)
        logger.info(f"Target Run ID: {run_id}")
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)

    # Execution Plan
    if args.phase == "ALL":
        # Logical dependency order
        phases = [
            "A", "H", "D", "E", # Inventory & structure
            "C",                # Code
            "W", "B", "G",      # Semantic planes (depend on above)
            "Q",                # QA checks
            "R",                # Arbitration (depends on Q/outputs)
            "X",                # Feature Index
            "T",                # Task Packets
            "Z"                 # Freeze
        ]
    else:
        phases = [args.phase]
    
    for p in phases:
        if p == "A": run_phase_A(dirs, args.dry_run)
        elif p == "H": run_phase_H(dirs, args.dry_run)
        elif p == "C": run_phase_C(dirs, args.dry_run)
        elif p == "D": run_phase_D(dirs, args.dry_run)
        elif p == "E": run_phase_E(dirs, args.dry_run)
        elif p == "W": run_phase_W(dirs, args.dry_run)
        elif p == "B": run_phase_B(dirs, args.dry_run)
        elif p == "G": run_phase_G(dirs, args.dry_run)
        elif p == "Q": run_phase_Q(dirs, args.dry_run)
        elif p == "R": run_phase_R(dirs, args.dry_run)
        elif p == "X": run_phase_X(dirs, args.dry_run)
        elif p == "T": run_phase_T(dirs, args.dry_run)
        elif p == "Z": run_phase_Z(dirs, args.dry_run)
        else:
            logger.warning(f"Unknown phase: {p}")

if __name__ == "__main__":
    main()
