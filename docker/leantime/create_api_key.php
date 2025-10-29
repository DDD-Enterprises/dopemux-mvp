#!/usr/bin/env php
<?php
/**
 * Leantime API Key Generator
 * Creates an API key directly in the database without web UI
 */

// Load Leantime bootstrap
require_once '/var/www/html/bootstrap/app.php';

use Leantime\Domain\Api\Services\Api as ApiService;
use Leantime\Domain\Auth\Models\Roles;
use Leantime\Domain\Projects\Repositories\Projects as ProjectRepository;

echo "\n===========================================\n";
echo "Leantime API Key Generator\n";
echo "===========================================\n\n";

try {
    // Get services
    $apiService = app()->make(ApiService::class);
    $projectRepo = app()->make(ProjectRepository::class);
    
    // API Key details
    $keyName = isset($argv[1]) ? $argv[1] : 'MCP Bridge Key';
    $role = isset($argv[2]) ? $argv[2] : Roles::$admin;
    
    echo "Creating API key...\n";
    echo "Key Name: {$keyName}\n";
    echo "Role: " . Roles::getRoleString($role) . "\n\n";
    
    // Create API key
    $values = [
        'firstname' => $keyName,
        'lastname' => '',
        'role' => $role,
        'status' => 'a',
        'source' => 'api',
    ];
    
    $apiKeyData = $apiService->createAPIKey($values);
    
    if ($apiKeyData && isset($apiKeyData['id'])) {
        // Format the API key
        $userId = $apiKeyData['user'];
        $password = $apiKeyData['passwordClean'];
        $apiKey = "lt_{$userId}_{$password}";
        
        echo "✅ API Key Created Successfully!\n\n";
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
        echo "API KEY: {$apiKey}\n";
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n";
        echo "User ID: {$apiKeyData['id']}\n";
        echo "Key Name: {$keyName}\n";
        echo "Role: " . Roles::getRoleString($role) . "\n";
        echo "Status: Active\n\n";
        
        // Assign to all projects
        $allProjects = $projectRepo->getAll();
        if (!empty($allProjects)) {
            $projectIds = array_column($allProjects, 'id');
            $projectRepo->editUserProjectRelations($apiKeyData['id'], $projectIds);
            echo "✅ Assigned to " . count($projectIds) . " project(s)\n\n";
        }
        
        echo "⚠️  IMPORTANT: Save this key securely!\n";
        echo "   This is the only time you will see the full key.\n\n";
        echo "Usage:\n";
        echo "  Export to environment:\n";
        echo "    export LEANTIME_API_TOKEN=\"{$apiKey}\"\n\n";
        echo "  Test with curl:\n";
        echo "    curl -H 'x-api-key: {$apiKey}' \\\n";
        echo "         http://localhost:8080/api/jsonrpc \\\n";
        echo "         -d '{\"method\":\"leantime.rpc.projects.getProjects\",\"jsonrpc\":\"2.0\",\"id\":1}'\n\n";
        
    } else {
        echo "❌ Failed to create API key\n";
        exit(1);
    }
    
} catch (Exception $e) {
    echo "❌ Error: " . $e->getMessage() . "\n";
    echo "Trace: " . $e->getTraceAsString() . "\n";
    exit(1);
}

echo "===========================================\n\n";
exit(0);
