---
id: OPEN_QUESTIONS
title: Open Questions
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-18'
last_review: '2026-03-18'
next_review: '2026-06-16'
prelude: Open Questions (explanation) for dopemux documentation and developer workflows.
---
# Open Questions (verbatim)

- (ASSISTANT) Input examples: do we have representative iMessage PDFs, Instagram JSON exports, WhatsApp exports, and mixed TXT to design against?

- (ASSISTANT) Any privacy constraints beyond local-first (retention, redaction rules, auditability)?

- (ASSISTANT) Expected scale: number of conversations, messages, and typical query latency target?

- (ASSISTANT) Do we need an HTTP API now or only CLI for the first milestone?

- (ASSISTANT) Which local model host do you prefer for offline LLMs: Ollama or llama.cpp?

- (ASSISTANT) Do we ship an HTTP API in M1 or defer to M2?

- (ASSISTANT) Do you want LangChain or a minimal in-house orchestration layer for RAG and tools?

- (ASSISTANT) Preferred local LLM host: Ollama or llama.cpp?

- (ASSISTANT) Which AI coding assistant do you want in repo docs by default: Copilot, Codeium, Cursor, Aider, or a mix?

- (ASSISTANT) Any explicit privacy redaction rules beyond “sanitize contraband, PII before remote calls”?

- (ASSISTANT) Corpus size target for perf tuning (messages, conversations)?

- (USER) is this a better approach?

- (ASSISTANT) Open questions: Any hard privacy constraints that forbid uploading transcripts to OpenAI at all? Are we okay paying extra for hosted File Search if enabled? Do we need vision parsing without cloud?

- (ASSISTANT) Are you expecting to extract messages directly from the chat.db SQLite database located in ~/Library/Messages on macOS?

- (ASSISTANT) Should the extraction include attachments (images, audio, etc.), or just text messages?

- (ASSISTANT) Are you interested in group chats as well or only one-on-one conversations?

- (ASSISTANT) Should archived or deleted messages be included if they’re available?

- (ASSISTANT) Do you want the extracted messages to be transformed directly into the YAML-based Message Block schema you described earlier (with fields like sender_id, tone, inferred_meaning, etc.)?

- (ASSISTANT) Or would you like a lighter format first (e.g., structured JSON or CSV) before downstream transformation?

- (ASSISTANT) Do you want to stick with a local solution like Chroma, or are you open to a hybrid setup (e.g., local Chroma with optional cloud embedding)?

- (ASSISTANT) [2023-05-01 10:00] Alice: Hi, how are you?

- (ASSISTANT) Do we need edits and unsend tracking in v1 for iMessage and Instagram, or log them as system events for now?

- (ASSISTANT) When I run chatx index and chatx query "What did we decide about rent?" --contact "<key>"

- (ASSISTANT) Additional sensitive categories to include by default (e.g., third-party names)?

- (ASSISTANT) Default coverage threshold (0.999 vs 0.995)?

- (ASSISTANT) [2024-11-05T18:23] CN_4P6Z: ok. what will you change?

- (ASSISTANT) Are you planning to run this fully locally or are you open to some cloud-based components (e.g. for LLM inference or heavier compute)?

- (ASSISTANT) Which LLMs are you considering using (e.g. GPT-4, Claude, Mistral, LLaMA) and do you have local inference in mind?

- (ASSISTANT) Do you want to prioritize transparency and extensibility over speed or UX?

- (ASSISTANT) . This approach significantly improves factual accuracy and allows the model to cite specifics from the chats. In practice, the prompt fed to the LLM could be something like: "Given the following excerpts from conversations between [You] and [Alice], answer the question..." and then include the retrieved messages (perhaps with some formatting or summarization if needed to fit the context window). The LLM can then produce an answer that references the content. RAG is especially useful for pinpoint questions like "How often does Bob apologize in our chats?" – the retrieval step might pull all instances of "sorry" or apologetic language, and the LLM can summarize from that evidence. This method was illustrated by a user-facing example where an AI (ChatGPT) was given an entire chat history and asked relationship questions. Rather than responding abstractly, it scanned the logs for evidence and provided answers with supporting quotes

- (ASSISTANT) Question Answering about the Relationship: Users can query things like "Does X person love me?" or "Who puts more effort into the conversations?" – and the LLM can answer based on the chats. In the Business Insider example, after analyzing ~23k messages, ChatGPT was able to answer who cared more in the relationship by even quantifying message counts and asking behavior (it found one person initiated contact far more often)

- (ASSISTANT) Simulating "What-If" Scenarios: This is a more advanced use-case, but the LLM could simulate different outcomes if the user had said something differently or wants to explore a hypothetical scenario. For instance, "What if I had not apologized in that argument? How might the conversation have continued?" Using the chat context, the LLM can role-play the rest of the conversation under that premise. Research prototypes like ConflictLens have used LLMs to let users rewrite parts of a conversation and then simulate how the partner might respond, as a form of communication training

- (ASSISTANT) . This approach significantly improves factual accuracy and allows the model to cite specifics from the chats. In practice, the prompt fed to the LLM could be something like: "Given the following excerpts from conversations between [You] and [Alice], answer the question..." and then include the retrieved messages (perhaps with some formatting or summarization if needed to fit the context window). The LLM can then produce an answer that references the content. RAG is especially useful for pinpoint questions like "How often does Bob apologize in our chats?" – the retrieval step might pull all instances of "sorry" or apologetic language, and the LLM can summarize from that evidence. This method was illustrated by a user-facing example where an AI (ChatGPT) was given an entire chat history and asked relationship questions. Rather than responding abstractly, it scanned the logs for evidence and provided answers with supporting quotes

- (ASSISTANT) Question Answering about the Relationship: Users can query things like "Does X person love me?" or "Who puts more effort into the conversations?" – and the LLM can answer based on the chats. In the Business Insider example, after analyzing ~23k messages, ChatGPT was able to answer who cared more in the relationship by even quantifying message counts and asking behavior (it found one person initiated contact far more often)

- (ASSISTANT) Simulating "What-If" Scenarios: This is a more advanced use-case, but the LLM could simulate different outcomes if the user had said something differently or wants to explore a hypothetical scenario. For instance, "What if I had not apologized in that argument? How might the conversation have continued?" Using the chat context, the LLM can role-play the rest of the conversation under that premise. Research prototypes like ConflictLens have used LLMs to let users rewrite parts of a conversation and then simulate how the partner might respond, as a form of communication training

- (ASSISTANT) chatx query "What changed after June?" --contact "<key>" --k 32 --retriever local|cloud --allow-cloud

- (ASSISTANT) chatx simulate "What if I had declined on 2024-07-12?" --contact "<key>" --allow-cloud

- (ASSISTANT) chatx query "How has intimacy changed and what influenced it?" \
