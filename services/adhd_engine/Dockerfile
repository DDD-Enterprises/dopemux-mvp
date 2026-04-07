#syntax=docker/dockerfile:1

##########
# builder
##########
# TODO: Upgrade to dhi.io/python:3.11-alpine3.21-dev after `docker login dhi.io`
FROM python:3.11-alpine3.21 AS builder
WORKDIR /app

# System deps for wheels that need compilation
# Keep minimal; remove what you don't need
RUN apk add --no-cache build-base gcc musl-dev libffi-dev openssl-dev curl

# Copy dependency manifests first for better caching
COPY pyproject.toml /app/pyproject.toml
COPY src/dopemux/__init__.py /app/src/dopemux/__init__.py
RUN python -m venv /app/venv && \
    /app/venv/bin/pip install --no-cache-dir /app/.[services]

# Copy code + shared libs (relative to root build context)
COPY services/adhd_engine /app/services/adhd_engine
COPY services/adhd_engine/mcp_stdio.py /app/mcp_stdio.py
COPY services/shared /app/services/shared
# Note: src/dopemux/__init__.py was already copied above
COPY src/dopemux /app/src/dopemux
# Copy repo root shared/ for monitoring module
COPY shared /app/shared

# Make sure services is a proper package
RUN touch /app/services/__init__.py

##########
# runtime
##########
# TODO: Upgrade to dhi.io/python:3.11-alpine3.21 after `docker login dhi.io`
FROM python:3.11-alpine3.21
WORKDIR /app

# Install curl for healthchecks (minimal runtime dep)
RUN apk add --no-cache curl

# DHI runtime may be non-root by default; ensure files are readable
COPY --from=builder /app/venv /app/venv
COPY --from=builder /app/services /app/services
COPY --from=builder /app/src /app/src
COPY --from=builder /app/shared /app/shared
COPY --from=builder /app/mcp_stdio.py /app/mcp_stdio.py
ENV PATH="/app/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/src \
    API_PORT=8095

# Expose API port (8095 for ADHD Engine)
EXPOSE 8095

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8095/health || exit 1

# Run the ASGI app directly in containers; the module entrypoint enables dev reload.
CMD ["uvicorn", "services.adhd_engine.main:app", "--host", "0.0.0.0", "--port", "8095"]
