import React from 'react';
import { Text, Box } from 'ink';

interface Metrics {
    totalEvents: number;
    eventsPerSecond: number;
    avgLatency: number;
    errorRate: number;
}

interface MetricsPanelProps {
    metrics: Metrics;
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({ metrics }) => {
    const getErrorRateColor = (rate: number) => {
        if (rate > 0.1) return 'red';
        if (rate > 0.05) return 'yellow';
        return 'green';
    };

    const getLatencyColor = (latency: number) => {
        if (latency > 1000) return 'red';
        if (latency > 500) return 'yellow';
        return 'green';
    };

    return (
        <Box borderStyle="round" borderColor="blue" paddingX={1}>
            <Box flexDirection="column">
                <Text color="blue" bold>📈 Performance Metrics</Text>

                <Box marginTop={1} gap={2}>
                    <Box flexDirection="column">
                        <Text color="cyan" bold>{metrics.totalEvents}</Text>
                        <Text color="gray">Total Events</Text>
                    </Box>

                    <Box flexDirection="column">
                        <Text color="yellow" bold>{metrics.eventsPerSecond.toFixed(1)}/s</Text>
                        <Text color="gray">Event Rate</Text>
                    </Box>

                    <Box flexDirection="column">
                        <Text color={getLatencyColor(metrics.avgLatency)} bold>
                            {Math.round(metrics.avgLatency)}ms
                        </Text>
                        <Text color="gray">Avg Latency</Text>
                    </Box>

                    <Box flexDirection="column">
                        <Text color={getErrorRateColor(metrics.errorRate)} bold>
                            {(metrics.errorRate * 100).toFixed(1)}%
                        </Text>
                        <Text color="gray">Error Rate</Text>
                    </Box>
                </Box>
            </Box>
        </Box>
    );
};