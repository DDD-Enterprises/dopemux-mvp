# RTE-PKT-09 Remaining Unknowns

These items remain `LIVE_VALIDATION_REQUIRED` after this plan-only packet.

## Provider Lanes

- Direct xAI model availability.
- Direct xAI returned/effective model shape.
- Direct xAI refusal and incomplete-state shape.
- Direct xAI usage and finish-reason shape.
- Direct xAI structured-output acceptance.
- OpenRouter `x-ai/...` route configuration and upstream equivalence.
- OpenRouter `x-ai/...` returned/effective model and proxy metadata.
- OpenAI-compatible provider edge fields across all configured routes.
- Gemini native refusal, incomplete, safety, and usage fields.
- Gemini OpenAI-compatible auth mode and structured-output behavior.

## Batch Lanes

- xAI batch submit acceptance.
- xAI batch status values.
- xAI batch polling terminal states.
- xAI batch cancel behavior.
- xAI downloaded output JSONL shape.
- xAI downloaded error JSONL shape.
- OpenAI-compatible output/error JSONL row reconciliation under live provider responses.
- Gemini batch output/error artifact shape under live provider responses.
- Remote file lifecycle for validation-created batch files.
- Remote deletion/cleanup support.
- xAI retrieval entrypoint alignment, because `batch_retriever.py` has xAI helpers while `run_extraction_v5.py --retrieve-provider` currently exposes only openai/gemini.

## Governance And Safety

- RTE-PKT-07 proof outputs are not present in this checkout's `out/` tree.
- RTE-PKT-08 proof outputs are not present in this checkout's `out/` tree.
- Provider billing truth.
- Provider ZDR truth.
- Provider retention truth.
- Provider account-level rate limits or quotas.
- Whether future downloaded artifacts can be retained after redaction.

## Readiness Statement

This packet does not move RTE beyond `READY_FOR_LIMITED_DRY_STATIC_USE`.

After acceptance, a future explicitly authorized live-validation execution packet may be proposed. Until then, provider and batch behavior must not be described as live validated.
