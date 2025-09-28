# Task Master AI MCP Server
# Node.js-based AI task management and PRD processing
# Source: https://github.com/eyaltoledano/claude-task-master
FROM node:18-alpine

# Install system dependencies
RUN apk add --no-cache \
    git \
    curl \
    bash

# Set up working directory
WORKDIR /app

# Clone the claude-task-master repository
RUN git clone https://github.com/eyaltoledano/claude-task-master.git . \
    && npm install --production

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Set up environment
ENV NODE_ENV=production
ENV MCP_SERVER_PORT=3005
ENV MCP_TRANSPORT=stdio

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${MCP_SERVER_PORT}/health || nc -z localhost ${MCP_SERVER_PORT} || exit 1

# Expose MCP server port
EXPOSE 3005

# Labels for Docker metadata
LABEL mcp.role="workflow"
LABEL mcp.priority="medium"
LABEL mcp.description="AI-powered task management and PRD processing"
LABEL mcp.source="https://github.com/eyaltoledano/claude-task-master"

# Run the MCP server
CMD ["npm", "run", "mcp"]