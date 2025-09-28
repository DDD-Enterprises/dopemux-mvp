"""Pydantic schemas for redaction reports and policy data."""


from pydantic import BaseModel, Field


class RedactionReport(BaseModel):
    """Privacy redaction report tracking what was removed/masked.
    
    This model provides transparency and auditability for the
    redaction process, ensuring users understand what data
    was modified before any cloud processing.
    """
    
    coverage: float = Field(
        ..., ge=0.0, le=1.0,
        description="Observed redaction coverage over target fields"
    )
    strict: bool = Field(..., description="Whether strict redaction mode was used")
    hardfail_triggered: bool = Field(
        ..., description="Whether hard failure was triggered during redaction"
    )
    messages_total: int = Field(..., ge=0, description="Total number of messages processed")
    tokens_redacted: int = Field(
        ..., ge=0, description="Total number of tokens that were redacted"
    )
    placeholders: dict[str, int] = Field(
        default_factory=dict,
        description="Counts by placeholder ID (e.g., SUBSTANCE_USE_PSYCHEDELICS)"
    )
    coarse_label_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Counts by coarse label categories"
    )
    visibility_leaks: list[str] = Field(
        default_factory=list,
        description="Non-empty if any visibility violations detected"
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Additional notes about the redaction process"
    )


class PolicyRule(BaseModel):
    """Individual privacy policy rule."""
    
    rule_id: str = Field(..., description="Unique identifier for this rule")
    description: str = Field(..., description="Human-readable description")
    pattern: str = Field(..., description="Pattern to match (regex or keyword)")
    replacement: str = Field(..., description="Replacement placeholder")
    severity: str = Field(..., description="Rule severity level")
    enabled: bool = Field(default=True, description="Whether rule is active")


class PrivacyPolicy(BaseModel):
    """Privacy policy configuration for redaction."""
    
    policy_id: str = Field(..., description="Policy identifier")
    version: str = Field(..., description="Policy version")
    description: str = Field(..., description="Policy description")
    rules: list[PolicyRule] = Field(..., description="List of redaction rules")
    strict_mode: bool = Field(
        default=True,
        description="Whether to use strict redaction mode"
    )
