#!/usr/bin/env node

const { spawn } = require('child_process');

// Re-index codebase with VoyageAI voyage-code-3 + rerank-2.5
async function reindexWithReranker() {
    console.log('🚀 Re-indexing codebase with VoyageAI voyage-code-3 + rerank-2.5...');

    const mcpProcess = spawn('npx', ['@zilliz/claude-context-mcp@latest'], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: {
            ...process.env,
            EMBEDDING_PROVIDER: 'VoyageAI',
            EMBEDDING_MODEL: 'voyage-code-3',
            VOYAGEAI_API_KEY: process.env.VOYAGEAI_API_KEY,
            VOYAGEAI_RERANK_MODEL: 'rerank-2.5',
            MILVUS_ADDRESS: 'milvus:19530',
            MILVUS_TOKEN: ''
        }
    });

    const indexRequest = {
        jsonrpc: "2.0",
        id: 1,
        method: "tools/call",
        params: {
            name: "index_codebase",
            arguments: {
                path: "/workspace/dopemux-mvp",
                force: true,
                splitter: "ast",
                customExtensions: [".md", ".yml", ".yaml", ".json"],
                ignorePatterns: [
                    "node_modules/**",
                    ".git/**",
                    "*.log",
                    ".venv/**",
                    "__pycache__/**",
                    "*.pyc"
                ]
            }
        }
    };

    console.log('📤 Sending indexing request with rerank-2.5...');
    mcpProcess.stdin.write(JSON.stringify(indexRequest) + '\n');

    let hasOutput = false;
    let totalProgress = 0;

    mcpProcess.stdout.on('data', (data) => {
        hasOutput = true;
        const response = data.toString().trim();
        if (response) {
            try {
                const parsed = JSON.parse(response);
                if (parsed.result?.content?.[0]?.text) {
                    const resultText = parsed.result.content[0].text;
                    console.log('📥 Response:', resultText);
                } else {
                    console.log('📥 Status:', JSON.stringify(parsed, null, 2));
                }
            } catch (e) {
                console.log('📥 Raw:', response);
            }
        }
    });

    mcpProcess.stderr.on('data', (data) => {
        hasOutput = true;
        const log = data.toString().trim();

        // Track progress
        if (log.includes('Progress:') && log.includes('files')) {
            const progressMatch = log.match(/(\d+)\/(\d+) files/);
            if (progressMatch) {
                const current = parseInt(progressMatch[1]);
                const total = parseInt(progressMatch[2]);
                const percent = Math.round((current / total) * 100);
                if (percent > totalProgress) {
                    totalProgress = percent;
                    console.log(`🔄 Progress: ${percent}% (${current}/${total} files)`);
                }
            }
        }

        // Show important logs
        if (log.includes('VoyageAI') || log.includes('rerank') || log.includes('embedding') ||
            log.includes('Dimension') || log.includes('✅') || log.includes('❌') ||
            log.includes('completed') || log.includes('chunks')) {
            console.log('🔍 Log:', log);
        }
    });

    mcpProcess.on('close', (code) => {
        console.log(`🏁 Indexing completed with code ${code}`);
        if (!hasOutput) {
            console.log('⚠️ No output received - check container logs');
        }
    });

    // Wait for indexing to complete
    setTimeout(() => {
        if (totalProgress < 100) {
            console.log(`⏰ Timeout reached at ${totalProgress}% progress. Check if indexing continues...`);
        } else {
            console.log('✅ Indexing completed successfully with VoyageAI rerank-2.5!');
        }
        mcpProcess.kill('SIGTERM');
    }, 300000); // 5 minutes
}

reindexWithReranker().catch(console.error);