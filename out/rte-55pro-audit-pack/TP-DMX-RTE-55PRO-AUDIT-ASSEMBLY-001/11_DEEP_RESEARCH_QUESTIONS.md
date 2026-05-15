# Deep Research Questions

These questions are for external/current facts only. Do not ask Deep Research to audit repository runtime; GPT-5.5 Pro should audit repo runtime from uploaded source files.

1. What are current OpenAI structured-output guarantees for GPT-5.x models, including JSON schema strictness, refusal behavior, batch compatibility, and known failure modes?
2. What are current Anthropic, Gemini, xAI, and OpenRouter schema/tool/JSON response-format capabilities, and which fields are passed through versus adapted or ignored?
3. What are current best practices for repairing malformed JSON/schema output without hiding provider failure, including provenance fields, lossy-repair flags, and retry/escalation rules?
4. What are current best practices for LLM-driven repository audit pipelines that separate source truth, generated summaries, proof bundles, and operator-facing reports?
5. What are current prompt-injection and secret-handling risks for automated repo analysis, especially when source inventories include generated artifacts, logs, proofs, env files, or historical run outputs?
6. What multi-model routing patterns are recommended for audit workloads where cost, context, determinism, and evidence quality matter more than conversational quality?
7. What are current context-window, latency, and cost tradeoffs for uploading large code/audit packs into ChatGPT Projects for multi-pass review?
8. What current eval methods can detect hallucinated source claims, unstable ordering, proof overclaiming, and schema drift in LLM-generated audit reports?
9. What current provider-specific caveats apply to batch jobs, file retrieval, and response-format enforcement for long-running audit phases?
10. What current security guidance applies to LLM systems that read code containing secrets, credentials, private paths, customer data, or proof artifacts?
