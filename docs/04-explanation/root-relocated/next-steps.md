---
id: NEXT_STEPS
title: Next Steps
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-20'
last_review: '2026-03-20'
next_review: '2026-06-18'
prelude: Next Steps (explanation) for dopemux documentation and developer workflows.
---
# Dopemux: What's Next? 🚀

Now that the installation process is modular, secure, and resilient, we are entering the **Optimization & Expansion** phase. Below are the high-priority workstreams.

## 1. Intelligence & Context (The Truth Engine)
- [ ] **Phase S Synthesis Implementation**: Fully implement the LLM-driven synthesis in `src/dopemux/extractor/runner.py` using LiteLLM.
- [ ] **Cross-Workspace Context**: Enable ConPort to seamlessly bridge data between independent worktrees using the "Mental Map" protocol.
- [ ] **Real-time Truth Sync**: Implement a file watcher that triggers lightweight "Truth Updates" on save, keeping the context window perfect.

## 2. Developer Experience (UX/UI Flair)
- [ ] **Interactive Dashboard**: Build a TUI (Terminal User Interface) dashboard using `textual` or `rich.live` to monitor all 17+ containers.
- [ ] **Voice-to-Task Integration**: Hook up the Desktop-Commander to allow creating Leantime tickets via voice.
- [ ] **Hyper-Themed Alarms**: Implement ADHD-friendly productivity timers (Pomodoro+) with neon-mint visual feedback.

## 3. Modular Scale
- [ ] **Remote MCP Hosting**: Allow Dopemux to connect to MCP servers running on remote high-spec machines to save local RAM.
- [ ] **Provider Ladder Optimization**: Automatically switch between GPT-4o, Claude 3.5 Sonnet, and local Llama 3 based on task complexity and budget.

## 4. Stability & Hardening
- [ ] **Automated Rollback Tests**: Add CI tests that simulate installation failures to verify the `on_error` trap.
- [ ] **Telemetry (Opt-in)**: Implement privacy-first telemetry to track common container startup failures and improve the "Pre-flight" resource checks.

---

## 🗺️ Execution Roadmap

### Stage 1: The Truth Pack (Now)
Focus on `dopemux extractor trace` and ensuring the repository "Ground Truth" is flawlessly delivered to Claude Code.

### Stage 2: The Cockpit (Next Month)
Transition from CLI-only to a full terminal dashboard experience.

### Stage 3: The Global Plane (Q3 2026)
Expanding Dopemux from a local tool to a team-wide cognitive coordination platform.
