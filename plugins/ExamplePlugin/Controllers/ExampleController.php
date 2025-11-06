<?php

namespace Leantime\Plugins\ExamplePlugin\Controllers;

use Leantime\Core\Controller;

/**
 * Example Controller for the Example Plugin
 */
class ExampleController extends Controller
{
    /**
     * Index action - main plugin page
     */
    public function init()
    {
        // Set template and data
        $this->tpl->assign('pluginName', 'Example Plugin');
        $this->tpl->assign('currentUser', $_SESSION['userdata']['name'] ?? 'Guest');
        $this->tpl->display('exampleplugin.index');
    }

    /**
     * Example API endpoint
     */
    public function api()
    {
        // Return JSON response
        header('Content-Type: application/json');
        echo json_encode([
            'status' => 'success',
            'plugin' => 'ExamplePlugin',
            'timestamp' => date('Y-m-d H:i:s'),
            'data' => [
                'user_count' => 1,
                'version' => '1.0.0'
            ]
        ]);
        exit;
    }
}