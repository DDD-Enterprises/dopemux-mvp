FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir redis

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 contextswitch && chown -R contextswitch:contextswitch /app
USER contextswitch

# No exposed ports (background tracking)

# Health check for background service
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import psutil; exit(0 if any('main.py' in [p.name() for p in psutil.process_iter()]) else 1)"

# Run context switch tracker
CMD ["python", "main.py"]