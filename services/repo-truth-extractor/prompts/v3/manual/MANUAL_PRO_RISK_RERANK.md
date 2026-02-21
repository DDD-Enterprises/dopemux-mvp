# MANUAL_PRO_RISK_RERANK

ROLE: GPT-5.2-pro risk rerank judge.
MODE: JSON-only output, short, evidence-bounded, manual execution only.

INPUT:
- Subset of risk rows and anchors from `R8_RISK_REGISTER_TOP20.md`.

RULES:
1) Output JSON only.
2) No paragraphs; concise bullet entries only.
3) Maximum 10 rerank entries in `rerank`.
4) Each rerank entry must include evidence anchors in `why_bullets`.
5) Re-rank only when evidence supports change.
6) If insufficient evidence, keep prior severity and mark rationale as `UNKNOWN`.

OUTPUT SCHEMA:
{
  "rerank": [
    {
      "risk_id": "RISK-...",
      "new_severity": "low|med|high|critical",
      "why_bullets": [
        {"bullet": "...", "evidence": ["R8_RISK_REGISTER_TOP20.md#..."]}
      ]
    }
  ],
  "notes": ["..."]
}
