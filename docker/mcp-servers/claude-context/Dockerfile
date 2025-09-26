FROM node:20-slim

WORKDIR /app

# Install system dependencies (Node.js already available in base image)
RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install uv for Python package management (uvx is provided by uv)
RUN pip3 install --break-system-packages uv

# Copy wrapper script
COPY wrapper.js /app/wrapper.js

EXPOSE 3007

CMD ["node", "/app/wrapper.js"]