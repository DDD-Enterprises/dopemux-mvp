{extends file="html5.tpl"}

{block name="content"}
<div class="pageheader">
    <div class="pageicon"><span class="fa fa-save"></span></div>
    <div class="pagetitle">
        <h1>{$__("dopemux.context.title")}</h1>
        <h4>{$__("dopemux.context.preserve_work")}</h4>
    </div>
</div>

<div class="maincontentinner">
    <div class="row">
        <div class="col-md-8">
            <!-- Current Context -->
            <div class="card">
                <div class="card-header">
                    <h3>{$__("dopemux.context.current_context")}</h3>
                </div>
                <div class="card-body">
                    <div class="context-display">
                        <h4>{$currentContext.active_project}</h4>
                        <p class="text-muted">{$__("dopemux.context.active_tickets")}: {count($currentContext.active_tickets)}</p>
                        <div class="context-details">
                            <strong>{$__("dopemux.context.open_files")}:</strong>
                            <ul>
                                {foreach $currentContext.open_files as $file}
                                <li><code>{$file}</code></li>
                                {/foreach}
                            </ul>
                            <strong>{$__("dopemux.context.notes")}:</strong>
                            <p>{$currentContext.notes}</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Saved Contexts -->
            <div class="card mt-3">
                <div class="card-header">
                    <h3>{$__("dopemux.context.saved_contexts")}</h3>
                </div>
                <div class="card-body">
                    {if $savedContexts}
                        <div class="context-list">
                            {foreach $savedContexts as $context}
                            <div class="context-item">
                                <div class="context-header">
                                    <strong>{$context.name}</strong>
                                    <small class="text-muted">{$context.saved_at}</small>
                                </div>
                                <div class="context-actions">
                                    <button class="btn btn-sm btn-outline-primary restore-btn"
                                            data-context-id="{$context.id}">
                                        {$__("dopemux.button.restore_context")}
                                    </button>
                                </div>
                            </div>
                            {/foreach}
                        </div>
                    {else}
                        <p class="text-muted">{$__("dopemux.context.no_saved_contexts")}</p>
                    {/if}
                </div>
            </div>
        </div>

        <div class="col-md-4">
            <!-- Auto-Save Settings -->
            <div class="card">
                <div class="card-header">
                    <h3>{$__("dopemux.context.auto_save")}</h3>
                </div>
                <div class="card-body">
                    <div class="auto-save-status">
                        {if $contextStatus.auto_save_enabled}
                            <div class="alert alert-success">
                                <i class="fa fa-check-circle"></i>
                                {$__("dopemux.context.auto_save_enabled")}
                            </div>
                            <p class="text-muted">
                                {$__("dopemux.context.last_save")}: {$contextStatus.last_save}
                            </p>
                        {else}
                            <div class="alert alert-warning">
                                <i class="fa fa-exclamation-triangle"></i>
                                {$__("dopemux.context.auto_save_disabled")}
                            </div>
                        {/if}
                    </div>
                </div>
            </div>

            <!-- Manual Save -->
            <div class="card mt-3">
                <div class="card-header">
                    <h3>{$__("dopemux.context.manual_save")}</h3>
                </div>
                <div class="card-body">
                    <form method="post" action="{url action='saveContext'}" id="saveContextForm">
                        <div class="form-group">
                            <label for="context_name">{$__("dopemux.form.context_name")}</label>
                            <input type="text" class="form-control" id="context_name"
                                   name="context_name" placeholder="My Current Work" required>
                        </div>
                        <div class="form-group">
                            <label for="context_data">{$__("dopemux.form.context_notes")}</label>
                            <textarea class="form-control" id="context_data"
                                      name="context_data" rows="3"
                                      placeholder="Optional notes about this context..."></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary btn-block">
                            <i class="fa fa-save"></i> {$__("dopemux.button.save_context")}
                        </button>
                    </form>
                </div>
            </div>

            <!-- Quick Actions -->
            <div class="card mt-3">
                <div class="card-header">
                    <h3>{$__("dopemux.context.quick_actions")}</h3>
                </div>
                <div class="card-body">
                    <div class="btn-group-vertical btn-block">
                        <button class="btn btn-outline-secondary btn-sm quick-save"
                                data-name="Quick Checkpoint">
                            <i class="fa fa-clock"></i> {$__("dopemux.context.quick_checkpoint")}
                        </button>
                        <button class="btn btn-outline-info btn-sm quick-save"
                                data-name="Before Meeting">
                            <i class="fa fa-users"></i> {$__("dopemux.context.before_meeting")}
                        </button>
                        <button class="btn btn-outline-warning btn-sm quick-save"
                                data-name="End of Day">
                            <i class="fa fa-sun"></i> {$__("dopemux.context.end_of_day")}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Context History -->
    <div class="row mt-4">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <h3>{$__("dopemux.context.history")}</h3>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>{$__("dopemux.context.name")}</th>
                                    <th>{$__("dopemux.context.saved_at")}</th>
                                    <th>{$__("dopemux.context.actions")}</th>
                                </tr>
                            </thead>
                            <tbody id="contextHistoryTable">
                                {foreach $savedContexts as $context}
                                <tr>
                                    <td>{$context.name}</td>
                                    <td>{$context.saved_at}</td>
                                    <td>
                                        <button class="btn btn-sm btn-outline-primary restore-btn"
                                                data-context-id="{$context.id}">
                                            {$__("dopemux.button.restore_context")}
                                        </button>
                                    </td>
                                </tr>
                                {/foreach}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
.context-display {
    padding: 1.5rem;
    background-color: #f8f9fa;
    border-radius: 8px;
    border-left: 4px solid #007bff;
}

.context-details {
    margin-top: 1rem;
}

.context-details ul {
    margin-bottom: 1rem;
}

.context-details code {
    background-color: #e9ecef;
    padding: 0.2rem 0.4rem;
    border-radius: 3px;
    font-size: 0.9em;
}

.context-list {
    max-height: 400px;
    overflow-y: auto;
}

.context-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    margin-bottom: 0.5rem;
    background-color: #fff;
}

.context-item:hover {
    background-color: #f8f9fa;
}

.context-header {
    flex-grow: 1;
}

.context-header strong {
    display: block;
    font-size: 1.1em;
}

.context-header small {
    color: #6c757d;
}

.quick-save {
    margin-bottom: 0.5rem;
}

.quick-save i {
    margin-right: 0.5rem;
}
</style>

<script>
document.querySelectorAll('.quick-save').forEach(button => {
    button.addEventListener('click', function() {
        const name = this.getAttribute('data-name');
        document.getElementById('context_name').value = name;
        // Could auto-submit or show confirmation
    });
});

document.querySelectorAll('.restore-btn').forEach(button => {
    button.addEventListener('click', function() {
        const contextId = this.getAttribute('data-context-id');
        if (confirm('{$__("dopemux.context.confirm_restore")}')) {
            // Submit restore form
            const form = document.createElement('form');
            form.method = 'GET';
            form.action = '{url action="restoreContext"}';
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'context_id';
            input.value = contextId;
            form.appendChild(input);
            document.body.appendChild(form);
            form.submit();
        }
    });
});
</script>
{/block}