#!/usr/bin/env php
<?php
/**
 * Leantime API Key Generator
 *
 * Creates an API user directly in Leantime DB and prints one key:
 *   lt_<api_username>_<api_secret>
 *
 * This avoids framework service-resolution edge cases seen in container CLI mode.
 */

require_once '/var/www/html/vendor/autoload.php';

$app = require '/var/www/html/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

use Illuminate\Support\Facades\DB;

function randomString(int $length = 32): string
{
    $chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
    $max = strlen($chars) - 1;
    $out = '';
    for ($i = 0; $i < $length; $i++) {
        $out .= $chars[random_int(0, $max)];
    }

    return $out;
}

function resolveRole(mixed $arg): int
{
    if (is_numeric($arg)) {
        return (int) $arg;
    }

    $map = [
        'readonly' => 5,
        'commenter' => 10,
        'editor' => 20,
        'manager' => 30,
        'admin' => 40,
        'owner' => 50,
    ];

    $key = strtolower((string) $arg);

    return $map[$key] ?? 50;
}

echo "\n===========================================\n";
echo "Leantime API Key Generator\n";
echo "===========================================\n\n";

try {
    $keyName = $argv[1] ?? 'MCP Bridge Key';
    $role = resolveRole($argv[2] ?? 'owner');

    $apiUser = randomString(24);      // keep underscore-free for key parser
    $apiSecret = randomString(32);    // keep underscore-free for key parser
    $hashed = password_hash($apiSecret, PASSWORD_DEFAULT);
    $now = date('Y-m-d H:i:s');

    DB::beginTransaction();

    $userId = DB::table('zp_user')->insertGetId([
        'firstname' => $keyName,
        'lastname' => '',
        'phone' => '',
        'username' => $apiUser,
        'role' => (string) $role,
        'notifications' => 1,
        'clientId' => '',
        'password' => $hashed,
        'source' => 'api',
        'pwReset' => '',
        'status' => 'a',
        'createdOn' => $now,
        'jobTitle' => '',
        'jobLevel' => '',
        'department' => '',
        'modified' => $now,
    ]);

    $projectIds = DB::table('zp_projects')->pluck('id')->all();
    foreach ($projectIds as $projectId) {
        DB::table('zp_relationuserproject')->updateOrInsert(
            ['userId' => $userId, 'projectId' => $projectId],
            ['projectRole' => '']
        );
    }

    DB::commit();

    $apiKey = "lt_{$apiUser}_{$apiSecret}";

    echo "✅ API key created successfully\n\n";
    echo "Key Name: {$keyName}\n";
    echo "User ID: {$userId}\n";
    echo "Role: {$role}\n";
    echo "Assigned Projects: " . count($projectIds) . "\n\n";
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
    echo "API KEY: {$apiKey}\n";
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n";
    echo "Usage:\n";
    echo "  export LEANTIME_API_TOKEN=\"{$apiKey}\"\n";
    echo "  export LEANTIME_TOKEN=\"{$apiKey}\"\n\n";
    echo "Validation:\n";
    echo "  curl -H 'x-api-key: {$apiKey}' \\\n";
    echo "       -H 'Content-Type: application/json' \\\n";
    echo "       -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"leantime.rpc.Projects.getAllProjects\",\"params\":{}}' \\\n";
    echo "       http://localhost:8080/api/jsonrpc\n\n";
} catch (Throwable $e) {
    if (DB::transactionLevel() > 0) {
        DB::rollBack();
    }

    echo "❌ Error: " . $e->getMessage() . "\n";
    if (stripos($e->getMessage(), 'install') !== false) {
        echo "ℹ️  Leantime may not be fully installed yet. Complete /install first.\n";
    }
    echo "Trace: " . $e->getTraceAsString() . "\n";
    exit(1);
}

echo "===========================================\n\n";
exit(0);
