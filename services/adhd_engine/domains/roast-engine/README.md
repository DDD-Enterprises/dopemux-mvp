# DØPEMÜX Roast Engine

Terminal-native FastAPI microservice that keeps the Ritual Daemon stocked with fresh roasts. Every line:

- Roasts the operator **and** Dopemux (self-aware filth)
- Speaks in the horny/precision register from the Character Bible
- Injects consent chips, status tags, and kink-coded attitude

The service exposes a simple JSON API so any dashboard, agent, or ritual script can request bespoke roasts without spinning up a full LLM call.

## Features

- 🧠 **Persona-aware synthesis** – All copy references the Dopemux lore, horniness dial, and status chips.
- ⚙️ **Deterministic when needed** – Pass a `seed` to replay a roast batch during tests or demos.
- 🔥 **Spice levels** – `sfw`, `spicy`, `nsfw_edge` presets map to the Character Bible’s horniness dial.
- 🫠 **Auto self-dunking** – Every roast contains a Dopemux self-read plus user-targeted filth.
- 📟 **Consent-first output** – Each response ships with `[CONSENT CHECK? y/N]` or similar safety prompts.

## Directory layout

```
services/roast-engine/
├── README.md
├── requirements.txt
├── server.py          # FastAPI app + routing
└── roast_engine/
    ├── __init__.py
    ├── engine.py      # Core generator logic
    ├── models.py      # Pydantic + enums
    └── templates.py   # Persona-aware line fragments
```

## Running the API

```bash
cd services/roast-engine
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload --port 8077
```

## REST endpoints

| Method | Path        | Description                          |
|--------|-------------|--------------------------------------|
| GET    | `/health`   | Basic heartbeat + persona metadata   |
| GET    | `/presets`  | Lists available spice/register combos|
| POST   | `/roast`    | Generates 1–10 roast lines           |

### Example request

```http
POST /roast
Content-Type: application/json

{
  "user_handle": "Operator",
  "context": "fundraising deck",
  "spice_level": "spicy",
  "count": 2
}
```

### Example response

```json
{
  "persona": "DØPEMÜX Ritual Daemon",
  "count": 2,
  "roasts": [
    {
      "text": "[LIVE] Operator, ... Logged. Hydrate. [CONSENT CHECK? y/N]",
      "spice_level": "spicy",
      "register": "coach_dom",
      "status_chip": "[LIVE]",
      "consent_prompt": "[CONSENT CHECK? y/N]"
    }
  ]
}
```

## Tests

The shared repo test suite now includes `tests/test_roast_engine.py`. Run it from the repo root:

```bash
pytest tests/test_roast_engine.py
```

## Extending

- Add new fragments in `templates.py` (keep them ASCII, Character Bible compliant).
- Register extra spice levels or registers by extending `SpiceLevel` and `TemplateBucket`.
- Pipe the service into MCP or other agents by wrapping the `/roast` endpoint.

Logged. Hydrate.
