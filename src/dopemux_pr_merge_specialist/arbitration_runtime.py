import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from .schema import (
    AnalyzerReport, 
    ChallengeReport, 
    ArbiterReport, 
    ProviderInvocationMetadata, 
    RuntimeFailure
)


class SchemaValidator:
    """Ensures model outputs match strict role schemas."""

    def validate(self, role: str, data: Dict[str, Any]):
        required_fields = {
            "analyzer": ["ours_summary", "theirs_summary", "candidate_end_states", "confidence"],
            "challenger": ["objections", "hidden_risks", "confidence"],
            "arbiter": ["preferred_candidate", "defer_to_human", "confidence"]
        }
        
        fields = required_fields.get(role.lower(), [])
        for field in fields:
            if field not in data:
                raise ValueError(f"Missing required field '{field}' for role '{role}'")


class ArbitrationLLMClient:
    """Provider-agnostic transport for high-risk arbitration roles."""

    def __init__(self, mode: str = "MOCK", provider_config: Optional[Dict[str, Any]] = None):
        self.mode = mode
        self.config = provider_config or {}
        self.validator = SchemaValidator()

    def run_role(
        self, 
        role: str, 
        evidence_bundle: Dict[str, Any], 
        prior_reports: List[Any] = None
    ) -> Union[Dict[str, Any], RuntimeFailure]:
        """Execute a role prompt via the configured provider."""
        start_time = time.time()
        
        # 1. Routing (Simplified for TP-033)
        provider = self.config.get(role, {}).get("provider", "MOCK")
        model = self.config.get(role, {}).get("model", "STUB")
        
        try:
            # 2. Mock / Real Call
            if provider == "MOCK" or self.mode == "MOCK":
                raw_output = self._get_mock_response(role)
            else:
                # In real impl, would use PAL MCP or direct SDK
                # For 033, we assume routed calls through PAL is the goal
                raw_output = "{}" 

            # 3. Parse and Validate
            data = json.loads(raw_output)
            self.validator.validate(role, data)
            
            latency = (time.time() - start_time) * 1000
            return {
                "data": data,
                "metadata": ProviderInvocationMetadata(
                    role=role,
                    provider=provider,
                    model=model,
                    latency_ms=latency,
                    status="SUCCESS",
                    prompt_version="1.0.0"
                )
            }

        except json.JSONDecodeError as e:
            return RuntimeFailure(role, "INVALID_JSON", str(e), can_retry=True)
        except ValueError as e:
            return RuntimeFailure(role, "SCHEMA_INVALID", str(e), can_retry=False)
        except Exception as e:
            return RuntimeFailure(role, "TRANSPORT_ERROR", str(e), can_retry=True)

    def call_role(self, role: str, prompt: str) -> str:
        """Execute a generic role-based prompt (e.g. for code synthesis)."""
        if self.mode == "MOCK":
            return self._get_mock_generic_response(role, prompt)
        
        # Real implementation would call PAL/SDK here
        return "{}"

    def _get_mock_generic_response(self, role: str, prompt: str) -> str:
        """Fixture-backed responses for generic tasks in MOCK mode."""
        if "Implement a review suggestion" in prompt:
            # Detect target file from prompt if possible
            import re
            file_match = re.search(r"File:\s*([^\s\n]+)", prompt)
            target_file = file_match.group(1) if file_match else "src/example.py"
            
            return json.dumps({
                "explanation": "Synthesized a surgical fix based on the review feedback.",
                "file": target_file,
                "patch": f"# Suggested fix for {target_file}\ndef resolved_logic():\n    return True\n",
                "confidence": "HIGH"
            })
        
        return "{}"

    def _get_mock_response(self, role: str) -> str:
        """Fixture-backed responses for MOCK mode."""
        mocks = {
            "analyzer": {
                "case_id": "ANALYZER_MOCK",
                "evidence_bundle_ref": "ARBITRATION_EVIDENCE_BUNDLE.json",
                "ours_summary": "Mock ours",
                "theirs_summary": "Mock theirs",
                "overlap_summary": "Mock overlap",
                "candidate_end_states": [{"id": "C1", "desc": "Synthesized"}],
                "confidence": "HIGH"
            },
            "challenger": {
                "case_id": "CHALLENGER_MOCK",
                "analyzer_ref": "ANALYZER_MOCK",
                "objections": [],
                "hidden_risks": [],
                "confidence": "HIGH"
            },
            "arbiter": {
                "case_id": "ARBITER_MOCK",
                "analyzer_ref": "ANALYZER_MOCK",
                "challenge_ref": "CHALLENGER_MOCK",
                "preferred_candidate": "C1",
                "defer_to_human": False,
                "confidence": "HIGH"
            }
        }
        return json.dumps(mocks.get(role.lower(), {}))
