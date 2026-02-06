#!/bin/sh
set -e

echo "🔧 Starting LiteLLM with PostgreSQL database..."

# Use DATABASE_URL from environment (set by docker-compose)
# Default to localhost for backwards compatibility with host networking
export DATABASE_URL="${DATABASE_URL:-postgresql://dopemux_age:dopemux_age_dev_password@localhost:5432/litellm}"
echo "📊 DATABASE_URL: ${DATABASE_URL}"

# Remove any cached Prisma client
rm -rf /usr/local/lib/python3.11/site-packages/litellm/proxy/generated 2>/dev/null || true

# Generate Prisma client
echo "🔨 Generating Prisma client..."
prisma generate --schema=/usr/local/lib/python3.11/site-packages/litellm/proxy/schema.prisma

# Run database migrations
echo "🗄️  Running database migrations..."
cd /usr/local/lib/python3.11/site-packages/litellm/proxy
prisma migrate deploy --schema=schema.prisma || echo "⚠️  Migration warnings (safe to ignore)"

# Start LiteLLM
echo "🚀 Starting LiteLLM proxy server..."
cd /app
exec litellm --config /app/config.yaml --port 4000 --host 0.0.0.0
