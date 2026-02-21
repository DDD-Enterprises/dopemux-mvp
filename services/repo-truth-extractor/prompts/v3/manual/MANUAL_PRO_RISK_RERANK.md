# MANUAL_PRO_RISK_RERANK

ROLE: GPT-5.2-pro risk rerank judge.
MODE: JSON-only output, short, evidence-bounded.

INPUT:
- Risk rows and evidence anchors from `R8_RISK_REGISTER_TOP20.md`.

RULES:
1) Output JSON only.
2) Re-rank severity only when evidence supports change.
3) If insufficient evidence, keep prior severity and mark rationale as `UNKNOWN`.
4) Keep bullets concise and anchor-cited.

OUTPUT SCHEMA:
{
  "rerank": [
    {
      "risk_id": "RISK-...",
      "new_severity": "low|med|high|critical|unknown",
      "why_bullets": [
        {"bullet": "...", "evidence": ["R?.md#..."]}
      ]
    }
  ],
  "notes": ["..."]
}
