#!/usr/bin/env node
import React, { useState, useEffect } from 'react';
import { render, Text, Box, useApp, useInput } from 'ink';
import Spinner from 'ink-spinner';
import Gradient from 'ink-gradient';
import BigText from 'ink-big-text';
import { createClient } from 'redis';
import { EventStream } from './components/EventStream.js';
import { InstancePanel } from './components/InstancePanel.js';
import { MetricsPanel } from './components/MetricsPanel.js';
import { ADHDPanel } from './components/ADHDPanel.js';
import type { DopemuxEvent, InstanceInfo, DashboardState } from './types.js';

const Dashboard = () => {
    const { exit } = useApp();
    const [state, setState] = useState<DashboardState>({
        connected: false,
        instances: [],
        events: [],
        metrics: {
            totalEvents: 0,
            eventsPerSecond: 0,
            avgLatency: 0,
            errorRate: 0
        },
        adhdMetrics: {
            highCognitiveLoad: 0,
            completions: 0,
            focusChanges: 0,
            interruptionsSafe: 0
        },
        selectedInstance: null,
        view: 'overview'
    });

    const [redisClient, setRedisClient] = useState<any>(null);

    // Connect to Redis on mount
    useEffect(() => {
        const connect = async () => {
            try {
                const client = createClient({
                    url: 'redis://localhost:6379'
                });

                client.on('error', (err) => {
                    console.error('Redis Client Error', err);
                    setState(s => ({ ...s, connected: false }));
                });

                await client.connect();
                setRedisClient(client);
                setState(s => ({ ...s, connected: true }));

                // Start consuming events
                consumeEvents(client);

            } catch (error) {
                console.error('Failed to connect to Redis:', error);
                setState(s => ({ ...s, connected: false }));
            }
        };

        connect();

        return () => {
            if (redisClient) {
                redisClient.disconnect();
            }
        };
    }, []);

    const consumeEvents = async (client: any) => {
        // Use Redis Streams XREAD to consume events
        while (true) {
            try {
                const messages = await client.xRead(
                    [
                        {
                            key: 'dopemux:events',
                            id: '$'  // Read new messages
                        }
                    ],
                    {
                        COUNT: 10,
                        BLOCK: 1000  // Block for 1 second
                    }
                );

                if (messages) {
                    for (const stream of messages) {
                        for (const message of stream.messages) {
                            processEvent(message);
                        }
                    }
                }
            } catch (error) {
                console.error('Error consuming events:', error);
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
    };

    const processEvent = (message: any) => {
        try {
            const event = JSON.parse(message.data.event || '{}');

            setState(prev => {
                const newState = { ...prev };

                // Add to events list
                newState.events = [event, ...prev.events].slice(0, 100);
                newState.metrics.totalEvents++;

                // Update metrics based on event type
                if (event.type?.includes('tool_call.completed')) {
                    const duration = event.payload?.duration_ms || 0;
                    newState.metrics.avgLatency =
                        (newState.metrics.avgLatency * (newState.metrics.totalEvents - 1) + duration)
                        / newState.metrics.totalEvents;

                    if (event.payload?.error) {
                        newState.metrics.errorRate =
                            ((newState.metrics.errorRate * (newState.metrics.totalEvents - 1)) + 1)
                            / newState.metrics.totalEvents;
                    }
                }

                // Update ADHD metrics
                if (event.adhd_metadata) {
                    const cognitiveLoad = event.adhd_metadata.cognitive_load;
                    if (cognitiveLoad === 'HIGH' || cognitiveLoad === 'EXTREME') {
                        newState.adhdMetrics.highCognitiveLoad++;
                    }

                    if (event.adhd_metadata.focus_context === 'positive_reinforcement') {
                        newState.adhdMetrics.completions++;
                    }

                    if (event.adhd_metadata.interruption_safe) {
                        newState.adhdMetrics.interruptionsSafe++;
                    }
                }

                // Update instance tracking
                if (event.namespace?.includes('instance.')) {
                    const instanceId = event.namespace.split('.')[1];
                    const instance = newState.instances.find(i => i.id === instanceId);
                    if (!instance) {
                        newState.instances.push({
                            id: instanceId,
                            status: 'active',
                            eventCount: 1,
                            lastSeen: new Date().toISOString()
                        });
                    } else {
                        instance.eventCount++;
                        instance.lastSeen = new Date().toISOString();
                    }
                }

                return newState;
            });
        } catch (error) {
            console.error('Error processing event:', error);
        }
    };

    // Handle keyboard input
    useInput((input, key) => {
        if (input === 'q' || (key.ctrl && input === 'c')) {
            exit();
        }

        // View switching
        if (input === '1') setState(s => ({ ...s, view: 'overview' }));
        if (input === '2') setState(s => ({ ...s, view: 'events' }));
        if (input === '3') setState(s => ({ ...s, view: 'instances' }));
        if (input === '4') setState(s => ({ ...s, view: 'adhd' }));

        // Clear events
        if (input === 'c') {
            setState(s => ({ ...s, events: [] }));
        }
    });

    return (
        <Box flexDirection="column" paddingX={1}>
            {/* Header */}
            <Box marginBottom={1}>
                <Gradient name="rainbow">
                    <BigText text="DOPEMUX" font="simple" />
                </Gradient>
            </Box>

            <Box marginBottom={1}>
                <Text color="cyan" bold>
                    Multi-Instance Coordination Dashboard
                </Text>
                <Text color="gray"> • </Text>
                {state.connected ? (
                    <Text color="green">
                        <Spinner type="dots" /> Connected to Redis
                    </Text>
                ) : (
                    <Text color="red">⚠ Disconnected</Text>
                )}
                <Text color="gray"> • </Text>
                <Text color="yellow">
                    {state.metrics.eventsPerSecond.toFixed(1)} events/sec
                </Text>
            </Box>

            {/* Navigation */}
            <Box marginBottom={1}>
                <Text color={state.view === 'overview' ? 'cyan' : 'gray'}>
                    [1] Overview
                </Text>
                <Text color="gray"> | </Text>
                <Text color={state.view === 'events' ? 'cyan' : 'gray'}>
                    [2] Events
                </Text>
                <Text color="gray"> | </Text>
                <Text color={state.view === 'instances' ? 'cyan' : 'gray'}>
                    [3] Instances
                </Text>
                <Text color="gray"> | </Text>
                <Text color={state.view === 'adhd' ? 'cyan' : 'gray'}>
                    [4] ADHD Focus
                </Text>
                <Text color="gray"> | </Text>
                <Text color="gray">[C] Clear</Text>
                <Text color="gray"> | </Text>
                <Text color="gray">[Q] Quit</Text>
            </Box>

            {/* Content based on view */}
            {state.view === 'overview' && (
                <Box flexDirection="column">
                    <MetricsPanel metrics={state.metrics} />
                    <Box marginTop={1}>
                        <InstancePanel instances={state.instances} />
                    </Box>
                    <Box marginTop={1}>
                        <EventStream events={state.events.slice(0, 5)} compact />
                    </Box>
                </Box>
            )}

            {state.view === 'events' && (
                <EventStream events={state.events} />
            )}

            {state.view === 'instances' && (
                <InstancePanel instances={state.instances} detailed />
            )}

            {state.view === 'adhd' && (
                <ADHDPanel metrics={state.adhdMetrics} events={state.events} />
            )}
        </Box>
    );
};

// Run the dashboard
render(<Dashboard />);