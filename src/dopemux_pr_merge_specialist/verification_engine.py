import re
import subprocess
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .schema import FeedbackItem, VerificationRequest, VerificationResult, VerificationExecutionPlan


class VerificationExtractor:
    """Extracts explicit verification requests from feedback text."""

    def __init__(self):
        self.patterns = [
            (r"(?i)run (pytest|test|tests)", "pytest"),
            (r"(?i)run (lint|linter|ruff|flake8)", "lint"),
            (r"(?i)run (typecheck|mypy|tsc)", "typecheck"),
            (r"(?i)verify (migration|schema|db)", "verify_migration"),
            (r"(?i)check (build|dist)", "build"),
        ]

    def extract(self, items: List[FeedbackItem]) -> List[VerificationRequest]:
        requests = []
        for item in items:
            for pattern, intent in self.patterns:
                if re.search(pattern, item.text):
                    requests.append(VerificationRequest(
                        id=f"VERIF_{item.id}_{intent}",
                        intent=f"Requested by {item.author}: {intent}",
                        source_item_id=item.id,
                        command_intent=intent
                    ))
        return requests


class CommandMapper:
    """Maps verification intents to safe, repo-local shell commands."""

    def __init__(self, policy_map: Optional[Dict[str, str]] = None):
        # Default policy for dopemux-mvp
        self.policy_map = policy_map or {
            "pytest": "pytest",
            "lint": "ruff check .",
            "typecheck": "mypy .",
            "verify_migration": "ls src/dopemux_pr_merge_specialist/", # Placeholder
            "build": "python3 -m build"
        }

    def map_requests(self, requests: List[VerificationRequest]) -> VerificationExecutionPlan:
        executable = []
        manual = []
        refused = []

        for req in requests:
            command = self.policy_map.get(req.command_intent)
            if command:
                # Security: Only allow exact mapped commands
                executable.append(VerificationRequest(
                    **{**req.__dict__, "mapped_command": command, "status": "EXECUTABLE"}
                ))
            else:
                # If intent not in map, default to manual
                manual.append(VerificationRequest(
                    **{**req.__dict__, "status": "MANUAL"}
                ))

        return VerificationExecutionPlan(executable=executable, manual=manual, refused=refused)


class VerificationExecutor:
    """Executes verification commands and captures results."""

    def __init__(self, evidence_dir: Path):
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, plan: VerificationExecutionPlan) -> List[VerificationResult]:
        results = []
        for req in plan.executable:
            print(f"  ⚡ Executing: {req.mapped_command}")
            start_time = time.time()
            
            # Execute with timeout
            try:
                res = subprocess.run(
                    req.mapped_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300 # 5 min limit
                )
                duration_ms = (time.time() - start_time) * 1000
                
                # Store evidence
                evidence_path = self.evidence_dir / f"{req.id}.log"
                evidence_path.write_text(f"Command: {req.mapped_command}\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")
                
                results.append(VerificationResult(
                    request_id=req.id,
                    command=req.mapped_command,
                    exit_code=res.returncode,
                    stdout=res.stdout[:1000], # Cap for report
                    stderr=res.stderr[:1000],
                    duration_ms=duration_ms,
                    evidence_path=str(evidence_path)
                ))
            except subprocess.TimeoutExpired:
                results.append(VerificationResult(
                    request_id=req.id,
                    command=req.mapped_command,
                    exit_code=-1,
                    stdout="",
                    stderr="TIMEOUT EXPIRED",
                    duration_ms=300000.0
                ))
            except Exception as e:
                results.append(VerificationResult(
                    request_id=req.id,
                    command=req.mapped_command,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Error executing command: {str(e)}",
                    duration_ms=0.0
                ))
        return results
