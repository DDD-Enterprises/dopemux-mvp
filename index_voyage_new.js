#!/usr/bin/env node

const { spawn } = require('child_process');

// Index codebase with new VoyageAI API key
async function indexWithNewVoyageAI() {
    console.log('🚀 Indexing codebase with VoyageAI voyage-code-3 (new API key)...');

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

    console.log('📤 Sending indexing request...');
    mcpProcess.stdin.write(JSON.stringify(indexRequest) + '\n');

    let hasOutput = false;
    let totalProgress = 0;

    mcpProcess.stdout.on('data', (data) => {
        hasOutput = true;
        const response = data.toString().trim();
        if (response) {
            try {
                const parsed = JSON.parse(response);
                console.log('📥 Response:', JSON.stringify(parsed.result?.content?.[0]?.text || parsed, null, 2));
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
        if (log.includes('VoyageAI') || log.includes('voyage-code') || log.includes('embedding') ||
            log.includes('Dimension') || log.includes('✅') || log.includes('❌') ||
            log.includes('completed') || log.includes('chunks')) {
            console.log('🔍 Log:', log);
        }
    });

    mcpProcess.on('close', (code) => {
        console.log(`🏁 Process exited with code ${code}`);
        if (!hasOutput) {
            console.log('⚠️ No output received - check container logs');
        }
    });

    // Wait longer for indexing to complete
    setTimeout(() => {
        if (totalProgress < 100) {
            console.log(`⏰ Timeout reached at ${totalProgress}% progress. Indexing may continue in background...`);
        } else {
            console.log('✅ Indexing completed successfully!');
        }
        mcpProcess.kill('SIGTERM');
    }, 240000); // 4 minutes
}

indexWithNewVoyageAI().catch(console.error);