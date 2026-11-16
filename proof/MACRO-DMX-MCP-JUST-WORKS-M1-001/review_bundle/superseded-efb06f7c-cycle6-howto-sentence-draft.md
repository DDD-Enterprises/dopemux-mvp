# Draft replacement for docs/02-how-to/mcp-setup-other-repos.md (Cleanup paragraph, ~line 287) — Grok low F1 at 380c2c52c

Current: "Such a dir is left while a detached image build may still be running, and automatic runs see it only while the
runtime registry lists at least one instance (no run sees it while that registry file is missing or unreadable)."

Replacement: "Such a dir is left while a detached image build may still be running. Automatic runs reach it even when the
runtime registry lists no instance: an empty, readable registry still scans the launcher-marked runtime dirs, while a
missing or unreadable registry file still reaps nothing."

Also check the same paragraph in `.claude/claude.md` / AGENTS.md §12 for the same claim (grep "lists at least one instance").
Owner decision pending: accept as a recorded low (follow-up docs fix) vs a docs-only micro-cycle (re-freeze + both routes).
