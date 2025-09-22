#!/bin/bash
set -e

echo "🚀 Testing DocRAG Service Deployment"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOCRAG_URL="http://localhost:3009"
MILVUS_URL="http://localhost:19530"
CONTAINER_NAME="mcp-docrag"

echo -e "${YELLOW}📋 Step 1: Checking prerequisites...${NC}"

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    exit 1
fi

# Check if Milvus is running
echo "Checking Milvus connection..."
if curl -f "${MILVUS_URL}/healthz" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Milvus is healthy${NC}"
else
    echo -e "${RED}❌ Milvus is not accessible at ${MILVUS_URL}${NC}"
    echo "Please start Milvus with: docker-compose up milvus"
    exit 1
fi

echo -e "${YELLOW}📋 Step 2: Building DocRAG service...${NC}"
cd "$(dirname "$0")/.."
docker-compose build docrag

echo -e "${YELLOW}📋 Step 3: Starting DocRAG service...${NC}"
docker-compose up -d docrag

# Wait for service to be healthy
echo "Waiting for DocRAG service to be healthy..."
for i in {1..30}; do
    if curl -f "${DOCRAG_URL}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ DocRAG service is healthy${NC}"
        break
    fi

    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ DocRAG service failed to start${NC}"
        docker logs $CONTAINER_NAME --tail 20
        exit 1
    fi

    echo "Waiting... ($i/30)"
    sleep 2
done

echo -e "${YELLOW}📋 Step 4: Testing service functionality...${NC}"

# Test health endpoint
echo "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s "${DOCRAG_URL}/health")
echo "Health response: $HEALTH_RESPONSE"

# Test search endpoint (should return empty results)
echo "Testing search endpoint..."
SEARCH_RESPONSE=$(curl -s -X POST "${DOCRAG_URL}/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "test query", "limit": 5}')
echo "Search response: $SEARCH_RESPONSE"

# Test if we can ingest a simple document
echo "Testing document ingestion..."
echo "This is a test document for DocRAG ingestion." > /tmp/test-doc.txt

INGEST_RESPONSE=$(curl -s -X POST "${DOCRAG_URL}/ingest" \
    -H "Content-Type: application/json" \
    -d '{
        "source_path": "/tmp/test-doc.txt",
        "chunk_size": 500,
        "metadata": {"test": true}
    }')
echo "Ingest response: $INGEST_RESPONSE"

echo -e "${YELLOW}📋 Step 5: Displaying service logs...${NC}"
docker logs $CONTAINER_NAME --tail 20

echo ""
echo -e "${GREEN}🎉 DocRAG Service Deployment Test Complete!${NC}"
echo ""
echo "Service endpoints:"
echo "  - Health: ${DOCRAG_URL}/health"
echo "  - Search: ${DOCRAG_URL}/search"
echo "  - Ingest: ${DOCRAG_URL}/ingest"
echo ""
echo "Next steps:"
echo "  1. Set your VOYAGEAI_API_KEY environment variable"
echo "  2. Ingest some documents: docker exec $CONTAINER_NAME docrag-ingest /workspace/docs"
echo "  3. Test search queries via the API or future MCP integration"
echo ""
echo "To view logs: docker logs $CONTAINER_NAME -f"
echo "To stop service: docker-compose down docrag"