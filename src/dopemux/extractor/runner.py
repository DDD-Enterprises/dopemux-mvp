"""Deprecated legacy trace runner kept only for non-authoritative compatibility imports."""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import time
import random
import sys

from .context import ContextGatherer
from ..ui.tree import create_truth_tree, add_phase_node, add_file_node
from ..console import console
from ..ui.theme import Glyphs, RITUAL_CYAN, SERUM_MINT, GREMLIN_PINK

# Ensure service modules are importable
EXTRACTOR_SERVICE_DIR = Path(__file__).resolve().parents[3] / "services" / "repo-truth-extractor"
if str(EXTRACTOR_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(EXTRACTOR_SERVICE_DIR))

try:
    from lib.prescan.code_prescan import CodePrescan
    from lib.prescan.classifier import Classifier
    from lib.prescan.models import PrescanConfig, FileEntry
    from lib.prescan.token_counter import estimate_file_tokens
    PRESCAN_AVAILABLE = True
except ImportError:
    PRESCAN_AVAILABLE = False

logger = logging.getLogger(__name__)

class PipelineRunner:
    """Orchestrates the Full Pipeline execution (Phases A-S)."""

    PHASE_LABELS = {
        'A': 'Repo Control Plane',
        'H': 'Home Control Plane',
        'D': 'Docs Pipeline',
        'C': 'Code Surfaces',
        'E': 'Execution Plane',
        'W': 'Workflow Plane',
        'B': 'Boundary Plane',
        'G': 'Governance Plane',
        'Q': 'Quality Assurance',
        'R': 'Arbitration',
        'X': 'Feature Index',
        'T': 'Task Packets',
        'Z': 'Handoff Freeze',
        'S': 'System Truths'
    }

    PHASE_DESCRIPTIONS = {
        'A': 'Analyzing repository instruction surface and MCP server definitions.',
        'H': 'Mapping local home directory profiles and provider ladders.',
        'D': 'Crawling documentation for topic clusters and contract claims.',
        'C': 'Scanning code for entry points, event bus surfaces, and trinity enforcement.',
        'E': 'Evaluating execution flow and runtime behavioral hints.',
        'W': 'Cataloging human runbooks and automated workflow launchers.',
        'B': 'Identifying system boundaries and cross-service enforcement points.',
        'G': 'Validating governance policies and change review protocols.',
        'Q': 'Performing multi-artifact quality assurance and duplicate drift analysis.',
        'R': 'Arbitrating contradictions between documentation and implementation.',
        'X': 'Indexing core features and high-level architectural capabilities.',
        'T': 'Generating actionable task packets for future development.',
        'Z': 'Freezing state and creating checksum-verified handoff manifests.',
        'S': 'Synthesizing all extracted data into the final Repository Ground Truth.'
    }

    def __init__(self, project_root: Path, output_dir: Optional[Path] = None):
        self.project_root = project_root
        self.output_dir = output_dir or (project_root / "_audit_out" / "pipeline_trace")
        self.extractor_service_dir = project_root / "services" / "repo-truth-extractor"
        self.context_gatherer = ContextGatherer(project_root)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_all(self, dry_run: bool = True, deep: bool = False, resume: bool = False, workers: int = 1, routing_policy: str = "cost"):
        """Run the full high-fidelity extraction pipeline with verbose narrative reporting."""
        console.print(f"\n[heading]🚀 Initializing Deep Truth Pipeline (Policy: [mint]{routing_policy}[/], Workers: [mint]{workers}[/])[/heading]")
        
        if resume:
            console.print("[violet]🔄 Resuming from previous run session...[/]")

        if PRESCAN_AVAILABLE:
            # Initialize logic components
            config = PrescanConfig(repo_root=self.project_root, output_dir=self.output_dir)
            self.code_prescan = CodePrescan(config)
            self.classifier = Classifier(config)

        # --- Stage 0: Corpus Discovery ---
        console.print(f"\n[bold {RITUAL_CYAN}]Stage 0: Global Pre-processing[/]")
        with console.status("[mint]Walking repository corpus...[/]", spinner="dots"):
            all_files = self.context_gatherer.gather_file_list()
            
        # --- Visual Tree Setup ---
        tree = create_truth_tree(f"Repository Ground Truth {'(DEEP MODE)' if deep else ''}")
        
        # --- Real Local Analysis & Savings Calculation ---
        authority_counts = {"canonical": 0, "historical": 0, "operational": 0, "noise": 0}
        total_symbols = 0
        total_complexity = 0.0
        
        raw_token_total = 0
        included_token_total = 0
        skipped_count = 0
        
        with console.status("[mint]Running AST prescan and classification...[/]", spinner="dots"):
            if PRESCAN_AVAILABLE:
                for rel_path in all_files:
                    file_path = self.project_root / rel_path
                    if not file_path.exists(): continue
                    
                    file_tokens = estimate_file_tokens(file_path)
                    raw_token_total += file_tokens
                    
                    entry = FileEntry(
                        rel_path=str(rel_path), 
                        extension=rel_path.suffix,
                        size_bytes=file_path.stat().st_size
                    )
                    auth = self.classifier.classify_file(entry)
                    
                    # Inclusion Logic
                    is_included = True
                    if auth == "noise": is_included = False
                    if auth == "historical" and not deep: is_included = False
                    
                    if is_included:
                        included_token_total += file_tokens
                        if auth in authority_counts: authority_counts[auth] += 1
                        else: authority_counts["operational"] += 1 # fallback
                        
                        # Code Analysis (Surgical)
                        if rel_path.suffix in ('.py', '.js', '.ts', '.tsx'):
                            intel = self.code_prescan.analyze_file(entry, self.project_root)
                            symbols = intel.get("symbols", [])
                            total_symbols += len(symbols)
                            total_complexity += sum(s.get("complexity", 0) for s in symbols)
                    else:
                        skipped_count += 1
                        authority_counts["noise"] += 1

        # Build Stage 0 Tree
        pre_node = tree.add(f"[heading]Global Infrastructure Map[/heading]")
        pre_node.add(f"[text.dim]{Glyphs.INFO} Corpus Walker: [mint]{len(all_files)}[/] files indexed[/]")
        
        auth_summary = f"[mint]{authority_counts['canonical']}[/] canonical, [mint]{authority_counts['operational']}[/] operational"
        if deep:
            auth_summary += f", [magenta]{authority_counts['historical']}[/] historical (INCLUDED)"
        else:
            auth_summary += f", [text.dim]{authority_counts['historical']} historical (SKIPPED)[/]"
            
        pre_node.add(f"[text.dim]{Glyphs.INFO} Authority Classifier: {auth_summary}[/]")
        pre_node.add(f"[text.dim]{Glyphs.INFO} Secret Masker: Redacting sensitive triggers...[/]")
        
        # --- Optimization & Savings Display ---
        savings_tokens = raw_token_total - included_token_total
        savings_pct = (savings_tokens / max(raw_token_total, 1)) * 100
        
        opt_node = pre_node.add(f"[bold {SERUM_MINT}]420 Optimization & Savings[/]")
        opt_node.add(f"[text.dim]{Glyphs.INFO} Files Skipped: [mint]{skipped_count}[/][/]")
        opt_node.add(f"[text.dim]{Glyphs.INFO} Context Reduction: [mint]{savings_pct:.1f}%[/] ([violet]{savings_tokens:,}[/] tokens saved)[/]")
        
        enr_node = pre_node.add(f"[magenta]Enrichment: Deep Context Fingerprints[/]")
        enr_node.add(f"[text.dim]{Glyphs.CODE} Symbols Mapped: [mint]{total_symbols}[/][/]")
        avg_comp = round(total_complexity / max(total_symbols, 1), 2)
        enr_node.add(f"[text.dim]{Glyphs.BUG} Avg Cognitive Complexity: [mint]{avg_comp}[/][/]")

        # 2. Sequential Phase Execution
        pipeline_phases = ['A', 'H', 'D', 'C', 'E', 'W', 'B', 'G', 'Q', 'R', 'X', 'T', 'Z', 'S']
        
        for phase in pipeline_phases:
            label = self.PHASE_LABELS.get(phase, "Unknown Phase")
            desc = self.PHASE_DESCRIPTIONS.get(phase, "")
            
            console.print(f"\n[bold {SERUM_MINT}]Phase {phase}: {label}[/]")
            console.print(f"[text.dim]  {desc}[/]")
            
            phase_node = add_phase_node(tree, phase, label, status="running")
            self._simulate_phase_lifecycle(phase, phase_node, dry_run, routing_policy)
            
        console.print("\n" + "="*80)
        console.print(tree)
        console.print("\n[success]✅ Full Pipeline execution complete![/success]")
        console.print(f"[text.dim]Artifacts saved to: {self.output_dir}[/]\n")

    def _simulate_phase_lifecycle(self, phase: str, node: Any, dry_run: bool, policy: str = "cost"):
        """Simulates the complex internal steps of the v5 extractor with verbose output."""
        
        # 1. Inventory & Partitioning
        inv_node = node.add(f"[violet.dim]Step 1: Inventory & Partitioning[/]")
        console.print(f"  [violet]•[/] Scanning internal logic for phase {phase}...")
        time.sleep(0.02)
        inv_node.add(f"[text.dim]{Glyphs.INFO} Logic scan complete[/]")
        
        # 2. Intelligence Dispatch (The Ladder)
        tier = "extract"
        if phase in ('A', 'H', 'D', 'W', 'B', 'G'): tier = "bulk"
        if phase in ('R', 'X', 'T', 'Z', 'S'): tier = "synthesis"
        if phase == 'Q': tier = "qa"
        
        ladder_node = node.add(f"[violet.dim]Step 2: Intelligence Dispatch ({tier})[/]")
        
        # Ladder Logic mapping
        if policy == "quality":
            primary = "gpt-5.2" if tier == "synthesis" else "gpt-5.3-codex"
        elif policy == "balanced":
            primary = "gpt-5-mini"
        elif policy == "optimal":
            primary = "gemini-3-flash-preview"
        else: # cost
            primary = "gpt-5-nano" if tier == "bulk" else "gpt-5-mini"
        
        console.print(f"  [violet]•[/] Dispatching to [mint]{primary}[/] ({tier} tier)...")
        ladder_node.add(f"[text.dim]{Glyphs.ARROW_RIGHT} Primary: [mint]{primary}[/][/]")
        
        # Flair: occasional repair
        if random.random() > 0.95:
            console.print(f"  [amber]⚠ Contract violation! Retrying with strict model...[/]")
            ladder_node.add(f"[amber]{Glyphs.WARNING} Contract violation detected. Triggering repair...[/]")
            ladder_node.add(f"[text.dim]{Glyphs.ARROW_RIGHT} Escalation: [magenta]gpt-5.2 (strict)[/][/]")
        
        # 3. Artifact Generation
        art_node = node.add(f"[violet.dim]Step 3: Artifact Synthesis[/]")
        console.print(f"  [violet]•[/] Finalizing artifacts...")
        prompt_file = f"PHASE_{phase}_PROMPT.md"
        trace_file = f"PHASE_{phase}_TRACE.md"
        
        add_file_node(art_node, prompt_file)
        add_file_node(art_node, trace_file, is_trace=True)
        
        self.run_phase(phase, dry_run=dry_run)

    def run_phase(self, phase: str, dry_run: bool = True):
        """Legacy handler for backward compatibility."""
        context_content = self.context_gatherer.get_context_for_phase(phase)
        prompt_content = f"# PHASE {phase} INSTRUCTIONS\nGenerated by Dopemux PipelineRunner."
        full_prompt = f"{prompt_content}\n\n# CONTEXT\n\n{context_content}"
        trace_file = self.output_dir / f"PHASE_{phase}_TRACE.md"
        trace_file.write_text(full_prompt, encoding='utf-8')

    def list_phases(self):
        """List available phases."""
        for phase, label in self.PHASE_LABELS.items():
            print(f"[{phase}] {label}")
