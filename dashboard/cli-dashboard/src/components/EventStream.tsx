import React from 'react';
import { Text, Box } from 'ink';
import type { DopemuxEvent } from '../types.js';

interface EventStreamProps {
    events: DopemuxEvent[];
    compact?: boolean;
}

export const EventStream: React.FC<EventStreamProps> = ({ events, compact = false }) => {
    const displayEvents = compact ? events.slice(0, 5) : events.slice(0, 20);

    const getCognitiveLoadColor = (load?: string) => {
        switch (load) {
            case 'MINIMAL': return 'blue';
            case 'LOW': return 'cyan';
            case 'MEDIUM': return 'yellow';
            case 'HIGH': return 'magenta';
            case 'EXTREME': return 'red';
            default: return 'gray';
        }
    };

    const getPriorityColor = (priority?: string) => {
        switch (priority) {
            case 'CRITICAL': return 'red';
            case 'HIGH': return 'magenta';
            case 'NORMAL': return 'cyan';
            case 'LOW': return 'blue';
            case 'MINIMAL': return 'gray';
            default: return 'gray';
        }
    };

    return (
        <Box flexDirection="column" borderStyle="round" borderColor="cyan" paddingX={1}>
            <Box marginBottom={1}>
                <Text color="cyan" bold>📊 Event Stream</Text>
                <Text color="gray"> ({events.length} total)</Text>
            </Box>

            {displayEvents.length === 0 ? (
                <Text color="gray">No events yet...</Text>
            ) : (
                <Box flexDirection="column">
                    {displayEvents.map((event, index) => (
                        <Box key={index} marginBottom={compact ? 0 : 1}>
                            <Box>
                                <Text color="gray">
                                    {new Date(event.timestamp || Date.now()).toLocaleTimeString()}
                                </Text>
                                <Text color="gray"> | </Text>
                                <Text color="cyan">{event.type}</Text>
                            </Box>

                            {!compact && (
                                <Box marginLeft={2}>
                                    <Text color="gray">Priority: </Text>
                                    <Text color={getPriorityColor(event.priority)}>
                                        {event.priority || 'NORMAL'}
                                    </Text>

                                    {event.adhd_metadata && (
                                        <>
                                            <Text color="gray"> | Load: </Text>
                                            <Text color={getCognitiveLoadColor(event.adhd_metadata.cognitive_load)}>
                                                {event.adhd_metadata.cognitive_load}
                                            </Text>

                                            {event.adhd_metadata.attention_required && (
                                                <Text color="yellow"> ⚠</Text>
                                            )}

                                            {event.adhd_metadata.focus_context && (
                                                <>
                                                    <Text color="gray"> | Context: </Text>
                                                    <Text color="green">
                                                        {event.adhd_metadata.focus_context}
                                                    </Text>
                                                </>
                                            )}
                                        </>
                                    )}
                                </Box>
                            )}

                            {!compact && event.payload && (
                                <Box marginLeft={2}>
                                    <Text color="gray" dimColor>
                                        {JSON.stringify(event.payload).substring(0, 80)}...
                                    </Text>
                                </Box>
                            )}
                        </Box>
                    ))}
                </Box>
            )}
        </Box>
    );
};