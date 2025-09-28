import React from 'react';
import { Text, Box } from 'ink';
import type { DopemuxEvent } from '../types.js';

interface ADHDMetrics {
    highCognitiveLoad: number;
    completions: number;
    focusChanges: number;
    interruptionsSafe: number;
}

interface ADHDPanelProps {
    metrics: ADHDMetrics;
    events: DopemuxEvent[];
}

export const ADHDPanel: React.FC<ADHDPanelProps> = ({ metrics, events }) => {
    // Calculate focus state from recent events
    const recentEvents = events.slice(0, 10);
    const recentHighLoad = recentEvents.filter(e =>
        e.adhd_metadata?.cognitive_load === 'HIGH' ||
        e.adhd_metadata?.cognitive_load === 'EXTREME'
    ).length;

    const focusState = recentHighLoad > 5 ? 'scattered' :
        recentHighLoad > 2 ? 'transitioning' : 'focused';

    const getFocusStateColor = (state: string) => {
        switch (state) {
            case 'focused': return 'green';
            case 'transitioning': return 'yellow';
            case 'scattered': return 'red';
            default: return 'gray';
        }
    };

    const getFocusStateIcon = (state: string) => {
        switch (state) {
            case 'focused': return '🎯';
            case 'transitioning': return '🔄';
            case 'scattered': return '🌀';
            default: return '❓';
        }
    };

    // Calculate productivity score
    const productivityScore = Math.min(100, Math.round(
        (metrics.completions * 10) +
        (metrics.interruptionsSafe * 2) -
        (metrics.highCognitiveLoad * 0.5)
    ));

    const getProductivityColor = (score: number) => {
        if (score >= 80) return 'green';
        if (score >= 60) return 'yellow';
        if (score >= 40) return 'blue';
        return 'red';
    };

    return (
        <Box flexDirection="column" borderStyle="round" borderColor="magenta" paddingX={1}>
            <Box marginBottom={1}>
                <Text color="magenta" bold>🧠 ADHD Focus Management</Text>
            </Box>

            {/* Current Focus State */}
            <Box marginBottom={1} borderStyle="single" borderColor={getFocusStateColor(focusState)} paddingX={1}>
                <Text>Current State: </Text>
                <Text color={getFocusStateColor(focusState)} bold>
                    {getFocusStateIcon(focusState)} {focusState.toUpperCase()}
                </Text>
            </Box>

            {/* Metrics Grid */}
            <Box gap={2} marginBottom={1}>
                <Box flexDirection="column">
                    <Text color="red" bold>{metrics.highCognitiveLoad}</Text>
                    <Text color="gray">High Load Events</Text>
                </Box>

                <Box flexDirection="column">
                    <Text color="green" bold>{metrics.completions}</Text>
                    <Text color="gray">Completions 🎉</Text>
                </Box>

                <Box flexDirection="column">
                    <Text color="yellow" bold>{metrics.focusChanges}</Text>
                    <Text color="gray">Focus Changes</Text>
                </Box>

                <Box flexDirection="column">
                    <Text color="cyan" bold>{metrics.interruptionsSafe}</Text>
                    <Text color="gray">Safe to Interrupt</Text>
                </Box>
            </Box>

            {/* Productivity Score */}
            <Box borderStyle="double" borderColor={getProductivityColor(productivityScore)} paddingX={1}>
                <Text>Productivity Score: </Text>
                <Text color={getProductivityColor(productivityScore)} bold>
                    {productivityScore}%
                </Text>
                {productivityScore >= 80 && <Text> 🚀</Text>}
                {productivityScore >= 60 && productivityScore < 80 && <Text> 💪</Text>}
                {productivityScore < 60 && <Text> 🔄</Text>}
            </Box>

            {/* Recommendations */}
            <Box marginTop={1} flexDirection="column">
                <Text color="yellow" bold>💡 Recommendations:</Text>
                {focusState === 'scattered' && (
                    <Box marginLeft={2}>
                        <Text color="gray">• Take a 5-minute break to reset focus</Text>
                    </Box>
                )}
                {focusState === 'transitioning' && (
                    <Box marginLeft={2}>
                        <Text color="gray">• Minimize context switches for next 10 minutes</Text>
                    </Box>
                )}
                {focusState === 'focused' && (
                    <Box marginLeft={2}>
                        <Text color="gray">• Great focus! Keep momentum for next task</Text>
                    </Box>
                )}
                {metrics.highCognitiveLoad > 10 && (
                    <Box marginLeft={2}>
                        <Text color="gray">• Consider breaking down complex tasks</Text>
                    </Box>
                )}
            </Box>

            {/* Focus Context Distribution */}
            <Box marginTop={1} flexDirection="column">
                <Text color="cyan" bold>📊 Focus Context Distribution:</Text>
                {(() => {
                    const contexts: Record<string, number> = {};
                    recentEvents.forEach(e => {
                        if (e.adhd_metadata?.focus_context) {
                            contexts[e.adhd_metadata.focus_context] =
                                (contexts[e.adhd_metadata.focus_context] || 0) + 1;
                        }
                    });

                    return Object.entries(contexts).map(([context, count]) => (
                        <Box key={context} marginLeft={2}>
                            <Text color="gray">{context}: </Text>
                            <Text color="blue">{count}</Text>
                        </Box>
                    ));
                })()}
            </Box>
        </Box>
    );
};