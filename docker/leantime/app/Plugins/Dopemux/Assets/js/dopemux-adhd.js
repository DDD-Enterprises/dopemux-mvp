/**
 * Dopemux ADHD Plugin - JavaScript Functionality
 *
 * Provides ADHD-optimized interactions for cognitive load, attention management,
 * and context preservation features.
 */

(function($) {
    'use strict';

    // Initialize when document is ready
    $(document).ready(function() {
        initializeADHDComponents();
        setupEventListeners();
        initializeCharts();
    });

    /**
     * Initialize ADHD-specific UI components
     */
    function initializeADHDComponents() {
        // Add loading states to prevent overwhelm
        $('.card').addClass('adhd-card-loading');

        // Initialize progress indicators
        initializeProgressIndicators();

        // Setup gentle animations for attention states
        setupAttentionAnimations();

        // Remove loading states after initialization
        setTimeout(function() {
            $('.adhd-card-loading').removeClass('adhd-card-loading');
        }, 500);
    }

    /**
     * Setup event listeners for ADHD interactions
     */
    function setupEventListeners() {
        // Quick action buttons for attention states
        setupQuickActions();

        // Cognitive load slider interactions
        setupCognitiveLoadControls();

        // Context saving interactions
        setupContextSaving();

        // Break reminder interactions
        setupBreakReminders();

        // Keyboard navigation for accessibility
        setupKeyboardNavigation();
    }

    /**
     * Initialize Chart.js charts for ADHD metrics
     */
    function initializeCharts() {
        // Cognitive Load History Chart
        initializeCognitiveLoadChart();

        // Attention State History Chart
        initializeAttentionStateChart();
    }

    /**
     * Setup quick action buttons for attention state changes
     */
    function setupQuickActions() {
        $('.quick-action').on('click', function(e) {
            e.preventDefault();

            const state = $(this).data('state');
            const button = $(this);

            // Visual feedback
            button.addClass('btn-loading');

            // Update form and submit
            $('#attention_state').val(state);

            // Simulate form submission (replace with actual form submission)
            setTimeout(function() {
                // Update UI immediately for better UX
                updateAttentionStateUI(state);

                // Show success feedback
                showSuccessMessage('Attention state updated to ' + state);

                button.removeClass('btn-loading');
            }, 500);
        });
    }

    /**
     * Setup cognitive load slider interactions
     */
    function setupCognitiveLoadControls() {
        const loadSlider = $('#cognitive_load');

        if (loadSlider.length) {
            loadSlider.on('input', function() {
                const value = $(this).val();
                updateLoadDisplay(value);
            });

            // Update on form submission
            $('form[action*="updateCognitiveLoad"]').on('submit', function(e) {
                const value = loadSlider.val();
                updateLoadDisplay(value);
                showSuccessMessage('Cognitive load updated to ' + value + '/10');
            });
        }
    }

    /**
     * Setup context saving interactions
     */
    function setupContextSaving() {
        // Auto-save context on page changes
        let contextSaveTimeout;

        $(window).on('beforeunload', function() {
            // Save context before leaving
            saveCurrentContext();
        });

        // Manual save button
        $('.btn-save-context').on('click', function(e) {
            e.preventDefault();
            saveCurrentContext();
        });
    }

    /**
     * Setup break reminder interactions
     */
    function setupBreakReminders() {
        $('.btn-take-break').on('click', function(e) {
            e.preventDefault();

            // Start break timer
            startBreakTimer();

            // Update UI
            $(this).addClass('btn-success').text('Break Started');

            // Show break overlay if available
            showBreakOverlay();
        });
    }

    /**
     * Setup keyboard navigation for accessibility
     */
    function setupKeyboardNavigation() {
        // Tab navigation through interactive elements
        $('.quick-action, .btn-save-context, .btn-take-break').attr('tabindex', '0');

        // Enter/Space activation for buttons
        $(document).on('keydown', '.quick-action, .btn-save-context, .btn-take-break', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                $(this).click();
            }
        });
    }

    /**
     * Initialize progress indicators
     */
    function initializeProgressIndicators() {
        // Add progress bars where needed
        $('.load-display').each(function() {
            const loadValue = $(this).find('.load-value').text().split('/')[0];
            updateLoadDisplay(loadValue);
        });
    }

    /**
     * Setup attention state animations
     */
    function setupAttentionAnimations() {
        // Add gentle animations for attention states
        $('.attention-hyperfocus .attention-icon').addClass('gentle-pulse');
        $('.attention-scattered .attention-icon').addClass('gentle-pulse');
    }

    /**
     * Initialize Cognitive Load History Chart
     */
    function initializeCognitiveLoadChart() {
        const chartCanvas = document.getElementById('cognitiveLoadChart');

        if (chartCanvas && typeof Chart !== 'undefined') {
            const ctx = chartCanvas.getContext('2d');
            const loadData = window.cognitiveLoadData || [];

            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: loadData.map(item => new Date(item.timestamp).toLocaleTimeString()),
                    datasets: [{
                        label: 'Cognitive Load',
                        data: loadData.map(item => item.load),
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.1,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 10,
                            ticks: {
                                stepSize: 1
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }
    }

    /**
     * Initialize Attention State History Chart
     */
    function initializeAttentionStateChart() {
        const chartCanvas = document.getElementById('attentionHistoryChart');

        if (chartCanvas && typeof Chart !== 'undefined') {
            const ctx = chartCanvas.getContext('2d');
            const historyData = window.attentionHistoryData || [];

            // Map states to numeric values for charting
            const stateMap = {
                'hyperfocus': 5,
                'focused': 4,
                'scattered': 2,
                'background': 1,
                'transition': 3
            };

            const reverseMap = {
                1: 'background',
                2: 'scattered',
                3: 'transition',
                4: 'focused',
                5: 'hyperfocus'
            };

            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: historyData.map(item => new Date(item.timestamp).toLocaleTimeString()),
                    datasets: [{
                        label: 'Attention State',
                        data: historyData.map(item => stateMap[item.state] || 3),
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 5,
                            ticks: {
                                callback: function(value) {
                                    return reverseMap[value] || value;
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }
    }

    /**
     * Update attention state UI immediately
     */
    function updateAttentionStateUI(state) {
        // Update display classes
        $('.attention-display').removeClass('attention-hyperfocus attention-focused attention-scattered attention-background attention-transition');
        $('.attention-display').addClass('attention-' + state);

        // Update icon
        const iconMap = {
            'hyperfocus': 'fa-bolt',
            'focused': 'fa-crosshairs',
            'scattered': 'fa-scatter-plot',
            'background': 'fa-clock',
            'transition': 'fa-question'
        };

        $('.attention-icon i').removeClass().addClass('fa ' + (iconMap[state] || 'fa-question'));

        // Update label
        $('.attention-label').text(state.charAt(0).toUpperCase() + state.slice(1));
    }

    /**
     * Update load display immediately
     */
    function updateLoadDisplay(value) {
        $('.load-display').removeClass('load-1 load-2 load-3 load-4 load-5 load-6 load-7 load-8 load-9 load-10');
        $('.load-display').addClass('load-' + Math.round(value));

        $('.load-value').text(value + '/10');

        const labels = {
            1: 'Very Low', 2: 'Low', 3: 'Low',
            4: 'Medium', 5: 'Medium', 6: 'Medium',
            7: 'High', 8: 'High', 9: 'Very High', 10: 'Extreme'
        };

        $('.load-label').text(labels[Math.round(value)] || 'Unknown');

        // Update progress bar
        $('.load-bar .progress-bar').css('width', (value * 10) + '%');
    }

    /**
     * Save current context
     */
    function saveCurrentContext() {
        // Collect current context data
        const contextData = {
            timestamp: new Date().toISOString(),
            url: window.location.href,
            open_tabs: [], // Would collect from browser API
            notes: $('#context-notes').val() || '',
            active_project: window.currentProject || '',
            active_tickets: window.activeTickets || []
        };

        // Send to server (would implement proper AJAX call)
        console.log('Saving context:', contextData);

        // Show feedback
        showSuccessMessage('Context saved successfully');
    }

    /**
     * Start break timer
     */
    function startBreakTimer() {
        const breakDuration = 5 * 60 * 1000; // 5 minutes in milliseconds

        // Set timer
        setTimeout(function() {
            showBreakReminder('Break time is up! Ready to get back to work?');
        }, breakDuration);

        // Update UI
        $('.break-info').addClass('break-active');
    }

    /**
     * Show break overlay
     */
    function showBreakOverlay() {
        // Create break overlay if it doesn't exist
        if (!$('#break-overlay').length) {
            $('body').append(`
                <div id="break-overlay" class="break-overlay">
                    <div class="break-content">
                        <h2>Time for a Break! 🌱</h2>
                        <p>Step away from your screen for 5 minutes.</p>
                        <p>Stretch, walk around, or just relax.</p>
                        <button class="btn btn-primary btn-lg" onclick="endBreak()">Resume Work</button>
                    </div>
                </div>
            `);
        }

        $('#break-overlay').fadeIn();
    }

    /**
     * End break and hide overlay
     */
    window.endBreak = function() {
        $('#break-overlay').fadeOut();
        $('.break-info').removeClass('break-active');
        showSuccessMessage('Welcome back! Ready to continue?');
    };

    /**
     * Show break reminder
     */
    function showBreakReminder(message) {
        // Show notification
        showNotification(message, 'info');

        // Play gentle sound if supported
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Break Reminder', {
                body: message,
                icon: '/images/break-icon.png'
            });
        }
    }

    /**
     * Show success message
     */
    function showSuccessMessage(message) {
        // Use Leantime's notification system or create custom
        if (typeof leantime !== 'undefined' && leantime.showNotification) {
            leantime.showNotification(message, 'success');
        } else {
            // Fallback notification
            showNotification(message, 'success');
        }
    }

    /**
     * Show notification
     */
    function showNotification(message, type) {
        // Create notification element
        const notification = $(`
            <div class="alert alert-${type} alert-dismissible fade show adhd-notification">
                ${message}
                <button type="button" class="close" data-dismiss="alert">
                    <span>&times;</span>
                </button>
            </div>
        `);

        // Add to page
        $('body').prepend(notification);

        // Auto-hide after 5 seconds
        setTimeout(function() {
            notification.fadeOut(function() {
                $(this).remove();
            });
        }, 5000);
    }

    /**
     * Make functions globally available for inline event handlers
     */
    window.DopemuxADHD = {
        updateAttentionState: updateAttentionStateUI,
        updateCognitiveLoad: updateLoadDisplay,
        saveContext: saveCurrentContext,
        takeBreak: startBreakTimer,
        endBreak: window.endBreak
    };

})(jQuery);