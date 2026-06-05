# Response Envelope Schema

## Canonical Envelope
Every successful response from the facade must adhere to the following schema:
```json
{
  "project_id": "string",
  "status": "string (SUCCESS/ERROR)",
  "authority_tier": "string",
  "data": "object"
}
```

## Status Semantics
- `SUCCESS`: The data was successfully retrieved and resolved.
- `ERROR`: Retrieval failed or path was denied.
