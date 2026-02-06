---
id: NEON_LAYOUT_ZEN_PLAN
title: Neon_Layout_Zen_Plan
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Neon_Layout_Zen_Plan (explanation) for dopemux documentation and developer
  workflows.
---
# Neon Tmux Dashboard – Zen Ultrathink + Plan Kickoff (Resume Checklist)

Date: 2025-10-28T06:52:26.308Z
Owner: hue
Context files: MONITORING-DESIGN-SPRINT-SUMMARY.md, COMPACT-DASHBOARD-COMPLETE.md

## Agreed Inputs
- Terminal: full height, width as needed; theme: Neon
- Panes: 5–8 (target 7–8)
- Agents: Claude Code orchestrator + Sandbox CLI + 1–2 agent panes (Claude/Codex/Copilot)
- Statusbar: show as many metrics as practical

## Goal
Design a vibrant, metrics‑rich tmux + Typer/Rich layout with:
- Top compact dashboard (1–3 lines)
- Bottom grid for Orchestrator, Sandbox, Agent A, Agent B, Metrics, Logs (+ optional PR/CI and Git/Serena panes)
- Robust data collectors with graceful degradation (2s timeouts, cached fallbacks)

## Target Metrics & Feeds
- ADHD Engine (energy/attention/health), Activity Capture (duration/interruptions)
- LiteLLM (/metrics, spend, latency), MCP health (mcp_server_health_report.sh)
- Docker ps/health, ConPort context, Leantime in-progress/todo/overdue, Serena untracked/abandonment, Git (branch/untracked/stale/unpushed)

## Status Bar (Neon)
Left: session • clock • workspace
Center: Active agents/models (Claude/Codex/Copilot) • continuation id (if any)
Right: LLM spend/latency • MCP healthy N/N • Docker up/err • ADHD energy • branch/untracked/stale • tasks (in‑progress/todo/overdue)

## Layout (Initial Proposal)
- P0 (top): Compact dashboard (live 1–3 lines)
- P1: Orchestrator (Claude Code)
- P2: Sandbox CLI
- P3: Agent A (Claude/Codex)
- P4: Agent B (Copilot/OpenRouter)
- P5: Metrics (LiteLLM/MCP/Docker/ADHD/ConPort/Leantime)
- P6: Logs (tail fused logs)
- P7 (opt): PR/CI summary
- P8 (opt): Git/Serena untracked & abandonment

## Zen Ultrathink Prompt (paste in Claude as /zen:thinkdeeper)
"""
You are designing a Neon-themed, metrics-heavy tmux + Typer/Rich dashboard for Dopemux.
Constraints:
- Terminal full-height, width flexible; target 7–8 panes.
- Top compact dashboard (1–3 lines); bottom grid with Orchestrator, Sandbox, Agent A (Claude/Codex), Agent B (Copilot/OpenRouter), Metrics, Logs, optional PR/CI and Git/Serena panes.
- Status bar shows: active agents/models, LLM spend/latency, MCP health N/N, Docker up/err, ADHD energy, branch/untracked/stale, tasks (in-progress/todo/overdue).
- Data feeds: ADHD Engine, Activity Capture, LiteLLM /metrics, MCP health script, docker ps/health, ConPort, Leantime, Serena untracked/abandonment, Git.
- Performance: <1% idle CPU, <20MB RAM; 1–5s refresh; 2s timeouts & graceful degradation.
Tasks:
1) Propose 3 alternative pane layouts (ASCII), pick one, justify.
2) Define exact metrics and visual encodings (icons/colors/spark-lines) for each pane and status bar.
3) Specify data collection strategy (timeouts, caching, fallback), error states, and update cadence.
4) Provide acceptance criteria and risk mitigations.
Output:
- Final chosen layout (ASCII), full metrics table, color palette (Neon), performance budget, and acceptance checklist.
"""

## Zen Plan Prompt (paste in Claude as /zen:planner)
"""
Plan phased implementation for the chosen Neon layout.
Deliver:
- Phase breakdown (P0–P3): files to create/edit, commands, keybindings.
- Tmux launcher script spec (creates panes/titles/layout, neon status line).
- Typer/Rich dashboard tasks (compact top pane + metrics pane tiles) and data collectors.
- Tests (smoke + timeouts), logging, config (~/.config/dopemux), and docs updates.
- Rollback plan and success metrics.
Output format: numbered tasks with file paths, code stubs, and ready-to-run commands.
"""

## Keybindings (to include in plan)
- Toggle layouts: metrics‑centric vs agent‑centric
- Rotate agents (A/B) • zoom current pane • reload status bar

## Resume Steps After Reset
1) Restart environment: `dopemux tmux start --happy`
2) Open Claude Code; run Ultrathink: `/zen:thinkdeeper` with the prompt above
3) Run Plan: `/zen:planner` with the plan prompt
4) Save outputs to: docs/ZEN_ULTRATHINK_OUTPUT.md and docs/ZEN_PLAN_OUTPUT.md
5) Implement P0 per plan (launcher + status bar + compact dashboard live)

Notes: Prefer externalized config; ensure graceful fallbacks when services are down; keep refresh lightweight.
