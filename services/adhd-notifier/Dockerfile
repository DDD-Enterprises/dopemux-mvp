"""
Dockerfile for ADHD Notifier
"""
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service files
COPY . .

# Run service
CMD ["python", "main.py"]
