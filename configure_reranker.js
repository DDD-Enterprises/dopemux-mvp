#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Configure reranker strategy for claude-context MCP server
async function configureReranker() {
    console.log('🔧 Configuring reranker strategy...');

    const rerankerConfig = {
        // Available strategies: 'rrf' (Reciprocal Rank Fusion) or 'weighted'
        strategy: process.env.RERANK_STRATEGY || 'rrf',

        // RRF parameters: k value (smoothing parameter, 10-100 recommended)
        rrf: {
            k: parseInt(process.env.RRF_K) || 60  // Changed from 100 to 60 for better balance
        },

        // WeightedRanker parameters: weights for [dense_vector, sparse_bm25]
        weighted: {
            weights: process.env.WEIGHTED_WEIGHTS ?
                JSON.parse(process.env.WEIGHTED_WEIGHTS) :
                [0.7, 0.3]  // 70% dense vector, 30% sparse BM25
        }
    };

    console.log('📋 Reranker Configuration:');
    console.log(`   Strategy: ${rerankerConfig.strategy}`);

    if (rerankerConfig.strategy === 'rrf') {
        console.log(`   RRF k parameter: ${rerankerConfig.rrf.k}`);
    } else if (rerankerConfig.strategy === 'weighted') {
        console.log(`   Weights: Dense=${rerankerConfig.weighted.weights[0]}, Sparse=${rerankerConfig.weighted.weights[1]}`);
    }

    // Create configuration file for the MCP server to read
    const configPath = '/Users/hue/code/dopemux-mvp/docker/mcp-servers/claude-context/reranker-config.json';

    try {
        fs.writeFileSync(configPath, JSON.stringify(rerankerConfig, null, 2));
        console.log(`✅ Configuration saved to: ${configPath}`);
    } catch (error) {
        console.error(`❌ Failed to save configuration: ${error.message}`);
    }

    // Also update docker-compose environment variables
    const dockerComposePath = '/Users/hue/code/dopemux-mvp/docker/mcp-servers/docker-compose.yml';

    console.log('\n💡 To switch reranker strategies:');
    console.log('   For RRF with k=60:');
    console.log('     RERANK_STRATEGY=rrf RRF_K=60');
    console.log('   For RRF with k=100:');
    console.log('     RERANK_STRATEGY=rrf RRF_K=100');
    console.log('   For WeightedRanker:');
    console.log('     RERANK_STRATEGY=weighted WEIGHTED_WEIGHTS="[0.7,0.3]"');

    console.log('\n🔄 Add these to docker-compose.yml claude-context environment:');
    console.log(`      - RERANK_STRATEGY=${rerankerConfig.strategy}`);
    if (rerankerConfig.strategy === 'rrf') {
        console.log(`      - RRF_K=${rerankerConfig.rrf.k}`);
    } else {
        console.log(`      - WEIGHTED_WEIGHTS=${JSON.stringify(rerankerConfig.weighted.weights)}`);
    }
}

configureReranker().catch(console.error);