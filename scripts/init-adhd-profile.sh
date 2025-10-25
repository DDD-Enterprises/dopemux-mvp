#!/bin/bash
#
# Initialize ADHD User Profile
#
# Creates a user profile in the ADHD Engine if it doesn't exist yet.
# Called automatically by start-all.sh to ensure statusline works.
#

USER_ID="${ADHD_USER_ID:-hue}"
ADHD_ENGINE_URL="${ADHD_ENGINE_URL:-http://localhost:8095}"

echo "🧠 Checking ADHD Engine user profile..."

# Wait for ADHD Engine to be ready
max_retries=10
retry=0
while [ $retry -lt $max_retries ]; do
    if curl -sf "$ADHD_ENGINE_URL/health" >/dev/null 2>&1; then
        break
    fi
    retry=$((retry + 1))
    sleep 1
done

if [ $retry -eq $max_retries ]; then
    echo "⚠️  ADHD Engine not responding after 10 seconds"
    exit 0  # Non-blocking failure
fi

# Check if profile exists
profile_exists=$(curl -s "$ADHD_ENGINE_URL/api/v1/energy-level/$USER_ID" 2>/dev/null | jq -r '.energy_level' 2>/dev/null)

if [ -n "$profile_exists" ] && [ "$profile_exists" != "null" ]; then
    echo "✅ ADHD profile already exists for user: $USER_ID"
    exit 0
fi

# Create profile
echo "📝 Creating ADHD profile for user: $USER_ID"

curl -s -X POST "$ADHD_ENGINE_URL/api/v1/user-profile" \
    -H "Content-Type: application/json" \
    -d "{
        \"user_id\": \"$USER_ID\",
        \"baseline_energy\": \"medium\",
        \"baseline_attention\": \"focused\",
        \"preferred_break_interval_minutes\": 25,
        \"hyperfocus_threshold_minutes\": 60,
        \"context_switch_sensitivity\": 0.7
    }" >/dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ ADHD profile created successfully"
else
    echo "⚠️  Failed to create ADHD profile (non-blocking)"
fi
