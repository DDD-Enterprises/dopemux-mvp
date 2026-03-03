from __future__ import annotations

from ..schema import Report


def render_report_md(r: Report) -> str:
    lines = []
    lines.append(f"## GitHub Specialist Report ({r.run_id})")
    lines.append(f"- Scope: **{r.scope}**")
    lines.append(f"- Target: **{r.target}**")
    lines.append(f"- Top-K: **{r.top_k}**")
    if r.warnings:
        lines.append("")
        lines.append("### Warnings")
        for w in r.warnings:
            lines.append(f"- {w}")

    for a in r.actions:
        lines.append("")
        lines.append(f"### {a.title} ({a.kind})")
        lines.append(a.body_md.strip() or "_(empty)_")
        if a.suggestions:
            lines.append("")
            lines.append("**Suggestions:**")
            for s in a.suggestions:
                lines.append(f"- **{s.title}** ({s.confidence})")
                lines.append(f"  - {s.detail}")
                if s.evidence:
                    evs = ", ".join([f"{e.kind}:{e.ref}" for e in s.evidence])
                    lines.append(f"  - Evidence: {evs}")

    return "\n".join(lines) + "\n"
