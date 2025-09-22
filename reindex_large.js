#!/usr/bin/env node

const { spawn } = require('child_process');

// Re-index codebase with OpenAI text-embedding-3-large (much better quality)
async function reindexWithLargeModel() {
    console.log('🚀 Re-indexing codebase with OpenAI text-embedding-3-large...');

    const mcpProcess = spawn('npx', ['@zilliz/claude-context-mcp@latest'], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: {
            ...process.env,
            EMBEDDING_PROVIDER: 'OpenAI',
            EMBEDDING_MODEL: 'text-embedding-3-large',
            OPENAI_API_KEY: process.env.OPENAI_API_KEY,
            MILVUS_ADDRESS: 'milvus:19530',
            MILVUS_TOKEN: ''
        }
    });

    // Force re-indexing request to replace old embeddings with better quality
    const reindexRequest = {
        jsonrpc: "2.0",
        id: 1,
        method: "tools/call",
        params: {
            name: "index_codebase",
            arguments: {
                path: "/workspace/dopemux-mvp",
                force: true, // Force re-indexing with better model
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

    console.log('📤 Sending force re-indexing request with text-embedding-3-large...');
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
        if (log.includes('OpenAI') || log.includes('text-embedding-3-large') || log.includes('Progress') || log.includes('embedding') || log.includes('Dimension: 3072')) {
            console.log('🔍 OpenAI Large Log:', log);
        }
    });

    mcpProcess.on('close', (code) => {
        console.log(`🏁 Re-indexing process exited with code ${code}`);
    });

    // Give it time to complete re-indexing
    setTimeout(() => {
        console.log('⏰ Re-indexing initiated with text-embedding-3-large, may continue in background...');
        mcpProcess.kill('SIGTERM');
    }, 60000); // 60 seconds
}

reindexWithLargeModel().catch(console.error);