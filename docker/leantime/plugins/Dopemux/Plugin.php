<?php

namespace Leantime\Plugins\Dopemux;

use Leantime\Plugins\Dopemux\Services\TaskOrchestratorClient;
use Exception;

/**
 * Dopemux ADHD Plugin for Leantime
 *
 * Main plugin class following Leantime's plugin structure
 * Provides ADHD-optimized project management features through Task Orchestrator integration
 */
class Plugin
{
    private TaskOrchestratorClient $taskClient;

    /**
     * Plugin initialization
     * Called when the plugin is loaded
     */
    public function init()
    {
        // Plugin is initialized
        error_log("=== Dopemux Plugin::init() called ===");
        error_log("Dopemux Plugin initialized successfully");

        // Initialize Task Orchestrator client
        $this->taskClient = new TaskOrchestratorClient();

        // Register hooks for task synchronization
        $this->registerHooks();

        // Add custom routes for ADHD features
        $this->registerRoutes();

        error_log("Dopemux Plugin: Task synchronization hooks registered");
    }

    /**
     * Plugin installation
     * Called when the plugin is first installed
     */
    public function install()
    {
        error_log("=== Dopemux Plugin::install() called ===");

        try {
            // Test connection to Task Orchestrator
            $this->testTaskOrchestratorConnection();

            error_log("Dopemux Plugin: Task Orchestrator connection verified");
            error_log("Dopemux Plugin installed successfully");
            return true;
        } catch (Exception $e) {
            error_log("Dopemux Plugin installation failed: " . $e->getMessage());
            return false;
        }
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

    /**
     * Register Leantime hooks for task synchronization
     */
    private function registerHooks()
    {
        // Hook into task creation/update events
        add_action('task_created', [$this, 'syncTaskToOrchestrator']);
        add_action('task_updated', [$this, 'syncTaskToOrchestrator']);
        add_action('task_deleted', [$this, 'removeTaskFromOrchestrator']);

        // Hook into project events
        add_action('project_created', [$this, 'syncProjectToOrchestrator']);
        add_action('project_updated', [$this, 'syncProjectToOrchestrator']);

        // Add periodic sync hook (runs every 15 minutes)
        add_action('dopemux_periodic_sync', [$this, 'performBidirectionalSync']);

        // Schedule the periodic sync if WP cron is available
        if (function_exists('wp_schedule_event')) {
            if (!wp_next_scheduled('dopemux_periodic_sync')) {
                wp_schedule_event(time(), '15min', 'dopemux_periodic_sync');
            }
        }
    }

    /**
     * Register custom routes for ADHD features
     */
    private function registerRoutes()
    {
        // Add REST API routes for ADHD features
        add_action('rest_api_init', function() {
            // ADHD dashboard route
            register_rest_route('dopemux/v1', '/dashboard', [
                'methods' => 'GET',
                'callback' => [$this, 'getAdhdDashboard'],
                'permission_callback' => '__return_true'
            ]);

            // Task recommendations route
            register_rest_route('dopemux/v1', '/recommendations', [
                'methods' => 'GET',
                'callback' => [$this, 'getTaskRecommendations'],
                'permission_callback' => '__return_true'
            ]);

            // ADHD state route
            register_rest_route('dopemux/v1', '/adhd-state', [
                'methods' => 'GET',
                'callback' => [$this, 'getAdhdState'],
                'permission_callback' => '__return_true'
            ]);

            // Task management routes
            register_rest_route('dopemux/v1', '/tasks/(?P<id>\d+)/start', [
                'methods' => 'POST',
                'callback' => [$this, 'startTask'],
                'permission_callback' => '__return_true',
                'args' => [
                    'id' => [
                        'required' => true,
                        'validate_callback' => function($param) {
                            return is_numeric($param);
                        }
                    ]
                ]
            ]);

            register_rest_route('dopemux/v1', '/tasks/(?P<id>\d+)/adhd-metadata', [
                'methods' => 'GET',
                'callback' => [$this, 'getTaskAdhdMetadata'],
                'permission_callback' => '__return_true',
                'args' => [
                    'id' => [
                        'required' => true,
                        'validate_callback' => function($param) {
                            return is_numeric($param);
                        }
                    ]
                ]
            ]);
        });

        // Add menu items for ADHD features
        add_action('admin_menu', function() {
            add_menu_page(
                'Dopemux ADHD Settings',
                'Dopemux ADHD',
                'manage_options',
                'dopemux-settings',
                [$this, 'renderSettingsPage'],
                'dashicons-brain',
                30
            );
        });

        // Add submenu items
        add_action('admin_menu', function() {
            add_submenu_page(
                'dopemux-settings',
                'ADHD Dashboard',
                'Dashboard',
                'manage_options',
                'dopemux-dashboard',
                [$this, 'renderDashboardPage']
            );

            add_submenu_page(
                'dopemux-settings',
                'Task Recommendations',
                'Recommendations',
                'manage_options',
                'dopemux-recommendations',
                [$this, 'renderRecommendationsPage']
            );
        });
    }

    /**
     * Render settings page for WordPress admin
     */
    public function renderSettingsPage()
    {
        // Get current settings
        $settings = [
            'workspace_id' => get_option('dopemux_workspace_id', '/Users/hue/code/dopemux-mvp'),
            'api_url' => get_option('dopemux_api_url', 'http://localhost:3016'),
            'sync_enabled' => get_option('dopemux_sync_enabled', '1'),
            'sync_interval' => get_option('dopemux_sync_interval', '15')
        ];

        // Handle form submission
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            $this->saveSettings();
            echo '<div class="notice notice-success"><p>Settings saved successfully!</p></div>';
        }

        // Render settings form
        include plugin_dir_path(__FILE__) . '../Views/settings.php';
    }

    /**
     * Render dashboard page
     */
    public function renderDashboardPage()
    {
        try {
            $dashboard = $this->taskClient->getAdhdState();
            echo '<div class="wrap">';
            echo '<h1>Dopemux ADHD Dashboard</h1>';
            echo '<pre>' . json_encode($dashboard, JSON_PRETTY_PRINT) . '</pre>';
            echo '</div>';
        } catch (Exception $e) {
            echo '<div class="wrap">';
            echo '<h1>Dopemux ADHD Dashboard</h1>';
            echo '<div class="notice notice-error"><p>Failed to load dashboard: ' . $e->getMessage() . '</p></div>';
            echo '</div>';
        }
    }

    /**
     * Render recommendations page
     */
    public function renderRecommendationsPage()
    {
        try {
            $recommendations = $this->taskClient->getRecommendations();
            echo '<div class="wrap">';
            echo '<h1>Dopemux Task Recommendations</h1>';
            echo '<pre>' . json_encode($recommendations, JSON_PRETTY_PRINT) . '</pre>';
            echo '</div>';
        } catch (Exception $e) {
            echo '<div class="wrap">';
            echo '<h1>Dopemux Task Recommendations</h1>';
            echo '<div class="notice notice-error"><p>Failed to load recommendations: ' . $e->getMessage() . '</p></div>';
            echo '</div>';
        }
    }

    /**
     * Sync Leantime task to Task Orchestrator
     *
     * @param array $task Leantime task data
     */
    public function syncTaskToOrchestrator($task)
    {
        try {
            error_log("Dopemux Plugin: Syncing task to orchestrator - ID: " . ($task['id'] ?? 'unknown'));

            // Map Leantime task to Task Orchestrator format
            $orchestratorTask = $this->mapLeantimeTaskToOrchestrator($task);

            // Check if task exists in orchestrator
            $existingTask = $this->findTaskInOrchestrator($task['id']);

            if ($existingTask) {
                // Update existing task
                $this->taskClient->updateTask($existingTask['task_id'], $orchestratorTask);
                error_log("Dopemux Plugin: Updated task in orchestrator");
            } else {
                // Create new task
                $result = $this->taskClient->createTask($orchestratorTask);
                error_log("Dopemux Plugin: Created new task in orchestrator - ID: " . ($result['task_id'] ?? 'unknown'));
            }

        } catch (Exception $e) {
            error_log("Dopemux Plugin: Failed to sync task to orchestrator: " . $e->getMessage());
        }
    }

    /**
     * Remove task from Task Orchestrator
     *
     * @param array $task Leantime task data
     */
    public function removeTaskFromOrchestrator($task)
    {
        try {
            error_log("Dopemux Plugin: Removing task from orchestrator - ID: " . ($task['id'] ?? 'unknown'));

            $existingTask = $this->findTaskInOrchestrator($task['id']);
            if ($existingTask) {
                // Note: Task Orchestrator might not have delete endpoint, log decision instead
                $this->taskClient->logDecision([
                    'summary' => "Task {$task['id']} deleted from Leantime",
                    'rationale' => 'Task was removed from Leantime project management',
                    'tags' => ['task-sync', 'deletion']
                ]);
            }

        } catch (Exception $e) {
            error_log("Dopemux Plugin: Failed to remove task from orchestrator: " . $e->getMessage());
        }
    }

    /**
     * Sync Leantime project to Task Orchestrator
     *
     * @param array $project Leantime project data
     */
    public function syncProjectToOrchestrator($project)
    {
        try {
            error_log("Dopemux Plugin: Syncing project to orchestrator - ID: " . ($project['id'] ?? 'unknown'));

            // Log project creation/update as decision
            $this->taskClient->logDecision([
                'summary' => "Project '{$project['name']}' " . (isset($project['id']) ? 'updated' : 'created') . " in Leantime",
                'rationale' => 'Project synchronization between Leantime and Dopemux',
                'tags' => ['project-sync', 'integration']
            ]);

        } catch (Exception $e) {
            error_log("Dopemux Plugin: Failed to sync project to orchestrator: " . $e->getMessage());
        }
    }

    /**
     * Get ADHD dashboard data
     *
     * @return array Dashboard data
     */
    public function getAdhdDashboard()
    {
        try {
            $dashboard = [
                'adhd_state' => $this->taskClient->getAdhdState(),
                'active_sprint' => $this->taskClient->getActiveSprint(),
                'session' => $this->taskClient->getSession(),
                'recent_activity' => $this->taskClient->getRecentActivity(24)
            ];

            return [
                'success' => true,
                'data' => $dashboard
            ];

        } catch (Exception $e) {
            error_log("Dopemux Plugin: Failed to get ADHD dashboard: " . $e->getMessage());
            return [
                'success' => false,
                'error' => $e->getMessage()
            ];
        }
    }

    /**
     * Perform bidirectional task synchronization
     * Pulls tasks from Task Orchestrator and pushes to Leantime
     */
    public function performBidirectionalSync()
    {
        try {
            error_log("Dopemux Plugin: Starting bidirectional task sync");

            // Pull tasks from Task Orchestrator
            $tasks = $this->taskClient->getTasks([
                'status' => 'TODO,IN_PROGRESS',
                'limit' => 50
            ]);

            $syncedCount = 0;
            foreach ($tasks as $task) {
                $leantimeId = $task['metadata']['leantime_id'] ?? null;
                if ($leantimeId) {
                    // Task already synced, check for updates
                    $this->updateLeantimeTask($leantimeId, $task);
                } else {
                    // New task, create in Leantime
                    $this->createLeantimeTask($task);
                    $syncedCount++;
                }
            }

            error_log("Dopemux Plugin: Bidirectional sync completed - synced {$syncedCount} new tasks");

        } catch (Exception $e) {
            error_log("Dopemux Plugin: Failed to perform bidirectional sync: " . $e->getMessage());
        }
    }

    /**
     * Create task in Leantime from Task Orchestrator data
     *
     * @param array $orchestratorTask Task data from orchestrator
     * @return int|false Leantime task ID or false on failure
     */
    private function createLeantimeTask($orchestratorTask)
    {
        global $tpl, $language, $db_plugin;

        try {
            $title = $orchestratorTask['title'];
            $description = $orchestratorTask['description'];
            $priority = $this->mapOrchestratorPriority($orchestratorTask['priority']);
            $status = $this->mapOrchestratorStatus($orchestratorTask['status']);

            $sql = "INSERT INTO zp_tasks (title, description, status, priority, projectId, dateCreated, lastUpdated) VALUES (?, ?, ?, ?, ?, NOW(), NOW())";
            $stmt = $db_plugin->prepare($sql);
            $result = $stmt->execute([$title, $description, $status, $priority, 1]); // Assuming project ID 1

            if ($result) {
                $taskId = $db_plugin->lastInsertId();

                // Update metadata in orchestrator
                $this->taskClient->updateTask($orchestratorTask['task_id'], [
                    'metadata' => [
                        'leantime_id' => $taskId,
                        'sync_timestamp' => date('c')
                    ]
                ]);

                error_log("Dopemux Plugin: Created Leantime task {$taskId} from orchestrator task {$orchestratorTask['task_id']}");
                return $taskId;
            }

            return false;

        } catch (Exception $e) {
            error_log("Dopemux Plugin: Failed to create Leantime task: " . $e->getMessage());
            return false;
        }
    }

    /**
     * Update Leantime task from Task Orchestrator data
     *
     * @param int $leantimeId Leantime task ID
     * @param array $orchestratorTask Task data from orchestrator
     * @return bool Success status
     */
    private function updateLeantimeTask($leantimeId, $orchestratorTask)
    {
        global $db_plugin;

        try {
            $title = $orchestratorTask['title'];
            $description = $orchestratorTask['description'];
            $status = $this->mapOrchestratorStatus($orchestratorTask['status']);
            $priority = $this->mapOrchestratorPriority($orchestratorTask['priority']);

            $sql = "UPDATE zp_tasks SET title = ?, description = ?, status = ?, priority = ?, lastUpdated = NOW() WHERE id = ?";
            $stmt = $db_plugin->prepare($sql);
            $result = $stmt->execute([$title, $description, $status, $priority, $leantimeId]);

            if ($result) {
                error_log("Dopemux Plugin: Updated Leantime task {$leantimeId} from orchestrator");
                return true;
            }

            return false;

        } catch (Exception $e) {
            error_log("Dopemux Plugin: Failed to update Leantime task {$leantimeId}: " . $e->getMessage());
            return false;
        }
    }

    /**
     * Map Task Orchestrator priority to Leantime priority
     *
     * @param int $orchestratorPriority Orchestrator priority (1-5)
     * @return string Leantime priority (low, medium, high)
     */
    private function mapOrchestratorPriority($orchestratorPriority)
    {
        if ($orchestratorPriority >= 4) return 'high';
        if ($orchestratorPriority >= 3) return 'medium';
        return 'low';
    }

    /**
     * Map Task Orchestrator status to Leantime status
     *
     * @param string $orchestratorStatus Orchestrator status
     * @return string Leantime status
     */
    private function mapOrchestratorStatus($orchestratorStatus)
    {
        $statusMap = [
            'TODO' => 'new',
            'IN_PROGRESS' => 'in_progress',
            'DONE' => 'done'
        ];

        return $statusMap[$orchestratorStatus] ?? 'new';
    }

    /**
     * Get task recommendations
     *
     * @return array Recommendations data
     */
    public function getTaskRecommendations()
    {
        try {
            $recommendations = $this->taskClient->getRecommendations();

            return [
                'success' => true,
                'data' => $recommendations
            ];

        } catch (Exception $e) {
            error_log("Dopemux Plugin: Failed to get task recommendations: " . $e->getMessage());
            return [
                'success' => false,
                'error' => $e->getMessage()
            ];
        }
    }

    /**
     * Get current ADHD state
     *
     * @return array ADHD state data
     */
    public function getAdhdState()
    {
        try {
            $state = $this->taskClient->getAdhdState();

            return [
                'success' => true,
                'data' => $state
            ];

        } catch (Exception $e) {
            error_log("Dopemux Plugin: Failed to get ADHD state: " . $e->getMessage());
            return [
                'success' => false,
                'error' => $e->getMessage()
            ];
        }
    }

    /**
     * Start a task (update ADHD session state)
     *
     * @param WP_REST_Request $request Request object
     * @return array Response data
     */
    public function startTask($request)
    {
        try {
            $taskId = $request->get_param('id');

            // Update task status in Leantime
            global $db_plugin;
            $sql = "UPDATE zp_tasks SET status = 'in_progress', lastUpdated = NOW() WHERE id = ?";
            $stmt = $db_plugin->prepare($sql);
            $stmt->execute([$taskId]);

            // Update Task Orchestrator
            $this->taskClient->updateTaskStatus($taskId, 'IN_PROGRESS');

            // Log to ADHD session
            $this->taskClient->logDecision([
                'summary' => "Started working on task {$taskId}",
                'rationale' => 'Task initiation through ADHD-optimized interface',
                'tags' => ['task-start', 'adhd-session', 'productivity']
            ]);

            return [
                'success' => true,
                'message' => 'Task started successfully',
                'task_id' => $taskId
            ];

        } catch (Exception $e) {
            error_log("Dopemux Plugin: Failed to start task {$taskId}: " . $e->getMessage());
            return [
                'success' => false,
                'error' => $e->getMessage()
            ];
        }
    }

    /**
     * Get ADHD metadata for a task
     *
     * @param WP_REST_Request $request Request object
     * @return array ADHD metadata
     */
    public function getTaskAdhdMetadata($request)
    {
        try {
            $taskId = $request->get_param('id');

            // Get task from Leantime
            global $db_plugin;
            $sql = "SELECT * FROM zp_tasks WHERE id = ?";
            $stmt = $db_plugin->prepare($sql);
            $stmt->execute([$taskId]);
            $task = $stmt->fetch();

            if (!$task) {
                return [
                    'success' => false,
                    'error' => 'Task not found'
                ];
            }

            // Generate ADHD metadata based on task properties
            $metadata = $this->generateAdhdMetadata($task);

            return [
                'success' => true,
                'data' => $metadata
            ];

        } catch (Exception $e) {
            error_log("Dopemux Plugin: Failed to get ADHD metadata for task {$taskId}: " . $e->getMessage());
            return [
                'success' => false,
                'error' => $e->getMessage()
            ];
        }
    }

    /**
     * Generate ADHD metadata for a task based on its properties
     *
     * @param array $task Leantime task data
     * @return array ADHD metadata
     */
    private function generateAdhdMetadata($task)
    {
        $complexity = $this->estimateComplexity($task);
        $descriptionLength = strlen($task['description'] ?? '');

        // Determine energy requirements
        $energyRequired = 'medium';
        if ($complexity >= 0.8 || $descriptionLength > 1000) {
            $energyRequired = 'high';
        } elseif ($complexity <= 0.3 && $descriptionLength < 100) {
            $energyRequired = 'low';
        }

        // Estimate focus time based on complexity
        $estimatedFocusTime = $this->estimateDuration($task);

        // Generate insights based on task characteristics
        $insights = $this->generateTaskInsights($task, $complexity, $energyRequired);

        return [
            'complexity' => $complexity,
            'energy_required' => $energyRequired,
            'estimated_focus_time' => $estimatedFocusTime,
            'insights' => $insights,
            'cognitive_load_level' => $this->getCognitiveLoadLevel($complexity),
            'recommended_session_type' => $this->getRecommendedSessionType($complexity, $energyRequired),
            'break_frequency' => $this->getBreakFrequency($complexity),
            'generated_at' => date('c')
        ];
    }

    /**
     * Generate personalized insights for a task
     *
     * @param array $task Task data
     * @param float $complexity Complexity score
     * @param string $energyRequired Energy level
     * @return string Insight message
     */
    private function generateTaskInsights($task, $complexity, $energyRequired)
    {
        $insights = [];

        if ($complexity >= 0.8) {
            $insights[] = "This is a high-complexity task. Consider breaking it into smaller, focused sessions.";
        }

        if ($energyRequired === 'high') {
            $insights[] = "High energy task detected. Schedule during your peak energy hours.";
        }

        if (strlen($task['description'] ?? '') < 50) {
            $insights[] = "Task description is brief. Consider adding more context to reduce cognitive overhead.";
        }

        if ($task['priority'] === 'urgent') {
            $insights[] = "Urgent priority task. Balance with regular breaks to maintain focus quality.";
        }

        return empty($insights) ? "Standard task complexity. Good candidate for regular workflow." : implode(" ", $insights);
    }

    /**
     * Get cognitive load level description
     *
     * @param float $complexity Complexity score
     * @return string Load level
     */
    private function getCognitiveLoadLevel($complexity)
    {
        if ($complexity >= 0.8) return 'Very High';
        if ($complexity >= 0.6) return 'High';
        if ($complexity >= 0.4) return 'Medium';
        if ($complexity >= 0.2) return 'Low';
        return 'Very Low';
    }

    /**
     * Get recommended session type
     *
     * @param float $complexity Complexity score
     * @param string $energyRequired Energy level
     * @return string Session type recommendation
     */
    private function getRecommendedSessionType($complexity, $energyRequired)
    {
        if ($complexity >= 0.7 && $energyRequired === 'high') {
            return 'Deep Focus Session (90-120 minutes)';
        } elseif ($complexity >= 0.5) {
            return 'Focused Work Session (45-60 minutes)';
        } else {
            return 'Standard Work Session (25-45 minutes)';
        }
    }

    /**
     * Get recommended break frequency
     *
     * @param float $complexity Complexity score
     * @return string Break frequency
     */
    private function getBreakFrequency($complexity)
    {
        if ($complexity >= 0.8) return 'Every 25-30 minutes';
        if ($complexity >= 0.6) return 'Every 45-50 minutes';
        if ($complexity >= 0.4) return 'Every 60-75 minutes';
        return 'Every 90 minutes or as needed';
    }

    /**
     * Map Leantime task to Task Orchestrator format
     *
     * @param array $leantimeTask Leantime task data
     * @return array Task Orchestrator format
     */
    private function mapLeantimeTaskToOrchestrator($leantimeTask)
    {
        // Map Leantime status to Task Orchestrator status
        $statusMap = [
            'new' => 'TODO',
            'in_progress' => 'IN_PROGRESS',
            'done' => 'DONE',
            'blocked' => 'TODO' // Map blocked to TODO for now
        ];

        return [
            'title' => $leantimeTask['title'] ?? 'Untitled Task',
            'description' => $leantimeTask['description'] ?? '',
            'status' => $statusMap[$leantimeTask['status'] ?? 'new'] ?? 'TODO',
            'priority' => $this->mapLeantimePriority($leantimeTask['priority'] ?? 'medium'),
            'complexity' => $this->estimateComplexity($leantimeTask),
            'estimated_duration' => $this->estimateDuration($leantimeTask),
            'dependencies' => [],
            'tags' => ['leantime-sync', 'project-' . ($leantimeTask['projectId'] ?? 'unknown')],
            'external_id' => 'leantime_' . $leantimeTask['id'],
            'metadata' => [
                'leantime_id' => $leantimeTask['id'],
                'leantime_project' => $leantimeTask['projectId'] ?? null,
                'sync_timestamp' => date('c')
            ]
        ];
    }

    /**
     * Find task in Task Orchestrator by Leantime ID
     *
     * @param int $leantimeId Leantime task ID
     * @return array|null Task data or null if not found
     */
    private function findTaskInOrchestrator($leantimeId)
    {
        try {
            $tasks = $this->taskClient->getTasks();
            foreach ($tasks as $task) {
                if (isset($task['metadata']['leantime_id']) && $task['metadata']['leantime_id'] == $leantimeId) {
                    return $task;
                }
            }
        } catch (Exception $e) {
            error_log("Dopemux Plugin: Error finding task in orchestrator: " . $e->getMessage());
        }
        return null;
    }

    /**
     * Map Leantime priority to Task Orchestrator priority
     *
     * @param string $leantimePriority Leantime priority
     * @return int Task Orchestrator priority (1-5)
     */
    private function mapLeantimePriority($leantimePriority)
    {
        $priorityMap = [
            'low' => 1,
            'medium' => 3,
            'high' => 5,
            'urgent' => 5
        ];

        return $priorityMap[$leantimePriority] ?? 3;
    }

    /**
     * Estimate task complexity based on Leantime task data
     *
     * @param array $task Leantime task data
     * @return float Complexity score (0.0-1.0)
     */
    private function estimateComplexity($task)
    {
        $complexity = 0.3; // Base complexity

        // Increase based on description length (longer = more complex)
        $descLength = strlen($task['description'] ?? '');
        if ($descLength > 500) $complexity += 0.3;
        elseif ($descLength > 100) $complexity += 0.1;

        // Increase for high priority
        if (($task['priority'] ?? 'medium') === 'urgent') $complexity += 0.2;

        return min(1.0, $complexity);
    }

    /**
     * Estimate task duration in minutes
     *
     * @param array $task Leantime task data
     * @return int Estimated duration in minutes
     */
    private function estimateDuration($task)
    {
        $complexity = $this->estimateComplexity($task);

        // Base duration on complexity
        if ($complexity >= 0.8) return 480; // 8 hours
        if ($complexity >= 0.6) return 240; // 4 hours
        if ($complexity >= 0.4) return 120; // 2 hours
        return 60; // 1 hour
    }

    /**
     * Test connection to Task Orchestrator
     *
     * @throws Exception If connection fails
     */
    private function testTaskOrchestratorConnection()
    {
        try {
            $this->taskClient->getAdhdState();
        } catch (Exception $e) {
            throw new Exception("Cannot connect to Task Orchestrator: " . $e->getMessage());
        }
    }
}