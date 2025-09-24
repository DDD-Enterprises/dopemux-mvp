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
        $userId = $_SESSION['userdata']['id'] ?? null;

        if (!$userId) {
            return new JsonResponse(['error' => 'Not authenticated'], 401);
        }

        $requestData = json_decode(file_get_contents('php://input'), true);
        $newLoad = $requestData['cognitive_load'] ?? null;

        if ($newLoad === null || !is_numeric($newLoad) || $newLoad < 1 || $newLoad > 10) {
            return new JsonResponse(['error' => 'Invalid cognitive load value'], 400);
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
        $userId = $_SESSION['userdata']['id'] ?? null;

        if (!$userId) {
            return new JsonResponse(['error' => 'Not authenticated'], 401);
        }

        $requestData = json_decode(file_get_contents('php://input'), true);
        $newState = $requestData['attention_state'] ?? null;

        $validStates = ['hyperfocus', 'focused', 'scattered', 'background', 'transition'];

        if (!in_array($newState, $validStates)) {
            return new JsonResponse(['error' => 'Invalid attention state'], 400);
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
    }

    /**
     * Save context (API)
     */
    public function saveContext(): JsonResponse
    {
        $userId = $_SESSION['userdata']['id'] ?? null;

        if (!$userId) {
            return new JsonResponse(['error' => 'Not authenticated'], 401);
        }

        $requestData = json_decode(file_get_contents('php://input'), true);
        $contextName = $requestData['context_name'] ?? 'Auto-saved Context';
        $contextData = $requestData['context_data'] ?? [];

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
    }

    /**
     * Restore context (API)
     */
    public function restoreContext(): JsonResponse
    {
        $userId = $_SESSION['userdata']['id'] ?? null;

        if (!$userId) {
            return new JsonResponse(['error' => 'Not authenticated'], 401);
        }

        $contextId = $_GET['context_id'] ?? null;

        if (!$contextId) {
            return new JsonResponse(['error' => 'Context ID required'], 400);
        }

        $contextData = $this->restoreUserContext($userId, $contextId);

        if ($contextData) {
            return new JsonResponse([
                'success' => true,
                'context_data' => $contextData,
                'timestamp' => date('c')
            ]);
        } else {
            return new JsonResponse(['error' => 'Failed to restore context'], 500);
        }
    }

    /**
     * Set break reminder (API)
     */
    public function setBreakReminder(): JsonResponse
    {
        $userId = $_SESSION['userdata']['id'] ?? null;

        if (!$userId) {
            return new JsonResponse(['error' => 'Not authenticated'], 401);
        }

        $requestData = json_decode(file_get_contents('php://input'), true);
        $frequency = $requestData['frequency'] ?? 25; // Default 25 minutes
        $enabled = $requestData['enabled'] ?? true;

        $success = $this->setBreakReminderPreference($userId, $frequency, $enabled);

        if ($success) {
            return new JsonResponse([
                'success' => true,
                'frequency' => $frequency,
                'enabled' => $enabled,
                'timestamp' => date('c')
            ]);
        } else {
            return new JsonResponse(['error' => 'Failed to set break reminder'], 500);
        }
    }

    // Helper Methods

    /**
     * Get current ADHD state for user
     */
    private function getADHDState(int $userId): array
    {
        // This would fetch from database
        return [
            'attention_state' => 'focused',
            'cognitive_load' => 5,
            'break_due' => false,
            'context_preserved' => true,
            'last_updated' => date('c')
        ];
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
        return [
            'next_break' => '25 minutes',
            'break_type' => 'short',
            'reminders_enabled' => true
        ];
    }

    /**
     * Get context status
     */
    private function getContextStatus(int $userId): array
    {
        return [
            'auto_save_enabled' => true,
            'last_save' => '5 minutes ago',
            'saved_contexts' => 3
        ];
    }

    /**
     * Get current cognitive load
     */
    private function getCurrentCognitiveLoad(int $userId): int
    {
        // This would fetch from user preferences or current session
        return 5; // Default moderate load
    }

    /**
     * Get cognitive load history
     */
    private function getCognitiveLoadHistory(int $userId): array
    {
        // This would fetch historical data
        return [
            ['timestamp' => '2025-01-20 10:00', 'load' => 3],
            ['timestamp' => '2025-01-20 11:00', 'load' => 5],
            ['timestamp' => '2025-01-20 12:00', 'load' => 7],
        ];
    }

    /**
     * Get cognitive load recommendations
     */
    private function getCognitiveLoadRecommendations(int $currentLoad): array
    {
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
    }

    /**
     * Get current attention state
     */
    private function getCurrentAttentionState(int $userId = null): string
    {
        // This would fetch from user session or preferences
        return 'focused'; // Default state
    }

    /**
     * Get attention state history
     */
    private function getAttentionStateHistory(int $userId): array
    {
        return [
            ['timestamp' => '2025-01-20 09:00', 'state' => 'scattered'],
            ['timestamp' => '2025-01-20 10:00', 'state' => 'focused'],
            ['timestamp' => '2025-01-20 11:00', 'state' => 'hyperfocus'],
        ];
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
        return [
            ['id' => 1, 'name' => 'Feature Development', 'saved_at' => '2025-01-20 10:00'],
            ['id' => 2, 'name' => 'Bug Fixing Session', 'saved_at' => '2025-01-19 15:30'],
            ['id' => 3, 'name' => 'Code Review', 'saved_at' => '2025-01-19 09:15'],
        ];
    }

    /**
     * Get current context
     */
    private function getCurrentContext(int $userId): array
    {
        return [
            'active_project' => 'Dopemux MVP',
            'active_tickets' => [1, 3, 7],
            'open_files' => ['bridge.py', 'client.py'],
            'notes' => 'Working on JSON-RPC integration'
        ];
    }

    /**
     * Set cognitive load
     */
    private function setCognitiveLoad(int $userId, int $load): bool
    {
        // This would store in database
        return true; // Placeholder
    }

    /**
     * Set attention state
     */
    private function setAttentionState(int $userId, string $state): bool
    {
        // This would store in database
        return true; // Placeholder
    }

    /**
     * Save user context
     */
    private function saveUserContext(int $userId, string $name, array $contextData): ?int
    {
        // This would store in database and return context ID
        return rand(1000, 9999); // Placeholder
    }

    /**
     * Restore user context
     */
    private function restoreUserContext(int $userId, int $contextId): ?array
    {
        // This would fetch from database
        return [
            'active_project' => 'Dopemux MVP',
            'active_tickets' => [1, 3, 7],
            'notes' => 'Restored context'
        ]; // Placeholder
    }

    /**
     * Set break reminder preference
     */
    private function setBreakReminderPreference(int $userId, int $frequency, bool $enabled): bool
    {
        // This would store in user preferences
        return true; // Placeholder
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