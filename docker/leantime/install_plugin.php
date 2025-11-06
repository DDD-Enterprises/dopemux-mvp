<?php

require_once '/var/www/html/bootstrap/app.php';

try {
    $pluginsService = app()->make('Leantime\Domain\Plugins\Services\Plugins');
    echo "Plugins service created\n";

    $discovered = $pluginsService->discoverPlugins();
    echo 'Discovered ' . count($discovered) . " plugins\n";

    foreach ($discovered as $plugin) {
        echo '- Found plugin: ' . $plugin->name . ' (' . $plugin->foldername . ")\n";
    }

    // Try to install Dopemux
    if (in_array('Dopemux', array_column($discovered, 'foldername'))) {
        echo "Installing Dopemux plugin...\n";
        $plugin = $pluginsService->installPlugin('Dopemux');
        if ($plugin) {
            echo 'Plugin installed successfully: ' . $plugin->name . "\n";
        } else {
            echo "Plugin installation failed\n";
        }
    } else {
        echo "Dopemux plugin not found in discovered plugins\n";
    }

} catch (Exception $e) {
    echo 'Error: ' . $e->getMessage() . "\n";
    echo 'Stack trace: ' . $e->getTraceAsString() . "\n";
}