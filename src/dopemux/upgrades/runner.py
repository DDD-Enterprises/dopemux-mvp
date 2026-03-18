import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json
import time

from .context import ContextGatherer

logger = logging.getLogger(__name__)

class PipelineRunner:
    """Orchestrates the Full Pipeline execution (Phases A-S)."""

    PHASES = {
        'A': ['PHASE_A_REPO_CONTROL_PLANE.md'],
        'H': ['PHASE_H_HOME_CONTROL_PLANE.md'],
        'D': ['PHASE_D_DOCS_PIPELINE.md'],
        'C': ['PHASE_C_CODE_SURFACES.md'],
        'R': ['PHASE_R_ARBITRATION_GPT52.md'],
        'S': ['PHASE_S_SYSTEM_TRUTHS_GPT52.md']
    }

    def __init__(self, project_root: Path, output_dir: Optional[Path] = None):
        self.project_root = project_root
        self.output_dir = output_dir or (project_root / "_audit_out" / "pipeline_trace")
        self.upgrades_dir = project_root / "UPGRADES"
        self.context_gatherer = ContextGatherer(project_root)

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_all(self, dry_run: bool = True):
        """Run all phases in order."""
        logger.info("🚀 Starting Full Pipeline execution...")

        for phase in ['A', 'H', 'D', 'C', 'R', 'S']:
            self.run_phase(phase, dry_run=dry_run)

        logger.info("✅ Full Pipeline execution complete!")

    def run_phase(self, phase: str, dry_run: bool = True):
        """Run a specific phase."""
        if phase not in self.PHASES:
            logger.error(f"❌ Unknown phase: {phase}")
            return

        logger.info(f"Running phase {phase}...")
        prompts = self.PHASES[phase]

        context_content = self.context_gatherer.get_context_for_phase(phase)

        for prompt_file in prompts:
            prompt_path = self.upgrades_dir / prompt_file
            if not prompt_path.exists():
                logger.warning(f"⚠️ Prompt file not found: {prompt_path}")
                continue

            prompt_content = prompt_path.read_text(encoding='utf-8')

            # Combine prompt and context
            full_prompt = f"{prompt_content}\n\n# CONTEXT\n\n{context_content}"

            # In a real implementation, we would send this to an LLM
            # For now, we simulate by writing the trace file

            trace_file = self.output_dir / f"{prompt_file.replace('.md', '_TRACE.md')}"

            if dry_run:
                trace_file.write_text(full_prompt, encoding='utf-8')
                logger.info(f"  ✅ Generated trace: {trace_file}")
            else:
                # TODO: Implement actual LLM call via litellm if available
                # For now, just write the trace as a fallback
                trace_file.write_text(full_prompt, encoding='utf-8')
                logger.info(f"  ✅ (Simulation) Generated trace: {trace_file}")

    def list_phases(self):
        """List available phases and prompts."""
        for phase, files in self.PHASES.items():
            print(f"Phase {phase}:")
            for f in files:
                exists = (self.upgrades_dir / f).exists()
                status = "✅" if exists else "❌"
                print(f"  {status} {f}")
