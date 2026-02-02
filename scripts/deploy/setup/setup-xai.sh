#!/bin/bash
# Setup and test xAI integration with Dopemux

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🚀 xAI (Grok) Integration Setup for Dopemux"
echo "==========================================="
echo ""

# Step 1: Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please ensure you're in the Dopemux project root"
    exit 1
fi

# Step 2: Check if XAI_API_KEY is set
if grep -q "XAI_API_KEY=your_xai_api_key_here" .env; then
    echo -e "${YELLOW}⚠️  XAI_API_KEY not configured${NC}"
    echo ""
    echo "To get your xAI API key:"
    echo "1. Visit: https://x.ai/api"
    echo "2. Sign up for API access"
    echo "3. Copy your API key"
    echo ""
    read -p "Enter your xAI API key (or press Enter to skip): " api_key

    if [ ! -z "$api_key" ]; then
        # Update .env file
        sed -i.bak "s/XAI_API_KEY=your_xai_api_key_here/XAI_API_KEY=$api_key/" .env
        echo -e "${GREEN}✅ xAI API key updated in .env${NC}"

        # Source the updated .env
        export XAI_API_KEY="$api_key"
    else
        echo -e "${YELLOW}⚠️  Skipping xAI setup - remember to add your API key later${NC}"
    fi
else
    # Load existing key
    source .env
    if [ ! -z "$XAI_API_KEY" ] && [ "$XAI_API_KEY" != "your_xai_api_key_here" ]; then
        echo -e "${GREEN}✅ xAI API key already configured${NC}"
    fi
fi

echo ""
echo "📋 Current AI Model Configuration:"
echo "=================================="

# Show configured models
if [ ! -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${GREEN}✅ Claude (Anthropic) - Configured${NC}"
else
    echo -e "${RED}❌ Claude (Anthropic) - Not configured${NC}"
fi

if [ ! -z "$OPENAI_API_KEY" ]; then
    echo -e "${GREEN}✅ OpenAI GPT-5 - Configured${NC}"
else
    echo -e "${RED}❌ OpenAI GPT-5 - Not configured${NC}"
fi

if [ ! -z "$XAI_API_KEY" ] && [ "$XAI_API_KEY" != "your_xai_api_key_here" ]; then
    echo -e "${GREEN}✅ xAI Grok - Configured${NC}"
else
    echo -e "${RED}❌ xAI Grok - Not configured${NC}"
fi

echo ""
echo "🔧 Testing xAI Connection..."
echo "============================"

if [ ! -z "$XAI_API_KEY" ] && [ "$XAI_API_KEY" != "your_xai_api_key_here" ]; then
    # Test xAI API
    response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST https://api.x.ai/v1/chat/completions \
        -H "Authorization: Bearer $XAI_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
            "model": "grok-2",
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 5
        }' 2>/dev/null || echo "000")

    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ xAI API connection successful${NC}"
    elif [ "$response" = "401" ]; then
        echo -e "${RED}❌ xAI API authentication failed - check your API key${NC}"
    elif [ "$response" = "000" ]; then
        echo -e "${RED}❌ Could not connect to xAI API - check network connection${NC}"
    else
        echo -e "${YELLOW}⚠️  xAI API returned status $response${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Skipping test - no API key configured${NC}"
fi

echo ""
echo "🚀 Launching Dopemux with xAI Support"
echo "====================================="

# Check if litellm is installed
if ! command -v litellm &> /dev/null; then
    echo -e "${YELLOW}⚠️  LiteLLM not found. Installing...${NC}"
    pip install litellm
fi

echo ""
echo "Available start options:"
echo "------------------------"
echo "1. dopemux start           # Use Claude Pro Max (primary)"
echo "2. dopemux start --litellm # Enable multi-model routing"
echo "3. dopemux start --debug   # Start with debug logging"
echo ""
echo -e "${GREEN}✨ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Run: source .env"
echo "2. Start: dopemux start --litellm"
echo "3. Monitor: tail -f .dopemux/litellm/A/litellm.log"