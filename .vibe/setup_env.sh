#!/bin/bash

# Vibe Environment Setup Script
# This script helps you set up the .env file for Vibe

echo "🎉 Vibe Environment Setup"
echo "========================"
echo ""

# Check if .env already exists
if [ -f ".vibe/.env" ]; then
    echo "⚠️  .vibe/.env already exists"
    echo ""
    read -p "Do you want to overwrite it? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "📝 Keeping existing .env file"
        exit 0
    fi
fi

# Copy example to actual .env
cp ".vibe/.env.example" ".vibe/.env"
echo "✅ Created .vibe/.env from example"

# Give instructions
echo ""
echo "📋 Next Steps:"
echo "1. Open .vibe/.env in your editor"
echo "2. Replace 'your_*_api_key' placeholders with actual API keys"
echo "3. Save the file"
echo ""
echo "💡 Tip: You can get API keys from:"
echo "   - Mistral: https://console.mistral.ai/"
echo "   - OpenAI: https://platform.openai.com/api-keys"
echo "   - OpenRouter: https://openrouter.ai/keys"
echo "   - etc."
echo ""
echo "🚀 When ready, start Vibe with: vibe"

# Show the file location
echo ""
echo "📁 File created at: $(pwd)/.vibe/.env"