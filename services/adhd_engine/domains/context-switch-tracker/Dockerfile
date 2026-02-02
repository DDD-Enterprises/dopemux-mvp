"""
Dockerfile for Context Switch Tracker
"""
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service files
COPY . .

# Run service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8099"]
