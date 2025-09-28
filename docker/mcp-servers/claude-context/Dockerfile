FROM node:20-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install pnpm globally
RUN npm install -g pnpm@latest

# Install uv for Python package management (uvx is provided by uv)
RUN pip3 install --break-system-packages uv

WORKDIR /app

# Copy the entire dope-context source from services submodule
COPY services/claude-context/ /app/

# Install dependencies and build the project
RUN pnpm install

# Build the MCP server package
RUN pnpm build:mcp

# Make the built MCP server executable
RUN chmod +x /app/packages/mcp/dist/index.js

EXPOSE 3007

# Run the MCP server directly via node (stdio transport)
CMD ["node", "/app/packages/mcp/dist/index.js"]