# syntax=docker/dockerfile:1

# ---- build args: keep fallback until you can pull dhi.io ----
ARG BUILDER_BASE=python:3.11-slim
ARG RUNTIME_BASE=python:3.11-slim

# When DHI is available, set:
#   BUILDER_BASE=ubuntu/python:3.11-24.04_stable
#   RUNTIME_BASE=ubuntu/python:3.11-24.04_stable
# You must `docker login dhi.io` before using DHI images.

FROM ${BUILDER_BASE} AS builder

ENV LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/venv/bin:$PATH"

WORKDIR /app

# Build tooling (only in builder)
RUN apt-get update && apt-get install -y --no-install-recommends \
      gcc \
      curl \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /app/venv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

FROM ${RUNTIME_BASE} AS runtime

ENV LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/venv/bin:$PATH"

WORKDIR /app

# Runtime-only: curl for healthcheck (keep minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/venv /app/venv
COPY --from=builder /app /app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
