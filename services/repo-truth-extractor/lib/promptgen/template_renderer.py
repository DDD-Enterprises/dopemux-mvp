"""Template renderer for the universal repo-truth-extractor.

Renders Jinja2-based base prompt templates with resolved variables
from feature detection, scope resolution, and domain vocabulary.

Output: Rendered prompt files in generated promptset directory.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# 9 required sections from the prompt contract
REQUIRED_SECTIONS = [
    "Goal",
    "Inputs",
    "Outputs",
    "Schema",
    "Extraction Procedure",
    "Evidence Rules",
    "Determinism Rules",
    "Anti-Fabrication Rules",
    "Failure Modes",
]

# The four shared/boilerplate sections a template may satisfy by pointing at
# PROMPTSET_RULES.md under "## Shared Rules" instead of inlining them. The pointer is
# resolved at runtime by run_extraction_v5._inject_promptset_rules(), which appends the
# rules file to the prompt before dispatch -- so a template carrying the pointer really
# does deliver these sections to the model.
SHARED_RULES_SECTION = "Shared Rules"
SHARED_RULES_SATISFIES = frozenset(
    {
        "Evidence Rules",
        "Determinism Rules",
        "Anti-Fabrication Rules",
        "Failure Modes",
    }
)

# Minimum section lengths (from promptset_audit_v4.py)
MIN_LENGTHS = {
    "Goal": 40,
    "Inputs": 220,
    "Schema": 280,
}


def _try_import_jinja2():
    """Import Jinja2 with fallback."""
    try:
        import jinja2
        return jinja2
    except ImportError:
        return None


def build_template_context(
    *,
    feature_map: Dict[str, Any],
    scope_resolution: Dict[str, Any],
    phase_plan: Dict[str, Any],
    repo_root: Path,
    profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the Jinja2 template context from pipeline artifacts.

    Returns a dict suitable for use as Jinja2 rendering context.
    """
    # Repo metadata
    repo_name = repo_root.name
    readme_path = repo_root / "README.md"
    repo_description = ""
    if readme_path.exists():
        lines = readme_path.read_text(errors="replace").split("\n")
        for line in lines[:10]:
            stripped = line.strip().lstrip("#").strip()
            if stripped and len(stripped) > 10:
                repo_description = stripped
                break

    # Languages from feature_map
    feature_ids = set(feature_map.get("feature_ids", []))
    languages: List[str] = []
    lang_features = {
        "python_packaging": "Python",
        "testing_python": "Python",
        "http_api_python": "Python",
        "http_api_node": "Node.js/TypeScript",
        "cli_python": "Python",
        "cli_node": "Node.js",
    }
    for fid, lang in lang_features.items():
        if fid in feature_ids and lang not in languages:
            languages.append(lang)

    # Scopes: per-step scope lists
    step_scopes = scope_resolution.get("step_scopes", {})
    scopes: Dict[str, List[str]] = {}
    for step_id, info in step_scopes.items():
        scopes[step_id] = info.get("scopes", [])

    # Features: structured access
    features: Dict[str, Dict[str, Any]] = {}
    for feat in feature_map.get("confirmed_features", []) + feature_map.get("added_features", []):
        fid = feat["feature_id"]
        features[fid] = {
            "present": True,
            "roots": feat.get("scan_roots", []),
            "confidence": feat.get("confidence", "unknown"),
            "evidence": feat.get("evidence", []),
        }

    # Domain vocabulary
    domain = feature_map.get("domain_vocabulary", {})

    # Profile
    profile_id = "P00_GENERIC"
    if profile:
        profile_id = profile.get("profile_id", "P00_GENERIC")

    # Included/skipped phases
    included_phases = scope_resolution.get("included_phases", [])
    skipped_steps = scope_resolution.get("skipped_steps", [])

    return {
        "repo": {
            "name": repo_name,
            "description": repo_description,
            "languages": languages,
            "root": str(repo_root),
        },
        "scopes": scopes,
        "features": features,
        "domain": domain,
        "profile": {
            "id": profile_id,
        },
        "phases": {
            "included": included_phases,
            "skipped_steps": skipped_steps,
        },
        "is_dopemux": feature_map.get("is_dopemux_repo", False),
    }


def render_prompt_template(
    template_text: str,
    context: Dict[str, Any],
) -> str:
    """Render a single prompt template with the given context.

    Uses Jinja2 if available; falls back to simple string substitution.
    """
    jinja2 = _try_import_jinja2()

    if jinja2 is not None:
        env = jinja2.Environment(
            undefined=jinja2.StrictUndefined,
            keep_trailing_newline=True,
        )
        # Add custom filters
        env.filters["as_list"] = _jinja_as_list
        env.filters["as_bullet_list"] = _jinja_as_bullet_list

        try:
            tmpl = env.from_string(template_text)
            return tmpl.render(**context)
        except jinja2.UndefinedError as e:
            logger.warning("Template variable not defined: %s — using fallback rendering", e)
            return _fallback_render(template_text, context)
    else:
        return _fallback_render(template_text, context)


def _jinja_as_list(value: Any) -> str:
    """Jinja2 filter: render a list as comma-separated."""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def _jinja_as_bullet_list(value: Any) -> str:
    """Jinja2 filter: render a list as markdown bullet points."""
    if isinstance(value, list):
        return "\n".join(f"- `{v}`" for v in value)
    return f"- `{value}`"


def _fallback_render(template_text: str, context: Dict[str, Any]) -> str:
    """Simple variable substitution without Jinja2."""
    result = template_text

    def _get_nested(obj: Any, path: str) -> Any:
        parts = path.split(".")
        current = obj
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part, f"{{{{ {path} }}}}")
            else:
                return f"{{{{ {path} }}}}"
        return current

    # Replace {{ var.path }} patterns
    pattern = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")
    for match in pattern.finditer(template_text):
        full = match.group(0)
        path = match.group(1)
        value = _get_nested(context, path)
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        result = result.replace(full, str(value))

    return result


def _has_section(prompt_text: str, section: str) -> bool:
    return bool(re.search(rf"^##\s+{re.escape(section)}", prompt_text, re.MULTILINE))


def validate_rendered_prompt(
    prompt_text: str,
    required_sections: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Validate that a rendered prompt meets the contract requirements.

    Args:
        prompt_text: The prompt body to check.
        required_sections: Section names to require. Defaults to REQUIRED_SECTIONS.
            Callers enforcing a promptset should pass its declared
            `required_prompt_sections` so the manifest stays the single source of truth.

    A template may satisfy the four shared boilerplate sections (SHARED_RULES_SATISFIES)
    by carrying a "## Shared Rules" pointer to PROMPTSET_RULES.md; the runtime resolves
    that pointer by injection before dispatch. This mirrors the semantics already used by
    scripts/repo_truth_extractor_promptset_audit_v4.py, so the runtime check and the
    offline linter agree rather than contradicting each other.

    Returns a dict with validation status and any issues found.
    """
    issues: List[str] = []
    sections = list(REQUIRED_SECTIONS if required_sections is None else required_sections)

    # Check for all required sections
    present_sections: Set[str] = set()
    shared_rules_present = _has_section(prompt_text, SHARED_RULES_SECTION)
    for section in sections:
        if _has_section(prompt_text, section):
            present_sections.add(section)
        elif shared_rules_present and section in SHARED_RULES_SATISFIES:
            # Delivered via the runtime PROMPTSET_RULES.md injection.
            present_sections.add(section)
        else:
            issues.append(f"Missing required section: ## {section}")

    # Check minimum lengths for present sections. Sections satisfied by the Shared Rules
    # pointer have no inline body to measure -- their length lives in PROMPTSET_RULES.md.
    for section, min_len in MIN_LENGTHS.items():
        if section not in present_sections:
            continue
        if section in SHARED_RULES_SATISFIES and not _has_section(prompt_text, section):
            continue
        # Extract section content (from header to next ## or end)
        pattern = re.compile(
            rf"^##\s+{re.escape(section)}\s*\n(.*?)(?=^##\s|\Z)",
            re.MULTILINE | re.DOTALL,
        )
        match = pattern.search(prompt_text)
        if match:
            content = match.group(1).strip()
            if len(content) < min_len:
                issues.append(
                    f"Section '{section}' too short: {len(content)} chars (min {min_len})"
                )

    # Check for unresolved template variables
    unresolved = re.findall(r"\{\{.*?\}\}", prompt_text)
    if unresolved:
        issues.append(f"Unresolved template variables: {unresolved[:5]}")

    return {
        "valid": len(issues) == 0,
        "sections_present": sorted(present_sections),
        "sections_missing": sorted(set(sections) - present_sections),
        "shared_rules_pointer": shared_rules_present,
        "issues": issues,
    }


def render_promptset(
    *,
    template_dir: Path,
    output_dir: Path,
    context: Dict[str, Any],
    step_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Render all templates in a directory to the output directory.

    Args:
        template_dir: Directory containing *.md.j2 or *.md template files.
        output_dir: Where to write rendered prompts.
        context: Template rendering context from build_template_context().
        step_ids: If provided, only render templates matching these step IDs.

    Returns:
        Summary dict with render statistics.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    templates = sorted(template_dir.glob("PROMPT_*.md*"))
    rendered = 0
    skipped = 0
    errors: List[Dict[str, str]] = []

    for tmpl_path in templates:
        # Extract step_id from filename (e.g., PROMPT_C1_SERVICE_ENTRYPOINTS.md)
        stem = tmpl_path.stem
        if stem.endswith(".md"):
            stem = stem[:-3]  # .md.j2 → strip .md
        parts = stem.split("_", 2)
        if len(parts) < 2:
            continue
        step_id = parts[1]

        if step_ids and step_id not in step_ids:
            skipped += 1
            continue

        # Skip if step is in skipped list
        if step_id in context.get("phases", {}).get("skipped_steps", []):
            skipped += 1
            continue

        try:
            template_text = tmpl_path.read_text(encoding="utf-8")
            rendered_text = render_prompt_template(template_text, context)

            # Determine output filename
            out_name = f"PROMPT_{step_id}_{stem.split('_', 2)[-1] if len(parts) > 2 else 'UNNAMED'}.md"
            out_path = output_dir / out_name
            out_path.write_text(rendered_text, encoding="utf-8")
            rendered += 1

        except Exception as e:
            errors.append({
                "template": tmpl_path.name,
                "error": str(e),
            })

    return {
        "total_templates": len(templates),
        "rendered": rendered,
        "skipped": skipped,
        "errors": errors,
        "output_dir": str(output_dir),
    }
