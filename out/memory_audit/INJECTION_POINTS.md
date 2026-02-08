# INJECTION_POINTS

## 1) Claude Brain (Primary Chat Completion Injection)

### Injection Site
- Messages are assembled in `_prepare_messages`: system prompt first, user prompt second, then serialized `request.context` appended to user content. (services/claude_brain/brain_manager.py:L447-L460)
- Completed `messages` are sent to LiteLLM `completion(...)` in `_make_ai_request`. (services/claude_brain/brain_manager.py:L375-L392)

### Source Order
- Source 1: system prompt from `_get_system_prompt(request)`. (services/claude_brain/brain_manager.py:L449-L453)
- Source 2: raw `request.prompt` as user message body. (services/claude_brain/brain_manager.py:L451-L454)
- Source 3: optional JSON dump of `request.context` appended inline to user message. (services/claude_brain/brain_manager.py:L456-L460)

### Truncation/Safety/Control
- Temperature is dynamically reduced for high cognitive load and analysis operations. (services/claude_brain/brain_manager.py:L501-L515)
- Max tokens are adjusted by cognitive load and operation type. (services/claude_brain/brain_manager.py:L517-L529)
- MISSING: explicit context-size guard or field allowlist for `request.context` before JSON append. (services/claude_brain/brain_manager.py:L456-L460)
- MISSING: audit persistence of injected context slices (what/why) for each LLM call. (services/claude_brain/brain_manager.py:L375-L405)

## 2) Dope-Context OpenAI Context Generator

### Injection Site
- `_build_prompt` constructs contextualization prompt including file/module metadata and full chunk content. (services/dope-context/src/context/openai_generator.py:L218-L241)
- Prompt is sent as user message with fixed system instruction. (services/dope-context/src/context/openai_generator.py:L134-L145)

### Source Order
- Source 1: static system role instruction. (services/dope-context/src/context/openai_generator.py:L138-L140)
- Source 2: generated prompt with file path/module/line range and chunk code. (services/dope-context/src/context/openai_generator.py:L230-L238)

### Truncation/Safety/Control
- Response budget is bounded by `max_completion_tokens=200`. (services/dope-context/src/context/openai_generator.py:L146-L148)
- Cache key avoids repeated generation for unchanged chunk context requests. (services/dope-context/src/context/openai_generator.py:L115-L121)
- MISSING: pre-send redaction pass on chunk content before model call. (services/dope-context/src/context/openai_generator.py:L230-L240)

## 3) Dope-Context Claude Context Generator

### Injection Site
- `_build_context_prompt` assembles prompt with location/language/lines/code and strict formatting target. (services/dope-context/src/context/claude_generator.py:L167-L215)
- Prompt is sent as single user message to Claude API. (services/dope-context/src/context/claude_generator.py:L253-L258)

### Source Order
- Source 1: prompt string built from chunk metadata and chunk content. (services/dope-context/src/context/claude_generator.py:L197-L206)
- Source 2: no additional context layers added after prompt construction. (services/dope-context/src/context/claude_generator.py:L253-L258)

### Truncation/Safety/Control
- Deterministic call settings: `temperature=0.0`, `max_tokens=150`. (services/dope-context/src/context/claude_generator.py:L255-L257)
- TTL cache prevents repeated re-generation. (services/dope-context/src/context/claude_generator.py:L142-L151)
- MISSING: lane/persona-based opt-in injection policy controls in this call path. (services/dope-context/src/context/claude_generator.py:L167-L215)

## 4) Dope-Context Grok/OpenRouter Context Generator

### Injection Site
- Prompt is assembled inline with file path/function context and chunk snippet. (services/dope-context/src/context/grok_generator.py:L95-L101)
- Prompt is sent as `messages=[{"role": "user", "content": prompt}]` to OpenRouter chat completions. (services/dope-context/src/context/grok_generator.py:L115-L118)

### Source Order
- Source 1: inline composed prompt (single user message). (services/dope-context/src/context/grok_generator.py:L95-L101)
- Source 2: no additional memory/context attachment layer. (services/dope-context/src/context/grok_generator.py:L115-L121)

### Truncation/Safety/Control
- Input truncation: chunk content is clipped to first 2000 characters in prompt. (services/dope-context/src/context/grok_generator.py:L98-L99)
- Output cap: `max_tokens=200`. (services/dope-context/src/context/grok_generator.py:L120-L121)
- MISSING: structured audit record for what was injected. (services/dope-context/src/context/grok_generator.py:L95-L121)

## 5) Non-LLM Context Injection Paths (Relevant for Architecture)
- Dopecon-bridge middleware hydrates request context from ConPort token and persists context deltas after request processing; this is request-context injection, not LLM prompt injection. (services/dopecon-bridge/main.py:L628-L661)
- Role/persona activation sets environment fields (`DOPEMUX_AGENT_ROLE`, `DOPEMUX_ROLE_ATTENTION_STATE`, etc.), but no direct binding to LLM context injection policies is present. (src/dopemux/roles/catalog.py:L298-L313)

## 6) Injection Gaps Against Target Requirements
- MISSING: explicit per-lane opt-in switch at each LLM injection site (`brain_manager`, dope-context generators). (services/claude_brain/brain_manager.py:L456-L460)
- MISSING: deterministic-first retrieval-to-injection pipeline that prefers chronicle deterministic recall before vector/semantic context in LLM calls. (services/working-memory-assistant/chronicle/store.py:L313-L315)
- MISSING: append-only audit log for injected fragments with reason codes and source entry IDs. (services/working-memory-assistant/chronicle/schema.sql:L149-L152)

