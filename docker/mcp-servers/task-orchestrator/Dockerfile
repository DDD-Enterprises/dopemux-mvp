# Task-Orchestrator MCP Server
# Kotlin-based task orchestration with 37 tools for project management
FROM openjdk:17-jdk-slim

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Install Gradle
ENV GRADLE_VERSION=8.4
RUN curl -L https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip -o gradle.zip \
    && unzip gradle.zip \
    && mv gradle-${GRADLE_VERSION} /opt/gradle \
    && rm gradle.zip
ENV PATH="/opt/gradle/bin:${PATH}"

# Clone the task-orchestrator repository
RUN git clone https://github.com/jpicklyk/task-orchestrator.git .

# Build the application
RUN gradle build --no-daemon

# Set up runtime environment
ENV MCP_SERVER_PORT=3014
ENV MCP_TRANSPORT=stdio

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${MCP_SERVER_PORT}/health || exit 1

# Expose MCP server port
EXPOSE 3014

# Labels for Docker metadata
LABEL mcp.role="workflow"
LABEL mcp.priority="high"
LABEL mcp.description="Task orchestration and dependency management"
LABEL mcp.tools="37"

# Run the MCP server
CMD ["gradle", "run", "--args=--transport=stdio --port=3014"]