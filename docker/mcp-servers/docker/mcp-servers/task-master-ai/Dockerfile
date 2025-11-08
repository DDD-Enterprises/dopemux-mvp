FROM node:20-alpine

WORKDIR /app

RUN apk add --no-cache \
    git \
    curl \
    bash

RUN git clone https://github.com/eyaltoledano/claude-task-master.git . \
    && npm install --production \
    && npm run build

RUN mkdir -p /app/data /app/logs

ENV NODE_ENV=production
ENV MCP_SERVER_PORT=3005
ENV MCP_TRANSPORT=sse

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${MCP_SERVER_PORT}/health || nc -z localhost ${MCP_SERVER_PORT} || exit 1

EXPOSE 3005

LABEL mcp.role="workflow"
LABEL mcp.priority="medium"
LABEL mcp.description="AI-powered task management and PRD processing"
LABEL mcp.source="https://github.com/eyaltoledano/claude-task-master"

CMD ["npm", "run", "mcp-server"]