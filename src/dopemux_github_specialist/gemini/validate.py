from __future__ import annotations

import json
from typing import Any, Dict

from ..schema import Report, ProposedAction, Suggestion, EvidenceRef
from ..errors import SchemaError
from ..deterministic import stable_sort


def parse_and_validate_report(raw_json: str, run_id: str) -> Report:
    """
    Parse raw JSON from Gemini and validate it against the Report schema.
    Enforces Dopemux safety invariants (safe_to_execute=False, top_k=3).
    """
    # Guardrails: fail if Gemini chatters
    if "```" in raw_json:
        # Extract JSON from blocks if present
        import re
        match = re.search(r"```json\s*(.*?)\s*```", raw_json, re.DOTALL)
        if match:
            raw_json = match.group(1)
        else:
            raise SchemaError("Gemini output contains markdown blocks but no valid json block")

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise SchemaError(f"Failed to parse JSON from Gemini: {e}\nRaw output: {raw_json[:200]}...")

    if not isinstance(data, dict):
        raise SchemaError("Gemini output is not a JSON object")

    # Enforce stable ordering and safety
    actions_raw = data.get("actions", [])
    if not isinstance(actions_raw, list):
        raise SchemaError("'actions' must be a list")

    validated_actions = []
    for a_raw in actions_raw:
        if not isinstance(a_raw, dict):
            continue
        
        suggestions_raw = a_raw.get("suggestions", [])
        validated_suggestions = []
        for s_raw in suggestions_raw:
            if not isinstance(s_raw, dict):
                continue
            
            evidence_raw = s_raw.get("evidence", [])
            validated_evidence = []
            for e_raw in evidence_raw:
                if not isinstance(e_raw, dict):
                    continue
                validated_evidence.append(EvidenceRef(
                    kind=e_raw.get("kind", "link"),
                    ref=e_raw.get("ref", "unknown"),
                    excerpt=e_raw.get("excerpt")[:200] if e_raw.get("excerpt") else None
                ))
            
            validated_suggestions.append(Suggestion(
                title=s_raw.get("title", "Untitled Suggestion"),
                detail=s_raw.get("detail", ""),
                confidence=s_raw.get("confidence", "LOW"),
                evidence=validated_evidence
            ))

        # Enforce Top-K=3 for suggestions
        validated_suggestions = validated_suggestions[:3]

        validated_actions.append(ProposedAction(
            kind=a_raw.get("kind", "comment_pr"),
            title=a_raw.get("title", "Untitled Action"),
            body_md=a_raw.get("body_md", ""),
            suggestions=validated_suggestions,
            safe_to_execute=False,  # Hard invariant: NEVER safe by default
            evidence=[] # Populate if needed
        ))

    # Stable sort actions by kind and title
    validated_actions = stable_sort(validated_actions, key=lambda a: (a.kind, a.title))

    return Report(
        run_id=run_id,
        scope=data.get("scope", "repo"),
        target=data.get("target", "unknown"),
        top_k=3,
        actions=validated_actions,
        warnings=data.get("warnings", []),
        blocked=data.get("blocked", False),
        blocked_reason=data.get("blocked_reason")
    )
