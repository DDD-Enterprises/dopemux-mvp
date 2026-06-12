# LiteLLM Proxy Server for Dopemux
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and upgrade OS packages to pick up security patches
# (openssl CVE-2025-x: fixed in 3.5.6-1~deb13u2)
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    curl \
    netcat-traditional \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*

# Install LiteLLM with all optional dependencies.
# Pin minimum versions to address Docker Scout CVEs:
#   litellm>=1.83.7          (CVE-2026-35030, critical + 3 high)
#   starlette>=0.49.1        (high CVE)
#   python-multipart>=0.0.27 (2 high CVEs)
#   cryptography>=46.0.5     (high CVE)
#   wheel>=0.46.2            (high CVE)
#   mcp>=1.23.0              (high CVE)
RUN pip install --no-cache-dir \
    "litellm[proxy]>=1.83.7" \
    "starlette>=0.49.1" \
    "python-multipart>=0.0.27" \
    "cryptography>=46.0.5" \
    "wheel>=0.46.2" \
    "mcp>=1.23.0" \
    prisma \
    pyyaml

# Copy configuration and entrypoint from root build context
COPY docker/mcp-servers-source/litellm/litellm.config.yaml /app/config.yaml
COPY docker/mcp-servers-source/litellm/entrypoint.sh /app/entrypoint.sh

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 4000

# NOTE: Healthcheck defined in docker-compose.yml to use correct auth token

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
