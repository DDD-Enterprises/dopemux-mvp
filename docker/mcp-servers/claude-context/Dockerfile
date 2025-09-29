FROM node:20-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# No additional npm packages needed

# Install uv for Python package management (uvx is provided by uv)
RUN pip3 install --break-system-packages uv

WORKDIR /app

# Copy the claude-context source files
COPY . /app/

# Make wrapper executable
RUN chmod +x /app/wrapper.js

EXPOSE 3007

# Run the wrapper which handles MCP server startup
CMD ["node", "/app/wrapper.js"]