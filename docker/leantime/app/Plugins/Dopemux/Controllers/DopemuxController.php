<?php

/**
 * Dopemux ADHD Plugin Controller
 *
 * Main controller for ADHD-optimized features in Leantime.
 * Provides cognitive load tracking, attention management, and context preservation.
 */

namespace Leantime\Plugins\Dopemux\Controllers;

use Leantime\Core\Controller\Controller;
use Leantime\Core\Http\ApiRequest;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Response;

class DopemuxController extends Controller
{
    /**
     * Initialize controller
     */
    public function init(): void
    {
        // Initialize ADHD-specific settings
        $this->tpl->assign('currentAttentionState', $this->getCurrentAttentionState());
        $this->tpl->assign('cognitiveLoadLimit', $this->getCognitiveLoadLimit());
    }

    /**
     * Show ADHD dashboard
     */
    public function dashboard(): Response
    {
        $userId = $_SESSION['userdata']['id'] ?? null;

        if (!$userId) {
            return $this->redirect('/auth/login');
        }

        // Get current ADHD state
        $adhdState = $this->getADHDState($userId);
        $recommendedTasks = $this->getRecommendedTasks($userId, $adhdState['attention_state']);
        $upcomingBreaks = $this->getUpcomingBreaks($userId);
        $contextStatus = $this->getContextStatus($userId);

        $this->tpl->assign('adhdState', $adhdState);
        $this->tpl->assign('recommendedTasks', $recommendedTasks);
        $this->tpl->assign('upcomingBreaks', $upcomingBreaks);
        $this->tpl->assign('contextStatus', $contextStatus);

        return $this->tpl->display('plugins.dopemux.dashboard');
    }

    /**
     * Show cognitive load management
     */
    public function cognitiveLoad(): Response
    {
        $userId = $_SESSION['userdata']['id'] ?? null;

        if (!$userId) {
            return $this->redirect('/auth/login');
        }

        $currentLoad = $this->getCurrentCognitiveLoad($userId);
        $loadHistory = $this->getCognitiveLoadHistory($userId);
        $recommendations = $this->getCognitiveLoadRecommendations($currentLoad);

        $this->tpl->assign('currentLoad', $currentLoad);
        $this->tpl->assign('loadHistory', $loadHistory);
        $this->tpl->assign('recommendations', $recommendations);

        return $this->tpl->display('plugins.dopemux.cognitive-load');
    }

    /**
     * Show attention manager
     */
    public function attentionManager(): Response
    {
        $userId = $_SESSION['userdata']['id'] ?? null;

        if (!$userId) {
            return $this->redirect('/auth/login');
        }

        $currentState = $this->getCurrentAttentionState($userId);
        $stateHistory = $this->getAttentionStateHistory($userId);
        $suggestions = $this->getAttentionSuggestions($currentState);

        $this->tpl->assign('currentState', $currentState);
        $this->tpl->assign('stateHistory', $stateHistory);
        $this->tpl->assign('suggestions', $suggestions);

        return $this->tpl->display('plugins.dopemux.attention-manager');
    }

    /**
     * Show context saver
     */
    public function contextSaver(): Response
    {
        $userId = $_SESSION['userdata']['id'] ?? null;

        if (!$userId) {
            return $this->redirect('/auth/login');
        }

        $savedContexts = $this->getSavedContexts($userId);
        $currentContext = $this->getCurrentContext($userId);

        $this->tpl->assign('savedContexts', $savedContexts);
        $this->tpl->assign('currentContext', $currentContext);

        return $this->tpl->display('plugins.dopemux.context-saver');
    }

    // API Endpoints

    /**
     * Get current cognitive load (API)
     */
    public function getCognitiveLoad(): JsonResponse
    {
        $userId = $_SESSION['userdata']['id'] ?? null;

        if (!$userId) {
            return new JsonResponse(['error' => 'Not authenticated'], 401);
        }

        $load = $this->getCurrentCognitiveLoad($userId);

        return new JsonResponse([
            'success' => true,
            'cognitive_load' => $load,
            'timestamp' => date('c')
        ]);
    }

    /**
     * Update cognitive load (API)
     */
    public function updateCognitiveLoad(): JsonResponse
    {
        try {
            $userId = $_SESSION['userdata']['id'] ?? null;

            if (!$userId) {
                return new JsonResponse(['error' => 'Not authenticated'], 401);
            }

            // Safely parse JSON input
            $input = file_get_contents('php://input');
            if (empty($input)) {
                return new JsonResponse(['error' => 'No input data provided'], 400);
            }

            $requestData = json_decode($input, true);
            if (json_last_error() !== JSON_ERROR_NONE) {
                return new JsonResponse(['error' => 'Invalid JSON format'], 400);
            }

            $newLoad = $requestData['cognitive_load'] ?? null;

            if ($newLoad === null || !is_numeric($newLoad) || $newLoad < 1 || $newLoad > 10) {
                return new JsonResponse(['error' => 'Invalid cognitive load value. Must be a number between 1 and 10'], 400);
            }

            $success = $this->setCognitiveLoad($userId, (int)$newLoad);

            if ($success) {
                return new JsonResponse([
                    'success' => true,
                    'cognitive_load' => (int)$newLoad,
                    'timestamp' => date('c')
                ]);
            } else {
                return new JsonResponse(['error' => 'Failed to update cognitive load'], 500);
            }
        } catch (\Exception $e) {
            error_log('Dopemux updateCognitiveLoad error: ' . $e->getMessage());
            return new JsonResponse(['error' => 'Internal server error'], 500);
        }
    }

    /**
     * Get current attention state (API)
     */
    public function getAttentionState(): JsonResponse
    {
        $userId = $_SESSION['userdata']['id'] ?? null;

        if (!$userId) {
            return new JsonResponse(['error' => 'Not authenticated'], 401);
        }

        $state = $this->getCurrentAttentionState($userId);

        return new JsonResponse([
            'success' => true,
            'attention_state' => $state,
            'timestamp' => date('c')
        ]);
    }

    /**
     * Update attention state (API)
     */
    public function updateAttentionState(): JsonResponse
    {
        try {
            $userId = $_SESSION['userdata']['id'] ?? null;

            if (!$userId) {
                return new JsonResponse(['error' => 'Not authenticated'], 401);
            }

            // Safely parse JSON input
            $input = file_get_contents('php://input');
            if (empty($input)) {
                return new JsonResponse(['error' => 'No input data provided'], 400);
            }

            $requestData = json_decode($input, true);
            if (json_last_error() !== JSON_ERROR_NONE) {
                return new JsonResponse(['error' => 'Invalid JSON format'], 400);
            }

            $newState = $requestData['attention_state'] ?? null;
            $validStates = ['hyperfocus', 'focused', 'scattered', 'background', 'transition'];

            if (!in_array($newState, $validStates)) {
                return new JsonResponse(['error' => 'Invalid attention state. Must be one of: ' . implode(', ', $validStates)], 400);
            }

            $success = $this->setAttentionState($userId, $newState);

            if ($success) {
                return new JsonResponse([
                    'success' => true,
                    'attention_state' => $newState,
                    'timestamp' => date('c')
                ]);
            } else {
                return new JsonResponse(['error' => 'Failed to update attention state'], 500);
            }
        } catch (\Exception $e) {
            error_log('Dopemux updateAttentionState error: ' . $e->getMessage());
            return new JsonResponse(['error' => 'Internal server error'], 500);
        }
    }

    /**
     * Save context (API)
     */
    public function saveContext(): JsonResponse
    {
        try {
            $userId = $_SESSION['userdata']['id'] ?? null;

            if (!$userId) {
                return new JsonResponse(['error' => 'Not authenticated'], 401);
            }

            // Safely parse JSON input
            $input = file_get_contents('php://input');
            if (empty($input)) {
                return new JsonResponse(['error' => 'No input data provided'], 400);
            }

            $requestData = json_decode($input, true);
            if (json_last_error() !== JSON_ERROR_NONE) {
                return new JsonResponse(['error' => 'Invalid JSON format'], 400);
            }

            $contextName = $requestData['context_name'] ?? 'Auto-saved Context';
            $contextData = $requestData['context_data'] ?? [];

            // Validate context name
            if (!is_string($contextName) || strlen($contextName) > 255) {
                return new JsonResponse(['error' => 'Invalid context name. Must be a string with maximum 255 characters'], 400);
            }

            // Validate context data is an array/object
            if (!is_array($contextData)) {
                return new JsonResponse(['error' => 'Invalid context data. Must be an array or object'], 400);
            }

            $contextId = $this->saveUserContext($userId, $contextName, $contextData);

            if ($contextId) {
                return new JsonResponse([
                    'success' => true,
                    'context_id' => $contextId,
                    'context_name' => $contextName,
                    'timestamp' => date('c')
                ]);
            } else {
                return new JsonResponse(['error' => 'Failed to save context'], 500);
            }
        } catch (\Exception $e) {
            error_log('Dopemux saveContext error: ' . $e->getMessage());
            return new JsonResponse(['error' => 'Internal server error'], 500);
        }
    }

    /**
     * Restore context (API)
     */
    public function restoreContext(): JsonResponse
    {
        try {
            $userId = $_SESSION['userdata']['id'] ?? null;

            if (!$userId) {
                return new JsonResponse(['error' => 'Not authenticated'], 401);
            }

            $contextId = $_GET['context_id'] ?? null;

            if (!$contextId || !is_numeric($contextId)) {
                return new JsonResponse(['error' => 'Valid context ID required'], 400);
            }

            $contextData = $this->restoreUserContext($userId, (int)$contextId);

            if ($contextData !== null) {
                return new JsonResponse([
                    'success' => true,
                    'context_data' => $contextData,
                    'timestamp' => date('c')
                ]);
            } else {
                return new JsonResponse(['error' => 'Context not found'], 404);
            }
        } catch (\Exception $e) {
            error_log('Dopemux restoreContext error: ' . $e->getMessage());
            return new JsonResponse(['error' => 'Internal server error'], 500);
        }
    }

    /**
     * Set break reminder (API)
     */
    public function setBreakReminder(): JsonResponse
    {
        try {
            $userId = $_SESSION['userdata']['id'] ?? null;

            if (!$userId) {
                return new JsonResponse(['error' => 'Not authenticated'], 401);
            }

            // Safely parse JSON input
            $input = file_get_contents('php://input');
            if (empty($input)) {
                return new JsonResponse(['error' => 'No input data provided'], 400);
            }

            $requestData = json_decode($input, true);
            if (json_last_error() !== JSON_ERROR_NONE) {
                return new JsonResponse(['error' => 'Invalid JSON format'], 400);
            }

            $frequency = $requestData['frequency'] ?? 25; // Default 25 minutes
            $enabled = $requestData['enabled'] ?? true;

            // Validate frequency
            if (!is_numeric($frequency) || $frequency < 5 || $frequency > 180) {
                return new JsonResponse(['error' => 'Invalid frequency. Must be a number between 5 and 180 minutes'], 400);
            }

            // Validate enabled flag
            if (!is_bool($enabled)) {
                return new JsonResponse(['error' => 'Invalid enabled flag. Must be true or false'], 400);
            }

            $success = $this->setBreakReminderPreference($userId, (int)$frequency, $enabled);

            if ($success) {
                return new JsonResponse([
                    'success' => true,
                    'frequency' => (int)$frequency,
                    'enabled' => $enabled,
                    'timestamp' => date('c')
                ]);
            } else {
                return new JsonResponse(['error' => 'Failed to set break reminder'], 500);
            }
        } catch (\Exception $e) {
            error_log('Dopemux setBreakReminder error: ' . $e->getMessage());
            return new JsonResponse(['error' => 'Internal server error'], 500);
        }
    }

    // Helper Methods

    /**
     * Get current ADHD state for user
     */
    private function getADHDState(int $userId): array
    {
        try {
            // Load models
            $preferencesModel = new \Leantime\Plugins\Dopemux\Models\ADHDUserPreferences();
            $cognitiveModel = new \Leantime\Plugins\Dopemux\Models\CognitiveLoadHistory();
            $attentionModel = new \Leantime\Plugins\Dopemux\Models\AttentionStateHistory();

            // Get real data from models
            $currentLoad = $cognitiveModel->getAverageLoad($userId, 1); // Last 24 hours
            $currentAttention = $attentionModel->getCurrentState($userId) ?: 'focused';
            $preferences = $preferencesModel->getUserPreferences($userId);

            return [
                'attention_state' => $currentAttention,
                'cognitive_load' => $currentLoad,
                'break_due' => $this->isBreakDue($userId),
                'context_preserved' => true, // Always true for now
                'last_updated' => date('c'),
                'preferences' => $preferences
            ];
        } catch (\Exception $e) {
            error_log('Dopemux getADHDState error for user ' . $userId . ': ' . $e->getMessage());
            // Return safe defaults on error
            return [
                'attention_state' => 'focused',
                'cognitive_load' => 5.0,
                'break_due' => false,
                'context_preserved' => false,
                'last_updated' => date('c'),
                'preferences' => []
            ];
        }
    }

    /**
     * Get recommended tasks based on attention state
     */
    private function getRecommendedTasks(int $userId, string $attentionState): array
    {
        // This would query tasks and filter by attention compatibility
        return [
            [
                'id' => 1,
                'title' => 'Code Review',
                'cognitive_load' => 4,
                'estimated_time' => '30 minutes',
                'compatibility' => 'high'
            ],
            [
                'id' => 2,
                'title' => 'Update Documentation',
                'cognitive_load' => 2,
                'estimated_time' => '15 minutes',
                'compatibility' => 'medium'
            ]
        ];
    }

    /**
     * Get upcoming breaks
     */
    private function getUpcomingBreaks(int $userId): array
    {
        $breakModel = new \Leantime\Plugins\Dopemux\Models\BreakReminderSettings();
        $settings = $breakModel->getUserSettings($userId);
        $isDue = $breakModel->isBreakDue($userId);

        if ($isDue && ($settings['enabled'] ?? true)) {
            return [
                'next_break' => 'Now',
                'break_type' => 'short',
                'reminders_enabled' => true
            ];
        } elseif ($settings['enabled'] ?? true) {
            return [
                'next_break' => $settings['frequency_minutes'] . ' minutes',
                'break_type' => 'short',
                'reminders_enabled' => true
            ];
        } else {
            return [
                'next_break' => null,
                'break_type' => null,
                'reminders_enabled' => false
            ];
        }
    }

    /**
     * Get context status
     */
    private function getContextStatus(int $userId): array
    {
        $breakModel = new \Leantime\Plugins\Dopemux\Models\BreakReminderSettings();
        $settings = $breakModel->getUserSettings($userId);

        $contextModel = new \Leantime\Plugins\Dopemux\Models\ContextSnapshot();
        $snapshots = $contextModel->getUserSnapshots($userId, 1); // Get latest

        $lastSave = 'Never';
        if (!empty($snapshots)) {
            $lastSave = date('i \m\i\n\u\t\e\s \a\g\o', strtotime($snapshots[0]['created_at']));
        }

        return [
            'auto_save_enabled' => $settings['enabled'] ?? true,
            'last_save' => $lastSave,
            'saved_contexts' => count($contextModel->getUserSnapshots($userId, 100)) // Count total
        ];
    }

    /**
     * Get current cognitive load
     */
    private function getCurrentCognitiveLoad(int $userId): int
    {
        $cognitiveModel = new \Leantime\Plugins\Dopemux\Models\CognitiveLoadHistory();
        return (int) $cognitiveModel->getAverageLoad($userId, 1); // Last 24 hours
    }

    /**
     * Get cognitive load history
     */
    private function getCognitiveLoadHistory(int $userId): array
    {
        try {
            $cognitiveModel = new \Leantime\Plugins\Dopemux\Models\CognitiveLoadHistory();
            $rawHistory = $cognitiveModel->getUserHistory($userId, 10);

            // Format for template
            return array_map(function($record) {
                return [
                    'timestamp' => date('Y-m-d H:i', strtotime($record['created_at'])),
                    'load' => (float) $record['load_value']
                ];
            }, $rawHistory);
        } catch (\Exception $e) {
            error_log('Dopemux getCognitiveLoadHistory error for user ' . $userId . ': ' . $e->getMessage());
            return [];
        }
    }

    /**
     * Get cognitive load recommendations
     */
    private function getCognitiveLoadRecommendations(int $currentLoad): array
    {
        try {
            if ($currentLoad >= 8) {
                return [
                    'status' => 'high',
                    'recommendation' => 'Take a break or switch to lighter tasks',
                    'suggested_actions' => ['Take 15 minute break', 'Do documentation tasks', 'Review code instead of writing']
                ];
            } elseif ($currentLoad >= 6) {
                return [
                    'status' => 'moderate',
                    'recommendation' => 'Monitor load and take breaks as needed',
                    'suggested_actions' => ['Continue current work', 'Plan break in 30 minutes']
                ];
            } else {
                return [
                    'status' => 'low',
                    'recommendation' => 'Good time for complex tasks',
                    'suggested_actions' => ['Tackle difficult problems', 'Start new features', 'Do architecture work']
                ];
            }
        } catch (\Exception $e) {
            error_log('Dopemux getCognitiveLoadRecommendations error: ' . $e->getMessage());
            return [
                'status' => 'unknown',
                'recommendation' => 'Unable to generate recommendations at this time',
                'suggested_actions' => ['Assess current state manually']
            ];
        }
    }

    /**
     * Get current attention state
     */
    private function getCurrentAttentionState(int $userId = null): string
    {
        if (!$userId) {
            return 'focused'; // Default for non-authenticated users
        }

        $attentionModel = new \Leantime\Plugins\Dopemux\Models\AttentionStateHistory();
        $currentState = $attentionModel->getCurrentState($userId);

        return $currentState ?: 'focused'; // Default if no history
    }

    /**
     * Get attention state history
     */
    private function getAttentionStateHistory(int $userId): array
    {
        $attentionModel = new \Leantime\Plugins\Dopemux\Models\AttentionStateHistory();
        $rawHistory = $attentionModel->getUserHistory($userId, 10);

        // Format for template compatibility
        return array_map(function($record) {
            return [
                'timestamp' => date('Y-m-d H:i', strtotime($record['created_at'])),
                'state' => $record['state']
            ];
        }, $rawHistory);
    }

    /**
     * Get attention suggestions
     */
    private function getAttentionSuggestions(string $currentState): array
    {
        switch ($currentState) {
            case 'hyperfocus':
                return [
                    'message' => 'You\'re in hyperfocus! Great time for complex work.',
                    'suggestions' => ['Work on challenging problems', 'Set a timer to avoid burnout', 'Stay hydrated']
                ];
            case 'focused':
                return [
                    'message' => 'Good focused state for productive work.',
                    'suggestions' => ['Continue current tasks', 'Plan next priorities', 'Maintain rhythm']
                ];
            case 'scattered':
                return [
                    'message' => 'Attention seems scattered. Try easier tasks.',
                    'suggestions' => ['Do quick admin tasks', 'Organize workspace', 'Take a short break']
                ];
            default:
                return [
                    'message' => 'Attention state unknown.',
                    'suggestions' => ['Assess current mental state', 'Choose appropriate tasks']
                ];
        }
    }

    /**
     * Get saved contexts
     */
    private function getSavedContexts(int $userId): array
    {
        $contextModel = new \Leantime\Plugins\Dopemux\Models\ContextSnapshot();
        $snapshots = $contextModel->getUserSnapshots($userId, 10);

        // Format for template compatibility
        return array_map(function($snapshot) {
            return [
                'id' => $snapshot['id'],
                'name' => $snapshot['name'],
                'saved_at' => date('Y-m-d H:i', strtotime($snapshot['created_at']))
            ];
        }, $snapshots);
    }

    /**
     * Get current context
     */
    private function getCurrentContext(int $userId): array
    {
        // This would ideally come from session data or user preferences
        // For now, return a basic structure
        return [
            'active_project' => $_SESSION['currentProject']['name'] ?? 'Dopemux MVP',
            'active_tickets' => $_SESSION['currentProject']['tickets'] ?? [],
            'open_files' => [],
            'notes' => $_SESSION['currentProject']['notes'] ?? 'No current notes'
        ];
    }

    /**
     * Set cognitive load
     */
    private function setCognitiveLoad(int $userId, int $load): bool
    {
        try {
            $cognitiveModel = new \Leantime\Plugins\Dopemux\Models\CognitiveLoadHistory();
            return $cognitiveModel->recordLoad($userId, $load, 'user_input');
        } catch (\Exception $e) {
            error_log('Dopemux setCognitiveLoad error for user ' . $userId . ': ' . $e->getMessage());
            return false;
        }
    }

    /**
     * Set attention state
     */
    private function setAttentionState(int $userId, string $state): bool
    {
        try {
            $attentionModel = new \Leantime\Plugins\Dopemux\Models\AttentionStateHistory();
            return $attentionModel->recordState($userId, $state, 'user_input');
        } catch (\Exception $e) {
            error_log('Dopemux setAttentionState error for user ' . $userId . ': ' . $e->getMessage());
            return false;
        }
    }

    /**
     * Save user context
     */
    private function saveUserContext(int $userId, string $name, array $contextData): ?int
    {
        try {
            $contextModel = new \Leantime\Plugins\Dopemux\Models\ContextSnapshot();
            $success = $contextModel->saveSnapshot($userId, $name, $contextData);

            if ($success) {
                // Get the last inserted ID (simplified approach)
                $pdo = $this->db ?? null;
                if ($pdo) {
                    return (int) $pdo->lastInsertId();
                }
            }

            return null;
        } catch (\Exception $e) {
            error_log('Dopemux saveUserContext error for user ' . $userId . ': ' . $e->getMessage());
            return null;
        }
    }

    /**
     * Restore user context
     */
    private function restoreUserContext(int $userId, int $contextId): ?array
    {
        try {
            $contextModel = new \Leantime\Plugins\Dopemux\Models\ContextSnapshot();
            $snapshot = $contextModel->getSnapshot($userId, $contextId);

            return $snapshot ? $snapshot['snapshot_data'] : null;
        } catch (\Exception $e) {
            error_log('Dopemux restoreUserContext error for user ' . $userId . ': ' . $e->getMessage());
            return null;
        }
    }

    /**
     * Set break reminder preference
     */
    private function setBreakReminderPreference(int $userId, int $frequency, bool $enabled): bool
    {
        $breakModel = new \Leantime\Plugins\Dopemux\Models\BreakReminderSettings();
        return $breakModel->updateUserSettings($userId, $frequency, $enabled);
    }

    /**
     * Check if break is due for user
     */
    private function isBreakDue(int $userId): bool
    {
        $breakModel = new \Leantime\Plugins\Dopemux\Models\BreakReminderSettings();
        return $breakModel->isBreakDue($userId);
    }

    /**
     * Get cognitive load limit for current user
     */
    private function getCognitiveLoadLimit(): int
    {
        // This would fetch from user preferences
        return 8; // Default limit
    }
}