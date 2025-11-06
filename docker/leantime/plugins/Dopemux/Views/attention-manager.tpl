{extends file="html5.tpl"}

{block name="content"}
<div class="pageheader">
    <div class="pageicon"><span class="fa fa-focus"></span></div>
    <div class="pagetitle">
        <h1>{$__("dopemux.attention.title")}</h1>
        <h4>{$__("dopemux.attention.monitor_state")}</h4>
    </div>
</div>

<div class="maincontentinner">
    <div class="row">
        <div class="col-md-6">
            <!-- Current Attention State -->
            <div class="card">
                <div class="card-header">
                    <h3>{$__("dopemux.attention.current_state")}</h3>
                </div>
                <div class="card-body">
                    <div class="text-center">
                        <div class="attention-display attention-{$currentState|lower}">
                            <h1 class="attention-icon">
                                {if $currentState == 'hyperfocus'}
                                    <i class="fa fa-bolt"></i>
                                {elseif $currentState == 'focused'}
                                    <i class="fa fa-crosshairs"></i>
                                {elseif $currentState == 'scattered'}
                                    <i class="fa fa-scatter-plot"></i>
                                {elseif $currentState == 'background'}
                                    <i class="fa fa-clock"></i>
                                {else}
                                    <i class="fa fa-question"></i>
                                {/if}
                            </h1>
                            <h2 class="attention-label">
                                {$__("dopemux.attention.{$currentState|lower}")}
                            </h2>
                        </div>
                    </div>
                </div>
            </div>

            <!-- State Suggestions -->
            <div class="card mt-3">
                <div class="card-header">
                    <h3>{$__("dopemux.attention.suggestions")}</h3>
                </div>
                <div class="card-body">
                    <h4>{$suggestions.message}</h4>
                    <ul class="suggestion-list">
                        {foreach $suggestions.suggestions as $suggestion}
                        <li>{$suggestion}</li>
                        {/foreach}
                    </ul>
                </div>
            </div>
        </div>

        <div class="col-md-6">
            <!-- Attention History Chart -->
            <div class="card">
                <div class="card-header">
                    <h3>{$__("dopemux.attention.state_history")}</h3>
                </div>
                <div class="card-body">
                    <canvas id="attentionHistoryChart" width="400" height="200"></canvas>
                    <script>
                    const ctx = document.getElementById('attentionHistoryChart').getContext('2d');
                    const historyData = {json_encode($stateHistory)};

                    // Map states to numeric values for charting
                    const stateMap = {
                        'hyperfocus': 5,
                        'focused': 4,
                        'scattered': 2,
                        'background': 1,
                        'transition': 3
                    };

                    new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: historyData.map(item => item.timestamp),
                            datasets: [{
                                label: '{$__("dopemux.attention.state_history")}',
                                data: historyData.map(item => stateMap[item.state] || 3),
                                borderColor: 'rgb(54, 162, 235)',
                                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                                tension: 0.1
                            }]
                        },
                        options: {
                            responsive: true,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    max: 5,
                                    ticks: {
                                        callback: function(value) {
                                            const reverseMap = {
                                                1: 'background',
                                                2: 'scattered',
                                                3: 'transition',
                                                4: 'focused',
                                                5: 'hyperfocus'
                                            };
                                            return reverseMap[value] || value;
                                        }
                                    }
                                }
                            }
                        }
                    });
                    </script>
                </div>
            </div>
        </div>
    </div>

    <!-- State Adjustment Controls -->
    <div class="row mt-4">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <h3>{$__("dopemux.attention.update_state")}</h3>
                </div>
                <div class="card-body">
                    <form method="post" action="{url action='updateAttentionState'}">
                        <div class="form-group">
                            <label for="attention_state">{$__("dopemux.attention.select_state")}</label>
                            <select class="form-control" id="attention_state" name="attention_state">
                                <option value="hyperfocus" {if $currentState == 'hyperfocus'}selected{/if}>
                                    {$__("dopemux.attention.hyperfocus")}
                                </option>
                                <option value="focused" {if $currentState == 'focused'}selected{/if}>
                                    {$__("dopemux.attention.focused")}
                                </option>
                                <option value="scattered" {if $currentState == 'scattered'}selected{/if}>
                                    {$__("dopemux.attention.scattered")}
                                </option>
                                <option value="background" {if $currentState == 'background'}selected{/if}>
                                    {$__("dopemux.attention.background")}
                                </option>
                                <option value="transition" {if $currentState == 'transition'}selected{/if}>
                                    {$__("dopemux.attention.transition")}
                                </option>
                            </select>
                        </div>
                        <button type="submit" class="btn btn-primary">
                            {$__("dopemux.button.save")}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- Quick Actions -->
    <div class="row mt-4">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <h3>{$__("dopemux.attention.quick_actions")}</h3>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-3">
                            <button class="btn btn-outline-success btn-block quick-action"
                                    data-state="focused">
                                <i class="fa fa-crosshairs"></i><br>
                                {$__("dopemux.attention.focused")}
                            </button>
                        </div>
                        <div class="col-md-3">
                            <button class="btn btn-outline-warning btn-block quick-action"
                                    data-state="scattered">
                                <i class="fa fa-scatter-plot"></i><br>
                                {$__("dopemux.attention.scattered")}
                            </button>
                        </div>
                        <div class="col-md-3">
                            <button class="btn btn-outline-info btn-block quick-action"
                                    data-state="hyperfocus">
                                <i class="fa fa-bolt"></i><br>
                                {$__("dopemux.attention.hyperfocus")}
                            </button>
                        </div>
                        <div class="col-md-3">
                            <button class="btn btn-outline-secondary btn-block quick-action"
                                    data-state="background">
                                <i class="fa fa-clock"></i><br>
                                {$__("dopemux.attention.background")}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
.attention-display {
    padding: 2rem;
    border-radius: 10px;
    margin-bottom: 1rem;
    text-align: center;
}

.attention-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
}

.attention-label {
    font-size: 1.5rem;
    font-weight: bold;
}

.attention-hyperfocus { background-color: #e8f5e8; color: #2e7d32; }
.attention-focused { background-color: #e3f2fd; color: #1976d2; }
.attention-scattered { background-color: #fff3e0; color: #f57c00; }
.attention-background { background-color: #f5f5f5; color: #616161; }
.attention-transition { background-color: #f3e5f5; color: #7b1fa2; }

.suggestion-list {
    padding-left: 1rem;
    margin-top: 1rem;
}

.quick-action {
    height: 80px;
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.quick-action i {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}
</style>

<script>
document.querySelectorAll('.quick-action').forEach(button => {
    button.addEventListener('click', function() {
        const state = this.getAttribute('data-state');
        document.getElementById('attention_state').value = state;
        // Could auto-submit or show confirmation
    });
});
</script>
{/block}