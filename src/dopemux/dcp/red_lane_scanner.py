import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from dopemux.dcp.red_lane import (
    RedLaneReport, Finding, ScannerInfo, RepoInfo, InputsInfo, GuardsInfo, SummaryInfo,
    Severity, Status, AuthorityLabel
)
from dopemux.dcp.red_lane_rules import FORBIDDEN_PATHS, TEXT_RULES, is_safe_false_positive, redact_secret_like

class RedLaneScanner:
    def __init__(self, repo_root: str):
        self.repo_root = repo_root

    def scan(
        self,
        changed_files: Optional[List[str]] = None,
        diff_text: Optional[str] = None,
        control_snapshot_paths: Optional[List[str]] = None,
        proof_paths: Optional[List[str]] = None,
        audit_paths: Optional[List[str]] = None,
        merge_readiness_paths: Optional[List[str]] = None,
        expected_head_sha: Optional[str] = None
    ) -> RedLaneReport:
        changed_files = changed_files or []
        control_snapshot_paths = control_snapshot_paths or []
        proof_paths = proof_paths or []
        audit_paths = audit_paths or []
        merge_readiness_paths = merge_readiness_paths or []
        
        findings = []
        
        # Check Paths
        for fpath in changed_files:
            for pattern in FORBIDDEN_PATHS:
                if pattern.match(fpath):
                    findings.append(Finding(
                        category="FORBIDDEN_PATH",
                        severity=Severity.CRITICAL,
                        status=Status.BLOCKED,
                        authority_label=AuthorityLabel.OBSERVED,
                        evidence=f"Edited forbidden path: {fpath}",
                        recommended_action="Revert changes to forbidden path.",
                        path=fpath
                    ))

        # Check Source Text
        for fpath in changed_files:
            if is_safe_false_positive(fpath):
                continue
            full_path = os.path.join(self.repo_root, fpath)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    try:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            for rule in TEXT_RULES:
                                for pat in rule.patterns:
                                    if pat.search(line):
                                        findings.append(Finding(
                                            category=rule.category,
                                            severity=Severity(rule.severity),
                                            status=Status.BLOCKED,
                                            authority_label=AuthorityLabel.OBSERVED,
                                            evidence=f"Found forbidden text matching rule {rule.rule_id}",
                                            recommended_action=rule.recommended_action,
                                            path=fpath,
                                            line=i+1,
                                            match=redact_secret_like(line.strip())
                                        ))
                    except UnicodeDecodeError:
                        pass # skip binary files
                        
        # Validate Artifacts
        guards = GuardsInfo()
        self._scan_artifacts(
            proof_paths, audit_paths, merge_readiness_paths, control_snapshot_paths,
            expected_head_sha, guards, findings
        )
        
        blocker_count = sum(1 for f in findings if f.severity in (Severity.BLOCKER, Severity.CRITICAL))
        critical_count = sum(1 for f in findings if f.severity == Severity.CRITICAL)
        warning_count = sum(1 for f in findings if f.severity == Severity.WARNING)
        
        # Check if ANY required guard is UNKNOWN or CONFLICTING
        # If no findings, but guards aren't explicitly safe, it might not be PASS
        final_status = Status.PASS
        unsafe_values = {"OPERATIONAL", "VIOLATED", "DETECTED"}
        if blocker_count > 0:
            final_status = Status.BLOCKED
        elif any(v in unsafe_values for v in guards.to_dict().values()):
            final_status = Status.BLOCKED # or UNKNOWN depending on rules. Fail-closed.
            if any(v == "CONFLICTING" for v in guards.to_dict().values()):
                final_status = Status.CONFLICTING
            elif final_status != Status.CONFLICTING and any(v == "UNKNOWN" for v in guards.to_dict().values()):
                final_status = Status.UNKNOWN if final_status != Status.BLOCKED else Status.BLOCKED

        if blocker_count > 0:
            final_status = Status.BLOCKED
        else:
            is_unknown = False
            for v in guards.to_dict().values():
                if v == "UNKNOWN":
                    is_unknown = True
                elif v in unsafe_values:
                    final_status = Status.BLOCKED
            if final_status != Status.BLOCKED and is_unknown:
                final_status = Status.UNKNOWN
                
        summary = SummaryInfo(
            blocker_count=blocker_count,
            critical_count=critical_count,
            warning_count=warning_count,
            unknown_count=sum(1 for f in findings if f.status == Status.UNKNOWN),
            conflicting_count=sum(1 for f in findings if f.status == Status.CONFLICTING),
            recommended_next_action="Review blocked findings" if final_status == Status.BLOCKED else "Ready"
        )
        
        return RedLaneReport(
            generated_at=datetime.utcnow().isoformat() + "Z",
            packet_id="TP-DCP-0005",
            scanner=ScannerInfo(),
            repo=RepoInfo(head_sha=expected_head_sha),
            inputs=InputsInfo(
                changed_files=changed_files,
                diff_text_supplied=bool(diff_text),
                control_snapshot_paths=control_snapshot_paths,
                proof_paths=proof_paths,
                audit_paths=audit_paths,
                merge_readiness_paths=merge_readiness_paths
            ),
            status=final_status,
            findings=findings,
            guards=guards,
            summary=summary
        )

    def _scan_artifacts(
        self, 
        proof_paths: List[str], 
        audit_paths: List[str], 
        merge_readiness_paths: List[str], 
        control_snapshot_paths: List[str],
        expected_head_sha: Optional[str], 
        guards: GuardsInfo, 
        findings: List[Finding]
    ) -> None:
        # We need to process proof/audit/merge_readiness to confirm:
        # no stale proof, no self-certification, no unknown reviewers.
        
        # If these are not provided, we have UNKNOWN for some guards, meaning it fails closed.
        if not proof_paths:
            guards.live_write_ready_status = "UNKNOWN"
            guards.live_write_status = "UNKNOWN"
            guards.merge_seam_status = "UNKNOWN"
            guards.dopetask_execution_status = "UNKNOWN"
            guards.github_mutation_status = "UNKNOWN"
            guards.external_write_status = "UNKNOWN"
            guards.self_certification_status = "UNKNOWN"
        else:
            for pp in proof_paths:
                full_path = os.path.join(self.repo_root, pp)
                if os.path.exists(full_path):
                    with open(full_path, "r") as f:
                        try:
                            data = json.load(f)
                        except json.JSONDecodeError:
                            continue
                            
                        # Stale proof check
                        # Note: Self-Reference Exception: Updating PROOF.json in a branch changes
                        # the branch's head SHA. Under docs/ops/pr-acceptance.md §1 (Acceptance Gates),
                        # proof freshness may be satisfied by an explicit supervisor-accepted
                        # self-reference exception when the proof records proof-only changed-file
                        # evidence and the embedded audit is nonblocking. In post-merge scenarios,
                        # reconciliation can be recorded in POST_MERGE_RECONCILIATION.json to close the gap.
                        proof_head = data.get("head_sha")
                        if expected_head_sha and proof_head and proof_head != expected_head_sha:
                            findings.append(Finding(
                                category="STALE_PROOF",
                                severity=Severity.BLOCKER,
                                status=Status.BLOCKED,
                                authority_label=AuthorityLabel.OBSERVED,
                                evidence="Proof head_sha does not match expected_head_sha",
                                recommended_action="Regenerate proof."
                            ))
                        
                        # Self certification / distinct auditor
                        impl = data.get("implementer_identity")
                        auditor = data.get("audit", {}).get("auditor_identity", data.get("auditor_identity"))
                        
                        if impl and auditor and impl == auditor:
                            guards.self_certification_status = "DETECTED"
                            findings.append(Finding(
                                category="SELF_CERTIFICATION",
                                severity=Severity.BLOCKER,
                                status=Status.BLOCKED,
                                authority_label=AuthorityLabel.OBSERVED,
                                evidence="Implementer and auditor are the same identity",
                                recommended_action="Use a distinct auditor."
                            ))
                        else:
                            guards.self_certification_status = "NONE"
                            
                        # Other guards inferred from proof file fields if present
                        guards.live_write_ready_status = data.get("live_write_ready_status", guards.live_write_ready_status)
                        guards.live_write_status = data.get("live_write_status", guards.live_write_status)
                        guards.merge_seam_status = data.get("merge_seam_status", guards.merge_seam_status)
                    
                    # Assume none if explicitly documented as such, or if not present assume unknown/blocker depending on policy
                    # For tests, we'll let the proof explicitly say "NONE"
                    # We can assume safe if the text scanner didn't find anything AND we got here.
                    
        # Update guards based on findings
        if any(f.category == "MERGE_SEAM_VIOLATION" for f in findings):
            guards.merge_seam_status = "VIOLATED"
        elif guards.merge_seam_status == "UNKNOWN":
             guards.merge_seam_status = "PRESERVED"
             
        if any(f.category == "LIVE_WRITE_CREEP" for f in findings):
            guards.live_write_ready_status = "OPERATIONAL"
            
        if guards.live_write_status == "UNKNOWN":
             guards.live_write_status = "NONE"
            
        if any(f.category == "DOPETASK_EXECUTION" for f in findings):
            guards.dopetask_execution_status = "DETECTED"
        elif guards.dopetask_execution_status == "UNKNOWN":
             guards.dopetask_execution_status = "NONE"
             
        if any(f.category == "FORBIDDEN_CALL" for f in findings):
             guards.external_write_status = "DETECTED"
             
        if any(f.category == "EXTERNAL_WRITE_STATUS" for f in findings):
             guards.external_write_status = "DETECTED"
        elif guards.external_write_status == "UNKNOWN":
             guards.external_write_status = "NONE"
             
        if guards.github_mutation_status == "UNKNOWN":
             guards.github_mutation_status = "NONE"

        # Check PR Steward Merge Readiness if present
        for mr in merge_readiness_paths:
            full_path = os.path.join(self.repo_root, mr)
            if os.path.exists(full_path):
                with open(full_path, "r") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        continue
                    
                    if data.get("has_unknown_reviewers") or data.get("has_unknown_bots"):
                        findings.append(Finding(
                            category="UNKNOWN_REVIEWER_OR_BOT",
                            severity=Severity.BLOCKER,
                            status=Status.BLOCKED,
                            authority_label=AuthorityLabel.OBSERVED,
                            evidence="Merge readiness indicates unknown reviewer or bot",
                            recommended_action="Review access."
                        ))
                    
                    if data.get("has_unresolved_blocking_threads"):
                        findings.append(Finding(
                            category="UNRESOLVED_BLOCKING_THREAD",
                            severity=Severity.BLOCKER,
                            status=Status.BLOCKED,
                            authority_label=AuthorityLabel.OBSERVED,
                            evidence="Merge readiness indicates unresolved blocking threads",
                            recommended_action="Resolve threads."
                        ))
                        
                    if data.get("failed_checks"):
                         findings.append(Finding(
                            category="CI_OR_WORKFLOW_MUTATION", # Mapping generic failure to blocked.
                            severity=Severity.BLOCKER,
                            status=Status.BLOCKED,
                            authority_label=AuthorityLabel.OBSERVED,
                            evidence="Failed checks reported",
                            recommended_action="Fix checks."
                        ))
                    
                    if data.get("undocumented_residual_risk"):
                         findings.append(Finding(
                            category="UNCLASSIFIED_RISK",
                            severity=Severity.BLOCKER,
                            status=Status.BLOCKED,
                            authority_label=AuthorityLabel.OBSERVED,
                            evidence="Undocumented residual risk",
                            recommended_action="Document risks."
                        ))
