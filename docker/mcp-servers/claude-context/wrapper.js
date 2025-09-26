const { spawn } = require('child_process');

const port = process.env.MCP_SERVER_PORT || 3007;

console.log('🔍 Starting Claude Context MCP Server with Zilliz Cloud...');

console.log('Environment variables:');
console.log('- MILVUS_ADDRESS:', process.env.MILVUS_ADDRESS);
console.log('- MILVUS_TOKEN:', process.env.MILVUS_TOKEN ? 'SET (length: ' + process.env.MILVUS_TOKEN.length + ')' : 'NOT SET');
console.log('- VOYAGEAI_API_KEY:', process.env.VOYAGEAI_API_KEY ? 'SET' : 'NOT SET');

// Run the MCP server with HTTP transport via mcp-proxy
console.log('Starting MCP server with HTTP transport...');

const proxyArgs = [
  'mcp-proxy',
  '--transport', 'streamablehttp',
  '--port', port.toString(),
  '--host', '0.0.0.0',
  '--allow-origin', '*',
  '--',
  'npx', '@zilliz/claude-context-mcp@latest'
];

console.log('Running command: uvx', proxyArgs.join(' '));

const mcpServer = spawn('uvx', proxyArgs, {
  stdio: ['inherit', 'inherit', 'inherit'],
  env: {
    ...process.env,
    EMBEDDING_PROVIDER: process.env.EMBEDDING_PROVIDER || 'VoyageAI',
    EMBEDDING_MODEL: process.env.EMBEDDING_MODEL || 'voyage-code-3',
    VOYAGEAI_API_KEY: process.env.VOYAGEAI_API_KEY,
    VOYAGEAI_RERANK_MODEL: process.env.VOYAGEAI_RERANK_MODEL || 'rerank-2.5',
    MILVUS_ADDRESS: process.env.MILVUS_ADDRESS,
    MILVUS_TOKEN: process.env.MILVUS_TOKEN,
    OPENAI_API_KEY: process.env.OPENAI_API_KEY,
    NODE_ENV: 'production'
  }
});

mcpServer.on('exit', (code) => {
  console.log(`🔍 Claude Context MCP Server exited with code ${code}`);
  process.exit(code);
});

mcpServer.on('error', (err) => {
  console.error('🔍 Claude Context MCP Server error:', err);
  process.exit(1);
});

// Handle process termination
process.on('SIGINT', () => {
  console.log('🔍 Claude Context MCP Server shutting down...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('🔍 Claude Context MCP Server shutting down...');
  process.exit(0);
});