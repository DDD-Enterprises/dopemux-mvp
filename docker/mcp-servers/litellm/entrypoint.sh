#!/bin/sh
set -e

echo "🔧 Starting LiteLLM with Prisma database..."
echo "📊 DATABASE_URL: ${DATABASE_URL}"

# Remove any cached Prisma client
rm -rf /usr/local/lib/python3.11/site-packages/litellm/proxy/generated 2>/dev/null || true

# Generate Prisma client with current DATABASE_URL
echo "🔨 Generating Prisma client..."
prisma generate --schema=/usr/local/lib/python3.11/site-packages/litellm/proxy/schema.prisma

# Run database migrations
echo "🗄️  Running database migrations..."
cd /usr/local/lib/python3.11/site-packages/litellm/proxy
prisma migrate deploy --schema=schema.prisma || echo "⚠️  Migration failed, continuing..."

# Prevent LiteLLM from running migrations again (they're already done)
export DATABASE_CONNECTION_POOL_LIMIT=100
export STORE_MODEL_IN_DB=false

# Start LiteLLM
echo "🚀 Starting LiteLLM proxy server..."
cd /app
exec litellm --config /app/config.yaml --port 4000 --host 0.0.0.0 --detailed_debug
