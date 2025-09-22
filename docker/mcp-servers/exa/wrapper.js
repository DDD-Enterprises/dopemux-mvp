const { spawn } = require('child_process');
const http = require('http');

const port = process.env.MCP_SERVER_PORT || 3008;

console.log('🔍 Starting EXA MCP Server...');

const mcpProcess = spawn('npx', ['exa-mcp'], {
  stdio: ['pipe', 'pipe', 'pipe'],
  env: {
    ...process.env,
    EXA_API_KEY: process.env.EXA_API_KEY
  }
});

const server = http.createServer((req, res) => {
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'healthy',
      mcp_running: !mcpProcess.killed,
      has_api_key: !!process.env.EXA_API_KEY
    }));
  } else {
    res.writeHead(404);
    res.end('Not Found');
  }
});

mcpProcess.stdout.on('data', data => {
  console.log('[EXA OUT]', data.toString().trim());
});

mcpProcess.stderr.on('data', data => {
  console.error('[EXA ERR]', data.toString().trim());
});

mcpProcess.on('exit', (code) => {
  console.log(`[EXA] Process exited with code ${code}`);
});

server.listen(port, '0.0.0.0', () => {
  console.log(`🔍 EXA MCP Server wrapper running on port ${port}`);
});