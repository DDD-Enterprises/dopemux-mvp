<?php

/**
 * Dopemux ADHD Plugin Registration
 *
 * This file registers the Dopemux ADHD-optimized features with Leantime.
 * Provides cognitive load tracking, attention management, and context preservation.
 */

use Leantime\Core\Plugins\Registration;

// Get registration helper
$registration = app()->makeWith(Registration::class, ['pluginId' => 'Dopemux']);

// Register language files
$registration->registerLanguageFiles(['en-US']);

// Add main menu item for ADHD management
$registration->addMenuItem([
    'title' => 'dopemux.menu.adhd_dashboard',
    'icon' => 'fa fa-brain',
    'tooltip' => 'dopemux.menu.adhd_tooltip',
    'href' => '/dopemux/dashboard',
], 'personal', [10]);

// Add cognitive load tracker submenu
$registration->addMenuItem([
    'title' => 'dopemux.menu.cognitive_load',
    'icon' => 'fa fa-chart-line',
    'tooltip' => 'dopemux.menu.cognitive_tooltip',
    'href' => '/dopemux/cognitive-load',
], 'personal', [11]);

// Add attention management submenu
$registration->addMenuItem([
    'title' => 'dopemux.menu.attention_manager',
    'icon' => 'fa fa-focus',
    'tooltip' => 'dopemux.menu.attention_tooltip',
    'href' => '/dopemux/attention-manager',
], 'personal', [12]);

// Add context preservation submenu
$registration->addMenuItem([
    'title' => 'dopemux.menu.context_saver',
    'icon' => 'fa fa-save',
    'tooltip' => 'dopemux.menu.context_tooltip',
    'href' => '/dopemux/context-saver',
], 'personal', [13]);

// Register API endpoints for Dopemux integration
$registration->addRoute([
    'path' => '/dopemux/api/cognitive-load',
    'controller' => 'Dopemux',
    'action' => 'getCognitiveLoad',
    'method' => 'GET'
]);

$registration->addRoute([
    'path' => '/dopemux/api/cognitive-load',
    'controller' => 'Dopemux',
    'action' => 'updateCognitiveLoad',
    'method' => 'POST'
]);

$registration->addRoute([
    'path' => '/dopemux/api/attention-state',
    'controller' => 'Dopemux',
    'action' => 'getAttentionState',
    'method' => 'GET'
]);

$registration->addRoute([
    'path' => '/dopemux/api/attention-state',
    'controller' => 'Dopemux',
    'action' => 'updateAttentionState',
    'method' => 'POST'
]);

$registration->addRoute([
    'path' => '/dopemux/api/context',
    'controller' => 'Dopemux',
    'action' => 'saveContext',
    'method' => 'POST'
]);

$registration->addRoute([
    'path' => '/dopemux/api/context',
    'controller' => 'Dopemux',
    'action' => 'restoreContext',
    'method' => 'GET'
]);

$registration->addRoute([
    'path' => '/dopemux/api/break-reminder',
    'controller' => 'Dopemux',
    'action' => 'setBreakReminder',
    'method' => 'POST'
]);

// Register event hooks for ADHD optimizations
$registration->addEventHook('tickets.created', function($ticket) {
    // Auto-calculate cognitive load when ticket is created
    $cognitiveLoad = calculateCognitiveLoad($ticket);
    $ticket->cognitive_load = $cognitiveLoad;
});

$registration->addEventHook('tickets.updated', function($ticket) {
    // Update break reminders based on estimated time
    updateBreakReminders($ticket);
});

$registration->addEventHook('user.login', function($user) {
    // Initialize ADHD preferences on login
    initializeADHDPreferences($user);
});

/**
 * Calculate cognitive load for a task based on ADHD criteria
 */
function calculateCognitiveLoad($ticket) {
    $load = 1;

    // Base load from story points
    if ($ticket->storypoints) {
        $load = min($ticket->storypoints, 10);
    }

    // Increase load for complex keywords
    $complexKeywords = ['algorithm', 'architecture', 'refactor', 'optimization', 'integration'];
    $description = strtolower($ticket->description . ' ' . $ticket->headline);

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
function updateBreakReminders($ticket) {
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
}

/**
 * Initialize ADHD preferences for new users
 */
function initializeADHDPreferences($user) {
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
        if (!userHasPreference($user, $key)) {
            setUserPreference($user, $key, $value);
        }
    }
}

/**
 * Check if user has a specific preference
 */
function userHasPreference($user, $key) {
    // Implementation would check Leantime's user preferences table
    return false; // Placeholder
}

/**
 * Set user preference
 */
function setUserPreference($user, $key, $value) {
    // Implementation would store in Leantime's user preferences table
}

?>