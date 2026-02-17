GOAL: identify execution risks from evidence (not speculation).

OUTPUT (JSON):
	•	EXEC_EXECUTION_RISKS.json

MUST FLAG:
	•	Ordering sensitivity (must run A before R, etc.) if enforced by code/scripts/docs
	•	“Hidden state” requirements (needs ~/.dopemux, needs docker volume, needs running service)
	•	Network assumptions (ports, hostnames) if present
	•	“Retry needed” surfaces (LLM calls, rate limit notes) if present
	•	Any failure modes that are explicitly described

FORMAT:

{
  "artifact_type":"EXEC_EXECUTION_RISKS",
  "generated_at":"...",
  "risks":[
    {"id":"RISK_E_0001","severity":"high|med|low","statement":"Phase R refuses without norm artifacts","evidence":["run_extraction_v3.py#..."],"mitigation_hint":"Run A/H/D/C first"}
  ]
}

RULES:
	•	No guessed mitigations. “Mitigation_hint” must be mechanical and directly supported.
