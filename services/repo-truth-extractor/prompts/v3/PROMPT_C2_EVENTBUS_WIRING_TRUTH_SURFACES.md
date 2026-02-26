OUTPUTS:
- EVENTBUS_SURFACE.json
- EVENT_PRODUCERS.json
- EVENT_CONSUMERS.json

Goals: EVENTBUS_SURFACE.json, EVENT_PRODUCERS.json, EVENT_CONSUMERS.json

Prompt:
- Extract:
  - event bus implementations/adapters
  - literal event names/topics (string constants)
  - producer call sites
  - consumer registration/handlers