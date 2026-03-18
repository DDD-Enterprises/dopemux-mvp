---
id: L2_OUTLINE
title: L2 Outline
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-18'
last_review: '2026-03-18'
next_review: '2026-06-16'
prelude: L2 Outline (explanation) for dopemux documentation and developer workflows.
---
# L2 Outline (Auto-assembled)

## block-0001 — Skip to content

## block-0002 — Assumptions

## block-0003 — Introduction: In today’s fast-paced tech landscape, developers are increasingly leveraging AI-powered tools to boost productivity and creativity. As a cloud/local AI software archi

## block-0004 — A efficient command-line environment is essential for both local and cloud development. Here are some CLI tools and workflows to supercharge your productivity on a MacBook Pro (App

## block-0005 — Your choice of IDE or editor will anchor your daily development experience. Visual Studio Code (VS Code) is an excellent starting point given its popularity and rich ecosystem. It’

## block-0006 — Effective collaboration and code management are crucial for an architect and product designer. Here are recommendations to streamline your workflow with GitHub and team tools:

## block-0007 — With your focus on Python and JavaScript and the need to build two backend systems and web apps, you’ll likely be working across a full-stack application. Here’s a recommended stac

## block-0008 — To build AI-powered features (like natural language query, assistants with memory, etc.), you should incorporate libraries that simplify LLM integration and enable “vector memory”

## block-0009 — Environment Setup Plan (Definition of Done)

## block-0010 — Finally, to ensure everything is set up for success, here’s a step-by-step plan (Definition of Done) for your project environment. Following these steps will yield a highly effecti
- Links: 1

## block-0011 — Definition of Done: At this point, your development environment should be fully operational. You can consider the setup complete when you can:

## block-0012 — README_PROJECT.md
- # README_PROJECT.md

## block-0013 — ARCHITECTURE.md
- # ARCHITECTURE.md

## block-0014 — ADR-0001.md
- # ADR-0001.md

## block-0015 — ADR-0002.md
- # ADR-0002.md

## block-0016 — INTERFACES.md
- # INTERFACES.md

## block-0017 — ACCEPTANCE_CRITERIA.md
- # ACCEPTANCE_CRITERIA.md

## block-0018 — NON_FUNCTIONAL.md
- # NON_FUNCTIONAL.md

## block-0019 — RISK_REGISTER.md
- # RISK_REGISTER.md

## block-0020 — REFERENCES.md
- # REFERENCES.md

## block-0021 — NEXT.md
- # NEXT.md

## block-0022 — Local Forensic Chat Analysis Pipeline Design (DØPEMÜX System)
- # Local Forensic Chat Analysis Pipeline Design (DØPEMÜX System)

## block-0023 — Overview
- ## Overview

## block-0024 — Phase 1: Message Ingestion & Chunking
- ## Phase 1: Message Ingestion & Chunking

## block-0025 — **Output of Phase 1:** A series of Message Blocks in YAML format (one per message), written to an output file (e.g. `tagged/message_blocks.dmpx`). Each block is a compact YAML snip

## block-0026 — Phase 2: Conversation Unit Assembly
- ## Phase 2: Conversation Unit Assembly

## block-0027 — **Output of Phase 2:** A YAML file (e.g. `outputs/conversation_units.dmpx`) listing each Conversation Unit with its metadata and ledgers. The output is relatively compact – focusin

## block-0028 — Phase 3: Psychological & Dynamics Rollups
- ## Phase 3: Psychological & Dynamics Rollups

## block-0029 — * **Tasteful Roast**: As a final touch, the pipeline appends a lighthearted **“roast”** or tongue-in-cheek advice at the end of the analysis. This is a single witty line that playf

## block-0030 — Phase 4: Forensic Audit & Guardrails
- ## Phase 4: Forensic Audit & Guardrails

## block-0031 — Integration of GPT-5 and File Search
- ## Integration of GPT-5 and File Search

## block-0032 — **Trade-off Summary:** If the chat data is extremely sensitive (e.g., legal or personal matters), leaning local is preferable to avoid cloud exposure. A local M4 MacBook is powerfu

## block-0033 — CLI Entry Point and Configuration
- ## CLI Entry Point and Configuration

## block-0034 — * **Extensibility**: The design allows adding more phases or custom analyses. For instance, one could add a phase for sentiment analysis per message (though tone/mood covers that s

## block-0035 — Design Trade-offs and Rationale
- ## Design Trade-offs and Rationale

## block-0036 — Assumptions: MODE=DESIGN. Local-first. Cloud calls are opt-in. iMessage PDFs vary between text-selectable and image-only. YAML “.dmpx” is the reporting format.

## block-0037 — Local-first; explicit opt-in for cloud tools.

## block-0038 — Sources

## block-0039 — Decision

## block-0040 — iMessage extract 50k messages ≤ 30 s on M-series with local DB copy.

## block-0041 — ARCHITECTURE.md

## block-0042 — Given redacted chunks and --retriever=cloud

## block-0043 — Assumptions: macOS “Tahoe”. One-on-one first. Attachments never sent to cloud. Cloud use gated behind redaction.

## block-0044 — privacy.redaction.threshold_default=0.995

## block-0045 — Assumptions: Cloud is optional. Pre-cloud Policy Shield is mandatory. Default coverage threshold 0.995. Opaque tokens for illicit/banned topics. Speakers pseudonymized (ME, CN_<id6

## block-0046 — Redacted context packer (pre-cloud).

## block-0047 — Research completed in 3m · 13 sources · 50 searches

## block-0048 — Sources

## block-0049 — ChatGPT can make mistakes. Check important info. See Cookie Preferences.

## block-0050 — WhatsApp Chat | ️ LangChain
- Links: 9

## block-0051 — Assumptions: macOS “Tahoe”, Apple Silicon. One-on-one chats first. Attachments optional. Cloud LLMs are allowed only after redaction. Local vector memory is primary.

## block-0052 — Thought for 24s

## block-0053 — user-extensible; never leaves device
- # user-extensible; never leaves device

## block-0054 — Thought for 27s

## block-0055 — Assumptions: one-on-one first; macOS Tahoe; Policy Shield stands (pseudonyms, opaque tokens, 0.995 threshold). Coarse labels are cloud-safe. Fine labels are local-only.

## block-0056 — Thought for 10s

## block-0057 — Assumptions: one-on-one first; Policy Shield still mandatory; coarse (cloud-safe) vs fine (local-only) split preserved.

## block-0058 — Thought for 22s

## block-0059 — Adult, consensual context. Any minor/CSAM indicators are hard-fail (block cloud).

## block-0060 — Thought for 15s
