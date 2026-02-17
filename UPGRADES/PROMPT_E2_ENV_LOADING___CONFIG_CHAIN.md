GOAL: map the environment/config loading chain.

OUTPUT (JSON):
	•	EXEC_ENV_CHAIN.json

MUST INCLUDE:
	•	Env vars referenced (names only) + source (dotenv file? shell? CI secrets? config.yaml? CLI flag?)
	•	Default values if explicitly set
	•	Precedence if explicitly stated (e.g., CLI overrides env, env overrides config file)
	•	“Required credentials” surfaces: Gemini/XAI/OpenAI keys, MCP configs, DB URLs, etc.

FORMAT:

{
  "artifact_type":"EXEC_ENV_CHAIN",
  "generated_at":"...",
  "env_vars":[
    {"name":"OPENAI_API_KEY","sources":[".env","CI","shell"],"default":null,"required_hint":true,"evidence":["PATH#locator"]}
  ],
  "config_files":[
    {"path":"config.yaml","keys":["..."],"evidence":["..."]}
  ],
  "precedence_rules":[
    {"rule":"CLI > ENV > FILE","evidence":["..."]}
  ]
}

RULES:
	•	If precedence is not explicitly documented, mark as UNKNOWN.
	•	Don’t guess required vs optional unless file explicitly indicates.
