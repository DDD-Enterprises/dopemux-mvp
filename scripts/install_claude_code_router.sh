#!/usr/bin/env bash
# Lightweight installer for Claude Code Router within Dopemux environments.

set -euo pipefail

command -v node >/dev/null 2>&1 || {
  echo "Error: Node.js is required. Install Node.js >= 18 and re-run." >&2
  exit 1
}

command -v npm >/dev/null 2>&1 || {
  echo "Error: npm is required but was not found in PATH." >&2
  exit 1
}

echo "==> Installing Claude Code CLI dependencies"
npm install -g @anthropic-ai/claude-code @musistudio/claude-code-router

echo "==> Verifying installation"
claude --version || echo "Warning: claude CLI not detected; ensure it is on PATH."
ccr --version

echo "\nClaude Code Router is installed. Dopemux will provision per-instance configs automatically when you run 'dopemux start'."
