<?php

/**
 * Dopemux ADHD Plugin Registration
 *
 * Debug version with logging to understand plugin discovery
 */

error_log("=== Dopemux Plugin register.php START ===");
echo "Dopemux plugin register.php loaded successfully\n";

try {
    // Check if composer.json exists and is readable
    $composerPath = __DIR__ . '/composer.json';
    if (file_exists($composerPath)) {
        error_log("Dopemux: composer.json exists at: " . $composerPath);
        $composerData = json_decode(file_get_contents($composerPath), true);
        if ($composerData) {
            error_log("Dopemux: composer.json parsed successfully, name: " . ($composerData['name'] ?? 'unknown'));
        } else {
            error_log("Dopemux: ERROR - composer.json could not be parsed");
        }
    } else {
        error_log("Dopemux: ERROR - composer.json not found at: " . $composerPath);
    }

    // Check if Plugin.php exists and is readable
    $pluginPath = __DIR__ . '/Plugin.php';
    if (file_exists($pluginPath)) {
        error_log("Dopemux: Plugin.php exists at: " . $pluginPath);
    } else {
        error_log("Dopemux: ERROR - Plugin.php not found at: " . $pluginPath);
    }

} catch (Exception $e) {
    error_log("Dopemux: ERROR in register.php: " . $e->getMessage());
}

error_log("=== Dopemux Plugin register.php END ===");

?>