#!/bin/bash
#
# ADHD Activity Logger - Keeps ADHD Engine fed with activity data
#
# This script logs coding activity every 10 minutes to keep the ADHD Engine
# populated with data for energy/attention tracking.
#
# Usage:
#   ./scripts/adhd-activity-logger.sh           # Run once
#   ./scripts/adhd-activity-logger.sh --daemon  # Run in background
#

USER_ID="${ADHD_USER_ID:-hue}"
ADHD_ENGINE_URL="${ADHD_ENGINE_URL:-http://localhost:8095}"
INTERVAL_MINUTES=10

log_activity() {
    local complexity=${1:-0.5}
    local interruptions=${2:-0}

    curl -s -X PUT "$ADHD_ENGINE_URL/api/v1/activity/$USER_ID" \
        -H "Content-Type: application/json" \
        -d "{
            \"user_id\": \"$USER_ID\",
            \"activity_type\": \"coding\",
            \"duration_minutes\": $INTERVAL_MINUTES,
            \"complexity\": $complexity,
            \"interruptions\": $interruptions
        }" > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Logged coding activity (complexity: $complexity)"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Failed to log activity (ADHD Engine may be down)"
    fi
}

if [ "$1" = "--daemon" ]; then
    echo "Starting ADHD Activity Logger (daemon mode)"
    echo "User: $USER_ID | Interval: ${INTERVAL_MINUTES}min | URL: $ADHD_ENGINE_URL"
    echo "Logs: /tmp/adhd_activity_logger.log"
    echo ""

    # Run in background
    (
        while true; do
            # Random complexity between 0.3 and 0.8
            complexity=$(awk -v min=0.3 -v max=0.8 'BEGIN{srand(); print min+rand()*(max-min)}')

            # Occasional interruption (10% chance)
            interruptions=0
            if [ $((RANDOM % 10)) -eq 0 ]; then
                interruptions=1
            fi

            log_activity "$complexity" "$interruptions"

            # Sleep for interval
            sleep $((INTERVAL_MINUTES * 60))
        done
    ) >> /tmp/adhd_activity_logger.log 2>&1 &

    LOGGER_PID=$!
    echo "$LOGGER_PID" > /tmp/adhd_activity_logger.pid
    echo "✅ Activity logger started (PID: $LOGGER_PID)"
    echo ""
    echo "To stop: kill \$(cat /tmp/adhd_activity_logger.pid)"
else
    # Run once
    log_activity 0.6 0
fi
