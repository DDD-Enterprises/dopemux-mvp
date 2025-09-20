// Context7 MCP Server for Dopemux
const { spawn } = require('child_process');
const http = require('http');

const port = process.env.MCP_SERVER_PORT || 3002;

// Start the actual Context7 MCP server as a subprocess
const mcpProcess = spawn('npx', ['-y', '@upstash/context7-mcp'], {
  stdio: ['pipe', 'pipe', 'pipe'],
  env: {
    ...process.env,
    CONTEXT7_API_KEY: process.env.CONTEXT7_API_KEY,
    CONTEXT7_ENDPOINT: process.env.CONTEXT7_ENDPOINT
  }
});

// HTTP wrapper for health checks and Docker compatibility
const server = http.createServer((req, res) => {
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      mcp_process_running: !mcpProcess.killed
    }));
  } else {
    res.writeHead(404);
    res.end('Not Found');
  }
});

server.listen(port, '0.0.0.0', () => {
  console.log(`🔍 Context7 MCP Server wrapper running on port ${port}`);
});

mcpProcess.stdout.on('data', (data) => {
  console.log(`Context7 MCP: ${data}`);
});

mcpProcess.stderr.on('data', (data) => {
  console.error(`Context7 MCP Error: ${data}`);
});

mcpProcess.on('close', (code) => {
  console.log(`Context7 MCP process exited with code ${code}`);
  process.exit(code);
});