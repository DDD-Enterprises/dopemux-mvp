{extends file="html5.tpl"}

{block name="content"}
<div class="pageheader">
    <div class="pageicon"><span class="fa fa-brain"></span></div>
    <div class="pagetitle">
        <h1>{$__("dopemux.dashboard.title")}</h1>
        <h4>{$__("dopemux.dashboard.welcome")}</h4>
    </div>
</div>

<div class="maincontentinner">
    <div class="row">
        <div class="col-md-8">
            <!-- Current ADHD State Card -->
            <div class="card">
                <div class="card-header">
                    <h3>{$__("dopemux.dashboard.current_attention")}</h3>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="metric">
                                <h2 class="metric-value attention-{$adhdState.attention_state|lower}">
                                    {$__("dopemux.attention.{$adhdState.attention_state|lower}")}
                                </h2>
                                <p class="metric-label">{$__("dopemux.attention.state")}</p>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="metric">
                                <h2 class="metric-value load-{$adhdState.cognitive_load|round}">
                                    {$adhdState.cognitive_load*100}%
                                </h2>
                                <p class="metric-label">{$__("dopemux.cognitive.current_load")}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Recommended Tasks -->
            <div class="card mt-3">
                <div class="card-header">
                    <h3>{$__("dopemux.dashboard.recommended_tasks")}</h3>
                </div>
                <div class="card-body">
                    {if $recommendedTasks}
                        {foreach $recommendedTasks as $task}
                        <div class="task-item">
                            <div class="task-header">
                                <strong>{$task.title}</strong>
                                <span class="badge badge-secondary">{$task.complexity}</span>
                            </div>
                            <div class="task-meta">
                                <small class="text-muted">
                                    {$__("dopemux.task.cognitive_load")}: {$task.cognitive_load} |
                                    {$__("dopemux.task.estimated_focus_time")}: {$task.estimated_time}
                                </small>
                            </div>
                        </div>
                        {/foreach}
                    {else}
                        <p class="text-muted">{$__("dopemux.dashboard.no_recommended_tasks")}</p>
                    {/if}
                </div>
            </div>
        </div>

        <div class="col-md-4">
            <!-- Break Reminder -->
            <div class="card">
                <div class="card-header">
                    <h3>{$__("dopemux.dashboard.break_reminder")}</h3>
                </div>
                <div class="card-body">
                    {if $upcomingBreaks.next_break}
                        <div class="break-info">
                            <h4>{$upcomingBreaks.next_break}</h4>
                            <p>{$__("dopemux.break.type_short")}</p>
                            <button class="btn btn-primary btn-sm">
                                {$__("dopemux.button.take_break")}
                            </button>
                        </div>
                    {else}
                        <p class="text-success">{$__("dopemux.break.no_breaks_needed")}</p>
                    {/if}
                </div>
            </div>

            <!-- Context Status -->
            <div class="card mt-3">
                <div class="card-header">
                    <h3>{$__("dopemux.dashboard.context_status")}</h3>
                </div>
                <div class="card-body">
                    <div class="context-metrics">
                        <div class="metric">
                            <span class="metric-value">{$contextStatus.saved_contexts}</span>
                            <span class="metric-label">{$__("dopemux.context.saved")}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-value">{$contextStatus.last_save}</span>
                            <span class="metric-label">{$__("dopemux.context.last_save")}</span>
                        </div>
                    </div>
                    <button class="btn btn-outline-primary btn-sm mt-2">
                        {$__("dopemux.button.save_context")}
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>
{/block}