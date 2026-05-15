# RTE-PKT-07 Fake Response Fixtures

All fixtures are local, redacted, and synthetic. No provider payload text or credentials are included.

## OpenAI-Compatible

```python
Obj(
    id="chatcmpl-local-001",
    model="gpt-returned-fixture",
    created=1770000000,
    system_fingerprint="fp_fixture",
    choices=[Obj(finish_reason="stop", message=Obj(content="{\"ok\": true}"))],
    usage=Obj(prompt_tokens=17, completion_tokens=5, total_tokens=22),
)
```

Expected summary fields: `response_id`, `returned_model_id`, `effective_model_id`, `finish_reason`, `finish_reasons`, `usage`, token aliases, `response_text_length`, `choice_count`, `created`, and `system_fingerprint_if_present`.

## Direct xAI-Style

```python
Obj(
    id="xai-local-001",
    model="grok-effective-fixture",
    choices=[Obj(finish_reason="stop", message=Obj(content="{}"))],
    usage=Obj(prompt_tokens=10, completion_tokens=4, total_tokens=14),
)
```

Expected request metadata keeps `requested_provider=xai` and `requested_model_id=grok-requested-fixture` separate from `returned_model_id=grok-effective-fixture`.

## OpenRouter xAI Proxy

```python
Obj(
    id="or-local-001",
    model="x-ai/grok-proxy-fixture",
    choices=[Obj(finish_reason="stop", message=Obj(content="{}"))],
    usage={"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
)
```

Expected request metadata keeps `requested_provider=openrouter`, `requested_model_id=x-ai/grok-proxy-fixture`, and `provider_route_kind=openrouter_proxy_xai`.

## Refusal

```python
Obj(
    id="chatcmpl-refusal",
    model="gpt-refusal-fixture",
    choices=[
        Obj(
            finish_reason="stop",
            message=Obj(content="", refusal="Cannot comply with [REDACTED]."),
        )
    ],
    usage=Obj(prompt_tokens=3, completion_tokens=1, total_tokens=4),
)
```

Expected summary fields: `refusal=true`, sanitized `refusal_reason`, and no local `failure_type`.

## Incomplete

```python
{
    "id": "chatcmpl-incomplete",
    "model": "gpt-incomplete-fixture",
    "status": "incomplete",
    "incomplete_details": {"reason": "max_output_tokens"},
    "choices": [{"finish_reason": "length", "message": {"content": "{\"partial\": true"}}],
    "usage": {"prompt_tokens": 9, "completion_tokens": 2, "total_tokens": 11},
}
```

Expected summary fields: `response_status=incomplete`, `finish_reason=length`, `incomplete=true`, and `incomplete_reason=max_output_tokens`.

## Gemini-Style

```python
Obj(
    candidates=[Obj(finish_reason="SAFETY", safety_reason="policy_block")],
    usage_metadata=Obj(
        prompt_token_count=13,
        candidates_token_count=6,
        total_token_count=19,
    ),
)
```

Expected summary fields: `finish_reason=SAFETY`, `finish_reasons=["SAFETY"]`, `safety_reason=policy_block`, and provider usage aliases.
