FROM python:3.11-slim

WORKDIR /app

COPY services/webhook_receiver/requirements.txt /app/services/webhook_receiver/requirements.txt
RUN pip install --no-cache-dir -r /app/services/webhook_receiver/requirements.txt

COPY services/webhook_receiver /app/services/webhook_receiver

COPY scripts/webhook_migrate.py /app/scripts/webhook_migrate.py
EXPOSE 8790
CMD ["python", "/app/services/webhook_receiver/server.py"]
