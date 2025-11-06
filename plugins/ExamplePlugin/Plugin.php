<?php

namespace Leantime\Plugins\ExamplePlugin;

use Leantime\Plugins\ExamplePlugin\Controllers\ExampleController;
use Leantime\Core\PluginBase;
use Leantime\Core\Eventhelpers;

/**
 * Example Plugin for Leantime
 *
 * This is a basic plugin structure that demonstrates how to create
 * custom functionality in Leantime with the mounted plugins volume.
 */
class Plugin extends PluginBase
{
    public function init()
    {
        // Plugin metadata
        $this->pluginName = "Example Plugin";
        $this->pluginId = "exampleplugin";
        $this->version = "1.0.0";
        $this->minimumLeantimeVersion = "3.0.0";
        $this->maximumLeantimeVersion = "4.0.0";

        // Register routes, events, etc.
        $this->addRoutes();
        $this->addEventListeners();
    }

    /**
     * Add custom routes for the plugin
     */
    private function addRoutes()
    {
        // Example route registration
        // $this->addRoute('/example', 'ExampleController', 'index');
    }

    /**
     * Register event listeners
     */
    private function addEventListeners()
    {
        // Example: Listen for project creation events
        Eventhelpers::add_event_listener(
            "plugins.exampleplugin.project_created",
            [$this, "onProjectCreated"]
        );
    }

    /**
     * Event handler example
     */
    public function onProjectCreated($payload)
    {
        // Handle project creation event
        error_log("Example Plugin: Project created - " . print_r($payload, true));
    }
}