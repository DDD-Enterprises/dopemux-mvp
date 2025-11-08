<?php

namespace Leantime\Plugins\Dopemux;

/**
 * Dopemux ADHD Plugin for Leantime
 *
 * Main plugin class following Leantime's plugin structure
 */
class Plugin
{
    /**
     * Plugin initialization
     * Called when the plugin is loaded
     */
    public function init()
    {
        // Plugin is initialized
        error_log("=== Dopemux Plugin::init() called ===");
        error_log("Dopemux Plugin initialized successfully");
    }

    /**
     * Plugin installation
     * Called when the plugin is first installed
     */
    public function install()
    {
        error_log("=== Dopemux Plugin::install() called ===");
        error_log("Dopemux Plugin installed successfully");
        return true;
    }

    /**
     * Plugin uninstallation
     * Called when the plugin is removed
     */
    public function uninstall()
    {
        error_log("=== Dopemux Plugin::uninstall() called ===");
        error_log("Dopemux Plugin uninstalled successfully");
        return true;
    }
}