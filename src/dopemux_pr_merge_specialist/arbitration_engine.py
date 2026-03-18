import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .schema import ArbitrationEvidenceBundle, HunkContext, PRMergeReport


class EvidencePackager:
    """Builds a canonical evidence pack for high-risk integrations."""

    def __init__(self):
        pass

    def check_trigger(self, report: PRMergeReport) -> tuple[bool, str]:
        """Verify if high-risk arbitration is required."""
        
        # 1. Conflict Class Check
        conflict_class = report.telemetry.get("conflict_class", "UNKNOWN")
        if conflict_class == "HIGH_RISK":
            return True, "Trigger: Conflict identified as HIGH_RISK."
            
        # 2. Critical Blockers
        if any(b.type == "CONFLICTS" for b in report.blockers):
             # For now, any conflict + certain labels
             if "arbitrate" in report.initial_state.labels:
                 return True, "Trigger: Explicit 'arbitrate' label present."

        return False, "Not triggered: Case does not meet high-risk criteria."

    def package_evidence(self, report: PRMergeReport) -> ArbitrationEvidenceBundle:
        """Extract and unify all context for arbitration."""
        
        # Mocking SHA extraction for now
        # In real loop, would use 'git rev-parse'
        base_sha = "BASE_SHA"
        ours_sha = "OURS_SHA"
        theirs_sha = "THEIRS_SHA"
        
        # 1. Overlap Extraction (Mocked)
        overlap_files = [f for f in report.initial_state.diffstat.split("\n") if f] # Simplified
        
        # 2. Hunk Capture (Mocked)
        hunks = []
        if report.initial_state.mergeable is False:
            hunks.append(HunkContext(
                file_path="unknown_file.py",
                ours_range="10-20",
                theirs_range="12-22",
                ours_text="def some_func():\n    pass",
                theirs_text="def some_func():\n    # new logic\n    pass",
                symbols=["some_func"]
            ))

        return ArbitrationEvidenceBundle(
            merge_base_sha=base_sha,
            ours_sha=ours_sha,
            theirs_sha=theirs_sha,
            overlap_files=overlap_files,
            hunks=hunks,
            feedback_summary=[{"id": f.id, "text": f.text} for f in report.feedback_items],
            enforcement_state={
                "status": report.status,
                "readiness": report.status == "merge_ready",
                "conflict_class": report.telemetry.get("conflict_class")
            },
            provenance={
                "base": "git_rev_parse",
                "hunks": "git_diff_parser",
                "feedback": "feedback_ingest_snapshot"
            }
        )

    def emit_bundle(self, bundle: ArbitrationEvidenceBundle, out_dir: Path):
        """Emit canonical arbitration artifacts."""
        (out_dir / "ARBITRATION_EVIDENCE_BUNDLE.json").write_text(
            json.dumps(bundle.__dict__, indent=2, default=str)
        )
        (out_dir / "CONTEXT_OVERLAP_MAP.json").write_text(
            json.dumps({"files": bundle.overlap_files}, indent=2)
        )
        (out_dir / "ARBITRATION_INPUT_MANIFEST.json").write_text(
            json.dumps(bundle.provenance, indent=2)
        )
