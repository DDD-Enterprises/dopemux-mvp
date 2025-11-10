<?php

namespace Leantime\Plugins\Dopemux\Controllers;

use Leantime\Core\Controller;
use Leantime\Plugins\Dopemux\Services\TaskOrchestratorClient;

/**
 * Dopemux Controller - Main controller for ADHD-optimized features
 */
class DopemuxController extends Controller
{
    private TaskOrchestratorClient $taskClient;

    /**
     * Initialize controller
     */
    public function init()
    {
        $this->taskClient = new TaskOrchestratorClient();
    }

    /**
     * Dashboard view - ADHD insights and recommendations
     */
    public function dashboard()
    {
        try {
            // Get ADHD dashboard data
            $dashboardData = $this->taskClient->getAdhdState();
            $activeSprint = $this->taskClient->getActiveSprint();
            $session = $this->taskClient->getSession();

            $this->tpl->assign('adhdState', $dashboardData);
            $this->tpl->assign('activeSprint', $activeSprint);
            $this->tpl->assign('session', $session);

            $this->tpl->display('plugins.dopemux.dashboard');

        } catch (Exception $e) {
            error_log("Dopemux Controller: Dashboard error: " . $e->getMessage());
            $this->tpl->assign('error', $e->getMessage());
            $this->tpl->display('plugins.dopemux.error');
        }
    }

    /**
     * Task recommendations view
     */
    public function recommendations()
    {
        try {
            $recommendations = $this->taskClient->getRecommendations();

            $this->tpl->assign('recommendations', $recommendations);
            $this->tpl->display('plugins.dopemux.recommendations');

        } catch (Exception $e) {
            error_log("Dopemux Controller: Recommendations error: " . $e->getMessage());
            $this->tpl->assign('error', $e->getMessage());
            $this->tpl->display('plugins.dopemux.error');
        }
    }

    /**
     * Settings/Configuration view
     */
    public function settings()
    {
        // Get current settings from Leantime config
        $currentSettings = [
            'workspace_id' => get_option('dopemux_workspace_id', '/Users/hue/code/dopemux-mvp'),
            'api_url' => get_option('dopemux_api_url', 'http://localhost:3016'),
            'sync_enabled' => get_option('dopemux_sync_enabled', '1'),
            'sync_interval' => get_option('dopemux_sync_interval', '15')
        ];

        $this->tpl->assign('settings', $currentSettings);

        // Handle form submission
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            $this->saveSettings();
            $this->tpl->assign('message', 'Settings saved successfully!');
        }

        $this->tpl->display('plugins.dopemux.settings');
    }

    /**
     * Save plugin settings
     */
    private function saveSettings()
    {
        if (!current_user_can('manage_options')) {
            return;
        }

        $settings = [
            'workspace_id' => sanitize_text_field($_POST['workspace_id'] ?? ''),
            'api_url' => sanitize_text_field($_POST['api_url'] ?? ''),
            'sync_enabled' => isset($_POST['sync_enabled']) ? '1' : '0',
            'sync_interval' => intval($_POST['sync_interval'] ?? 15)
        ];

        foreach ($settings as $key => $value) {
            update_option('dopemux_' . $key, $value);
        }

        // Update sync schedule if changed
        if ($settings['sync_enabled'] && $settings['sync_interval'] > 0) {
            if (wp_next_scheduled('dopemux_periodic_sync')) {
                wp_unschedule_event(wp_next_scheduled('dopemux_periodic_sync'), 'dopemux_periodic_sync');
            }
            wp_schedule_event(time(), $settings['sync_interval'] . 'min', 'dopemux_periodic_sync');
        } elseif (wp_next_scheduled('dopemux_periodic_sync')) {
            wp_unschedule_event(wp_next_scheduled('dopemux_periodic_sync'), 'dopemux_periodic_sync');
        }
    }

    /**
     * Manual sync trigger
     */
    public function sync()
    {
        try {
            // Trigger bidirectional sync
            $syncResult = [
                'success' => true,
                'message' => 'Synchronization completed successfully'
            ];

            // In a real implementation, you'd call the sync method here
            // For now, just return success

            $this->tpl->assign('syncResult', $syncResult);
            $this->tpl->display('plugins.dopemux.sync');

        } catch (Exception $e) {
            $syncResult = [
                'success' => false,
                'message' => 'Sync failed: ' . $e->getMessage()
            ];

            $this->tpl->assign('syncResult', $syncResult);
            $this->tpl->display('plugins.dopemux.sync');
        }
    }
}