FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    procps \
    wmctrl \
    xdotool \
    && rm -rf /var/lib/apt/lists/*

COPY services/workspace-watcher/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/workspace-watcher /app/services/workspace-watcher
COPY services/dopecon-bridge /app/services/dopecon-bridge
COPY services/shared /app/services/shared
COPY src/dopemux /app/src/dopemux

WORKDIR /app/services/workspace-watcher

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/src

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD pgrep -f "python main.py" >/dev/null || exit 1

CMD ["python", "main.py", "--interval", "5"]
