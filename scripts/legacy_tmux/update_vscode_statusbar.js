#!/usr/bin/env node
// Update VS Code status bar with current LLM model
// This creates a status bar item that shows the current model

const fs = require('fs');
const path = require('path');

const STATE_FILE = '/tmp/dopemux_current_model.txt';
const VSCODE_SETTINGS = path.join(
    process.env.HOME,
    'Library/Application Support/Code/User/settings.json'
);

function getModelDisplay() {
    try {
        if (fs.existsSync(STATE_FILE)) {
            const model = fs.readFileSync(STATE_FILE, 'utf8').trim();
            const displays = {
                'gpt-5-pro': '🧠PRO',
                'gpt-5-codex': '💻CDX',
                'gpt-5-mini': '⚡MIN',
                'gpt-5': '🤖GP5',
                'grok-4-fast': '🚀GRK',
                'grok-code-fast': '⚡GRC',
                'grok-4-fast-reasoning': '🧠GRR',
                'gemini-2-flash': '✨GEM',
                'gemini-2.0-flash-exp': '✨GEM',
                'llama-3.1-405b-instruct': '🦙LMA',
                'claude-sonnet-4.5': '🎭CL4'
            };
            return displays[model] || '🤖' + model.substring(0, 3).toUpperCase();
        }
    } catch (err) {
        // Fallback
    }
    return '🤖GP5';
}

console.log(getModelDisplay());
