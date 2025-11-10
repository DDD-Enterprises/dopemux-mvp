# Task Orchestrator Service

## Overview

The Task Orchestrator is a microservice that handles task coordination and management for the Dopemux system. It integrates with ConPort for persistent storage and provides REST API endpoints for task creation, retrieval, and coordination.

## API Endpoints

- `POST /api/v1/tasks` - Create a new task
- `GET /api/v1/tasks` - Get all tasks
- `POST /api/v1/coordinate` - Coordinate tasks using the Task Coordinator

## Authentication

All API endpoints are secured using API key authentication via the `X-API-Key` header.

### Environment Variables

- **TASK_ORCHESTRATOR_API_KEY** (required for production)
  - Type: String
  - Description: The API key used for authenticating requests to the Task Orchestrator service.
  - Default: None (authentication disabled in development mode)
  - Example: `export TASK_ORCHESTRATOR_API_KEY="your-secret-api-key-here"`
  - Usage: Set this environment variable to enable API key validation. In development mode, if this variable is not set, authentication is bypassed.

### Security Features

- **Header**: `X-API-Key`
- **Error Responses**:
  - 401 Unauthorized: Missing API key
  - 403 Forbidden: Invalid API key
- **Development Mode**: Authentication is disabled if `TASK_ORCHESTRATOR_API_KEY` is not set
- **CORS**: Configured to allow `X-API-Key` header from authorized origins

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables:
   ```bash
   export TASK_ORCHESTRATOR_API_KEY="your-secret-api-key"
   ```

3. Run the service:
   ```bash
   python server.py
   ```

## Testing Authentication

### Valid API Key
```bash
curl -H "X-API-Key: your-secret-api-key" http://localhost:8000/api/v1/tasks
```

### Missing API Key (Development Mode)
If `TASK_ORCHESTRATOR_API_KEY` is not set, requests will succeed without the header.

### Invalid API Key (Production Mode)
```bash
curl -H "X-API-Key: invalid-key" http://localhost:8000/api/v1/tasks
```
Expected response: 403 Forbidden