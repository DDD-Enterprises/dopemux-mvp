FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir redis

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 energytrends && chown -R energytrends:energytrends /app
USER energytrends

# No exposed ports (background analysis)

# Health check for background service
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import psutil; exit(0 if any('main.py' in [p.name() for p in psutil.process_iter()]) else 1)"

# Run energy trends analyzer
CMD ["python", "main.py"]