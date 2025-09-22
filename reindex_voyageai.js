#!/usr/bin/env node

const { spawn } = require('child_process');

// Re-index codebase with VoyageAI voyage-code-3 embeddings
async function reindexWithVoyageAI() {
    console.log('🚀 Re-indexing codebase with VoyageAI voyage-code-3...');

    const mcpProcess = spawn('npx', ['@zilliz/claude-context-mcp@latest'], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: {
            ...process.env,
            EMBEDDING_PROVIDER: 'VoyageAI',
            EMBEDDING_MODEL: 'voyage-code-3',
            VOYAGEAI_API_KEY: process.env.VOYAGEAI_API_KEY,
            MILVUS_ADDRESS: 'milvus:19530',
            MILVUS_TOKEN: ''
        }
    });

    // Force re-indexing request to replace OpenAI embeddings with VoyageAI
    const reindexRequest = {
        jsonrpc: "2.0",
        id: 1,
        method: "tools/call",
        params: {
            name: "index_codebase",
            arguments: {
                path: "/workspace/dopemux-mvp",
                force: true, // Force re-indexing to replace old embeddings
                splitter: "ast",
                customExtensions: [".md", ".yml", ".yaml", ".json"],
                ignorePatterns: [
                    "node_modules/**",
                    ".git/**",
                    "*.log",
                    ".venv/**",
                    "__pycache__/**",
                    "*.pyc",
                    ".coverage",
                    ".pytest_cache/**",
                    "htmlcov/**"
                ]
            }
        }
    };

    console.log('📤 Sending force re-indexing request with VoyageAI...');
    mcpProcess.stdin.write(JSON.stringify(reindexRequest) + '\n');

    // Handle responses
    mcpProcess.stdout.on('data', (data) => {
        const response = data.toString().trim();
        if (response) {
            try {
                const parsed = JSON.parse(response);
                console.log('📥 MCP Response:', JSON.stringify(parsed, null, 2));
            } catch (e) {
                console.log('📥 Raw Response:', response);
            }
        }
    });

    mcpProcess.stderr.on('data', (data) => {
        const log = data.toString().trim();
        if (log.includes('VoyageAI') || log.includes('voyage-code') || log.includes('Progress') || log.includes('embedding')) {
            console.log('🔍 VoyageAI Log:', log);
        }
    });

    mcpProcess.on('close', (code) => {
        console.log(`🏁 Re-indexing process exited with code ${code}`);
    });

    // Give it time to complete re-indexing
    setTimeout(() => {
        console.log('⏰ Re-indexing initiated with VoyageAI, may continue in background...');
        mcpProcess.kill('SIGTERM');
    }, 60000); // 60 seconds
}

reindexWithVoyageAI().catch(console.error);