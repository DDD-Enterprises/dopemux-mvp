import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional


class TemplateDiscoverer:
    """Finds and deduplicates existing PR templates in the repository."""

    def __init__(self, discovery_paths: List[str] = None):
        self.search_paths = discovery_paths or [
            ".github/pull_request_template.md",
            ".github/PULL_REQUEST_TEMPLATE.md",
            "docs/PULL_REQUEST_TEMPLATE.md",
            ".github/PULL_REQUEST_TEMPLATE/default.md"
        ]

    def discover(self) -> List[Dict[str, Any]]:
        found = []
        seen_files = []
        
        for path in self.search_paths:
            if os.path.exists(path):
                is_duplicate = False
                for seen in seen_files:
                    if os.path.samefile(path, seen):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    found.append({"path": path, "is_primary": len(found) == 0})
                    seen_files.append(path)
        
        template_dir = Path(".github/PULL_REQUEST_TEMPLATE")
        if template_dir.exists():
            for f in template_dir.glob("*.md"):
                path_str = str(f)
                is_duplicate = False
                for seen in seen_files:
                    if os.path.samefile(path_str, seen):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    found.append({"path": path_str, "is_primary": False})
                    seen_files.append(path_str)
                    
        return found


class DriftDetector:
    """Detects template drift using a deterministic weighted scoring model."""

    def __init__(self, alias_map_path: Path):
        self.config = json.loads(alias_map_path.read_text())
        self.canonical_sections = self.config["canonical_sections"]
        self.multipliers = {
            "PRESENT_AND_SUFFICIENT": 1.00,
            "ALIASED_SUFFICIENT": 0.95,
            "PRESENT_BUT_INSUFFICIENT": 0.40,
            "UNKNOWN": 0.20,
            "MISSING": 0.00
        }

    def normalize_heading(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"^[^\w\s]+", "", text) # Strip leading emoji/symbols
        text = text.strip(" :.!?-_")
        text = " ".join(text.split()) # Collapse internal whitespace
        return text

    def is_sufficient(self, content: str) -> bool:
        cleaned = content.strip().lower()
        if not cleaned or cleaned in self.config["insufficiency_markers"]:
            return False
        return len(cleaned) > 2

    def score_checklist(self, content: str, is_high_risk: bool = False) -> float:
        """Score checklist by represented intent count."""
        intents = self.config["checklist_intents"]
        expected = 8 if is_high_risk else 7
        matched = 0
        
        norm_content = content.lower()
        for intent_name, patterns in intents.items():
            if intent_name == "high_risk_notes_completed" and not is_high_risk:
                continue
            for pattern in patterns:
                if pattern.lower() in norm_content:
                    matched += 1
                    break
        
        return matched / expected if expected > 0 else 0.0

    def analyze(self, template_path: str, is_high_risk: bool = False) -> Dict[str, Any]:
        raw_content = Path(template_path).read_text()
        lines = raw_content.splitlines()
        
        # 1. Segment sections
        sections_content = {}
        current_section = "intro"
        for line in lines:
            m = re.match(r"^(#+)\s+(.+)$", line)
            if m:
                current_section = self.normalize_heading(m.group(2))
                sections_content[current_section] = []
            else:
                if current_section not in sections_content:
                    sections_content[current_section] = []
                sections_content[current_section].append(line)
        
        # 2. Deterministic Scoring
        raw_score = 0.0
        section_results = {}
        applicable_total_weight = 95.0
        if is_high_risk:
            applicable_total_weight = 100.0

        for name, cfg in self.canonical_sections.items():
            if name == "High-Risk Integration Notes" and not is_high_risk:
                continue
                
            weight = self.config["alignment_score_weights"].get(name, 0)
            status = "MISSING"
            detected_heading = None
            
            # Check canonical and aliases
            targets = [name] + cfg.get("accepted_aliases", [])
            for target in targets:
                norm_target = self.normalize_heading(target)
                if norm_target in sections_content:
                    detected_heading = target
                    content_str = "\n".join(sections_content[norm_target])
                    
                    if name == "Checklist":
                        multiplier = self.score_checklist(content_str, is_high_risk)
                        status = "PRESENT_AND_SUFFICIENT" if multiplier > 0.8 else "PRESENT_BUT_INSUFFICIENT"
                    else:
                        is_aliased = self.normalize_heading(target) != self.normalize_heading(name)
                        if self.is_sufficient(content_str):
                            status = "ALIASED_SUFFICIENT" if is_aliased else "PRESENT_AND_SUFFICIENT"
                            multiplier = self.multipliers[status]
                        else:
                            status = "PRESENT_BUT_INSUFFICIENT"
                            multiplier = self.multipliers[status]
                    
                    raw_score += weight * multiplier
                    break
            
            section_results[name] = {"status": status, "detected_heading": detected_heading}

        # 3. Normalization
        normalized_score = round((raw_score / applicable_total_weight) * 100)
        
        # 4. Final State Mapping & Hard Blockers
        state_bands = [
            (90, "ALIGNED"), (70, "PARTIALLY_ALIGNED"), (50, "PRESENT_BUT_WEAK"), (1, "DRIFTED"), (0, "MISSING")
        ]
        raw_band_state = "DRIFTED"
        for low, state_name in state_bands:
            if normalized_score >= low:
                raw_band_state = state_name
                break
        
        hard_blockers = []
        max_state = "ALIGNED"
        
        if section_results.get("Verification", {}).get("status") == "MISSING" or \
           section_results.get("Risks", {}).get("status") == "MISSING" or \
           section_results.get("Rollback", {}).get("status") == "MISSING":
            hard_blockers.append("missing_critical_safety_sections")
            max_state = "DRIFTED"
            
        if section_results.get("Checklist", {}).get("status") == "MISSING":
            hard_blockers.append("missing_checklist")
            max_state = min(max_state, "PRESENT_BUT_WEAK", key=lambda x: ["MISSING", "DRIFTED", "PRESENT_BUT_WEAK", "PARTIALLY_ALIGNED", "ALIGNED"].index(x))

        # Apply state ordering for min()
        state_order = ["MISSING", "DRIFTED", "PRESENT_BUT_WEAK", "PARTIALLY_ALIGNED", "ALIGNED"]
        final_state = raw_band_state
        if max_state != "ALIGNED":
            if state_order.index(raw_band_state) > state_order.index(max_state):
                final_state = max_state

        return {
            "path": template_path,
            "alignment_state": final_state,
            "normalized_score": normalized_score,
            "raw_score": round(raw_score, 2),
            "hard_blockers": hard_blockers,
            "sections": section_results,
            "recommended_mode": self.config["recommended_modes"].get(final_state, "ESCALATE")
        }


class TemplateInjectionPlanner:
    """Generates patch plans based on drift analysis."""

    def plan(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        actions = []
        for name, data in analysis["sections"].items():
            if data["status"] == "MISSING":
                actions.append({"type": "INSERT_SECTION", "section": name})
            elif data["status"] == "PRESENT_BUT_INSUFFICIENT":
                actions.append({"type": "PATCH_SECTION_BODY", "section": name})

        return {
            "target_path": analysis["path"],
            "actions": actions,
            "status": "PLAN_READY" if actions else "ALIGNED",
            "recommended_mode": analysis["recommended_mode"]
        }
