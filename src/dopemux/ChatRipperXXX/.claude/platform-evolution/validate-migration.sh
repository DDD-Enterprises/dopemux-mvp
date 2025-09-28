#!/bin/bash

# MCP Migration Validation Script
echo "🔍 Validating MCP migration..."

# Check cluster configs exist
for cluster in research implementation quality coordination; do
    config_file=".claude/platform-evolution/mcp-${cluster}_cluster.json"
    if [ -f "$config_file" ]; then
        echo "✅ $config_file exists"
    else
        echo "❌ $config_file missing"
        exit 1
    fi
done

# Test Context7 integration
python3 .claude/platform-evolution/context7-enforcer.py --validate
if [ $? -eq 0 ]; then
    echo "✅ Context7 integration validated"
else
    echo "❌ Context7 integration failed"
    exit 1
fi

# Test agent connectivity
docker-compose -f .claude/platform-evolution/docker-compose.yml config
if [ $? -eq 0 ]; then
    echo "✅ Docker compose configuration valid"
else
    echo "❌ Docker compose configuration invalid"
    exit 1
fi

echo "🎉 MCP migration validation passed!"
