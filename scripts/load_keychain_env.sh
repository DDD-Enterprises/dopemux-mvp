#!/bin/bash
# Dynamically generates .env.unified from the macOS keychain
# Uses local fallback values for database passwords and configs if not found in the keychain.

SECRETS=(
    # API Keys (Expected in Keychain)
    "GEMINI_API_KEY"
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
    "OPENROUTER_API_KEY"
    "VOYAGE_API_KEY"
    "VOYAGEAI_API_KEY"
    "XAI_API_KEY"
    "TAVILY_API_KEY"
    "CONTEXT7_API_KEY"
    "CONTEXT7_ENDPOINT"
    
    # Passwords (Keychain or Fallback)
    "POSTGRES_PASSWORD:dopemux_secure_2024"
    "AGE_PASSWORD:dopemux_age_dev_password"
    "AGE_DB_PASSWORD:dopemux_age_dev_password"
    "REDIS_PASSWORD:dopemux_redis_2024"
    "REDIS_UI_PASSWORD:dopemux-redis-ui"
    "MYSQL_ROOT_PASSWORD:dopemux_mysql_root_2024"
    "MYSQL_PASSWORD:leantime_secure_2024"
    "LEAN_SESSION_PASSWORD:dopemux_session_secure_2024"
    "MINIO_ACCESS_KEY:minioadmin"
    "MINIO_SECRET_KEY:minioadmin"
    
    # Non-sensitive Service Configurations
    "MYSQL_DATABASE:leantime"
    "MYSQL_USER:leantime"
    "LEAN_API_ENABLED:true"
)

ENV_FILE=".env.unified"
echo "# Generated securely from macOS Keychain" > "$ENV_FILE"

for item in "${SECRETS[@]}"; do
    secret="${item%%:*}"
    fallback="${item#*:}"
    
    if [ "$fallback" = "$secret" ]; then
        fallback=""
    fi

    # Fetch from keychain
    val=$(security find-generic-password -s "$secret" -w 2>/dev/null)
    
    if [ -n "$val" ]; then
        echo "$secret=$val" >> "$ENV_FILE"
    elif [ -n "$fallback" ]; then
        echo "$secret=$fallback" >> "$ENV_FILE"
    else
        echo "# $secret not found in keychain and no fallback provided" >> "$ENV_FILE"
    fi
done

echo "Successfully generated $ENV_FILE from keychain."