#!/usr/bin/env node

const { spawn } = require('child_process');

// Create a simple MCP client to call the index_codebase tool
async function indexCodebase() {
    console.log('🔍 Starting codebase indexing...');

    // Start the claude-context MCP server process
    const mcpProcess = spawn('npx', ['@zilliz/claude-context-mcp@latest'], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: {
            ...process.env,
            EMBEDDING_PROVIDER: 'OpenAI',
            EMBEDDING_MODEL: 'text-embedding-3-small',
            OPENAI_API_KEY: process.env.OPENAI_API_KEY,
            MILVUS_ADDRESS: 'milvus:19530',
            MILVUS_TOKEN: ''
        }
    });

    // Send MCP request to index the codebase
    const indexRequest = {
        jsonrpc: "2.0",
        id: 1,
        method: "tools/call",
        params: {
            name: "index_codebase",
            arguments: {
                path: "/workspace/dopemux-mvp",
                force: false,
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

    console.log('📤 Sending indexing request...');
    mcpProcess.stdin.write(JSON.stringify(indexRequest) + '\n');

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
        console.log('🔍 MCP Log:', data.toString().trim());
    });

    mcpProcess.on('close', (code) => {
        console.log(`🏁 MCP process exited with code ${code}`);
    });

    // Give it some time to process
    setTimeout(() => {
        console.log('⏰ Indexing initiated, process may continue in background...');
        mcpProcess.kill('SIGTERM');
    }, 30000); // 30 seconds
}

indexCodebase().catch(console.error);