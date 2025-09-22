const { spawn } = require('child_process');
const http = require('http');

const port = process.env.MCP_SERVER_PORT || 3007;

console.log('🔍 Starting Claude Context MCP Server...');

const mcpProcess = spawn('npx', ['@zilliz/claude-context-mcp@latest'], {
  stdio: ['pipe', 'pipe', 'pipe'],
  env: {
    ...process.env,
    EMBEDDING_PROVIDER: process.env.EMBEDDING_PROVIDER,
    EMBEDDING_MODEL: process.env.EMBEDDING_MODEL,
    OPENAI_API_KEY: process.env.OPENAI_API_KEY,
    VOYAGEAI_API_KEY: process.env.VOYAGEAI_API_KEY,
    GEMINI_API_KEY: process.env.GEMINI_API_KEY,
    MILVUS_ADDRESS: process.env.MILVUS_ADDRESS,
    MILVUS_TOKEN: process.env.MILVUS_TOKEN
  }
});

const server = http.createServer((req, res) => {
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'healthy',
      mcp_running: !mcpProcess.killed,
      embedding_provider: process.env.EMBEDDING_PROVIDER,
      embedding_model: process.env.EMBEDDING_MODEL,
      has_openai_key: !!process.env.OPENAI_API_KEY,
      has_voyageai_key: !!process.env.VOYAGEAI_API_KEY,
      milvus_address: process.env.MILVUS_ADDRESS
    }));
  } else {
    res.writeHead(404);
    res.end('Not Found');
  }
});

mcpProcess.stdout.on('data', data => {
  console.log('[CLAUDE-CONTEXT OUT]', data.toString().trim());
});

mcpProcess.stderr.on('data', data => {
  console.error('[CLAUDE-CONTEXT ERR]', data.toString().trim());
});

mcpProcess.on('exit', (code) => {
  console.log(`[CLAUDE-CONTEXT] Process exited with code ${code}`);
});

server.listen(port, '0.0.0.0', () => {
  console.log(`🔍 Claude Context MCP Server wrapper running on port ${port}`);
});