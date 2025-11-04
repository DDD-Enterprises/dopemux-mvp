  FROM python:3.11-slim

  WORKDIR /app

  # Install system dependencies including Java for Kotlin backend
  RUN apt-get update && apt-get install -y --no-install-recommends \
     gcc \
     default-jdk \
     && rm -rf /var/lib/apt/lists/*

  # Copy requirements
  COPY requirements.txt .

  # Install Python dependencies
  RUN pip install --no-cache-dir -r requirements.txt

  # Copy application code
  COPY . .

  # Create directory for Task-Orchestrator JAR and data
  RUN mkdir -p /opt/task-orchestrator /app/data

  # Copy the Task-Orchestrator JAR to expected location
  COPY mcp-task-orchestrator-*.jar /opt/task-orchestrator/task-orchestrator.jar

  # Set permissions for data directory
  RUN chmod 755 /app/data

  # Expose MCP port
  EXPOSE 3014

  # Health check - just ensure Java process is running
  HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
      CMD pgrep java > /dev/null || exit 1

  # Run the Python MCP wrapper that spawns the JAR subprocess
  CMD ["python", "server.py"]
