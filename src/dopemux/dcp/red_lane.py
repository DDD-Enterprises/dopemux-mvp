from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKER = "BLOCKER"
    CRITICAL = "CRITICAL"

class Status(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"
    CONFLICTING = "CONFLICTING"

class AuthorityLabel(str, Enum):
    OBSERVED = "OBSERVED"
    CLAIMED = "CLAIMED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"
    CONFLICTING = "CONFLICTING"

@dataclass
class Finding:
    category: str
    severity: Severity
    status: Status
    authority_label: AuthorityLabel
    evidence: str
    recommended_action: str
    path: Optional[str] = None
    line: int = 0
    match: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity.value,
            "status": self.status.value,
            "authority_label": self.authority_label.value,
            "evidence": self.evidence,
            "recommended_action": self.recommended_action,
            "path": self.path,
            "line": self.line,
            "match": self.match
        }

@dataclass
class ScannerInfo:
    implementation: str = "local"
    live_adapters_used: bool = False
    external_writes_used: bool = False
    dopetask_execution_used: bool = False
    github_api_used: bool = False
    taxonomy_id: str = "UNKNOWN"
    taxonomy_path: str = "schemas/dcp/dcp_red_lane_taxonomy.instance.json"
    taxonomy_lane_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "implementation": self.implementation,
            "live_adapters_used": self.live_adapters_used,
            "external_writes_used": self.external_writes_used,
            "dopetask_execution_used": self.dopetask_execution_used,
            "github_api_used": self.github_api_used,
            "taxonomy_id": self.taxonomy_id,
            "taxonomy_path": self.taxonomy_path,
            "taxonomy_lane_ids": self.taxonomy_lane_ids
        }

@dataclass
class RepoInfo:
    base_branch: str = "main"
    base_sha: Optional[str] = None
    head_sha: Optional[str] = None
    worktree: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_branch": self.base_branch,
            "base_sha": self.base_sha,
            "head_sha": self.head_sha,
            "worktree": self.worktree
        }

@dataclass
class InputsInfo:
    changed_files: List[str] = field(default_factory=list)
    diff_text_supplied: bool = False
    control_snapshot_paths: List[str] = field(default_factory=list)
    proof_paths: List[str] = field(default_factory=list)
    audit_paths: List[str] = field(default_factory=list)
    merge_readiness_paths: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "changed_files": self.changed_files,
            "diff_text_supplied": self.diff_text_supplied,
            "control_snapshot_paths": self.control_snapshot_paths,
            "proof_paths": self.proof_paths,
            "audit_paths": self.audit_paths,
            "merge_readiness_paths": self.merge_readiness_paths
        }

@dataclass
class GuardsInfo:
    live_write_ready_status: str = "UNDEFINED_AND_BLOCKING"
    live_write_status: str = "UNKNOWN"
    merge_seam_status: str = "UNKNOWN"
    dopetask_execution_status: str = "UNKNOWN"
    github_mutation_status: str = "UNKNOWN"
    external_write_status: str = "UNKNOWN"
    self_certification_status: str = "UNKNOWN"

    def to_dict(self) -> Dict[str, str]:
        return {
            "live_write_ready_status": self.live_write_ready_status,
            "live_write_status": self.live_write_status,
            "merge_seam_status": self.merge_seam_status,
            "dopetask_execution_status": self.dopetask_execution_status,
            "github_mutation_status": self.github_mutation_status,
            "external_write_status": self.external_write_status,
            "self_certification_status": self.self_certification_status
        }

@dataclass
class SummaryInfo:
    blocker_count: int = 0
    critical_count: int = 0
    warning_count: int = 0
    unknown_count: int = 0
    conflicting_count: int = 0
    recommended_next_action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "blocker_count": self.blocker_count,
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "unknown_count": self.unknown_count,
            "conflicting_count": self.conflicting_count,
            "recommended_next_action": self.recommended_next_action
        }

@dataclass
class RedLaneReport:
    generated_at: str
    packet_id: str
    scanner: ScannerInfo
    repo: RepoInfo
    inputs: InputsInfo
    status: Status
    findings: List[Finding]
    guards: GuardsInfo
    summary: SummaryInfo
    report_family: str = "DCP_RED_LANE_REPORT"
    schema_version: str = "0.1.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_family": self.report_family,
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "packet_id": self.packet_id,
            "scanner": self.scanner.to_dict(),
            "repo": self.repo.to_dict(),
            "inputs": self.inputs.to_dict(),
            "status": self.status.value,
            "findings": [f.to_dict() for f in self.findings],
            "guards": self.guards.to_dict(),
            "summary": self.summary.to_dict()
        }
