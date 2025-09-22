FROM node:20-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install claude-context MCP server globally
RUN npm install -g @zilliz/claude-context-mcp@latest

# Copy wrapper script
COPY wrapper.js /app/wrapper.js

EXPOSE 3007

CMD ["node", "/app/wrapper.js"]