import React from 'react';
import { Text, Box } from 'ink';
import type { InstanceInfo } from '../types.js';

interface InstancePanelProps {
    instances: InstanceInfo[];
    detailed?: boolean;
}

export const InstancePanel: React.FC<InstancePanelProps> = ({ instances, detailed = false }) => {
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'active': return 'green';
            case 'idle': return 'yellow';
            case 'error': return 'red';
            case 'stopped': return 'gray';
            default: return 'gray';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'active': return '🟢';
            case 'idle': return '🟡';
            case 'error': return '🔴';
            case 'stopped': return '⚫';
            default: return '⚪';
        }
    };

    return (
        <Box flexDirection="column" borderStyle="round" borderColor="green" paddingX={1}>
            <Box marginBottom={1}>
                <Text color="green" bold>🏢 Instances</Text>
                <Text color="gray"> ({instances.length} running)</Text>
            </Box>

            {instances.length === 0 ? (
                <Text color="gray">No instances detected</Text>
            ) : (
                <Box flexDirection="column">
                    {instances.map((instance, index) => (
                        <Box key={instance.id} marginBottom={1}>
                            <Box>
                                {getStatusIcon(instance.status)}
                                <Text color="white" bold> Instance {instance.id}</Text>
                                <Text color="gray"> | </Text>
                                <Text color={getStatusColor(instance.status)}>
                                    {instance.status.toUpperCase()}
                                </Text>
                            </Box>

                            {detailed && (
                                <Box marginLeft={3} flexDirection="column">
                                    <Box>
                                        <Text color="gray">Events: </Text>
                                        <Text color="cyan">{instance.eventCount}</Text>
                                        <Text color="gray"> | Last seen: </Text>
                                        <Text color="blue">
                                            {new Date(instance.lastSeen).toLocaleTimeString()}
                                        </Text>
                                    </Box>

                                    {instance.port && (
                                        <Box>
                                            <Text color="gray">Port: </Text>
                                            <Text color="yellow">{instance.port}</Text>
                                        </Box>
                                    )}

                                    {instance.sessionId && (
                                        <Box>
                                            <Text color="gray">Session: </Text>
                                            <Text color="magenta">{instance.sessionId}</Text>
                                        </Box>
                                    )}
                                </Box>
                            )}
                        </Box>
                    ))}
                </Box>
            )}

            {detailed && instances.length > 1 && (
                <Box marginTop={1} borderStyle="single" borderColor="yellow" paddingX={1}>
                    <Text color="yellow">💡 Tip: </Text>
                    <Text color="gray">Press H to request session handoff between instances</Text>
                </Box>
            )}
        </Box>
    );
};