"""Normalized PM-plane models for chronicle reads and writes."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class PMChronicleProvenance(BaseModel):
    source: str = "dope-memory"
    query_mode: str
    workspace_id: str
    time_range: Optional[str] = None

class PMChronicleSupportingSource(BaseModel):
    kind: str = "canonical"
    backend: str = "dope-memory"
    entry_ids: List[str] = Field(default_factory=list)

class PMChronicleReadResult(BaseModel):
    canonical_backend: str = "dope-memory"
    canonical_id: Optional[str] = None
    linked_ids: Dict[str, str] = Field(default_factory=dict)
    provenance: PMChronicleProvenance
    supporting_sources: List[PMChronicleSupportingSource] = Field(default_factory=list)
    items: List[Dict[str, Any]] = Field(default_factory=list)
    more_count: int = 0
    next_token: Optional[str] = None

class PMChronicleWriteReceipt(BaseModel):
    canonical_backend: str = "dope-memory"
    canonical_id: str
    entry_id: str
    linked_ids: Dict[str, str] = Field(default_factory=dict)
    success: bool
    error: Optional[str] = None
