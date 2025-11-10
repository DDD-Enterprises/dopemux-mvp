<?php
/**
 * ADHD-Optimized Task Card View
 *
 * Displays tasks with ADHD accommodations:
 * - Complexity scoring with color coding
 * - Energy requirements and focus time estimates
 * - Visual progress indicators
 * - Cognitive load warnings
 */

$task = $tpl->get('task');
$adhdMetadata = $tpl->get('adhdMetadata') ?? [];
$complexity = $adhdMetadata['complexity'] ?? 0.5;
$energyRequired = $adhdMetadata['energy_required'] ?? 'medium';
$estimatedFocusTime = $adhdMetadata['estimated_focus_time'] ?? 60;
$priority = $task['priority'] ?? 'medium';

// Determine complexity color and label
$complexityColor = 'green';
$complexityLabel = 'Low Complexity';
if ($complexity >= 0.8) {
    $complexityColor = 'red';
    $complexityLabel = 'High Complexity - Schedule Focus Time';
} elseif ($complexity >= 0.6) {
    $complexityColor = 'orange';
    $complexityLabel = 'Medium Complexity';
}

// Energy level indicator
$energyColor = 'blue';
$energyIcon = '⚡';
switch ($energyRequired) {
    case 'high':
        $energyColor = 'red';
        $energyIcon = '🔴';
        break;
    case 'medium':
        $energyColor = 'yellow';
        $energyIcon = '🟡';
        break;
    case 'low':
        $energyColor = 'green';
        $energyIcon = '🟢';
        break;
}

// Priority styling
$priorityClasses = '';
switch ($priority) {
    case 'urgent':
        $priorityClasses = 'border-red-500 bg-red-50';
        break;
    case 'high':
        $priorityClasses = 'border-orange-500 bg-orange-50';
        break;
    case 'medium':
        $priorityClasses = 'border-blue-500 bg-blue-50';
        break;
    case 'low':
        $priorityClasses = 'border-gray-300 bg-gray-50';
        break;
}
?>

<div class="task-card adhd-task-card <?php echo $priorityClasses; ?> border-2 rounded-lg p-4 mb-4 shadow-sm hover:shadow-md transition-shadow">
    <!-- Header with title and status -->
    <div class="flex justify-between items-start mb-3">
        <h3 class="text-lg font-semibold text-gray-800 flex-1 pr-2">
            <?php echo htmlspecialchars($task['title']); ?>
        </h3>
        <div class="flex items-center space-x-2">
            <span class="px-2 py-1 text-xs font-medium rounded-full
                <?php echo $task['status'] === 'done' ? 'bg-green-100 text-green-800' : ($task['status'] === 'in_progress' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'); ?>">
                <?php echo ucfirst(str_replace('_', ' ', $task['status'] ?? 'new')); ?>
            </span>
            <span class="text-lg"><?php echo $energyIcon; ?></span>
        </div>
    </div>

    <!-- Description -->
    <?php if (!empty($task['description'])): ?>
    <div class="text-gray-600 text-sm mb-3 line-clamp-3">
        <?php echo nl2br(htmlspecialchars(substr($task['description'], 0, 200))); ?>
        <?php if (strlen($task['description']) > 200): ?>
            <span class="text-blue-500 cursor-pointer" onclick="toggleDescription(this)">... show more</span>
        <?php endif; ?>
    </div>
    <?php endif; ?>

    <!-- ADHD Metadata Section -->
    <div class="adhd-metadata bg-gray-50 rounded p-3 mb-3">
        <div class="grid grid-cols-2 gap-3 text-sm">

            <!-- Complexity Score -->
            <div class="flex items-center space-x-2">
                <div class="w-3 h-3 rounded-full bg-<?php echo $complexityColor; ?>-500"></div>
                <span class="text-gray-700">
                    <strong><?php echo $complexityLabel; ?></strong><br>
                    <span class="text-xs text-gray-500">
                        Cognitive Load: <?php echo round($complexity * 100); ?>%
                    </span>
                </span>
            </div>

            <!-- Focus Time Estimate -->
            <div class="flex items-center space-x-2">
                <span class="text-2xl">⏱️</span>
                <span class="text-gray-700">
                    <strong>Estimated Focus Time</strong><br>
                    <span class="text-xs text-gray-500">
                        <?php echo $estimatedFocusTime; ?> minutes
                    </span>
                </span>
            </div>

        </div>

        <!-- Energy Requirements Warning -->
        <?php if ($energyRequired === 'high' && $complexity >= 0.7): ?>
        <div class="mt-2 p-2 bg-yellow-100 border border-yellow-300 rounded text-yellow-800 text-xs">
            ⚠️ <strong>High Energy Task:</strong> Consider scheduling during peak energy hours for optimal performance.
        </div>
        <?php endif; ?>
    </div>

    <!-- Progress Bar (if task has progress tracking) -->
    <?php if (isset($task['progress']) && $task['progress'] > 0): ?>
    <div class="mb-3">
        <div class="flex justify-between text-sm text-gray-600 mb-1">
            <span>Progress</span>
            <span><?php echo $task['progress']; ?>%</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-2">
            <div class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                 style="width: <?php echo $task['progress']; ?>%"></div>
        </div>
    </div>
    <?php endif; ?>

    <!-- Action Buttons -->
    <div class="flex space-x-2 pt-2 border-t border-gray-200">
        <button class="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                onclick="startTask(<?php echo $task['id']; ?>)">
            Start Task
        </button>

        <?php if ($complexity >= 0.7): ?>
        <button class="px-3 py-1 text-sm bg-purple-500 text-white rounded hover:bg-purple-600 transition-colors"
                onclick="scheduleFocusSession(<?php echo $task['id']; ?>)">
            Schedule Focus Time
        </button>
        <?php endif; ?>

        <button class="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
                onclick="editTask(<?php echo $task['id']; ?>)">
            Edit
        </button>
    </div>

    <!-- ADHD Insights (if available) -->
    <?php if (!empty($adhdMetadata['insights'])): ?>
    <div class="mt-3 p-2 bg-blue-50 border border-blue-200 rounded text-blue-800 text-xs">
        <strong>💡 ADHD Insight:</strong> <?php echo htmlspecialchars($adhdMetadata['insights']); ?>
    </div>
    <?php endif; ?>
</div>

<script>
function toggleDescription(element) {
    const card = element.closest('.adhd-task-card');
    const description = card.querySelector('.line-clamp-3');
    const isExpanded = description.classList.contains('line-clamp-none');

    if (isExpanded) {
        description.classList.remove('line-clamp-none');
        description.classList.add('line-clamp-3');
        element.textContent = '... show more';
    } else {
        description.classList.remove('line-clamp-3');
        description.classList.add('line-clamp-none');
        element.textContent = 'show less';
    }
}

function startTask(taskId) {
    if (confirm('Start working on this task? This will update your ADHD session state.')) {
        fetch('/wp-json/dopemux/v1/tasks/' + taskId + '/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-WP-Nonce': wpApiSettings.nonce
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Failed to start task: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error starting task:', error);
            alert('Error starting task');
        });
    }
}

function scheduleFocusSession(taskId) {
    // Open focus session scheduler
    window.open('/focus-scheduler?task=' + taskId, '_blank', 'width=600,height=400');
}

function editTask(taskId) {
    window.location.href = '/tickets/showTicket/' + taskId;
}
</script>

<style>
.line-clamp-3 {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.line-clamp-none {
    display: block;
    -webkit-line-clamp: unset;
}
</style>