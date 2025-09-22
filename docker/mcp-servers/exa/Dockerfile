FROM node:20-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install exa-mcp globally
RUN npm install -g exa-mcp

# Create wrapper script
COPY wrapper.js /app/wrapper.js

EXPOSE 3008

CMD ["node", "/app/wrapper.js"]