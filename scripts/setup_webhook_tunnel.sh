#!/bin/bash
# Script to setup a Cloudflare Tunnel for the webhook receiver.

PORT=${1:-8790}
echo "Starting Cloudflare tunnel for localhost:$PORT..."

# Start cloudflared in the background and capture output to a temp file
TMP_LOG=$(mktemp)
cloudflared tunnel --url http://localhost:$PORT > "$TMP_LOG" 2>&1 &
CLOUDFLARED_PID=$!

echo "Waiting for tunnel URL... (PID: $CLOUDFLARED_PID)"

# Wait for the URL to appear in the log
COUNT=0
URL=""
while [ $COUNT -lt 30 ]; do
    URL=$(grep -oE "https://[a-zA-Z0-9.-]+\.trycloudflare\.com" "$TMP_LOG" | head -n 1)
    if [ -n "$URL" ]; then
        break
    fi
    sleep 1
    COUNT=$((COUNT + 1))
done

if [ -n "$URL" ]; then
    echo "------------------------------------------------"
    echo "Tunnel is UP!"
    echo "Public URL: $URL"
    echo "Webhook URL: $URL/openai/webhooks"
    echo "------------------------------------------------"
    echo "Keep this script running to maintain the tunnel."
    echo "Press Ctrl+C to stop."
    
    # Store URL for other scripts if needed
    echo "$URL" > .webhook_url
    
    # Wait for the background process
    wait $CLOUDFLARED_PID
else
    echo "Failed to get tunnel URL within 30 seconds."
    kill $CLOUDFLARED_PID
    exit 1
fi
