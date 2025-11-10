<?php

namespace Leantime\Plugins\Dopemux\Services;

use Exception;

/**
 * Task Orchestrator Client for Dopemux Leantime Plugin
 *
 * Provides communication with the MCP Integration Bridge to access Task Orchestrator
 * functionality for ADHD-optimized project management and task synchronization.
 */
class TaskOrchestratorClient
{
    private string $workspaceId;
    private string $baseUrl;
    private int $timeout = 30;

    /**
     * Constructor
     *
     * @param string $workspaceId The workspace identifier (absolute path)
     * @param string $baseUrl Base URL for MCP Integration Bridge
     */
    public function __construct(string $workspaceId = '/Users/hue/code/dopemux-mvp', string $baseUrl = 'http://localhost:3016')
    {
        $this->workspaceId = $workspaceId;
        $this->baseUrl = $baseUrl;
    }

    /**
     * Get active sprint information
     *
     * @return array Active sprint data
     * @throws Exception
     */
    public function getActiveSprint(): array
    {
        return $this->makeRequest('GET', '/orchestrator/active-sprint');
    }

    /**
     * Get current ADHD state
     *
     * @return array ADHD state information
     * @throws Exception
     */
    public function getAdhdState(): array
    {
        return $this->makeRequest('GET', '/orchestrator/adhd-state');
    }

    /**
     * Get task recommendations
     *
     * @param array $context Optional context for recommendations
     * @return array Task recommendations
     * @throws Exception
     */
    public function getRecommendations(array $context = []): array
    {
        $url = '/orchestrator/recommendations';
        if (!empty($context)) {
            $query = http_build_query($context);
            $url .= '?' . $query;
        }
        return $this->makeRequest('GET', $url);
    }

    /**
     * Get session information
     *
     * @return array Session data
     * @throws Exception
     */
    public function getSession(): array
    {
        return $this->makeRequest('GET', '/orchestrator/session');
    }

    /**
     * Get all tasks from Task Orchestrator
     *
     * @param array $filters Optional filters (status, priority, etc.)
     * @return array Tasks list
     * @throws Exception
     */
    public function getTasks(array $filters = []): array
    {
        $url = '/orchestrator/tasks';
        if (!empty($filters)) {
            $query = http_build_query($filters);
            $url .= '?' . $query;
        }
        return $this->makeRequest('GET', $url);
    }

    /**
     * Get specific task by ID
     *
     * @param string $taskId Task identifier
     * @return array Task details
     * @throws Exception
     */
    public function getTask(string $taskId): array
    {
        return $this->makeRequest('GET', "/orchestrator/tasks/{$taskId}");
    }

    /**
     * Update task status
     *
     * @param string $taskId Task identifier
     * @param string $status New status (TODO, IN_PROGRESS, DONE)
     * @param array $additionalData Additional update data
     * @return array Updated task data
     * @throws Exception
     */
    public function updateTaskStatus(string $taskId, string $status, array $additionalData = []): array
    {
        $data = array_merge($additionalData, ['status' => $status]);
        return $this->makeRequest('PUT', "/orchestrator/tasks/{$taskId}/status", $data);
    }

    /**
     * Create a new task in the Task Orchestrator
     *
     * @param array $taskData Task data (title, description, priority, complexity, etc.)
     * @return array Created task data
     * @throws Exception
     */
    public function createTask(array $taskData): array
    {
        return $this->makeRequest('POST', '/orchestrator/tasks', $taskData);
    }

    /**
     * Update an existing task
     *
     * @param string $taskId Task identifier
     * @param array $taskData Updated task data
     * @return array Updated task data
     * @throws Exception
     */
    public function updateTask(string $taskId, array $taskData): array
    {
        return $this->makeRequest('PUT', "/orchestrator/tasks/{$taskId}", $taskData);
    }

    /**
     * Get recent activity summary
     *
     * @param int $hoursAgo Hours to look back
     * @return array Activity summary
     * @throws Exception
     */
    public function getRecentActivity(int $hoursAgo = 24): array
    {
        return $this->makeRequest('GET', "/kg/recent?hours_ago={$hoursAgo}");
    }

    /**
     * Search decisions in ConPort
     *
     * @param string $query Search query
     * @param int $limit Maximum results
     * @return array Search results
     * @throws Exception
     */
    public function searchDecisions(string $query, int $limit = 10): array
    {
        return $this->makeRequest('GET', "/kg/decisions/search?query_term=" . urlencode($query) . "&limit={$limit}");
    }

    /**
     * Get custom data from ConPort
     *
     * @param string $category Data category
     * @param string|null $key Specific key (optional)
     * @return array Custom data
     * @throws Exception
     */
    public function getCustomData(string $category, ?string $key = null): array
    {
        $url = "/kg/custom_data?category=" . urlencode($category);
        if ($key) {
            $url .= "&key=" . urlencode($key);
        }
        return $this->makeRequest('GET', $url);
    }

    /**
     * Log a decision to ConPort
     *
     * @param array $decisionData Decision data (summary, rationale, etc.)
     * @return array Created decision
     * @throws Exception
     */
    public function logDecision(array $decisionData): array
    {
        return $this->makeRequest('POST', '/ddg/decisions/recent', $decisionData);
    }

    /**
     * Get project dashboard data
     *
     * @param string $projectId Project identifier
     * @return array Dashboard data
     * @throws Exception
     */
    public function getProjectDashboard(string $projectId): array
    {
        return $this->makeRequest('GET', "/api/projects/{$projectId}/dashboard");
    }

    /**
     * Get next recommended tasks
     *
     * @param string $projectId Project identifier
     * @return array Recommended tasks
     * @throws Exception
     */
    public function getNextTasks(string $projectId): array
    {
        return $this->makeRequest('GET', "/api/projects/{$projectId}/next-tasks");
    }

    /**
     * Parse PRD and create tasks
     *
     * @param array $prdData PRD data
     * @return array Parsing results
     * @throws Exception
     */
    public function parsePrd(array $prdData): array
    {
        return $this->makeRequest('POST', '/api/parse-prd', $prdData);
    }

    /**
     * Make HTTP request to MCP Integration Bridge
     *
     * @param string $method HTTP method
     * @param string $endpoint API endpoint
     * @param array|null $data Request data for POST/PUT
     * @return array Response data
     * @throws Exception
     */
    private function makeRequest(string $method, string $endpoint, ?array $data = null): array
    {
        $url = $this->baseUrl . $endpoint;

        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, $this->timeout);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false); // For development

        // Set headers
        $headers = [
            'Content-Type: application/json',
            'Accept: application/json',
            'X-Workspace-ID: ' . $this->workspaceId
        ];
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

        // Add data for POST/PUT requests
        if ($data && in_array($method, ['POST', 'PUT'])) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);

        if ($error) {
            throw new Exception("MCP Integration Bridge request failed: {$error}");
        }

        if ($httpCode < 200 || $httpCode >= 300) {
            throw new Exception("MCP Integration Bridge returned HTTP {$httpCode}: {$response}");
        }

        $result = json_decode($response, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            throw new Exception("Invalid JSON response from MCP Integration Bridge: {$response}");
        }

        return $result;
    }

    /**
     * Set request timeout
     *
     * @param int $timeout Timeout in seconds
     */
    public function setTimeout(int $timeout): void
    {
        $this->timeout = $timeout;
    }

    /**
     * Set workspace ID
     *
     * @param string $workspaceId New workspace ID
     */
    public function setWorkspaceId(string $workspaceId): void
    {
        $this->workspaceId = $workspaceId;
    }

    /**
     * Set base URL
     *
     * @param string $baseUrl New base URL
     */
    public function setBaseUrl(string $baseUrl): void
    {
        $this->baseUrl = $baseUrl;
    }
}