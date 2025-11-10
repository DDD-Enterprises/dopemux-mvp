<?php
/**
 * Dopemux Plugin Settings View
 *
 * Configuration interface for Dopemux ADHD features
 */

$settings = $tpl->get('settings');
$message = $tpl->get('message');
?>

@extends($layout)

@section('content')
<div class="pageheader">
    <div class="pageicon"><i class="fa-solid fa-cogs"></i></div>
    <div class="pagetitle">
        <h1>Dopemux ADHD Plugin Settings</h1>
        <h4>Configure ADHD-optimized project management features</h4>
    </div>
</div>

<div class="maincontent">
    <div class="maincontentinner">
        @if($message)
        <div class="alert alert-success">
            <strong>Success!</strong> {{ $message }}
        </div>
        @endif

        <form method="post" action="{{ url('/plugins/dopemux/settings') }}" class="settings-form">
            @csrf

            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h4><i class="fa-solid fa-server"></i> Task Orchestrator Connection</h4>
                        </div>
                        <div class="card-body">
                            <div class="form-group">
                                <label for="workspace_id">Workspace ID</label>
                                <input type="text"
                                       id="workspace_id"
                                       name="workspace_id"
                                       class="form-control"
                                       value="{{ $settings['workspace_id'] ?? '' }}"
                                       placeholder="/path/to/workspace">
                                <small class="form-text text-muted">
                                    Absolute path to your Dopemux workspace (e.g., /Users/username/code/project)
                                </small>
                            </div>

                            <div class="form-group">
                                <label for="api_url">API URL</label>
                                <input type="url"
                                       id="api_url"
                                       name="api_url"
                                       class="form-control"
                                       value="{{ $settings['api_url'] ?? '' }}"
                                       placeholder="http://localhost:3016">
                                <small class="form-text text-muted">
                                    URL of the MCP Integration Bridge service
                                </small>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h4><i class="fa-solid fa-sync"></i> Synchronization Settings</h4>
                        </div>
                        <div class="card-body">
                            <div class="form-group">
                                <div class="form-check">
                                    <input type="checkbox"
                                           id="sync_enabled"
                                           name="sync_enabled"
                                           class="form-check-input"
                                           value="1"
                                           {{ $settings['sync_enabled'] ? 'checked' : '' }}>
                                    <label for="sync_enabled" class="form-check-label">
                                        Enable bidirectional task synchronization
                                    </label>
                                </div>
                                <small class="form-text text-muted">
                                    Automatically sync tasks between Leantime and Task Orchestrator
                                </small>
                            </div>

                            <div class="form-group">
                                <label for="sync_interval">Sync Interval (minutes)</label>
                                <select id="sync_interval" name="sync_interval" class="form-control">
                                    <option value="5" {{ $settings['sync_interval'] == 5 ? 'selected' : '' }}>5 minutes</option>
                                    <option value="15" {{ $settings['sync_interval'] == 15 ? 'selected' : '' }}>15 minutes</option>
                                    <option value="30" {{ $settings['sync_interval'] == 30 ? 'selected' : '' }}>30 minutes</option>
                                    <option value="60" {{ $settings['sync_interval'] == 60 ? 'selected' : '' }}>1 hour</option>
                                </select>
                                <small class="form-text text-muted">
                                    How often to check for task updates
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h4><i class="fa-solid fa-brain"></i> ADHD Features</h4>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h5>Task Analysis</h5>
                                    <ul class="list-unstyled">
                                        <li><i class="fa-solid fa-check text-success"></i> Complexity scoring (0.0-1.0)</li>
                                        <li><i class="fa-solid fa-check text-success"></i> Energy requirement assessment</li>
                                        <li><i class="fa-solid fa-check text-success"></i> Focus time recommendations</li>
                                        <li><i class="fa-solid fa-check text-success"></i> Cognitive load warnings</li>
                                    </ul>
                                </div>
                                <div class="col-md-6">
                                    <h5>Session Management</h5>
                                    <ul class="list-unstyled">
                                        <li><i class="fa-solid fa-check text-success"></i> ADHD-optimized focus sessions</li>
                                        <li><i class="fa-solid fa-check text-success"></i> Break recommendations</li>
                                        <li><i class="fa-solid fa-check text-success"></i> Progress tracking</li>
                                        <li><i class="fa-solid fa-check text-success"></i> Task prioritization</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mt-4">
                <div class="col-12 text-center">
                    <button type="submit" class="btn btn-primary btn-lg">
                        <i class="fa-solid fa-save"></i> Save Settings
                    </button>
                    <a href="{{ url('/plugins/dopemux/sync') }}" class="btn btn-secondary btn-lg ml-2">
                        <i class="fa-solid fa-sync"></i> Manual Sync
                    </a>
                </div>
            </div>
        </form>

        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h4><i class="fa-solid fa-info-circle"></i> How It Works</h4>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4">
                                <h5><i class="fa-solid fa-exchange-alt text-primary"></i> Bidirectional Sync</h5>
                                <p>Tasks created in Leantime automatically appear in your Task Orchestrator, and vice versa. Changes in either system are synchronized.</p>
                            </div>
                            <div class="col-md-4">
                                <h5><i class="fa-solid fa-brain text-success"></i> ADHD Optimization</h5>
                                <p>Each task gets analyzed for complexity, energy requirements, and focus time needs. Visual indicators help you choose tasks that match your current mental state.</p>
                            </div>
                            <div class="col-md-4">
                                <h5><i class="fa-solid fa-chart-line text-info"></i> Progress Tracking</h5>
                                <p>Track your productivity patterns and get insights into your work rhythms. The system learns from your behavior to provide better recommendations.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
@endsection

<style>
.settings-form .card {
    margin-bottom: 1rem;
}

.settings-form .form-group {
    margin-bottom: 1.5rem;
}

.settings-form label {
    font-weight: 600;
    margin-bottom: 0.5rem;
    display: block;
}

.settings-form .form-control {
    border-radius: 0.375rem;
}

.settings-form .btn {
    border-radius: 0.375rem;
    font-weight: 500;
}

.alert {
    border-radius: 0.375rem;
    margin-bottom: 2rem;
}
</style>