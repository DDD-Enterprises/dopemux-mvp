{extends file="html5.tpl"}

{block name="content"}
<div class="pageheader">
    <div class="pageicon"><span class="fa fa-chart-line"></span></div>
    <div class="pagetitle">
        <h1>{$__("dopemux.cognitive.title")}</h1>
        <h4>{$__("dopemux.cognitive.monitor_load")}</h4>
    </div>
</div>

<div class="maincontentinner">
    <div class="row">
        <div class="col-md-6">
            <!-- Current Load Display -->
            <div class="card">
                <div class="card-header">
                    <h3>{$__("dopemux.cognitive.current_load")}</h3>
                </div>
                <div class="card-body">
                    <div class="text-center">
                        <div class="load-display load-{$currentLoad|round}">
                            <h1 class="load-value">{$currentLoad}/10</h1>
                            <p class="load-label">
                                {if $currentLoad >= 8}
                                    {$__("dopemux.cognitive.load_extreme")}
                                {elseif $currentLoad >= 6}
                                    {$__("dopemux.cognitive.load_high")}
                                {elseif $currentLoad >= 4}
                                    {$__("dopemux.cognitive.load_medium")}
                                {else}
                                    {$__("dopemux.cognitive.load_low")}
                                {/if}
                            </p>
                        </div>
                        <div class="load-bar">
                            <div class="progress">
                                <div class="progress-bar load-{$currentLoad|round}"
                                     style="width: {$currentLoad * 10}%"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Load Recommendations -->
            <div class="card mt-3">
                <div class="card-header">
                    <h3>{$__("dopemux.cognitive.recommendations")}</h3>
                </div>
                <div class="card-body">
                    <div class="recommendation {$recommendations.status}">
                        <h4>{$recommendations.recommendation}</h4>
                        <ul class="recommendation-list">
                            {foreach $recommendations.suggested_actions as $action}
                            <li>{$action}</li>
                            {/foreach}
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <div class="col-md-6">
            <!-- Load History Chart -->
            <div class="card">
                <div class="card-header">
                    <h3>{$__("dopemux.cognitive.load_history")}</h3>
                </div>
                <div class="card-body">
                    <canvas id="cognitiveLoadChart" width="400" height="200"></canvas>
                    <script>
                    // Simple chart using Chart.js (assuming it's available)
                    const ctx = document.getElementById('cognitiveLoadChart').getContext('2d');
                    const loadData = {json_encode($loadHistory)};

                    new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: loadData.map(item => item.timestamp),
                            datasets: [{
                                label: '{$__("dopemux.cognitive.load_history")}',
                                data: loadData.map(item => item.load),
                                borderColor: 'rgb(75, 192, 192)',
                                tension: 0.1
                            }]
                        },
                        options: {
                            responsive: true,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    max: 10
                                }
                            }
                        }
                    });
                    </script>
                </div>
            </div>
        </div>
    </div>

    <!-- Load Adjustment Controls -->
    <div class="row mt-4">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <h3>{$__("dopemux.cognitive.adjust_load")}</h3>
                </div>
                <div class="card-body">
                    <form method="post" action="{url action='updateCognitiveLoad'}">
                        <div class="form-group">
                            <label for="cognitive_load">{$__("dopemux.cognitive.set_load")}</label>
                            <input type="range" class="form-control-range" id="cognitive_load"
                                   name="cognitive_load" min="1" max="10" value="{$currentLoad}">
                            <div class="range-labels">
                                <span>1</span>
                                <span>5</span>
                                <span>10</span>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary">
                            {$__("dopemux.button.save")}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
.load-display {
    padding: 2rem;
    border-radius: 10px;
    margin-bottom: 1rem;
}

.load-value {
    font-size: 3rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}

.load-1, .load-2, .load-3 { background-color: #d4edda; color: #155724; }
.load-4, .load-5, .load-6 { background-color: #fff3cd; color: #856404; }
.load-7, .load-8, .load-9, .load-10 { background-color: #f8d7da; color: #721c24; }

.recommendation.high { border-left: 4px solid #dc3545; }
.recommendation.medium { border-left: 4px solid #ffc107; }
.recommendation.low { border-left: 4px solid #28a745; }

.recommendation-list {
    padding-left: 1rem;
}
</style>
{/block}