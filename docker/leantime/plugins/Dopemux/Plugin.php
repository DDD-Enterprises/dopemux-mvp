<?php

namespace Leantime\Plugins\Dopemux;

use Leantime\Plugins\Dopemux\Controllers\DopemuxController;
use Leantime\Core\PluginBase;
use Leantime\Core\Eventhelpers;

/**
 * Dopemux ADHD Plugin for Leantime
 *
 * Provides ADHD-optimized features including cognitive load tracking,
 * attention management, break reminders, and context preservation.
 */
class Plugin extends PluginBase
{
    public function init()
    {
        // Plugin metadata
        $this->pluginName = "Dopemux ADHD Features";
        $this->pluginId = "Dopemux";
        $this->version = "1.0.0";
        $this->minimumLeantimeVersion = "3.0.0";
        $this->maximumLeantimeVersion = "4.0.0";

        // Initialize plugin components
        $this->initRoutes();
        $this->initEventListeners();
        $this->initDatabase();
    }

    /**
     * Initialize plugin routes
     */
    private function initRoutes()
    {
        // Main dashboard route
        $this->addRoute('/dopemux', 'Dopemux', 'index');

        // API routes for ADHD features
        $this->addRoute('/dopemux/api/cognitive-load', 'Dopemux', 'getCognitiveLoad', 'GET');
        $this->addRoute('/dopemux/api/cognitive-load', 'Dopemux', 'updateCognitiveLoad', 'POST');
        $this->addRoute('/dopemux/api/attention-state', 'Dopemux', 'getAttentionState', 'GET');
        $this->addRoute('/dopemux/api/attention-state', 'Dopemux', 'updateAttentionState', 'POST');
        $this->addRoute('/dopemux/api/context', 'Dopemux', 'saveContext', 'POST');
        $this->addRoute('/dopemux/api/context', 'Dopemux', 'restoreContext', 'GET');
        $this->addRoute('/dopemux/api/break-reminder', 'Dopemux', 'setBreakReminder', 'POST');
    }

    /**
     * Initialize event listeners
     */
    private function initEventListeners()
    {
        // Hook into ticket events for cognitive load calculation
        Eventhelpers::add_event_listener(
            "tickets.created",
            [$this, "onTicketCreated"]
        );

        Eventhelpers::add_event_listener(
            "tickets.updated",
            [$this, "onTicketUpdated"]
        );

        Eventhelpers::add_event_listener(
            "user.login",
            [$this, "onUserLogin"]
        );
    }

    /**
     * Initialize database tables if needed
     */
    private function initDatabase()
    {
        // Database tables are created via migrations
        // This method can be used for any additional setup
    }

    /**
     * Event handler for ticket creation
     */
    public function onTicketCreated($ticket)
    {
        // Auto-calculate cognitive load when ticket is created
        $cognitiveLoad = $this->calculateCognitiveLoad($ticket);
        $ticket->cognitive_load = $cognitiveLoad;

        // Log the event
        error_log("Dopemux Plugin: Ticket created with cognitive load: " . $cognitiveLoad);
    }

    /**
     * Event handler for ticket updates
     */
    public function onTicketUpdated($ticket)
    {
        // Update break reminders based on estimated time
        $this->updateBreakReminders($ticket);

        error_log("Dopemux Plugin: Ticket updated, break reminders updated");
    }

    /**
     * Event handler for user login
     */
    public function onUserLogin($user)
    {
        // Initialize ADHD preferences on login
        $this->initializeADHDPreferences($user);

        error_log("Dopemux Plugin: ADHD preferences initialized for user: " . ($user->id ?? 'unknown'));
    }

    /**
     * Calculate cognitive load for a task
     */
    private function calculateCognitiveLoad($ticket)
    {
        $load = 1;

        // Base load from story points
        if (isset($ticket->storypoints) && $ticket->storypoints) {
            $load = min($ticket->storypoints, 10);
        }

        // Increase load for complex keywords
        $complexKeywords = ['algorithm', 'architecture', 'refactor', 'optimization', 'integration'];
        $description = strtolower(($ticket->description ?? '') . ' ' . ($ticket->headline ?? ''));

        foreach ($complexKeywords as $keyword) {
            if (strpos($description, $keyword) !== false) {
                $load += 2;
            }
        }

        // Cap at 10
        return min($load, 10);
    }

    /**
     * Update break reminders based on task complexity
     */
    private function updateBreakReminders($ticket)
    {
        $cognitiveLoad = $ticket->cognitive_load ?? 5;

        if ($cognitiveLoad >= 8) {
            // High complexity - 25 minute breaks
            $breakFrequency = 25;
        } elseif ($cognitiveLoad >= 5) {
            // Medium complexity - 30 minute breaks
            $breakFrequency = 30;
        } else {
            // Low complexity - 45 minute breaks
            $breakFrequency = 45;
        }

        // Store break reminder preference
        // This would integrate with Leantime's user preferences system
        error_log("Dopemux Plugin: Break frequency set to {$breakFrequency} minutes for cognitive load {$cognitiveLoad}");
    }

    /**
     * Initialize ADHD preferences for new users
     */
    private function initializeADHDPreferences($user)
    {
        $defaultPreferences = [
            'attention_tracking' => true,
            'break_reminders' => true,
            'context_preservation' => true,
            'cognitive_load_display' => true,
            'notification_batching' => true,
            'gentle_notifications' => true,
        ];

        // This would store preferences in Leantime's user settings
        foreach ($defaultPreferences as $key => $value) {
            if (!$this->userHasPreference($user, $key)) {
                $this->setUserPreference($user, $key, $value);
            }
        }
    }

    /**
     * Check if user has a specific preference
     */
    private function userHasPreference($user, $key)
    {
        // Implementation would check Leantime's user preferences table
        return false; // Placeholder
    }

    /**
     * Set user preference
     */
    private function setUserPreference($user, $key, $value)
    {
        // Implementation would store in Leantime's user preferences table
        error_log("Dopemux Plugin: Set preference {$key} = {$value} for user " . ($user->id ?? 'unknown'));
    }
}