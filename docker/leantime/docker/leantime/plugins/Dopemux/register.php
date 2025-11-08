<?php

/**
 * Dopemux ADHD Plugin Registration
 *
 * Registers the Dopemux plugin with Leantime's plugin system
 */

// Prevent direct access - temporarily removed LEANTIME check for debugging
// if (!defined('LEANTIME')) {
//     die('Access denied');
// }

// Plugin registration
error_log("=== DOPMUX REGISTER.PHP LOADED ===");
file_put_contents('/tmp/dopemux_debug.log', "Dopemux register.php loaded at " . date('Y-m-d H:i:s') . "\n", FILE_APPEND);

$plugin = new \Leantime\Plugins\Dopemux\Plugin();

// Register with Leantime plugin manager
if (method_exists($plugin, 'getPluginName')) {
    $pluginName = $plugin->getPluginName();
    $pluginVersion = $plugin->getVersion();

    error_log("=== Registering Dopemux Plugin: {$pluginName} v{$pluginVersion} ===");

    // Initialize the plugin
    $plugin->init();

    // Make plugin available globally
    $GLOBALS['plugins'][$pluginName] = $plugin;

    error_log("Dopemux Plugin registered successfully");
} else {
    error_log("ERROR: Dopemux Plugin missing required methods");
}

?>